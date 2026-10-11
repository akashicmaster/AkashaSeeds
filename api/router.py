"""
Command Router (Payload Builder).
Maps CLI short-hand tokens to JSON-RPC 2.0 method calls.
No execution logic — purely parses input and constructs payloads.
"""
import re
import uuid
import shlex

# A token counts as a key=value kwarg only when the part before the first '=' is a
# bare identifier (letters/digits/_.:- , no whitespace or punctuation). This stops a
# quoted free-text argument that legitimately contains '=' — e.g. a `def "id"
# "sampling_operation; slot=001; candidate_set=historical; …"` description — from
# being shredded into a bogus kwarg (key "sampling_operation; slot"), which silently
# dropped the description and left a bare hub atom. Real kwargs (content=, color=,
# col1=) always have identifier keys, so this never affects them.
_KWARG_KEY_RE = re.compile(r"^[A-Za-z_][\w.:-]*$")

from api import cli_table as _cli_table     # GENERATED — the platform's commands (group 4, 4.6)


class CommandRouter:
    # GENERATED from the manifests' `cli` attributes (scripts/gen_cli_table.py → api/cli_table.py) —
    # the platform's and the application's alike, each declared beside its op. Registry-derived
    # Concept Model specs are merged in lazily (augment_from_registry).
    COMMAND_SPECS = dict(_cli_table.CLI_SPECS)

    # ── Concept-model prefix → group name ────────────────────────────────────
    # Commands whose keys start with one of these prefixes belong to that
    # concept model and are hidden from the default help listing.
    # Filled from the registry (augment_from_registry). A command names its group through its op
    # (the method's own prefix) or a `group` in its `cli`; no abbreviated spelling is held as data.
    CONCEPT_PREFIXES: dict = {}

    @classmethod
    def _get_concept_group(cls, cmd: str) -> "str | None":
        # Exact CLI-alias match first (e.g. "reference" → "thesaurus"); such aliases
        # do not start with the "prefix." so the startswith scan below would miss them.
        g = cls._command_groups.get(cmd)
        if g:
            return g
        spec = cls.COMMAND_SPECS.get(cmd) or {}
        if spec.get("group"):                   # a platform `cli` entry that names its group
            return spec["group"]
        for prefix, group in cls.CONCEPT_PREFIXES.items():
            if cmd.startswith(prefix):
                return group
        # An abbreviated spelling (`cs.new` → `cast.new`) belongs to its METHOD's model.
        method = str(spec.get("method") or "")
        if "." in cmd and "." in method:
            return cls.CONCEPT_PREFIXES.get(method.split(".", 1)[0] + ".")
        return None

    @classmethod
    def get_core_specs(cls) -> dict:
        return {cmd: spec for cmd, spec in cls.COMMAND_SPECS.items()
                if cls._get_concept_group(cmd) is None}

    @classmethod
    def get_concept_specs(cls, group: str) -> dict:
        return {cmd: spec for cmd, spec in cls.COMMAND_SPECS.items()
                if cls._get_concept_group(cmd) == group}

    # ── Concept-model short descriptions (for list views) ────────────────────
    # Help labels: a registry-discovered class labels its own group (CONCEPT_LABEL); a package
    # labels a group no class names (`cli_groups` in its manifest, generated into CLI_GROUPS).
    CONCEPT_LABELS: dict = dict(_cli_table.CLI_GROUPS)

    # ── Auto-augmentation from ConceptRegistry ───────────────────────────────
    # Populated lazily on first use; never overwrites hand-written entries.
    _augmented: bool = False
    # CLI command → concept group, for aliases that don't start with the "prefix."
    # (e.g. "reference" → "thesaurus"); consulted by _get_concept_group.
    _command_groups: dict = {}
    # Full method name → its CLI alias, so typing the method name ("thesaurus.reference")
    # dispatches the same as the short alias ("reference"). Not shown in help.
    _method_aliases: dict = {}

    @classmethod
    def augment_from_registry(cls, registry) -> None:
        """
        Merge auto-derived specs from a ConceptRegistry into this router.

        Called lazily by _ensure_augmented() on first use, using the
        module-level active registry set by kernel.py at startup.
        Hand-written entries always take precedence — registry entries only
        fill in what is absent.
        """
        for cmd, spec in registry.get_command_specs().items():
            if cmd not in cls.COMMAND_SPECS:
                cls.COMMAND_SPECS[cmd] = spec
        # CLI-alias → concept-group map, so help groups aliases like "reference".
        for cmd, group in registry.get_command_groups().items():
            cls._command_groups.setdefault(cmd, group)
        for prefix, group in registry.get_concept_prefixes().items():
            if prefix not in cls.CONCEPT_PREFIXES:
                cls.CONCEPT_PREFIXES[prefix] = group
        for name, label in registry.get_concept_labels().items():
            if name not in cls.CONCEPT_LABELS:
                cls.CONCEPT_LABELS[name] = label

        # The full concept-model method name always dispatches, uniformly across ALL
        # models — the canonical form. Every command whose spec targets a different
        # method (an abbreviation like "cs.new" → cast.new, or an alias) registers its
        # method name as a dispatch alias, so `cast.new` works as well as `cs.new` and
        # `thesaurus.reference` as well as any short form. Built from the full merged
        # COMMAND_SPECS (hand-written abbreviations + registry entries alike).
        for cmd, spec in cls.COMMAND_SPECS.items():
            method = spec.get("method")
            if method and method != cmd and method not in cls.COMMAND_SPECS:
                cls._method_aliases.setdefault(method, cmd)
        cls._augmented = True

    @classmethod
    def _ensure_augmented(cls) -> None:
        """Augment from the active ConceptRegistry if not yet done.

        In the split front/back deployment the CLI runs as a thin client attached to the Cell
        daemon and never boots the kernel — so no registry is `set_active` in THIS process and the
        drop-in concept-model commands (rec/table/quadrant/lens.flatten/recipe/formula + the food
        models) would be missing from the client's router (Unknown command / absent from `help -c`).
        When no active registry exists, discover one here: discovery only imports the concept
        classes, needs no engine, and makes those commands routable in any process."""
        if cls._augmented:
            return
        try:
            from lib.akasha.concepts import registry as _reg_mod
            reg = _reg_mod.get_active()
            if reg is None:
                # the same discovery the kernel runs: the platform's models, the instance layer,
                # and the application's from the application root
                reg = _reg_mod.build_active()
            if reg is not None:
                cls.augment_from_registry(reg)
        except ImportError:
            cls._augmented = True  # don't retry if import fails
        except Exception:
            cls._augmented = True  # a discovery hiccup must never break the CLI

    @classmethod
    def concept_namespaces(cls) -> "dict":
        """Return {model-namespace: [operator-suffix, …]} for every concept model —
        the set a shell can offer as subcommand modes. The namespace is the method
        prefix (e.g. "thesaurus", "cast", "note"); the operators are its bare suffixes
        (what you type inside `[thesaurus]` mode: reference / explore / concept)."""
        cls._ensure_augmented()
        ns: dict = {}
        for cmd, spec in cls.COMMAND_SPECS.items():
            if cls._get_concept_group(cmd) is None:
                continue
            method = spec.get("method", cmd)
            if "." not in method:
                continue
            prefix, suffix = method.split(".", 1)
            ns.setdefault(prefix, set()).add(suffix)
        return {k: sorted(v) for k, v in ns.items()}

    @classmethod
    def is_command(cls, token: str) -> bool:
        """True if `token` is the head of a recognised global command / alias. A subcommand
        mode uses this to let real commands pass through (`tree`, `s.ls`, `lens`, `sim` …)
        instead of scoping them to the mode."""
        cls._ensure_augmented()
        t = (token or "").strip().lower()
        return bool(t) and (t in cls.COMMAND_SPECS or t in cls._method_aliases)

    @classmethod
    def list_concepts(cls) -> "list[str]":
        cls._ensure_augmented()
        seen: set = set()
        result = []
        for cmd in cls.COMMAND_SPECS:
            g = cls._get_concept_group(cmd)
            if g and g not in seen:
                seen.add(g)
                result.append(g)
        return sorted(result)

    @classmethod
    def get_concept_info(cls) -> "list[tuple[str,str,int]]":
        """Return (name, label, operator_count) for all concept models, sorted by name."""
        cls._ensure_augmented()
        counts: dict = {}
        for cmd in cls.COMMAND_SPECS:
            g = cls._get_concept_group(cmd)
            if g:
                counts[g] = counts.get(g, 0) + 1
        result = []
        for name in sorted(counts):
            label = cls.CONCEPT_LABELS.get(name, "")
            result.append((name, label, counts[name]))
        return result

    @classmethod
    def build_rpc_request(cls, command_str: str, session_token: str) -> dict:
        """
        Parses a CLI input string and constructs a JSON-RPC 2.0 payload.
        Returns None if the command is unrecognised.
        """
        cls._ensure_augmented()
        if not command_str.strip():
            return None

        try:
            parts = shlex.split(command_str)
        except ValueError:
            parts = command_str.strip().split()

        if not parts:
            return None

        cmd = parts[0].lower()
        args = parts[1:]

        # ── Subcommand resolution ─────────────────────────────────────────────
        # Allow space-separated subcommands as an alternative to dots.
        # "al ls" → "al.ls",  "s add name $it" → "s.add" with ["name", "$it"]
        # The subcommand always wins when cmd.arg[0] is a known entry, so
        # "al ls" maps to al.ls (list all), not al with id="ls".
        # Plain args ("ln src dst rel", "al $it name") are unaffected because
        # "ln.src" and "al.$it" are not in COMMAND_SPECS.
        if args:
            _sub = f"{cmd}.{args[0]}"
            # Also match a full concept method name ("thesaurus reference" → thesaurus.reference,
            # "cast new" → cast.new) so a concept model reads as "<model> <operator>".
            if _sub in cls.COMMAND_SPECS or _sub in cls._method_aliases:
                cmd, args = _sub, args[1:]

        # focus — all remaining tokens are the filter list (@me, @group:x, @ns:x, @all)
        if cmd == "focus":
            return cls._create_payload("session.focus", {"tokens": args}, session_token)

        # su / user.* / grp.* — admin-only, hidden from help
        if cmd == "su":
            target = args[0] if args else "exit"
            return cls._create_payload("sys.su", {"target": target, "passphrase": ""}, session_token)

        if cmd == "user.ls":
            return cls._create_payload("user.ls", {}, session_token)
        if cmd == "user.add":
            # user.add <id> [role]  — passphrase_hash injected by stdio portal
            cid   = args[0] if args else ""
            role  = args[1] if len(args) > 1 else "user"
            return cls._create_payload("user.add", {"client_id": cid, "role": role, "passphrase_hash": ""}, session_token)
        if cmd == "user.rm":
            return cls._create_payload("user.rm", {"client_id": args[0] if args else ""}, session_token)
        if cmd == "user.mod":
            cid  = args[0] if args else ""
            role = args[1] if len(args) > 1 else ""
            return cls._create_payload("user.mod", {"client_id": cid, "role": role}, session_token)
        if cmd == "user.id":
            return cls._create_payload("user.id", {"client_id": args[0] if args else ""}, session_token)
        if cmd == "user.passwd":
            # passphrase_hash injected by stdio portal
            return cls._create_payload("user.passwd", {"client_id": args[0] if args else "", "passphrase_hash": ""}, session_token)

        # S2-f — grp.* accept BOTH positional (`grp.add plants-lab henri`) AND key=value
        # (`grp.add group_id=plants-lab member_id=henri`); the two spellings must agree. Previously a
        # `key=value` token was taken positionally, so `group_id=plants-lab` became the group id itself
        # and minted a phantom group.
        if cmd in ("grp.ls", "grp.new", "grp.add", "grp.rm", "grp.lib", "grp.del"):
            _keys = {"grp.ls": ["group_id"], "grp.new": ["group_id", "admin_id"],
                     "grp.add": ["group_id", "member_id"], "grp.rm": ["group_id", "member_id"],
                     "grp.lib": ["group_id", "action", "member_id"], "grp.del": ["group_id"]}[cmd]
            return cls._create_payload(cmd, cls._kv_or_positional(args, _keys), session_token)

        # dont.* — delegation / donation sets
        if cmd in ("dont", "dont.create", "dont.add", "dont.send", "dont.ls", "dont.open"):
            sub = args[0] if (cmd == "dont" and args) else cmd.split(".", 1)[-1] if "." in cmd else ""
            rest = args[1:] if cmd == "dont" else args
            if sub == "create":
                name = rest[0] if rest else ""
                desc = " ".join(rest[1:]) if len(rest) > 1 else ""
                return cls._create_payload("dont.create", {"name": name, "description": desc}, session_token)
            if sub == "add":
                name = rest[0] if rest else ""
                targets = rest[1:] if len(rest) > 1 else []
                return cls._create_payload("dont.add", {"name": name, "targets": targets}, session_token)
            if sub == "send":
                name = rest[0] if rest else ""
                to   = rest[1] if len(rest) > 1 else ""
                return cls._create_payload("dont.send", {"name": name, "to": to}, session_token)
            if sub == "open":
                name = rest[0] if rest else ""
                to   = rest[1] if len(rest) > 1 else ""
                return cls._create_payload("dont.open", {"name": name, "to": to}, session_token)
            if sub in ("ls", "list", ""):
                name = rest[0] if rest else ""
                return cls._create_payload("dont.ls", {"name": name}, session_token)

        # Special handling for 'exp' / 'explore' — explore with key=value filter syntax
        # exp ns=myth  |  exp set=deity  |  exp type=rec  |  exp icarus%  |  exp myth
        if cmd in ("exp", "explore"):
            params = {}
            for token in args:
                if "=" in token:
                    k, v = token.split("=", 1)
                    params[k.strip()] = v.strip()
                elif "pat" not in params and "ns" not in params and "set" not in params:
                    params["pat"] = token  # first bare token → pat= (pattern search)
            return cls._create_payload("explore", params, session_token)

        # Special handling for 'assoc'/'associate' — gap detection with key=value syntax
        # assoc myth:icarus  |  assoc myth:icarus axis=emotion  |  assoc id=icarus fill=yes
        if cmd in ("assoc", "associate"):
            params = {}
            id_set = False
            for token in args:
                if "=" in token:
                    k, v = token.split("=", 1)
                    params[k.strip()] = v.strip()
                elif not id_set:
                    params["id"] = token
                    id_set = True
            return cls._create_payload("kernel.associate", params, session_token)

        # Special handling for 'dream' — hypothetical linking with key=value syntax
        # dream myth:icarus  |  dream myth:icarus axis=emotion commit=yes
        if cmd == "dream":
            params = {}
            id_set = False
            for token in args:
                if "=" in token:
                    k, v = token.split("=", 1)
                    params[k.strip()] = v.strip()
                elif not id_set:
                    params["id"] = token
                    id_set = True
            return cls._create_payload("jataka.dream", params, session_token)

        # Special handling for 'nebula' — global survey, key=value tuning only, no positional.
        # `nebula`, `nebula again`, `nebula limit=10 min_size=5`, `nebula ns=dish`.
        if cmd == "nebula":
            params = {}
            for token in args:
                if "=" in token:
                    k, v = token.split("=", 1)
                    params[k.strip()] = v.strip()
                elif token:
                    params[token.strip()] = "yes"      # bare flag, e.g. `again`
            return cls._create_payload("nebula", params, session_token)

        # Special handling for 'cross' / 'cross.axes' / 'cross.atom'
        if cmd in ("cross", "cross.axes"):
            method = "sys.cross.query" if cmd == "cross" else "sys.cross.axes"
            return cls._create_payload(method, {"concepts": args}, session_token)
        if cmd == "cross.atom":
            # First arg is the ontology atom; remaining args are concept filters
            atom    = args[0] if args else ""
            concepts = args[1:] if len(args) > 1 else []
            return cls._create_payload("sys.cross.atom", {"atom": atom, "concepts": concepts}, session_token)

        # Special handling for 'locale' — locale [set <primary> [<l1,l2,...>]]
        if cmd == "locale":
            if not args or args[0] == "get":
                return cls._create_payload("locale.get", {}, session_token)
            if args[0] == "set":
                primary   = args[1] if len(args) > 1 else ""
                supported = args[2] if len(args) > 2 else ""
                params = {}
                if primary:   params["primary"]   = primary
                if supported: params["supported"]  = supported
                return cls._create_payload("locale.set", params, session_token)
            # locale <primary> [<supported>]  — shorthand
            primary   = args[0]
            supported = args[1] if len(args) > 1 else ""
            params = {"primary": primary}
            if supported: params["supported"] = supported
            return cls._create_payload("locale.set", params, session_token)

        # Special handling for 'scope' — subcommand routing + key=value parsing
        if cmd == "scope":
            if not args or args[0] == "get":
                return cls._create_payload("sys.scope.get", {}, session_token)
            if args[0] == "reset":
                return cls._create_payload("sys.scope.reset", {}, session_token)
            # Parse key=value pairs for sys.scope.set
            params = {}
            for token in args:
                if "=" in token:
                    k, v = token.split("=", 1)
                    params[k.strip()] = v.strip()
            return cls._create_payload("sys.scope.set", params, session_token)

        # Bare non-negative integer → navigate to stored signpost by index
        if cmd.isdigit():
            return cls._create_payload("dive.look", {"signpost": int(cmd)}, session_token)

        # A full concept-method name typed directly ("thesaurus.reference") dispatches
        # the same as its short CLI alias ("reference").
        if cmd in cls._method_aliases:
            cmd = cls._method_aliases[cmd]

        if cmd not in cls.COMMAND_SPECS:
            return None

        spec = cls.COMMAND_SPECS[cmd]
        method = spec["method"]
        expected = spec.get("args", [])

        # Separate key=value tokens from positional tokens.
        # key=value wins over positional when the key matches a declared arg name.
        # Extra key=value pairs beyond the declared spec pass through as-is
        # (e.g. rec.new content="Apple" color=red, table.row.add col1=v1 col2=v2).
        kw_args: dict = {}
        pos_args: list = []
        for token in args:
            if "=" in token and not token.startswith("="):
                k, v = token.split("=", 1)
                # Only a bare-identifier key is a real kwarg; a quoted free-text
                # argument that happens to contain '=' stays positional (see
                # _KWARG_KEY_RE above).
                if _KWARG_KEY_RE.match(k.strip()):
                    kw_args[k.strip()] = v.strip()
                else:
                    pos_args.append(token)
            else:
                pos_args.append(token)

        params: dict = {}
        for i, arg_name in enumerate(expected):
            if arg_name in kw_args:
                params[arg_name] = kw_args.pop(arg_name)
            elif pos_args:
                # Last declared arg absorbs all remaining positional tokens
                if i == len(expected) - 1:
                    params[arg_name] = " ".join(pos_args)
                    pos_args = []
                else:
                    params[arg_name] = pos_args.pop(0)

        # Pass through extra key=value args not in the declared spec
        params.update(kw_args)

        return cls._create_payload(method, params, session_token)

    @staticmethod
    def _kv_or_positional(args, keys):
        """S2-f — build a params dict from CLI args that may be POSITIONAL (`plants-lab henri`) or
        `key=value` (`group_id=plants-lab member_id=henri`), or a mix. A `k=v` token is taken by its
        key; bare tokens fill the remaining canonical `keys` in order. Both spellings then agree."""
        out, pos = {}, []
        for a in args:
            if "=" in a and not a.startswith("="):
                k, v = a.split("=", 1)
                out[k.strip()] = v
            else:
                pos.append(a)
        for k in keys:
            if k not in out and pos:
                out[k] = pos.pop(0)
        return out

    @staticmethod
    def _create_payload(method: str, params: dict, session_token: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": {
                "session_token": session_token,
                "data": params
            },
            "id": str(uuid.uuid4())
        }
