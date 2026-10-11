"""
Learning bench (world-workbench-society spec + PLANTS Vision Learning v0.1) — a concrete `bench`
concept, kind `learning`. It subclasses the workbench base and adds the operation FAMILIES a local
neural-network learning experiment needs:

  dataset   — reference a frozen Source pool of image REFERENCES into the bench (never a copy)
  feature   — machine feature extraction, delegated to the EXISTING vlab observers (transient fetch →
              embedding Feature atom → unlink; the image binary is never stored)
  train     — fit a small classifier head on the Feature atoms of a run (NEW)
  evaluate  — re-score a trained head on any frozen sample (NEW)
  promote   — register the trained head back as a vlab OBSERVER whose predictions are auditable
              observations like any other (NEW)

The six laws (design §0) are held by construction:
  1. the image binary is NEVER stored — dataset/feature only ever carry an image_ref, and training
     runs on the Feature VECTORS the vlab observers already produce, not on pixels;
  2. trained weights are a binary artifact — the head file lives OUTSIDE the store (the bench artifact
     dir) and the store holds only a model-identity atom (sha256 + size + provenance);
  3. learning provenance IS observations — every op runs through `_perform`, so success AND failure
     tee onto the bench's Source Stream (observation time = the training history, replayable);
  4. metrics are aggregates — ONE metrics atom per training run (+ a per-class table), never a
     per-batch/per-epoch write stream;
  5. no hypothesis-filtering of data — the train/test split is a deterministic, seeded, frozen
     stratified sample recorded on the bench (auditable frame);
  6. degradation-first — sklearn → a numpy nearest-centroid floor → a mock; a missing library never
     crashes the bench (the failure is a recorded observation).

There is NOTHING PLANTS-specific in this module — species, iNaturalist, and the block logic are DATA
of an instance (app/config/workbench/plants-vision/templates/*.ak + app/config/workbench/workloads/plants_vision.json), exactly as
bench_research kept the research families clean of any seminar.
"""
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.api.process import artifact_id as _artifact_id, is_stale as _is_stale
from lib.akasha.api.concepts import slug as _uslug
from lib.akasha.api.concepts import WorkbenchConcept

logger = logging.getLogger("Harmonia.Concept.BenchLearning")


def _sha8_list(members) -> str:
    """A stable 8-hex digest of a members list (order-independent) — the corpus fingerprint that lets a
    frame/metrics atom announce whether it is the SAME frozen corpus or a re-trained one (A46)."""
    import hashlib as _hl
    h = _hl.sha256("\n".join(sorted(str(m) for m in (members or []))).encode("utf-8"))
    return h.hexdigest()[:8]


# The nucleus set the vlab roster reads to load PROMOTED learned heads as observers (kept in the
# shared nucleus so a fresh VisionLabConcept instance — one per dispatch — rediscovers them).
LEARNED_OBSERVERS_SET = "set:vlab:learned"

class LearningBenchConcept(WorkbenchConcept):
    """`bench.*` (kind=learning) — dataset / feature / train / evaluate / promote, all observed."""

    CONCEPT_PREFIX = "learning"
    CONCEPT_LABEL = "Learning bench — dataset, feature extraction, training, evaluation, promotion (observed)"

    KIND = "learning"
    _FAMILIES = ("dataset", "feature", "observe", "train", "evaluate", "promote")

    CONCEPT_METHODS: Dict[str, Any] = {
        "dataset.bind": {"op": "op_dataset_bind", "action": "record",
                         "desc": "Reference a frozen Source image pool into the bench (never a copy): "
                                 "learning.dataset.bind name= pool="},
        "dataset.ls":   {"op": "op_dataset_ls", "action": "read",
                         "desc": "List the bench's bound datasets: learning.dataset.ls name="},
        "feature.extract": {"op": "op_feature_extract", "action": "record",
                            "desc": "Extract features via the vlab observers (transient, no binary): "
                                    "learning.feature.extract name= pool= observers=mobilenet[,color] run="},
        "feature.run":    {"op": "op_feature_run", "action": "record",
                           "desc": "Open a feature run over a pool (no execution yet): "
                                   "learning.feature.run name= pool= observers=mobilenet run="},
        "feature.execute": {"op": "op_feature_execute", "action": "record",
                            "desc": "Execute a chunk of a feature run (resumable): "
                                    "learning.feature.execute name= run= [limit=]"},
        "feature.seal":   {"op": "op_feature_seal", "action": "record",
                           "desc": "Seal a completed feature run: learning.feature.seal name= run="},
        "feature.spaces": {"op": "op_feature_spaces", "action": "read",
                           "desc": "Per-observer feature counts for a run: learning.feature.spaces name= run="},
        "observe":  {"op": "op_observe", "action": "record",
                     "desc": "Observe a pool with a reading observer (run.new + whole-pool execute + "
                             "seal, resumable) — the learning-free reading (T2) or the learned reading "
                             "(T6): learning.observe name= pool=<pool|role:target> observers=litert run=o0"},
        "train":    {"op": "op_train", "action": "record",
                     "desc": "Train a classifier head on a feature run: learning.train name= run= "
                             "space=mobilenet head=logreg|mlp [split=0.8] [seed=] [label_key=label]"},
        "evaluate": {"op": "op_evaluate", "action": "record",
                     "desc": "Re-score a trained head on a frozen sample: learning.evaluate name= model= "
                             "[sample=<train|test|its alias>]"},
        "promote":  {"op": "op_promote", "action": "record",
                     "desc": "Register a trained head as a vlab observer: learning.promote name= model= "
                             "[observer=<id>]"},
        "runs":     {"op": "op_runs", "action": "read",
                     "desc": "The runs of the bench with coordinates + sizes + stored diffs: "
                             "learning.runs name= [branch=] [mode=]"},
    }

    # ── helpers ──────────────────────────────────────────────────────────────────
    def _require_bench(self, name: str) -> str:
        alias = self._bench_alias(name)
        if not self._key(alias):
            raise ValueError(f"unknown bench '{name}' — bench.new it first")
        return alias

    def _sub(self, name: str, suffix: str) -> str:
        return f"{self._bench_alias(name)}:{suffix}"

    def _next_n(self, name: str, family_set: str) -> int:
        return len(self._members(self._sub(name, family_set))) + 1

    def _record(self, name: str, key: str, family_set: str) -> None:
        self._add_to_set(self._sub(name, family_set), key)
        self._add_to_set(self._scope_set(name), key)

    def _vlab(self):
        from app.concepts.vision_lab import VisionLabConcept
        v = getattr(self, "_vlab_cache", None)
        if v is None:
            v = self._vlab_cache = VisionLabConcept(self.session)
        return v

    def _nucleus_meta(self, ident: str) -> Dict[str, Any]:
        """Read an atom that lives in the vlab/source NUCLEUS space (features, source atoms, learned
        observers) while the bench is bound to its group engine."""
        saved = getattr(self, "_space", "")
        self._space = ""
        try:
            return self._meta(ident)
        finally:
            self._space = saved

    def _nucleus_write(self, alias: str, content: str, meta: Dict[str, Any]) -> str:
        saved = getattr(self, "_space", "")
        self._space = ""
        try:
            key = self._mk(alias, content, meta)
            return key
        finally:
            self._space = saved

    def _nucleus_replace(self, alias: str, content: str, meta: Dict[str, Any], compare_meta=()) -> tuple:
        """A46(4) — REPLACE-on-change a nucleus record by alias (the learned-observer record must follow
        the model it points at, not stay pinned to yesterday's head). Returns (key, changed, old_key)."""
        saved = getattr(self, "_space", "")
        self._space = ""
        try:
            return self._mk_replace(alias, content, meta, compare_meta=compare_meta)
        finally:
            self._space = saved

    def _nucleus_add(self, set_name: str, key: str) -> None:
        saved = getattr(self, "_space", "")
        self._space = ""
        try:
            self._add_to_set(set_name, key)
        finally:
            self._space = saved

    def _source_label(self, src_alias: str, keys) -> Optional[str]:
        """A source atom's class label — the join key back to the checklist. `keys` is a candidate list
        (the pool's declared `label_field` first — A34b — then `label`/`symbol`), tried at the top level
        AND inside `source_metadata`. The declared join lives on the DATA, so a workflow needs no
        label_key."""
        if isinstance(keys, str):
            keys = [keys]
        cand = [k for k in list(keys or []) if k] + ["label", "symbol"]
        m = self._nucleus_meta(src_alias)
        if not m:
            return None
        for k in cand:
            if m.get(k):
                return str(m[k])
        sm = m.get("source_metadata") or {}
        for k in cand:
            if sm.get(k):
                return str(sm[k])
        return None

    def _pool_label_fields(self, name: str) -> List[str]:
        """The `label_field` declared on each pool bound to this bench (A34b) — the DATA declares the
        join, so `learning.train` needs no `label_key`. De-duplicated, first-seen order."""
        out: List[str] = []
        try:
            for k in self._members(self._sub(name, "datasets")):
                pool = (self._meta(k) or {}).get("pool")
                if not pool:
                    continue
                lf = (self._nucleus_meta(pool) or {}).get("label_field")
                if lf and lf not in out:
                    out.append(str(lf))
        except Exception:
            pass
        return out

    def _sm_fields_seen(self, src_aliases) -> List[str]:
        """The union of source_metadata field names on a few sample atoms — for the A34(e) error text
        ('what did the learner actually see?'). Bounded to the first handful (never a full scan)."""
        seen: List[str] = []
        for a in list(src_aliases)[:8]:
            sm = (self._nucleus_meta(a) or {}).get("source_metadata") or {}
            for f in sm.keys():
                if f not in seen:
                    seen.append(f)
        return seen[:12]

    @staticmethod
    def _rank(seed: str, alias: str) -> int:
        import hashlib
        return int.from_bytes(hashlib.sha256((str(seed) + "|" + alias).encode()).digest()[:8], "big")

    def _split(self, labeled: List[Tuple[str, List[float], str]], ratio: float,
               seed: str) -> Tuple[list, list]:
        """Deterministic STRATIFIED split (per class), ordered by the same sha256(seed+alias) rank the
        Source Layer's pool.sample uses — reproducible and auditable. Returns (train, test)."""
        by_class: Dict[str, list] = {}
        for row in labeled:
            by_class.setdefault(row[2], []).append(row)
        train, test = [], []
        for c, rows in by_class.items():
            rows = sorted(rows, key=lambda r: self._rank(seed, r[0]))
            k = int(round(len(rows) * ratio))
            k = min(max(k, 1), len(rows) - 1) if len(rows) > 1 else len(rows)
            train.extend(rows[:k])
            test.extend(rows[k:])
        return train, test

    def _freeze_sample(self, name: str, run: str, which: str, members: List[str],
                       seed: str, ratio: float, corpus_sha: str = "") -> tuple:
        """A46(2) — freeze a train/test frame. The frame is REPLACE-on-change (not idempotent-by-alias):
        a re-train over a changed corpus produces a different `members` list, so the frozen frame is
        re-minted (new content-addressed atom, alias re-pointed, old kept) instead of silently returning
        yesterday's 2-class 20-item split. An identical re-train is a no-op. `corpus_sha` is the FULL
        corpus fingerprint (shared by the model and both frames) so evaluate can tell a frame belongs to
        the model's corpus (a frame's own members are a subset, so the frame's member-hash would not
        match the model's whole-corpus hash — they must carry the SAME corpus_sha)."""
        alias = self._sub(name, f"sample:{which}:{_uslug(run)}")
        # the members fingerprint is folded into the MINTED content so a changed frame (same length,
        # different members) still yields a NEW content-addressed key (A46(2)).
        content = f"[{alias}] frozen {which} sample ({len(members)} members)\n#members {_sha8_list(members)}"
        key, changed, old_key = self._mk_replace(
            alias, content,
            {"concept": "bench_sample", "bench": self._bench_alias(name), "run": run,
             "which": which, "members": members, "seed": seed, "ratio": ratio,
             "status": "FROZEN", "member_count": len(members),
             "corpus_sha": corpus_sha or _sha8_list(members),
             "frozen_wall": round(time.time(), 3), "author": self._client()},
            compare_meta=("members",))
        if old_key:
            self._link(alias, old_key, "bench:superseded_by")
        self._record(name, key, "samples")
        return alias, bool(changed)

    # ── dataset family ───────────────────────────────────────────────────────────────
    def op_dataset_bind(self, name: str, pool: str = "", cast: str = "", role: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            if not pool:
                raise ValueError("learning.dataset.bind requires pool=")
            n = self._next_n(name, "datasets")
            alias = self._sub(name, f"dataset:{n}")
            # role= (Part D §2 T1) — an OPTIONAL functional role (train | target | reference) recorded on
            # the binding, so later blocks/macros resolve `pool=role:target` instead of by pool name.
            key = self._mk(alias, f"[{alias}] dataset reference → {pool}",
                           {"concept": "bench_dataset", "bench": self._bench_alias(name),
                            "pool": pool, "n": n, "role": role or None, "author": self._client(),
                            "created_wall": round(time.time(), 3)})
            self._record(name, key, "datasets")
            self._link(alias, pool, "bench:references")     # a reference, never a copy
            return {"bound": alias, "pool": pool, "n": n, "role": role or None}
        return self._perform(name, "dataset", "bind", {"pool": pool, "cast": cast, "role": role}, _fn)

    def _resolve_pool(self, name: str, pool: str) -> str:
        """Resolve a `pool=role:<role>` reference to the actual pool bound with that role (Part D §2 T1).
        A plain pool id passes through unchanged. The newest binding for a role wins (a re-bind updates
        the role), so a role always points at the current dataset."""
        if not pool or not pool.startswith("role:"):
            return pool
        want = pool.split(":", 1)[1].strip()
        found = None
        for k in self._members(self._sub(name, "datasets")):
            m = self._meta(k) or {}
            if (m.get("role") or "") == want and m.get("pool"):
                found = str(m["pool"])                       # keep scanning → newest binding wins
        if not found:
            raise ValueError(f"bench '{name}' has no dataset bound with role={want} "
                             f"(learning.dataset.bind … role={want})")
        return found

    def op_dataset_ls(self, name: str) -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)
        rows = []
        for k in self._members(self._sub(name, "datasets")):
            m = self._meta(k)
            rows.append({"id": self._alias(k), "pool": m.get("pool")})
        return {"bench": self._bench_alias(name), "datasets": rows, "count": len(rows)}

    # ── feature family (delegates to vlab, unchanged) ────────────────────────────────
    def op_feature_extract(self, name: str, pool: str = "", observers: str = "mobilenet",
                           run: str = "", cast: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            if not pool or not run:
                raise ValueError("learning.feature.extract requires pool= and run=")
            pool_r = self._resolve_pool(name, pool)
            vl = self._vlab()
            vl.op_run_new(pool=pool_r, observers=observers, run=run)
            ex = vl.op_run_execute(run=run)
            alias = self._sub(name, f"featrun:{_uslug(run)}")
            key = self._mk(alias, f"[{alias}] feature run {run} on {pool_r} ({observers})",
                           {"concept": "bench_featrun", "bench": self._bench_alias(name), "run": run,
                            "pool": pool_r, "observers": observers, "observed": ex.get("observed"),
                            "failed": ex.get("failed"), "author": self._client(),
                            "created_wall": round(time.time(), 3)})
            self._record(name, key, "featruns")
            self._link(alias, f"vision_run:{_uslug(run)}", "bench:references")
            return {"featrun": alias, "run": run, "pool": pool_r, "observers": observers,
                    "observed": ex.get("observed"), "failed": ex.get("failed")}
        return self._perform(name, "feature", "extract",
                             {"pool": pool, "observers": observers, "run": run, "cast": cast}, _fn)

    def op_feature_run(self, name: str, pool: str = "", observers: str = "mobilenet",
                       run: str = "", cast: str = "", branch: str = "") -> Dict[str, Any]:
        """[learning.feature.run] Open a vlab feature run over a pool (no execution yet) — the design's
        chunked B3 vocabulary (run → execute×N → seal). feature.extract is run+execute in one call."""
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            if not pool or not run:
                raise ValueError("learning.feature.run requires pool= and run=")
            pool_r = self._resolve_pool(name, pool)
            r = self._vlab().op_run_new(pool=pool_r, observers=observers, run=run,
                                        bench=self._bench_alias(name), branch=branch, purpose="bench")
            alias = self._sub(name, f"featrun:{_uslug(run)}")
            key = self._mk(alias, f"[{alias}] feature run {run} on {pool_r} ({observers})",
                           {"concept": "bench_featrun", "bench": self._bench_alias(name), "run": run,
                            "pool": pool_r, "observers": observers, "status": "open",
                            "author": self._client(), "created_wall": round(time.time(), 3)})
            self._record(name, key, "featruns")
            self._link(alias, f"vision_run:{_uslug(run)}", "bench:references")
            return {"featrun": alias, "run": run, "pool": pool_r, "observers": r.get("observers")}
        return self._perform(name, "feature", "run",
                             {"pool": pool, "observers": observers, "run": run, "cast": cast,
                              "branch": branch}, _fn)

    def op_feature_execute(self, name: str, run: str = "", limit: Any = "",
                           chunk: Any = 100, cast: str = "") -> Dict[str, Any]:
        """[learning.feature.execute] Execute a feature run over the WHOLE pool.

        A41.2 (amended 2026-09-08) — a pool is finite and frozen and the op streams it with
        per-observation sentinels, so the whole-pool pass is the DEFAULT: with only `run=` the op
        streams the pool in `chunk`-sized batches (an internal tuning knob, default 100) until the pass
        is COMPLETE (`remaining == 0`) or the step's soft wall-clock budget is spent. It stays ONE
        `_perform` observation (the vlab line reports each chunk); on a spent budget it returns
        `complete=false` — the run is resumable (its sentinels persist), so the next daily rerun
        continues and NOTHING fails on slow/closed egress (deploy-autonomy §3.4). `limit=N` is a DEV
        knob only: run ONE bounded chunk (tests / interactive probing); it is never written into a
        shipped `.ak`."""
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            if not run:
                raise ValueError("learning.feature.execute requires run=")
            vl = self._vlab()
            # B2 (S2-k) — REUSE an identical earlier embedding across sweep conditions: a sweep runs many
            # conditions over the SAME frozen train pool with the SAME embedder (model_sha8); without
            # reuse each condition re-embeds all N items (~40 min). `reuse="1"` shares the existing
            # observation + feature atoms and registers this run's per-source sentinel + feature membrane
            # (vlab._register_reuse_coverage), so the seal probe reads remaining==0 and learning.train finds
            # the vectors — the condition then completes in seconds, not forty minutes.
            if str(limit).strip().isdigit():          # DEV knob: one bounded chunk (incl. limit=0 probe)
                ex = vl.op_run_execute(run=run, limit=limit, reuse="1")
                _rem = int(ex.get("remaining") or 0)
                return {"run": run, "chunks": 1, "observed": ex.get("observed"),
                        "skipped": ex.get("skipped"), "failed": ex.get("failed"),
                        "reused": ex.get("reused"), "remaining": _rem, "complete": _rem == 0}
            try:
                ch = max(1, int(chunk))
            except (TypeError, ValueError):
                ch = 100
            tot_obs = tot_fail = tot_reused = chunks = 0
            remaining = None
            complete = False
            while True:
                ex = vl.op_run_execute(run=run, limit=str(ch), reuse="1")
                chunks += 1
                _o, _f, _r = (int(ex.get("observed") or 0), int(ex.get("failed") or 0),
                              int(ex.get("reused") or 0))
                tot_obs += _o
                tot_fail += _f
                tot_reused += _r
                remaining = int(ex.get("remaining") or 0)
                if remaining == 0:
                    complete = True
                    break
                if _o == 0 and _f == 0 and _r == 0:   # no progress (stall guard; reuse counts as progress)
                    break
                if self._budget_exhausted():          # yield before the block's wall-clock share is spent
                    break
            logger.info("[bench] feature.execute %s run=%s chunks=%d observed=%d reused=%d failed=%d "
                        "remaining=%s complete=%s", self._bench_alias(name), run, chunks, tot_obs,
                        tot_reused, tot_fail, remaining, complete)
            # B1 §A3 — the pass stopped short of the pool on a spent wall-clock budget (it will resume in
            # a later chunk): actual diverged from the plan's "cover the whole pool", mint budget_chunked.
            if not complete:
                self._mint_deviation_for_run(name, run, "budget_chunked",
                                             {"run": run, "target": "remaining==0"},
                                             {"run": run, "remaining": remaining, "complete": False})
            return {"run": run, "chunks": chunks, "observed": tot_obs, "reused": tot_reused,
                    "failed": tot_fail, "remaining": remaining, "complete": complete}
        return self._perform(name, "feature", "execute",
                             {"run": run, "limit": limit, "chunk": chunk, "cast": cast}, _fn)

    @staticmethod
    def _budget_exhausted() -> bool:
        """A41.2 — has the enclosing JCL step's soft wall-clock deadline passed? The worker publishes
        it per step (from the block's `timeout_s`, which the driver sets from `max_wall_s /
        len(workflows)`). No step / no deadline ⇒ never exhausted (a plain CLI call runs to completion)."""
        try:
            from lib.akasha.api import jobs as _wsctx
            return _wsctx.budget_exhausted()
        except Exception:
            return False

    def _mint_deviation_for_run(self, name: str, run: str, kind: str, planned, actual) -> None:
        """B1 §A3 — mint a deviation for a bench RUN through the ONE deviation writer
        (WorkflowConcept._mint_deviation), resolving the run's `wf_branch` to its readable lineage via
        the sweep marker when it is a sweep branch. Best-effort — a deviation is a record, never a gate."""
        try:
            vl = self._vlab()
            _rb = (vl.meta("vision_run:%s" % _uslug(str(run))) or {}).get("wf_branch") or ""
            _lin = _rb
            if _rb:
                _sm = self._meta("wf:sweep:%s:%s" % (_uslug(name), _uslug(_rb))) or {}
                _lin = _sm.get("lineage") or _rb
            from lib.akasha.api.concepts import model as _model
            _model(self.session, "workflow").mint_deviation(
                name, self._bench_gid(name), _lin, 0, kind, planned, actual, exec_id=str(run))
        except Exception as exc:
            logger.debug("[deviation] run-mint skipped bench=%s run=%s kind=%s: %s", name, run, kind, exc)

    def _stamp_last_metrics(self, name: str, summary: Dict[str, Any]) -> None:
        """A41.5 — record the latest train/evaluate summary on the bench meta so the auto-run driver's
        run-end line can carry `corpus=/classes=/accuracy=` (read via _bench_last_metrics) without
        re-reading the metrics atom. Best-effort; never fails the op."""
        try:
            bk = self._key(self._bench_alias(name))
            if bk:
                self._set_meta(bk, "last_metrics", dict(summary))
        except Exception:
            pass

    # ── P0-a slice 2 piece 5 — versioned weights (§2.5) ──────────────────────────────
    def _versions_set(self, name: str, run: str) -> str:
        return "set:wb:%s:model:%s:versions" % (_uslug(name), _uslug(run))

    def _write_versioned_weights(self, name: str, run: str, model: Dict[str, Any]):
        """Write the trained head to an IMMUTABLE, hash-named file `head_<run>_<sha8>.json` under the run's
        artifact dir, publish it as a durable GENERATION (`model:<bench>:<run>`) and CAS the pointer to it.
        There is no mutable `head_<run>.json` beside it: a head is only ever a content-named file. Returns
        (versioned_path, sha, size, sha8, generation). The on-disk file is the truth the observer loads; the
        generation is the durable record. Degrades cleanly when no writer store is active (gen=None)."""
        from lib.akasha.api import learned as _lh
        adir = self._artifact_dir(run, name)
        tmp = os.path.join(adir, "head_%s.writing.json" % _uslug(run))
        sha, size = _lh.save(model, tmp)                    # writes the file and computes the content sha
        sha8 = sha[:8]
        ver = os.path.join(adir, "head_%s_%s.json" % (_uslug(run), sha8))
        if os.path.exists(ver):
            os.remove(tmp)                                  # the same head again: the immutable file stands
        else:
            os.replace(tmp, ver)
        gen = None
        try:
            from lib.akasha.api.process import active_store
            durable = active_store().get("durable")
            if durable is not None:
                with open(ver, "rb") as _wf:
                    blob = _wf.read()
                kind = "model:%s:%s" % (_uslug(name), _uslug(run))
                gen = durable.publish_generation(kind, blob)   # immutable, content-named
                cur = durable.resolve_generation(kind).get("generation")
                durable.cas_pointer(kind, cur, gen)            # move the pointer to this generation
        except Exception:
            gen = None
        return ver, sha, size, sha8, gen

    def _record_version(self, name: str, run: str, ver_path: str, sha: str, size: int,
                        sha8: str, gen) -> None:
        """Record ONE version atom (`model:ver:<b>:<run>:<sha8>`) + join the run's versions Set, so
        `@<sha8>` pins to this file, keep_versions can prune, and the version stack enumerates them."""
        vralias = "model:ver:%s:%s:%s" % (_uslug(name), _uslug(run), sha8)
        vk, _c, _o = self._mk_replace(
            vralias, "[%s] learned-head weights %s (%d bytes)" % (vralias, sha8, size),
            {"concept": "model_version", "bench": self._bench_alias(name), "run": run, "sha8": sha8,
             "weights_path": ver_path, "weights_sha256": sha, "weights_size": size, "generation": gen,
             "weights_present": True, "cronon": self._akasha_now(), "author": self._client()},
            compare_meta=("weights_sha256",))
        self._add_to_set(self._versions_set(name, run), vk)

    def _prune_versions(self, name: str, run: str) -> int:
        """keep_versions (bench meta; default = keep ALL) — after a new version lands, remove the OLDEST
        versioned weight FILES beyond the budget and stamp `weights_present=false` on their version
        atoms (the file is gone; the record stays for provenance). Returns the number pruned."""
        kv = self._bench_meta(name).get("keep_versions")
        try:
            kv = int(kv) if kv not in (None, "", "all") else 0
        except (TypeError, ValueError):
            kv = 0
        if kv <= 0:
            return 0
        vers = []
        for vk in self._members(self._versions_set(name, run)):
            vm = self._meta(self._alias(vk) or vk) or {}
            if vm.get("weights_present"):
                vers.append((vm.get("cronon") or 0, self._alias(vk) or vk, vm))
        vers.sort(reverse=True)                             # newest first
        pruned = 0
        for _c, valias, vm in vers[kv:]:
            p = vm.get("weights_path")
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
            self._set_meta(self._key(valias), "weights_present", False)
            logger.info("[bench] weights prune %s run=%s sha8=%s removed (keep_versions=%d)",
                        self._bench_alias(name), run, vm.get("sha8"), kv)
            pruned += 1
        return pruned

    def _weights_for(self, name: str, mm: Dict[str, Any], pin: str) -> str:
        """Resolve the weights file to load for a model: a `@<sha8>` PIN → that version's file (P0-a
        §2.5); otherwise the model's own `weights_path` (the current generation's file)."""
        if pin:
            vm = self._meta("model:ver:%s:%s:%s" % (
                _uslug(name), _uslug(str(mm.get("feature_run") or "")), pin)) or {}
            if vm.get("weights_path"):
                return vm["weights_path"]
        return mm.get("weights_path", "")

    def op_feature_seal(self, name: str, run: str = "", cast: str = "") -> Dict[str, Any]:
        """[learning.feature.seal] Seal a COMPLETE feature run (delegates to vlab.run.seal).

        A41.3 — a run is sealed only when its pass has covered the whole pool. `remaining` is read with
        a zero-cap probe (`op_run_execute(run, limit=0)` examines + counts, observes nothing); if any
        source is still uncovered the run is left OPEN and the step is still `ok` — a workflow may run
        seal every day and it seals on the day the pass completes, so the bench never stalls waiting for
        an operator. Re-sealing an already-sealed run is a no-op (no re-stamp)."""
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            if not run:
                raise ValueError("learning.feature.seal requires run=")
            alias = self._sub(name, f"featrun:{_uslug(run)}")
            if self._key(alias) and (self._meta(alias) or {}).get("status") == "sealed":
                return {"run": run, "sealed": True, "already": True}
            remaining = int((self._vlab().op_run_execute(run=run, limit="0") or {}).get("remaining") or 0)
            if remaining > 0:
                return {"run": run, "sealed": False, "reason": "incomplete", "remaining": remaining}
            try:
                self._vlab().op_run_seal(run=run)
            except Exception as exc:
                return {"run": run, "sealed": False, "note": str(exc)[:120]}
            if self._key(alias):
                self._set_meta(self._key(alias), "status", "sealed")
            return {"run": run, "sealed": True}
        return self._perform(name, "feature", "seal", {"run": run, "cast": cast}, _fn)

    def op_feature_spaces(self, name: str, run: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)
        try:
            return self._vlab().op_spaces(run=run)
        except Exception as exc:
            return {"spaces": [], "count": 0, "error": str(exc)[:120]}

    # ── observe family (Part D §2 T2/T6) ──────────────────────────────────────────────
    def op_observe(self, name: str, pool: str = "", observers: str = "litert",
                   run: str = "", chunk: Any = 100, cast: str = "", branch: str = "") -> Dict[str, Any]:
        """[learning.observe] The READING of a pool by a reading observer, as ONE observation:
        `vlab.run.new` + whole-pool `run.execute` (A41.2 loop — resumable, budget-yielding) +
        `run.seal`. This is the template's "observe → learn → observe again" step: T2 reads the target
        with the learning-free classifier (`observers=litert`, ImageNet labels a human can compare), T6
        reads the SAME target with the promoted learned head (`observers=plants_head_f1`, species). The
        target's labels are NEVER read here (they are the §6 answer key). `pool=role:target|role:train`
        resolves via the bench's role bindings (T1). Result `{run, observed, failed, remaining, complete,
        sealed}`; each observation joins `set:vlab:run:<run>:observations` (§4.1) and registers a source
        bridge (§4.2), so `source.trace` shows before/after per item."""
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            if not run:
                raise ValueError("learning.observe requires run=")
            rpool = self._resolve_pool(name, pool)
            if not rpool:
                raise ValueError("learning.observe requires pool= (or role:<role>)")
            vl = self._vlab()
            # D2-M §2 — stamp the bench + workflow-branch + purpose onto the run, so every observation
            # it mints carries them; §3 — reuse an identical earlier reading (e.g. the boot precompute)
            # instead of re-running the observer.
            vl.op_run_new(pool=rpool, observers=observers, run=run,
                          bench=self._bench_alias(name), branch=branch, purpose="bench")
            try:
                ch = max(1, int(chunk))
            except (TypeError, ValueError):
                ch = 100
            tot_obs = tot_fail = tot_deg = tot_reused = tot_reused_emb = chunks = 0
            tot_timing = {"t_fetch": 0.0, "t_embed": 0.0, "t_head": 0.0, "t_write": 0.0,
                          "t_observe": 0.0, "n": 0}   # S2-k3 — the observe cost split, summed over chunks
            remaining = None
            complete = False
            while True:
                ex = vl.op_run_execute(run=run, limit=str(ch), reuse="1")
                chunks += 1
                tot_obs += int(ex.get("observed") or 0)
                tot_fail += int(ex.get("failed") or 0)
                tot_deg += int(ex.get("degraded") or 0)
                tot_reused += int(ex.get("reused") or 0)
                tot_reused_emb += int(ex.get("reused_embeddings") or 0)   # S2-k2
                for _tk, _tv in (ex.get("timing") or {}).items():         # S2-k3
                    tot_timing[_tk] = tot_timing.get(_tk, 0.0) + float(_tv or 0.0)
                remaining = int(ex.get("remaining") or 0)
                if remaining == 0:
                    complete = True
                    break
                if (int(ex.get("observed") or 0) == 0 and int(ex.get("failed") or 0) == 0
                        and int(ex.get("reused") or 0) == 0):
                    break                                     # no progress (stall guard; reuse counts)
                if self._budget_exhausted():
                    break
            sealed = False
            if complete:
                try:
                    vl.op_run_seal(run=run)
                    sealed = True
                except Exception:
                    sealed = False
            # count the whole target so the log/answer key report `items=` (bounded — a frozen pool)
            items = len(self._vlab_pool_members(rpool))
            alias = self._sub(name, f"observerun:{_uslug(run)}")
            key = self._mk(alias, f"[{alias}] observation run {run} on {rpool} ({observers})",
                           {"concept": "bench_observerun", "bench": self._bench_alias(name), "run": run,
                            "pool": rpool, "observers": observers, "items": items, "branch": branch,
                            "observed": tot_obs, "failed": tot_fail, "degraded": tot_deg,
                            "reused": tot_reused, "remaining": remaining, "complete": complete,
                            "sealed": sealed, "author": self._client(), "created_wall": round(time.time(), 3)})
            self._record(name, key, "observeruns")
            self._link(alias, f"vision_run:{_uslug(run)}", "bench:references")
            logger.info("[bench] observe %s run=%s observer=%s items=%d observed=%d reused=%d "
                        "reused_embeddings=%d failed=%d degraded=%d remaining=%s complete=%s",
                        self._bench_alias(name), run, observers, items, tot_obs, tot_reused,
                        tot_reused_emb, tot_fail, tot_deg, remaining, complete)
            return {"run": run, "pool": rpool, "observers": observers, "items": items,
                    "observed": tot_obs, "reused": tot_reused, "reused_embeddings": tot_reused_emb,
                    "failed": tot_fail, "degraded": tot_deg,
                    "remaining": remaining, "complete": complete, "sealed": sealed,
                    "timing": {k: round(v, 3) for k, v in tot_timing.items()}}   # S2-k3
        return self._perform(name, "observe", "observe",
                             {"pool": pool, "observers": observers, "run": run, "chunk": chunk,
                              "cast": cast, "branch": branch}, _fn)

    def op_runs(self, name: str, branch: str = "", mode: str = "") -> Dict[str, Any]:
        """[learning.runs] The runs of the bench (D2-M §4.3) — read from `set:wb:<b>:runs`, one row per
        run with its coordinates + sizes {run, wf_branch, mode, purpose, observers, model_sha8s,
        observations, items, sealed, at_seq}, filterable by branch/mode, plus `diffs` = every stored
        `lens.compare` aggregate for this bench. All O(#runs) — no scan."""
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)
        balias = self._bench_alias(name)
        _tag = _uslug(balias[3:] if balias.startswith("wb:") else balias)   # set tag = bare bench name
        vl = self._vlab()
        rows = []
        # the run / diff index Sets live in the NUCLEUS (written by vlab / lens.compare), so read them
        # through the vlab concept (whose cortex unions the nucleus), not the bench's group core.
        for rk in vl.members("set:wb:%s:runs" % _tag):
            rm = vl.meta(vl.alias(rk)) or {}
            if not rm:
                continue
            if branch and rm.get("wf_branch") != branch:
                continue
            rmode = rm.get("mode", "execution")
            if mode == "execution" and rmode == "thought":
                continue
            if mode == "thought" and rmode != "thought":
                continue
            run = rm.get("run")
            observers = rm.get("observers") or []
            n_obs = len(vl.members("set:vlab:run:%s:observations" % _uslug(str(run))))
            # §2.8 — a run stamped `wf_branch=<materialised sweep branch>` also carries the sweep
            # COORDINATE: read the sweep marker (nucleus, via the vlab cortex union) and fill `branch`
            # (the full lineage `parent@pN/template@cond8`) + `cond8` (the condition digest). A static
            # (non-sweep) branch has no marker, so both stay None — the row still identifies the branch
            # by `wf_branch`.
            _wfb = rm.get("wf_branch") or ""
            _lineage = _cond8 = None
            if _wfb:
                _sm = vl.meta("wf:sweep:%s:%s" % (_tag, _uslug(_wfb))) or {}
                if _sm.get("concept") == "wf_sweep_branch":
                    _lineage = _sm.get("lineage")
                    _cond8 = _sm.get("cond8")
            rows.append({"run": run, "wf_branch": _wfb,
                         "branch": _lineage, "cond8": _cond8,
                         "mode": rmode, "purpose": rm.get("purpose"),
                         "observers": observers, "model_sha8s": rm.get("model_sha8s") or [],
                         "observations": n_obs,
                         "items": (n_obs // len(observers)) if len(observers) == 1 else None,
                         # B1-b — the run's cost, stamped on the run atom by vlab.run.execute (GUI §7).
                         "reused": rm.get("reused_count"), "wall_s": rm.get("wall_s"),
                         "sealed": rm.get("status") == "sealed", "at_seq": rm.get("cronon")})
        rows.sort(key=lambda r: r.get("at_seq") or 0, reverse=True)
        # M2-b — an old (pre-epoch, hyphen-aliased) diff and its new re-minted twin both land in the
        # bench diffs Set. Collapse to the NEWEST per (a, b) pair; the older aliases travel as
        # `superseded` so history is one hop away (never two competing rows for one comparison).
        _by_pair: Dict[tuple, list] = {}
        for dk in vl.members("set:wb:%s:diffs" % _tag):
            dm = vl.meta(vl.alias(dk)) or {}
            if not dm:
                continue
            _by_pair.setdefault((dm.get("a"), dm.get("b")), []).append((dk, dm))
        diffs = []
        for (pa, pb), entries in _by_pair.items():
            # newest = highest built_at_epoch, then highest atom cronon/at_seq (an epoch-less old atom
            # sorts below any epoch-keyed one).
            def _rank(e):
                m = e[1]
                return (m.get("built_at_epoch") or -1, m.get("cronon") or m.get("at_seq") or 0)
            entries.sort(key=_rank, reverse=True)
            dk, dm = entries[0]
            _dsum = {k: dm.get(k) for k in
                     ("items", "changed", "agree_a", "agree_b", "truth_known")}
            # R5 (maintainer decision) — `agree_a`/`agree_b` are COUNTS over labels, not labels; they are
            # the public evidence that learning happened (stage-1: agree_a=0 → agree_b=93), so a guest
            # SEES them. Only `truth_known` (and the per-item answer key, never in this summary) stays
            # withheld — truth_known=0 for a guest.
            if self._is_guest():
                _dsum["truth_known"] = 0
            # S1-a §1.4 — a stored diff is a DERIVED accelerator: flag it `stale` when its input Sets
            # have advanced past the epoch it was built at (a later observation was added to a run), so
            # the reader knows to regenerate rather than trust a superseded aggregate. O(members).
            _cur = self._diff_inputs_epoch(vl, dm.get("a"), dm.get("b"))
            _stale = _is_stale(dm.get("built_at_epoch"), _cur)
            diffs.append({"a": dm.get("a"), "b": dm.get("b"), "atom": vl.alias(dk),
                          "built_at_epoch": dm.get("built_at_epoch"), "artifact_id": dm.get("artifact_id"),
                          "stale": _stale, "superseded": [vl.alias(k) for k, _ in entries[1:]],
                          "summary": _dsum})
        diffs.sort(key=lambda d: (d.get("built_at_epoch") or -1), reverse=True)
        return {"bench": balias, "runs": rows, "count": len(rows), "diffs": diffs}

    def _diff_inputs_epoch(self, vl, a: str, b: str):
        """S1-a §1.4 — the current epoch of a stored diff's inputs = the MAX member coordinate across
        its two observation Sets (a later observation raises it). O(members); None when unknown."""
        hi = None
        for s in (a, b):
            if not s:
                continue
            for okey in vl._members(s):
                m = vl._meta(vl._alias(okey) or okey) or {}
                e = m.get("cronon")
                if e is None:
                    e = m.get("at_seq")
                try:
                    e = int(e) if e is not None else None
                except (TypeError, ValueError):
                    e = None
                if e is not None and (hi is None or e > hi):
                    hi = e
        return hi

    def _vlab_pool_members(self, pool: str) -> List[str]:
        try:
            return self._vlab()._pool_members(pool)
        except Exception:
            return []

    # ── train family (NEW) ────────────────────────────────────────────────────────────
    def op_train(self, name: str, run: str = "", space: str = "mobilenet", head: str = "logreg",
                 split: Any = 0.8, seed: str = "akasha", label_key: str = "label",
                 cast: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            from lib.akasha.api import learned as lh
            if not run:
                raise ValueError("learning.train requires run=")
            # S2-h — refuse an unknown head= instead of silently degrading to the centroid/majority mock
            # (which read as a real `ridge`/`linear` model). Only the implemented learner KINDS train.
            if head not in lh.KINDS:
                raise ValueError("unknown head='%s' — learning.train learner kinds are %s" %
                                 (head, ", ".join(lh.KINDS)))
            vl = self._vlab()
            # A41.5 — the learner trains on a COMPLETE corpus: refuse a run whose pass has not covered
            # the whole pool (remaining>0), so a partial corpus never silently becomes a model. A
            # zero-cap probe counts without observing. A run sealed by feature.seal (or fully covered by
            # a one-shot feature.extract) has remaining=0 and trains.
            _rem = int((vl.op_run_execute(run=run, limit="0") or {}).get("remaining") or 0)
            if _rem > 0:
                raise ValueError(f"run '{run}' is not sealed (remaining={_rem}) — the learner trains "
                                 f"on a complete, frozen corpus")
            vecs = vl._space_vectors(run, space)          # {source_alias: [floats]}
            if not vecs:
                raise ValueError(f"no features for run='{run}' space='{space}' — run "
                                 f"learning.feature.extract first")
            # A34(b) — the join is declared on the DATA: the pool's `label_field` is tried FIRST, then
            # any explicit label_key, then the label/symbol fallbacks. A workflow needs no label_key.
            cand = self._pool_label_fields(name) + ([label_key] if label_key else [])
            labeled: List[Tuple[str, List[float], str]] = []
            for src, vec in vecs.items():
                lab = self._source_label(src, cand)
                if lab and vec:
                    labeled.append((src, [float(x) for x in vec], lab))
            classes = sorted({r[2] for r in labeled})
            # A40(b) — record WHICH candidate field actually resolved the labels, so evaluate/promote on
            # a fresh VPS (where the pool's label_field re-stamp may not have reached this dispatch yet)
            # can resolve the SAME way from the model itself, not only from the pool's label_fields.
            used_key = None
            if labeled:
                _fs = labeled[0][0]
                used_key = next((c for c in cand if self._source_label(_fs, [c])), None)
            if len(labeled) < 2 or len(classes) < 2:
                # A34(e) — name what the learner actually saw so the failure is diagnosable in one line.
                raise ValueError(
                    "need ≥2 labeled feature vectors across ≥2 classes to train "
                    f"(got {len(labeled)} vectors, {len(classes)} classes; "
                    f"{len(vecs)} feature vectors present; label keys tried={cand + ['label', 'symbol']}; "
                    f"source_metadata fields seen={self._sm_fields_seen(list(vecs.keys()))})")
            try:
                ratio = float(split)
            except (TypeError, ValueError):
                ratio = 0.8
            train, test = self._split(labeled, ratio, seed)
            corpus_sha = _sha8_list([r[0] for r in labeled])
            _, _tr_new = self._freeze_sample(name, run, "train", [r[0] for r in train], seed, ratio, corpus_sha)
            _, _te_new = self._freeze_sample(name, run, "test", [r[0] for r in test], seed, ratio, corpus_sha)
            # A49(9) — the frame's provenance: whether this train froze a NEW corpus or re-used one.
            logger.info("[bench] frame %s train n=%d test n=%d corpus_sha=%s (%s)",
                        self._bench_alias(name), len(train), len(test), corpus_sha,
                        "new" if (_tr_new or _te_new) else "unchanged")
            model = lh.fit([r[1] for r in train], [r[2] for r in train], kind=head, seed=0)
            # weights artifact — OUTSIDE the store, now VERSIONED (P0-a §2.5): an immutable
            # head_<run>_<sha8>.json + a durable generation (CAS pointer); `weights_path` IS that file.
            wpath, sha, size, sha8, gen = self._write_versioned_weights(name, run, model)
            self._record_version(name, run, wpath, sha, size, sha8, gen)
            self._prune_versions(name, run)
            world = self._bench_meta(name).get("world") or "default"
            tick = self._world().op_tick(reason="env", ref=self._bench_alias(name), world=world)
            malias = f"model:learned:{_uslug(name)}_head:{_uslug(run)}"
            mkey = self._identity_atom(malias, {
                "concept": "vision_model", "kind": "classifier", "family": "learned",
                "variant": "learned", "version": _uslug(run), "engine": model["engine"], "algo": head,
                "feature_space": space, "base_space": space, "classes": classes,
                "label_key": used_key,          # A40(b) — the field the labels were resolved through
                "weights_path": wpath, "weights_sha256": sha, "weights_size": size,
                "weights_sha8": sha8,   # P0-a §2.5
                "weights_generation": gen, "weights_present": True,
                "feature_run": run, "bench": self._bench_alias(name),
                "train_n": len(train), "test_n": len(test), "corpus_sha": corpus_sha,   # A46(3) provenance
                "trained_cronon": tick.get("cronon"), "trained_wall": round(time.time(), 3),
                "author": self._client(), "content": f"[{malias}] learned head ({model['engine']})"})
            self._record(name, mkey, "models")
            self._link(malias, self._sub(name, f"sample:train:{_uslug(run)}"), "bench:trained_on")
            # metrics on the TEST frame — ONE aggregate atom (R5). A46(3) — keyed by the model KEY it
            # measures and REPLACE-on-change (not idempotent-by-alias), so a re-train's numbers replace
            # yesterday's instead of the stale metrics atom lingering under the same alias.
            preds = lh.predict_batch(model, [r[1] for r in test]) if test else []
            m = lh.metrics([r[2] for r in test], preds, classes)
            metalias = self._sub(name, f"metrics:{_uslug(run)}")
            metkey, _mchg, _mold = self._mk_replace(
                metalias,
                f"[{metalias}] accuracy={m['accuracy']} macro_f1={m['macro_f1']} "
                f"(engine={model['engine']}, test n={m['n']}, model={mkey[:8]})",
                {"concept": "bench_metrics", "bench": self._bench_alias(name),
                 "model": malias, "model_key": mkey, "run": run, "frame": "test",
                 "corpus_sha": corpus_sha, "engine": model["engine"], **m, "author": self._client()},
                compare_meta=("model_key", "accuracy", "macro_f1", "n"))
            if _mold:
                self._link(metalias, _mold, "bench:superseded_by")
            self._record(name, metkey, "metrics")
            self._link(metalias, malias, "bench:metrics_of")
            self._link(metalias, self._sub(name, f"sample:test:{_uslug(run)}"), "bench:evaluated_on")
            logger.info("[bench] train %s run=%s n_labeled=%d classes=%d engine=%s "
                        "accuracy=%s macro_f1=%s", self._bench_alias(name), run, len(labeled),
                        len(classes), model["engine"], m["accuracy"], m["macro_f1"])
            # A41.5 — leave a compact summary on the bench so the driver's run-end line can carry
            # `corpus=/classes=/accuracy=` without re-reading the metrics atom.
            self._stamp_last_metrics(name, {"corpus": len(labeled), "classes": len(classes),
                                            "engine": model["engine"], "accuracy": m["accuracy"]})
            # A42 — the training tick is recorded on the world axis so the axis tells the learning
            # story (bench.trained → bench.evaluated → bench.promoted) without opening the stream.
            try:
                self._world().op_env_record(
                    kind="bench.trained", ref=malias, world=world,
                    note=f"corpus={len(labeled)} classes={len(classes)} engine={model['engine']} "
                         f"accuracy={m['accuracy']}")
            except Exception:
                pass
            return {"model": malias, "metrics": metalias, "engine": model["engine"],
                    "accuracy": m["accuracy"], "macro_f1": m["macro_f1"], "n_labeled": len(labeled),
                    "train_n": len(train), "test_n": len(test), "classes": classes}
        return self._perform(name, "train", "train",
                             {"run": run, "space": space, "head": head, "split": split,
                              "seed": seed, "cast": cast}, _fn)

    # ── evaluate family (NEW) ──────────────────────────────────────────────────────────
    def op_evaluate(self, name: str, model: str = "", sample: str = "test",
                    cast: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            from lib.akasha.api import learned as lh
            if not model:
                raise ValueError("learning.evaluate requires model=")
            # P0-a §2.5 — a `model:…@<sha8>` reference PINS a specific weights version; the base alias
            # (before the @) resolves the identity atom, the pin selects the versioned file to load.
            _pin = ""
            _model_ref = model
            if "@" in model:
                _model_ref, _pin = model.split("@", 1)
            mm = self._meta(_model_ref)
            if not mm:
                raise ValueError(f"unknown model '{_model_ref}'")
            head = lh.load(self._weights_for(name, mm, _pin))
            degraded = head is None
            if head is None:                                   # weights gone → honest degradation
                head = {"engine": "mock", "classes": mm.get("classes") or ["unknown"],
                        "params": {"majority": (mm.get("classes") or ["unknown"])[0]}}
            run, space = mm.get("feature_run"), mm.get("feature_space")
            classes = mm.get("classes") or []
            # resolve the frame: a frozen sample alias, or the run's train/test sample
            sid = sample if str(sample).startswith("wb:") else self._sub(name, f"sample:{sample}:{_uslug(run)}")
            frame_meta = self._meta(sid) or {}
            members = frame_meta.get("members") or []
            # A46(3) — refuse a frame that does NOT belong to this model's corpus: its `run` must match
            # the model's `feature_run` and its `corpus_sha` (when both carry one) must agree, so a stale
            # frame frozen from a different (smaller) corpus can never be scored against a newer model.
            _mcs, _fcs = mm.get("corpus_sha"), frame_meta.get("corpus_sha")
            if frame_meta and frame_meta.get("run") not in (None, run):
                raise ValueError(f"frame '{sample}' is from run '{frame_meta.get('run')}', not the "
                                 f"model's feature_run '{run}' — evaluate on the model's own frame")
            if _mcs and _fcs and _mcs != _fcs:
                raise ValueError(f"frame '{sample}' corpus_sha={_fcs} does not match the model's "
                                 f"corpus_sha={_mcs} — the frame is from a different (stale) corpus")
            vecs = self._vlab()._space_vectors(run, space)
            # A34(b)/A40(b) — the SAME data-declared resolver as train, but the model's OWN recorded
            # `label_key` comes FIRST: a model trained this run knows the field its labels came through,
            # so evaluate resolves even if the pool's label_field re-stamp has not reached this dispatch.
            cand = ([mm.get("label_key")] if mm.get("label_key") else []) + self._pool_label_fields(name)
            y_true, y_pred = [], []
            for src in members:
                vec = vecs.get(src)
                lab = self._source_label(src, cand)
                if vec and lab:
                    y_true.append(lab)
                    y_pred.append(lh.predict(head, [float(x) for x in vec])[0])
            m = lh.metrics(y_true, y_pred, classes)
            model_key = self._key(_model_ref) or _model_ref
            metalias = self._sub(name, f"metrics:{_uslug(run)}:{_uslug(sample)}")
            # P0-a §2.4 — an evaluation is a first-class row a sweep leaderboard ranks: carry the
            # coordinates (lineage branch + cond8 from the run atom, model_sha8, engine) and the S1-a
            # epoch keys (built_at_epoch + artifact_id) so it is epoch-comparable like lens.compare.
            _rmeta = self._vlab().meta("vision_run:%s" % _uslug(str(run))) or {}
            _branch = _rmeta.get("wf_branch") or ""
            _cond8 = _rmeta.get("cond8") or ""
            # a sweep branch carries its coordinate on a `wf:sweep:<bench>:<branch>` marker — read the
            # cond8 + the k=v bindings from it so this evaluation is faceted by the SAME condition Sets
            # (`set:wb:<b>:cond:<k>:<v>`) the sweep declared, and a leaderboard can select on them.
            _sbind: Dict[str, Any] = {}
            _sweep = ""
            if _branch:
                _smeta = self._meta("wf:sweep:%s:%s" % (_uslug(name), _uslug(_branch))) or {}
                _cond8 = _cond8 or (_smeta.get("cond8") or "")
                _sbind = _smeta.get("bindings") or {}
                _sweep = _smeta.get("sweep") or ""   # P0-a slice 2 — the sweep this branch belongs to
            _msha8 = str(mm.get("weights_sha256") or mm.get("sha256") or "")[:8] or None
            _epoch = self._akasha_now()
            _aid = _artifact_id(_epoch, "universal", _branch, [sid], "learning.evaluate", sample, "member")
            # A46(3) — REPLACE-on-change, keyed to the model KEY it measured, so a re-evaluation over a
            # superseded model's frame does not leave yesterday's numbers under the same alias.
            metkey, _echg, _eold = self._mk_replace(
                metalias,
                f"[{metalias}] accuracy={m['accuracy']} macro_f1={m['macro_f1']} (model={model_key[:8]})",
                {"concept": "bench_metrics", "bench": self._bench_alias(name),
                 "model": _model_ref, "model_key": model_key, "run": run, "branch": _branch, "cond8": _cond8,
                 "model_pin": _pin or None, "weights_sha8": _msha8,
                 "model_sha8": _msha8, "engine": head.get("engine"), "frame": sample,
                 "corpus_sha": _fcs, "degraded": degraded, "built_at_epoch": _epoch, "artifact_id": _aid,
                 "cronon": _epoch, "at_seq": _epoch, **m, "author": self._client()},
                compare_meta=("model_key", "accuracy", "macro_f1", "n"))
            if _eold:
                self._link(metalias, _eold, "bench:superseded_by")
                # B1 §A3 — a re-run with the SAME bindings produced an evaluation whose `artifact_id`
                # DIFFERS from the previous one on this branch (the metrics atom was replaced, not a
                # no-op): result_drift. An identical re-run is a _mk_replace no-op (_eold is None) and
                # mints nothing.
                if _branch:
                    _old_aid = (self._meta(self._alias(_eold) or _eold) or {}).get("artifact_id")
                    self._mint_deviation_for_run(name, run, "result_drift",
                                                 {"artifact_id": _old_aid}, {"artifact_id": _aid})
            self._record(name, metkey, "metrics")
            # P0-a §2.4 — the evaluation joins the bench's evaluations Set (lens.rank / leaderboard read it)
            self._add_to_set("set:wb:%s:evaluations" % _uslug(name), metkey)
            # …and the sweep's condition Sets, so `lens.rank set=…:evaluations within=…:cond:<k>:<v>`
            # facets by any bound parameter in pure set algebra.
            for _k, _v in _sbind.items():
                self._add_to_set("set:wb:%s:cond:%s:%s" % (_uslug(name), _uslug(_k), _uslug(str(_v))), metkey)
            # P0-a slice 2 — file the evaluation under its sweep, so sweep.leaderboard ranks exactly the
            # sweep's rows (set:wb:<b>:sweep:<sweep>:evaluations) and sweep.status can derive `done`.
            if _sweep:
                self._add_to_set("set:wb:%s:sweep:%s:evaluations" % (_uslug(name), _uslug(_sweep)), metkey)
                # S2-l — the leaderboard is DERIVED state (R0): rebuild it the moment a sweep evaluation
                # joins the Set, in THIS write path (one lens.rank + one _mk_replace; the artifact_id
                # makes a no-change rebuild a no-op). The trigger is the evaluation landing, never an
                # operator command. Best-effort — a leaderboard failure never fails the evaluation.
                try:
                    from lib.akasha.api.concepts import model as _model
                    _model(self.session, "sweep").build_leaderboard(bench=name, name=_sweep)
                except Exception as _lbexc:
                    logger.debug("[bench] leaderboard rebuild skipped for %s/%s: %s", name, _sweep, _lbexc)
            self._link(metalias, _model_ref, "bench:metrics_of")
            if self._key(sid):
                self._link(metalias, sid, "bench:evaluated_on")
            # A37/A49(11) — evaluate reports its held-out frame WITH provenance (corpus_sha + model_sha),
            # so a stale frame/model mismatch is visible in the log.
            logger.info("[bench] evaluate %s model=%s frame=%s n=%d classes=%d engine=%s "
                        "accuracy=%s macro_f1=%s corpus_sha=%s model_sha=%s%s",
                        self._bench_alias(name), model, sample, m["n"], len(classes),
                        head.get("engine"), m["accuracy"], m["macro_f1"], _fcs or "?", model_key[:8],
                        " (degraded)" if degraded else "")
            # A42 — record the evaluation on the world axis (bench.evaluated), so the axis carries the
            # held-out result alongside bench.trained / bench.promoted.
            try:
                _world = self._bench_meta(name).get("world") or "default"
                self._world().op_env_record(
                    kind="bench.evaluated", ref=metalias, world=_world,
                    note=f"frame={sample} n={m['n']} accuracy={m['accuracy']} macro_f1={m['macro_f1']}")
            except Exception:
                pass
            return {"metrics": metalias, "model": model, "frame": sample, "degraded": degraded,
                    "accuracy": m["accuracy"], "macro_f1": m["macro_f1"], "n": m["n"]}
        return self._perform(name, "evaluate", "evaluate",
                             {"model": model, "sample": sample, "cast": cast}, _fn)

    # ── promote family (NEW) ───────────────────────────────────────────────────────────
    def op_promote(self, name: str, model: str = "", observer: str = "",
                   cast: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            if not model:
                raise ValueError("learning.promote requires model=")
            mm = self._meta(model)
            if not mm:
                raise ValueError(f"unknown model '{model}'")
            oid = _uslug(observer) or f"{_uslug(name)}_head"
            model_key = self._key(model) or model
            # A46(4) — idempotent by the model KEY it points at, NOT the alias: a re-train supersedes the
            # model atom (same alias, NEW key), so a plain alias compare would wrongly report `already`
            # and leave the learned observer carrying yesterday's head. Compare the KEY: a superseded
            # model is a NEW promotion.
            # D2-M M6 — TWO fingerprints exist for one head: the model IDENTITY-ATOM key (a content hash
            # of the identity atom, `model_key[:8]`) and the WEIGHTS sha8 (`weights_sha256[:8]`, the model
            # file the observer actually loads). The observations, `vlab.item`, `versions` and
            # `learning.runs` all key on the WEIGHTS sha8 (`_obs_sha8`), so the promote log prints THAT too —
            # one number the operator can match across the log and the reads (the atom key stays in
            # `bench.info` only).
            _wsha8 = str(mm.get("weights_sha256") or "")[:8] or "nomodel"
            ralias = self._sub(name, f"promotion:{oid}")
            if self._key(ralias) and (self._meta(ralias) or {}).get("model_key") == model_key:
                logger.info("[bench] promote unchanged %s model_sha8=%s observer=%s",
                            self._bench_alias(name), _wsha8, oid)   # A49(10)
                return {"observer": oid, "model": model, "already": True,
                        "base_space": mm.get("base_space"), "classes": mm.get("classes") or []}
            # D2-M M5 — the held-out accuracy the version stack shows (`vlab.item.versions.accuracy`)
            # is the `evaluate` aggregate of the run this model was TRAINED on. Read it from the stored
            # test-frame metrics atom (`metrics:<feature_run>:test`) and carry it onto the learned
            # record, so a freshly-reconstructed observer's config has the number (the roster already
            # passes `accuracy` through) and the accuracy is not re-computed client-side.
            _acc = _mf1 = None
            _fr = mm.get("feature_run")
            if _fr:
                _mtest = self._meta(self._sub(name, f"metrics:{_uslug(str(_fr))}:test")) or {}
                _acc = _mtest.get("accuracy")
                _mf1 = _mtest.get("macro_f1")
            # The promotion record lives in the NUCLEUS so a fresh VisionLabConcept roster (one per
            # dispatch) rediscovers the learned observer. It carries everything the observer needs to
            # load the head + embed in the base space; the weights file stays OUTSIDE the store.
            palias = f"vlab:learned:{oid}"
            pkey, _pchg, _pold = self._nucleus_replace(
                palias, f"[{palias}] learned observer {oid} ← {model} ({model_key[:8]})",
                {"concept": "vlab_learned", "observer": oid, "model": model, "model_key": model_key,
                 "model_alias": mm.get("family") and
                 f"model:learned:learned:{mm.get('version', '0')}" or model,
                 "weights_path": mm.get("weights_path"),
                 # D2-M §1/§4.2 — carry the model fingerprint + provenance on the learned observer so a
                 # freshly-reconstructed observer stamps a real model_sha8 onto its observations (no
                 # cross-space model-atom lookup) and vlab.item.versions can show engine/accuracy.
                 "weights_sha256": mm.get("weights_sha256"), "weights_size": mm.get("weights_size"),
                 "engine": mm.get("engine"), "feature_run": mm.get("feature_run"),
                 "accuracy": _acc, "macro_f1": _mf1,       # M5 — the held-out figure for the version stack
                 "base_space": mm.get("base_space") or mm.get("feature_space"),
                 "classes": mm.get("classes") or [], "bench": self._bench_alias(name),
                 "promoted_wall": round(time.time(), 3)},
                compare_meta=("model_key",))
            self._nucleus_add(LEARNED_OBSERVERS_SET, pkey)
            # a bench-side record + the provenance link model → observer (replace-on-change; old kept)
            rkey, _rchg, _rold = self._mk_replace(
                ralias, f"[{ralias}] {model} promoted as observer {oid} ({model_key[:8]})",
                {"concept": "bench_promotion", "bench": self._bench_alias(name),
                 "model": model, "model_key": model_key, "observer": oid, "author": self._client(),
                 "promoted_wall": round(time.time(), 3)},
                compare_meta=("model_key",))
            if _rold:
                self._link(ralias, _rold, "bench:superseded_by")
            self._record(name, rkey, "promotions")
            self._link(model, palias, "bench:promoted_as")
            _classes = mm.get("classes") or []
            # A42 — promote is no longer invisible: an INFO line + a world-axis record so the promotion
            # appears in the log and on `world.axis` (bench.trained → bench.evaluated → bench.promoted).
            logger.info("[bench] promote %s model_sha8=%s model=%s observer=%s base_space=%s classes=%d",
                        self._bench_alias(name), _wsha8, model, oid, mm.get("base_space"), len(_classes))
            try:
                _world = self._bench_meta(name).get("world") or "default"
                self._world().op_env_record(
                    kind="bench.promoted", ref=ralias, world=_world,
                    note=f"{model} → observer {oid} (classes={len(_classes)})")
            except Exception:
                pass
            return {"observer": oid, "model": model, "base_space": mm.get("base_space"),
                    "classes": _classes}
        return self._perform(name, "promote", "promote",
                             {"model": model, "observer": observer, "cast": cast}, _fn)
