"""
General file import/export — the single Harmonia-owned disk I/O layer.

Before this, real file I/O was scattered and domain-specific (kernel's ontology loader read
`.ak` from disk; `table.import`/`export` moved CSV *strings* with no file endpoint; the
Harmonia `transport.py` / `FileSystemWatcher` scaffolds were dead). This is the one place
that touches the disk for general data: it reads/writes text and semi-text formats
(CSV, JSON, Markdown, TXT), and the kernel's `io.*` handlers project the parsed result into
the graph (tabular → the `table` model; documents → indexed atoms). PDF and other binary
multi-format support is deferred (tracked as a GitHub issue).

FileIO is graph-agnostic (no cortex/atom knowledge) — pure path-safe read/parse and
serialize/write, plus directory iteration. All reads/writes are confined to an explicit
allow-list of roots (the maintainer "permits a directory"), so it cannot wander the host
filesystem even when driven by an admin.
"""
import os
import io
import csv
import json
import re
from typing import Any, Dict, List, Optional, Tuple, Iterator

_EXT_FORMAT = {
    ".csv": "csv", ".tsv": "csv",
    ".json": "json",
    ".md": "md", ".markdown": "md",
    ".txt": "txt", ".text": "txt",
}
IMPORT_FORMATS = frozenset({"csv", "json", "md", "txt"})
EXPORT_FORMATS = frozenset({"csv", "json", "md"})


class FileIO:
    """Path-safe disk read/write + parse/serialize for CSV/JSON/MD/TXT. Confined to an
    allow-list of root directories."""

    def __init__(self, infra=None, extra_roots: Optional[List[str]] = None):
        roots: List[str] = []
        for attr in ("import_dir", "export_dir", "data_dir"):
            p = getattr(infra, attr, None)
            if p:
                roots.append(p)
        roots.extend(extra_roots or [])
        self.roots: List[str] = []
        for r in roots:
            self.add_root(r)

    # ── allow-list ────────────────────────────────────────────────────────────────
    def add_root(self, path: str) -> str:
        """Permit reads/writes under `path`. Returns the absolute root."""
        ap = os.path.abspath(path)
        if ap not in self.roots:
            self.roots.append(ap)
        return ap

    def _within_roots(self, abspath: str) -> bool:
        return any(abspath == r or abspath.startswith(r + os.sep) for r in self.roots)

    def _safe(self, path: str, must_exist: bool = False) -> str:
        ap = os.path.abspath(path)
        if not self._within_roots(ap):
            raise PermissionError(
                f"path is outside the allowed roots (permit it first): {path}")
        if must_exist and not os.path.exists(ap):
            raise FileNotFoundError(path)
        return ap

    @staticmethod
    def detect_format(path: str) -> Optional[str]:
        return _EXT_FORMAT.get(os.path.splitext(path)[1].lower())

    # ── read / parse ────────────────────────────────────────────────────────────────
    def read(self, path: str, fmt: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Read + parse a file (path-checked). Thin wrapper over parse_text so the same
        parsing serves both disk files and in-memory bytes (e.g. a future web upload)."""
        ap = self._safe(path, must_exist=True)
        fmt = fmt or self.detect_format(ap)
        with open(ap, encoding="utf-8") as fh:
            raw = fh.read()
        return self.parse_text(raw, fmt, name=os.path.basename(ap))

    @classmethod
    def parse_text(cls, raw: str, fmt: Optional[str], name: str = "input") -> Tuple[str, Dict[str, Any]]:
        """Parse already-in-memory content (no disk). Returns (kind, payload):
             kind 'table' → {'columns': [...], 'rows': [{col: val}], 'csv': text}
             kind 'doc'   → {'text': str, 'title': str}
        JSON that is an array-of-objects becomes a table; any other JSON becomes a doc. This
        is the shared parse used by file reads AND by non-file sources (uploads, streams)."""
        if fmt == "csv":
            delim = "\t" if name.lower().endswith(".tsv") else ","
            return "table", cls._parse_csv(raw, delim)
        if fmt == "json":
            data = json.loads(raw)
            if isinstance(data, list) and data and all(isinstance(x, dict) for x in data):
                return "table", cls._records_to_table(data)
            return "doc", {"text": json.dumps(data, ensure_ascii=False, indent=2), "title": name}
        if fmt in ("md", "txt"):
            return "doc", {"text": raw, "title": cls._md_title(raw) or name}
        raise ValueError(f"unsupported import format: {fmt}")

    @staticmethod
    def _parse_csv(text: str, delim: str = ",") -> Dict[str, Any]:
        reader = csv.reader(io.StringIO(text), delimiter=delim)
        header = [h.strip() for h in next(reader, [])]
        rows = [dict(zip(header, r)) for r in reader]
        # Re-serialise as canonical comma CSV so table.import (RFC-4180) can reuse it.
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(header)
        for r in rows:
            w.writerow([r.get(c, "") for c in header])
        return {"columns": header, "rows": rows, "csv": buf.getvalue()}

    @staticmethod
    def _records_to_table(records: List[dict]) -> Dict[str, Any]:
        cols: List[str] = []
        for rec in records:
            for kk in rec:
                if kk not in cols:
                    cols.append(kk)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(cols)
        for rec in records:
            w.writerow(["" if rec.get(c) is None else rec.get(c) for c in cols])
        return {"columns": cols, "rows": records, "csv": buf.getvalue()}

    @staticmethod
    def _md_title(text: str) -> Optional[str]:
        for line in text.splitlines():
            m = re.match(r"^\s*#\s+(.+)$", line)
            if m:
                return m.group(1).strip()
            if line.strip():
                break
        return None

    # ── serialize / write ────────────────────────────────────────────────────────────
    def write(self, path: str, payload: Dict[str, Any], fmt: Optional[str] = None) -> Dict[str, Any]:
        """Serialise `payload` and write it. For csv/json payload = {'columns':[...],
        'rows':[{col:val}]}; for md payload = {'text': str} or {'title','rows'}."""
        ap = self._safe(path)
        fmt = fmt or self.detect_format(ap)
        parent = os.path.dirname(ap)
        if parent:
            os.makedirs(parent, exist_ok=True)
        text = self.serialize(payload, fmt)
        with open(ap, "w", encoding="utf-8") as fh:
            fh.write(text)
        return {"path": ap, "bytes": len(text.encode("utf-8")), "format": fmt,
                "rows": len(payload.get("rows", []) or [])}

    @classmethod
    def serialize(cls, payload: Dict[str, Any], fmt: Optional[str]) -> str:
        """Serialise a payload to text (no disk) — shared by file writes and non-file sinks."""
        if fmt == "csv":
            return cls._to_csv(payload)
        if fmt == "json":
            return json.dumps(payload.get("rows", payload), ensure_ascii=False, indent=2)
        if fmt == "md":
            return cls._to_md(payload)
        raise ValueError(f"unsupported export format: {fmt}")

    @staticmethod
    def _to_csv(payload: Dict[str, Any]) -> str:
        cols = payload.get("columns") or (
            list(payload["rows"][0].keys()) if payload.get("rows") else [])
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(cols)
        for r in payload.get("rows", []):
            w.writerow([r.get(c, "") for c in cols])
        return buf.getvalue()

    @staticmethod
    def _to_md(payload: Dict[str, Any]) -> str:
        if payload.get("text"):
            return payload["text"]
        lines = []
        if payload.get("title"):
            lines.append(f"# {payload['title']}\n")
        cols = payload.get("columns") or (
            list(payload["rows"][0].keys()) if payload.get("rows") else [])
        if cols:
            lines.append("| " + " | ".join(cols) + " |")
            lines.append("| " + " | ".join("---" for _ in cols) + " |")
            for r in payload.get("rows", []):
                lines.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
        return "\n".join(lines) + "\n"

    # ── directory iteration (for local-directory indexing) ────────────────────────────
    def iter_dir(self, dirpath: str, exts: Optional[set] = None,
                 recursive: bool = True) -> Iterator[str]:
        """Yield supported files under an allowed directory (skips dotfiles). `exts` is an
        optional set of lowercase extensions ('.md', …); default = all supported formats."""
        ap = self._safe(dirpath, must_exist=True)
        for root, _dirs, names in os.walk(ap):
            for n in sorted(names):
                if n.startswith("."):
                    continue
                ext = os.path.splitext(n)[1].lower()
                if exts is not None:
                    if ext not in exts:
                        continue
                elif ext not in _EXT_FORMAT:
                    continue
                yield os.path.join(root, n)
            if not recursive:
                break
