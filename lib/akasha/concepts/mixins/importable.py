"""
ImportableMixin — lens projection adapter base.

Any concept model that wants to appear as a candidate in `lens.match` /
`lens.cast` must:

  1. Inherit from ImportableMixin (alongside BaseConcept)
  2. Override IMPORT_SCHEMA
  3. Override match_projection(cls, profile) → score + auto-mapping
  4. Override import_projection(self, nodes, mapping, into, **opts) → result

The base implementations of match_projection and import_projection are
non-functional stubs that guarantee a safe fallback — subclasses call
super() where sensible or replace entirely.
"""

from typing import Any, Dict, List


class ImportableMixin:
    """
    Mixin for concept models that can receive a lens projection.

    IMPORT_SCHEMA declares what the model needs.
    match_projection() scores compatibility with a ProjectionProfile.
    import_projection() executes the actual atom creation.
    """

    # ── Subclass overrides this ───────────────────────────────────────────────

    IMPORT_SCHEMA: Dict[str, Any] = {
        # Unique model identifier (same as CONCEPT_PREFIX).
        "model": "",
        # Source attribute keys that MUST be present for score > 0.
        # Use "rec:" as a prefix wildcard (any rec: attr counts).
        "requires": [],
        # Source attribute keys or prefixes that raise the score when present.
        "prefers": [],
        # Minimum number of source nodes needed.
        "min_nodes": 1,
        # One-line human description shown in lens.match output.
        "description": "",
    }

    # ── Matching — classmethod (no instance needed) ───────────────────────────

    @classmethod
    def match_projection(cls, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score this model's compatibility with a ProjectionProfile.

        The base implementation:
          - Returns score=0.0 if required attrs are missing or node_count < min_nodes.
          - Scores 0.3–1.0 based on fraction of 'prefers' attrs present.

        Subclasses should override to add model-specific auto-mapping logic.

        Returns a dict with:
          score:        float  0.0–1.0 compatibility
          auto_mapping: dict   {model_field: source_attr}  suggested mapping
          auto_opts:    dict   extra kwargs to pass to import_projection
          notes:        list   human-readable explanation lines
          missing:      list   required attrs that were absent
        """
        schema  = cls.IMPORT_SCHEMA
        attrs   = profile.get("attrs", {})
        missing = []

        if profile.get("node_count", 0) < schema.get("min_nodes", 1):
            return {"score": 0.0, "auto_mapping": {}, "auto_opts": {},
                    "notes": [], "missing": ["not enough nodes"]}

        for req in schema.get("requires", []):
            if req.endswith(":"):
                # prefix wildcard — any attr starting with req counts
                if not any(a.startswith(req) for a in attrs):
                    missing.append(req + "*")
            else:
                if req not in attrs:
                    missing.append(req)

        if missing:
            return {"score": 0.0, "auto_mapping": {}, "auto_opts": {},
                    "notes": [], "missing": missing}

        prefers = schema.get("prefers", [])
        matched = 0
        for p in prefers:
            if p.endswith(":"):
                if any(a.startswith(p) for a in attrs):
                    matched += 1
            else:
                if p in attrs:
                    matched += 1

        if prefers:
            score = min(1.0, 0.3 + matched / len(prefers) * 0.7)
            notes = [f"{matched}/{len(prefers)} preferred attrs matched"]
        else:
            score = 0.5
            notes = []

        return {
            "score":        score,
            "auto_mapping": {},
            "auto_opts":    {},
            "notes":        notes,
            "missing":      [],
        }

    # ── Execution — instance method (needs self.cortex via BaseConcept) ───────

    def import_projection(
        self,
        nodes:   List,             # [(atom_key, attrs_dict, depth, meta), …]
        mapping: Dict[str, str],   # {model_field: source_attr}
        into:    str,              # target name (e.g. table name, set name)
        **opts,                    # model-specific extras (e.g. auto_cols)
    ) -> Dict[str, Any]:
        """
        Execute the projection and return a summary dict.

        nodes:   list of (atom_key, attrs, depth, meta) tuples from SourceScanner
        mapping: auto_mapping from match_projection (user may override)
        into:    human-readable name for the created target (e.g. table name)
        **opts:  extra kwargs from auto_opts (e.g. auto_cols for table)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement import_projection. "
            "Add it or remove the ImportableMixin."
        )
