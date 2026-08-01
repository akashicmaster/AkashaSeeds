"""
DishFamilyConcept — the shared base for a FAMILY of dish:* atoms singled out by a family set.

Several food families arrive in the SAME shape (the smallplates importer, the sweets/bread
importer): the items live in the shared `dish:` namespace (so the canonical layer already treats
them as meals — sys:is_a meal, in meal:all), and a family is singled out by a membership set
(`smallplate:all` / `sweet:all` / `bread:all`). Each item `sys:is_a` one or more sub-types
(`dish:<type>`), and each sub-type `sys:is_a` the family umbrella (`dish:<family>`); a per-sub-type
membership set (`<family>:<type>`) makes the sub-type browsable.

That mechanism lives here once. A subclass is a thin, clearly-named surface (smallplate / sweet /
bread) that declares four class attributes and reuses the operators — the shared machinery is in
the base, the surface stays each concept's own (the operand/operator separation). DishFamilyConcept
itself is abstract (no CONCEPT_PREFIX) so the registry never registers it.

A subclass sets:
  CONCEPT_PREFIX   the surface name (smallplate / sweet / bread)
  ENTITY_SET       the family membership set (smallplate:all / sweet:all / bread:all)
  UMBRELLA         the family umbrella concept alias (dish:smallplate / dish:sweet / dish:bread) —
                   excluded as an entity and never listed as a sub-type
  AXIS_SPEC        the browse axes — conventionally `style` (the sub-type set `<family>:{v}`),
                   `country` (dish:from:{v}) and `cuisine` (thesaurus:related cuisine:{v})
  CONCEPT_METHODS  the search / ls / get surface (op_* live here in the base)
"""
from typing import Any, Dict

from lib.akasha.concepts.dictionary import DictionaryConcept


class DishFamilyConcept(DictionaryConcept):
    """Shared base: dish:* items in a family set, browsable by sub-type / country / cuisine."""

    NS       = "dish"          # items live in the shared dish: namespace (already meals in canon)
    UMBRELLA = ""              # the family umbrella concept (dish:<family>), excluded / not a type

    def _types_of(self, key: str) -> list:
        """The sub-types this item IS-A (tapa / cake / sourdough / …), from its `sys:is_a
        dish:<type>` links; the family umbrella is not a type."""
        out = set()
        for dst, rel in (self.cortex.get_adjacent_links(key) or []):
            if rel != "sys:is_a" or not self._visible(dst):
                continue
            nm = self._name(dst) or ""
            if nm.startswith("dish:") and nm != self.UMBRELLA:
                out.add(nm.split(":", 1)[1])
        return sorted(out)

    def _profile(self, key: str, alias: str) -> Dict[str, Any]:
        """Adds the sub-type list `types` (an item may be several) to the base profile, alongside
        the single representative `cuisine` the base fills in."""
        prof = super()._profile(key, alias)
        prof["types"] = self._types_of(key)
        return prof

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """Find items whose name or description contains every query token. READ-level;
        paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, type: str = "", country: str = "", cuisine: str = "", limit: Any = "",
              offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """Browse by axis — `type` (the sub-type), `country` of origin, and `cuisine`; axes
        intersect. READ-level; paginated (default 20, max 100)."""
        return self._dict_ls({"style": type, "country": country, "cuisine": cuisine},
                             limit, offset, cursor)

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """An item's profile — its sub-type(s), the cuisines and base ingredients it relates to,
        and its description. READ-level."""
        ref = (id or name).strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError(f"{self.CONCEPT_PREFIX}.get: no such {self.NOUN}.")
        prof = self._profile(key, self._alias_of(key, ref))     # id/key/name/note/cuisine/types
        prof["type"] = f"{self.CONCEPT_PREFIX}:profile"
        cuisines, ingredients = set(), set()
        for dst, rel in (self.cortex.get_adjacent_links(key) or []):
            if rel != "thesaurus:related" or not self._visible(dst):
                continue
            nm = self._name(dst) or ""
            if nm.startswith("cuisine:"):
                cuisines.add(nm.split(":", 1)[1])
            elif nm.startswith("ingred:"):
                ingredients.add(nm.split(":", 1)[1])
        prof["cuisines"] = sorted(cuisines)
        prof["ingredients"] = sorted(ingredients)
        return prof
