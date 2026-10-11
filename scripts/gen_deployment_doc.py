#!/usr/bin/env python3
"""
docs/deployment.md — every environment variable a cell reads, generated from the manifests (the
purge order, 3 October §4.5). The heart's manifest declares the platform's variables; a package's
manifest declares its own under `env`. Each is a deployment FACT — a path, an address, a secret, an
identity, the series, a capacity — never a behaviour switch. The launcher refuses a set AKASHA_*
variable no manifest declares, by name, so this page is the whole list.

Run:  python scripts/gen_deployment_doc.py           (writes docs/deployment.md)
      python scripts/gen_deployment_doc.py --check   (exit 1 when the page is stale)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "deployment.md")

KINDS = (
    ("path", "Paths", "Where the cell reads and writes."),
    ("network", "Network", "Where the cell listens and whom it talks to."),
    ("secret", "Secrets", "Keys. Supply them out-of-band (the environment or a secrets manager); "
                          "never commit them."),
    ("identity", "Identity", "Names the cell is given."),
    ("series", "Series and host", "What this deployment is: the series, the store, what the host "
                                  "provides."),
    ("capacity", "Capacity", "Budgets and limits sized to the host. A `0` means unbounded where "
                             "the row says so."),
    ("process", "Set by the platform", "The launcher sets these on its own child processes. An "
                                       "operator does not set them."),
)


def _platform_packages(M):
    """The packages whose manifests live outside the application root."""
    out = set()
    for path in M.default_manifest_paths(os.path.join(ROOT, "lib", "akasha")):
        with open(path, encoding="utf-8") as fh:
            man = json.load(fh)
        if man.get("owner") == "platform":
            out.add(man.get("package"))
    return out


def render() -> str:
    sys.path.insert(0, ROOT)
    from lib.akasha.api import manifest as M
    env = {n: r for n, r in M.declared_env().items() if r.get("package") in _platform_packages(M)}
    lines = [
        "# Deployment — environment variables",
        "",
        "Generated from the manifests by `scripts/gen_deployment_doc.py`; do not edit by hand.",
        "",
        "Every variable here is a **deployment fact**: a path, an address, a secret, an identity, "
        "the series, a capacity. None of them switches behaviour on or off.",
        "",
        "- **The launcher refuses an `AKASHA_*` variable that no manifest declares.** It stops with "
        "exit 3 and one line per name: `[env] refused name=<NAME>`. That covers a variable "
        "exported in the shell and one set in `env/deployment.env`.",
        "- `stop` still runs with an undeclared variable set, so a cell can always be halted.",
        "- A name with `*` declares a family (one provider's budget, e.g. "
        "`AKASHA_LLM_MISTRAL_CALLS_PER_DAY`).",
        "- The application declares its own variables under `env` in its manifest "
        "(`app/config/MANIFEST.json`); the launcher accepts them, and they are listed there, not here.",
        "",
        "`env/deployment.env` (KEY=VALUE, `#` comments) is read at every launch. An exported "
        "variable wins over the file.",
        "",
    ]
    seen = set()
    for kind, title, blurb in KINDS:
        rows = sorted((n, r) for n, r in env.items() if r.get("kind") == kind)
        if not rows:
            continue
        lines += ["## " + title, "", blurb, "", "| variable | default | means | declared by |",
                  "|---|---|---|---|"]
        for n, r in rows:
            seen.add(n)
            lines.append("| `%s` | %s | %s | %s |" % (
                n, ("`%s`" % r["default"]) if str(r.get("default") or "") else "—",
                str(r.get("means") or "").replace("|", "\\|"), r.get("package") or "?"))
        lines.append("")
    rest = sorted(n for n in env if n not in seen)
    if rest:
        lines += ["## Other", "", "| variable | default | means | declared by |", "|---|---|---|---|"]
        for n in rest:
            r = env[n]
            lines.append("| `%s` | %s | %s | %s |" % (n, r.get("default") or "—",
                                                      r.get("means") or "", r.get("package") or "?"))
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    text = render()
    if "--check" in sys.argv[1:]:
        try:
            with open(OUT, encoding="utf-8") as fh:
                cur = fh.read()
        except OSError:
            cur = ""
        if cur != text:
            print("docs/deployment.md is stale — run: python scripts/gen_deployment_doc.py")
            return 1
        print("docs/deployment.md is current")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote docs/deployment.md (%d variables)" % text.count("\n| `"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
