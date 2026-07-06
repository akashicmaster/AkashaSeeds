"""
RecConcept — schema-free record model.

  Operand  : Atom (record atom, value atoms), Set (index sets)
  Operator : rec.new / rec.set / rec.idx / rec.get / rec.ls / rec.sum / rec.rm
  Agent    : any AkashaSession client — human, LLM, sensor, script

Akasha's methodology: Operand, Operator, and Agent are kept strictly separate.
Data atoms carry no behaviour. Operators are registered independently of the
data they transform. Agents apply any operator they are authorised for.

We do not put methods inside data objects.
That is the trap existing object-oriented frameworks fell into.

Schema layer
────────────
This model enforces nothing. Granularity is free. Attribute keys and value
types carry the same freedom as Atoms themselves — the identity of a value
is its content hash, not a column definition.

If schema enforcement is needed, layer an audit concept model on top:

    rec.*          ← this file: zero constraints, maximum freedom
    <audit>.*      ← future overlay: required-field checks, type coercion, etc.

The same layering principle applies everywhere in Akasha. Start free,
add constraints only where the problem demands them.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Rec")


def _coerce_new(data: Dict[str, Any]) -> Dict[str, Any]:
    """Pass content/type explicitly; collect everything else as inline_attrs."""
    reserved = {"content", "type"}
    return {
        "content":      data.get("content", ""),
        "type":         data.get("type", ""),
        "inline_attrs": {k: v for k, v in data.items() if k not in reserved},
    }


class RecConcept(BaseConcept):
    """
    Schema-free record model.

    Records are Atoms.  Attributes are typed links (rel = "rec:{attr_key}").
    Values are Atoms — content-addressed, so identical values share one Atom.
    Index sets are arbitrary: any set name the agent chooses to use.
    """

    CONCEPT_PREFIX = "rec"
    CONCEPT_METHODS = {
        "new":   {"op": "op_new", "coerce": _coerce_new},
        "set":   {"op": "op_set"},
        "idx":   {"op": "op_idx"},
        "get":   {"op": "op_get"},
        "ls":    {"op": "op_ls"},
        "sum":   {"op": "op_sum"},
        "rm":    {"op": "op_rm"},
        "table": {
            "op":     "op_table",
            "action": "read",
            "args":   ["in_set"],
            "desc":   "Show records in a set as a formatted table: rec.table in_set=<set> [type=<t>] [limit=N]",
        },
        "hist": {
            "op":     "op_hist",
            "action": "read",
            "args":   ["attr", "in_set"],
            "desc":   "Histogram of a numeric attribute: rec.hist attr=<a> in_set=<set> [bins=10]",
        },
        "heatmap": {
            "op":     "op_heatmap",
            "action": "read",
            "args":   ["x", "y", "in_set"],
            "desc":   (
                "2-D heatmap of two numeric attributes: "
                "rec.heatmap x=<a> y=<b> in_set=<set> [x_bins=8] [y_bins=6] [value=<attr>]"
            ),
        },
    }

    # ── helpers ──────────────────────────────────────────────────────────────

    def _author_scopes(self):
        aid = getattr(self.session, "client_id", "system")
        return aid, [f"owner:user_{aid}", f"view:user_{aid}"]

    def _val_key(self, val: str, author: str, scopes: List[str]) -> str:
        """Resolve alias → existing key; otherwise store value as a content-addressed atom."""
        existing = self.cortex.resolve_alias(val)
        if existing:
            return existing
        return self.cortex.put_chunk(
            content=val,
            meta={"type": "rec_value"},
            author=author,
            scopes=scopes,
        )

    @staticmethod
    def _set_name(s: str) -> str:
        """Normalise a set name: bare names get 'set:' prefix."""
        return s if s.startswith("set:") else f"set:{s}"

    # ── operators ─────────────────────────────────────────────────────────────

    def op_new(
        self,
        content: str = "",
        type: str = "",
        inline_attrs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """[rec.new] Create a new record atom.

        content      — human-readable description (any text)
        type         — concept atom alias or key (type hint; not enforced)
        inline_attrs — any additional key=value pairs stored as attributes

        Extra CLI arguments (date=..., payee=..., amount=...) land in inline_attrs
        via the coerce function and are stored immediately as rec:{key} links.
        """
        author, scopes = self._author_scopes()
        text = content or (f"[ rec:{type} ]" if type else "[ rec ]")
        meta: Dict[str, Any] = {"type": "rec", "created_at": time.time()}
        if type:
            meta["rec_type"] = type

        key = self.cortex.put_chunk(content=text, meta=meta, author=author, scopes=scopes)

        # Type hint: instance_of link + type-based index set
        if type:
            type_key = self.cortex.resolve_alias(type) or type
            self.cortex.put_link(key, type_key, "instance_of", author=author)
            self.cortex.add_to_set(self._set_name(f"rec:{type}"), key)

        # Inline attribute links
        for attr_key, attr_val in (inline_attrs or {}).items():
            if attr_val is None:
                continue
            vk = self._val_key(str(attr_val), author, scopes)
            self.cortex.put_link(key, vk, f"rec:{attr_key}", author=author)

        logger.debug("[RecConcept] new %s (type=%s)", key[:8], type or "—")
        return {"key": key, "type": type or None, "content": text}

    def op_set(self, key: str, attr: str, val: str) -> Dict[str, Any]:
        """[rec.set] Add or replace an attribute on a record.

        key  — record atom key
        attr — attribute name (any string; no schema constraint)
        val  — value text or alias
        """
        if not key or not attr:
            raise ValueError("key and attr are required.")
        author, scopes = self._author_scopes()
        vk = self._val_key(val, author, scopes)
        self.cortex.put_link(key, vk, f"rec:{attr}", author=author)
        return {"status": "set", "key": key, "attr": attr, "val_key": vk}

    def op_idx(self, key: str, sets: str) -> Dict[str, Any]:
        """[rec.idx] Add a record to one or more index sets.

        key  — record atom key
        sets — comma-separated set names (bare names get 'set:' prefix)
        """
        if not key or not sets:
            raise ValueError("key and sets are required.")
        set_list = [self._set_name(s.strip()) for s in sets.split(",") if s.strip()]
        for s in set_list:
            self.cortex.add_to_set(s, key)
        return {"status": "indexed", "key": key, "sets": set_list}

    def op_get(self, key: str) -> Dict[str, Any]:
        """[rec.get] Retrieve a record with all its attributes."""
        if not key:
            raise ValueError("key is required.")
        content = self.cortex.get_chunk(key) or ""
        meta    = self.cortex.get_meta(key) or {}
        links   = self.cortex.get_adjacent_links(key)  # [[dst, rel], ...]

        attrs: Dict[str, str] = {}
        for dst, rel in links:
            if rel.startswith("rec:"):
                attrs[rel[4:]] = self.cortex.get_chunk(dst) or dst

        return {
            "key":     key,
            "content": content,
            "type":    meta.get("rec_type", ""),
            "attrs":   attrs,
        }

    def op_ls(
        self,
        type: str = "",
        in_set: str = "",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """[rec.ls] List records by type and/or set membership.

        type   — concept atom alias used at rec.new time (optional)
        in_set — set name to filter by (optional)
        At least one of type or in_set is required.
        """
        scopes = self.allowed_scopes

        if type and in_set:
            a = set(self.cortex.get_collection_members(self._set_name(f"rec:{type}")))
            b = set(self.cortex.get_collection_members(self._set_name(in_set)))
            keys = list(a & b)
        elif type:
            keys = self.cortex.get_collection_members(self._set_name(f"rec:{type}"))
        elif in_set:
            keys = self.cortex.get_collection_members(self._set_name(in_set))
        else:
            raise ValueError("Provide type= and/or in_set= to list records.")

        records = []
        for k in keys[:limit]:
            if scopes and not self.cortex.check_access(k, scopes):
                continue
            records.append({"key": k, "preview": (self.cortex.get_chunk(k) or "")[:60]})

        return {
            "records": records,
            "count":   len(records),
            "type":    type or None,
            "in_set":  in_set or None,
        }

    def op_sum(
        self,
        attr: str,
        in_set: str = "",
        type: str = "",
    ) -> Dict[str, Any]:
        """[rec.sum] Sum a numeric attribute across records in a set.

        attr   — attribute key (e.g. "amount")
        in_set — index set name (optional)
        type   — type filter (optional)
        At least one of in_set or type is required.
        """
        if not attr:
            raise ValueError("attr is required.")
        scopes  = self.allowed_scopes
        rel_key = f"rec:{attr}"

        if in_set:
            keys = self.cortex.get_collection_members(self._set_name(in_set))
        elif type:
            keys = self.cortex.get_collection_members(self._set_name(f"rec:{type}"))
        else:
            raise ValueError("Provide in_set= or type= to scope the sum.")

        total = 0.0
        count = skipped = 0
        for k in keys:
            if scopes and not self.cortex.check_access(k, scopes):
                continue
            for dst, rel in self.cortex.get_adjacent_links(k):
                if rel == rel_key:
                    raw = self.cortex.get_chunk(dst) or ""
                    try:
                        total += float(raw.replace(",", "").replace("_", ""))
                        count += 1
                    except (ValueError, TypeError):
                        skipped += 1
                    break

        return {
            "attr":    attr,
            "sum":     total,
            "count":   count,
            "skipped": skipped,
            "in_set":  in_set or None,
            "type":    type or None,
        }

    def op_table(
        self,
        in_set: str = "",
        type: str = "",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """[rec.table] Display records in a set as a formatted table.

        in_set — set name to read from (e.g. "set:my_export")
        type   — optional type filter (combined with in_set when both given)
        limit  — max rows to show (default 100)

        Returns the same shape as tbl.ls so the table renderer handles display.
        Attribute columns are discovered from the actual rec: links present in
        the set — no schema declaration required.

        Typical use after lens.flatten:
          lens src=tbl:expenses
          lens.flatten into=snapshot
          rec.table in_set=set:snapshot
        """
        scopes = self.allowed_scopes

        if in_set and type:
            a    = set(self.cortex.get_collection_members(self._set_name(f"rec:{type}")))
            b    = set(self.cortex.get_collection_members(self._set_name(in_set)))
            keys = list(a & b)
        elif in_set:
            keys = self.cortex.get_collection_members(self._set_name(in_set))
        elif type:
            keys = self.cortex.get_collection_members(self._set_name(f"rec:{type}"))
        else:
            raise ValueError("Provide in_set= and/or type= to scope the table.")

        col_order: List[str] = []
        col_seen:  set       = set()
        rows_raw:  List[Dict[str, Any]] = []

        for k in keys[:limit]:
            if scopes and not self.cortex.check_access(k, scopes):
                continue
            attrs: Dict[str, str] = {}
            for dst, rel in self.cortex.get_adjacent_links(k):
                if rel.startswith("rec:"):
                    col = rel[4:]
                    attrs[col] = self.cortex.get_chunk(dst) or ""
                    if col not in col_seen:
                        col_seen.add(col)
                        col_order.append(col)
            rows_raw.append({"key": k, "data": attrs})

        from lib.akasha.concepts.textview import TextViewConcept
        title = in_set or f"rec:{type}"
        return TextViewConcept.table(
            title   = title,
            columns = col_order,
            rows    = [r["data"] for r in rows_raw],
        )

    # ── helpers shared by hist / heatmap ─────────────────────────────────────

    def _collect_float_attr(
        self,
        attr: str,
        keys: List[str],
    ) -> List[float]:
        """Collect numeric values of rec:{attr} from a list of atom keys."""
        rel_key = f"rec:{attr}"
        scopes  = self.allowed_scopes
        values: List[float] = []
        for k in keys:
            if scopes and not self.cortex.check_access(k, scopes):
                continue
            for dst, rel in self.cortex.get_adjacent_links(k):
                if rel == rel_key:
                    raw = self.cortex.get_chunk(dst) or ""
                    try:
                        values.append(float(raw.replace(",", "").replace("_", "")))
                    except (ValueError, TypeError):
                        pass
                    break
        return values

    def _resolve_keys(self, in_set: str, type: str) -> List[str]:
        """Resolve in_set / type arguments to a list of atom keys."""
        if in_set and type:
            a = set(self.cortex.get_collection_members(self._set_name(f"rec:{type}")))
            b = set(self.cortex.get_collection_members(self._set_name(in_set)))
            return list(a & b)
        if in_set:
            return self.cortex.get_collection_members(self._set_name(in_set))
        if type:
            return self.cortex.get_collection_members(self._set_name(f"rec:{type}"))
        raise ValueError("Provide in_set= and/or type= to scope the operation.")

    # ── operators ─────────────────────────────────────────────────────────────

    def op_hist(
        self,
        attr:   str,
        in_set: str = "",
        type:   str = "",
        bins:   int = 10,
    ) -> Dict[str, Any]:
        """[rec.hist] Horizontal bar histogram of a numeric attribute.

        attr   — attribute name to plot (must be numeric)
        in_set — index set name (optional)
        type   — type filter (optional; combined with in_set when both given)
        bins   — number of buckets (default 10)
        """
        if not attr:
            raise ValueError("attr is required.")
        keys   = self._resolve_keys(in_set, type)
        values = self._collect_float_attr(attr, keys)
        if not values:
            raise ValueError(
                f"No numeric '{attr}' values found in '{in_set or ('rec:' + type)}'."
            )

        mn, mx = min(values), max(values)
        rng    = mx - mn or 1.0
        counts = [0] * bins
        for v in values:
            idx = min(bins - 1, int((v - mn) / rng * bins))
            counts[idx] += 1

        step   = rng / bins
        labels = [f"{mn + i * step:.4g}" for i in range(bins)]
        title  = f"{in_set or ('rec:' + type)}  ·  {attr}  (n={len(values)})"

        from lib.akasha.concepts.textview import TextViewConcept
        return TextViewConcept.chart(
            title      = title,
            series     = [float(c) for c in counts],
            labels     = labels,
            chart_type = "bar",
        )

    def op_heatmap(
        self,
        x:      str,
        y:      str,
        in_set: str = "",
        type:   str = "",
        x_bins: int = 8,
        y_bins: int = 6,
        value:  str = "",
    ) -> Dict[str, Any]:
        """[rec.heatmap] 2-D intensity heatmap of two numeric attributes.

        x / y   — attribute names for the two axes
        in_set  — index set name (optional)
        type    — type filter (optional)
        x_bins  — horizontal resolution (default 8)
        y_bins  — vertical resolution (default 6)
        value   — optional third numeric attribute to average per cell
                  (default: frequency count)
        """
        if not x or not y:
            raise ValueError("Both x= and y= attribute names are required.")

        keys   = self._resolve_keys(in_set, type)
        xs     = self._collect_float_attr(x, keys)
        # rebuild parallel y / value arrays
        rel_x  = f"rec:{x}"
        rel_y  = f"rec:{y}"
        rel_v  = f"rec:{value}" if value else None
        scopes = self.allowed_scopes

        points: List[tuple] = []
        for k in keys:
            if scopes and not self.cortex.check_access(k, scopes):
                continue
            lmap: Dict[str, str] = {}
            for dst, rel in self.cortex.get_adjacent_links(k):
                if rel in (rel_x, rel_y) or (rel_v and rel == rel_v):
                    lmap[rel] = self.cortex.get_chunk(dst) or ""
            if rel_x not in lmap or rel_y not in lmap:
                continue
            try:
                xv = float(lmap[rel_x].replace(",", "").replace("_", ""))
                yv = float(lmap[rel_y].replace(",", "").replace("_", ""))
            except (ValueError, TypeError):
                continue
            vv: Optional[float] = None
            if rel_v and rel_v in lmap:
                try:
                    vv = float(lmap[rel_v].replace(",", "").replace("_", ""))
                except (ValueError, TypeError):
                    pass
            points.append((xv, yv, vv))

        if not points:
            raise ValueError(
                f"No atoms in '{in_set or ('rec:' + type)}' have both "
                f"numeric '{x}' and '{y}' attributes."
            )

        xv_all = [p[0] for p in points]
        yv_all = [p[1] for p in points]
        x_mn, x_mx = min(xv_all), max(xv_all)
        y_mn, y_mx = min(yv_all), max(yv_all)
        x_rng = x_mx - x_mn or 1.0
        y_rng = y_mx - y_mn or 1.0

        # counts[y_row][x_col]  (y_row 0 = highest y)
        counts: List[List[int]]         = [[0] * x_bins for _ in range(y_bins)]
        sums:   List[List[float]]       = [[0.0] * x_bins for _ in range(y_bins)]

        for xv, yv, vv in points:
            xi   = min(x_bins - 1, int((xv - x_mn) / x_rng * x_bins))
            yi_b = min(y_bins - 1, int((yv - y_mn) / y_rng * y_bins))
            yi   = y_bins - 1 - yi_b                    # flip: row 0 = high y
            counts[yi][xi] += 1
            if vv is not None:
                sums[yi][xi] += vv

        if value:
            raw = [[sums[r][c] / counts[r][c] if counts[r][c] else 0.0
                    for c in range(x_bins)] for r in range(y_bins)]
            value_label = value
        else:
            raw = [[float(counts[r][c]) for c in range(x_bins)] for r in range(y_bins)]
            value_label = "count"

        max_val = max(v for row in raw for v in row) or 1.0
        matrix  = [[v / max_val for v in row] for row in raw]

        step_x = x_rng / x_bins
        step_y = y_rng / y_bins
        x_labels = [f"{x_mn + i * step_x:.4g}" for i in range(x_bins)]
        y_labels = [f"{y_mx - i * step_y:.4g}" for i in range(y_bins)]

        scope_lbl = in_set or f"rec:{type}"
        title = (
            f"{scope_lbl}  ·  {x} × {y}"
            + (f"  [{value}]" if value else "  [freq]")
        )

        from lib.akasha.concepts.textview import TextViewConcept
        return TextViewConcept.heatmap(
            title       = title,
            matrix      = matrix,
            x_labels    = x_labels,
            y_labels    = y_labels,
            x_attr      = x,
            y_attr      = y,
            value_label = value_label,
        )

    def op_rm(self, key: str) -> Dict[str, Any]:
        """[rec.rm] Delete a record atom (removes from all sets, drops all links)."""
        if not key:
            raise ValueError("key is required.")
        scopes = self.allowed_scopes
        self.cortex.drop_chunk(key, requester_scopes=scopes)
        return {"status": "removed", "key": key}
