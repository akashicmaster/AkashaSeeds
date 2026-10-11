"""
The I/O pipe's ops (io.*, contexa.*, jataka.present, curation.project, pres.export, image.profile, web.search), moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

Every function takes the kernel (the heart) as its first argument: it is the object the
dispatcher / timer registry hands in, never imported. Bodies are the kernel's own, moved
verbatim except `self.` → `kernel.` and intra-family calls.
"""
import os
import re
import sys
import time
import json
import uuid
import logging
import hashlib
import functools
from typing import Dict, Any, Optional, List, Callable
try:
    from lib.harmonia.fileio import FileIO
    from lib.harmonia.infra import HarmoniaInfra
    from lib.harmonia.pipeline import (
        run_pipeline, FileSource, FileSink, InlineSource,
        TableSource, TableSink, DocSink, SetSource,
        LensScanSource, ConceptCastSink, ResponseSink,
        ContexaWebSource, ResponseIngestSink,
        SurveyAggregateSource, InterpretationSource,
        PresentTableSink, ScatterSink, NarrativeSink,
        CurationPathSource, PresentationSink, PresentationSceneSource, ExportSink,
    )
except ImportError:
    FileIO = None  # type: ignore
    HarmoniaInfra = None  # type: ignore
try:
    from lib.contexa.engine import ContexaEngine
except ImportError:
    ContexaEngine = None  # type: ignore
from lib.akasha.api.heart import _NucleusWriteCtx, _FEED_WRITER, _BROADCASTER
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha.source import bootstrap as _src_bootstrap, fetch as _src_fetch   # transitional (S3→S4/S5)
from lib.akasha.ontology import weave

from lib.akasha.concepts import registry as _registry_mod

logger = logging.getLogger("Akasha.Kernel")


def _vision_engine(kernel):
    """The vision engine, constructed on first use (it used to be built in the kernel's __init__; the
    constructor only records paths, so lazy construction is equivalent). None when unavailable."""
    if not hasattr(kernel, "_vision_engine"):
        try:
            from lib.akasha.source.vision import VisionEngine
            kernel._vision_engine = VisionEngine()
        except ImportError:
            kernel._vision_engine = None
    return kernel._vision_engine


def handle_contexa_fetch(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """
    contexa.fetch — fetch external content and write to Akasha.

    Wikipedia (keyword query):
      - Full article text → written as Atom with evidence.authority=0.9
      - Triggers Weaver + NLP (same pipeline as any w command)
      - URL Atom created as exit point; linked via ref:source
      - Query Atom linked via ctx:topic
      - Added to fetch:{client_id}:refs set

    URL fetch:
      - Scraped content → written as Atom with evidence.authority=0.5
      - Same Weaver/NLP pipeline
      - URL Atom (the URL itself) created as exit point

    In both cases the atom_key is returned so the user can navigate
    or link from it immediately ($it).
    """
    if not kernel.contexa:
        return _err(rid, -32001, "ContexaEngine not available in this environment.")
    query = data.get("query") or data.get("url", "")
    if not query:
        return _err(rid, -32602, "contexa.fetch requires 'query' or 'url'")
    return _ok(rid, _src_fetch.do_fetch(kernel, session, ctx, scopes, client_id, query))


def handle_image_profile(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """image.profile path=|url= [top_k=] — classify an image (local file or URL) into
    labels via the LiteRT vision engine and integrate them into the graph. This is the
    image counterpart of contexa.fetch: the image becomes an atom, each predicted label
    becomes/links a concept (`calc:depicts`, weighted by confidence), and everything
    carries the provenance=external guardrail (trust = model confidence) so model-
    inferred labels can neither poison the learned model nor be mistaken for curation.
    Degrades gracefully (no runtime/model/PIL, or offline → written=false, no error).
    Runs inside the write workspace."""
    src = (data.get("path") or data.get("url") or data.get("src")
           or data.get("image") or "").strip()
    if not src:
        return _err(rid, -32602, "image.profile requires 'path' or 'url'")
    _vis = _vision_engine(kernel)
    if not _vis or not _vis.available():
        return _err(rid, -32001,
                    "Vision engine unavailable (no TFLite/LiteRT runtime or PIL).")

    top_k = max(1, min(int(data.get("top_k", 5)), 10))
    res = _vis.classify(src, top_k=top_k)
    labels = res.get("labels") or []
    if not labels:
        return _ok(rid, res)                          # error / no labels → graceful

    import re
    is_url = src.startswith("http")
    top = labels[0]
    summary = "image: " + ", ".join(l["label"] for l in labels)
    write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}",
                    "provenance:external", "provenance:vision"]
    image_key = ctx.put_chunk(
        content=summary,
        meta={"type": "image", "provenance": "external", "source": "vision",
              "model": res.get("model"), "backend": res.get("backend"),
              "trust": round(float(top.get("score", 0.0)), 3),
              "labels": labels, "src": src},
        author=client_id, scopes=write_scopes)
    session.last_written_id = image_key
    session.set_context("last_written_id", image_key)

    # Each label → a concept atom (find-or-create by alias), linked from the image via
    # calc:depicts weighted by confidence. Concepts are ordinary (curated) atoms, so the
    # graph gains real, referenceable nodes; the *inference* provenance lives on the edge
    # weight + the image atom, not on the concept.
    for lab in labels:
        name = lab["label"]
        c_alias = f"concept:{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}"
        c_key = None
        try:
            c_key = ctx.resolve_alias(c_alias)
        except Exception:
            c_key = None
        if not c_key:
            try:
                c_key = ctx.put_chunk(content=name, meta={"type": "concept"},
                                      author=client_id, scopes=write_scopes)
                ctx.set_alias(c_key, c_alias)
            except Exception:
                c_key = None
        if c_key:
            try:
                ctx.put_link(image_key, c_key, "calc:depicts",
                             w=float(lab.get("score", 1.0)), author=client_id)
            except Exception:
                pass

    # URL exit-point atom (so the source image is navigable) + fetch/vision ref set.
    if is_url:
        url_key = _src_fetch.find_or_create_url_atom(kernel, ctx, src, top["label"],
                                                client_id, write_scopes)
        if url_key:
            try:
                ctx.put_link(image_key, url_key, "ref:source", author=client_id)
            except Exception:
                pass
    session_id = getattr(session, "session_id", client_id)
    try:
        ctx.add_to_set(f"vision:{session_id}:refs", image_key)
    except Exception:
        pass

    # Weave the label summary into the semantic layer (same pipeline as w / fetch).
    weave.post_write(kernel, session, isinstance(ctx, _NucleusWriteCtx), image_key, summary)

    res["atom_key"] = image_key
    res["written"] = True
    return _ok(rid, res)


def io_slug(path: str) -> str:
    import re
    base = os.path.splitext(os.path.basename(path.rstrip("/")))[0] or os.path.basename(path.rstrip("/"))
    return re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_") or "import"


def io_dispatch(kernel, session, rid) -> Callable:
    """A (method, data) -> result closure over the concept registry — used by pipeline
    graph endpoints to reach table/lens operators through the one dispatch route.

    A pipeline endpoint names the VERB it needs as a point — `pipeline.table.create`,
    `pipeline.survey.answer`, `pipeline.deck.new`, … — and this closure resolves it to the op that
    declares it implements that point (group 4): the endpoints name no application op. A point
    nobody implements answers a JSON-RPC error the endpoint reports as it reports any other."""
    import lib.akasha.api as _api_pts

    def _dispatch(method, data):
        if _registry_mod.get_active() is None:
            raise RuntimeError("concept models unavailable")
        if str(method).startswith("pipeline."):
            target = _api_pts.implementer(kernel, method)
            if not target:
                return {"error": {"code": -32601,
                                  "message": "no op implements %s — declare `implements` on "
                                             "the op that provides it" % method}}
            method = target
        return _registry_mod.get_active().dispatch_if_handled(method, session, data, rid)
    return _dispatch


def io_doc_sink(kernel, ctx, session, client_id, set_name) -> "DocSink":
    """A DocSink that writes through the guarded composite path and weaves the text."""
    def _write_atom(text, meta, scopes_):
        return ctx.put_chunk(content=text, meta=meta, author=client_id, scopes=scopes_)

    def _weave(key, text):
        weave.post_write(kernel, session, isinstance(ctx, _NucleusWriteCtx), key, text)
    return DocSink(_write_atom, ctx.add_to_set, _weave, client_id, set_name)


def io_ingest(kernel, source, ctx, session, client_id, rid, table_name=None,
               set_name=None, origin_slug=None) -> dict:
    """Connect a Source to the right graph Sink (table vs document, decided by the stream
    kind) and run the pipeline. Shared by io.import (one file) and io.index (many)."""
    stream = source.read()                                   # may raise (path/parse)
    # The graph Sink is chosen by the stream kind, so we peek the stream here and write it
    # (rather than run_pipeline reading it a second time). Transform hooks, when added, go
    # between this read and the write.
    if stream.kind == "table":
        import re as _re
        name = _re.sub(r"[^a-z0-9_]+", "_", str(table_name or "").lower()).strip("_") \
            or origin_slug or io_slug(stream.origin or "import")
        sink = TableSink(io_dispatch(kernel, session, rid), name)
    else:
        sink = io_doc_sink(kernel, ctx, session, client_id,
                                 set_name or f"docs:{origin_slug or io_slug(stream.origin or 'doc')}")
    result = sink.write(stream)
    if stream.origin and "source" not in result:
        result["source"] = stream.origin
    return result


def handle_io_import(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """io.import path=|text= [format=] [table=] — connect a file (or an inline upload
    payload) Source to a graph Sink: tabular → the `table` model; a document → an indexed
    atom. The single disk-read route into the graph; confined to permitted roots
    (io.allow). Admin/librarian only. Runs in the write workspace."""
    err = kernel._assert_admin(session)
    if err:
        return _err(rid, -32003, err)
    if not kernel.fileio:
        return _err(rid, -32001, "FileIO unavailable in this environment.")
    fmt = (data.get("format") or "").strip() or None
    # Source: a local file, OR an inline payload (text=) — the latter is how a future Web
    # GUI upload plugs into the SAME pipeline without touching disk.
    if data.get("text") is not None:
        if not fmt:
            return _err(rid, -32602, "io.import text= requires 'format'")
        source = InlineSource(str(data["text"]), fmt, name=data.get("name") or "upload")
    else:
        path = (data.get("path") or data.get("file") or "").strip()
        if not path:
            return _err(rid, -32602, "io.import requires 'path' or 'text'")
        source = FileSource(kernel.fileio, path, fmt)
    try:
        return _ok(rid, io_ingest(kernel, source, ctx, session, client_id, rid,
                                        table_name=data.get("table")))
    except PermissionError as exc:
        return _err(rid, -32001, str(exc))
    except FileNotFoundError:
        return _err(rid, -32002, "file not found")
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32602, str(exc))
    except Exception as exc:
        return _err(rid, -32002, f"import failed: {str(exc)[:140]}")


def handle_io_index(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """io.index dir= [exts=] [limit=] — index every supported file under a permitted
    directory (the local-directory-indexing feature: the maintainer permits a dir, and its
    files' content/keywords become index atoms — raw files are never stored). Each file is
    a FileSource run through the ingest pipeline. Bounded; admin/librarian only."""
    err = kernel._assert_admin(session)
    if err:
        return _err(rid, -32003, err)
    if not kernel.fileio:
        return _err(rid, -32001, "FileIO unavailable in this environment.")
    dirp = (data.get("dir") or data.get("path") or "").strip()
    if not dirp:
        return _err(rid, -32602, "io.index requires 'dir'")
    exts = None
    if data.get("exts"):
        exts = {e if e.startswith(".") else "." + e
                for e in str(data["exts"]).lower().replace(",", " ").split()}
    limit = max(1, min(int(data.get("limit", 1000)), 5000))
    slug = io_slug(dirp)
    set_name = f"index:{slug}"
    indexed = tables = errors = files = 0
    try:
        paths = list(kernel.fileio.iter_dir(dirp, exts))
    except PermissionError as exc:
        return _err(rid, -32001, str(exc))
    except FileNotFoundError:
        return _err(rid, -32002, f"directory not found: {dirp}")
    for fpath in paths[:limit]:
        files += 1
        try:
            r = io_ingest(kernel, FileSource(kernel.fileio, fpath), ctx, session, client_id, rid,
                                set_name=set_name)
            if r.get("kind") == "table":
                tables += 1
            else:
                indexed += 1
        except Exception as exc:
            logger.warning("[io.index] %s: %s", fpath, exc)
            errors += 1
    return _ok(rid, {"dir": dirp, "files": files, "indexed_docs": indexed,
                     "tables": tables, "errors": errors, "set": set_name,
                     "truncated": len(paths) > limit})


def handle_io_export(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """io.export (table=|set=) (path=|inline=true) [format=] — connect a graph Source (a
    `table`, or a set of atoms) to a Sink: FileSink writes CSV/JSON/MD to a permitted path;
    with inline=true a ResponseSink returns the serialised content in the result instead
    (the client 'receive' path — a session downloads a table/set as a file). The reverse
    of io.import through the SAME pipeline. Admin/librarian only."""
    err = kernel._assert_admin(session)
    if err:
        return _err(rid, -32003, err)
    if not kernel.fileio:
        return _err(rid, -32001, "FileIO unavailable in this environment.")
    inline = str(data.get("inline", "")).lower() in ("true", "1", "yes")
    path = (data.get("path") or data.get("file") or "").strip()
    if not inline and not path:
        return _err(rid, -32602, "io.export requires 'path' (or inline=true)")
    fmt = (data.get("format") or "").strip() \
        or (kernel.fileio.detect_format(path) if path else None) or "csv"
    if data.get("table"):
        source = TableSource(io_dispatch(kernel, session, rid), data["table"])
    elif data.get("set"):
        set_name = data["set"]
        source = SetSource(
            list_members=lambda: ctx.list_set(set_name, allowed_scopes=scopes),
            get_content=lambda k: (ctx.get_scoped_chunk(k, scopes) if scopes
                                   else ctx.get_chunk(k)),
            set_name=set_name)
    else:
        return _err(rid, -32602, "io.export requires 'table' or 'set'")
    sink = ResponseSink(fmt) if inline else FileSink(kernel.fileio, path, fmt)
    try:
        return _ok(rid, run_pipeline(source, sink))
    except PermissionError as exc:
        return _err(rid, -32001, str(exc))
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32002, str(exc))
    except Exception as exc:
        return _err(rid, -32002, f"export failed: {str(exc)[:140]}")


def handle_io_project(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """io.project src= [model=table|rec] [into=] [depth=] — project an in-graph source (a set,
    an atom/alias tree root, or an Exportable model instance such as a survey) into a concept
    model through the lens pipeline (LensScanSource -> ConceptCastSink). This is the base of the
    general "project into any concept model" path and of model->model chaining; targets today are
    `table` (schema-first) and `rec` (schema-free universal fallback); survey is Exportable
    (other models are a per-model follow-up — issue #43). Admin/librarian only; write."""
    err = kernel._assert_admin(session)
    if err:
        return _err(rid, -32003, err)
    if _registry_mod.get_active() is None:
        return _err(rid, -32001, "concept models unavailable")
    src = (data.get("src") or data.get("source") or "").strip()
    if not src:
        return _err(rid, -32602, "io.project requires 'src' (a set name or atom/alias)")
    model = (data.get("model") or "table").strip()
    dispatch = io_dispatch(kernel, session, rid)
    try:
        return _ok(rid, run_pipeline(
            LensScanSource(dispatch, src, depth=int(data.get("depth", 2))),
            ConceptCastSink(dispatch, model, into=data.get("into"))))
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32602, str(exc))
    except Exception as exc:
        return _err(rid, -32002, f"project failed: {str(exc)[:140]}")


def io_records(kernel, data) -> "list":
    """Acquire a list of raw record dicts from records= (RPC list or JSON string), text= (inline
    JSONL/CSV/JSON), or path= (a permitted file). The shared record-acquisition for io.ingest —
    the same parse serves file, upload, and RPC, so every source lands as plain dicts."""
    recs = data.get("records")
    if isinstance(recs, list):
        return recs
    if isinstance(recs, str) and recs.strip():
        import json as _json
        parsed = _json.loads(recs)
        return parsed if isinstance(parsed, list) else [parsed]
    from lib.harmonia.fileio import FileIO
    if data.get("text") is not None:
        fmt = (data.get("format") or "jsonl").strip()
        _, payload = FileIO.parse_text(str(data["text"]), fmt, name="ingest")
        return payload.get("rows") or []
    path = (data.get("path") or data.get("file") or "").strip()
    if path:
        if not kernel.fileio:
            raise RuntimeError("FileIO unavailable in this environment.")
        _, payload = kernel.fileio.read(path)
        return payload.get("rows") or []
    return None


def handle_io_ingest(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """io.ingest model=<concept> (path=|text=|records=) [into=] [map=field:col,…] — the GENERAL
    raw-records import: read external records (JSONL/CSV/JSON from a permitted file, an inline
    payload, or an RPC list) and hand them to ANY concept model implementing the Importable
    contract (import_records). Model-agnostic — the single route that replaces per-model batch
    ingest ops. Admin/librarian only; runs in the write workspace, so model writes stay guarded."""
    err = kernel._assert_admin(session)
    if err:
        return _err(rid, -32003, err)
    if _registry_mod.get_active() is None:
        return _err(rid, -32001, "concept models unavailable")
    model = (data.get("model") or "").strip()
    if not model:
        return _err(rid, -32602, "io.ingest requires model=<concept prefix>")
    cls = _registry_mod.get_active().get_class(model)
    if not cls:
        return _err(rid, -32602, f"unknown model '{model}'")
    try:
        records = io_records(kernel, data)
    except PermissionError as exc:
        return _err(rid, -32001, str(exc))
    except FileNotFoundError:
        return _err(rid, -32002, "file not found")
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32602, str(exc))
    if records is None:
        return _err(rid, -32602, "io.ingest requires records=, text=, or path=")
    inst = cls(session)
    if not hasattr(inst, "import_records"):
        return _err(rid, -32601, f"model '{model}' is not importable (no import_records contract)")
    # optional field remap: map=field:col,field2:col2
    mapping = {}
    for pair in str(data.get("map") or "").replace(";", ",").split(","):
        if ":" in pair:
            f, _, c = pair.partition(":")
            if f.strip() and c.strip():
                mapping[f.strip()] = c.strip()
    try:
        return _ok(rid, inst.import_records(records, into=(data.get("into") or "").strip(),
                                            mapping=mapping or None))
    except NotImplementedError as exc:
        return _err(rid, -32601, str(exc))
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32602, str(exc))
    except Exception as exc:
        return _err(rid, -32002, f"ingest failed: {str(exc)[:140]}")


def handle_io_allow(kernel, rid, data, session) -> dict:
    """io.allow dir= — permit a local directory for io.import/io.index/io.export (the
    maintainer explicitly grants a directory; reads/writes are otherwise confined to
    data/import, data/export, data). Admin/librarian only."""
    err = kernel._assert_admin(session)
    if err:
        return _err(rid, -32003, err)
    if not kernel.fileio:
        return _err(rid, -32001, "FileIO unavailable in this environment.")
    dirp = (data.get("dir") or data.get("path") or "").strip()
    if not dirp:
        return _err(rid, -32602, "io.allow requires 'dir'")
    root = kernel.fileio.add_root(dirp)
    return _ok(rid, {"allowed": root, "roots": list(kernel.fileio.roots)})


def survey_questions_ordered(kernel, dispatch, ctx, survey_id):
    """Open a survey and return its question atom ids ordered by meta['order'] then
    creation. Returns (question_ids, error_msg)."""
    opened = dispatch("pipeline.survey.open", {"survey_id": survey_id})
    if not isinstance(opened, dict) or opened.get("error") or "result" not in opened:
        return None, f"survey '{survey_id[:12]}' not found or not a survey root"
    inv = (dispatch("pipeline.survey.list", {}) or {}).get("result") or {}
    q_ids = list(inv.get("questions") or [])

    def _order(q):
        m = ctx.get_meta(q) or {}
        o = m.get("order")
        return (o if o is not None else 1e9, m.get("created_at", 0))
    return sorted(q_ids, key=_order), None


def handle_contexa_ingest(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """contexa.ingest survey=<id> (path=|text=) [format=] [respondent_col=] [map=] — the
    client's INPUT side: read collected responses (a CSV/JSON file, or an inline upload
    payload) into the survey graph WITH Contexa macro-binding (ctx:answers → question,
    ctx:from → respondent, per-question set) layered on the survey model's structural links.

    Columns after the respondent column map to the survey's questions: explicitly via
    map=col:qid[,col:qid] (qid may be a question id, an alias, or a 1-indexed position),
    else to the survey's questions in order. Writes into the client's own survey (WRITE);
    disk reads honour the io.allow list. Runs in the write workspace (single-route guard)."""
    if _registry_mod.get_active() is None:
        return _err(rid, -32001, "concept models unavailable")
    if not kernel.contexa:
        return _err(rid, -32001, "ContexaEngine not available in this environment.")
    survey_id = (data.get("survey") or data.get("survey_id") or "").strip()
    if not survey_id:
        survey_id = getattr(session, "get_context", lambda k: None)("active_survey_root") or ""
    if not survey_id:
        return _err(rid, -32602, "contexa.ingest requires 'survey' (survey id)")

    dispatch = io_dispatch(kernel, session, rid)
    q_ids, qerr = survey_questions_ordered(kernel, dispatch, ctx, survey_id)
    if qerr:
        return _err(rid, -32602, qerr)

    # Source: an inline upload (text=) — the Web-GUI path — or a permitted file.
    fmt = (data.get("format") or "").strip() or None
    if data.get("text") is not None:
        if not fmt:
            return _err(rid, -32602, "contexa.ingest text= requires 'format'")
        source = InlineSource(str(data["text"]), fmt, name=data.get("name") or "responses")
    else:
        path = (data.get("path") or data.get("file") or "").strip()
        if not path:
            return _err(rid, -32602, "contexa.ingest requires 'path' or 'text'")
        if not kernel.fileio:
            return _err(rid, -32001, "FileIO unavailable in this environment.")
        # Disk reads are admin/librarian only (same posture as io.import — the io.allow
        # list is maintainer-managed); a WRITE client ingests its own data via text=.
        err = kernel._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        source = FileSource(kernel.fileio, path, fmt)

    try:
        stream = source.read()
    except PermissionError as exc:
        return _err(rid, -32001, str(exc))
    except FileNotFoundError:
        return _err(rid, -32002, "file not found")
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32602, str(exc))
    if stream.kind != "table":
        return _err(rid, -32602, "contexa.ingest requires a tabular source (CSV/JSON rows)")

    cols = list(stream.columns)
    if not cols:
        return _err(rid, -32602, "no columns in the response source")
    respondent_col = (data.get("respondent_col") or "").strip() or cols[0]
    if respondent_col not in cols:
        return _err(rid, -32602,
                    f"respondent_col '{respondent_col}' not in columns {cols}")

    question_map = {}
    if data.get("map"):
        for pair in str(data["map"]).split(","):
            if ":" not in pair:
                continue
            col, q = (p.strip() for p in pair.split(":", 1))
            if col not in cols:
                continue
            if q.isdigit():
                idx = int(q) - 1
                if 0 <= idx < len(q_ids):
                    question_map[col] = q_ids[idx]
            elif q in q_ids:
                question_map[col] = q
            else:
                resolved = ctx.resolve_alias(q)
                if resolved:
                    question_map[col] = resolved
    else:
        q_cols = [c for c in cols if c != respondent_col]
        for i, col in enumerate(q_cols):
            if i < len(q_ids):
                question_map[col] = q_ids[i]
    if not question_map:
        return _err(rid, -32602, "no question columns could be mapped "
                    "(add questions to the survey first, or pass map=col:qid)")

    def _bind(resp_id, question_key=None, respondent_key=None, set_names=None):
        return kernel.contexa.bind_context(
            ctx, resp_id, question_key=question_key, respondent_key=respondent_key,
            set_names=set_names, author=client_id)

    sink = ResponseIngestSink(dispatch, _bind, survey_id, respondent_col, question_map)
    try:
        result = sink.write(stream)
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32602, str(exc))
    result["mapped_questions"] = {c: q[:12] for c, q in question_map.items()}
    if stream.origin:
        result.setdefault("source", stream.origin)
    return _ok(rid, result)


def handle_jataka_present(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """jataka.present (survey=<id>|set=<name>|focus=<atom>) as=table|scatter|narrative
    [format=] — the client's OUTPUT side: read a graph selection THROUGH the Consciousness
    substrate and render a presentation, returned inline (READ-level; no graph write).
      as=table     survey=|set=   → per-(question,answer) counts / listed rows (+ format=)
      as=scatter   survey=|set=   → 2-D points positioned by cosmos_nd
      as=narrative focus=|survey= → prose from generate_view (LLM-optional; template floor)"""
    as_fmt = (data.get("as") or data.get("mode") or "table").strip().lower()
    survey_id = (data.get("survey") or data.get("survey_id") or "").strip()
    set_name = (data.get("set") or "").strip()
    focus = (data.get("focus") or data.get("id") or "").strip()
    dispatch = io_dispatch(kernel, session, rid)

    def _view(k):
        return session.consciousness.generate_view(k, allowed_scopes=scopes)

    def _content(k):
        return (ctx.get_scoped_chunk(k, scopes) if scopes else ctx.get_chunk(k)) or ""

    def _agg_source(sid):
        return SurveyAggregateSource(
            lambda: (dispatch("pipeline.survey.list", {}) or {}).get("result") or {},
            lambda k: ctx.get_meta(k) or {}, _content, sid)

    try:
        if as_fmt == "table":
            if survey_id:
                opened = dispatch("pipeline.survey.open", {"survey_id": survey_id})
                if not isinstance(opened, dict) or "result" not in opened:
                    return _err(rid, -32602, f"survey '{survey_id[:12]}' not found")
                source = _agg_source(survey_id)
            elif set_name:
                source = SetSource(
                    list_members=lambda: ctx.list_set(set_name, allowed_scopes=scopes),
                    get_content=_content, set_name=set_name)
            else:
                return _err(rid, -32602, "jataka.present as=table requires 'survey' or 'set'")
            sink = PresentTableSink((data.get("format") or "").strip() or None)
            return _ok(rid, run_pipeline(source, sink))

        if as_fmt in ("scatter", "cosmos"):
            sset = f"set:survey:{survey_id}:responses" if survey_id else set_name
            if not sset:
                return _err(rid, -32602, "jataka.present as=scatter requires 'survey' or 'set'")
            source = SetSource(
                list_members=lambda: ctx.list_set(sset, allowed_scopes=scopes),
                get_content=_content, set_name=sset)

            def _coords(k):
                v = _view(k) or {}
                if "error" in v:
                    return None
                f = v.get("focus") or {}
                nd = f.get("cosmos_nd") or []
                if len(nd) < 2:
                    return None
                label = f.get("alias") or (f.get("content") or "")[:20].replace("\n", " ")
                color = nd[5] if len(nd) > 5 else "#888888"
                return (nd[0], nd[1], label, color)
            return _ok(rid, run_pipeline(source, ScatterSink(_coords)))

        if as_fmt in ("narrative", "story", "narrate"):
            if not focus and survey_id:
                focus = survey_id
            if not focus:
                return _err(rid, -32602,
                            "jataka.present as=narrative requires 'focus' or 'survey'")
            resolved = ctx.resolve_alias(focus) or focus
            rows, cols = [], []
            if survey_id:
                opened = dispatch("pipeline.survey.open", {"survey_id": survey_id})
                if not isinstance(opened, dict) or "result" not in opened:
                    return _err(rid, -32602, f"survey '{survey_id[:12]}' not found")
                agg = _agg_source(survey_id).read()
                rows, cols = agg.rows, agg.columns
            source = InterpretationSource(_view, resolved, data_rows=rows, data_columns=cols)
            return _ok(rid, run_pipeline(source, NarrativeSink(getattr(kernel, "_narrative_llm", None))))

        return _err(rid, -32602,
                    f"unknown presentation mode '{as_fmt}' (table|scatter|narrative)")
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32602, str(exc))
    except Exception as exc:
        return _err(rid, -32002, f"present failed: {str(exc)[:140]}")


def handle_curation_project(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """curation.project id=<cur>|name= as=presentation [title=] — HOP A: project a curation's
    narrative path into a PRIVATE working presentation deck (1 frame per path atom, in order).
    run_pipeline(CurationPathSource → PresentationSink). Idempotent: if the curation already
    has a projected presentation (curation:projected_as), returns it. CLI: cur.project."""
    as_fmt = (data.get("as") or "presentation").strip().lower()
    if as_fmt != "presentation":
        return _err(rid, -32602, "curation.project supports as=presentation "
                                 "(as=table|scatter → jataka.present)")
    cur = (data.get("id") or data.get("curation_id") or data.get("name") or "").strip()
    if not cur:
        return _err(rid, -32602, "curation.project requires 'id' (or name=)")
    dispatch = io_dispatch(kernel, session, rid)
    # Idempotency: reuse a prior projection if linked.
    try:
        cur_key = ctx.resolve_alias(cur) or cur
        for (dst, _rel) in (ctx.get_adjacent_links(cur_key, "curation:projected_as") or []):
            # the pipe's own `curation:projected_as` link IS the record of a prior projection —
            # read by relation, not by the presentation model's concept name
            return _ok(rid, {"status": "exists", "presentation_id": dst,
                             "source": f"curation:{cur_key}", "reused": True})
    except Exception:
        cur_key = cur
    try:
        result = run_pipeline(CurationPathSource(dispatch, cur),
                              PresentationSink(dispatch, title=(data.get("title") or "").strip() or None))
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32602, str(exc))
    except Exception as exc:
        return _err(rid, -32002, f"project failed: {str(exc)[:140]}")
    pres_id = result.get("presentation_id")
    if pres_id:
        try:
            ctx.put_link(cur_key, pres_id, "curation:projected_as", author=client_id)
        except Exception:
            pass
    result["status"] = "projected"
    return _ok(rid, result)


def handle_pres_export(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """pres.export id=<pres> as=scroll|kamishibai [inline=true | publish=<slug>] — HOP B:
    resolve each frame's ref atom into a full self-contained card and render the export
    object (§6). inline=true (default) returns it in-band (+ a CLI text rendering); publish=
    <slug> (librarian) writes the frozen artifact to the `exports` declaration root as <slug>.<fmt>.json
    and returns its URL. Format-only, no graph write. CLI: pr.export."""
    pres_id = (data.get("id") or data.get("pres_id") or data.get("presentation_id") or "").strip()
    if not pres_id:
        return _err(rid, -32602, "pres.export requires 'id'")
    pres_id = ctx.resolve_alias(pres_id) or pres_id
    fmt = (data.get("as") or data.get("format") or "scroll").strip().lower()
    if fmt not in ("scroll", "kamishibai"):
        return _err(rid, -32602, "pres.export as= must be scroll|kamishibai")
    publish = (data.get("publish") or "").strip()
    dispatch = io_dispatch(kernel, session, rid)

    def _get_links(key, rel):
        return [(l[0], l[1]) for l in (ctx.get_adjacent_links(key, rel) or [])]

    try:
        source = PresentationSceneSource(dispatch, pres_id, fmt,
                                         lambda k: ctx.get_meta(k) or {}, _get_links)
        result = run_pipeline(source, ExportSink(fmt))
    except (ValueError, RuntimeError) as exc:
        return _err(rid, -32602, str(exc))
    except Exception as exc:
        return _err(rid, -32002, f"export failed: {str(exc)[:140]}")
    export = result.get("export") or {}

    if publish:
        # Publishing writes a PUBLIC static artifact → librarian-gated (it exposes a snapshot).
        if "role:librarian" not in scopes:
            return _err(rid, -32601, "pres.export publish=<slug> requires role:librarian")
        if not kernel.fileio:
            return _err(rid, -32001, "FileIO unavailable in this environment.")
        import re as _re
        slug = _re.sub(r"[^a-z0-9._-]+", "-", publish.lower()).strip("-") or "export"
        from lib.akasha.api import reserved as _reserved
        exports_dir  = _reserved.root("exports")
        try:
            os.makedirs(exports_dir, exist_ok=True)
            kernel.fileio.add_root(exports_dir)        # allow-list this public archives dir
            rel_path = os.path.join(exports_dir, f"{slug}.{fmt}.json")
            # FileIO.serialize(payload,"json") dumps the payload directly → the file is the
            # RAW export object (self-contained, renderable with zero graph access).
            kernel.fileio.write(rel_path, export, "json")
            # Maintain a published-exhibits index so the archives Exhibition Room can
            # list and link exhibits (it can't know a slug otherwise). Upsert by slug,
            # tracking which formats exist. Non-fatal — a bad index never fails a publish.
            try:
                import json as _json, time as _t
                idx_path = os.path.join(exports_dir, "index.json")
                by_slug = {}
                if os.path.exists(idx_path):
                    with open(idx_path, "r", encoding="utf-8") as _f:
                        for e in (_json.load(_f) or {}).get("exhibits", []):
                            if e.get("slug"):
                                by_slug[e["slug"]] = e
                entry = by_slug.get(slug, {"slug": slug})
                entry.update({"slug": slug, "title": export.get("title", ""),
                              "thesis": export.get("thesis", ""),
                              "count": export.get("count", 0), "updated_at": _t.time()})
                entry["formats"] = sorted(set(entry.get("formats") or []) | {fmt})
                by_slug[slug] = entry
                with open(idx_path, "w", encoding="utf-8") as _f:
                    _json.dump({"exhibits": sorted(by_slug.values(),
                                key=lambda e: e.get("updated_at", 0), reverse=True)},
                               _f, ensure_ascii=False, indent=2)
            except Exception as _iexc:
                logger.warning("[pres.export] exhibits index update failed: %s", _iexc)
        except Exception as exc:
            return _err(rid, -32002, f"publish failed: {str(exc)[:140]}")
        return _ok(rid, {"status": "published", "format": fmt, "slug": slug,
                         "url": f"/curation/exports/{slug}.{fmt}.json",
                         "scenes": export.get("count", 0)})

    # inline (default): return the export + a CLI text rendering.
    return _ok(rid, {"status": "exported", "format": fmt, "export": export,
                     "text": render_export_text(export)})


def render_export_text(export: dict) -> str:
    """A plain-text rendering of an export object for the CLI — the same scenes the archives
    page draws, as a readable 紙芝居/scroll transcript (headword, description, caption, refs,
    links per scene). Degradation-first: a headword-only scene still prints."""
    lines: List[str] = []
    title = export.get("title") or "(untitled)"
    fmt = export.get("format", "scroll")
    lines.append(f"╔═ {title}  [{fmt}]")
    if export.get("thesis"):
        lines.append(f"║  {export['thesis']}")
    lines.append(f"╚═ {export.get('count', 0)} scene(s)")
    for sc in export.get("scenes") or []:
        n = sc.get("scene")
        lines.append("")
        lines.append(f"── [{n}] {sc.get('headword') or '(no headword)'} ──"
                     + (f"   {sc['href']}" if sc.get("href") else ""))
        desc = (sc.get("description") or "").strip()
        if desc:
            lines.append(desc if len(desc) <= 400 else desc[:400] + "…")
        if sc.get("caption"):
            lines.append(f"  ⟨caption⟩ {sc['caption']}")
        img = sc.get("image") or None
        if isinstance(img, dict) and img.get("url"):
            lines.append(f"  ⟨image⟩ {img['url']}"
                         + (f"  ({img.get('source')})" if img.get("source") else ""))
        for rf in (sc.get("refs") or [])[:6]:
            lines.append(f"  → {rf.get('label') or rf.get('url')}  [{rf.get('source','')}] "
                         f"{rf.get('url','')}")
        links = sc.get("links") or []
        if links:
            lines.append("  related: " + ", ".join(l.get("name", "") for l in links[:8]))
        for blk in (sc.get("blocks") or []):
            lines.append(f"    · {blk.get('region','')}/{blk.get('role','')}: "
                         f"{(blk.get('headword') or blk.get('body') or '')[:60]}")
    return "\n".join(lines)


def handle_web_search(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """
    web.search — surface-level web search; results stored as lightweight refs.

    For each result: a ref Atom (title + snippet) is created and linked to
    a URL exit-point Atom via ref:source.  The full page is NOT fetched or
    processed — only the search API snippet is stored.  No Weaver/NLP is
    triggered on ref Atoms (they are reference metadata, not knowledge).

    All refs are added to search:{client_id}:refs for navigation.
    """
    if not kernel.contexa:
        return _err(rid, -32001, "ContexaEngine not available in this environment.")
    query = data.get("query", "")
    if not query:
        return _err(rid, -32602, "web.search requires 'query'")
    limit = int(data.get("limit", 5))

    result  = kernel.contexa.search(query, limit=limit)
    results = result.get("results", [])

    write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}"]
    session_id   = getattr(session, "session_id", client_id)
    ref_set      = f"search:{session_id}:refs"
    ref_keys: List[str] = []

    for r in results:
        url     = r.get("url", "")
        title   = r.get("title", "")
        snippet = r.get("snippet", "")
        if not url:
            continue

        # URL exit-point Atom
        url_key = _src_fetch.find_or_create_url_atom(kernel, ctx, url, title,
                                                 client_id, write_scopes)

        # Lightweight ref Atom: title + snippet only (no page fetch)
        ref_content = f"{title}\n{snippet}".strip() if snippet else title
        if ref_content:
            try:
                ref_key = ctx.put_chunk(
                    content=ref_content,
                    meta={"type": "ref:web", "url": url, "title": title},
                    author=client_id,
                    scopes=write_scopes,
                )
                if url_key:
                    ctx.put_link(ref_key, url_key, "ref:source", author=client_id)
                ctx.add_to_set(ref_set, ref_key)
                ref_keys.append(ref_key)
            except Exception as exc:
                logger.debug("[WebSearch] ref atom '%s': %s", url, exc)
        elif url_key:
            try:
                ctx.add_to_set(ref_set, url_key)
                ref_keys.append(url_key)
            except Exception:
                pass

    result["ref_keys"] = ref_keys
    return _ok(rid, result)
