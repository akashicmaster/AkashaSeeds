"""
The shape a DECLARED source importer has in common — step 1 §1.7.

Four datasets used to be four bodies inside `lib/akasha/source/bootstrap.py`, each knowing its own
corpus directory, its own pool id, its own labo and its own reset rule. Those are the things
that differ between datasets, so they are declared in `app/config/source/<id>.json`
and the bodies move here, to the side that owns the data.

What stays PLATFORM is the managed unit around the call: the heartbeat, the hard cap, the boot
sentinel and the progress file. What is here is what the dataset itself needs:

  · resolve the corpus the declaration names, and say so plainly when it is absent — a cell that
    did not ship a corpus has nothing to import, which is not a failure;
  · a dispatch closure, so an importer talks to the cell the same way an operator would;
  · the CONTENT-HASH skip: when the bundle is the one this cell imported, nothing is opened. The hash is recorded in the GRAPH rather than in a file beside the
    process — a file is invisible to `lens`, to `as_of` and to retention, and it does not survive a
    cell that moves.

Each importer's entry is `run_declared(kernel, decl) -> dict`. The name is in the declaration
(`importer: "module:fn"`), which is why it can be this rather than `run`: `run` is already each
script's dataset primitive, driven directly by ten evals, and renaming it to win a cosmetic match
would cost more than it is worth.
"""
import glob
import hashlib
import logging
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def corpus_dir(decl):
    """The corpus directory this declaration names, or "" when it is not on this cell."""
    rel = str((decl or {}).get("corpus") or "").strip()
    if not rel:
        return ""
    p = os.path.join(ROOT, rel)
    return p if os.path.isdir(p) else ""


def content_hash(decl):
    """A hash over the files `reset_key` names, in declared order.

    The key is DECLARED rather than inferred from the directory: adding a file to a bundle should
    be a deliberate re-import, not something that happens because a stray file landed there. A file
    the key names and the cell does not have contributes its absence, so a bundle that loses a file
    is a change too."""
    h = hashlib.sha256()
    for pat in ((decl or {}).get("reset_key") or []):
        for p in sorted(glob.glob(os.path.join(ROOT, str(pat)))) or [os.path.join(ROOT, str(pat))]:
            h.update(str(os.path.relpath(p, ROOT)).encode("utf-8"))
            try:
                with open(p, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
            except OSError:
                h.update(b"\x00absent")
    return h.hexdigest()


def dispatcher(kernel, client="admin"):
    """A `dispatch(method, data) -> result` over this cell, as the boot admin.

    Every importer talks to the cell through ordinary ops — the same ones an operator would type —
    so an import has no write path of its own and nothing to keep in step with the rest."""
    from lib.akasha.api.trust import TRUST_INTERNAL

    def _d(method, data=None):
        r = kernel.dispatch({"jsonrpc": "2.0", "method": method,
                             "params": {"client_id": client, "data": dict(data or {})},
                             "id": "declared-import"}, TRUST_INTERNAL)
        if isinstance(r, dict) and "result" in r:
            return r.get("result")
        # A refusal is still None to the caller (importers probe with reads that may miss), but it
        # is never SILENT: a write an import depended on that came back None used to surface only
        # as an AttributeError several lines later, with the op's own reason thrown away.
        err = (r or {}).get("error") if isinstance(r, dict) else None
        if err and method not in ("r", "read"):
            logging.getLogger("akasha.import").warning(
                "[import] refused method=%s code=%s — %s", method, err.get("code"), err.get("message"))
        return None

    return _d


def _mark_alias(decl):
    return "source:import:%s:content" % str((decl or {}).get("id") or "unknown")


def marker(kernel, decl):
    """What this cell recorded about its last import of this corpus, as a mapping ({} when none).

    The record is the atom's own BODY rather than its meta: an atom's meta is the store's — a
    definition is stamped `type: hub, role: concept` whatever a caller passes — so a fact a reader
    needs back has to be in the content, where `r` shows it and a person can read it."""
    try:
        got = dispatcher(kernel)("r", {"id": _mark_alias(decl)}) or {}
    except Exception:
        return {}
    body = str(got.get("content") or "")
    i = body.find("{")
    if i < 0:
        return {}
    try:
        out = json.loads(body[i:])
        return out if isinstance(out, dict) else {}
    except ValueError:
        return {}


def recorded_hash(kernel, decl):
    """The content hash of the bundle this cell last imported, or ""."""
    return str(marker(kernel, decl).get("content_hash") or "")


def record_hash(kernel, decl, digest, extra=None):
    """Remember what was imported, as an atom. Best-effort: an import that succeeded and failed to
    leave its marker will simply re-import next boot, which is wasteful but never wrong."""
    try:
        meta = {"concept": "source_import", "source_id": (decl or {}).get("id"),
                "content_hash": digest, "pool": (decl or {}).get("pool"),
                "labo": (decl or {}).get("labo")}
        meta.update(extra or {})
        dispatcher(kernel)("kernel.memory.define",
                           {"name": _mark_alias(decl),
                            "description": json.dumps(meta, ensure_ascii=False, sort_keys=True),
                            "scope": "universal"})
    except Exception:
        pass


def unchanged(kernel, decl):
    """True when this cell has already imported exactly this bundle.

    Checked BEFORE a corpus file is opened, which is the point: a boot is O(what changed), not
    O(the corpus)."""
    d = content_hash(decl)
    return bool(d) and d == recorded_hash(kernel, decl)


def decide(kernel, decl, populated=False):
    """`("skip" | "import", digest)` — what this boot owes the declared corpus.

    *skip* — the recorded hash is this bundle's: nothing is opened.
    *import* — anything else: create, acquire and freeze. Acquisition is idempotent, so importing rows that
      happen to be present costs time and changes nothing. There is no repair, no adoption and no reset: a
      cell starts from Genesis, and a changed corpus is a new seed on a new cell."""
    d = content_hash(decl)
    rec = recorded_hash(kernel, decl)
    if d and rec and d == rec:
        return "skip", d
    return "import", d


class Ctl:
    """What the platform's managed unit offers a declared importer, and what it looks like without one.

    An importer is called during a boot by a supervised background unit that owns the heartbeat, the
    hard wall-clock cap, the run-once sentinel and the resume cursor. None of that is dataset
    knowledge, so none of it is written here — but an importer still has to SPEAK to it (each phase
    it reaches) and, when a corpus is too large to finish inside one cap, to ADVANCE a cursor so the
    next boot continues instead of starting over. This is that seam, and its default is a working
    stand-alone one so an importer can be driven from a terminal or an eval with nothing else present."""

    def __init__(self, log=print, progress_path=""):
        self._log = log or (lambda _m: None)
        self._path = progress_path
        self._n = None

    def say(self, msg):
        """One phase. The platform's implementation also beats the heartbeat and RAISES when the run
        has outlived its cap or the cell is shutting down — so an importer must let this propagate."""
        self._log(msg)

    def progress(self):
        """How many records of this corpus are already acquired, from an earlier run that ran out of
        cap. 0 when there is no cursor, which is also the honest answer for a first run."""
        if self._n is None:
            self._n = 0
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    self._n = max(0, int((fh.read() or "0").strip() or 0))
            except (OSError, ValueError, TypeError):
                pass
        return self._n

    def advance(self, n):
        """Record the cursor after a batch is DURABLY acquired — never before, or a killed run
        resumes past rows it never wrote."""
        self._n = max(0, int(n))
        if not self._path:
            return
        try:
            with open(self._path, "w", encoding="utf-8") as fh:
                fh.write(str(self._n))
                fh.flush()
                os.fsync(fh.fileno())
        except OSError:
            pass


def await_job(kernel, job, ctl, what, cap_s=3600):
    """Wait for one submitted JCL job and say plainly how it ended.

    An importer whose compute is a job must not stamp its corpus complete while that job is still
    running: the sentinel is what stops the work being done again, so writing it early converts an
    interrupted compute into a permanent gap. Returns `(ok, detail)`; `ok` is False for every ending
    that should be retried on the next boot, including "still running when the cap expired"."""
    import time

    from lib.akasha.api import process as lifecycle
    from lib.akasha.api.jobs import CANCELLED, DONE, FAILED

    deadline = time.time() + max(1, int(cap_s))
    beat = 0
    while True:
        if lifecycle.is_shutting_down():
            return False, "shutting down — %s resumes next boot" % what
        st = getattr(job, "status", None)
        if st == DONE:
            return True, "%s complete" % what
        if st in (FAILED, CANCELLED):
            errs = "; ".join((getattr(job, "step_errors", None) or [])[:3]) or \
                   (getattr(job, "error", None) or "")
            return False, "%s ended %s (%s)" % (what, st, errs[:160])
        if time.time() > deadline:
            return False, "%s still running after %ds — deferred to the next boot" % (what, cap_s)
        beat += 1
        if beat % 10 == 1:        # ~every 30s: enough to keep a heartbeat alive, not a log flood
            ctl.say("%s running (job %s)" % (what, getattr(job, "job_id", "?")))
        time.sleep(3)
