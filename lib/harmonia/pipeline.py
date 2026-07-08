"""
I/O pipeline interface — the Unix-pipe of Akasha's data plane.

Any data endpoint (a file, a `table`, a set of atoms, a future web upload, a network stream)
is either a **Source** (produces a `Stream`) or a **Sink** (consumes one). `run_pipeline`
connects a source to a sink — `source | transforms… | sink` — so every combination works
through one interface:

    file  → table      import a CSV/JSON into the concept model   (FileSource   → TableSink)
    table → file       export a table to a CSV/JSON/MD file       (TableSource  → FileSink)
    upload→ table      a web upload projected into a model         (InlineSource → TableSink)
    set   → file       dump a set of atoms to a file              (SetSource    → FileSink)
    file  → atom       index a document                           (FileSource   → DocSink)

The interchange currency is `Stream` — structured records (`kind="table"`) or a document
(`kind="doc"`) — the pipeline's equivalent of a byte stream. Endpoints are wired by
dependency injection (callables/objects passed in), so this module stays graph-agnostic: it
imports nothing from `akasha`, exactly like a pipe knows nothing about the programs it joins.
"""
from typing import Any, Callable, Dict, Iterable, List, Optional

from lib.harmonia.fileio import FileIO


class Stream:
    """The unit of flow between a Source and a Sink: a table (columns + row dicts) or a
    document (text + title). `meta` carries endpoint hints (e.g. a pre-rendered CSV, the
    origin path); `origin` is a human label for provenance/reporting."""
    TABLE = "table"
    DOC = "doc"

    def __init__(self, kind: str, columns: Optional[List[str]] = None,
                 rows: Optional[Iterable[dict]] = None, text: str = "",
                 title: Optional[str] = None, meta: Optional[dict] = None,
                 origin: Optional[str] = None):
        self.kind = kind
        self.columns = list(columns or [])
        self.rows = list(rows or [])
        self.text = text or ""
        self.title = title
        self.meta = meta or {}
        self.origin = origin

    @classmethod
    def table(cls, columns, rows, **kw) -> "Stream":
        return cls(cls.TABLE, columns=columns, rows=rows, **kw)

    @classmethod
    def doc(cls, text, title=None, **kw) -> "Stream":
        return cls(cls.DOC, text=text, title=title, **kw)

    def to_payload(self) -> Dict[str, Any]:
        """FileIO-shaped payload for serialization."""
        if self.kind == self.TABLE:
            return {"columns": self.columns, "rows": self.rows}
        return {"text": self.text, "title": self.title}

    def csv(self) -> str:
        """A CSV rendering of a table stream (uses a pre-rendered one if the source gave it)."""
        return self.meta.get("csv") or FileIO.serialize(self.to_payload(), "csv")


class Source:
    def read(self) -> Stream:
        raise NotImplementedError


class Sink:
    def write(self, stream: Stream) -> Dict[str, Any]:
        raise NotImplementedError


def run_pipeline(source: Source, sink: Sink,
                 transforms: Iterable[Callable[[Stream], Stream]] = ()) -> Dict[str, Any]:
    """Move one Stream from `source` through `transforms` into `sink`. Returns the sink's
    result dict, annotated with the origin. Endpoints raise on their own errors (path denied,
    table missing, …); the caller maps those to RPC errors."""
    stream = source.read()
    for t in transforms:
        stream = t(stream)
    result = sink.write(stream) or {}
    if stream.origin and "source" not in result:
        result["source"] = stream.origin
    result.setdefault("kind", stream.kind)
    return result


# ── File endpoints (wrap the path-safe FileIO) ───────────────────────────────────────────
class FileSource(Source):
    def __init__(self, fileio: FileIO, path: str, fmt: Optional[str] = None):
        self.fileio, self.path, self.fmt = fileio, path, fmt

    def read(self) -> Stream:
        kind, payload = self.fileio.read(self.path, self.fmt)
        if kind == "table":
            return Stream.table(payload["columns"], payload["rows"],
                                meta={"csv": payload.get("csv")}, origin=self.path)
        return Stream.doc(payload["text"], payload.get("title"), origin=self.path)


class FileSink(Sink):
    def __init__(self, fileio: FileIO, path: str, fmt: Optional[str] = None):
        self.fileio, self.path, self.fmt = fileio, path, fmt

    def write(self, stream: Stream) -> Dict[str, Any]:
        return self.fileio.write(self.path, stream.to_payload(), self.fmt)


class InlineSource(Source):
    """A non-file source: already-in-memory content (a web upload, a network payload). Same
    interface as FileSource, no disk. This is how a future Web GUI plugs in unchanged."""
    def __init__(self, raw: str, fmt: str, name: str = "upload"):
        self.raw, self.fmt, self.name = raw, fmt, name

    def read(self) -> Stream:
        kind, payload = FileIO.parse_text(self.raw, self.fmt, name=self.name)
        if kind == "table":
            return Stream.table(payload["columns"], payload["rows"],
                                meta={"csv": payload.get("csv")}, origin=self.name)
        return Stream.doc(payload["text"], payload.get("title"), origin=self.name)


# ── Graph endpoints (dependency-injected — no akasha import) ──────────────────────────────
class TableSink(Sink):
    """Project a table Stream into the `table` concept model. `dispatch(method, data)` is a
    caller-bound wrapper over the concept registry (session + rid already bound)."""
    def __init__(self, dispatch: Callable[[str, dict], dict], name: str):
        self.dispatch, self.name = dispatch, name

    def write(self, stream: Stream) -> Dict[str, Any]:
        if stream.kind != Stream.TABLE:
            raise ValueError("TableSink requires a table stream")
        cols = ",".join(c for c in stream.columns if c)
        if not cols:
            raise ValueError("no columns to import")
        self.dispatch("table.new",
                      {"name": self.name, "cols": cols,
                       "description": f"imported via pipeline from {stream.origin or 'source'}"})
        r = self.dispatch("table.import", {"table": self.name, "csv": stream.csv()}) or {}
        res = r.get("result") or r.get("error") or {}
        return {"kind": "table", "table": self.name, "columns": stream.columns,
                "imported": res.get("imported"), "errors": res.get("errors")}


class TableSource(Source):
    def __init__(self, dispatch: Callable[[str, dict], dict], name: str):
        self.dispatch, self.name = dispatch, name

    def read(self) -> Stream:
        exp = self.dispatch("table.export", {"table": self.name}) or {}
        r = exp.get("result") or {}
        if "csv" not in r:
            raise ValueError((exp.get("error") or {}).get("message", f"table '{self.name}' not found"))
        _, payload = FileIO.parse_text(r["csv"], "csv", name=f"{self.name}.csv")
        return Stream.table(payload["columns"], payload["rows"],
                            meta={"csv": r["csv"]}, origin=f"tbl:{self.name}")


class DocSink(Sink):
    """Index a document Stream as an atom. `write_atom(text, meta, scopes) -> key`,
    `add_to_set(name, key)`, `weave(key, text)` are caller-bound."""
    def __init__(self, write_atom: Callable, add_to_set: Callable, weave: Callable,
                 client_id: str, set_name: str):
        self.write_atom, self.add_to_set, self.weave = write_atom, add_to_set, weave
        self.client_id, self.set_name = client_id, set_name

    def write(self, stream: Stream) -> Dict[str, Any]:
        text = stream.text
        if not text.strip():
            raise ValueError("empty document")
        title = stream.title or (stream.origin or "document")
        scopes = [f"owner:user_{self.client_id}", f"view:user_{self.client_id}", "provenance:file"]
        key = self.write_atom(text, {"type": "document", "provenance": "file",
                                     "source": stream.origin, "title": title}, scopes)
        try:
            self.add_to_set(self.set_name, key)
        except Exception:
            pass
        self.weave(key, text)
        return {"kind": "doc", "atom_key": key, "title": title, "chars": len(text)}


class SetSource(Source):
    """Read a set of atoms as a two-column (key, content) table Stream."""
    def __init__(self, list_members: Callable[[], list], get_content: Callable[[str], str],
                 set_name: str):
        self.list_members, self.get_content, self.set_name = list_members, get_content, set_name

    def read(self) -> Stream:
        rows = []
        for m in (self.list_members() or []):
            mk = m if isinstance(m, str) else m.get("key")
            if mk:
                rows.append({"key": mk, "content": self.get_content(mk) or ""})
        return Stream.table(["key", "content"], rows, origin=f"set:{self.set_name}")


class ResponseSink(Sink):
    """Return the serialised content in the result instead of writing a file — the client
    'receive' path: a session asks for a table/set and gets CSV/JSON/MD bytes back to save
    locally. No disk write; the mirror of InlineSource (the upload path)."""
    def __init__(self, fmt: str):
        self.fmt = fmt

    def write(self, stream: Stream) -> Dict[str, Any]:
        text = FileIO.serialize(stream.to_payload(), self.fmt)
        return {"kind": stream.kind, "format": self.fmt, "content": text,
                "bytes": len(text.encode("utf-8")), "rows": len(stream.rows)}


# ── Concept-model projection endpoints (base: lens scan + cast) ───────────────────────────
# The general "project into ANY concept model" path routes through lens: scan an in-graph
# source into candidate models, then cast the scanned nodes into one. These endpoints wrap
# that as a pipe. The base is model-agnostic; today only `table` implements the Importable
# contract, so table is the one working target (other models are a per-model follow-up).
# lens.cast consumes the nodes the paired scan staged in the session, so LensScanSource and
# ConceptCastSink must share a session (run_pipeline runs them in sequence, which they do).
class LensScanSource(Source):
    """Scan an in-graph source (a set name, or an atom/alias tree root) via lens.scan. The
    Stream carries the candidate models; the scan also stages nodes in the session for a
    downstream ConceptCastSink. `dispatch(method, data)` is the caller-bound registry call."""
    def __init__(self, dispatch: Callable[[str, dict], dict], src: str, depth: int = 2):
        self.dispatch, self.src, self.depth = dispatch, src, depth

    def read(self) -> Stream:
        r = self.dispatch("lens.scan", {"src": self.src, "depth": self.depth}) or {}
        if "result" not in r:
            raise ValueError((r.get("error") or {}).get("message", "lens.scan failed"))
        res = r["result"] or {}
        cands = res.get("candidates") or []
        rows = [{"candidate": i + 1, "model": c.get("model"), "score": c.get("score")}
                for i, c in enumerate(cands)]
        return Stream(Stream.TABLE, columns=["candidate", "model", "score"], rows=rows,
                      meta={"scanned": True, "candidates": [c.get("model") for c in cands]},
                      origin=f"lens:{self.src}")


class ConceptCastSink(Sink):
    """Cast the current lens scan into a concept model (lens.cast). Works for any model that
    implements the Importable contract — currently `table`. `into` names the target."""
    def __init__(self, dispatch: Callable[[str, dict], dict], model: str = "table",
                 into: Optional[str] = None):
        self.dispatch, self.model, self.into = dispatch, model, into

    def write(self, stream: Stream) -> Dict[str, Any]:
        if not stream.meta.get("scanned"):
            raise ValueError("ConceptCastSink requires a LensScanSource upstream")
        if stream.meta.get("candidates") and self.model not in stream.meta["candidates"]:
            raise ValueError(
                f"model '{self.model}' is not a compatible target for this source "
                f"(candidates: {stream.meta['candidates']})")
        data = {"model": self.model}
        if self.into:
            data["into"] = self.into
        r = self.dispatch("lens.cast", data) or {}
        if "result" not in r:
            raise ValueError((r.get("error") or {}).get("message", "lens.cast failed"))
        res = r["result"] or {}
        return {"kind": "cast", "model": self.model,
                "into": res.get("into") or self.into, "cast": res}
