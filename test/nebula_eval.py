"""
Nebula cartographer eval (#52) — inductive concept-model-candidate discovery.

Builds a synthetic meaning-universe with two planted "emerging categories" (a fruit clump
sharing has:sweetness/color/season, a tool clump sharing has:material/use) plus noise, and
asserts nebula surfaces BOTH cores with the right proposed salient-rels — and that noise
does not masquerade as a category. Pure algorithm test on a mock engine (no boot).

Run:  python test/nebula_eval.py      (exit 0 = all pass)
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from lib.akasha.nebula import NebulaCartographer

_fails = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"   ({detail})" if detail and not cond else ""))
    if not cond:
        _fails.append(name)


class MockEngine:
    """Minimal ctx surface: atoms with alias/meta(salience,vec)/adjacency."""
    def __init__(self):
        self.atoms = {}       # key -> {alias, salience, vec, links:[(dst,rel)]}

    def add(self, key, alias, salience, vec, links):
        self.atoms[key] = {"alias": alias, "salience": salience, "vec": vec, "links": links}

    def stream(self, limit=None):
        return [{"key": k} for k in list(self.atoms)[:(limit or len(self.atoms))]]

    def get_meta(self, key):
        a = self.atoms.get(key, {})
        return {"salience": a.get("salience", 0.0), "semantic_vector": a.get("vec")}

    def get_aliases_by_key(self, key):
        a = self.atoms.get(key)
        return [a["alias"]] if a else []

    def get_adjacent_links(self, key, rel=None):
        return [[d, r] for (d, r) in self.atoms.get(key, {}).get("links", [])]

    def check_access(self, key, scopes):
        return True


def _vec(base, jitter, i):
    # 6-dim vector near `base` (a one-hot-ish centroid) with small per-atom jitter.
    v = [b + (jitter if (i % 6) == k else 0.0) * 0.1 for k, b in enumerate(base)]
    return v


def build_universe():
    eng = MockEngine()
    # value atoms the categories point at (give members shared neighbours + rel signature).
    for vk in ("val:sweet", "val:red", "val:summer", "val:steel", "val:cutting"):
        eng.add(vk, vk, 0.2, None, [])

    # Cluster A — fruit: shared schema {has:sweetness, has:color, has:season}, cohesive vecs.
    fruit_base = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    fruits = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape"]
    for i, f in enumerate(fruits):
        k = f"K_fruit_{f}"
        eng.add(k, f"ingred:fruit:{f}", 0.9,
                _vec(fruit_base, 1.0, i),
                [("val:sweet", "has:sweetness"), ("val:red", "has:color"),
                 ("val:summer", "has:season")])

    # Cluster B — tool: shared schema {has:material, has:use}, different vec region.
    tool_base = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    tools = ["hammer", "saw", "drill", "wrench", "pliers"]
    for i, t in enumerate(tools):
        k = f"K_tool_{t}"
        eng.add(k, f"tool:{t}", 0.8,
                _vec(tool_base, 1.0, i),
                [("val:steel", "has:material"), ("val:cutting", "has:use")])

    # Noise — varied namespaces, low salience, idiosyncratic single rels, scattered vecs.
    import_ = [("misc:alpha", [0.2, 0.2, 0.9, 0.0, 0.0, 0.0], "rel:one"),
               ("misc:beta",  [0.0, 0.3, 0.0, 0.9, 0.0, 0.0], "rel:two"),
               ("misc:gamma", [0.4, 0.0, 0.0, 0.0, 0.9, 0.0], "rel:three"),
               ("event:x",    [0.0, 0.0, 0.4, 0.0, 0.0, 0.9], "rel:four"),
               ("place:y",    [0.3, 0.3, 0.3, 0.0, 0.0, 0.0], "rel:five")]
    for i, (al, vec, rel) in enumerate(import_):
        eng.add(f"K_noise_{i}", al, 0.15, vec, [(f"val:steel", rel)])
    # scaffolding atoms that MUST be ignored (proto-words / sys).
    eng.add("K_proto", "word:thing", 0.99, fruit_base, [])
    eng.add("K_sys", "sys:anchor", 0.99, tool_base, [])
    return eng


def main():
    eng = build_universe()
    neb = NebulaCartographer(eng)
    cands = neb.survey(scopes=["scope:public"],
                       params={"min_size": 4, "threshold": 0.3, "cluster_cap": 200, "limit": 8})

    print(f"[survey] {len(cands)} candidate region(s):")
    for c in cands:
        print(f"    · {c['name']:12} size={c['size']} score={c['score']} "
              f"salient={c['salient_rels']} kind={c['kind']}")
    print()

    check("at least two candidate regions surfaced", len(cands) >= 2, f"got {len(cands)}")

    # locate the fruit and tool cores by their members
    def core_with(alias_frag):
        for c in cands:
            if any(alias_frag in a for a in c["member_aliases"]):
                return c
        return None

    fruit = core_with("ingred:fruit:")
    tool = core_with("tool:")
    check("fruit core discovered", fruit is not None)
    check("tool core discovered", tool is not None)

    if fruit:
        fs = set(fruit["salient_rels"])
        check("fruit's proposed salient-rels = the shared schema (sweetness/color/season)",
              {"has:sweetness", "has:color", "has:season"} <= fs, str(fruit["salient_rels"]))
        check("fruit members are the fruits (>=5, all ingred:fruit)",
              fruit["size"] >= 5 and all("ingred:fruit:" in a for a in fruit["member_aliases"]),
              f"size={fruit['size']}")
        check("fruit region proposes a name", bool(fruit["name"]))
        check("fruit cohesion is high (cohesive vectors)", fruit["cohesion"] >= 0.7,
              str(fruit["cohesion"]))
    if tool:
        check("tool's proposed salient-rels = material/use",
              {"has:material", "has:use"} <= set(tool["salient_rels"]), str(tool["salient_rels"]))

    # noise / scaffolding must NOT form a strong category
    for c in cands:
        check(f"scaffolding excluded from '{c['name']}' (no word:/sys: members)",
              not any(a.startswith(("word:", "sys:")) for a in c["member_aliases"]))
    top = cands[0]
    check("a planted core (not noise) ranks #1",
          any(f in top["member_aliases"][0] for f in ("ingred:fruit:", "tool:")),
          top["member_aliases"][:1])

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — nebula discovers emerging categories + proposes their salient-rels; noise excluded.")
    sys.exit(0)


if __name__ == "__main__":
    main()
