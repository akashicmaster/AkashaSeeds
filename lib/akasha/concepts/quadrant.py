"""
QuadrantConcept — 4-quadrant scatter plot concept model.

Reads rec atoms from any set, extracts two numeric attributes as X / Y
axes, and returns a TextViewConcept.scatter() view for the CLI renderer.

Typical workflow:
  rec.new type=fruit content="Mango"  sweetness=0.9 acidity=0.2
  rec.new type=fruit content="Lemon"  sweetness=0.1 acidity=0.95
  rec.new type=fruit content="Grape"  sweetness=0.7 acidity=0.5
  ...
  quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness

The scatter TextViewConcept is rendered as an ASCII 4-quadrant plot by
the renderer, with no web browser or external library required.
"""

import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Quadrant")


class QuadrantConcept(BaseConcept):
    """
    4-quadrant scatter plot operator.

    Operand  : rec atoms carrying two numeric attributes
    Operator : quadrant.plot — project any rec set into a scatter view
    Agent    : any AkashaSession client
    """

    CONCEPT_PREFIX = "quadrant"
    CONCEPT_LABEL  = "4-quadrant scatter plot from rec attributes"
    CONCEPT_METHODS = {
        "plot": {
            "op":     "op_plot",
            "action": "read",
            "args":   ["in_set", "x", "y"],
            "desc":   (
                "Render a 4-quadrant scatter plot from a set of rec atoms: "
                "quadrant.plot in_set=<set> x=<attr> y=<attr> "
                "[label=content] [x_mid=<float>] [y_mid=<float>]"
            ),
        },
    }

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _set_name(s: str) -> str:
        return s if s.startswith("set:") else f"set:{s}"

    @staticmethod
    def _to_float(s: Any) -> Optional[float]:
        try:
            sv = str(s)
            if sv.startswith("[") and "\n" in sv:
                sv = sv.split("\n", 1)[1]
            return float(sv.replace(",", "").replace("_", ""))
        except (ValueError, TypeError):
            return None

    # ── operator ─────────────────────────────────────────────────────────────

    def op_plot(
        self,
        in_set:  str,
        x:       str,
        y:       str,
        label:   str = "content",
        x_mid:   Optional[float] = None,
        y_mid:   Optional[float] = None,
        x_label: str = "",
        y_label: str = "",
        q1:      str = "",
        q2:      str = "",
        q3:      str = "",
        q4:      str = "",
    ) -> Dict[str, Any]:
        """[quadrant.plot] Render rec atoms in a set as a 4-quadrant scatter plot.

        in_set  — set name (e.g. "set:rec:fruit" or bare "rec:fruit")
        x       — attribute name to use as the horizontal axis (must be numeric)
        y       — attribute name to use as the vertical axis (must be numeric)
        label   — attribute to use as point label (default: atom content)
        x_mid   — X quadrant divider (default: midpoint of x values)
        y_mid   — Y quadrant divider (default: midpoint of y values)
        x_label — X axis display label (default: same as x)
        y_label — Y axis display label (default: same as y)
        q1..q4  — optional quadrant corner labels (q1=top-right, q2=top-left,
                  q3=bottom-left, q4=bottom-right)
        """
        if not in_set:
            raise ValueError("'in_set' is required.")
        if not x or not y:
            raise ValueError("Both 'x' and 'y' attribute names are required.")

        scopes  = self.allowed_scopes
        rel_x   = f"rec:{x}"
        rel_y   = f"rec:{y}"
        rel_lbl = f"rec:{label}" if label != "content" else None

        keys = self.cortex.get_collection_members(self._set_name(in_set))
        if not keys:
            raise ValueError(f"Set '{in_set}' is empty or does not exist.")

        points: List[Dict[str, Any]] = []

        for k in keys:
            if scopes and not self.cortex.check_access(k, scopes):
                continue

            links = self.cortex.get_adjacent_links(k)
            attr_map: Dict[str, str] = {}
            for dst, rel in links:
                if rel.startswith("rec:"):
                    attr_map[rel[4:]] = self.cortex.get_chunk(dst) or ""

            x_raw = attr_map.get(x)
            y_raw = attr_map.get(y)
            if x_raw is None or y_raw is None:
                continue

            x_f = self._to_float(x_raw)
            y_f = self._to_float(y_raw)
            if x_f is None or y_f is None:
                logger.debug("Skipping %s — non-numeric %s or %s", k[:12], x, y)
                continue

            if rel_lbl:
                lbl = attr_map.get(label) or (self.cortex.get_chunk(k) or "")[:24]
            else:
                # Prefer rec:content attribute over raw atom content so that
                # lens.flatten snap atoms show the source's readable name
                lbl = attr_map.get("content") or (self.cortex.get_chunk(k) or "")[:24]

            points.append({"label": lbl, "x": x_f, "y": y_f})

        if not points:
            raise ValueError(
                f"No atoms in '{in_set}' have both numeric '{x}' and '{y}' attributes."
            )

        # Auto-compute quadrant midpoints from data range
        if x_mid is None:
            xs = [p["x"] for p in points]
            x_mid = (min(xs) + max(xs)) / 2
        if y_mid is None:
            ys = [p["y"] for p in points]
            y_mid = (min(ys) + max(ys)) / 2

        from lib.akasha.concepts.textview import TextViewConcept
        return TextViewConcept.scatter(
            title           = f"{in_set}  ·  {x} × {y}",
            points          = points,
            x_label         = x_label or x,
            y_label         = y_label or y,
            x_mid           = x_mid,
            y_mid           = y_mid,
            quadrant_labels = {
                k: v for k, v in {"q1": q1, "q2": q2, "q3": q3, "q4": q4}.items() if v
            },
        )
