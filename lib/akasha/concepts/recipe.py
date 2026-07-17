"""
Recipe Concept Model — the cooking specialization of the `formula` base model.

`recipe` **extends `FormulaConcept`** (materials + operations + ordered process +
property rollup + specs + axis suggestion). Cooking maps onto that base one-to-one:

  material  → ingredient          operation → cooking method
  step/process → recipe step      rollup    → NUTRITION (and cost) accumulation
  spec (constraint) → allergen / taboo       spec (target) → calorie / nutrient goal
  axes      → season / ethnic / course / scene / group

So this file is a thin skin: it renames the operators to cooking vocabulary,
binds the material source to **food** atoms (USDA FoodData Central), and overrides
the rollup's per-material property hook to read food nutrition — from structured
`meta.nutrition` (written by `recipe.food`) OR a USDA `.ak` content string
("… — per 100g: 18 kcal, Protein 0.6g, …", since `.ak def` can't write meta). A
food is reachable by name (`food:{slug}`) OR by `food:fdc:{id}` (pin an ingredient
with `fdc=`), so a recipe resolves nutrition whichever way the loader named it.

Why recipe is developed in depth: within the OSS project it is the one model
carried as a product surface (an iOS app backend), so its API (JSON-RPC field
names, operator names) is kept stable and backward-compatible even as the generic
base evolves.

Operators (core — the default; extensible):
  recipe.new       create a recipe root (+ axes: season/ethnic/course/scene/group)
  recipe.add       add one operand: ingredient= | method= | hint= | plating= | constraint=
  recipe.step      append an ordered step, crossing it with the food/method it touches
  recipe.food      define/refresh a food atom's nutrition (USDA import endpoint)
  recipe.nutrition accumulate ingredient nutrition (+ cost) → totals + table + target check
  recipe.view      assemble the full card (GUI-ready), incl. nutrition summary
  recipe.ls        list recipes, optionally filtered by axis
  recipe.suggest   rank recipes by axis intersection; avoid= / constraints subtract

See `docs/concept-model/concept-model-spec.md` §10.9 and the `formula` base.
"""

import os
import re
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.concepts.formula import FormulaConcept, _as_list, _slug, _num, _paginate

logger = logging.getLogger("Harmonia.Concept.Recipe")


# ── Entitlement / tiering (the akashickitchen product model) ─────────────────────
# OFF by default so the open-source recipe model has NO limits. A product deployment
# opts in with AKASHA_RECIPE_TIERING=1; then a free plan is capped at
# AKASHA_RECIPE_FREE_QUOTA own recipes (default 5) and the analytics features in
# AKASHA_RECIPE_PAID_FEATURES (default nutrition,critical,haccp) require a paid plan.
# A user's plan is a server-written atom aliased plan:<uid> ("paid" = upgraded).
_PAID_ATOM_TEXT = "paid"


def _tiering_on() -> bool:
    return str(os.environ.get("AKASHA_RECIPE_TIERING", "")).strip().lower() in ("1", "yes", "true", "on")


def _free_quota() -> int:
    try:
        return max(0, int(os.environ.get("AKASHA_RECIPE_FREE_QUOTA", "5")))
    except (TypeError, ValueError):
        return 5


def _paid_features() -> set:
    raw = os.environ.get("AKASHA_RECIPE_PAID_FEATURES", "nutrition,critical,haccp")
    return {f.strip().lower() for f in str(raw).replace(" ", ",").split(",") if f.strip()}


# ── USDA nutrition content-string parsing (food atoms loaded via .ak) ────────────
# USDA labels (scripts/usda_food_import.py) → canonical nutrient keys, so a food
# whose nutrition arrived as an .ak content string accumulates identically to one
# written structurally by recipe.food.
_NUTR_LABEL_KEY = {
    "energy": "kcal", "kcal": "kcal", "calories": "kcal",
    "protein": "protein_g",
    "fat": "fat_g", "total fat": "fat_g",
    "carbohydrate": "carb_g", "carbohydrates": "carb_g", "carbs": "carb_g", "carb": "carb_g",
    "fiber": "fiber_g", "fibre": "fiber_g",
    "sugar": "sugar_g", "sugars": "sugar_g",
    "sodium": "sodium_mg", "calcium": "calcium_mg", "vitamin c": "vitc_mg",
}
_PER_BASIS_RE  = re.compile(r"per\s+(\d+(?:\.\d+)?)\s*g\b", re.I)
_KCAL_RE       = re.compile(r"(\d+(?:\.\d+)?)\s*k?cal\b", re.I)
_NUTR_FIELD_RE = re.compile(r"([A-Za-z][A-Za-z ]*?)\s+(\d+(?:\.\d+)?)\s*(mg|g)\b", re.I)

# A USDA FoodData Central id, however written: fdc=11429 / fdc:11429 / food:fdc:11429 / bare number.
_FDC_RE = re.compile(r"^(?:food:)?fdc[:_]?(\d+)$", re.I)


def _parse_nutrition_content(content: str) -> Optional[Dict[str, float]]:
    """Parse a USDA-style content string into a nutrition dict, or None. Only fires on
    the `per <N>g:` basis marker so a food's descriptive name is never read as data."""
    if not content:
        return None
    mb = _PER_BASIS_RE.search(content)
    if not mb:
        return None
    seg = content[mb.end():]
    nut: Dict[str, float] = {}
    mk = _KCAL_RE.search(seg)
    if mk:
        nut["kcal"] = float(mk.group(1))
    for m in _NUTR_FIELD_RE.finditer(seg):
        label = m.group(1).strip().lower()
        key = _NUTR_LABEL_KEY.get(label) or (
            _NUTR_LABEL_KEY.get(label.split()[-1]) if label.split() else None)
        if key:
            nut[key] = float(m.group(2))
    if not nut:
        return None
    nut["basis_g"] = float(mb.group(1))
    return nut


def _fdc_id(value) -> Optional[str]:
    """Extract a USDA FDC id from any of its written forms, or None."""
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    m = _FDC_RE.match(s)
    if m:
        return m.group(1)
    return s if s.isdigit() and len(s) >= 3 else None


# ── ontology dish parsing (a recipe: atom's description → structured recipe) ──────
# The recipe ontology (e.g. TheMealDB) stores a dish as ONE described atom in the shared
# catalogue, in a labelled grammar the importer emits:
#   "<Title> (<Category> · <Cuisine> · <Country>). Ingredients: <m> <name>; …. Method:
#    <step 1 …> step 2 …. Source: <url>"
# `_parse_dish` turns that back into {title, axes, ingredients, steps, source} so the
# recipe model can PROJECT it (reference.get) or MATERIALISE it (reference.clone) — the
# description → structured-steps expansion the app's reference library needs.

_UNIT_WORDS = {
    "g", "kg", "mg", "oz", "lb", "lbs", "ml", "l", "litre", "liter", "litres", "liters",
    "cup", "cups", "tbsp", "tbsps", "tablespoon", "tablespoons", "tsp", "tsps",
    "teaspoon", "teaspoons", "clove", "cloves", "pinch", "pinches", "can", "cans",
    "slice", "slices", "piece", "pieces", "sprig", "sprigs", "handful", "handfuls",
    "stick", "sticks", "cube", "cubes", "dash", "dashes", "knob", "bunch", "packet",
    "pkg", "package", "jar", "tin", "tins", "sheet", "sheets", "strip", "strips",
}
_MASS_ATTACHED_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(g|kg|mg|oz|lb|lbs|ml|l)\b", re.I)
_QTY_RE = re.compile(r"^\s*(\d+(?:[./]\d+)?(?:\s*[½¼¾⅓⅔⅛⅜⅝⅞])?|[½¼¾⅓⅔⅛⅜⅝⅞])\s*")
_STEP_MARK_RE = re.compile(r"(?i)\bstep\s*\d+\b[:.\s]*")


def _parse_ing_line(s: str) -> Dict[str, str]:
    """One 'Ingredients:' item → {raw, qty, unit, name}. Best-effort: a leading number
    (and unit) is split off; the remainder is the name (modifiers included). A line with
    no leading quantity (e.g. 'For frying Vegetable Oil') keeps qty/unit empty."""
    raw = s.strip()
    rest = raw
    qty, unit = "", ""
    m = _MASS_ATTACHED_RE.match(rest)              # '800g Lamb Mince'
    if m:
        qty, unit, rest = m.group(1), m.group(2).lower(), rest[m.end():].strip()
    else:
        mq = _QTY_RE.match(rest)
        if mq:
            qty, rest = mq.group(1).strip(), rest[mq.end():].strip()
            first = rest.split(" ", 1)[0].lower() if rest else ""
            if first in _UNIT_WORDS:               # '2 tablespoons Flour' / '1 clove Garlic'
                unit = first
                rest = rest[len(first):].strip()
    return {"raw": raw, "qty": qty, "unit": unit, "name": rest or raw}


def _split_steps(method: str) -> List[str]:
    """A 'Method:' body → ordered step texts. Prefers explicit 'step N' markers, then
    line breaks, then sentence segmentation (short fragments merge forward)."""
    body = (method or "").strip()
    if not body:
        return []
    if _STEP_MARK_RE.search(body):
        parts = [p.strip() for p in _STEP_MARK_RE.split(body) if p and p.strip()]
        return parts
    if "\n" in body:
        return [p.strip() for p in body.splitlines() if p.strip()]
    # sentence split; glue very short fragments onto the previous step.
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", body)
    out: List[str] = []
    for s in (x.strip() for x in sents if x.strip()):
        if out and len(s) < 15:
            out[-1] = out[-1] + " " + s
        else:
            out.append(s)
    return out


def _parse_dish(content: str) -> Dict[str, Any]:
    """A recipe: atom's description → {title, category, cuisine, country, ingredients,
    steps, source}. Degrades gracefully when a label/section is absent."""
    text = (content or "").strip()
    title = text
    category = cuisine = country = source = ""
    ingredients: List[Dict[str, str]] = []
    # Title + parenthetical axes: "<Title> (<A> · <B> · <C>)."
    mt = re.match(r"^(.*?)\s*\(([^)]*)\)\s*\.", text)
    head_end = 0
    if mt:
        title = mt.group(1).strip()
        axes = [a.strip() for a in re.split(r"\s*[·,]\s*", mt.group(2)) if a.strip()]
        category = axes[0] if len(axes) > 0 else ""
        cuisine = axes[1] if len(axes) > 1 else ""
        country = axes[2] if len(axes) > 2 else ""
        head_end = mt.end()
    else:
        # No parenthetical — title is up to the first sentence / 'Ingredients:'.
        title = re.split(r"\.\s+|(?=Ingredients:)", text, 1)[0].strip()
    body = text[head_end:] if head_end else text
    ms = re.search(r"\bSource:\s*(\S.*)$", body)
    if ms:
        source = ms.group(1).strip()
        body = body[:ms.start()]
    ing_block, method_block = "", body
    mi = re.search(r"\bIngredients:\s*(.*?)(?:\bMethod:\s*(.*))?$", body, re.S)
    if mi and (mi.group(1) or mi.group(2)):
        ing_block = (mi.group(1) or "").strip().rstrip(".")
        method_block = (mi.group(2) or "").strip()
    else:
        mm = re.search(r"\bMethod:\s*(.*)$", body, re.S)
        if mm:
            method_block = mm.group(1).strip()
    if ing_block:
        for part in ing_block.split(";"):
            part = part.strip().rstrip(".")
            if part:
                ingredients.append(_parse_ing_line(part))
    return {"title": title, "category": category, "cuisine": cuisine, "country": country,
            "ingredients": ingredients, "steps": _split_steps(method_block),
            "source": source}


class RecipeConcept(FormulaConcept):
    """Cooking specialization of `formula`: ingredients/methods/steps + nutrition."""

    CONCEPT_PREFIX     = "recipe"
    CONCEPT_LABEL      = "cookable structure over food/method/step atoms, with nutrition + axis suggestion"
    CONTEXT_KEY_ACTIVE = "active_recipe_root"

    ID_KEY    = "recipe_id"
    NOUN      = "recipe"
    AXES      = ("season", "ethnic", "course", "scene", "group")
    SOURCE_NS = "food"          # ingredients resolve to food:{slug} / food:fdc:{id}
    STUB_NS   = "rfood"         # last-resort step-cross stub (never claims food:)

    CONCEPT_METHODS = {
        "new": {
            "op": "op_new", "action": "write", "cli": "rcp.new", "args": ["title"],
            "desc": "Create a recipe: recipe new <title> [season= ethnic= course= scene= group=]",
        },
        "add": {
            "op": "op_add", "action": "write", "cli": "rcp.add", "args": ["recipe"],
            "desc": ("Add one operand (exactly one keyword): recipe add <recipe> "
                     "ingredient=daikon [qty=300 unit=g] [fdc=11429] [cost=80] | method=simmer | "
                     "hint='…' | plating='…' | constraint=peanut | constraint=kcal<=600"),
        },
        "food": {
            "op": "op_food", "action": "write", "cli": "rcp.food", "args": ["name"],
            "desc": ("(librarian/admin) Define/refresh a SHARED catalogue food's nutrition "
                     "(USDA import endpoint): recipe food daikon kcal=18 protein_g=0.6 "
                     "carb_g=4.1 [basis_g=100]"),
        },
        "food.personal": {
            "op": "op_food_personal", "action": "write", "cli": "rcp.food.me", "args": ["name"],
            "desc": ("Define/refresh a PRIVATE food (your own catalogue, not shared): "
                     "recipe food.personal 'my granola' kcal=480 protein_g=10 [basis_g=100]"),
        },
        "food.search": {
            "op": "op_food_search", "action": "read", "cli": "rcp.food.find", "args": [],
            "desc": ("Search foods by name → results with fdc + nutrition (the ingredient "
                     "picker): recipe food.search q=daikon [limit=20]"),
        },
        "food.lookup": {
            "op": "op_food_lookup", "action": "read", "cli": "rcp.food.lookup", "args": ["name"],
            "desc": ("Food-dictionary read (nutrition/allergens/season); ambiguous → "
                     "{candidates}: recipe food.lookup name=daikon"),
        },
        "method.list": {
            "op": "op_method_list", "action": "read", "cli": "rcp.methods", "args": [],
            "desc": "The cooking-method catalogue {methods:[{name,label}]}: recipe method.list",
        },
        "tool.list": {
            "op": "op_tool_list", "action": "read", "cli": "rcp.tools", "args": [],
            "desc": "The cooking-tool catalogue {tools:[{name,label}]}: recipe tool.list",
        },
        "publish": {
            "op": "op_publish", "action": "write", "cli": "rcp.publish", "args": ["recipe"],
            "desc": ("Publish own recipe as a public reference (paid; free → locked): "
                     "recipe publish <recipe>"),
        },
        "reference.get": {
            "op": "op_reference_get", "action": "read", "cli": "rcp.ref", "args": ["id"],
            "desc": ("Project a shared reference dish (recipe:* ontology atom) into a card "
                     "(parsed steps + ingredients): recipe reference.get id=recipe:mealdb:53262"),
        },
        "reference.clone": {
            "op": "op_reference_clone", "action": "write", "cli": "rcp.ref.clone", "args": ["id"],
            "desc": ("Materialise a reference dish into your own editable recipe: "
                     "recipe reference.clone id=recipe:mealdb:53262"),
        },
        "nutrition": {
            "op": "op_nutrition", "action": "read", "cli": "rcp.nutrition", "args": ["recipe"],
            "desc": "Accumulate ingredient nutrition (+cost) + target check: recipe nutrition <recipe>",
        },
        "step": {
            "op": "op_step", "action": "write", "cli": "rcp.step", "args": ["recipe"],
            "desc": ("Append a step, crossing what it touches: recipe step <recipe> "
                     "text='…' [uses=daikon,pork] [by=simmer] [dur=25 dur_unit=min] "
                     "[after=0,1] [label=x]"),
        },
        "critical": {
            "op": "op_critical", "action": "read", "cli": "rcp.critical", "args": ["recipe"],
            "desc": "Recipe timeline + critical path (parallel cooking): recipe critical <recipe>",
        },
        "control": {
            "op": "op_control", "action": "write", "cli": "rcp.control", "args": ["recipe"],
            "desc": ("HACCP control point: recipe control <recipe> param=core_temp op='>=' "
                     "value=75 unit=C [step=<ref>] [ccp=yes]  (also storage_temp / shelf_life)"),
        },
        "measure": {
            "op": "op_measure", "action": "write", "cli": "rcp.measure", "args": ["recipe"],
            "desc": "Record a food-safety measurement: recipe measure <recipe> param=core_temp value=78 [step=<ref>]",
        },
        "haccp": {
            "op": "op_haccp", "action": "read", "cli": "rcp.haccp", "args": ["recipe"],
            "desc": "Hygiene checkpoint report (CCPs, violations, safe): recipe haccp <recipe>",
        },
        "plan": {
            "op": "op_plan", "action": "read", "cli": "rcp.plan", "args": [],
            "desc": "The caller's plan: tier, recipe quota + usage, locked features: recipe plan",
        },
        "plan.set": {
            "op": "op_plan_set", "action": "write", "cli": "rcp.plan.set", "args": ["user"],
            "desc": "(admin) Set a user's plan: recipe plan.set user=<id> tier=paid|free",
        },
        "remove": {
            "op": "op_remove", "action": "write", "cli": "rcp.remove", "args": ["recipe"],
            "desc": "Remove a recipe, or one item: recipe remove <recipe> [item=<key>]",
        },
        "ingredient.remove": {
            "op": "op_ingredient_remove", "action": "write", "cli": "rcp.ing.rm", "args": ["recipe"],
            "desc": "Remove an ingredient line: recipe ingredient.remove <recipe> item=<key>",
        },
        "ingredient.update": {
            "op": "op_ingredient_update", "action": "write", "cli": "rcp.ing.set", "args": ["recipe"],
            "desc": ("Change an ingredient: recipe ingredient.update <recipe> item=<key> "
                     "[name= qty= unit= fdc= cost=]"),
        },
        "step.remove": {
            "op": "op_step_remove", "action": "write", "cli": "rcp.step.rm", "args": ["recipe"],
            "desc": "Remove a step: recipe step.remove <recipe> item=<key>",
        },
        "step.update": {
            "op": "op_step_update", "action": "write", "cli": "rcp.step.set", "args": ["recipe"],
            "desc": ("Change a step: recipe step.update <recipe> item=<key> "
                     "[text= uses= by= dur= after= label=]"),
        },
        "view": {
            "op": "op_view", "action": "read", "cli": "rcp.view", "args": ["recipe"],
            "desc": "Assemble the full recipe card: recipe view <recipe|alias>",
        },
        "ls": {
            "op": "op_ls", "action": "read", "cli": "rcp.ls", "args": [],
            "desc": "List recipes, optionally by axis: recipe ls [season= ethnic= course=]",
        },
        "suggest": {
            "op": "op_suggest", "action": "read", "cli": "rcp.suggest", "args": [],
            "desc": ("Suggest by axes (intersection ranking): recipe suggest season=winter "
                     "ethnic=japanese have=daikon,pork avoid=peanut — avoid is a hard filter"),
        },
    }

    # ── food resolution + nutrition source hook (the recipe specialization) ──────

    def _resolve_food_ref(self, ref: str) -> Optional[str]:
        """Resolve a DIRECT food identifier to an atom key. Accepts every id the dictionary
        / search surfaces: a numeric FDC id, a `food:…` alias (`food:daikon`,
        `food:vegetable:…`, `food:fdc:…`, `food:user:<uid>:…`), or a raw atom key. This is
        the pin the client sends after picking a food (via `food=` — or `fdc=`, kept
        tolerant so the already-deployed client that sends `fdc=food:daikon` keeps working)."""
        if not ref:
            return None
        s = str(ref).strip()
        if not s:
            return None
        fid = _fdc_id(s)
        if fid:
            k = self.cortex.resolve_alias(f"food:fdc:{fid}")
            if k:
                return k
        if s.startswith("food:"):
            k = self.cortex.resolve_alias(s)
            if k:
                return k
        if len(s) >= 16 and self.cortex.get_chunk(s) is not None:
            return s                       # a raw content-addressed atom key
        return None

    def _resolve_food(self, name: str = "", slug: str = "", fdc: str = "",
                      food: str = "") -> Optional[str]:
        """Resolve a food atom. An explicit id wins (`food=`, or a `fdc=` that carries a
        food id — client compat), then the caller's own `food:user:<uid>:<slug>`, then the
        pinned `food:fdc:<id>`, then the shared `food:<slug>`, then a plain-name / leaf
        lookup — so a picked food resolves exactly, a private food shadows the shared
        catalogue, and a bare name still resolves when unambiguous."""
        for ref in (food, fdc):
            k = self._resolve_food_ref(ref)
            if k:
                return k
        uid = self._client()
        if slug:
            k = self.cortex.resolve_alias(f"food:user:{uid}:{slug}")
            if k:
                return k
        fid = _fdc_id(fdc) or _fdc_id(name) or _fdc_id(slug)
        if fid:
            k = self.cortex.resolve_alias(f"food:fdc:{fid}")
            if k:
                return k
        if slug:
            k = self.cortex.resolve_alias(f"food:{slug}")
            if k:
                return k
        return self._resolve(name) or (self._resolve(slug) if slug else None)

    def _is_catalog_manager(self) -> bool:
        """True for a librarian/admin session — the roles allowed to write the SHARED food
        catalogue (`food:<slug>`). Regular users write private foods via
        recipe.food.personal instead (so the shared catalogue stays curated/authoritative)."""
        scopes = getattr(self.session, "active_scopes", []) or []
        return ("role:librarian" in scopes or "scope:sys:admin" in scopes
                or "role:superuser" in scopes)

    def _source_props(self, line_meta: Dict[str, Any]):
        """[rollup hook] An ingredient's per-basis properties = its food atom's nutrition,
        read from structured `meta.nutrition` OR a USDA `.ak` content string."""
        food = self._resolve_food(name=line_meta.get("name", ""),
                                  slug=line_meta.get("slug", ""),
                                  fdc=line_meta.get("fdc", ""),
                                  food=line_meta.get("food_key", ""))
        if not food:
            return None
        nut = (self.cortex.get_meta(food) or {}).get("nutrition") \
            or _parse_nutrition_content(self.cortex.get_chunk(food) or "")
        if not nut:
            return None
        basis = _num(nut.get("basis_g")) or 100.0
        return ({k: v for k, v in nut.items() if k != "basis_g"}, basis)

    def _nutr_targets(self, root: str, totals: Dict[str, float]) -> List[Dict[str, Any]]:
        """Recipe surface for targets — exposes `nutrient` (the historical field name)
        alongside the generic `key`, so existing clients keep working."""
        out = []
        for t in self._specs(root, totals):
            out.append({**t, "nutrient": t.get("key")})
        return out

    # ── entitlement / tiering (server-side enforcement; default OFF for OSS) ──────
    # (_is_admin is inherited from FormulaConcept.)

    def _plan_vault(self):
        """The shared-nucleus vault holding entitlement (server-side KV, cross-session).
        Entitlement is NOT a user-visible graph atom — it is server config keyed by uid."""
        return getattr(self.session, "nucleus", None)

    def _tier(self, uid: str = "") -> str:
        """A user's plan: 'paid' if the server marked them so in the shared nucleus vault,
        else 'free'. With tiering OFF (OSS default) everyone is 'paid' (no limits)."""
        if not _tiering_on():
            return "paid"
        uid = uid or self._client()
        nuc = self._plan_vault()
        try:
            v = nuc.vault_retrieve("entitlement", uid) if nuc else None
        except Exception:
            v = None
        return "paid" if str(v or "").strip().lower() == _PAID_ATOM_TEXT else "free"

    def _own_count(self, uid: str = "") -> int:
        uid = uid or self._client()
        return len(self.cortex.get_collection_members(f"set:recipe:owner:{uid}") or [])

    def _feature_locked(self, feature: str) -> bool:
        """True when `feature` requires a paid plan the caller doesn't have."""
        return _tiering_on() and feature in _paid_features() and self._tier() != "paid"

    def _locked(self, feature: str, root: str = "") -> Dict[str, Any]:
        return {"type": f"recipe:{feature}", "recipe_id": root, "locked": True,
                "reason": "upgrade_required", "feature": feature, "tier": self._tier()}

    def op_plan(self, name: str = "") -> Dict[str, Any]:
        """[recipe.plan] The caller's plan status — tier, recipe quota, usage, and which
        features are locked — so the app can render entitlement/upgrade state."""
        uid = self._client()
        tier = self._tier(uid)
        quota = _free_quota() if _tiering_on() else 0
        used = self._own_count(uid)
        return {"type": "recipe:plan", "user_id": uid, "tier": tier,
                "tiering": _tiering_on(),
                "recipe_quota": (quota if tier != "paid" else 0),   # 0 = unlimited
                "recipes_used": used,
                "recipes_remaining": (max(0, quota - used) if (_tiering_on() and tier != "paid") else None),
                "paid_features": sorted(_paid_features()) if _tiering_on() else [],
                "locked_features": ([f for f in sorted(_paid_features())]
                                    if (_tiering_on() and tier != "paid") else [])}

    def op_plan_set(self, user: str = "", tier: str = "", name: str = "") -> Dict[str, Any]:
        """[recipe.plan.set] (admin) Set a user's plan to 'paid' or 'free'. This is the
        server-side upgrade hook — a billing integration (e.g. validated App Store
        receipt) calls it after confirming payment. Writes/updates the plan:<uid> marker."""
        if not self._is_admin():
            raise RuntimeError("upgrade_denied: recipe.plan.set requires an admin/server role.")
        uid = (user or "").strip()
        want = (tier or "").strip().lower()
        if not uid or want not in ("paid", "free"):
            raise ValueError("recipe.plan.set requires user=<id> and tier=paid|free.")
        nuc = self._plan_vault()
        if nuc is None:
            raise RuntimeError("plan store unavailable (no shared nucleus in this session).")
        nuc.vault_store("entitlement", uid, want)      # shared, cross-session, server-only
        return {"status": "set", "user_id": uid, "tier": want}

    # ── operators (cooking vocabulary → base helpers) ────────────────────────────

    def op_new(self, title: str = "", alias: str = "", **axis_kwargs) -> Dict[str, Any]:
        """[recipe.new] Create a recipe. On a metered deployment a free plan is limited to
        a fixed number of own recipes; exceeding it raises `quota_reached:` (the app should
        show an upgrade prompt). No limit on OSS / paid plans."""
        if _tiering_on() and self._tier() == "free":
            quota = _free_quota()
            if quota and self._own_count() >= quota:
                raise RuntimeError(
                    f"quota_reached: the free plan allows {quota} recipes "
                    f"(you have {self._own_count()}). Upgrade for unlimited recipes.")
        return super().op_new(title=title, alias=alias, **axis_kwargs)

    def _write_food(self, name: str, alias: str, basis_g: str,
                    nutrients: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Shared body for the catalogue + personal food writers: upsert a food atom and
        (re)point `alias` at it. Fresh values on an existing food re-point the alias, so
        recipes (which resolve by alias at read time) pick up the change transparently."""
        slug = _slug(name)
        author, scopes = self._author_scopes()
        nut: Dict[str, float] = {"basis_g": _num(basis_g) or 100.0}
        for nk, nv in (nutrients or {}).items():
            fv = _num(nv)
            if fv is not None:
                nut[nk] = fv
        existing = self.cortex.resolve_alias(alias)
        if existing and len(nut) <= 1:
            return {"status": "exists", "food_id": existing, "name": name.strip(),
                    "slug": slug, "alias": alias,
                    "nutrition": (self.cortex.get_meta(existing) or {}).get("nutrition")}
        key = self.cortex.put_chunk(
            content=name.strip(),
            meta={"type": "atom", "role": "food", "concept": "recipe", "slug": slug,
                  "name": name.strip(), "nutrition": nut, "source": source,
                  "created_at": time.time()},
            author=author, scopes=scopes)
        self.cortex.set_alias(key, alias, force=bool(existing))
        return {"status": "updated" if existing else "created", "food_id": key,
                "name": name.strip(), "slug": slug, "alias": alias, "nutrition": nut}

    def op_food(self, name: str = "", basis_g: str = "100", **nutrients) -> Dict[str, Any]:
        """[recipe.food] Define/refresh a SHARED-catalogue food's nutrition — the USDA
        import write endpoint. Restricted to a librarian/admin (catalog manager): the
        shared `food:<slug>` namespace is a curated, authoritative catalogue, so a regular
        user cannot write it (they use recipe.food.personal for their own foods). Nutrition
        is stored per `basis_g` grams; the rollup sums whatever numeric keys are present."""
        if not name or not name.strip():
            raise ValueError("recipe.food requires a food name.")
        if not self._is_catalog_manager():
            raise RuntimeError(
                "catalog_denied: recipe.food writes the shared food catalogue and requires "
                "a librarian/admin role. Use recipe.food.personal for your own foods.")
        return self._write_food(name, f"food:{_slug(name)}", basis_g, nutrients, "recipe.food")

    def op_food_search(self, q: str = "", name: str = "", limit: Any = "",
                       offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[recipe.food.search] Search the food catalogue by name (substring, all tokens),
        across the shared catalogue AND the caller's private foods, returning each match's
        nutrition per basis and its `fdc` id. This is the picker the app needs: users type a
        name, choose a result, then `recipe.add ingredient=<name> fdc=<fdc>` — pinning to a
        precise food so nutrition resolves exactly (a bare name can be ambiguous across the
        catalogue's category-namespaced entries). READ-level (guests may browse); paginated
        (default 20, max 100)."""
        query = q or name
        hits = self._source_scan(query)
        items = []
        for key, alias in hits:
            content = self.cortex.get_chunk(key) or ""
            nut = (self.cortex.get_meta(key) or {}).get("nutrition") \
                or _parse_nutrition_content(content) or {}
            per = {k: v for k, v in nut.items() if k != "basis_g"}
            items.append({
                "key": key, "name": self._source_name(key, alias),
                "fdc": self._fdc_of(key),
                "scope": "personal" if alias.startswith("food:user:") else "catalog",
                "basis_g": _num(nut.get("basis_g")) or 100.0,
                "per_basis": per,
            })
        items.sort(key=lambda x: x["name"].lower())
        page, nxt, more = _paginate(items, self._page_limit(limit), cursor or offset)
        return {"type": "recipe:food_search", "query": query, "results": page,
                "count": len(items), "next_cursor": nxt, "has_more": more}

    def op_food_personal(self, name: str = "", basis_g: str = "100",
                         **nutrients) -> Dict[str, Any]:
        """[recipe.food.personal] Define/refresh a PRIVATE food in the caller's own
        catalogue (`food:user:<uid>:<slug>`), never the shared catalogue. Any authenticated
        user may do this for their own foods; `_resolve_food` prefers a personal food over a
        shared one for that user's recipes. Same nutrition shape as recipe.food."""
        if not name or not name.strip():
            raise ValueError("recipe.food.personal requires a food name.")
        alias = f"food:user:{self._client()}:{_slug(name)}"
        r = self._write_food(name, alias, basis_g, nutrients, "recipe.food.personal")
        r["scope"] = "personal"
        return r

    # ── food dictionary + catalogues (the reference side of the app) ─────────────

    def _best_food_id(self, key: str, aliases: List[str]) -> str:
        """The stable id a client should pin with (`food=<id>`): prefer a personal alias,
        then a plain `food:<slug>`, then the `food:fdc:<id>`, else the raw atom key."""
        cat = [a for a in aliases if a.startswith("food:") and not a.startswith("food:fdc:")]
        personal = [a for a in cat if a.startswith("food:user:")]
        plain = [a for a in cat if a.count(":") == 1]
        fdc = [a for a in aliases if a.startswith("food:fdc:")]
        return (personal or plain or cat or fdc or [key])[0]

    def _bucket_links(self, key: str, allergens: set, season: set,
                      categories: set, related: set) -> List[str]:
        """Bucket one atom's out-links by target namespace (into the given sets); return the
        `ingred:*` concept leaves it points at (so the caller can hop one more level — the
        ontology hangs allergens/season on the ingredient concept, not on each food)."""
        ingreds = []
        for dst, _ in (self.cortex.get_adjacent_links(key) or []):
            a = self._name(dst) or ""
            leaf = a.split(":")[-1]
            if a.startswith("allergen:") or a.startswith("constraint:"):
                allergens.add(leaf)                     # ontology uses allergen:; keep constraint: too
            elif a.startswith("season:"):
                season.add(leaf)
            elif a.startswith("food:category:"):
                categories.add(leaf)
            elif a.startswith("ingred:"):
                related.add(leaf)
                ingreds.append(dst)
        return ingreds

    def _food_record(self, key: str) -> Dict[str, Any]:
        """Assemble a dictionary record for one food atom: display name, the id to pin, the
        fdc, per-basis nutrition, and its allergens / season / categories / related concepts.
        Allergens and season live on the *ingredient concept* the food bridges to, so this
        hops food → `ingred:*` → `allergen:`/`season:` (one extra level) to surface them."""
        content = self.cortex.get_chunk(key) or ""
        meta = self.cortex.get_meta(key) or {}
        aliases = self.cortex.get_aliases_by_key(key) or []
        nut = meta.get("nutrition") or _parse_nutrition_content(content) or {}
        allergens, season, categories, related = set(), set(), set(), set()
        ingreds = self._bucket_links(key, allergens, season, categories, related)
        for ik in ingreds[:8]:                          # hop into the linked ingredient concepts
            self._bucket_links(ik, allergens, season, categories, related)
        return {"found": True, "id": self._best_food_id(key, aliases), "key": key,
                "name": self._source_name(key, aliases[0] if aliases else ""),
                "fdc": self._fdc_of(key), "basis_g": _num(nut.get("basis_g")) or 100.0,
                "nutrition": {k: v for k, v in nut.items() if k != "basis_g"},
                "allergens": sorted(allergens), "season": sorted(season),
                "categories": sorted(categories), "related": sorted(related)}

    def op_food_lookup(self, name: str = "", q: str = "") -> Dict[str, Any]:
        """[recipe.food.lookup] Food-dictionary read for one food: nutrition, allergens,
        season, categories. Exact-match preferred (case-insensitive): resolves the caller's
        personal food then the shared catalogue by name. If the name is ambiguous (no exact
        hit), returns `{found:false, candidates:[…]}` — a short list of matches (id + name +
        fdc) for the user to choose from. READ-level (guests may browse)."""
        query = (name or q or "").strip()
        if not query:
            raise ValueError("recipe.food.lookup requires a food name.")
        key = self._resolve_food(name=query, slug=_slug(query))
        if key and (self.cortex.get_meta(key) or {}).get("role") == "food":
            return {"type": "recipe:food", **self._food_record(key), "query": query}
        # No exact food hit → offer candidates from the search index.
        cands = []
        for ck, alias in self._source_scan(query)[:20]:
            content = self.cortex.get_chunk(ck) or ""
            nut = (self.cortex.get_meta(ck) or {}).get("nutrition") \
                or _parse_nutrition_content(content) or {}
            cands.append({"id": self._best_food_id(ck, self.cortex.get_aliases_by_key(ck) or []),
                          "key": ck, "name": self._source_name(ck, alias),
                          "fdc": self._fdc_of(ck),
                          "kcal": (nut or {}).get("kcal")})
        cands.sort(key=lambda x: x["name"].lower())
        return {"type": "recipe:food", "found": False, "query": query, "candidates": cands}

    def op_method_list(self, name: str = "") -> Dict[str, Any]:
        """[recipe.method.list] The cooking-method catalogue: `{methods:[{name,label,desc}]}`
        (`name` = the save key the recipe references, `label` = a display name). Unions the
        curated `method:*` vocab with the ontology's richer `technique:*` namespace (deduped
        by name)."""
        by_name: Dict[str, Dict[str, str]] = {}
        for prefix in ("method", "technique"):
            for key, alias in self._catalog_scan(prefix):
                slug = alias.split(":")[-1]
                if not slug or slug in by_name:
                    continue
                by_name[slug] = {"name": slug, "label": slug.replace("_", " ").title(),
                                 "desc": (self.cortex.get_chunk(key) or "").strip()}
        methods = sorted(by_name.values(), key=lambda m: m["name"])
        return {"type": "recipe:methods", "methods": methods, "count": len(methods)}

    def op_tool_list(self, name: str = "") -> Dict[str, Any]:
        """[recipe.tool.list] The cooking-tool catalogue: `{tools:[{name,label,desc}]}`.
        Tools are created as recipes reference them (recipe.step tools=…) and/or seeded by
        the ontology; this lists whatever `tool:*` atoms exist."""
        tools = []
        for key, alias in self._catalog_scan("tool"):
            slug = alias.split(":")[-1]
            tools.append({"name": slug, "label": slug.replace("_", " ").title(),
                          "desc": (self.cortex.get_chunk(key) or "").strip()})
        tools.sort(key=lambda t: t["name"])
        return {"type": "recipe:tools", "tools": tools, "count": len(tools)}

    def op_publish(self, recipe: str = "", name: str = "") -> Dict[str, Any]:
        """[recipe.publish] Publish the caller's own recipe as a public reference (adds it
        to the public feed, `set:recipe:published`, and grants public read). A paid feature
        on a metered deployment — a free-plan caller receives a `locked` result. Official
        promotion / moderation of a published recipe is a separate curator step."""
        root = self._root(recipe or name)
        if _tiering_on() and self._tier() != "paid":
            return {"type": "recipe:publish", "recipe_id": root, "locked": True,
                    "reason": "upgrade_required", "feature": "publish", "tier": self._tier()}
        self.cortex.add_to_set(self._published_set(), root)
        # Grant public read to the whole card (root + its member atoms) so a public
        # reader can actually see it — the caller is publishing their own content.
        try:
            core = getattr(self.cortex, "core", None)
            if core is not None and hasattr(core, "put_chunk_access"):
                for k in [root] + list(self._members_all(root)):
                    core.put_chunk_access(k, ["view:public"])
        except Exception as exc:
            logger.warning("[recipe.publish] public scope grant failed for %s: %s", root, exc)
        self._bump(root)
        return {"status": "published", "recipe_id": root, "public": True,
                **self._version(root)}

    # ── ontology reference recipes (dish atom → structured recipe) ───────────────

    def _resolve_dish(self, ref: str) -> Optional[str]:
        """Resolve a reference-recipe handle (a `recipe:<slug>` / `recipe:mealdb:<id>`
        alias, or a raw atom key) to a described ontology dish atom — NOT a recipe-model
        root (those are handled by `_root`)."""
        if not ref:
            return None
        key = (self.cortex.resolve_alias(str(ref)) if ":" in str(ref) else None) or ref
        if self.cortex.get_chunk(key) is None:
            key = self.cortex.resolve_alias(str(ref)) or self._resolve(str(ref)) or ""
        if not key or self.cortex.get_chunk(key) is None:
            return None
        if (self.cortex.get_meta(key) or {}).get("role") == "root":
            return None                    # a model instance, not an ontology dish
        return key

    def _dish_links(self, key: str) -> Dict[str, Any]:
        """The dish atom's linked ingredient concepts + image url."""
        concepts, image = [], ""
        for dst, _ in (self.cortex.get_adjacent_links(key) or []):
            a = self._name(dst) or ""
            if a.startswith("ingred:"):
                concepts.append(a.split(":")[-1])
            elif a.startswith("media:img:") or a.startswith("media:"):
                image = image or (self.cortex.get_chunk(dst) or "").strip()
        return {"ingredient_concepts": concepts, "image": image}

    def op_reference_get(self, id: str = "", name: str = "", recipe: str = "") -> Dict[str, Any]:
        """[recipe.reference.get] Project a shared reference dish (a `recipe:*` ontology
        atom, e.g. from TheMealDB) into a recipe card WITHOUT materialising it — its
        description is parsed on the fly into title, axes, ingredients (with measures),
        and ordered steps, plus its linked ingredient concepts, image, and source. READ
        (guests may browse the reference library). To get an editable copy, clone it."""
        key = self._resolve_dish(id or recipe or name)
        if not key:
            raise ValueError("recipe.reference.get: no such reference dish.")
        d = _parse_dish(self.cortex.get_chunk(key) or "")
        links = self._dish_links(key)
        return {"type": "recipe:reference", "reference": True, "id": key,
                "aliases": [a for a in (self.cortex.get_aliases_by_key(key) or [])
                            if a.startswith("recipe:")],
                "title": d["title"],
                "axes": {"course": [d["category"]] if d["category"] else [],
                         "ethnic": [d["cuisine"]] if d["cuisine"] else [],
                         "group": [d["country"]] if d["country"] else []},
                "ingredients": d["ingredients"], "steps": d["steps"],
                "ingredient_concepts": links["ingredient_concepts"],
                "image": links["image"], "source": d["source"],
                "counts": {"ingredients": len(d["ingredients"]), "steps": len(d["steps"])}}

    def op_reference_clone(self, id: str = "", name: str = "", recipe: str = "",
                           title: str = "") -> Dict[str, Any]:
        """[recipe.reference.clone] Materialise a shared reference dish into the caller's
        OWN editable recipe: parses the dish description and builds a real recipe-model
        instance (recipe.new + a step per instruction + an ingredient per parsed line, with
        a best-effort food pin so nutrition resolves where the name matches). Returns the
        new `recipe_id`. Counts against the caller's recipe quota. This is 'save & customise'
        for a reference recipe."""
        key = self._resolve_dish(id or recipe or name)
        if not key:
            raise ValueError("recipe.reference.clone: no such reference dish.")
        d = _parse_dish(self.cortex.get_chunk(key) or "")
        created = super().op_new(
            title=(title.strip() or d["title"] or "Untitled"),
            course=d["category"], ethnic=d["cuisine"], group=d["country"])
        if created.get("status") not in ("created", "exists"):
            return created                          # e.g. quota_reached surfaced by op_new
        root = created["recipe_id"]
        for ing in d["ingredients"]:
            food_key = self._resolve_food(name=ing["name"], slug=_slug(ing["name"])) or ""
            self._add_material(root, ing["name"], ing.get("qty", ""), ing.get("unit", ""),
                               extra_meta={"food_key": food_key})
        for st in d["steps"]:
            self._mk_step(root, st)
        if d["source"]:
            self._add_note(root, f"Source: {d['source']}", "hints", self._rel("hint"))
        return {"status": "cloned", "recipe_id": root, "from": key,
                "title": created.get("title", ""),
                "ingredients": len(d["ingredients"]), "steps": len(d["steps"]),
                **self._version(root)}

    def op_add(self, recipe: str = "", ingredient: str = "", method: str = "",
               hint: str = "", plating: str = "", constraint: str = "",
               qty: str = "", unit: str = "", fdc: str = "", food: str = "", cost: str = "",
               request_key: str = "", expected_updated_at: Any = "",
               expected_revision: Any = "") -> Dict[str, Any]:
        """[recipe.add] Add exactly one operand to a recipe.

          ingredient=daikon [qty=300 unit=g] [food=food:daikon|fdc=11429] [cost=80]  — a food line
          method=simmer                         — a cooking method
          hint="don't over-salt" / plating="…"  — a caution / a presentation note
          constraint=peanut                     — an allergen / taboo (hard filter)
          constraint=kcal<=600                  — a nutrient target (checked vs totals)

        Pin the food record the user picked from the dictionary/search with `food=<id>` (a
        `food:…` alias, an atom key, or a numeric FDC). `fdc=` is the legacy field and is
        kept tolerant — it accepts the same ids — so the pin resolves whichever field the
        client uses. `cost=` is that line's cost. `request_key=` makes the add idempotent;
        `expected_revision=` (preferred) / `expected_updated_at=` guard a concurrent edit.
        An added ingredient returns a stable `ingredient_id` (survives later edits).
        """
        root = self._root(recipe)
        self._guard_version(root, expected_updated_at, expected_revision)
        dup = self._idem_hit("recipe.add", request_key)
        if dup:
            m = self.cortex.get_meta(dup) or {}
            return {"status": "duplicate", "recipe_id": root, "key": dup,
                    "atom_key": dup, "ingredient_id": m.get("lid", ""),
                    "item_id": m.get("lid", "")}
        given = [(k, v) for k, v in (("ingredient", ingredient), ("method", method),
                                     ("hint", hint), ("plating", plating),
                                     ("constraint", constraint)) if v and str(v).strip()]
        if len(given) != 1:
            raise ValueError("recipe.add takes exactly one of "
                             "ingredient= / method= / hint= / plating= / constraint=.")
        kind, value = given[0]
        value = str(value).strip()

        def _return(r):
            self._idem_record("recipe.add", request_key, r.get("key", ""))
            return r

        if kind == "ingredient":
            fid = _fdc_id(fdc) or _fdc_id(value)
            # Pin the picked food: `food=` (canonical) or a food id sent in `fdc=` (compat).
            food_key = self._resolve_food_ref(food) or self._resolve_food_ref(fdc) or ""
            props = {}
            c = _num(cost)
            if c is not None:
                props["cost"] = c
            r = self._add_material(root, value, qty, unit, props=props,
                                   extra_meta={"fdc": fid or "", "food_key": food_key})
            r["kind"] = "ingredient"
            r["ingredient_id"] = r.get("lid", "")
            r["fdc"] = fid or ""
            r["food_key"] = food_key
            return _return(r)
        if kind == "method":
            r = self._add_operation(root, value)
            r["kind"] = "method"
            return _return(r)
        if kind == "constraint":
            return _return(self._add_spec(root, value))   # nutrient bound → target, else allergen
        # hint / plating — free annotation atoms in their own sub-groups
        if kind == "hint":
            return _return(self._add_note(root, value, "hints", self._rel("hint")))
        return _return(self._add_note(root, value, "presentation", self._rel("plating")))

    def op_step(self, recipe: str = "", text: str = "", uses: Any = None, by: Any = None,
                dur: str = "", dur_unit: str = "min", after: Any = None, label: str = "",
                tools: Any = None, temp: str = "",
                request_key: str = "", expected_updated_at: Any = "",
                expected_revision: Any = "") -> Dict[str, Any]:
        """[recipe.step] Append one step and cross it with what it touches.

        `dur=`/`dur_unit=` estimate cooking time; `tools=` names equipment used (pot, oven,
        …); `temp=` a target temperature in °C. `after=` names predecessor steps by their
        stable `step_id` (order index / label / key also accepted) — omit for the linear
        default, use it for parallel cooking (a second burner, the oven running while you
        prep). See recipe.critical. Returns a stable `step_id` that survives later edits.
        `request_key=` makes the step idempotent on retry; `expected_revision=` (or the
        legacy `expected_updated_at=`) guards against a concurrent edit."""
        root = self._root(recipe)
        self._guard_version(root, expected_updated_at, expected_revision)
        dup = self._idem_hit("recipe.step", request_key)
        if dup:
            return {"status": "duplicate", "recipe_id": root,
                    "step_id": self._lid_of(dup), "atom_key": dup, "key": dup}
        r = self._mk_step(root, text, uses, by, dur=dur, dur_unit=dur_unit,
                          after=after, label=label, tools=tools, temp=temp)
        self._idem_record("recipe.step", request_key, r.get("key", ""))
        return r

    def op_critical(self, recipe: str = "", name: str = "") -> Dict[str, Any]:
        """[recipe.critical] The recipe's timeline: per-step earliest/latest start,
        slack, the critical path (what gates total time), and the makespan with parallel
        cooking vs the naive sequential total. Parallel-process planning is a paid feature
        on a metered deployment; a free-plan caller receives a `locked` result."""
        root = self._root(recipe or name)
        if self._feature_locked("critical"):
            return self._locked("critical", root)
        meta = self.cortex.get_meta(root) or {}
        c = self._critical(root)
        return {"type": "recipe:critical", "recipe_id": root,
                "title": meta.get("title", ""), **c}

    def op_control(self, recipe: str = "", param: str = "", op: str = ">=",
                   value: str = "", unit: str = "", step: str = "",
                   ccp: str = "") -> Dict[str, Any]:
        """[recipe.control] Food-safety / HACCP control point — a bound on a process
        parameter, the hook to hygiene management:

          recipe control <recipe> param=core_temp op='>=' value=75 unit=C step=<cook> ccp=yes
          recipe control <recipe> param=storage_temp op='<=' value=5 unit=C
          recipe control <recipe> param=shelf_life op='<=' value=3 unit=day

        Cooking temperature, holding/storage temperature, serve-within, and shelf life
        are all control specs; `recipe.measure` records the actual and `recipe.haccp`
        reports pass/fail. `ccp=yes` marks a critical control point.

        HACCP is a paid feature on a metered deployment: control/measure/haccp are gated
        together (a free-plan caller receives a `locked` result), so the write and the
        report it feeds stay consistent."""
        root = self._root(recipe)
        if self._feature_locked("haccp"):
            return self._locked("haccp", root)
        from lib.akasha.concepts.formula import _num as _fnum, _slug as _fslug
        v = _fnum(value)
        if not param or v is None or op not in ("<=", ">=", "<", ">", "="):
            raise ValueError("recipe.control requires param=, op= (<= >= < > =), numeric value=.")
        return self._add_spec(root, f"{_fslug(param)}{op}{v:g}", step=step, unit=unit,
                             ccp=str(ccp).lower() in ("1", "yes", "true", "y"))

    def op_measure(self, recipe: str = "", param: str = "", value: str = "",
                   step: str = "", request_key: str = "") -> Dict[str, Any]:
        """[recipe.measure] Record an observed food-safety value (e.g. core_temp=78 at the
        cook step): recipe measure <recipe> param=core_temp value=78 [step=<ref>].
        `request_key=` makes a retried measurement idempotent (no double record). Gated
        with the rest of HACCP (paid feature on a metered deployment)."""
        root = self._root(recipe)
        if self._feature_locked("haccp"):
            return self._locked("haccp", root)
        dup = self._idem_hit("recipe.measure", request_key)
        if dup:
            return {"status": "duplicate", "recipe_id": root, "key": dup}
        r = self._add_measurement(root, param, value, step)
        self._idem_record("recipe.measure", request_key, r.get("key", ""))
        return r

    def op_remove(self, recipe: str = "", item: str = "",
                  expected_updated_at: Any = "", expected_revision: Any = "") -> Dict[str, Any]:
        """[recipe.remove] Remove the whole recipe (item omitted) or one item by its stable
        id / key (an ingredient/method/step/hint/…): recipe remove <recipe> [item=<id>]."""
        root = self._root(recipe)
        self._guard_version(root, expected_updated_at, expected_revision)
        if item:
            self._forget(root, self._resolve_item(root, item))
            self._bump(root)
            return {"status": "removed", "recipe_id": root, "item": item, **self._version(root)}
        return {**self._remove_root(root)}

    def op_ingredient_remove(self, recipe: str = "", item: str = "",
                             expected_updated_at: Any = "",
                             expected_revision: Any = "") -> Dict[str, Any]:
        """[recipe.ingredient.remove] Remove an ingredient line by its stable ingredient_id
        or atom key."""
        root = self._root(recipe)
        self._guard_version(root, expected_updated_at, expected_revision)
        item = self._resolve_item(root, item)
        if (self.cortex.get_meta(item) or {}).get("role") != "material":
            raise ValueError("recipe.ingredient.remove: item is not an ingredient.")
        self._forget(root, item)
        self._bump(root)
        return {"status": "removed", "recipe_id": root, "item": item, **self._version(root)}

    def op_ingredient_update(self, recipe: str = "", item: str = "", name: str = "",
                             qty: str = "", unit: str = "", fdc: str = "", food: str = "",
                             cost: str = "", expected_updated_at: Any = "",
                             expected_revision: Any = "") -> Dict[str, Any]:
        """[recipe.ingredient.update] Change an ingredient (atoms are immutable, so this
        detaches the old line and re-adds it with the new values): pass only the fields to
        change; omitted ones inherit the old line (incl. its pinned food). The stable
        ingredient_id is carried forward so client references survive the edit."""
        root = self._root(recipe)
        self._guard_version(root, expected_updated_at, expected_revision)
        item = self._resolve_item(root, item)
        old = self.cortex.get_meta(item) or {}
        if old.get("role") != "material":
            raise ValueError("recipe.ingredient.update: item is not an ingredient.")
        props = dict(old.get("props") or {})
        c = _num(cost)
        if c is not None:
            props["cost"] = c
        fid = _fdc_id(fdc) if fdc else old.get("fdc", "")
        food_key = (self._resolve_food_ref(food) or self._resolve_food_ref(fdc)
                    or old.get("food_key", ""))
        lid = old.get("lid", "")
        self._forget(root, item)
        r = self._add_material(root, name or old.get("name", ""),
                               qty or old.get("qty", ""), unit or old.get("unit", ""),
                               props=props,
                               extra_meta={"fdc": fid or "", "food_key": food_key, "lid": lid})
        r["kind"] = "ingredient"
        r["ingredient_id"] = r.get("lid", "")
        r["fdc"] = fid or ""
        r["food_key"] = food_key
        return r

    def op_step_remove(self, recipe: str = "", item: str = "",
                       expected_updated_at: Any = "",
                       expected_revision: Any = "") -> Dict[str, Any]:
        """[recipe.step.remove] Remove a step by its stable step_id or atom key."""
        root = self._root(recipe)
        self._guard_version(root, expected_updated_at, expected_revision)
        item = self._resolve_item(root, item)
        if (self.cortex.get_meta(item) or {}).get("role") != "step":
            raise ValueError("recipe.step.remove: item is not a step.")
        self._forget(root, item)
        self._bump(root)
        return {"status": "removed", "recipe_id": root, "item": item, **self._version(root)}

    def op_step_update(self, recipe: str = "", item: str = "", text: str = "",
                       uses: Any = None, by: Any = None, dur: str = "", dur_unit: str = "min",
                       after: Any = None, label: str = "", tools: Any = None, temp: str = "",
                       expected_updated_at: Any = "",
                       expected_revision: Any = "") -> Dict[str, Any]:
        """[recipe.step.update] Change a step (detach + re-add); omitted fields inherit the
        old step (incl. tools/temp). The stable step_id is carried forward so `after=`
        references and client handles survive the edit. Note: re-adding appends at the end
        of the current order."""
        root = self._root(recipe)
        self._guard_version(root, expected_updated_at, expected_revision)
        item = self._resolve_item(root, item)
        old = self.cortex.get_meta(item) or {}
        if old.get("role") != "step":
            raise ValueError("recipe.step.update: item is not a step.")
        old_uses = [d for d, _ in self.cortex.get_adjacent_links(item, self._rel("step_uses"))]
        old_by = [d for d, _ in self.cortex.get_adjacent_links(item, self._rel("step_by"))]
        old_tools = old.get("tools") or []
        new_text = text or self._line(item)
        lid = old.get("lid", "")
        self._forget(root, item)
        return self._mk_step(root, new_text,
                             uses if uses is not None else old_uses,
                             by if by is not None else old_by,
                             dur=dur or old.get("dur_min", ""), dur_unit=dur_unit,
                             after=after, label=label or old.get("label", ""),
                             tools=tools if tools is not None else old_tools,
                             temp=temp if str(temp).strip() != "" else old.get("temp", ""),
                             lid=lid)

    def op_haccp(self, recipe: str = "", name: str = "") -> Dict[str, Any]:
        """[recipe.haccp] The hygiene checkpoint report: every control spec checked against
        its recorded measurement — pass / fail / pending, the critical control points, any
        violations, and an overall `safe` flag. Paid feature on a metered deployment."""
        root = self._root(recipe or name)
        if self._feature_locked("haccp"):
            return self._locked("haccp", root)
        meta = self.cortex.get_meta(root) or {}
        return {"type": "recipe:haccp", "recipe_id": root,
                "title": meta.get("title", ""), **self._checkpoints(root)}

    def op_nutrition(self, recipe: str = "", name: str = "") -> Dict[str, Any]:
        """[recipe.nutrition] Accumulate the recipe's ingredient nutrition (and any line
        cost) into totals + a per-ingredient table, and check nutrient targets.

        Degradation-first: a non-mass unit is `unmeasured`, an ingredient with no food
        data `no_data` — both listed, never silently dropped.

        Nutrition/cost calculation is a paid feature on a metered deployment; a free-plan
        caller receives a `locked` result (the app should prompt to upgrade)."""
        root = self._root(recipe or name)
        if self._feature_locked("nutrition"):
            return self._locked("nutrition", root)
        meta = self.cortex.get_meta(root) or {}
        acc = self._rollup(root)
        per = [{**e, "nutrition": e.get("props", {})} for e in acc["per_material"]]
        return {"type": "recipe:nutrition", "recipe_id": root,
                "title": meta.get("title", ""), "totals": acc["totals"],
                "per_ingredient": per, "measured": acc["measured"],
                "unmeasured": acc["unmeasured"], "no_data": acc["no_data"],
                "targets": self._nutr_targets(root, acc["totals"])}

    def op_view(self, recipe: str = "", name: str = "") -> Dict[str, Any]:
        """[recipe.view] Assemble the full recipe card: ingredients (with qty/fdc),
        methods, ordered steps (with crossings), hints, presentation, axes,
        constraints, a nutrition summary, and targets. GUI-ready."""
        root = self._root(recipe or name)
        meta = self.cortex.get_meta(root) or {}

        def _ing(k):
            m = self.cortex.get_meta(k) or {}
            return {"key": k, "ingredient_id": m.get("lid", ""), "name": m.get("name", ""),
                    "qty": m.get("qty", ""), "unit": m.get("unit", ""), "fdc": m.get("fdc", ""),
                    "line": self._line(k)}

        ingredients = [_ing(k) for k in self._members(self._rset(root, "material"))]

        def _step(k):
            m = self.cortex.get_meta(k) or {}
            return {"key": k, "step_id": m.get("lid", ""), "order": m.get("order", 0),
                    "text": self._line(k), "dur_min": m.get("dur_min"),
                    "temp": m.get("temp"), "tools": m.get("tools") or [],
                    "uses": [d for d, _ in self.cortex.get_adjacent_links(k, self._rel("step_uses"))],
                    "by":   [d for d, _ in self.cortex.get_adjacent_links(k, self._rel("step_by"))]}

        steps = sorted((_step(k) for k in self._members(self._rset(root, "step"))),
                       key=lambda s: s["order"])
        methods = [{"key": k, "name": self._name(k) or self._line(k)}
                   for k in self._members(self._rset(root, "operation"))]
        # hints carry their item ids too (hint_items) so the client can delete one memo;
        # the plain `hints` string list is kept for backward compatibility.
        hint_keys = self._members(self._rset(root, "hints"))
        hints = [self._line(k) for k in hint_keys]
        hint_items = [{"item_id": self._lid_of(k), "key": k, "text": self._line(k)}
                      for k in hint_keys]
        plating = [self._line(k) for k in self._members(self._rset(root, "presentation"))]
        constraints = self._constraints(root)

        if self._feature_locked("nutrition"):
            nutrition = {"locked": True, "reason": "upgrade_required"}
            targets = []
        else:
            acc = self._rollup(root)
            nutrition = {"totals": acc["totals"], "measured": acc["measured"],
                         "unmeasured": acc["unmeasured"], "no_data": acc["no_data"]}
            targets = self._nutr_targets(root, acc["totals"])

        return {"type": "recipe:card", "recipe_id": root, "title": meta.get("title", ""),
                "axes": meta.get("axes", {}), "mine": meta.get("owner") == self._client(),
                "published": self._is_published(root),
                "ingredients": ingredients,
                "methods": methods, "steps": steps, "hints": hints, "hint_items": hint_items,
                "presentation": plating, "constraints": constraints,
                "nutrition": nutrition, "targets": targets, **self._version(root),
                "counts": {"ingredients": len(ingredients), "steps": len(steps),
                           "methods": len(methods), "constraints": len(constraints),
                           "targets": len(targets)}}

    def op_ls(self, season: str = "", ethnic: str = "", course: str = "",
              scene: str = "", group: str = "", limit: Any = "", offset: Any = 0,
              cursor: Any = "") -> Dict[str, Any]:
        """[recipe.ls] List recipes, optionally filtered by discrete axis. `limit`/`cursor`
        paginate (result carries `next_cursor`/`has_more`): default page 20, max 100; the
        whole list (limit=0) is admin-only."""
        filters = [(ax, v) for ax, v in (("season", season), ("ethnic", ethnic),
                                         ("course", course), ("scene", scene),
                                         ("group", group)) if v]
        return self._ls(filters, limit=self._page_limit(limit), offset=cursor or offset)

    def op_suggest(self, season: Any = None, ethnic: Any = None, course: Any = None,
                   scene: Any = None, group: Any = None, have: Any = None,
                   avoid: Any = None, mode: str = "retrieval", limit: Any = "",
                   offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[recipe.suggest] Rank recipes by dimensional-axis intersection; avoid= /
        allergen constraints are a hard, fail-closed filter (subtract, never rank).
        `limit`/`cursor` paginate (default 20, max 100, full list admin-only)."""
        terms = [(ax, val)
                 for ax, v in (("season", season), ("ethnic", ethnic), ("course", course),
                               ("scene", scene), ("group", group))
                 for val in _as_list(v)]
        return self._suggest(terms, have, avoid, mode, self._page_limit(limit),
                             offset=cursor or offset)
