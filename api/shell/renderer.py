"""
Output renderer for Akasha shell portals.
Formats JSON-RPC 2.0 responses into human-readable terminal output.
"""

import io
import sys
import shutil
import subprocess
import contextlib
import json
from api.env_detector import Colors


def c(color: str, text: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


# ── Truecolor aura helpers ─────────────────────────────────────────────────

def _hex_to_rgb(hex_col: str):
    """Parse '#RRGGBB' → (r, g, b). Returns None on invalid input."""
    h = (hex_col or "").lstrip('#')
    if len(h) != 6:
        return None
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None


def aura_c(hex_col: str, text: str) -> str:
    """Apply 24-bit ANSI truecolor foreground. Falls back to plain text on bad input."""
    rgb = _hex_to_rgb(hex_col)
    if not rgb:
        return text
    r, g, b = rgb
    return f"\033[38;2;{r};{g};{b}m{text}{Colors.ENDC}"


# Mirrors CosmosMapper palettes — kept in sync by design (see consciousness.py)
_EMO_AURA = {
    "emo:joy":          "#FFD060",
    "emo:trust":        "#88CC66",
    "emo:anticipation": "#FF9922",
    "emo:calm":         "#99CCBB",
    "emo:surprise":     "#44CCEE",
    "emo:fear":         "#5577BB",
    "emo:sadness":      "#5566AA",
    "emo:disgust":      "#9966BB",
    "emo:anger":        "#EE3344",
    "emo:awe":          "#CC88FF",
}
_SENSE_AURA = {
    "word:sense:sight": "#FFEE88",
    "word:sense:sound": "#66AADD",
    "word:sense:touch": "#EE99AA",
    "word:sense:taste": "#88CC88",
    "word:sense:smell": "#DD88CC",
}
_AXIS_AURA = {
    "emotion": "#CC88FF",
    "sense":   "#88CC88",
    "calc":    "#44CCEE",
    "word":    "#88CC66",
    "chrono":  "#FF9922",
    "story":   "#FF6699",
    "polti":   "#FFCC44",
}


def _alias_aura(alias: str):
    """Return hex color if alias is a known emotion or sense atom, else None."""
    return _EMO_AURA.get(alias or "") or _SENSE_AURA.get(alias or "")


def _page(text: str) -> None:
    """Pipe text through less -RFX, falling back to plain print if unavailable.

    Flags: -R pass ANSI colour codes; -F exit immediately when output fits on
    one screen (so short renders never open the pager); -X suppress terminal
    init/deinit so content stays on screen after quitting — important for
    numbered-selection commands (explore, dive, r) where the user needs to see
    the list while typing their selection number.
    """
    if not sys.stdout.isatty():
        sys.stdout.write(text)
        return
    try:
        proc = subprocess.Popen(
            ["less", "-RFXE"],
            stdin=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
        )
        try:
            proc.stdin.write(text)
            proc.stdin.close()
            proc.wait()
        except BrokenPipeError:
            pass  # user pressed q before reading all output
    except FileNotFoundError:
        # less not installed (Windows minimal env, Docker scratch, etc.)
        sys.stdout.write(text)


def paged_render(resp: dict) -> None:
    """Render a response, piping through a pager when output exceeds terminal height."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        render(resp)
    text = buf.getvalue()
    if not text:
        return
    term_h = shutil.get_terminal_size(fallback=(80, 24)).lines
    if text.count("\n") >= term_h - 1:
        _page(text)
    else:
        sys.stdout.write(text)


def render(resp: dict):
    """Render a JSON-RPC 2.0 response dict to stdout."""
    if "error" in resp:
        e    = resp["error"]
        msg  = e.get("message", str(e)) if isinstance(e, dict) else str(e)
        code = e.get("code", "")        if isinstance(e, dict) else ""
        print(c(Colors.FAIL, f"✖ [{code}] {msg}"))
        return

    result = resp.get("result")
    if result is None:
        return

    # ── TextViewConcept — deterministic dispatch, checked before heuristics ──
    if isinstance(result, dict) and "_view" in result:
        _render_textview(result)
        return

    if isinstance(result, dict) and result.get("type") == "lens:scan":
        render_lens_scan(result)
        return

    if isinstance(result, dict) and result.get("type") == "lens:cast":
        render_lens_cast(result)
        return

    if isinstance(result, dict) and result.get("type") == "lens:flatten":
        render_lens_flatten(result)
        return

    if isinstance(result, dict) and result.get("type") in ("atom", "collection"):
        render_dive(result)
        return

    if isinstance(result, dict) and result.get("type") == "thesaurus:AtomView":
        _render_thesaurus_atom_view(result)
        return

    if isinstance(result, dict) and result.get("type") == "thesaurus:CurationView":
        _render_thesaurus_curation_view(result)
        return

    if isinstance(result, dict) and result.get("type") == "thesaurus:SeriesView":
        _render_thesaurus_series_view(result)
        return

    if isinstance(result, dict) and "focus_state" in result:
        state  = result["focus_state"]
        status = result.get("status", "")
        col    = Colors.DIM if state == "@all" else Colors.CYAN
        suffix = f"  {c(Colors.DIM, status)}" if status else ""
        print(f"\n  {c(Colors.DIM, 'focus:')}  {c(col, state)}{suffix}\n")
        return

    if isinstance(result, dict) and "ceremony" in result:
        for line in result["ceremony"]:
            print(c(Colors.CYAN, f"  {line}"))
        return

    # ── JCL structured views ──────────────────────────────────────────────────
    if isinstance(result, dict) and "job_id" in result and "step_count" in result:
        _render_job(result)
        return

    if isinstance(result, dict) and "jobs" in result:
        _render_job_list(result)
        return

    if isinstance(result, dict) and "queue_depth" in result and "by_status" in result:
        _render_monitor(result)
        return

    if isinstance(result, dict) and "evidence" in result and "tx_id" in result:
        _render_job_log(result)
        return

    if isinstance(result, dict) and "users" in result and "count" in result:
        _render_user_list(result)
        return

    if isinstance(result, dict) and "groups" in result:
        _render_group_list(result)
        return

    if isinstance(result, dict) and "donation_sets" in result:
        _render_dont_ls(result)
        return

    if isinstance(result, dict) and result.get("type") in ("donation_set", "donation_receipt") or (
            isinstance(result, dict) and "set" in result and "donations" in result.get("meta", {})):
        _render_dont_detail(result)
        return

    if isinstance(result, dict) and "donated" in result and "set" in result:
        _render_dont_send(result)
        return

    if isinstance(result, dict) and "sets" in result and "count" in result and isinstance(result.get("sets"), list):
        _render_set_names(result)
        return

    if (isinstance(result, dict) and "members" in result and "set" in result
            and "count" in result and "donations" not in result.get("meta", {})):
        _render_set_ls(result)
        return

    if isinstance(result, dict) and "group" in result:
        _render_group_list({"groups": [result["group"]]})
        return

    # ── onto.* structured views ───────────────────────────────────────────────
    if isinstance(result, dict) and "packages" in result and "enabled" in result and isinstance(result.get("packages"), list):
        _render_onto_pack_list(result)
        return

    if isinstance(result, dict) and "nucleus" in result and "sentinels" in result:
        _render_onto_status(result)
        return

    if isinstance(result, dict) and "mode" in result and "items" in result and "count" in result:
        _render_onto_dump(result)
        return

    if isinstance(result, dict) and "exported" in result and "files" in result:
        _render_onto_export(result)
        return

    if isinstance(result, dict) and "pack" in result and result.get("status") in ("enabled", "disabled"):
        _render_onto_pack_status(result)
        return

    if isinstance(result, dict) and result.get("status") in ("reload_triggered", "reset_complete"):
        _render_onto_reload_reset(result)
        return

    if isinstance(result, dict) and "self" in result and "somatic_stats" in result:
        _render_status(result)
        return

    if isinstance(result, dict) and "slots" in result and all(
            k in result["slots"] for k in ("who", "where", "why")):
        _render_ref_slots(result["slots"])
        return

    if isinstance(result, dict) and "var" in result and "dim" in result:
        _render_ref_set(result)
        return

    if isinstance(result, dict) and "ak" in result and "call_count" in result:
        _render_csl_build(result)
        return

    if isinstance(result, dict) and "valid" in result and "errors" in result and isinstance(result.get("errors"), list):
        _render_csl_check(result)
        return

    if isinstance(result, dict) and "results" in result and isinstance(result.get("results"), list) and result.get("results") and "method" in result["results"][0]:
        _render_csl_run(result)
        return

    if isinstance(result, dict) and "atom" in result and "matches" in result and "count" in result:
        _render_cross_atom(result)
        return

    if isinstance(result, dict) and "table" in result and "row_key" in result and "data" in result:
        _render_tbl_row_get(result)
        return

    if isinstance(result, dict) and "table" in result and isinstance(result.get("columns"), list) and isinstance(result.get("rows"), list):
        _render_tbl_ls(result)
        return

    if isinstance(result, dict) and "name" in result and "alias" in result and "row_count" in result and isinstance(result.get("columns"), list):
        _render_tbl_get(result)
        return

    if isinstance(result, dict) and "attrs" in result and "key" in result and "content" in result:
        _render_rec_get(result)
        return

    if isinstance(result, dict) and "records" in result and "count" in result:
        _render_rec_ls(result)
        return

    if isinstance(result, dict) and "attr" in result and "sum" in result and "skipped" in result:
        _render_rec_sum(result)
        return

    if isinstance(result, dict) and "logs" in result and "count" in result:
        _render_log_list(result)
        return

    if isinstance(result, dict) and "has_passphrase" in result:
        _render_user_id(result)
        return

    if isinstance(result, dict) and ("out_links" in result or "in_links" in result):
        render_atom(result)
        return

    if isinstance(result, dict):
        key     = result.get("key")
        status  = result.get("status", "")
        alias   = result.get("alias", "")
        content = result.get("content")

        # ── Structured views — checked before generic key/status fallback ──
        if "links" in result:
            links = result["links"]
            root  = (key or "?")[:16] + "…"
            if not links:
                print(c(Colors.DIM, f"  {root}  (no links)"))
            else:
                print(c(Colors.DIM, f"\n  {root}"))
                for lk in links:
                    arrow = "→" if lk.get("direction") == "out" else "←"
                    rel   = c(Colors.DIM,  f"[{lk.get('rel', '?')}]")
                    lkey  = c(Colors.CYAN, (lk.get("key", "?"))[:14] + "…")
                    prev  = lk.get("preview", "")[:50]
                    print(f"  {arrow} {rel} {lkey}  {prev}")
                print()
            return
        if "tree" in result:
            _render_tree(result["tree"])
            return
        if "atoms" in result:
            atoms = result["atoms"]
            if not atoms:
                print(c(Colors.DIM, "  (no atoms written yet)"))
            else:
                print(c(Colors.DIM, f"\n  {'$n':<4} {'key':16}  preview"))
                print(c(Colors.DIM, "  " + "─" * 60))
                for a in atoms:
                    idx      = a.get("idx", 0)
                    key_str  = a.get("key", "")[:14] + "…"
                    preview  = str(a.get("preview", ""))[:50]
                    aliases  = a.get("aliases", [])
                    alias_str = f"  {c(Colors.GREEN, '@' + aliases[0])}" if aliases else ""
                    print(f"  ${idx:<3} {c(Colors.CYAN, key_str):<22}{alias_str}  {preview}")
                print()
            return
        if "history" in result:
            entries = result["history"]
            if not entries:
                print(c(Colors.DIM, "  (history empty)"))
            else:
                for e in entries:
                    key_str = e.get("key", "")[:14] + "…"
                    preview = str(e.get("preview", ""))[:60]
                    print(f"  {c(Colors.DIM, key_str)}  {preview}")
            return
        if "atoms" in result and "filters" in result:
            _render_explore(result)
            return
        if "voids" in result and "focal" in result:
            _render_assoc(result)
            return
        if "proposals" in result and "status" in result:
            _render_dream(result)
            return
        if "nodes" in result:
            _render_explore(result)
            return
        # ── Generic key/content/status fallback ──
        if content:
            print(c(Colors.GREEN, f"\n{content}\n"))
        elif key:
            hint = f"  {c(Colors.GREEN, '@' + alias)}" if alias else ""
            print(c(Colors.DIM, f"  ↳ {key[:14]}…") + hint + (f"  {c(Colors.DIM, status)}" if status else ""))
        elif "aliases" in result:
            for a in result["aliases"]:
                if isinstance(a, dict):
                    print(f"  {c(Colors.CYAN, a.get('alias','?'))}  →  {a.get('key','?')[:14]}…")
                else:
                    print(f"  {a}")
        elif status:
            print(c(Colors.DIM, f"  ✓ {status}"))
        else:
            # Generic concept list: {"<type>s": [{name/title/id, ...}]}
            # Catches n.ls, wb.ls, cp.ls, sv.ls, ag.ls, etc. — all return one list key.
            list_entries = [(k, v) for k, v in result.items() if isinstance(v, list)]
            if list_entries:
                _render_concept_list(result, list_entries)
            else:
                print(c(Colors.GREEN, json.dumps(result, indent=2, ensure_ascii=False)))
        return

    print(c(Colors.GREEN, str(result)))


_ROLE_COLOR = {
    "admin":       "\033[31m",   # red
    "librarian":   "\033[35m",   # magenta
    "group_admin": "\033[33m",   # yellow
    "user":        "\033[32m",   # green
    "guest":       "\033[90m",   # grey
}


def _render_user_list(result: dict):
    users = result.get("users", [])
    if not users:
        print(c(Colors.DIM, "  (no users registered)"))
        return
    print(c(Colors.DIM, f"\n  {'id':<20} {'role':<14} {'display_name':<20} created_at"))
    print(c(Colors.DIM, "  " + "─" * 72))
    for u in users:
        cid      = u.get("client_id", "")
        role     = u.get("role", "")
        name     = u.get("display_name", "")
        created  = (u.get("created_at") or "")[:10]
        col      = _ROLE_COLOR.get(role, "")
        print(f"  {c(Colors.CYAN, cid):<29} {col}{role:<14}{Colors.ENDC} {name:<20} {c(Colors.DIM, created)}")
    print()


def _render_user_id(result: dict):
    print(f"\n{c(Colors.CYAN, '─' * 48)}")
    print(f"  {c(Colors.DIM, 'id:')}           {c(Colors.CYAN, result.get('client_id', ''))}")
    role = result.get("role", "")
    col  = _ROLE_COLOR.get(role, "")
    print(f"  {c(Colors.DIM, 'role:')}         {col}{role}{Colors.ENDC}")
    if result.get("display_name"):
        print(f"  {c(Colors.DIM, 'display:')}      {result['display_name']}")
    if result.get("created_at"):
        print(f"  {c(Colors.DIM, 'created:')}      {result['created_at'][:19]}")
    if result.get("created_by"):
        print(f"  {c(Colors.DIM, 'created_by:')}   {result['created_by']}")
    pw = "yes" if result.get("has_passphrase") else c(Colors.WARNING, "NO — set with user.passwd")
    print(f"  {c(Colors.DIM, 'passphrase:')}   {pw}")
    groups = result.get("groups", [])
    if groups:
        print(f"  {c(Colors.DIM, 'groups:')}       {', '.join(groups)}")
    print()


def _render_group_list(result: dict):
    groups = result.get("groups", [])
    if not groups:
        print(c(Colors.DIM, "  (no groups)"))
        return
    for g in groups:
        gid      = g.get("group_id", "")
        admin    = g.get("admin", "")
        members  = g.get("members", [])
        libs     = g.get("librarians", [])
        print(f"\n  {c(Colors.CYAN, gid)}  {c(Colors.DIM, f'admin: {admin}')}")
        for m in members:
            tag = " [lib]" if m in libs else ""
            print(f"    · {m}{c(Colors.DIM, tag)}")
    print()


def render_atom(result: dict):
    """Render a kernel.memory.read response with full atom detail."""
    key      = result.get("key", "")
    content  = result.get("content", "")
    aliases  = result.get("aliases", [])
    meta     = result.get("meta", {}) or {}
    out_links = result.get("out_links", [])
    in_links  = result.get("in_links", [])

    print(f"\n{c(Colors.CYAN, '─' * 52)}")

    # Full hash key line
    print(f"  {c(Colors.DIM, 'key:')}  {c(Colors.CYAN, key)}")

    # Aliases (@name)
    if aliases:
        for alias in aliases:
            name = alias.get("alias", alias) if isinstance(alias, dict) else alias
            print(f"  {c(Colors.GREEN, f'@{name}')}")

    # Content in quotes
    if content:
        print(f"  {c(Colors.GREEN, chr(34) + str(content) + chr(34))}")

    # Meta fields (skip empty/internal)
    _SKIP_META = {"key", "content"}
    if meta:
        for mk, mv in meta.items():
            if mk not in _SKIP_META and mv is not None:
                print(f"  {c(Colors.DIM, mk + ':')}  {mv}")

    # Links
    all_links = out_links + in_links
    if all_links:
        print(f"  {c(Colors.DIM, '─' * 46)}")
        for lk in all_links:
            arrow   = "→" if lk.get("direction") == "out" else "←"
            rel     = lk.get("rel", "?")
            lkey    = lk.get("key", "")
            lshort  = lkey[:8] + "…" if len(lkey) > 8 else lkey
            laliases = lk.get("aliases", [])
            lalias_str = ""
            if laliases:
                la = laliases[0]
                la_name = la.get("alias", la) if isinstance(la, dict) else la
                lalias_str = f"  {c(Colors.GREEN, f'@{la_name}')}"
            preview = lk.get("preview", "")
            prev_str = f'  {c(Colors.DIM, chr(34) + preview[:50] + chr(34))}' if preview else ""
            print(f"  {c(Colors.CYAN, f'~{rel}')}  {arrow}  {c(Colors.DIM, lshort)}{lalias_str}{prev_str}")

    # Set membership
    sets = result.get("sets", [])
    if sets:
        print(f"  {c(Colors.DIM, '∈ sets:')}  {c(Colors.GREEN, '  '.join(sets))}")

    print()


def _render_tree(node: dict, prefix: str = "", is_last: bool = True):
    """Recursive tree printer."""
    if not node:
        return
    connector = "└─" if is_last else "├─"
    rel_str   = f"[{node.get('rel', 'root')}] " if node.get("rel") else ""
    key_str   = c(Colors.CYAN, node.get("key", "?")[:14] + "…")
    prev      = node.get("preview", "")[:60]
    print(f"  {prefix}{connector} {c(Colors.DIM, rel_str)}{key_str}  {prev}")
    children  = node.get("children", [])
    ext       = "   " if is_last else "│  "
    for i, child in enumerate(children):
        _render_tree(child, prefix + ext, i == len(children) - 1)


def _fmt_nd(nd: list) -> str:
    """Format cosmos_nd vector [x,y,z,t,layer,color] for terminal display."""
    if not nd or len(nd) < 3:
        return ""
    x, y, z = nd[0], nd[1], nd[2]
    color = nd[5] if len(nd) > 5 else ""
    color_s = f"  {color}" if color else ""
    return f"({x:.2f}, {y:.2f}, {z:.2f}){color_s}"


def _render_set_names(result: dict):
    """Render s.ls (no-arg) — list of user-defined set names."""
    sets  = result.get("sets", [])
    count = result.get("count", len(sets))
    print(f"\n{c(Colors.CYAN, '─── User-defined sets ' + '─'*30)}")
    print(c(Colors.DIM, f"  {count} set{'s' if count != 1 else ''}"))
    if not sets:
        print(c(Colors.DIM, "  (none — create with  s.add name=<name> id=<atom>)"))
        print()
        return
    for name in sets:
        print(f"  {c(Colors.GREEN, name)}")
    print()


def _render_set_ls(result: dict):
    """Render s.ls name=<set> — set member list."""
    name    = result.get("set", "?")
    members = result.get("members", [])
    count   = result.get("count", len(members))
    print(f"\n{c(Colors.CYAN, '─── set: ' + name + ' ' + '─'*max(0, 43-len(name)))}")
    print(c(Colors.DIM, f"  {count} member{'s' if count != 1 else ''}"))
    if not members:
        print(c(Colors.DIM, "  (empty)"))
        print()
        return
    for m in members:
        alias   = m.get("alias")
        key     = (m.get("key") or "")[:14] + "…"
        content = (m.get("content") or "")[:60].replace("\n", " ")
        label   = f"@{alias}" if alias else key
        col     = Colors.GREEN if alias else Colors.DIM
        print(f"  {c(col, label)}  {c(Colors.DIM, content)}")
    print()


def _render_concept_list(result: dict, list_entries: list):
    """Generic renderer for concept op_ls results: {<type>s: [{name/title/id, ...}]}.

    Handles n.ls, wb.ls, cp.ls, sv.ls, ag.ls, and any future concept that returns
    a dict with a single list-valued key. The largest list wins as the primary display.
    """
    list_key, items = max(list_entries, key=lambda x: len(x[1]))
    label = list_key.replace("_", " ").title()
    print(f"\n{c(Colors.CYAN, '─── ' + label + ' ' + '─'*max(0, 46-len(label)))}")
    print(c(Colors.DIM, f"  {len(items)} item{'s' if len(items) != 1 else ''}"))
    if not items:
        print(c(Colors.DIM, "  (none)"))
        print()
        return
    _SKIP_KEYS = {"meta", "created_at", "updated_at"}
    for item in items:
        if not isinstance(item, dict):
            print(f"  {item}")
            continue
        name_val = item.get("name") or item.get("title") or item.get("label") or ""
        id_val   = next((str(v)[:16] + "…" for k, v in item.items()
                         if (k.endswith("_id") or k == "id") and v), "")
        extras   = [(k, v) for k, v in item.items()
                    if k not in _SKIP_KEYS and not k.endswith("_id") and k != "id"
                    and k not in ("name", "title", "label") and v is not None][:2]
        extra_s  = "  ".join(f"{c(Colors.DIM, str(k) + '=' + str(v)[:20])}" for k, v in extras)
        line = f"  {c(Colors.GREEN, name_val)}" if name_val else f"  {c(Colors.DIM, id_val)}"
        if name_val and id_val:
            line += f"  {c(Colors.DIM, id_val)}"
        if extra_s:
            line += f"  {extra_s}"
        print(line)
    print()


def _render_explore(result: dict):
    """Render explore query results — flat list numbered for dive navigation."""
    atoms   = result.get("atoms", [])
    count   = result.get("count", len(atoms))
    filters = result.get("filters", {})

    filter_str = "  ".join(f"{k}={v}" for k, v in filters.items()) if filters else "all"
    print(f"\n{c(Colors.CYAN, '─' * 52)}")
    print(f"{c(Colors.CYAN, '◎')} explore  {c(Colors.DIM, filter_str)}  {c(Colors.DIM, f'{count} atoms')}")

    if not atoms:
        print(c(Colors.DIM, "  (nothing found)"))
        print()
        return

    for i, atom in enumerate(atoms):
        alias   = atom.get("alias") or ""
        preview = (atom.get("preview") or "")[:50].replace("\n", " ")
        label   = f"[{alias}]" if alias else (atom.get("key", "")[:12] + "…")
        hex_col = atom.get("color") or _alias_aura(alias)
        label_c = aura_c(hex_col, label) if hex_col else c(Colors.GREEN, label)
        print(f"  {i:>2}. {label_c}  {c(Colors.DIM, preview)}")

    if count > 0:
        print(c(Colors.DIM, f"\n     (type 0–{len(atoms) - 1} to dive)"))
    print()


def _render_assoc(result: dict):
    """Render assoc gap-detection results with numbered candidates for interactive selection."""
    focal  = result.get("focal", {})
    voids  = result.get("voids", [])
    filled = result.get("filled", [])
    axis   = result.get("axis", "all")

    alias_str = f" [{focal.get('alias')}]" if focal.get("alias") else ""
    print(f"\n{c(Colors.CYAN, '─' * 52)}")
    print(f"{c(Colors.CYAN, '⊘')} assoc{alias_str}  {c(Colors.DIM, f'axis={axis}')}")
    if focal.get("preview"):
        print(f"  {focal['preview'][:80]}")

    if not voids:
        print(c(Colors.GREEN, "  ✓ No link voids found on this atom."))
        print()
        return

    focal_ref = focal.get("alias") or focal.get("key", "?")
    num = 1  # global counter across all voids
    for void in voids:
        ax       = void.get("axis", "?")
        hint     = void.get("hint", "")
        cands    = void.get("candidates", [])
        miss_rel = void.get("missing", "")
        ax_col   = _AXIS_AURA.get(ax)
        ax_label = aura_c(ax_col, ax) if ax_col else c(Colors.CYAN, ax)
        print(f"\n  {ax_label}  {c(Colors.DIM, hint)}")
        if cands:
            print(f"    {c(Colors.DIM, 'candidates:')}")
            for cand in cands:
                ca      = cand.get("alias") or ""
                a       = f"[{ca}]" if ca else cand.get("key","")[:12]+"…"
                cand_col = cand.get("color") or _alias_aura(ca)
                a_c     = aura_c(cand_col, a) if cand_col else c(Colors.GREEN, a)
                rel     = c(Colors.DIM, cand.get("rel",""))
                cnt     = c(Colors.DIM, f"×{cand['count']}")
                prv     = cand.get("preview","")[:35]
                print(f"    {c(Colors.CYAN, str(num)):>6}. {rel} → {a_c}  {prv}  {cnt}")
                num += 1
        else:
            hint_rel = miss_rel or ax
            print(f"    {c(Colors.DIM, f'(no candidates — ln {focal_ref} <target> {hint_rel})')}")

    if filled:
        print(f"\n  {c(Colors.GREEN, f'Filled {len(filled)} void(s):')}")
        for f_item in filled:
            a = f"[{f_item['alias']}]" if f_item.get("alias") else f_item.get("dst","")[:12]+"…"
            print(f"    {c(Colors.DIM, f_item.get('rel',''))} → {c(Colors.GREEN, a)}")

    if num > 1:
        print(c(Colors.DIM, f"\n     (type 1–{num - 1} to create link)"))
    print()


def extract_assoc_menu(result: dict) -> dict:
    """Extract numbered candidate menu from assoc result. Returns state dict for the REPL."""
    focal       = result.get("focal", {})
    focal_key   = focal.get("key", "")
    focal_alias = focal.get("alias")

    menu = {}
    num = 1
    for void in result.get("voids", []):
        for cand in void.get("candidates", []):
            menu[num] = {
                "focal_key":   focal_key,
                "focal_alias": focal_alias,
                "dst_key":     cand.get("key", ""),
                "dst_alias":   cand.get("alias"),
                "rel":         cand.get("rel", ""),
                "axis":        void.get("axis", ""),
            }
            num += 1
    return {"focal_key": focal_key, "focal_alias": focal_alias, "menu": menu}


def _render_dream(result: dict):
    """Render dream hypothetical-linking results with numbered proposals for approval."""
    focal     = result.get("focal") or {}
    proposals = result.get("proposals", [])
    committed = result.get("committed", [])
    status    = result.get("status", "")
    axis      = result.get("axis", "all")

    alias_str = f" [{focal.get('alias')}]" if focal.get("alias") else ""
    print(f"\n{c(Colors.CYAN, '─' * 52)}")
    print(f"{c(Colors.CYAN, '✦')} dream{alias_str}  {c(Colors.DIM, f'axis={axis}  status={status}')}")

    if not proposals:
        print(c(Colors.DIM, "  (no hypothetical links proposed)"))
        print()
        return

    src_labels = {"structural": "struct", "transitive": "trans", "affinity": "affin", "jataka": "jataka"}
    print(f"\n{c(Colors.DIM, 'Proposals:')}")
    for num, p in enumerate(proposals, start=1):
        src     = p.get("source", "?")
        rel     = p.get("rel", "?")
        ax      = p.get("axis", "")
        alias   = p.get("alias") or p.get("dst","")[:12]
        prv     = p.get("preview", "")[:38]
        hint    = p.get("hint", "")
        ax_str  = f" [{ax}]" if ax else ""
        src_str = src_labels.get(src, src)
        hex_col = p.get("color") or _alias_aura(alias)
        dst_c   = aura_c(hex_col, f"[{alias}]") if hex_col else c(Colors.GREEN, f"[{alias}]")
        if rel.startswith("tent:"):
            inner   = rel[5:]
            rel_str = f"\033[2;3mtent:\033[0m{c(Colors.DIM, inner)}"
        else:
            rel_str = c(Colors.DIM, rel)
        print(f"  {c(Colors.CYAN, str(num)):>6}. {rel_str} → {dst_c}  {prv}{ax_str}  {c(Colors.DIM, f'[{src_str}]')}")
        if hint:
            print(f"         {c(Colors.DIM, hint)}")

    if committed:
        print(f"\n{c(Colors.GREEN, f'Committed {len(committed)} tent: link(s):')}")
        for item in committed:
            a = f"[{item['alias']}]" if item.get("alias") else item.get("dst","")[:12]+"…"
            print(f"  {c(Colors.DIM, item.get('rel',''))} → {c(Colors.GREEN, a)}")
    else:
        print(c(Colors.DIM, f"\n     (type 1–{len(proposals)} to approve  |  commit=yes to write all as tent:)"))
    print()


def extract_dream_menu(result: dict) -> dict:
    """Extract numbered proposal menu from dream result for interactive approval."""
    focal       = (result.get("focal") or {})
    focal_key   = focal.get("key", "")
    focal_alias = focal.get("alias")

    menu = {}
    for i, p in enumerate(result.get("proposals", []), start=1):
        rel = p.get("rel", "")
        real_rel = rel[5:] if rel.startswith("tent:") else rel
        menu[i] = {
            "focal_key":   focal_key,
            "focal_alias": focal_alias,
            "dst_key":     p.get("dst", ""),
            "dst_alias":   p.get("alias"),
            "rel":         real_rel,
            "axis":        p.get("axis", ""),
            "source":      p.get("source", ""),
        }
    return {"focal_key": focal_key, "focal_alias": focal_alias, "menu": menu}


# ── Lens (source scanner + projection engine) ─────────────────────────────────

def _bar(coverage: float, width: int = 10) -> str:
    filled = round(coverage * width)
    return "█" * filled + "░" * (width - filled)


def render_lens_scan(result: dict):
    """Render a lens.scan result — profile summary + numbered candidates."""
    src        = result.get("src", "?")
    profile    = result.get("profile", {})
    candidates = result.get("candidates", [])

    node_count = profile.get("node_count", 0)
    scope      = profile.get("scope", "")
    attrs      = profile.get("attrs", {})
    content_ok = profile.get("content_available", False)

    print(f"\n{c(Colors.CYAN, '─' * 56)}")
    print(f"{c(Colors.CYAN, '◎')} lens scan  {c(Colors.DIM, src)}  "
          f"{c(Colors.DIM, f'{node_count} node(s)')}  {c(Colors.DIM, scope)}")

    # Attribute coverage table
    if attrs:
        print(f"\n{c(Colors.DIM, '  Attributes:')}")
        for attr_name, info in sorted(attrs.items()):
            cov     = info.get("coverage", 0)
            th      = info.get("type_hint", "text")
            sample  = info.get("sample", "")[:30]
            bar     = _bar(cov)
            cov_str = f"{int(cov * 100):3d}%"
            print(f"  {c(Colors.DIM, bar)} {cov_str}  {c(Colors.CYAN, attr_name):<28}  "
                  f"{c(Colors.DIM, th):<6}  {sample}")
    if content_ok:
        sample = str(profile.get("content_sample", ""))[:50]
        print(f"\n  {c(Colors.DIM, 'content:')} {sample}")

    # Data preview (when nodes carry actual attribute data)
    preview_cols = result.get("preview_cols", [])
    preview_rows = result.get("preview_rows", [])
    if preview_rows and preview_cols:
        print(f"\n{c(Colors.DIM, '  Data preview:')}")
        _render_table(preview_cols, preview_rows, max_col_w=24)

    # Candidates
    if not candidates:
        print(c(Colors.DIM, "\n  (no compatible concept models found)"))
    else:
        print(f"\n{c(Colors.DIM, '  Candidates:')}")
        for i, cand in enumerate(candidates, start=1):
            model   = cand.get("model", "?")
            score   = cand.get("score", 0.0)
            notes   = cand.get("notes", [])
            missing = cand.get("missing", [])
            score_bar = _bar(score, 8)
            note_str  = f"  {c(Colors.DIM, notes[0])}" if notes else ""
            miss_str  = f"  {c(Colors.FAIL, 'missing: ' + ', '.join(missing))}" if missing else ""
            print(f"  {c(Colors.CYAN, str(i)):>6}.  {c(Colors.GREEN, model):<16}"
                  f"  {c(Colors.DIM, score_bar)} {score:.2f}{note_str}{miss_str}")
        print(c(Colors.DIM, f"\n       type 1–{len(candidates)} to project  |  lens.cast signpost=N [into=<name>]"))
    print()


def render_lens_cast(result: dict):
    """Render a lens.cast result — projection summary."""
    model      = result.get("model", "?")
    into       = result.get("into", "?")
    node_count = result.get("node_count", 0)
    inner      = result.get("result", {})

    created    = inner.get("created", into)
    alias      = inner.get("alias", "")
    rows       = inner.get("rows_written", node_count)
    cols       = inner.get("cols_written", 0)

    print(f"\n{c(Colors.CYAN, '─' * 56)}")
    print(f"{c(Colors.GREEN, '✓')} lens cast → {c(Colors.GREEN, model)}")
    print(f"  {c(Colors.DIM, 'name:')}   {c(Colors.CYAN, created)}"
          + (f"  {c(Colors.GREEN, '@' + alias)}" if alias else ""))
    if cols:
        print(f"  {c(Colors.DIM, 'cols:')}   {cols}")
    print(f"  {c(Colors.DIM, 'rows:')}   {rows}")
    print()


def render_lens_flatten(result: dict):
    """Render a lens.flatten result — snapshot summary."""
    into    = result.get("into", "?")
    written = result.get("written", 0)
    print(f"\n{c(Colors.CYAN, '─' * 56)}")
    print(f"{c(Colors.GREEN, '✓')} lens flatten → {c(Colors.GREEN, into)}")
    print(f"  {c(Colors.DIM, 'atoms:')}  {written}")
    print(f"  {c(Colors.DIM, 'use:')}    rec.table in_set={into}  |  lens src={into}  |  table.ls ...")
    print()


def extract_lens_candidates(result: dict) -> dict:
    """Extract numbered candidate list from lens.scan result. Returns state dict for the REPL."""
    candidates = result.get("candidates", [])
    src        = result.get("src", "")
    menu = {}
    for i, cand in enumerate(candidates, start=1):
        menu[i] = cand
    return {"src": src, "candidates": menu}


def render_dive(view: dict):
    """Render a dive view: focus atom/collection, signposts, and cosmos neighbourhood."""
    focus        = view.get("focus", {})
    signposts    = view.get("signposts", [])
    resonance    = view.get("resonance", [])
    associations = view.get("associations", [])
    concept      = view.get("concept", {})       # concept atom for collection views
    view_type    = view.get("type", "atom")

    print(f"\n{c(Colors.CYAN, '─' * 52)}")
    alias_str = f" [{focus.get('alias')}]" if focus.get("alias") else ""
    print(f"{c(Colors.CYAN, '▶')} {focus.get('key','')[:16]}…{alias_str}")
    if focus.get("content"):
        print(f"  {str(focus['content'])[:120]}")

    # ── For collection view: show linked concept atom if exists ───────────
    if view_type == "collection" and concept:
        c_alias = concept.get("alias") or concept.get("key","")[:12]
        c_content = concept.get("content", "")[:80]
        n_links   = concept.get("link_count", 0)
        links_str = c(Colors.DIM, f"  {n_links} links") if n_links else ""
        c_preview = c_content.split("\n")[-1].strip() if "\n" in c_content else c_content
        c_preview = c_preview[:60]
        print(f"\n  {c(Colors.DIM, 'Concept:')}  {c(Colors.GREEN, c_alias)}  {c(Colors.DIM, c_preview)}{links_str}")
        print(f"  {c(Colors.DIM, '(dive ' + c_alias + '  — to enter concept atom)')}")

    # ── Cosmos vector for focus atom ──────────────────────────────────────
    focus_nd = focus.get("cosmos_nd")
    if focus_nd:
        nd_str = _fmt_nd(focus_nd)
        print(f"  {c(Colors.DIM, 'cosmos: ' + nd_str)}")

    # ── Signposts: links + containment, numbered for navigation ──────────
    if signposts:
        link_sps   = [sp for sp in signposts if sp.get("rel") != "sys:member_of"]
        set_sps    = [sp for sp in signposts if sp.get("rel") == "sys:member_of" and sp.get("direction") == "out"]
        member_sps = [sp for sp in signposts if sp.get("rel") == "sys:member_of" and sp.get("direction") == "in"]

        if link_sps:
            print(f"\n{c(Colors.DIM, 'Signposts:')}")
            for sp in link_sps[:15]:
                raw_alias = (f"[{sp['alias']}]" if sp.get("alias")
                             else sp.get("key", "")[:12] + "…")
                sp_nd   = sp.get("cosmos_nd")
                hex_col = (sp_nd[5] if (sp_nd and len(sp_nd) > 5) else None) \
                          or _alias_aura(sp.get("alias") or "")
                alias   = aura_c(hex_col, raw_alias) if hex_col else raw_alias
                rel     = c(Colors.DIM, sp.get("rel", ""))
                arrow   = "←" if sp.get("direction") == "in" else "→"
                bra     = sp.get("branches_ahead", 0)
                bra_s   = f"  {c(Colors.DIM, f'[{bra}→]')}" if bra else ""
                print(f"  {sp['index']:>2}. {rel} {arrow} {alias}  {sp.get('preview','')[:40]}{bra_s}")

        if set_sps:
            print(f"\n{c(Colors.DIM, 'Collections: ∈')}")
            for sp in set_sps:
                alias = (f"[{sp['alias']}]" if sp.get("alias")
                         else sp.get("key", "")[:12] + "…")
                print(f"  {sp['index']:>2}. {c(Colors.DIM, '∈')} {c(Colors.GREEN, alias)}")

        if member_sps:
            print(f"\n{c(Colors.DIM, 'Members: ⊃')}")
            for sp in member_sps:
                alias = (f"[{sp['alias']}]" if sp.get("alias")
                         else sp.get("key", "")[:12] + "…")
                print(f"  {sp['index']:>2}. {c(Colors.DIM, '⊃')} {alias}  {sp.get('preview','')[:40]}")

        print(c(Colors.DIM, f"     (type 0–{len(signposts)-1} to navigate)"))

    # ── Resonance: atoms that share semantic tags with this atom ──────────
    if resonance:
        print(f"\n{c(Colors.DIM, 'Resonance:')}")
        for r in resonance[:6]:
            via  = r.get("via_alias") or r.get("via", "")[:16]
            prev = r.get("preview", "")[:50]
            print(f"      ≈ via [{c(Colors.DIM, via)}]  {prev}")

    # ── Field summary: semantic neighborhood breadth ──────────────────────
    if associations:
        type_counts: dict = {}
        for a in associations:
            t = a.get("type", "?")
            type_counts[t] = type_counts.get(t, 0) + 1
        type_str = "  ".join(f"{t}:{n}" for t, n in
                              sorted(type_counts.items(), key=lambda x: -x[1]))
        print(f"\n{c(Colors.DIM, f'Field: {len(associations)} nodes  [{type_str}]')}")
    elif signposts:
        # Compact cosmos neighbourhood summary from signpost vectors
        nd_list = [sp.get("cosmos_nd") for sp in signposts if sp.get("cosmos_nd")]
        if nd_list:
            colors = {nd[5] for nd in nd_list if len(nd) > 5 and nd[5]}
            print(f"\n{c(Colors.DIM, f'Cosmos field: {len(signposts)} neighbours  {len(colors)} regions')}")

    print()


def _render_ref_set(result: dict):
    """Render result of ref.set."""
    var = result.get("var", "")
    key = result.get("key", "—")
    print(f"  {c(Colors.CYAN, var)}  →  {c(Colors.GREEN, key[:16])}{'…' if len(key) > 16 else ''}")


def _render_ref_slots(slots: dict):
    """Render result of ref.get (all slots)."""
    from lib.akasha.ref_primitives import REF_SLOT_DIMENSIONS
    # Two-column: interrogative axes first, then deictic
    interrog = ["who", "what", "where", "when", "why", "how", "which"]
    deictic  = ["this", "that", "here", "there", "now", "then"]

    def _slot_line(dim):
        val = slots.get(dim)
        label = f"${dim}:".ljust(8)
        if val:
            short = val[:20] + ("…" if len(val) > 20 else "")
            return f"{c(Colors.CYAN, label)} {c(Colors.GREEN, short)}"
        return f"{c(Colors.DIM, label)} {c(Colors.DIM, '—')}"

    print(f"\n{c(Colors.DIM, '  Ref slots')}")
    pairs = list(zip(interrog[::2], interrog[1::2]))
    if len(interrog) % 2:
        pairs.append((interrog[-1], None))
    for a, b in pairs:
        left  = _slot_line(a)
        right = ("  " + _slot_line(b)) if b else ""
        print(f"    {left}{right}")

    print(f"\n{c(Colors.DIM, '  Deictic')}")
    dpairs = list(zip(deictic[::2], deictic[1::2]))
    for a, b in dpairs:
        left  = _slot_line(a)
        right = ("  " + _slot_line(b)) if b else ""
        print(f"    {left}{right}")
    print()


def render_svc_list(services: list, session_counts: dict = None):
    """Render ServiceManager.list_services() + live session summary.

    session_counts: optional dict from AkashaManager.count_sessions()
    """
    if not services:
        print(c(Colors.DIM, "  (no services registered)"))
    else:
        print(c(Colors.DIM, f"\n  {'name':<22} {'status':<8} {'engine':<8} {'address / pid':<22} uptime"))
        print(c(Colors.DIM,   "  " + "─" * 72))
        for s in services:
            name   = s.get("name", "?")
            status = s.get("status", "?")
            engine = s.get("engine", "?")
            uptime = s.get("uptime_sec")
            uptime_str = f"{uptime}s" if uptime is not None else "—"
            status_c = c(Colors.GREEN, status) if status == "Active" else c(Colors.FAIL, status)
            if engine == "thread":
                host = s.get("host", "0.0.0.0")
                port = s.get("port", 0)
                addr = f"http://{host}:{port}" if port else f"http://{host}:?"
                print(f"  {name:<22} {status_c:<18} {engine:<8} {addr:<22} {uptime_str}")
            else:
                pid = s.get("pid", "?")
                print(f"  {name:<22} {status_c:<18} {engine:<8} {'PID=' + str(pid):<22} {uptime_str}")

    if session_counts is not None:
        total = session_counts.get("total", 0)
        parts = []
        for role in ("admin", "librarian", "user", "group_admin", "guest"):
            n = session_counts.get(role, 0)
            if n:
                parts.append(f"{role}: {n}")
        detail = "  (" + "  ".join(parts) + ")" if parts else ""
        total_c = c(Colors.CYAN, str(total)) if total else c(Colors.DIM, "0")
        print(f"\n  {c(Colors.DIM, 'sessions:')}  {total_c} connected{c(Colors.DIM, detail)}")
    print()


def _render_csl_build(result: dict):
    """Render csl.build output — .ak text with a header."""
    ak      = result.get("ak", "")
    n_calls = result.get("call_count", 0)
    n_lines = result.get("source_lines", 0)
    out     = result.get("out")
    header  = f"# transpiled from {n_lines} CSL lines → {n_calls} .ak operations"
    if out:
        header += f" → {out}"
    print(c(Colors.DIM, f"\n  {header}\n"))
    for line in ak.splitlines():
        if line.startswith("#"):
            print(c(Colors.DIM, f"  {line}"))
        else:
            print(f"  {c(Colors.CYAN, line)}")
    print()


def _render_csl_check(result: dict):
    """Render csl.check output — validation report."""
    valid  = result.get("valid", False)
    errors = result.get("errors", [])
    if valid:
        print(c(Colors.GREEN, "\n  ✓ CSL valid\n"))
        return
    print(c(Colors.RED, f"\n  ✗ CSL invalid — {len(errors)} issue(s)\n"))
    for e in errors:
        lvl    = e.get("level", "error")
        color  = Colors.RED if lvl == "error" else Colors.YELLOW
        loc    = f"line {e.get('line', '?')}"
        if e.get("col"):
            loc += f":{e['col']}"
        msg    = e.get("error", "")
        hint   = e.get("suggestion", "")
        print(f"  {c(color, lvl.upper()):<12}  {c(Colors.DIM, loc):<14}  {msg}")
        if hint:
            print(c(Colors.DIM, f"              hint: {hint}"))
    print()


def _render_csl_run(result: dict):
    """Render csl / csl.run output — per-operation results."""
    results = result.get("results", [])
    if not results:
        print(c(Colors.DIM, "\n  (no operations)\n"))
        return
    ok_count  = sum(1 for r in results if not r.get("error"))
    err_count = len(results) - ok_count
    summary   = f"{ok_count} ok" + (f", {err_count} failed" if err_count else "")
    print(c(Colors.DIM, f"\n  {summary}\n"))
    for r in results:
        method  = r.get("method", "?")
        assigns = r.get("assigns_to")
        err     = r.get("error")
        res     = r.get("result")
        if err:
            print(f"  {c(Colors.RED, '✗')} {c(Colors.DIM, method)}  {c(Colors.RED, str(err))}")
        else:
            assign_str = f"  ${assigns} =" if assigns else ""
            res_str    = ""
            if isinstance(res, dict) and "key" in res:
                res_str = c(Colors.DIM, res["key"][:14] + "…")
            elif res is not None:
                res_str = c(Colors.DIM, str(res)[:60])
            print(f"  {c(Colors.GREEN, '✓')} {c(Colors.DIM, method)}{assign_str}  {res_str}")
    print()


def _render_cross_atom(result: dict):
    """Render cross.atom output — concept atoms that reference an ontology atom."""
    matches   = result.get("matches", [])
    count     = result.get("count", len(matches))
    atom      = result.get("atom", "?")
    query     = result.get("atom_query", atom)
    concepts  = result.get("concepts")

    header = f"  {count} atom(s) referencing {c(Colors.CYAN, query)}"
    if concepts:
        header += f"  {c(Colors.DIM, 'in: ' + ', '.join(concepts))}"
    print(c(Colors.DIM, f"\n{header}\n"))

    if not matches:
        print(c(Colors.DIM, "  (none found)\n"))
        return

    REL_LABEL = {"instance_of": "instance", "sys:refers_to": "weave"}
    for m in matches:
        key       = m.get("key", "?")
        preview   = m.get("preview", "")[:50]
        rel       = REL_LABEL.get(m.get("relation", ""), m.get("relation", ""))
        present   = ", ".join(m.get("present_in", []))
        rel_color = Colors.GREEN if rel == "instance" else Colors.DIM
        tag       = f"[{present}]" if present else ""
        print(f"  {c(rel_color, rel):<10}  {c(Colors.DIM, key[:14] + '…')}  {preview}  {c(Colors.DIM, tag)}")
    print()


def _render_rec_get(result: dict):
    """Render rec.get output — record with all attributes."""
    key     = result.get("key", "?")
    content = result.get("content", "")
    type_   = result.get("type", "")
    attrs   = result.get("attrs", {})

    header = f"  {c(Colors.DIM, key[:14] + '…')}"
    if type_:
        header += f"  {c(Colors.DIM, '[' + type_ + ']')}"
    print(c(Colors.DIM, f"\n{header}"))
    if content:
        print(f"  {content}")
    if attrs:
        print()
        for k, v in sorted(attrs.items()):
            print(f"  {c(Colors.GREEN, k):<20}  {v}")
    print()


def _render_rec_ls(result: dict):
    """Render rec.ls output — list of records."""
    records = result.get("records", [])
    count   = result.get("count", len(records))
    type_   = result.get("type") or ""
    in_set  = result.get("in_set") or ""

    scope = type_ or in_set or "all"
    print(c(Colors.DIM, f"\n  {count} record(s)  [{scope}]\n"))
    if not records:
        print(c(Colors.DIM, "  (none)\n"))
        return
    for r in records:
        key     = r.get("key", "?")
        preview = r.get("preview", "")
        print(f"  {c(Colors.DIM, key[:14] + '…')}  {preview}")
    print()


def _render_rec_sum(result: dict):
    """Render rec.sum output — aggregated numeric total."""
    attr    = result.get("attr", "?")
    total   = result.get("sum", 0.0)
    count   = result.get("count", 0)
    skipped = result.get("skipped", 0)
    scope   = result.get("in_set") or result.get("type") or "all"

    # Format sum: drop .0 if integer value
    total_str = str(int(total)) if total == int(total) else f"{total:.4g}"
    print(c(Colors.DIM, f"\n  sum({attr})  [{scope}]\n"))
    print(f"  {c(Colors.GREEN, total_str)}")
    detail = f"  {count} record(s)"
    if skipped:
        detail += f"  {c(Colors.DIM, f'({skipped} non-numeric skipped)')}"
    print(c(Colors.DIM, detail))
    print()


def _render_table(columns: list, rows: list, max_col_w: int = 28) -> None:
    """Rich-table renderer. Columns is a list of str keys; rows is a list of dicts.

    Uses rich.table.Table with SIMPLE_HEAD box style so it fits the existing
    terminal output aesthetic without heavy borders.  Creates a fresh Console
    pointing at the current sys.stdout so it respects paged_render's redirect.
    """
    if not columns:
        print(c(Colors.DIM, "  (no columns)\n"))
        return
    if not rows:
        print(c(Colors.DIM, "  (empty)\n"))
        return

    import sys
    import shutil
    from rich.console import Console
    from rich.table import Table
    from rich import box as _box

    width = shutil.get_terminal_size(fallback=(100, 24)).columns
    con   = Console(file=sys.stdout, force_terminal=True, highlight=False, width=width)
    tbl   = Table(
        box=_box.SIMPLE_HEAD,
        show_header=True,
        header_style="dim",
        show_edge=False,
        padding=(0, 1),
    )

    # Add columns — detect numeric columns for right-alignment
    numeric_cols: set = set()
    for col in columns:
        vals = [str(r.get(col) or "") for r in rows if r.get(col)]
        if vals and all(_looks_numeric(v) for v in vals[:20]):
            numeric_cols.add(col)
    for col in columns:
        justify = "right" if col in numeric_cols else "left"
        # Truncate column values that exceed max_col_w
        tbl.add_column(col, justify=justify, no_wrap=True,
                        max_width=max_col_w, overflow="ellipsis")

    for row in rows:
        tbl.add_row(*[str(row.get(col) or "") for col in columns])

    print()
    con.print(tbl)


def _looks_numeric(s: str) -> bool:
    """Return True if s looks like an integer, float, or currency value."""
    cleaned = s.replace(",", "").replace("_", "").lstrip("+-¥$€£")
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _render_tbl_ls(result: dict):
    """Render tbl.ls output — rows as an aligned table."""
    tbl_name = result.get("table", "?")
    columns  = result.get("columns", [])
    rows     = result.get("rows", [])
    count    = result.get("count", len(rows))

    print(c(Colors.DIM, f"\n  tbl:{tbl_name}  {count} row(s)\n"))
    if not rows:
        print(c(Colors.DIM, "  (empty)\n"))
        return
    # Rows are {key, data: {col: val}} from op_ls; unwrap data
    norm = [r.get("data", r) for r in rows]
    _render_table(columns, norm)


def _render_tbl_row_get(result: dict):
    """Render tbl.row.get — single row as vertical KV list."""
    tbl_name = result.get("table", "?")
    row_key  = result.get("row_key", "?")
    data     = result.get("data", {})

    print(c(Colors.DIM, f"\n  tbl:{tbl_name}  {row_key[:14]}…\n"))
    for col, val in data.items():
        val_str = str(val or "")[:60]
        print(f"  {c(Colors.CYAN, col):<24}  {val_str}")
    print()


def _render_tbl_get(result: dict):
    """Render tbl.get — table schema and row count."""
    name      = result.get("name", "?")
    columns   = result.get("columns", [])
    row_count = result.get("row_count", 0)

    print(f"\n  {c(Colors.CYAN, 'tbl:' + name)}  {c(Colors.DIM, str(row_count) + ' rows')}\n")
    for col in columns:
        if isinstance(col, dict):
            col_name = col.get("name", "?")
            col_type = col.get("type", "text")
        else:
            col_name, col_type = str(col), "text"
        print(f"  {c(Colors.GREEN, col_name):<26}  {c(Colors.DIM, col_type)}")
    print()


def _render_log_list(result: dict):
    """Render log.ls output."""
    logs = result.get("logs", [])
    if not logs:
        print(c(Colors.DIM, "\n  (no logs)\n"))
        return
    print(c(Colors.DIM, f"\n  {'name':<30}  {'created':>19}  active"))
    print(c(Colors.DIM,   "  " + "─" * 60))
    import datetime as _dt
    for lg in logs:
        name     = str(lg.get("name", ""))[:28]
        ts       = lg.get("created_at", 0) or 0
        active   = lg.get("active", False)
        try:
            dt_str = _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            dt_str = "—"
        mark = c(Colors.GREEN, " ✓") if active else ""
        print(f"  {name:<30}  {dt_str}  {mark}")
    print()


def _render_status(result: dict):
    """Render sys.status.full — aggregated system dashboard."""
    import datetime as _dt

    self_  = result.get("self", {})
    soma   = result.get("somatic_stats", {})
    resil  = result.get("resilience", {})
    env    = result.get("environment", {})
    ctx    = result.get("experiential_context", {})
    jcl    = result.get("jcl")
    focus  = result.get("display_focus") or {}
    name   = result.get("akasha_name", "AKASHA")
    series = result.get("series", "")
    lat    = self_.get("reflection_latency_ms", 0)
    uptime = env.get("uptime_seconds", 0)

    version    = result.get("version", "")
    ver_str    = f"  v{version}" if version else ""
    series_str = f"  [{series}]" if series else ""
    lat_str    = f"{lat:.0f}ms" if lat else "—"

    # Uptime: human-readable
    up_h, up_rem = divmod(int(uptime), 3600)
    up_m, up_s   = divmod(up_rem, 60)
    uptime_str   = (f"{up_h}h {up_m}m" if up_h else f"{up_m}m {up_s}s") if uptime else "—"

    _W = 52
    _header_inner = name + ver_str + series_str
    print(f"\n{c(Colors.CYAN, '─── ' + _header_inner + ' ' + '─'*max(0, _W-6-len(_header_inner)))}")
    state_col = Colors.GREEN if self_.get("state") == "alive" else Colors.FAIL
    print(f"  {c(state_col, self_.get('state', '?'))}  ·  {c(Colors.DIM, lat_str)}  ·  uptime {c(Colors.DIM, uptime_str)}")

    # Memory
    _atoms   = f"{soma.get('total_atoms',   0):,}"
    _links   = f"{soma.get('total_links',   0):,}"
    _aliases = f"{soma.get('total_aliases', 0):,}"
    _sets    = f"{soma.get('total_sets',    0):,}"
    print(f"\n{c(Colors.DIM, '  Memory')}")
    print(f"    atoms:    {c(Colors.GREEN, _atoms):<22}links:   {c(Colors.GREEN, _links)}")
    print(f"    aliases:  {c(Colors.GREEN, _aliases):<22}sets:    {c(Colors.GREEN, _sets)}")

    # Session
    print(f"\n{c(Colors.DIM, '  Session')}")
    print(f"    user:     {c(Colors.GREEN, str(ctx.get('active_client', '—')))}")
    focal = ctx.get("current_focal_point", "$origin")
    print(f"    focus:    {c(Colors.CYAN, str(focal))}")
    locale = ctx.get("locale_primary", "en")
    print(f"    locale:   {c(Colors.DIM, str(locale))}")

    # Display focus filter
    ns_prefixes = focus.get("ns_prefixes", [])
    scopes      = focus.get("scopes", [])
    if ns_prefixes or scopes:
        tokens = [f"@{s.split(':',1)[1]}" for s in scopes if ':' in s] + \
                 [f"@ns:{p.rstrip(':')}" for p in ns_prefixes]
        print(f"    filter:   {c(Colors.CYAN, '  '.join(tokens))}")
    else:
        print(f"    filter:   {c(Colors.DIM, '@all  (no focus set)')}")

    # Integrity
    pending = resil.get("unwoven_synapses_queued", 0)
    rstat   = resil.get("status", "?")
    rcol    = Colors.GREEN if rstat == "fully_functional" else Colors.WARNING
    print(f"\n{c(Colors.DIM, '  Integrity')}")
    print(f"    pending:  {c(rcol, str(pending))}  {c(Colors.DIM, '(' + rstat + ')')}")

    # JCL
    if jcl is not None:
        run  = jcl.get("running", 0)
        pend = jcl.get("pending", 0)
        qdep = jcl.get("queue_depth", 0)
        rcol = Colors.CYAN if run > 0 else Colors.DIM
        pcol = Colors.CYAN if pend > 0 else Colors.DIM
        print(f"\n{c(Colors.DIM, '  JCL')}")
        print(f"    running:  {c(rcol, str(run)):<22}pending:  {c(pcol, str(pend))}")
        if qdep > 0:
            print(f"    queue depth: {c(Colors.DIM, str(qdep))}")

    # Environment
    print(f"\n{c(Colors.DIM, '  Environment')}")
    print(f"    os:       {c(Colors.DIM, env.get('os', '?') + ' ' + env.get('os_release', ''))}")
    print(f"    python:   {c(Colors.DIM, env.get('python_version', '?'))}")
    db_path = env.get("database_path", "?")
    print(f"    db:       {c(Colors.DIM, db_path)}")

    # Libraries
    import importlib.util as _ilu
    _LIBS = [
        ("fastapi",               "fastapi"),
        ("uvicorn",               "uvicorn"),
        ("requests",              "requests"),
        ("torch",                 "torch"),
        ("sentence-transformers", "sentence_transformers"),
        ("numpy",                 "numpy"),
        ("tflite-runtime",        "tflite_runtime"),
    ]
    print(f"\n{c(Colors.DIM, '  Libraries')}")
    lib_pairs = [(_LIBS[i], _LIBS[i + 1] if i + 1 < len(_LIBS) else None)
                 for i in range(0, len(_LIBS), 2)]
    for left, right in lib_pairs:
        def _lib_col(label, mod):
            ok = _ilu.find_spec(mod) is not None
            mark  = c(Colors.GREEN, "✓") if ok else c(Colors.FAIL, "✗")
            plain = f"{label}:".ljust(24)
            col   = Colors.GREEN if ok else Colors.DIM
            return mark + "  " + c(col, plain)
        left_str = _lib_col(left[0], left[1])
        if right:
            right_str = _lib_col(right[0], right[1])
            print(f"    {left_str}{right_str}")
        else:
            print(f"    {left_str}")
    print()


_STATUS_COLOR = {
    "PENDING":   "\033[33m",   # yellow
    "RUNNING":   "\033[36m",   # cyan
    "DONE":      "\033[32m",   # green
    "FAILED":    "\033[31m",   # red
    "CANCELLED": "\033[90m",   # grey
}


def _status_str(status: str) -> str:
    col = _STATUS_COLOR.get(status, "")
    return f"{col}{status}{Colors.ENDC}"


def _render_job(j: dict):
    """Single job stat view."""
    done  = j.get("step_done", 0)
    total = j.get("step_count", 0)
    pct   = f"{done}/{total}"
    elapsed = j.get("elapsed_sec")
    elapsed_str = f"  {elapsed}s" if elapsed is not None else ""
    print(f"\n  {c(Colors.CYAN, j.get('job_id','?'))}  {_status_str(j.get('status','?'))}  {pct}{elapsed_str}")
    if j.get("label"):
        print(c(Colors.DIM, f"  label: {j['label']}"))
    if j.get("tx_id"):
        print(c(Colors.DIM, f"  tx:    {j['tx_id']}"))
    if j.get("error"):
        print(c(Colors.FAIL, f"  error: {j['error']}"))
    print()


def _render_job_list(result: dict):
    """job.ls view."""
    jobs = result.get("jobs", [])
    if not jobs:
        print(c(Colors.DIM, "  (no jobs)"))
        return
    print(c(Colors.DIM, f"\n  {'job_id':<18} {'status':<12} {'progress':<10} label"))
    print(c(Colors.DIM, "  " + "─" * 64))
    for j in jobs:
        done  = j.get("step_done", 0)
        total = j.get("step_count", 0)
        prog  = f"{done}/{total}"
        status_col = _status_str(j.get("status", "?"))
        label = j.get("label", "")[:28]
        print(f"  {c(Colors.CYAN, j.get('job_id','?')):<27} {status_col:<21} {prog:<10} {label}")
    print()


def _render_monitor(result: dict):
    """sys.monitor view."""
    by_status = result.get("by_status", {})
    summary   = "  ".join(f"{_status_str(s)}: {n}" for s, n in by_status.items())
    print(f"\n  Queue depth: {c(Colors.CYAN, str(result.get('queue_depth', 0)))}  "
          f"Total jobs: {result.get('total_jobs', 0)}")
    if summary:
        print(f"  {summary}")
    recent = result.get("recent", [])
    if recent:
        print(c(Colors.DIM, "\n  Recent:"))
        for j in recent:
            done  = j.get("step_done", 0)
            total = j.get("step_count", 0)
            print(f"    {c(Colors.CYAN, j.get('job_id','?'))}  "
                  f"{_status_str(j.get('status','?'))}  {done}/{total}  {j.get('label','')[:30]}")
    print()


def _render_job_log(result: dict):
    """job.log view."""
    evidence = result.get("evidence", [])
    print(c(Colors.DIM, f"\n  Job log for {result.get('job_id','?')}  tx={result.get('tx_id') or '—'}"))
    if not evidence:
        print(c(Colors.DIM, "  (no evidence atoms found)"))
    else:
        for e in evidence:
            t = e.get("type", "")
            tag = c(Colors.DIM, f"[{t}]")
            txt = e.get("content", "")[:80]
            print(f"  {tag}  {txt}")
    print()


def _render_dont_ls(result: dict):
    import time as _time
    sets = result.get("donation_sets", [])
    if not sets:
        print(c(Colors.DIM, "  (no delegation sets)"))
        return
    print(c(Colors.CYAN, f"\n  Delegation Sets ({len(sets)})\n"))
    for s in sets:
        name  = s["name"]
        count = s.get("atom_count", 0)
        meta  = s.get("meta", {})
        desc  = meta.get("description", "")
        dons  = meta.get("donations", [])
        ts    = meta.get("created_at", 0)
        date  = _time.strftime("%Y-%m-%d", _time.localtime(ts)) if ts else "?"
        line  = f"  {c(Colors.GREEN, name):<40} {count} atoms  {c(Colors.DIM, date)}"
        if desc:
            line += f"  {c(Colors.DIM, desc[:40])}"
        print(line)
        for d in dons:
            dt = _time.strftime("%Y-%m-%d %H:%M", _time.localtime(d.get("donated_at", 0)))
            print(f"      → {c(Colors.CYAN, d.get('target','?'))}  {d.get('atom_count',0)} atoms  {c(Colors.DIM, dt)}  [{d.get('mode','copy')}]")
    print()


def _render_dont_detail(result: dict):
    import time as _time
    set_name   = result.get("set", result.get("name", "?"))
    atom_count = result.get("atom_count", 0)
    meta       = result.get("meta", {})
    mtype      = meta.get("type", "")
    print(c(Colors.CYAN, f"\n  {set_name}"))
    print(f"  atoms: {atom_count}")
    if mtype == "donation_receipt":
        print(f"  from:  {c(Colors.GREEN, meta.get('source_cell', '?'))}")
        ts = meta.get("donated_at", 0)
        print(f"  date:  {_time.strftime('%Y-%m-%d %H:%M', _time.localtime(ts)) if ts else '?'}")
        print(f"  mode:  {meta.get('mode', 'copy')}")
    else:
        dons = meta.get("donations", [])
        if dons:
            print(f"  donations ({len(dons)}):")
            for d in dons:
                dt = _time.strftime("%Y-%m-%d %H:%M", _time.localtime(d.get("donated_at", 0)))
                print(f"    → {c(Colors.CYAN, d.get('target','?'))}  {d.get('atom_count',0)} atoms  {c(Colors.DIM, dt)}")
    print()


def _render_dont_send(result: dict):
    import time as _time
    status = result.get("status", "?")
    sname  = result.get("set", "?")
    to     = result.get("to", "?")
    n      = result.get("donated", 0)
    skip   = result.get("skipped", 0)
    mode   = result.get("mode", "copy")
    ts     = result.get("donated_at", 0)
    dt     = _time.strftime("%Y-%m-%d %H:%M", _time.localtime(ts)) if ts else "?"
    print(c(Colors.GREEN, f"\n  ✓ {sname}  →  {to}"))
    print(f"  {n} atoms donated  ({mode} mode)  {c(Colors.DIM, dt)}")
    if skip:
        print(c(Colors.DIM, f"  {skip} skipped (not found)"))
    print()


def print_help(core_specs: dict, concept_info: "list[tuple[str,str,int]]"):
    """Render core commands only; list concept models at the bottom."""
    print(f"\n{c(Colors.CYAN, '─── Commands ' + '─'*35)}")
    for cmd, spec in core_specs.items():
        args_str = "  ".join(f"<{a}>" for a in spec.get("args", []))
        print(f"  {c(Colors.GREEN, cmd):<22} {args_str:<32} {spec.get('desc','')}")
    print(f"\n  {c(Colors.DIM, '── Shell (REPL only) ──────────────────────────────────────────────────────')}")
    print(f"  {c(Colors.GREEN, 'csl'):<22} {'':32} Open the CSL interactive interpreter")
    print(f"  {c(Colors.GREEN, 'ont.load'):<22} {'':32} Load acquired ontology (.ak files)")
    print(f"  {c(Colors.GREEN, 'run <file>'):<22} {'':32} Submit .ak file as JCL batch job")
    print(f"  {c(Colors.GREEN, '<cmd> > <file>'):<22} {'':32} Redirect output to local file")
    print(f"  {c(Colors.GREEN, 'svc ls|stop|restart <n>'):<22} {'':32} Service control  (stop/restart: admin only)")
    print(f"  {c(Colors.GREEN, 'su <target|exit>'):<22} {'':32} Role switch: root / librarian / <user>  (admin only)")
    print(f"  {c(Colors.GREEN, 'history [n]'):<22} {'':32} Show last n commands (default 50)")
    print(f"  {c(Colors.GREEN, '!! / !n / !-n / !pfx'):<22} {'':32} Re-run: last / by index / from end / by prefix")
    print(f"  {c(Colors.GREEN, 'help [-c <model>] [<cmd>]'):<22} {'':32} This help / concept operators / command detail")
    print(f"  {c(Colors.GREEN, 'exit'):<22} {'':32} Disconnect")
    print(f"\n  {c(Colors.DIM, '── Auto-weave ─────────────────────────────────────────────────────────────')}")
    print(f"  {c(Colors.DIM, 'w / def / al / s.add'):<54} {c(Colors.DIM, 'trigger background Weaver → protoword links created automatically')}")
    if concept_info:
        print(f"\n{c(Colors.CYAN, '─── Concept models ' + '─'*29)}")
        for name, label, n_ops in concept_info:
            ops_tag = c(Colors.DIM, f"({n_ops})")
            print(f"  {c(Colors.GREEN, name):<24} {ops_tag}  {c(Colors.DIM, label[:54])}")
        print(f"  {c(Colors.DIM, 'Use: help -c <model>  ·  Full guide: docs/users/user-manual.md  ·  Quick ref: docs/users/cli-quick-reference.md')}")
    print()


def print_concepts_list(concept_info: "list[tuple[str,str,int]]"):
    """Render the full concept model index with labels and operator counts."""
    print(f"\n{c(Colors.CYAN, '─── Concept models ' + '─'*29)}")
    for name, label, n_ops in concept_info:
        ops_tag = c(Colors.DIM, f"{n_ops} ops")
        print(f"  {c(Colors.GREEN, name):<24} {ops_tag:<20} {label}")
    print(f"\n  {c(Colors.DIM, 'Use: help -c <model>  to see operators')}")
    print()


def print_concept_help(group: str, group_specs: dict, concept_names: "list[str]"):
    """Render all commands belonging to one concept model."""
    if not group_specs:
        available = "  ".join(concept_names)
        print(c(Colors.FAIL, f"\n  [!] Unknown concept model '{group}'"))
        print(f"  Available:  {available}\n")
        return
    title = group.title() + " operators"
    pad = max(0, 48 - len(title))
    print(f"\n{c(Colors.CYAN, '─── ' + title + ' ' + '─'*pad)}")
    for cmd, spec in group_specs.items():
        args_str = "  ".join(f"<{a}>" for a in spec.get("args", []))
        print(f"  {c(Colors.GREEN, cmd):<26} {args_str:<30} {spec.get('desc','')}")
    print()


def print_command_detail(cmd: str, spec: "dict | None", group: "str | None",
                         related: "list[str]"):
    """Render detailed help for a single command."""
    if spec is None:
        print(c(Colors.FAIL, f"\n  [!] Unknown command '{cmd}'"))
        print(f"  Try {c(Colors.GREEN, 'help')} for all commands, "
              f"or {c(Colors.GREEN, 'help -c <model>')} for concept operators.\n")
        return
    args = spec.get("args", [])
    usage = f"{cmd} " + " ".join(f"<{a}>" for a in args) if args else cmd
    pad = max(0, 52 - len(cmd))
    print(f"\n{c(Colors.CYAN, '─── ' + cmd + ' ' + '─'*pad)}")
    print(f"  {c(Colors.DIM, 'Usage  ')}  {c(Colors.GREEN, usage)}")
    if spec.get("desc"):
        print(f"  {c(Colors.DIM, 'About  ')}  {spec['desc']}")
    if spec.get("method"):
        print(f"  {c(Colors.DIM, 'Method ')}  {c(Colors.DIM, spec['method'])}")
    if group:
        print(f"  {c(Colors.DIM, 'Model  ')}  {group}"
              f"  {c(Colors.DIM, '→ help -c ' + group)}")
    if related:
        print(f"  {c(Colors.DIM, 'Related')}  {c(Colors.DIM, '  '.join(related[:10]))}")
    print()


def _render_thesaurus_atom_view(result: dict):
    atom  = result.get("atom", {})
    score = result.get("shelf_score", {})
    slinks = result.get("semantic_links", {})
    ext   = result.get("external_refs", [])
    curs  = result.get("curations", [])
    all_links = result.get("all_links", {})

    name  = atom.get("name") or atom.get("key", "?")[:14] + "…"
    total = score.get("shelf_score", 0.0)
    bar_w = 24
    filled = round(total * bar_w)
    bar = "█" * filled + "░" * (bar_w - filled)

    print(f"\n{c(Colors.CYAN, '─── ' + name + ' ' + '─'*max(0, 52-len(name)))}")
    desc = (atom.get("description") or "")[:200]
    if desc:
        print(f"  {c(Colors.DIM, desc)}")

    # All aliases
    aliases = atom.get("aliases", [])
    if aliases:
        alias_str = "  ".join(c(Colors.GREEN, f"@{a}") for a in aliases[:8])
        print(f"  {alias_str}")

    # Meta fields (skip display-redundant keys)
    _SKIP_META = {"type", "name", "role", "canonical", "auto_created"}
    meta = atom.get("meta") or {}
    meta_items = [(k, v) for k, v in meta.items() if k not in _SKIP_META and v is not None]
    if meta_items:
        for mk, mv in meta_items:
            print(f"  {c(Colors.DIM, mk + ':')}  {mv}")
    print()

    print(f"  ShelfScore  {c(Colors.GREEN, f'{total:.3f}')}  {bar}")
    comps = score.get("components", {})
    labels = {
        "synonym_coverage":  "synonyms    ",
        "antonym_presence":  "antonyms    ",
        "chain_balance":     "chain       ",
        "example_density":   "examples    ",
        "affective_score":   "affective   ",
        "namespace_bridges": "ns bridges  ",
        "external_refs":     "ext refs    ",
        "link_total":        "link total  ",
    }
    for k, lbl in labels.items():
        v = comps.get(k, 0.0)
        mini = round(v * 10)
        mini_bar = "▪" * mini + "·" * (10 - mini)
        print(f"    {c(Colors.DIM, lbl)} {mini_bar}  {v:.3f}")
    print()

    if ext:
        print(f"  {c(Colors.CYAN, 'External refs')}")
        for ref in ext:
            print(f"    ├─ {c(Colors.GREEN, ref.get('label','?'))}  {c(Colors.DIM, ref.get('url',''))}")
        print()

    for rel_key, label in [
        ("synonyms", "Synonyms"), ("near_synonyms", "Near synonyms"),
        ("antonyms", "Antonyms"), ("affective", "Affective"),
        ("namespace_bridges", "NS bridges"),
    ]:
        items = slinks.get(rel_key, [])
        if items:
            names = ", ".join(i.get("name") or i.get("key","?")[:12]+"…" for i in items[:5])
            print(f"  {c(Colors.DIM, label+':')}  {names}")
    if any(slinks.get(k) for k in ("synonyms","near_synonyms","antonyms","affective","namespace_bridges")):
        print()

    if curs:
        print(f"  {c(Colors.CYAN, 'Curations')}")
        for entry in curs:
            title = entry.get("collection_title") or entry.get("collection_id","?")[:16]+"…"
            pos   = entry.get("position")
            pos_s = f"  #{pos}" if pos is not None else ""
            interp = (entry.get("interpretation") or "")[:80]
            print(f"    [{c(Colors.GREEN, title)}{pos_s}]")
            if interp:
                print(f"    {c(Colors.DIM, interp)}")
        print()

    out_links = all_links.get("outgoing", [])
    in_links  = all_links.get("incoming", [])
    if out_links or in_links:
        print(f"  {c(Colors.CYAN, 'Graph Links')}")
        for lk in out_links[:12]:
            rel   = c(Colors.DIM, f"[{lk.get('rel','?')}]")
            lname = lk.get("name") or (lk.get("key","?"))[:16] + "…"
            print(f"    → {rel}  {lname}")
        for lk in in_links[:12]:
            rel   = c(Colors.DIM, f"[{lk.get('rel','?')}]")
            lname = lk.get("name") or (lk.get("key","?"))[:16] + "…"
            print(f"    ← {rel}  {lname}")
        print()


def _render_thesaurus_curation_view(result: dict):
    col  = result.get("collection", {})
    ways = result.get("waypoints", [])

    title = col.get("title", "?")
    alias = col.get("alias", "")
    cnt   = col.get("waypoint_count", len(ways))

    print(f"\n{c(Colors.CYAN, '══ ' + title + ' ' + '═'*max(0, 48-len(title)))}")
    if alias:
        print(f"  {c(Colors.DIM, alias)}   {cnt} waypoints")
    concept = col.get("concept")
    if concept:
        print(f"  concept: {c(Colors.GREEN, concept)}")
    print()

    for wp in ways:
        pos    = wp.get("position") or "·"
        interp = (wp.get("interpretation") or "")
        orig   = wp.get("original", {})
        oname  = orig.get("name") or orig.get("key","?")[:14]+"…"
        oscore = orig.get("shelf_score")
        ext    = orig.get("external_refs", [])

        score_s = f"  score={oscore:.3f}" if oscore is not None else ""
        print(f"  {c(Colors.GREEN, f'[{pos}]')} {c(Colors.CYAN, oname)}{c(Colors.DIM, score_s)}")

        if ext:
            ext_labels = " · ".join(e.get("label","?") for e in ext)
            print(f"       {c(Colors.DIM, '↗ ' + ext_labels)}")

        # Print interpretation, wrapping at ~70 chars
        for i in range(0, len(interp), 70):
            prefix = "       " if i > 0 else "     "
            print(f"{prefix}{c(Colors.DIM, interp[i:i+70])}")
        print()


def _render_thesaurus_series_view(result: dict):
    series  = result.get("series", {})
    current = result.get("current")
    archive = result.get("archive", [])

    title  = series.get("title", "?")
    slug   = series.get("url_slug") or series.get("slug", "")
    count  = series.get("exhibition_count", 0)

    print(f"\n{c(Colors.CYAN, '╔══ ' + title + ' ' + '═'*max(0, 44-len(title)))}")
    if slug:
        print(f"  {c(Colors.DIM, f'/series/{slug}')}   {count} exhibition{'s' if count != 1 else ''}")
    print()

    if current:
        ctitle  = current.get("title", "?")
        cslug   = current.get("url_slug", "")
        cwp     = current.get("waypoint_count", 0)
        cconcept = current.get("concept", "")
        print(f"  {c(Colors.GREEN, '▶ CURRENT')}  {c(Colors.CYAN, ctitle)}")
        if cslug:
            print(f"       {c(Colors.DIM, f'/exhibition/{cslug}')}   {cwp} waypoints")
        if cconcept:
            print(f"       concept: {c(Colors.DIM, cconcept)}")
        print()
    else:
        print(f"  {c(Colors.DIM, '(no exhibitions yet)')}")
        print()

    if archive:
        print(f"  {c(Colors.DIM, 'Archive')}")
        for entry in archive:
            pos    = entry.get("position", "·")
            atitle = entry.get("title", "?")
            aslug  = entry.get("url_slug", "")
            awp    = entry.get("waypoint_count", 0)
            print(f"  {c(Colors.DIM, f'[{pos}]')} {atitle}")
            if aslug:
                print(f"       {c(Colors.DIM, f'/exhibition/{aslug}')}   {awp} waypoints")
        print()
    else:
        print(f"  {c(Colors.DIM, 'Archive: (empty)')}")
        print()


# ---------------------------------------------------------------------------
# onto.* renderers
# ---------------------------------------------------------------------------

def _render_onto_pack_list(result: dict):
    packages = result.get("packages", [])
    enabled  = set(result.get("enabled", []))

    print(f"\n{c(Colors.CYAN, '─── Ontology Packages ' + '─'*30)}")

    for p in packages:
        name     = p.get("name", "?")
        autoload = p.get("autoload", False)
        loaded   = p.get("loaded")
        ena      = p.get("enabled") or autoload
        files    = p.get("ak_files", 0)
        label    = p.get("label", "")
        desc     = (p.get("description") or "")[:60]
        unreg    = p.get("unregistered", False)
        dot      = "●" if (ena or loaded) else "○"
        col      = Colors.GREEN if loaded else (Colors.CYAN if ena else Colors.DIM)
        parts    = []
        if autoload:
            parts.append(c(Colors.GREEN, "autoload"))
        elif ena:
            parts.append("enabled")
        if loaded:
            parts.append(c(Colors.GREEN, "loaded"))
        if unreg:
            parts.append(c(Colors.WARNING, "!registry"))
        status   = " ".join(parts) if parts else c(Colors.DIM, "—")
        print(f"  {dot} {c(col, name):<22} {status:<28} {files} files   {c(Colors.DIM, label)}")
        if desc:
            print(f"    {c(Colors.DIM, desc)}")

    print()


def _render_onto_status(result: dict):
    nucleus   = result.get("nucleus", {})
    registry  = result.get("registry", {})
    opt_packs = result.get("enabled_packs", [])
    sentinels = result.get("sentinels", {})

    print(f"\n{c(Colors.CYAN, '─── Ontology Status ' + '─'*32)}")

    atoms   = nucleus.get("atoms", 0)
    links   = nucleus.get("links", 0)
    aliases = nucleus.get("aliases", 0)
    print(f"\n  {c(Colors.DIM, 'Nucleus')}")
    print(f"    atoms:    {c(Colors.GREEN, f'{atoms:,}')}")
    print(f"    links:    {c(Colors.GREEN, f'{links:,}')}")
    print(f"    aliases:  {c(Colors.GREEN, f'{aliases:,}')}")

    reg_pkgs = registry.get("packages", [])
    if reg_pkgs:
        print(f"\n  {c(Colors.DIM, 'REGISTRY.json packages:')}")
        for p in reg_pkgs:
            dot    = "●" if p.get("exists") else c(Colors.WARNING, "○")
            label  = p.get("name", "?")
            fcount = p.get("file_count", 0)
            auto   = " (autoload)" if p.get("autoload") else ""
            print(f"    {dot} {label:<22} {fcount} files{auto}")

    if opt_packs:
        print(f"\n  {c(Colors.DIM, 'Enabled packs:')}  {', '.join(opt_packs)}")
    else:
        print(f"\n  {c(Colors.DIM, 'Enabled packs:  (none)')}")

    sent_count = sentinels.get("count", 0)
    sent_files = sentinels.get("files", [])
    print(f"\n  {c(Colors.DIM, 'Sentinels:')}  {sent_count}")
    for sf in sent_files[:8]:
        print(f"    · {c(Colors.DIM, sf)}")
    if len(sent_files) > 8:
        print(c(Colors.DIM, f"    … and {len(sent_files)-8} more"))
    print()


def _render_onto_dump(result: dict):
    mode  = result.get("mode", "atoms")
    count = result.get("count", 0)
    items = result.get("items", [])
    coll  = result.get("collection", "")

    extra  = f"  [{coll}]" if coll else ""
    header = f"─── Dump: {mode}{extra} ({count:,} total) "
    print(f"\n{c(Colors.CYAN, header + '─'*max(0, 52-len(header)))}")

    if not items:
        print(c(Colors.DIM, "  (empty)"))
        print()
        return

    if mode == "namespaces":
        print(c(Colors.DIM, f"\n  {'namespace':<28} count"))
        print(c(Colors.DIM, "  " + "─" * 36))
        for it in items:
            ns  = it.get("ns", "?")
            cnt = it.get("count", 0)
            print(f"  {c(Colors.CYAN, ns):<36} {cnt}")

    elif mode in ("links", "antonyms"):
        print(c(Colors.DIM, f"\n  {'src':<22} {'rel':<28} dst"))
        print(c(Colors.DIM, "  " + "─" * 72))
        for it in items[:120]:
            src = (it.get("src") or "")[:20]
            rel = (it.get("rel") or "")[:26]
            dst = (it.get("dst") or "")[:24]
            print(f"  {c(Colors.CYAN, src):<30} {c(Colors.DIM, rel):<34} {dst}")
        if len(items) > 120:
            print(c(Colors.DIM, f"  … {len(items)-120} more"))

    elif mode in ("sets", "aliases"):
        print(c(Colors.DIM, f"\n  {'alias':<28} key"))
        print(c(Colors.DIM, "  " + "─" * 50))
        for it in items[:200]:
            alias = (it.get("alias") or "")[:26]
            key   = it.get("key", "")
            print(f"  {c(Colors.GREEN, alias):<36} {c(Colors.DIM, key)}")
        if len(items) > 200:
            print(c(Colors.DIM, f"  … {len(items)-200} more"))

    else:
        print(c(Colors.DIM, f"\n  {'alias':<24} {'key':<14} preview"))
        print(c(Colors.DIM, "  " + "─" * 72))
        for it in items[:200]:
            alias   = (it.get("alias") or "")[:22]
            key     = (it.get("key") or "")[:12]
            preview = (it.get("preview") or "")[:48]
            print(f"  {c(Colors.GREEN, alias):<32} {c(Colors.DIM, key):<20} {preview}")
        if len(items) > 200:
            print(c(Colors.DIM, f"  … {len(items)-200} more"))

    print()


def _render_onto_export(result: dict):
    exported = result.get("exported", 0)
    files    = result.get("files", [])
    out_dir  = result.get("out_dir", "out/")
    note     = result.get("note", "")

    if note or not exported:
        msg = note or "No atoms matched — nothing exported"
        print(c(Colors.DIM, f"\n  {msg}"))
        print()
        return

    noun = "atom" if exported == 1 else "atoms"
    print(f"\n  {c(Colors.GREEN, f'✓ Exported {exported} {noun}')}  →  {c(Colors.CYAN, out_dir)}\n")
    for f in files:
        fname  = f.get("file", "?")
        natoms = f.get("atoms", 0)
        print(f"  {c(Colors.DIM, fname):<44} {natoms} atoms")
    print()


def _render_onto_pack_status(result: dict):
    status   = result.get("status", "?")
    pack     = result.get("pack", "?")
    message  = result.get("message", "")
    location = result.get("location", "")

    col = Colors.GREEN if status == "enabled" else Colors.DIM
    print(f"\n  {c(col, f'✓ {pack}  {status}')}")
    if location:
        print(f"  {c(Colors.DIM, location)}")
    if message:
        print(f"  {c(Colors.DIM, message)}")
    print()


def _render_onto_reload_reset(result: dict):
    status  = result.get("status", "?")
    message = result.get("message", "")

    if status == "reload_triggered":
        removed = result.get("sentinel_files_removed", 0)
        cleared = result.get("sentinels_cleared", [])
        print(f"\n  {c(Colors.GREEN, '✓ Reload triggered')}")
        if removed:
            noun = "file" if removed == 1 else "files"
            print(f"  {c(Colors.DIM, f'{removed} sentinel {noun} cleared')}")
        if cleared:
            print(f"  {c(Colors.DIM, 'Sentinels removed: ' + ', '.join(cleared[:6]))}")
    elif status == "reset_complete":
        preserved = result.get("dna_atoms_preserved", 0)
        print(f"\n  {c(Colors.GREEN, '✓ Reset complete')}")
        if preserved:
            print(f"  {c(Colors.DIM, f'{preserved} DNA atoms preserved')}")
    else:
        print(f"\n  {c(Colors.DIM, f'✓ {status}')}")

    if message:
        print(f"  {c(Colors.DIM, message)}")
    print()


# ── TextViewConcept renderers ─────────────────────────────────────────────────

def _render_textview(result: dict):
    """Dispatch a textview result to the appropriate typed renderer."""
    vtype = result.get("_view")
    if   vtype == "table":   _render_tv_table(result)
    elif vtype == "tree":    _render_tv_tree(result)
    elif vtype == "list":    _render_tv_list(result)
    elif vtype == "keyval":  _render_tv_keyval(result)
    elif vtype == "chart":   _render_tv_chart(result)
    elif vtype == "scatter": _render_tv_scatter(result)
    elif vtype == "heatmap": _render_tv_heatmap(result)
    else:
        # Unknown view type: fall back to raw JSON
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))


def _render_tv_table(result: dict):
    """Render a textview:table — title + rich table."""
    title   = result.get("title", "")
    columns = result.get("columns", [])
    rows    = result.get("rows", [])
    count   = result.get("count", len(rows))
    if title:
        print(c(Colors.DIM, f"\n  {title}  ({count})"))
    _render_table(columns, rows)


def _render_tv_tree(result: dict):
    """Render a textview:tree — rich (default) or ASCII fallback."""
    fmt = result.get("format", "rich")
    if fmt == "ascii":
        _render_tv_tree_ascii(result)
        return

    import sys
    import shutil
    from rich.console import Console
    from rich.tree import Tree

    title    = result.get("title", "")
    root_lbl = result.get("root", title)
    children = result.get("children", [])

    tree = Tree(f"[bold cyan]{root_lbl}[/bold cyan]"
                + (f"  [dim]{title}[/dim]" if title and title != root_lbl else ""))

    def _add(node, items):
        for ch in items:
            label    = str(ch.get("label", ""))
            sublabel = ch.get("sublabel", "")
            full     = f"[cyan]{label}[/cyan]  [dim]{sublabel}[/dim]" if sublabel else f"[cyan]{label}[/cyan]"
            child    = node.add(full)
            if ch.get("children"):
                _add(child, ch["children"])

    _add(tree, children)

    width = shutil.get_terminal_size(fallback=(100, 24)).columns
    con   = Console(file=sys.stdout, force_terminal=True, highlight=False, width=width)
    print()
    con.print(tree)
    print()


def _render_tv_tree_ascii(result: dict):
    """ASCII fallback for textview:tree — pure line-drawing, no dependencies."""
    title    = result.get("title", "")
    root_lbl = result.get("root", title)
    children = result.get("children", [])

    print(f"\n  {c(Colors.CYAN, root_lbl)}"
          + (f"  {c(Colors.DIM, title)}" if title and title != root_lbl else ""))

    def _draw(items, prefix=""):
        for i, ch in enumerate(items):
            is_last  = (i == len(items) - 1)
            conn     = "└─" if is_last else "├─"
            label    = str(ch.get("label", ""))
            sublabel = ch.get("sublabel", "")
            sub_str  = f"  {c(Colors.DIM, sublabel)}" if sublabel else ""
            print(f"  {prefix}{conn} {c(Colors.CYAN, label)}{sub_str}")
            if ch.get("children"):
                ext = "   " if is_last else "│  "
                _draw(ch["children"], prefix + ext)

    _draw(children)
    print()


def _render_tv_list(result: dict):
    """Render a textview:list — flat items with optional meta and detail."""
    title = result.get("title", "")
    items = result.get("items", [])
    if title:
        print(c(Colors.DIM, f"\n  {title}\n"))
    else:
        print()
    for it in items:
        label  = str(it.get("label", ""))
        meta   = str(it.get("meta", ""))
        detail = str(it.get("detail", ""))
        meta_s = f"  {c(Colors.DIM, meta)}" if meta else ""
        print(f"  {label}{meta_s}")
        if detail:
            print(f"    {c(Colors.DIM, detail)}")
    print()


def _render_tv_keyval(result: dict):
    """Render a textview:keyval — two-column key-value list."""
    title = result.get("title", "")
    pairs = result.get("pairs", [])
    if title:
        print(c(Colors.DIM, f"\n  {title}\n"))
    else:
        print()
    for pair in pairs:
        if isinstance(pair, (list, tuple)):
            k, v = (str(pair[0]), str(pair[1])) if len(pair) >= 2 else (str(pair[0]), "")
        else:
            k, v = str(pair.get("key", "")), str(pair.get("val", ""))
        print(f"  {c(Colors.CYAN, k):<26}  {v}")
    print()


_SPARK_BLOCKS = "▁▂▃▄▅▆▇█"

def _render_tv_chart(result: dict):
    """Render a textview:chart — Unicode sparkline or horizontal bar chart."""
    title      = result.get("title", "")
    series     = result.get("series", [])
    labels     = result.get("labels", [])
    chart_type = result.get("type", "sparkline")

    if not series:
        print(c(Colors.DIM, "  (no data)\n"))
        return

    mn, mx = min(series), max(series)
    rng    = mx - mn or 1

    if title:
        print(c(Colors.DIM, f"\n  {title}"))

    if chart_type == "bar":
        # Horizontal bar chart
        max_bar = 40
        print()
        for i, val in enumerate(series):
            label    = labels[i] if i < len(labels) else str(i)
            bar_len  = int((val - mn) / rng * max_bar)
            bar      = c(Colors.CYAN, "█" * bar_len)
            val_str  = f"{val:.4g}"
            print(f"  {c(Colors.DIM, label[:16]):<18}  {bar}  {c(Colors.DIM, val_str)}")
    else:
        # Sparkline (default)
        spark = "".join(_SPARK_BLOCKS[int((v - mn) / rng * 7)] for v in series)
        print(f"\n  {c(Colors.CYAN, spark)}")
        if labels:
            first, last = labels[0][:12], labels[-1][:12]
            pad = max(0, len(series) - len(first) - len(last))
            print(f"  {c(Colors.DIM, first + ' ' * pad + last)}")
        print(f"  {c(Colors.DIM, f'min {mn:.4g}   max {mx:.4g}')}")

    print()


def _render_tv_scatter(result: dict):
    """Render a textview:scatter — ASCII 4-quadrant scatter plot.

    Grid is 48 × 12 characters.  Quadrant dividers use box-drawing dashes.
    Point labels are placed inline to the right of each row when unambiguous;
    a numbered legend is shown below when multiple points share a grid row.
    """
    GRID_W = 48
    GRID_H = 12

    points          = result.get("points", [])
    x_label         = result.get("x_label", "x")
    y_label         = result.get("y_label", "y")
    x_mid_arg       = result.get("x_mid")
    y_mid_arg       = result.get("y_mid")
    title           = result.get("title", "")
    quadrant_labels = result.get("quadrant_labels", {})

    if not points:
        print(c(Colors.DIM, "  (no points)\n"))
        return

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    # 12 % padding so edge points are not on the axis line
    x_pad = (x_max - x_min) * 0.12 or 0.1
    y_pad = (y_max - y_min) * 0.12 or 0.1
    x_min -= x_pad;  x_max += x_pad
    y_min -= y_pad;  y_max += y_pad
    x_rng = x_max - x_min
    y_rng = y_max - y_min

    x_mid = x_mid_arg if x_mid_arg is not None else (min(xs) + max(xs)) / 2
    y_mid = y_mid_arg if y_mid_arg is not None else (min(ys) + max(ys)) / 2

    def _col(x): return max(0, min(GRID_W - 1, round((x - x_min) / x_rng * (GRID_W - 1))))
    def _row(y): return max(0, min(GRID_H - 1, round((y_max - y) / y_rng * (GRID_H - 1))))

    mid_col = _col(x_mid)
    mid_row = _row(y_mid)

    # Build grid
    grid = [[" "] * GRID_W for _ in range(GRID_H)]

    # Quadrant dividers
    for r in range(GRID_H):
        if grid[r][mid_col] == " ":
            grid[r][mid_col] = "┆"
    for cc in range(GRID_W):
        if grid[mid_row][cc] == " ":
            grid[mid_row][cc] = "╌"
    grid[mid_row][mid_col] = "┼"

    # Place points; detect row collisions
    point_rows: dict = {}
    for pt in points:
        r  = _row(pt["y"])
        cc = _col(pt["x"])
        grid[r][cc] = "●"
        point_rows.setdefault(r, []).append((cc, pt["label"]))

    need_legend = any(len(v) > 1 for v in point_rows.values())

    # Swap ● for index number when legend is needed
    if need_legend:
        for i, pt in enumerate(points, 1):
            r  = _row(pt["y"])
            cc = _col(pt["x"])
            grid[r][cc] = str(i) if i <= 9 else "+"

    # ── print ────────────────────────────────────────────────────────────────
    if title:
        print(c(Colors.DIM, f"\n  {title}"))

    # Optional quadrant corner annotations (placed before the grid)
    if quadrant_labels:
        q2 = quadrant_labels.get("q2", "")  # top-left
        q1 = quadrant_labels.get("q1", "")  # top-right
        pad = max(0, mid_col - len(q2))
        right_pad = max(0, GRID_W - mid_col - 1 - len(q1))
        print(f"  {' ' * 6}{c(Colors.DIM, q2)}{' ' * pad}┆{c(Colors.DIM, q1)}{' ' * right_pad}")

    print(f"\n  {c(Colors.DIM, y_label)} ↑")

    for r in range(GRID_H):
        sep = "┼" if r == mid_row else "┤"

        # Y-axis tick (top, mid, bottom)
        if r == 0:
            y_str = f"{y_max:5.2f}"
        elif r == mid_row:
            y_str = f"{y_mid:5.2f}"
        elif r == GRID_H - 1:
            y_str = f"{y_min:5.2f}"
        else:
            y_str = "     "

        row_str = "".join(grid[r])

        # Inline labels when no conflict in this row
        suffix = ""
        if not need_legend and r in point_rows:
            lbls = [lbl[:18] for _, lbl in sorted(point_rows[r])]
            suffix = "  " + "  ".join(c(Colors.DIM, lbl) for lbl in lbls)

        print(f"  {c(Colors.DIM, y_str)} {c(Colors.DIM, sep)}{row_str}{suffix}")

    # Bottom quadrant corner annotations
    if quadrant_labels:
        q3 = quadrant_labels.get("q3", "")   # bottom-left
        q4 = quadrant_labels.get("q4", "")   # bottom-right
        pad = max(0, mid_col - len(q3))
        right_pad = max(0, GRID_W - mid_col - 1 - len(q4))
        print(f"  {' ' * 6}{c(Colors.DIM, q3)}{' ' * pad}┆{c(Colors.DIM, q4)}{' ' * right_pad}")

    # X axis line + tick labels
    print(f"  {' ' * 6}└{'─' * GRID_W}")

    left_lbl  = f"{x_min:.2f}"
    mid_lbl   = f"{x_mid:.2f}"
    right_lbl = f"{x_max:.2f}"
    mid_gap   = max(0, mid_col - len(left_lbl) - 1)
    right_gap = max(0, GRID_W - mid_col - len(mid_lbl) - len(right_lbl))
    x_tick_line = left_lbl + " " * mid_gap + mid_lbl + " " * right_gap + right_lbl
    print(f"  {' ' * 7}{c(Colors.DIM, x_tick_line)}")
    print(f"  {' ' * 7}{c(Colors.DIM, x_label)} →")

    # Numbered legend
    if need_legend:
        print()
        cols = 2
        items = [f"{c(Colors.DIM, str(i) + '.')}  {pt['label']}" for i, pt in enumerate(points, 1)]
        for j in range(0, len(items), cols):
            row_items = items[j:j + cols]
            print("  " + "   ".join(f"{it:<36}" for it in row_items))

    print()


def _render_tv_heatmap(result: dict):
    """Render a textview:heatmap — 2-D intensity grid using Unicode block chars.

    matrix[row][col]: row 0 = highest y bin; values normalised 0.0–1.0.
    Cells are 2 chars wide; 5-level intensity: '  ' · '░░' · '▒▒' · '▓▓' · '██'.
    """
    _HEAT = ["  ", "░░", "▒▒", "▓▓", "██"]   # 5 intensity levels

    title       = result.get("title", "")
    matrix      = result.get("matrix", [])
    x_labels    = result.get("x_labels", [])
    y_labels    = result.get("y_labels", [])
    x_attr      = result.get("x_attr", "x")
    y_attr      = result.get("y_attr", "y")
    value_label = result.get("value_label", "count")

    if not matrix or not matrix[0]:
        print(c(Colors.DIM, "  (no data)\n"))
        return

    n_rows = len(matrix)
    n_cols = len(matrix[0])

    def _cell(v: float) -> str:
        return _HEAT[min(4, int(v * 5))]

    if title:
        print(c(Colors.DIM, f"\n  {title}"))

    print(f"\n  {c(Colors.DIM, y_attr)} ↑")

    Y_LABEL_W = 7   # chars reserved for y-axis tick label

    for r in range(n_rows):
        # Y tick: top, middle, bottom rows only
        if r == 0:
            y_str = f"{y_labels[0][:Y_LABEL_W - 1]:>{Y_LABEL_W - 1}}" if y_labels else " " * (Y_LABEL_W - 1)
        elif r == n_rows // 2:
            mid_lbl = y_labels[n_rows // 2] if n_rows // 2 < len(y_labels) else ""
            y_str = f"{mid_lbl[:Y_LABEL_W - 1]:>{Y_LABEL_W - 1}}"
        elif r == n_rows - 1:
            y_str = f"{y_labels[-1][:Y_LABEL_W - 1]:>{Y_LABEL_W - 1}}" if y_labels else " " * (Y_LABEL_W - 1)
        else:
            y_str = " " * (Y_LABEL_W - 1)

        row_str = "".join(_cell(matrix[r][cc]) for cc in range(n_cols))
        print(f"  {c(Colors.DIM, y_str)} │{row_str}│")

    # X axis line
    bar_w = n_cols * 2
    print(f"  {' ' * Y_LABEL_W}└{'─' * bar_w}┘")

    # X tick labels: first, middle, last — placed on a fixed-width char array
    if x_labels:
        buf = [" "] * bar_w
        def _place(label: str, pos: int):
            for i, ch in enumerate(label):
                p = pos + i
                if 0 <= p < bar_w:
                    buf[p] = ch
        _place(x_labels[0],  0)
        _place(x_labels[-1], bar_w - len(x_labels[-1]))
        mid_col = (n_cols // 2) * 2
        mid_lbl = x_labels[n_cols // 2] if n_cols // 2 < len(x_labels) else ""
        _place(mid_lbl, max(0, mid_col - len(mid_lbl) // 2))
        print(f"  {' ' * (Y_LABEL_W + 1)}{c(Colors.DIM, ''.join(buf))}")

    print(f"  {' ' * (Y_LABEL_W + 1)}{c(Colors.DIM, x_attr)} →")
    print(f"  {c(Colors.DIM, f'intensity = {value_label}   ░░ low · ▒▒ · ▓▓ · ██ high')}")
    print()
