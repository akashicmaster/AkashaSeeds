#!/usr/bin/env python3
"""
Invariant checker — loose coupling, security, single-route-to-core, and junk.

A lightweight standing guard against regression. It does NOT replace the .ak
regression suite (test_00..07); it verifies the *structural* invariants those
tests cannot see: that the write path still funnels through one guarded route,
that no new back-door into the core has appeared, that the security anchors are
still in place, and that no regression-inducing junk was left behind.

Run it after any change that touches the write path, auth/scope, the WriteQueue/
JCL, or a backend:

    python test/check_invariants.py

Exit code 0 = all hard invariants hold. Non-zero = a hard invariant broke.
REVIEW lines (new core-write callsites) are warnings, not failures — they mean
"a human should confirm this new route to the core is legitimately guarded."

Four groups:
  A. Static anchors      — required guard/security code must be present.
  B. Route proliferation — AST scan of raw core-write callsites vs a reviewed
                           baseline; new callsites are flagged for review.
  C. Junk detection      — leftover TODO/FIXME, references to removed symbols,
                           stray debug prints in shipped lib code.
  D. Runtime guard       — boot a kernel and prove the guard actually fires.
"""
import ast
import os
import re
import sys
import tempfile
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fail = []   # hard invariant violations
_warn = []   # review-only (route proliferation, soft)
_ok = []


def ok(msg):
    _ok.append(msg)


def fail(msg):
    _fail.append(msg)


def warn(msg):
    _warn.append(msg)


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _call_within(src, def_pat, call_pat, window=15):
    """True if a line matching call_pat appears within `window` lines after a line
    matching def_pat. Line-based (no DOTALL) so it cannot catastrophically backtrack
    on large files. Used to assert `def X(): ... calls Y()` without a monster regex."""
    lines = src.splitlines()
    d = re.compile(def_pat)
    c = re.compile(call_pat)
    for i, line in enumerate(lines):
        if d.search(line):
            for j in range(i, min(i + window + 1, len(lines))):
                if c.search(lines[j]):
                    return True
    return False


# ── A. Static anchors — required guard/security code must be present ─────────

def check_static_anchors():
    # Two def→call proximity checks (line-windowed, backtracking-safe).
    if _call_within(_read("lib/akasha/composite.py"),
                    r"def commit\(", r"_workspace_guard\("):
        ok("[A] commit calls _workspace_guard")
    else:
        fail("[A] commit calls _workspace_guard: guard NOT found near def commit "
             "(single-route guard may have regressed)")
    if _call_within(_read("lib/akasha/composite.py"),
                    r"def put_link\(", r"_workspace_guard\("):
        ok("[A] put_link calls _workspace_guard")
    else:
        fail("[A] put_link calls _workspace_guard: guard NOT found near def put_link "
             "(single-route guard may have regressed)")

    # (file, human-name, plain regex that MUST match somewhere in the file)
    required = [
        # Guard is in ENFORCE (reject) mode, not observe.
        ("lib/akasha/jcl/workspace_context.py", "guard ENFORCE=True",
         r"^ENFORCE\s*=\s*True\b"),
        ("lib/akasha/jcl/workspace_context.py", "guard raises outside workspace",
         r"raise PermissionError\("),
        # ws:/wf: reserved-prefix rejection on every add_to_set (all 3 engines).
        ("lib/akasha/composite.py", "ws:/wf: reserved in add_to_set (x3)",
         r'startswith\("ws:"\)\s+or\s+name\.startswith\("wf:"\)'),
        # Transport trust is a server-set enum, network is the safe default.
        ("lib/akasha/kernel.py", "transport trust constants",
         r'TRUST_NETWORK\s*=\s*"network"'),
        ("lib/akasha/kernel.py", "trusted transports frozenset",
         r"_TRUSTED_TRANSPORTS\s*=\s*frozenset"),
        ("lib/akasha/kernel.py", "_WRITE_ACTIONS gate",
         r"_WRITE_ACTIONS\s*=\s*frozenset"),
        ("lib/akasha/kernel.py", "genesis_rite is local/internal only",
         r"genesis_rite must be performed from the local console"),
        ("lib/akasha/kernel.py", "system identity gated off network",
         r"is_system_identity\(client_id\)\s+and\s+transport_trust\s*!=\s*TRUST_INTERNAL"),
        # Credential hardening.
        ("lib/akasha/identity.py", "PBKDF2 password KDF",
         r"pbkdf2_hmac\("),
        ("lib/akasha/identity.py", "constant-time compare",
         r"hmac\.compare_digest\("),
        ("lib/akasha/identity.py", "token_epoch revocation",
         r"token_epoch"),
        # JCL hardening: bounded, transient-only retry.
        ("lib/akasha/jcl/worker.py", "retry ceiling bound",
         r"_MAX_RETRIES_CEILING\s*=\s*8\b"),
        ("lib/akasha/jcl/worker.py", "non-retryable (deterministic) codes",
         r"_NON_RETRYABLE_CODES\s*=\s*frozenset"),
        # WriteQueue is a single-worker priority queue (order, not parallelism).
        ("lib/akasha/jcl/write_queue.py", "PriorityQueue serialiser",
         r"PriorityQueue"),
    ]
    for rel, name, pat in required:
        try:
            src = _read(rel)
        except FileNotFoundError:
            fail(f"[A] {name}: file missing: {rel}")
            continue
        if re.search(pat, src, re.MULTILINE | re.DOTALL):
            ok(f"[A] {name}")
        else:
            fail(f"[A] {name}: anchor NOT found in {rel} (invariant may have regressed)")


# ── B. Route proliferation — AST scan of raw core-write callsites ────────────
# The single-route rule: every graph write reaches the core through the composite
# engine's guarded methods (or an explicit system_context exemption). A brand-new
# function that calls a raw core-write primitive is a *new route to the core* and
# must be reviewed to confirm it is guarded. This baseline is the reviewed set as
# of the last audit; additions surface as REVIEW warnings, removals as info.

_RAW_WRITES = {
    "put_chunk_raw", "put_link_raw", "add_to_collection", "put_alias",
    "put_chunk_access", "upsert_collection_def", "clear_collection",
    "delete_chunk", "remove_from_collection", "del_alias", "delete_alias",
    "merge_collection_def_meta",
}

# Reviewed baseline: "module::Class::function" allowed to call raw core writes.
_BASELINE_ROUTES = {
    "akasha.backends.sqlite::SQLiteBackend::merge_collection_def_meta",
    "akasha.composite::AkashaEngine::_ensure_protoword",
    "akasha.composite::AkashaEngine::_link_instance_to_universals",
    "akasha.composite::AkashaEngine::_weave_pending_links",
    "akasha.composite::AkashaEngine::add_to_set",
    "akasha.composite::AkashaEngine::clear_set",
    "akasha.composite::AkashaEngine::commit",
    "akasha.composite::AkashaEngine::create_donation_set",
    "akasha.composite::AkashaEngine::delete_alias",
    "akasha.composite::AkashaEngine::explore",
    "akasha.composite::AkashaEngine::put_link",
    "akasha.composite::AkashaEngine::put_virtual_node",
    "akasha.composite::AkashaEngine::reassign_scopes",
    "akasha.composite::AkashaEngine::remove_from_set",
    "akasha.composite::AkashaEngine::set_alias",
    "akasha.composite::AkashaEngine::set_map",
    "akasha.composite::AkashaEngine::set_operation",
    "akasha.composite::AkashaEngine::update_donation_set_meta",
    "akasha.composite::GroupEngine::add_to_set",
    "akasha.composite::GroupEngine::put_atom",
    "akasha.composite::GroupEngine::put_link",
    "akasha.composite::GroupEngine::upsert_set_meta",
    "akasha.composite::NucleusEngine::_ensure_lemma_protoword",
    "akasha.composite::NucleusEngine::_ensure_protoword",
    "akasha.composite::NucleusEngine::_resolve_pending_links_for_alias",
    "akasha.composite::NucleusEngine::add_to_set",
    "akasha.composite::NucleusEngine::put_atom",
    "akasha.composite::NucleusEngine::put_link",
    "akasha.composite::NucleusEngine::set_alias",
    "akasha.composite::NucleusEngine::upsert_set_meta",
    "akasha.concepts.cast::CastConcept::op_publish",
    "akasha.concepts.table::TableConcept::op_new",
    "akasha.kernel::KernelDispatcher::_handle_alias_rm",
    "akasha.kernel::KernelDispatcher::_handle_dont_add",
    "akasha.kernel::KernelDispatcher::_handle_dont_send",
    "akasha.kernel::KernelDispatcher::_handle_onto_reload",
    "akasha.kernel::KernelDispatcher::_handle_workflow_rm",
    # IDLE background bake of learned semantic_vector onto nucleus atoms. Writes to
    # the nucleus PURE store (same path as NucleusEngine.put_atom) via @_queued
    # put_chunk_raw — WriteQueue-serialised, crash-safe, meta-only enrichment
    # (re-derivable). System-owned, no user write path. Confirmed exempt.
    "akasha.kernel::KernelDispatcher::_schedule_semantic_learn::_run",
    "akasha.ref_primitives::bootstrap_ref_primitives",
    "harmonia.engine::HarmoniaEngine::commit_workspace",
    "harmonia.engine::HarmoniaEngine::reconcile_orphan_workspaces",
    "harmonia.engine::HarmoniaEngine::rollback_workspace",
}


def _scan_routes(path):
    with open(path, encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=path)
        except SyntaxError:
            return set()
    found = set()

    class V(ast.NodeVisitor):
        def __init__(self):
            self.stack = []

        def visit_FunctionDef(self, n):
            self.stack.append(n.name)
            self.generic_visit(n)
            self.stack.pop()
        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, n):
            self.stack.append(n.name)
            self.generic_visit(n)
            self.stack.pop()

        def visit_Call(self, n):
            fn = n.func
            if isinstance(fn, ast.Attribute) and fn.attr in _RAW_WRITES:
                found.add("::".join(self.stack) or "<module>")
            self.generic_visit(n)

    V().visit(tree)
    return found


def check_route_proliferation():
    current = set()
    for dirpath, _, files in os.walk(os.path.join(ROOT, "lib")):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            mod = os.path.relpath(p, os.path.join(ROOT, "lib"))[:-3].replace(os.sep, ".")
            for ctx in _scan_routes(p):
                current.add(f"{mod}::{ctx}")

    new_routes = current - _BASELINE_ROUTES
    gone_routes = _BASELINE_ROUTES - current

    if not new_routes:
        ok(f"[B] no new routes to core ({len(current)} reviewed callsites)")
    for r in sorted(new_routes):
        warn(f"[B] NEW route to core — confirm it is guarded / system-exempt: {r}")
    for r in sorted(gone_routes):
        ok(f"[B] route removed (baseline can be trimmed): {r}")


# ── B2. Concept models dispatch through the ONE registry path (issue #50) ────

def check_concept_one_path():
    """#50 Stage 2: every registry-discovered concept model dispatches through the ONE
    concept registry. A hand-wired `if method == "<prefix>."` handler in kernel.py would be
    a SECOND dispatch path shadowing the registry (the anti-pattern that note/fieldnote/
    survey used to embody) — outside core/composite, a concept operation must live in its
    plugin, not be hardcoded in the kernel."""
    try:
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        from lib.akasha.concepts.registry import ConceptRegistry
        reg = ConceptRegistry()
        reg.discover(os.path.join(ROOT, "lib", "akasha", "concepts"),
                     module_prefix="lib.akasha.concepts")
        reg.discover(os.path.join(ROOT, "lib", "akasha", "session"),
                     module_prefix="lib.akasha.session")
    except Exception as exc:
        warn(f"[B2] could not load concept registry ({exc}) — one-path check skipped")
        return
    prefixes = set(p.rstrip(".") for p in reg.get_concept_prefixes())
    kernel_src = _read("lib/akasha/kernel.py")
    dispatched = set(re.findall(r'if method == "([a-z_]+)\.', kernel_src))
    clash = sorted(prefixes & dispatched)
    if clash:
        for pfx in clash:
            fail(f"[B2] concept model '{pfx}' has a hand-wired kernel handler — it must "
                 f"dispatch through the registry, not a shadowing `if method ==` (issue #50)")
    else:
        ok(f"[B2] all {len(prefixes)} concept models dispatch through the ONE registry "
           f"(no shadowing kernel handler)")


# ── C. Junk detection — regression-inducing residue in shipped lib code ──────

def check_junk():
    # Symbols that were deliberately removed; a live *identifier* use is a ghost.
    # Match attribute access / assignment only — NOT prose that mentions the name
    # (e.g. a design comment "no `ontology_loading` flag" is correct and desirable).
    removed_symbols = [
        # ontology_loading flag was removed when the single-route guard landed.
        (r"\.ontology_loading\b|\bontology_loading\s*=",
         "removed flag 'ontology_loading' still used as an identifier"),
    ]
    # Markers that should not ship in lib/ (docs/tests may keep TODOs).
    marker_re = re.compile(r"#\s*(TODO|FIXME|XXX|HACK)\b")

    lib_files = []
    for dirpath, _, files in os.walk(os.path.join(ROOT, "lib")):
        for fn in files:
            if fn.endswith(".py"):
                lib_files.append(os.path.join(dirpath, fn))

    ghost = 0
    markers = 0
    for p in lib_files:
        rel = os.path.relpath(p, ROOT)
        src = _read(rel)
        for pat, desc in removed_symbols:
            if re.search(pat, src):
                fail(f"[C] {desc} in {rel}")
                ghost += 1
        for m in marker_re.finditer(src):
            warn(f"[C] leftover {m.group(1)} marker in {rel}")
            markers += 1
    if ghost == 0:
        ok("[C] no ghost identifiers for removed symbols in lib/")
    if markers == 0:
        ok("[C] no TODO/FIXME/XXX/HACK markers in lib/")


# ── D. Runtime guard — boot a kernel and prove the guard actually fires ──────

def check_runtime():
    os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
    try:
        from lib.akasha.kernel import KernelDispatcher
        from lib.akasha.jcl.workspace_context import system_context
    except Exception as e:  # pragma: no cover
        fail(f"[D] cannot import kernel: {e!r}")
        return

    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="akasha_inv_")
    k = KernelDispatcher(series="seeds", base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(method, data, trust="local"):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": "admin", "data": data},
                           "id": "t"}, trust)

    # R1: a raw composite write with NO workspace on this thread must be rejected.
    try:
        engine = k.manager.get_session("admin").local_cortex
    except Exception as e:
        fail(f"[D] cannot obtain admin cortex: {e!r}")
        return
    try:
        engine.commit("invariant-probe-unguarded", author="probe")
        fail("[D] R1 single-route guard: unguarded commit SUCCEEDED (guard bypassed!)")
    except PermissionError:
        ok("[D] R1 single-route guard: unguarded commit correctly rejected")
    except Exception as e:
        fail(f"[D] R1 single-route guard: unexpected error {e!r}")

    # R2: the same write inside system_context() is exempt and succeeds.
    try:
        with system_context():
            engine.commit("invariant-probe-system-exempt", author="probe")
        ok("[D] R2 system_context exemption: system write permitted")
    except Exception as e:
        fail(f"[D] R2 system_context exemption: system write raised {e!r}")

    # R3: ws:/wf: reserved prefixes rejected on the user set.add path.
    for pfx in ("ws:probe", "wf:probe"):
        r = d("set.add", {"name": pfx, "id": "deadbeef"})
        if "error" in r and "reserved" in str(r["error"]).lower():
            ok(f"[D] R3 reserved-prefix rejected: {pfx}")
        else:
            fail(f"[D] R3 reserved-prefix NOT rejected: {pfx} -> {str(r)[:80]}")

    # R4: genesis_rite over TRUST_NETWORK is refused (no network admin land-grab).
    r = k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                    "params": {"session_token": "x",
                               "data": {"user_name": "attacker",
                                        "passphrase": hashlib.sha256(b"x").hexdigest()}},
                    "id": "n"}, "network")
    if "error" in r and "local console" in str(r["error"]).lower():
        ok("[D] R4 genesis_rite over network refused")
    else:
        fail(f"[D] R4 genesis_rite over network NOT refused: {str(r)[:100]}")


def check_set_membership_orphans():
    """Every `set.add ... id=X` across the ontology must reference an atom that is
    actually defined (by `def` or `al`) SOMEWHERE in the ontology — even in another
    pack. A cross-pack orphan (base1 adding a base2 atom) silently loses the
    membership at load time, so it must never ship. Static, pack-agnostic scan.
    """
    import glob
    ont = os.path.join(ROOT, "ontology")
    if not os.path.isdir(ont):
        return
    defined = set()          # ids created by def / alias, anywhere
    set_adds = []            # (id, file) for every set.add
    def_re = re.compile(r'^def\s+"([^"]+)"')
    al_re  = re.compile(r'^al\s+(\S+)\s+(\S+)')
    sa_re  = re.compile(r'^set\.add\s+.*\bid="([^"]+)"')
    for fp in glob.glob(os.path.join(ont, "**", "*.ak"), recursive=True):
        rel = os.path.relpath(fp, ROOT)
        for raw in open(fp, encoding="utf-8", errors="replace"):
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            m = def_re.match(s)
            if m:
                defined.add(m.group(1)); continue
            m = al_re.match(s)
            if m:
                defined.add(m.group(1)); defined.add(m.group(2)); continue
            m = sa_re.match(s)
            if m:
                set_adds.append((m.group(1), rel))
    orphans = [(i, f) for (i, f) in set_adds if i not in defined]
    if orphans:
        shown = ", ".join(f"{i} ({f})" for i, f in orphans[:6])
        more = "" if len(orphans) <= 6 else f" …+{len(orphans) - 6} more"
        fail(f"set.add orphans — id defined nowhere in the ontology: {shown}{more}")
    else:
        ok(f"set.add membership: all {len(set_adds)} ids resolve to a def/alias (no cross-pack orphans)")


def check_loaded_set_memberships():
    """Runtime companion to the static orphan check: if a loaded nucleus DB is present
    (a real ontology load has happened), assert every loaded `set.add` membership
    actually survived into the collections table — the failure the static check can't
    see. No DB → skip (nothing has been loaded to verify). Delegates to
    test/verify_set_memberships.py so the same logic serves the release soak test."""
    db = os.path.join(ROOT, "data", "central", "nucleus.db")
    if not os.path.isfile(db):
        return  # nothing loaded — the release soak test runs this after a full load
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "vsm", os.path.join(ROOT, "test", "verify_set_memberships.py"))
        vsm = importlib.util.module_from_spec(spec); spec.loader.exec_module(vsm)
        r = vsm.verify(db, os.path.join(ROOT, "ontology"))
    except Exception as e:
        warn(f"loaded set-membership check could not run: {e}")
        return
    if r["dropped"]:
        shown = ", ".join(f"{n} <- {i}" for n, i, _ in r["dropped"][:6])
        more = "" if len(r["dropped"]) <= 6 else f" …+{len(r['dropped']) - 6} more"
        fail(f"{len(r['dropped'])} loaded set membership(s) LOST at load: {shown}{more}")
    else:
        ok(f"loaded set memberships: all {r['checked']} survived (nucleus.db)")


def check_loaded_link_targets():
    """Runtime guard for cross-pack `ln` mis-binding: if a loaded nucleus DB is present,
    assert every loaded namespaced `ln SRC DST REL` hangs off the REAL source atom, not a
    proto-word bound before the atom existed. No DB → skip. Delegates to
    test/verify_link_targets.py so the same logic serves the release soak test."""
    db = os.path.join(ROOT, "data", "central", "nucleus.db")
    if not os.path.isfile(db):
        return
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "vlt", os.path.join(ROOT, "test", "verify_link_targets.py"))
        vlt = importlib.util.module_from_spec(spec); spec.loader.exec_module(vlt)
        r = vlt.verify(db, os.path.join(ROOT, "ontology"))
    except Exception as e:
        warn(f"loaded link-target check could not run: {e}")
        return
    if r["misbound"]:
        shown = ", ".join(f"{s} -{rel}->" for s, rel, _ in r["misbound"][:6])
        more = "" if len(r["misbound"]) <= 6 else f" …+{len(r['misbound']) - 6} more"
        fail(f"{len(r['misbound'])} loaded link(s) mis-bound to a proto-word: {shown}{more}")
    else:
        ok(f"loaded link targets: all {r['checked']} namespaced links hang off their real atom")


def check_canon_law():
    """The Product·Component·Method upper ontology (docs/for-llm/product-component-ontology.md)
    is derived automatically at ingestion. Assert the law holds after normalization: domain
    super-concepts carry their role, an orphan recipe MINTS its product (recipe ⊆ meal:all),
    and every recipe reaches a product via sys:method_of. Boots a kernel, seeds a food slice,
    runs the normalizer exactly as the ingestion hook does, and checks the shape."""
    os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
    try:
        from lib.akasha.kernel import KernelDispatcher
        from lib.akasha.ontology_normalize import OntologyNormalizer
        from lib.akasha import canon
    except Exception as e:
        fail(f"[E] cannot import canon/normalizer: {e!r}")
        return
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_canon_inv_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for a, d in [("role:product", "product."), ("role:component", "component."),
                 ("role:method", "method."), ("role:producer", "producer."),
                 ("meal", "Meal."), ("recipe", "Recipe."), ("ingredient", "Ingredient."),
                 ("drink", "Drink."), ("cocktail", "Cocktail."), ("spirit", "Spirit."),
                 ("producer", "Producer."), ("dish:soup", "Soup — a dish."),
                 ("recipe:paella", "Paella (Rice). Method: simmer."),
                 ("ingred:veg:tomato", "Tomato."),
                 ("whiskey:brand:x", "A whisky brand."),
                 ("whiskey:distillery:d", "A distillery (producer, not a drink)."),
                 ("ing:lime", "Lime — a cocktail ingredient."),
                 ("spirit:gin", "Gin — a base spirit (a cocktail component).")]:
        loc("def", name=a, description=d, scope="universal")
    ln = [{"method": "kernel.memory.link",
           "params": {"src": "recipe:paella", "dst": "ingred:veg:tomato", "rel": "thesaurus:related"}},
          {"method": "kernel.memory.link",
           "params": {"src": "whiskey:brand:x", "dst": "whiskey:distillery:d", "rel": "whiskey:made_by"}}]
    for s in ln:
        loc(s["method"], **s["params"])

    sess = k.manager.get_session("admin")
    cortex = sess.local_cortex
    cores = [getattr(cortex, "core", None), getattr(getattr(sess, "nucleus", None), "core", None)]
    for s in OntologyNormalizer(cores).plan(link_steps=ln):
        loc(s["method"], **s["params"])

    def linked(src, dst, rel):
        sk, dk = cortex.resolve_alias(src), cortex.resolve_alias(dst)
        return bool(sk and dk) and any(x == dk and r == rel
                                       for x, r in (cortex.get_adjacent_links(sk) or []))

    if linked("meal", "role:product", canon.IS_A) and linked("recipe", "role:method", canon.IS_A):
        ok("[E] canon: domain super-concepts carry their role")
    else:
        fail("[E] canon: a domain super-concept is missing its role sys:is_a")

    if cortex.resolve_alias("dish:paella") and linked("recipe:paella", "dish:paella", canon.METHOD_OF):
        ok("[E] canon: orphan recipe minted its product + method_of (recipe ⊆ meal)")
    else:
        fail("[E] canon: orphan recipe NOT bound to a minted product (subset invariant broken)")

    mkey = cortex.resolve_alias("dish:paella")
    if mkey and mkey in set(cortex.get_collection_members("meal:all") or []):
        ok("[E] canon: minted product is in the meal:all superset")
    else:
        fail("[E] canon: minted product missing from meal:all")

    # drink side — the category rolls up into the drink umbrella, a spirit brand is a drink
    # product, its distillery is a PRODUCER (never a drink), and made_by is canonicalized.
    def in_set(setname, alias):
        key = cortex.resolve_alias(alias)
        return bool(key) and key in set(cortex.get_collection_members(setname) or [])

    if linked("spirit", "drink", canon.IS_A) and in_set("drink:all", "whiskey:brand:x"):
        ok("[E] canon: spirit rolls up into drink; a spirit brand is in drink:all")
    else:
        fail("[E] canon: drink rollup broken (spirit not is_a drink or brand not in drink:all)")

    if not in_set("drink:all", "whiskey:distillery:d") and in_set("producer:all", "whiskey:distillery:d"):
        ok("[E] canon: a producer (distillery) is NOT a drink — it stays in producer:all")
    else:
        fail("[E] canon: a producer leaked into drink:all (or is missing from producer:all)")

    if linked("whiskey:brand:x", "whiskey:distillery:d", canon.MADE_BY):
        ok("[E] canon: producer link canonicalized to sys:made_by")
    else:
        fail("[E] canon: made_by not canonicalized")

    # drink components (ing:/spirit: base) are enrolled in the universal component role.
    if (linked("ing:lime", "ingredient", canon.IS_A) and in_set("ingredient:all", "ing:lime")
            and linked("spirit:gin", "ingredient", canon.IS_A)):
        ok("[E] canon: drink components (ing:/spirit:) carry role:component (is_a ingredient)")
    else:
        fail("[E] canon: drink components not enrolled in the component role")


def main():
    check_static_anchors()
    check_route_proliferation()
    check_concept_one_path()
    check_junk()
    check_set_membership_orphans()
    check_loaded_set_memberships()
    check_loaded_link_targets()
    check_runtime()
    check_canon_law()

    print()
    for m in _ok:
        print(f"  OK   {m}")
    for m in _warn:
        print(f"  REVIEW {m}")
    for m in _fail:
        print(f"  FAIL {m}")
    print()
    print(f"  {len(_ok)} ok, {len(_warn)} review, {len(_fail)} fail")
    if _fail:
        print("\nRESULT: FAIL — a hard invariant regressed.")
        return 1
    if _warn:
        print("\nRESULT: PASS (with review items — confirm new routes / markers).")
        return 0
    print("\nRESULT: PASS — all invariants hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
