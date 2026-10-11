#!/usr/bin/env python3
"""
Generate the marked sections of the platform specification, `docs/platform/SPEC.md`, from the API's
name table (`lib/akasha/api/exports.py`), its reserved names and declaration roots
(`lib/akasha/api/reserved.py`), the engine-owned field declarations and the data-format id.

    python scripts/gen_application_api.py           write them
    python scripts/gen_application_api.py --check   exit 1 if a section is not what the code says

A section is the text between `<!-- generated:<name> -->` and `<!-- /generated:<name> -->`. The prose
around them is the contract's text and is written by hand. The spec's title carries its version
(`lib.akasha.api.spec.NAME`), and a title that disagrees is a check failure too.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("AKASHA_SKIP_AUTOINSTALL", "1")
OUT = os.path.join(ROOT, "docs", "platform", "SPEC.md")


def sections() -> dict:
    from lib.akasha.api.exports import EXPORTS, target_of
    from lib.akasha.api.reserved import RESERVED_CONCEPTS, DECLARATION_ROOTS
    from lib.akasha import data_format
    import lib.akasha.concepts.source  # noqa: F401 — the source engine's owned-field declarations
    from lib.akasha.owned_fields import declared
    api = []
    for topic in sorted(EXPORTS):
        api += ["#### `lib.akasha.api.%s`" % topic, "", "| name | owner module | contract |", "|---|---|---|"]
        for name in sorted(EXPORTS[topic]):
            mod, attr = target_of(topic, name)
            owner = ("`%s`" % mod) if attr == name else "`%s` (`%s`)" % (mod, attr)
            api.append("| `%s` | %s | %s |" % (name, owner, EXPORTS[topic][name][1].replace("|", "\\|")))
        api.append("")
    roots = ["| kind | path under the application root |", "|---|---|"]
    roots += ["| `%s` | `%s` |" % (k, v) for k, v in sorted(DECLARATION_ROOTS.items())]
    reserved = ["| concept | engine |", "|---|---|"]
    reserved += ["| `%s` | %s |" % (c, e) for c, e in sorted(RESERVED_CONCEPTS.items())]
    owned = ["| field | owner | scope |", "|---|---|---|"]
    owned += ["| `%s` | %s | %s |" % (d["field"], d["owner"], d["scope"]) for d in declared()]
    fmt = ["The data-format id of this release: `%s`." % data_format.DATA_FORMAT_ID]
    return {"api": "\n".join(api).rstrip("\n"), "roots": "\n".join(roots),
            "reserved": "\n".join(reserved), "owned": "\n".join(owned), "data_format": "\n".join(fmt)}


def render(cur: str) -> str:
    import re
    from lib.akasha.api.spec import NAME
    out = re.sub(r"^# The Akasha platform specification — .*$",
                 "# The Akasha platform specification — %s" % NAME, cur, count=1, flags=re.M)
    for name, body in sections().items():
        open_, close = "<!-- generated:%s -->" % name, "<!-- /generated:%s -->" % name
        if open_ not in out or close not in out:
            raise SystemExit("SPEC.md has no section %s" % name)
        a, b = out.index(open_) + len(open_), out.index(close)
        out = out[:a] + "\n" + body + "\n" + out[b:]
    return out


def main() -> int:
    cur = open(OUT, encoding="utf-8").read()
    text = render(cur)
    if "--check" in sys.argv:
        if cur != text:
            print("docs/platform/SPEC.md is stale — run: python scripts/gen_application_api.py")
            return 1
        print("up to date")
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
