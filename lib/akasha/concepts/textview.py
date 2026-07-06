"""
TextViewConcept — canonical display format for CLI rendering.

The mirror of a web GUI's view-model layer.  Any concept model that wants
clean CLI output wraps its result with one of the static factory methods here.
The renderer checks ``_view`` first — dispatch is deterministic, not heuristic.

View types
──────────
table   columns + flat row dicts  →  rich.table.Table
tree    root + recursive children →  rich.tree.Tree
list    flat items with meta/detail  →  ANSI list
keyval  key-value pairs              →  ANSI two-column
chart   numeric series               →  Unicode sparkline / bar

Migration contract
──────────────────
Existing op_* methods are not required to adopt TextViewConcept immediately.
The renderer's legacy heuristic dispatch remains as fallback.
New operations and new concept models use TextViewConcept from day one.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from lib.akasha.concepts.base import BaseConcept

# ── view type tokens ──────────────────────────────────────────────────────────

TABLE   = "table"
TREE    = "tree"
LIST    = "list"
KEYVAL  = "keyval"
CHART   = "chart"
SCATTER = "scatter"
HEATMAP = "heatmap"


class TextViewConcept(BaseConcept):
    """
    Protocol class: static factory functions for CLI view descriptors.

    No op_* commands — TextViewConcept is not driven by user input.
    It is the agreed-upon output format for concept models that want
    deterministic terminal rendering.
    """

    CONCEPT_PREFIX  = "textview"
    CONCEPT_LABEL   = "Canonical CLI display format (textview protocol)"
    CONCEPT_METHODS: Dict[str, Any] = {}   # no user-facing commands

    # ── factories ─────────────────────────────────────────────────────────────

    @staticmethod
    def table(
        title:   str,
        columns: List[str],
        rows:    List[Dict[str, Any]],
        count:   Optional[int] = None,
    ) -> Dict[str, Any]:
        """Tabular view rendered with rich.table.Table.

        rows must be plain {col: val} dicts — no {key, data} wrappers.
        """
        return {
            "_view":   TABLE,
            "title":   title,
            "columns": columns,
            "rows":    rows,
            "count":   count if count is not None else len(rows),
        }

    @staticmethod
    def tree(
        title:    str,
        root:     str,
        children: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Tree view rendered with rich.tree.Tree.

        Each child: {"label": str, "sublabel": str (opt), "children": [...] (opt)}
        Nesting is arbitrary.
        """
        return {
            "_view":    TREE,
            "title":    title,
            "root":     root,
            "children": children,
        }

    @staticmethod
    def list_(
        title: str,
        items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Flat list view.

        Each item: {"label": str, "meta": str (opt), "detail": str (opt)}
        """
        return {
            "_view": LIST,
            "title": title,
            "items": items,
        }

    @staticmethod
    def keyval(
        title: str,
        pairs: List[Union[Tuple[str, str], Dict[str, str]]],
    ) -> Dict[str, Any]:
        """Key-value view for schema display or single-record detail.

        pairs: list of (key, val) tuples  OR  {"key": k, "val": v} dicts.
        """
        return {
            "_view": KEYVAL,
            "title": title,
            "pairs": pairs,
        }

    @staticmethod
    def chart(
        title:      str,
        series:     List[float],
        labels:     Optional[List[str]] = None,
        chart_type: str = "sparkline",
    ) -> Dict[str, Any]:
        """Chart view — Unicode sparkline or horizontal bar.

        chart_type: "sparkline" | "bar"
        """
        return {
            "_view":  CHART,
            "title":  title,
            "series": series,
            "labels": labels or [],
            "type":   chart_type,
        }

    @staticmethod
    def heatmap(
        title:       str,
        matrix:      List[List[float]],
        x_labels:    List[str],
        y_labels:    List[str],
        x_attr:      str = "x",
        y_attr:      str = "y",
        value_label: str = "count",
    ) -> Dict[str, Any]:
        """2-D intensity heatmap view.

        matrix[row][col] — row 0 is the HIGHEST y bin; values normalised 0.0–1.0.
        x_labels — one label per column (left → right).
        y_labels — one label per row (top → bottom, i.e. high → low y).
        value_label — what the intensity represents ("count", attribute name, …).
        """
        return {
            "_view":       HEATMAP,
            "title":       title,
            "matrix":      matrix,
            "x_labels":    x_labels,
            "y_labels":    y_labels,
            "x_attr":      x_attr,
            "y_attr":      y_attr,
            "value_label": value_label,
        }

    @staticmethod
    def scatter(
        title:            str,
        points:           List[Dict[str, Any]],
        x_label:          str = "x",
        y_label:          str = "y",
        x_mid:            Optional[float] = None,
        y_mid:            Optional[float] = None,
        quadrant_labels:  Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """4-quadrant scatter plot view.

        points: list of {"label": str, "x": float, "y": float}
        x_mid / y_mid: quadrant dividing lines (auto-computed from data midpoint if omitted)
        quadrant_labels: {"q1": top-right, "q2": top-left, "q3": bottom-left, "q4": bottom-right}
        """
        return {
            "_view":           "scatter",
            "title":           title,
            "points":          points,
            "x_label":         x_label,
            "y_label":         y_label,
            "x_mid":           x_mid,
            "y_mid":           y_mid,
            "quadrant_labels": quadrant_labels or {},
        }

    # ── node / item builder helpers ───────────────────────────────────────────

    @staticmethod
    def node(
        label:    str,
        sublabel: str = "",
        children: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build a tree node dict."""
        n: Dict[str, Any] = {"label": label}
        if sublabel:
            n["sublabel"] = sublabel
        if children:
            n["children"] = children
        return n

    @staticmethod
    def item(
        label:  str,
        meta:   str = "",
        detail: str = "",
    ) -> Dict[str, Any]:
        """Build a list item dict."""
        i: Dict[str, Any] = {"label": label}
        if meta:
            i["meta"] = meta
        if detail:
            i["detail"] = detail
        return i
