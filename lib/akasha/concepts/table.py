"""
TableConcept — formal tabular data model.

  Operand  : Table atom (schema), Column atoms, Row atoms (rec-compatible)
  Operator : table.new / table.col.add / table.col.ls /
             table.row.add / table.row.get / table.row.rm /
             table.ls / table.get / table.export / table.import / table.rm
  Agent    : any AkashaSession client — human, LLM, sensor, script

[table vs rec]

rec.*   : schema-free — any key, any value, no column declarations.
table.* : schema-first — columns declared up-front; row.add validates against them.

Every row in a table IS a rec-compatible atom.  rec.get / rec.set work on table
rows transparently.  TableConcept sits above RecConcept in the type hierarchy:
it layers a column schema contract and CSV/RDB-compatible export/import on top
of the same Atom+Link substrate that rec.* uses.

[Graph representation]

Table atom
  content → description or "[table:<name>]"
  meta    → {"type": "table", "name": <name>, "created_at": <ts>}
  alias   → tbl:<name>   (registered at creation; first-wins)
  links   → tbl:col → each column atom
             tbl:row → each row atom
  sets    → (the table atom itself is not a member of its own col/row sets)

Column atom
  content → "col:<name> (<type>)"
  meta    → {"type": "table_col", "col_name": ..., "col_type": ...,
              "ordinal": <int>, "table_key": <tbl_key>}
  sets    → tbl:<name>:cols

Row atom  (rec-compatible — rec.get / rec.set work on it)
  content → "[ row:<ns timestamp> in <name> ]"  (unique per insertion)
  meta    → {"type": "rec", "rec_type": "tbl_row",
              "table_key": <tbl_key>, "created_at": <ts>}
  links   → rec:<col_name> → value atom    (same as rec.* attributes)
             instance_of   → table atom
  (from table) → tbl:row → this row
  sets    → tbl:<name>:rows, set:rec:tbl_row

[Column types]

text (default) · int · float · bool · date
Types are stored in column meta and respected by export order.
No coercion is applied at write time — values are always stored as text atoms.

[Import / Export]

Columns are written in ordinal order (set at table.new / table.col.add time).
table.export → RFC 4180 CSV with header row.
table.import → parses RFC 4180 CSV; header must use declared column names.
"""

import csv as _csv
import io
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.concepts.base import BaseConcept
from lib.akasha.concepts.mixins.importable import ImportableMixin
from lib.akasha.concepts.mixins.exportable import ExportableMixin

logger = logging.getLogger("Harmonia.Table")

_VALID_TYPES     = {"text", "int", "float", "bool", "date"}
_MAX_EXPORT_ROWS = 5000   # hard cap for export_projection (mirrors lens _MAX_NODES)


def _parse_cols(cols_str: str) -> List[Tuple[str, str]]:
    """Parse "id:int,name:text,email" → [("id","int"), ("name","text"), ("email","text")]."""
    result: List[Tuple[str, str]] = []
    for token in cols_str.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" in token:
            name, typ = token.split(":", 1)
            name = name.strip()
            typ  = typ.strip().lower()
        else:
            name = token
            typ  = "text"
        if typ not in _VALID_TYPES:
            raise ValueError(
                f"Unknown type '{typ}' for column '{name}'. "
                f"Valid types: {', '.join(sorted(_VALID_TYPES))}"
            )
        if not name.isidentifier():
            raise ValueError(
                f"Column name '{name}' must be a valid identifier "
                "(letters, digits, underscores; must not start with a digit)."
            )
        result.append((name, typ))
    if not result:
        raise ValueError("cols must define at least one column.")
    return result


def _coerce_row_add(data: Dict[str, Any]) -> Dict[str, Any]:
    """Separate the 'table' key from the column-value pairs in row.add."""
    reserved = {"table"}
    return {
        "table":  data.get("table", ""),
        "values": {k: v for k, v in data.items() if k not in reserved},
    }


def _coerce_import(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map CLI 'csv=...' to internal 'csv_text=...' (avoids shadowing the csv module)."""
    return {
        "table":    data.get("table", ""),
        "csv_text": data.get("csv", data.get("csv_text", "")),
    }


class TableConcept(BaseConcept, ImportableMixin, ExportableMixin):
    """
    Schema-first tabular data model.

    Columns are declared at table.new time.  Rows are validated on insert.
    Every row is a rec-compatible atom — rec.get / rec.set work transparently.
    Supports RFC 4180 CSV export and import.
    """

    CONCEPT_PREFIX = "table"
    CONCEPT_METHODS = {
        "new":     {"op": "op_new"},
        "get":     {"op": "op_get"},
        "rm":      {"op": "op_rm"},
        "col.add": {"op": "op_col_add"},
        "col.ls":  {"op": "op_col_ls"},
        "row.add": {"op": "op_row_add", "coerce": _coerce_row_add},
        "row.get": {"op": "op_row_get"},
        "row.rm":  {"op": "op_row_rm"},
        "ls":      {"op": "op_ls"},
        "view":    {
            "op":     "op_view",
            "action": "read",
            "args":   ["table"],
            "desc":   "Show table rows as a formatted CLI table: tbl.view <name> [limit=N]",
        },
        "export":  {"op": "op_export"},
        "import":  {"op": "op_import", "coerce": _coerce_import},
    }

    _COL_SUFFIX = "cols"
    _ROW_SUFFIX = "rows"

    # ── ExportableMixin — lens export adapter ────────────────────────────────

    EXPORT_SCHEMA = {
        "model":       "table",
        "meta_type":   "table",      # atom meta["type"] that identifies table atoms
        "description": "Table rows as attribute records (rec: links per column)",
        "produces":    ["rec:"],
    }

    def export_projection(
        self,
        src_key: str,
        **opts,
    ) -> List[Tuple]:
        """Return table rows as SourceScanner-format nodes.

        src_key — atom key of the table atom (resolved from alias by SourceScanner)
        Each returned node: (row_key, attrs_dict, 0, row_meta)
          attrs_dict contains "content" + "rec:<col>" link values.
        """
        tbl_name = self._tbl_name(src_key)
        if not tbl_name:
            return []

        row_keys = self.cortex.get_collection_members(
            self._tbl_set(tbl_name, self._ROW_SUFFIX)
        ) or []

        result: List[Tuple] = []
        for row_key in row_keys[:_MAX_EXPORT_ROWS]:
            content  = self.cortex.get_chunk(row_key) or ""
            row_meta = self.cortex.get_meta(row_key) or {}
            links    = self.cortex.get_adjacent_links(row_key)
            attrs: Dict[str, str] = {"content": content}
            for dst, rel in links:
                if rel.startswith("rec:") or rel.startswith("tbl:"):
                    val = self.cortex.get_chunk(dst) or ""
                    if val:
                        attrs[rel] = val
            result.append((row_key, attrs, 0, row_meta))

        return result

    # ── ImportableMixin — lens projection adapter ─────────────────────────────

    IMPORT_SCHEMA = {
        "model":       "table",
        "requires":    [],
        "prefers":     ["rec:"],
        "min_nodes":   1,
        "description": "Maps rec: attributes to columns; one row per source node.",
    }

    @classmethod
    def match_projection(cls, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Score table compatibility and propose auto-columns from rec: attrs."""
        attrs     = profile.get("attrs", {})
        rec_attrs = {k: v for k, v in attrs.items() if k.startswith("rec:")}

        if not rec_attrs:
            if profile.get("content_available"):
                return {
                    "score":        0.30,
                    "auto_mapping": {"content": "content"},
                    "auto_opts":    {"auto_cols": "content:text"},
                    "notes":        ["No rec: attrs; will use content as single column"],
                    "missing":      [],
                }
            return {"score": 0.05, "auto_mapping": {}, "auto_opts": {}, "notes": ["No attributes found"], "missing": []}

        # Sort by coverage (descending); omit very sparse attrs (< 10%) unless few total
        threshold = 0.10 if len(rec_attrs) > 5 else 0.0
        chosen    = {k: v for k, v in rec_attrs.items() if v.get("coverage", 0) >= threshold}
        chosen    = dict(sorted(chosen.items(), key=lambda x: -x[1].get("coverage", 0)))

        auto_cols    = []
        auto_mapping = {}
        for attr, info in chosen.items():
            col_name = attr[4:]   # strip "rec:"
            col_type = info.get("type_hint", "text")
            auto_cols.append(f"{col_name}:{col_type}")
            auto_mapping[col_name] = attr

        score = min(1.0, 0.40 + len(chosen) * 0.10)
        notes = [f"{len(auto_cols)} col(s): {', '.join(auto_cols)}"]
        if len(rec_attrs) > len(chosen):
            notes.append(f"{len(rec_attrs)-len(chosen)} sparse attr(s) omitted (<10% coverage)")

        return {
            "score":        score,
            "auto_mapping": auto_mapping,
            "auto_opts":    {"auto_cols": ",".join(auto_cols)},
            "notes":        notes,
            "missing":      [],
        }

    def import_projection(
        self,
        nodes:   List,
        mapping: Dict[str, str],
        into:    str,
        **opts,
    ) -> Dict[str, Any]:
        """Create a table from a projection node list.

        nodes   — [(atom_key, attrs_dict, depth, meta), …]
        mapping — {col_name: source_attr}  e.g. {"date": "rec:date"}
        into    — table name
        opts    — auto_cols str (from match_projection) or cols= override
        """
        cols_str = opts.get("cols") or opts.get("auto_cols") or ",".join(
            f"{col}:text" for col in mapping
        )
        if not cols_str:
            raise ValueError("No columns could be determined for the table projection.")

        self.op_new(name=into, cols=cols_str)
        inserted = 0
        for atom_key, attrs, depth, meta in nodes:
            values = {}
            for col_name, src_attr in mapping.items():
                if src_attr == "content":
                    values[col_name] = attrs.get("content", "")
                else:
                    values[col_name] = attrs.get(src_attr, "")
            if any(v for v in values.values()):
                self.op_row_add(table=into, values=values)
                inserted += 1

        return {"table": into, "alias": f"tbl:{into}", "rows_inserted": inserted}

    # ── internal helpers ──────────────────────────────────────────────────────

    def _author_scopes(self) -> Tuple[str, List[str]]:
        aid = getattr(self.session, "client_id", "system")
        return aid, [f"owner:user_{aid}", f"view:user_{aid}"]

    def _tbl_set(self, tbl_name: str, suffix: str) -> str:
        return f"tbl:{tbl_name}:{suffix}"

    def _resolve_table(self, table: str) -> str:
        """Resolve name / tbl:<name> alias / raw key → atom key.  Raises if not found.

        The canonical `tbl:<name>` alias is tried FIRST: a bare table name is also
        weaved into a proto-word (same string, different atom), so resolving the bare
        name first would return that proto-word instead of the table — dropping the
        schema. Trying `tbl:<name>` first binds to the real table atom."""
        if not table:
            raise ValueError("'table' is required.")
        for candidate in (f"tbl:{table}", table):
            key = self.cortex.resolve_alias(candidate)
            if key:
                return key
        if self.cortex.get_chunk(table):
            return table
        raise ValueError(f"Table '{table}' not found.")

    def _tbl_name(self, tbl_key: str, fallback: str = "") -> str:
        meta = self.cortex.get_meta(tbl_key) or {}
        return meta.get("name") or fallback

    def _get_columns(self, tbl_key: str) -> List[Dict[str, Any]]:
        """Return column descriptors sorted by ordinal."""
        links = self.cortex.get_adjacent_links(tbl_key, "tbl:col")
        cols: List[Dict[str, Any]] = []
        for dst, _ in links:
            meta = self.cortex.get_meta(dst) or {}
            if meta.get("type") == "table_col":
                cols.append({
                    "key":     dst,
                    "name":    meta.get("col_name", ""),
                    "type":    meta.get("col_type", "text"),
                    "ordinal": meta.get("ordinal", 0),
                })
        cols.sort(key=lambda c: c["ordinal"])
        return cols

    def _val_key(self, val: str, author: str, scopes: List[str]) -> str:
        existing = self.cortex.resolve_alias(val)
        if existing:
            return existing
        return self.cortex.put_chunk(
            content=val,
            meta={"type": "rec_value"},
            author=author,
            scopes=scopes,
        )

    # ── operators ─────────────────────────────────────────────────────────────

    def op_new(
        self,
        name:        str,
        cols:        str,
        description: str = "",
    ) -> Dict[str, Any]:
        """[table.new] Create a table with a declared column schema.

        name        — table name; registers alias tbl:<name> (first-wins policy)
        cols        — comma-separated column definitions: "col1[:type],col2[:type],..."
                      Types: text (default) | int | float | bool | date
        description — optional human-readable description for the table atom

        Examples:
          table.new name="users" cols="id:int,name:text,email:text"
          table.new name="ohlcv" cols="date:date,open:float,high:float,low:float,close:float,volume:int"
          table.new name="inventory" cols="sku:text,qty:int,price:float" description="Product inventory"
        """
        if not name:
            raise ValueError("'name' is required.")
        col_defs = _parse_cols(cols)

        author, scopes = self._author_scopes()
        ts = time.time()

        tbl_key = self.cortex.put_chunk(
            content=description or f"[table:{name}]",
            meta={"type": "table", "name": name, "created_at": ts},
            author=author,
            scopes=scopes,
        )

        alias = f"tbl:{name}"
        if not self.cortex.resolve_alias(alias):
            self.cortex.put_alias(tbl_key, alias)

        col_results = []
        for ordinal, (col_name, col_type) in enumerate(col_defs):
            col_key = self.cortex.put_chunk(
                content=f"col:{col_name} ({col_type})",
                meta={
                    "type":      "table_col",
                    "col_name":  col_name,
                    "col_type":  col_type,
                    "ordinal":   ordinal,
                    "table_key": tbl_key,
                },
                author=author,
                scopes=scopes,
            )
            self.cortex.put_link(tbl_key, col_key, "tbl:col", author=author)
            self.cortex.add_to_set(self._tbl_set(name, self._COL_SUFFIX), col_key)
            col_results.append({"name": col_name, "type": col_type, "ordinal": ordinal})

        logger.debug("[TableConcept] created table %s key=%s cols=%d", name, tbl_key[:8], len(col_defs))
        return {"key": tbl_key, "name": name, "alias": alias, "columns": col_results}

    def op_get(self, table: str) -> Dict[str, Any]:
        """[table.get] Retrieve the table schema (columns and row count).

        table — table name, alias tbl:<name>, or atom key
        """
        tbl_key  = self._resolve_table(table)
        tbl_name = self._tbl_name(tbl_key, fallback=table)
        cols     = self._get_columns(tbl_key)
        row_keys = self.cortex.get_collection_members(self._tbl_set(tbl_name, self._ROW_SUFFIX))
        return {
            "key":       tbl_key,
            "name":      tbl_name,
            "alias":     f"tbl:{tbl_name}",
            "columns":   cols,
            "row_count": len(row_keys),
        }

    def op_col_add(self, table: str, name: str, type: str = "text") -> Dict[str, Any]:
        """[table.col.add] Add a new column to an existing table.

        table — table name, alias, or key
        name  — column name (valid identifier, unique within this table)
        type  — text | int | float | bool | date  (default: text)

        Existing rows will have NULL for the new column until explicitly set.
        """
        tbl_key  = self._resolve_table(table)
        tbl_name = self._tbl_name(tbl_key, fallback=table)

        col_type = type.lower()
        if col_type not in _VALID_TYPES:
            raise ValueError(f"Unknown type '{col_type}'. Valid: {', '.join(sorted(_VALID_TYPES))}")
        if not name.isidentifier():
            raise ValueError(f"Column name '{name}' must be a valid identifier.")

        existing = [c["name"] for c in self._get_columns(tbl_key)]
        if name in existing:
            raise ValueError(f"Column '{name}' already exists in table '{tbl_name}'.")

        author, scopes = self._author_scopes()
        ordinal = len(existing)

        col_key = self.cortex.put_chunk(
            content=f"col:{name} ({col_type})",
            meta={
                "type":      "table_col",
                "col_name":  name,
                "col_type":  col_type,
                "ordinal":   ordinal,
                "table_key": tbl_key,
            },
            author=author,
            scopes=scopes,
        )
        self.cortex.put_link(tbl_key, col_key, "tbl:col", author=author)
        self.cortex.add_to_set(self._tbl_set(tbl_name, self._COL_SUFFIX), col_key)

        return {
            "status": "added",
            "table":  tbl_name,
            "column": {"name": name, "type": col_type, "ordinal": ordinal},
        }

    def op_col_ls(self, table: str) -> Dict[str, Any]:
        """[table.col.ls] List columns in ordinal order.

        table — table name, alias, or key
        """
        tbl_key  = self._resolve_table(table)
        tbl_name = self._tbl_name(tbl_key, fallback=table)
        return {"table": tbl_name, "columns": self._get_columns(tbl_key)}

    def op_row_add(
        self,
        table:  str,
        values: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """[table.row.add] Insert a row.

        table    — table name, alias, or key
        (others) — column=value pairs passed as extra CLI arguments

        Unknown column names are rejected.  Columns may be omitted (NULL).
        Identical values share one content-addressed atom (same as rec.*).
        The row atom's content encodes a nanosecond timestamp so that even
        identical-valued rows remain distinct atoms when inserted at different times.

        Example:
          table.row.add table=users id=1 name="Henri" email="h@example.com"
          table.row.add table=ohlcv date=2025-01-02 open=150.0 high=155.3 low=149.8 close=153.1 volume=8420000
        """
        tbl_key  = self._resolve_table(table)
        tbl_name = self._tbl_name(tbl_key, fallback=table)

        cols_info = self._get_columns(tbl_key)
        declared  = {c["name"]: c["type"] for c in cols_info}
        vals      = values or {}

        unknown = set(vals.keys()) - set(declared.keys())
        if unknown:
            raise ValueError(
                f"Unknown column(s): {sorted(unknown)}. "
                f"Table '{tbl_name}' declares: {sorted(declared.keys())}"
            )

        author, scopes = self._author_scopes()
        ts    = time.time()
        ts_ns = time.time_ns()

        row_key = self.cortex.put_chunk(
            content=f"[ row:{ts_ns} in {tbl_name} ]",
            meta={
                "type":       "rec",
                "rec_type":   "tbl_row",
                "table_key":  tbl_key,
                "created_at": ts,
            },
            author=author,
            scopes=scopes,
        )

        self.cortex.put_link(row_key, tbl_key, "instance_of", author=author)
        self.cortex.put_link(tbl_key, row_key, "tbl:row",     author=author)

        for col_name, raw_val in vals.items():
            if raw_val is None or str(raw_val).strip() == "":
                continue
            vk = self._val_key(str(raw_val), author, scopes)
            self.cortex.put_link(row_key, vk, f"rec:{col_name}", author=author)

        self.cortex.add_to_set(self._tbl_set(tbl_name, self._ROW_SUFFIX), row_key)
        self.cortex.add_to_set("set:rec:tbl_row", row_key)

        return {
            "status":  "inserted",
            "row_key": row_key,
            "table":   tbl_name,
            "values":  {k: str(v) for k, v in vals.items() if v is not None},
        }

    def op_row_get(self, table: str, row: str) -> Dict[str, Any]:
        """[table.row.get] Retrieve a single row as a column-keyed dict.

        table — table name, alias, or key
        row   — row atom key
        """
        tbl_key  = self._resolve_table(table)
        tbl_name = self._tbl_name(tbl_key, fallback=table)

        cols_ordered   = self._get_columns(tbl_key)
        declared_names = {c["name"] for c in cols_ordered}
        row_key        = self.cortex.resolve_alias(row) or row

        links    = self.cortex.get_adjacent_links(row_key)
        cell_map: Dict[str, str] = {}
        for dst, rel in links:
            if rel.startswith("rec:"):
                col = rel[4:]
                if col in declared_names:
                    cell_map[col] = self.cortex.get_chunk(dst) or ""

        return {
            "table":   tbl_name,
            "row_key": row_key,
            "data":    {c["name"]: cell_map.get(c["name"]) for c in cols_ordered},
        }

    def op_row_rm(self, table: str, row: str) -> Dict[str, Any]:
        """[table.row.rm] Remove a row.

        table — table name, alias, or key
        row   — row atom key
        """
        tbl_key  = self._resolve_table(table)
        tbl_name = self._tbl_name(tbl_key, fallback=table)
        row_key  = self.cortex.resolve_alias(row) or row
        self.cortex.drop_chunk(row_key, requester_scopes=self.allowed_scopes)
        return {"status": "removed", "row_key": row_key, "table": tbl_name}

    def op_ls(self, table: str, limit: int = 100) -> Dict[str, Any]:
        """[table.ls] List rows as column-keyed dicts.

        table — table name, alias, or key
        limit — max rows to return (default 100)

        Rows are returned in set-membership order (typically insertion order).
        """
        tbl_key      = self._resolve_table(table)
        tbl_name     = self._tbl_name(tbl_key, fallback=table)
        cols_ordered = self._get_columns(tbl_key)
        col_names    = [c["name"] for c in cols_ordered]
        declared     = set(col_names)
        scopes       = self.allowed_scopes

        row_keys = self.cortex.get_collection_members(
            self._tbl_set(tbl_name, self._ROW_SUFFIX)
        )

        rows: List[Dict[str, Any]] = []
        for rk in row_keys[:limit]:
            row_meta = self.cortex.get_meta(rk) or {}
            if row_meta.get("type") != "rec":
                continue
            if scopes and not self.cortex.check_access(rk, scopes):
                continue
            links    = self.cortex.get_adjacent_links(rk)
            cell_map = {
                rel[4:]: self.cortex.get_chunk(dst) or ""
                for dst, rel in links
                if rel.startswith("rec:") and rel[4:] in declared
            }
            rows.append({"key": rk, "data": {c: cell_map.get(c) for c in col_names}})

        return {"table": tbl_name, "columns": col_names, "rows": rows, "count": len(rows)}

    def op_view(self, table: str, limit: int = 100) -> Dict[str, Any]:
        """[table.view] Show table rows as a formatted CLI table (textview format).

        table — table name, alias, or key
        limit — max rows to display (default 100)

        Calls op_ls internally and projects the result to TextViewConcept.table
        so the renderer uses rich.table.Table for display.
        """
        from lib.akasha.concepts.textview import TextViewConcept
        result = self.op_ls(table, limit=limit)
        title  = f"tbl:{result['table']}  {result['count']} row(s)"
        return TextViewConcept.table(
            title   = title,
            columns = result["columns"],
            rows    = [r["data"] for r in result["rows"]],
        )

    def op_export(self, table: str) -> Dict[str, Any]:
        """[table.export] Export the table as RFC 4180 CSV text.

        table — table name, alias, or key

        Returns {"table": <name>, "csv": "<CSV text>", "row_count": <N>}
        The first row of the CSV is the column header.
        """
        result    = self.op_ls(table, limit=10_000)
        col_names = result["columns"]
        rows      = result["rows"]

        buf    = io.StringIO()
        writer = _csv.writer(buf, dialect="excel")
        writer.writerow(col_names)
        for row in rows:
            writer.writerow([row["data"].get(c) or "" for c in col_names])

        return {"table": result["table"], "csv": buf.getvalue(), "row_count": len(rows)}

    def op_import(self, table: str, csv_text: str) -> Dict[str, Any]:
        """[table.import] Import CSV rows into a table.

        table  — table name, alias, or key
        csv=   — RFC 4180 CSV text; first row must be the column header

        The header must use declared column names (column order may differ from
        table.new).  Unknown header columns are rejected.  Missing columns are
        treated as NULL.

        Example (CLI):
          table.import table=users csv="id,name,email\\n1,Henri,h@e.com\\n2,Alice,a@e.com"
        """
        tbl_key  = self._resolve_table(table)
        tbl_name = self._tbl_name(tbl_key, fallback=table)
        declared = {c["name"] for c in self._get_columns(tbl_key)}

        reader = _csv.reader(io.StringIO(csv_text))
        header = next(reader, None)
        if header is None:
            return {"status": "empty", "table": tbl_name, "imported": 0}

        header  = [h.strip() for h in header]
        unknown = set(header) - declared
        if unknown:
            raise ValueError(
                f"CSV header contains unknown column(s): {sorted(unknown)}. "
                f"Declared columns: {sorted(declared)}"
            )

        imported = errors = 0
        for row_vals in reader:
            vals = {h: v for h, v in zip(header, row_vals) if v.strip()}
            try:
                self.op_row_add(table=table, values=vals)
                imported += 1
            except Exception as exc:
                logger.warning("[TableConcept.import] row error: %s", exc)
                errors += 1

        return {
            "status":   "imported",
            "table":    tbl_name,
            "imported": imported,
            "errors":   errors,
        }

    def op_rm(self, table: str) -> Dict[str, Any]:
        """[table.rm] Drop an entire table — removes all rows, columns, and the table atom.

        table — table name, alias, or key

        WARNING: this is irreversible.  Row atoms (and their rec: links) are deleted.
        Value atoms are content-addressed and may be shared; they are NOT deleted.
        """
        tbl_key  = self._resolve_table(table)
        tbl_name = self._tbl_name(tbl_key, fallback=table)
        scopes   = self.allowed_scopes

        row_keys = self.cortex.get_collection_members(
            self._tbl_set(tbl_name, self._ROW_SUFFIX)
        )
        for rk in row_keys:
            try:
                self.cortex.drop_chunk(rk, requester_scopes=scopes)
            except Exception:
                pass

        for col in self._get_columns(tbl_key):
            try:
                self.cortex.drop_chunk(col["key"], requester_scopes=scopes)
            except Exception:
                pass

        self.cortex.drop_chunk(tbl_key, requester_scopes=scopes)

        return {"status": "dropped", "table": tbl_name, "rows_removed": len(row_keys)}
