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

Contexa (the client session's INPUT side) and Jataka (its OUTPUT side) are pipe endpoints too
— Contexa reads the world in, Jataka presents a selection out, and Consciousness is the
substrate both flow THROUGH (auto-weave on input, generate_view on output), never a pipe end:

    web   → doc        fetch external content                     (ContexaWebSource → DocSink)
    responses→ survey  ingest answers with ctx-binding            (FileSource → ResponseIngestSink)
    survey→ table      aggregate + present per-question counts     (SurveyAggregateSource → PresentTableSink)
    set   → scatter    2-D points from cosmos_nd                   (SetSource → ScatterSink)
    focus → narrative  prose from generate_view (LLM-optional)     (InterpretationSource → NarrativeSink)

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


# ── Contexa endpoints — the client session's INPUT side ───────────────────────────────────
# Contexa reads the external world into the graph. As pipe endpoints it is a Source (external
# fetch → Stream) plus an ingest Sink that writes a response Stream into a concept model WITH
# Contexa's macro context-binding (ctx:answers / ctx:from / per-question set) layered on the
# structural links the concept model already writes. Consciousness is NOT a pipe endpoint: the
# graph writes here are auto-woven downstream (Weaver → Consciousness) — the substrate the
# client's input flows THROUGH, filled in without the client managing it.
class ContexaWebSource(Source):
    """Fetch external content (web / Wikipedia) as a document Stream. `fetch(query) ->
    {text,title,url,source_type,evidence}` is the caller-bound ContexaEngine.fetch closure."""
    def __init__(self, fetch: Callable[[str], dict], query: str):
        self.fetch, self.query = fetch, query

    def read(self) -> Stream:
        r = self.fetch(self.query) or {}
        if "error" in r:
            raise ValueError(r["error"])
        return Stream.doc(r.get("text", ""), r.get("title") or self.query,
                          meta={"url": r.get("url"), "source_type": r.get("source_type"),
                                "evidence": r.get("evidence"), "alias": r.get("alias")},
                          origin=f"contexa:{self.query[:40]}")


class ResponseIngestSink(Sink):
    """Consume a table Stream of survey responses and write each cell as a survey response
    WITH Contexa macro-binding. The survey model (`survey.ans` via `dispatch`) writes the
    structural tri-links; this Sink adds the dialogue/context layer on top — `bind(resp,
    question_key, respondent_key, set_names)` creates ctx:answers → question, ctx:from →
    respondent, and adds the response to the per-question set. That macro binding is Contexa's
    responsibility (the concept model owns structure; Contexa owns context).

    Column model: one `respondent_col` identifies the respondent (deduped by content-address);
    every column in `question_map` (column_name → question_id) is a question — its cell is the
    answer. Empty cells are skipped."""
    def __init__(self, dispatch: Callable[[str, dict], dict], bind: Callable,
                 survey_id: str, respondent_col: str, question_map: Dict[str, str]):
        self.dispatch, self.bind = dispatch, bind
        self.survey_id, self.respondent_col, self.question_map = \
            survey_id, respondent_col, question_map

    def _result(self, r: dict) -> dict:
        return (r or {}).get("result") or {}

    def write(self, stream: Stream) -> Dict[str, Any]:
        if stream.kind != Stream.TABLE:
            raise ValueError("ResponseIngestSink requires a table stream")
        if not self.question_map:
            raise ValueError("no question columns mapped for ingest")
        respondents = set()
        responses = errors = 0
        for row in stream.rows:
            label = str(row.get(self.respondent_col, "")).strip()
            if not label:
                continue
            r_atom = self._result(self.dispatch(
                "survey.res.add", {"respondent_id": label})).get("respondent_atom")
            if not r_atom:
                errors += 1
                continue
            respondents.add(r_atom)
            for col, q_id in self.question_map.items():
                answer = row.get(col)
                if answer is None or str(answer).strip() == "":
                    continue
                resp_id = self._result(self.dispatch(
                    "survey.ans",
                    {"question_id": q_id, "respondent_atom": r_atom, "answer": answer}
                )).get("response_id")
                if not resp_id:
                    errors += 1
                    continue
                # Contexa macro-binding (the context layer over the structural tri-links)
                self.bind(resp_id, question_key=q_id, respondent_key=r_atom,
                          set_names=[f"survey:{self.survey_id}:q:{q_id[:12]}"])
                responses += 1
        return {"kind": "survey_ingest", "survey": self.survey_id,
                "respondents": len(respondents), "responses": responses, "errors": errors}


# ── Jataka endpoints — the client session's OUTPUT side ───────────────────────────────────
# Jataka presents a graph selection to the world. As pipe endpoints it is a Source that reads
# the selection THROUGH the Consciousness substrate (a survey aggregate, or generate_view's
# interpretation) plus a Sink family that renders one presentation format. generate_view /
# cosmos_nd is where the output flows through Consciousness — the client asks "present this",
# the substrate supplies the interpretation the client did not compute.
class SurveyAggregateSource(Source):
    """Read a survey's responses aggregated per (question, answer) into a table Stream — the
    analysis result Jataka presents. Injected closures keep this graph-agnostic:
    `list_survey() -> survey.list result`, `get_meta(key) -> meta`, `get_content(key) -> str`."""
    def __init__(self, list_survey: Callable[[], dict],
                 get_meta: Callable[[str], dict], get_content: Callable[[str], str],
                 survey_id: str):
        self.list_survey, self.get_meta, self.get_content = list_survey, get_meta, get_content
        self.survey_id = survey_id

    def read(self) -> Stream:
        inv = self.list_survey() or {}
        q_text = {q: (self.get_content(q) or q) for q in inv.get("questions", [])}
        counts: Dict[tuple, int] = {}
        for resp in inv.get("responses", []):
            m = self.get_meta(resp) or {}
            qid = m.get("question_id")
            ans = m.get("answer")
            if ans is None:
                ans = self.get_content(resp) or ""
            qt = q_text.get(qid, qid or "?")
            counts[(qt, str(ans))] = counts.get((qt, str(ans)), 0) + 1
        rows = [{"question": q, "answer": a, "count": c}
                for (q, a), c in sorted(counts.items())]
        return Stream.table(["question", "answer", "count"], rows,
                            meta={"survey": self.survey_id,
                                  "total_responses": sum(counts.values())},
                            origin=f"survey:{self.survey_id}")


class InterpretationSource(Source):
    """Read Consciousness's interpretation of a focus atom (generate_view: signposts /
    resonance / cosmos_nd) into a Stream for a NarrativeSink. `view(focus) -> generate_view
    dict` is caller-bound. Optional `data_rows`/`data_columns` fold an analysis table (e.g. a
    survey aggregate) into the same stream so the narration can weave data + interpretation."""
    def __init__(self, view: Callable[[str], dict], focus: str,
                 data_rows: Optional[list] = None, data_columns: Optional[list] = None):
        self.view, self.focus = view, focus
        self.data_rows, self.data_columns = data_rows or [], data_columns or []

    def read(self) -> Stream:
        v = self.view(self.focus) or {}
        if "error" in v:
            raise ValueError(v["error"])
        title = (v.get("focus") or {}).get("alias") or self.focus
        return Stream(Stream.DOC, columns=self.data_columns, rows=self.data_rows,
                      title=title, meta={"view": v}, origin=f"view:{self.focus[:12]}")


class PresentTableSink(Sink):
    """Present a table Stream as structured output (columns + rows for a web/GUI render).
    With `fmt` (csv/json/md) it also serialises the table for client download — the mirror of
    an upload, on the output side."""
    def __init__(self, fmt: Optional[str] = None):
        self.fmt = fmt

    def write(self, stream: Stream) -> Dict[str, Any]:
        if stream.kind != Stream.TABLE:
            raise ValueError("PresentTableSink requires a table stream")
        out = {"kind": "present", "format": "table",
               "columns": stream.columns, "rows": stream.rows,
               "row_count": len(stream.rows)}
        if stream.meta.get("total_responses") is not None:
            out["total_responses"] = stream.meta["total_responses"]
        if self.fmt:
            out["content"] = FileIO.serialize(stream.to_payload(), self.fmt)
            out["serialized_as"] = self.fmt
        return out


class ScatterSink(Sink):
    """Present rows as 2-D scatter points positioned by the Consciousness substrate. Each row
    must carry a `key`; `coords(key) -> (x, y, label, color)` reads generate_view's cosmos_nd
    for that atom. Rows without a key or coordinates are skipped."""
    def __init__(self, coords: Callable[[str], Optional[tuple]]):
        self.coords = coords

    def write(self, stream: Stream) -> Dict[str, Any]:
        points = []
        for row in stream.rows:
            key = row.get("key")
            if not key:
                continue
            xy = self.coords(key)
            if not xy:
                continue
            x, y, label, color = xy
            points.append({"key": key, "x": x, "y": y, "label": label, "color": color})
        return {"kind": "present", "format": "scatter",
                "points": points, "count": len(points)}


def _narrate_template(view: dict, rows: list, columns: list) -> str:
    """Deterministic structural narration from a generate_view payload (+ optional data rows).
    This is the degradation floor: with no LLM the client still gets a readable summary woven
    from the interpretation the substrate produced. An LLM lifts it; it is never empty."""
    focus = view.get("focus") or {}
    name = focus.get("alias") or (focus.get("content") or "").split("\n")[0][:60] or "the focus"
    signposts = view.get("signposts") or []
    resonance = view.get("resonance") or []
    lines = [f"{name} sits at the centre of this reading."]
    if signposts:
        near = ", ".join(
            (sp.get("alias") or sp.get("preview") or sp.get("key", "")[:8]) + f" ({sp.get('rel')})"
            for sp in signposts[:5])
        lines.append(f"Directly connected: {near}.")
    if resonance:
        echoes = "; ".join((r.get("preview") or "").strip() for r in resonance[:4] if r.get("preview"))
        if echoes:
            lines.append(f"Further out, it resonates with: {echoes}.")
    if rows:
        top = sorted(rows, key=lambda r: r.get("count", 0), reverse=True)[:5]
        parts = []
        for r in top:
            if "question" in r and "answer" in r:
                parts.append(f"“{r['answer']}” to “{str(r['question'])[:40]}” (×{r.get('count', 0)})")
        if parts:
            lines.append("The gathered responses cluster around " + "; ".join(parts) + ".")
    if not signposts and not resonance and not rows:
        lines.append("The graph around it is still sparse — little has been woven in yet.")
    return " ".join(lines)


class NarrativeSink(Sink):
    """Present a focus as prose narration. Reads the interpretation the InterpretationSource
    carried (stream.meta['view'] = generate_view) plus any analysis rows, and renders text.
    Degradation-first: with no `llm` it emits `_narrate_template`; an injected
    `llm(prompt) -> str` lifts it to a generated narrative, falling back to the template on
    any error. Never empty — the substrate always yields a view."""
    def __init__(self, llm: Optional[Callable[[str], str]] = None):
        self.llm = llm

    def write(self, stream: Stream) -> Dict[str, Any]:
        view = stream.meta.get("view")
        if not view:
            raise ValueError("NarrativeSink requires an InterpretationSource upstream")
        template = _narrate_template(view, stream.rows, stream.columns)
        text, llm_used = template, False
        if self.llm:
            try:
                prompt = ("Narrate this knowledge-graph reading as a short, readable summary.\n"
                          f"Structural draft: {template}\n"
                          "Keep it faithful to the draft; do not invent facts.")
                generated = self.llm(prompt)
                if generated and generated.strip():
                    text, llm_used = generated.strip(), True
            except Exception:
                text, llm_used = template, False
        return {"kind": "present", "format": "narrative", "text": text,
                "focus": (view.get("focus") or {}).get("key"), "llm_used": llm_used}
