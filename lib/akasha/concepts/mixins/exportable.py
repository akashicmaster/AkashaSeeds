"""
ExportableMixin — lens export adapter base.

The mirror of ImportableMixin.  Any concept model that wants to appear as a
*source* in a lens pipeline must:

  1. Inherit from ExportableMixin (alongside BaseConcept)
  2. Override EXPORT_SCHEMA
  3. Override export_projection(self, src_key, **opts) → List[Tuple]

export_projection() returns nodes in the same format that SourceScanner
produces — (atom_key, attrs_dict, depth, meta_dict) — so the caller can
build a ProjectionProfile and forward the nodes to any ImportableMixin target
without knowing anything about the source model's internal structure.

EXPORT_SCHEMA["meta_type"] is the value that lens.py's SourceScanner looks for
in an atom's meta["type"] field to detect that this model owns the atom and
should handle the export.
"""

from typing import Any, Dict, List, Tuple


class ExportableMixin:
    """
    Mixin for concept models that can act as a source in a lens pipeline.

    EXPORT_SCHEMA declares what the model produces.
    export_projection() returns nodes in SourceScanner format.
    """

    EXPORT_SCHEMA: Dict[str, Any] = {
        # Unique model identifier (same as CONCEPT_PREFIX).
        "model": "",
        # Value of atom meta["type"] that identifies instances of this model.
        # SourceScanner checks this to auto-detect exportable sources.
        "meta_type": "",
        # One-line description shown in lens.scan output.
        "description": "",
        # Attribute prefixes that exported nodes typically carry
        # (informational — used in profile display).
        "produces": [],
    }

    @classmethod
    def describe_export(cls) -> Dict[str, Any]:
        """Return the EXPORT_SCHEMA for introspection / display."""
        return dict(cls.EXPORT_SCHEMA)

    def export_projection(
        self,
        src_key: str,   # atom key of the model instance to export
        **opts,         # model-specific extras
    ) -> List[Tuple]:
        """
        Return this model instance's data as a list of SourceScanner-format nodes.

        Each node is a tuple: (atom_key, attrs_dict, depth, meta_dict)
          attrs_dict may contain "content" and any typed link values
          (rec:, tbl:, ctx:, …) — same shape as SourceScanner._node_tuple().

        The returned list is ready to pass directly to SourceScanner._build_profile()
        or to any ImportableMixin's import_projection().
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement export_projection. "
            "Add it or remove the ExportableMixin."
        )
