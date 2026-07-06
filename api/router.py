"""
Command Router (Payload Builder).
Maps CLI short-hand tokens to JSON-RPC 2.0 method calls.
No execution logic — purely parses input and constructs payloads.
"""
import uuid
import shlex


class CommandRouter:
    COMMAND_SPECS = {
        # ── Memory ────────────────────────────────────────────────────
        "w":      {"method": "kernel.memory.write",  "args": ["text"],             "desc": "Write an atom into memory"},
        "def":    {"method": "kernel.memory.define", "args": ["name"],             "desc": "Define a conceptual hub"},
        "r":      {"method": "kernel.memory.read",   "args": ["id"],               "desc": "Remember — recall an atom by ID / alias / $ref"},
        "rm":     {"method": "kernel.memory.drop",   "args": ["id"],               "desc": "Drop an atom from memory"},
        "ln":     {"method": "kernel.memory.link",   "args": ["src", "dst", "rel"],"desc": "Link two nodes with a typed relation (quote multi-word names)"},
        "ln.ls":  {"method": "link.list",            "args": ["id"],               "desc": "List links on an atom"},
        "ln.+":   {"method": "link.reinforce",       "args": ["src", "dst", "rel"],"desc": "Reinforce a link weight"},
        "ln.rm":  {"method": "ln.rm",               "args": ["src", "dst", "rel"],"desc": "Remove a typed link between two atoms"},
        "meta":   {"method": "meta.set",             "args": ["id", "key", "value"],"desc": "Set metadata key on atom"},
        "exp":    {"method": "explore",              "args": ["ns", "set", "type", "pat", "limit"], "desc": "Explore ontology by filter: ns=, set=, type=, pat= (positional = pat)"},
        "tree":   {"method": "graph.tree",           "args": ["target", "depth", "follow", "format"], "desc": "Link-traversal tree: tree <alias|key|set:*|ns:*> [depth=2] [follow=<rel>] [format=rich|ascii]"},
        # ── Names / Aliases ───────────────────────────────────────────
        "al":     {"method": "kernel.identity.alias",      "args": ["id", "name"],  "desc": "Name an atom (multi-word: al $it first kiss)"},
        "al.ls":  {"method": "kernel.identity.alias.list", "args": [],              "desc": "List all named atoms"},
        "al.rm":  {"method": "al.rm",                     "args": ["name"],        "desc": "Remove an alias binding (atom is not deleted)"},
        "al.find":{"method": "kernel.identity.alias.find", "args": ["pattern"],     "desc": "Find names matching a pattern (e.g. city%)"},
        # ── Dive ─────────────────────────────────────────────────────
        "dive":   {"method": "dive.look", "args": ["id"],  "desc": "Dive into an atom — see its meaning space and signposts"},
        "look":   {"method": "dive.look", "args": ["id"],  "desc": "Dive (legacy alias)"},
        "d":      {"method": "dive.look", "args": ["id"],  "desc": "Dive (short alias)"},
        "out":    {"method": "dive.out",  "args": ["id"],  "desc": "Zoom out to the macro view"},
        # ── Sets ──────────────────────────────────────────────────────
        "s.add":  {"method": "set.add",   "args": ["name", "id"],             "desc": "Add atom to set"},
        "s.rm":   {"method": "set.rm",    "args": ["name", "id"],             "desc": "Remove atom from set"},
        "s.ls":   {"method": "set.ls",    "args": ["name"],                   "desc": "List set members"},
        "s.clear":{"method": "set.clear", "args": ["name"],                   "desc": "Clear a set"},
        "s.op":   {"method": "set.op",    "args": ["op", "result", "a", "b"], "desc": "Set operation (union|isect|diff)"},
        # ── Notes ─────────────────────────────────────────────────────
        "n.new":  {"method": "note.new",       "args": ["title"],         "desc": "Create a new note/document"},
        "n.ls":   {"method": "note.ls",        "args": [],                "desc": "List all notes for current user"},
        "n.open": {"method": "note.open",      "args": ["note_id"],       "desc": "Open (mount) an existing note by ID"},
        "n.add":  {"method": "note.add",       "args": ["text"],          "desc": "Append a content chunk to the active note"},
        "n.sec":  {"method": "note.section",   "args": ["title"],         "desc": "Add a section to the active note"},
        "n.chap": {"method": "note.section",   "args": ["title", "role"], "desc": "Add a chapter (role=chapter)"},
        "n.para": {"method": "note.paragraph", "args": ["category"],      "desc": "Add a paragraph container"},
        "n.toc":  {"method": "note.toc",       "args": [],                "desc": "Show table of contents for the active note"},
        "n.read": {"method": "note.read",      "args": [],                "desc": "Read the active note as sequential text"},
        "n.rm":     {"method": "note.rm",      "args": [],                  "desc": "Delete the active note"},
        "n.list":   {"method": "note.list",    "args": [],                  "desc": "List chunks (head preview)"},
        "n.edit":   {"method": "note.edit",    "args": ["chunk_id", "text"],"desc": "Edit a chunk (new version)"},
        "n.move":   {"method": "note.move",    "args": ["chunk_id", "after"],"desc": "Reorder a chunk"},
        "n.undo":   {"method": "note.undo",    "args": [],                  "desc": "Undo last edit or reorder"},
        "n.redo":   {"method": "note.redo",    "args": [],                  "desc": "Redo last undone edit"},
        "n.restore":{"method": "note.restore", "args": [],                  "desc": "Restore original order and content"},
        "n.rename": {"method": "note.rename",  "args": ["title"],           "desc": "Rename the active note"},
        # ── Associate ─────────────────────────────────────────────────
        "associate": {"method": "kernel.associate", "args": ["id", "axis", "fill"], "desc": "Gap detection: find missing semantic links for an atom (one level, no inference)"},
        "assoc":     {"method": "kernel.associate", "args": ["id", "axis", "fill"], "desc": "Gap detection (alias: associate)"},
        # ── Focus ─────────────────────────────────────────────────────
        "focus":     {"method": "session.focus",    "args": [],                                "desc": "Set display focus (@me @group:name @ns:prefix | @all)"},
        # ── Scope ─────────────────────────────────────────────────────
        "scope":     {"method": "sys.scope.set",    "args": [],                                "desc": "Get/set session scope state (scope [get|reset|key=val ...])"},
        # ── Ontology Dump & Inspection ────────────────────────────────
        "onto.dump":   {"method": "onto.dump",   "args": ["mode", "ns", "rel", "collection", "sort", "limit"], "desc": "Dump ontology (modes: atoms|links|antonyms|aliases|sets|namespaces)"},
        "onto.reload":       {"method": "onto.reload",       "args": ["confirm"],         "desc": "Clear ontology sentinels and re-trigger boot load (requires librarian, confirm=RELOAD)"},
        "onto.reset":        {"method": "onto.reset",        "args": ["confirm"],         "desc": "⚠ Wipe nucleus ontology data (DNA preserved) then reload (requires librarian, confirm=RESET)"},
        "onto.genesis.redo": {"method": "onto.genesis.redo", "args": ["confirm"],         "desc": "⚠ Remove genesis anchors to allow re-running genesis_rite (requires admin, confirm=GENESIS)"},
        "onto.scope.drop":   {"method": "onto.scope.drop",   "args": ["scope", "confirm"],"desc": "⚠ Delete all nucleus atoms carrying a given scope (requires librarian, confirm=DROP:<scope>)"},
        "onto.pack.list":    {"method": "onto.pack.list",    "args": [],       "desc": "List all ontology packages from REGISTRY.json with load status"},
        "onto.pack.enable":  {"method": "onto.pack.enable",  "args": ["name"], "desc": "Enable an optional ontology pack and trigger load (requires librarian)"},
        "onto.pack.disable": {"method": "onto.pack.disable", "args": ["name"], "desc": "Disable an optional ontology pack (atoms remain until onto.reset) (requires librarian)"},
        # ── Log ───────────────────────────────────────────────────────
        "log.new":    {"method": "log.new",        "args": ["name"],   "desc": "Create a new exploration Log"},
        "log.ls":     {"method": "log.ls",         "args": [],         "desc": "List all exploration Logs"},
        "log.cp":     {"method": "log.checkpoint", "args": ["note"],   "desc": "Record a session checkpoint"},
        "log.ann":    {"method": "log.annotate",   "args": ["text"],   "desc": "Annotate the last checkpoint"},
        "log.replay": {"method": "log.replay",     "args": [],         "desc": "Replay all checkpoints"},
        "log.read":   {"method": "log.read",       "args": [],         "desc": "Read the active log"},
        "log.rm":     {"method": "log.rm",         "args": [],         "desc": "Delete the active log"},
        # ── Whiteboard ────────────────────────────────────────────────
        "wb.new":    {"method": "wb.new",    "args": ["name"],    "desc": "Create a new Whiteboard"},
        "wb.pin":    {"method": "wb.pin",    "args": ["concept"], "desc": "Pin a concept to active Whiteboard"},
        "wb.unpin":  {"method": "wb.unpin",  "args": ["concept"], "desc": "Unpin a concept"},
        "wb.focus":  {"method": "wb.focus",  "args": ["name"],    "desc": "Switch active Whiteboard"},
        "wb.ls":     {"method": "wb.ls",     "args": [],          "desc": "List all Whiteboards"},
        "wb.show":   {"method": "wb.show",   "args": [],          "desc": "Show active Whiteboard state"},
        "wb.rm":     {"method": "wb.rm",     "args": ["name"],    "desc": "Remove a Whiteboard"},
        # ── Cockpit ───────────────────────────────────────────────────
        "cp.new":    {"method": "cockpit.new",    "args": ["name"],         "desc": "Commission a new cockpit"},
        "cp.ls":     {"method": "cockpit.ls",     "args": [],               "desc": "List all cockpits for current user"},
        "cp.open":   {"method": "cockpit.open",   "args": ["cockpit_id"],   "desc": "Mount an existing cockpit"},
        "cp.lock":   {"method": "cockpit.lock",   "args": ["target"],       "desc": "Lock cockpit focal point to an atom"},
        "cp.tune":   {"method": "cockpit.tune",   "args": ["axis", "scope"],"desc": "Tune dimensional lens (axis and/or scope)"},
        "cp.beacon": {"method": "cockpit.beacon", "args": ["note"],         "desc": "Drop a beacon at the locked focal point"},
        "cp.wake":   {"method": "cockpit.wake",   "args": [],               "desc": "Read the chronological beacon trail"},
        "cp.status": {"method": "cockpit.status", "args": [],               "desc": "Show cockpit instrument panel state"},
        "cp.rm":     {"method": "cockpit.rm",     "args": [],               "desc": "Decommission the active cockpit"},
        # ── FieldNote ─────────────────────────────────────────────────
        "fn.new":  {"method": "fieldnote.new",  "args": ["title", "project", "region", "season"], "desc": "Create a new FieldNote"},
        "fn.ls":   {"method": "fieldnote.ls",   "args": [],                                       "desc": "List all FieldNotes"},
        "fn.open": {"method": "fieldnote.open", "args": ["fieldnote_id"],                         "desc": "Open an existing FieldNote"},
        "fn.add":  {"method": "fieldnote.add",  "args": ["text"],                                 "desc": "Add an observation to the active FieldNote"},
        "fn.read": {"method": "fieldnote.read", "args": [],                                       "desc": "Read all observations in the active FieldNote"},
        "fn.rm":   {"method": "fieldnote.rm",   "args": [],                                       "desc": "Delete the active FieldNote"},
        # ── Survey ────────────────────────────────────────────────────
        "sv.new":  {"method": "survey.new",     "args": ["title", "description"],             "desc": "Create a new Survey"},
        "sv.open": {"method": "survey.open",    "args": ["survey_id"],                        "desc": "Open an existing Survey"},
        "sv.ls":   {"method": "survey.ls",      "args": [],                                   "desc": "List all Surveys"},
        "sv.q":    {"method": "survey.q.add",   "args": ["text", "qtype"],                    "desc": "Add a question to active Survey"},
        "sv.opt":  {"method": "survey.opt.add", "args": ["question_id", "label", "value"],    "desc": "Add an option to a question"},
        "sv.who":  {"method": "survey.res.add", "args": ["respondent_id"],                    "desc": "Register a respondent"},
        "sv.ans":  {"method": "survey.ans",     "args": ["question_id", "respondent_atom", "answer"], "desc": "Record a response"},
        "sv.list": {"method": "survey.list",    "args": [],                                   "desc": "Show active Survey structure"},
        "sv.rm":   {"method": "survey.rm",      "args": [],                                   "desc": "Delete the active Survey"},
        # ── Jataka ────────────────────────────────────────────────────
        "dream":  {"method": "jataka.dream",   "args": ["id", "axis", "commit"], "desc": "Inference-based hypothetical linking (tent: prefix). commit=yes to write."},
        # ── Contexa ───────────────────────────────────────────────────
        "fetch":  {"method": "contexa.fetch",  "args": ["query"], "desc": "Fetch from web / Wikipedia"},
        # ── Cross ─────────────────────────────────────────────────────
        "cross":      {"method": "sys.cross.query", "args": [],         "desc": "Cross-concept atom intersection (Space-aware)"},
        "cross.axes": {"method": "sys.cross.axes",  "args": [],         "desc": "Axes available across concepts"},
        "cross.atom": {"method": "sys.cross.atom",  "args": ["atom"],   "desc": "Find concept atoms referencing an ontology atom"},
        # ── Locale ────────────────────────────────────────────────────
        "locale": {"method": "locale.get",  "args": [],        "desc": "Show / set priority locale  (locale  |  locale set <primary> [<l1>,<l2>,...])"},
        # ── Game concept models (soma / engram / operator / eidolon) ──────────
        # These concept models live in lib/akasha/concepts/ and are discoverable
        # by ConceptRegistry, but their CLI short-forms are intentionally absent
        # from COMMAND_SPECS until the game integration is complete.
        # ── Human (evidence-based actor model) ────────────────────────
        "hum.new":        {"method": "human.new",          "args": ["name", "description"],                          "desc": "Create a new Human actor record"},
        "hum.open":       {"method": "human.open",         "args": ["human_id"],                                     "desc": "Open an existing Human record"},
        "hum.ls":         {"method": "human.ls",           "args": [],                                               "desc": "List all Human records"},
        "hum.map":        {"method": "human.map",          "args": [],                                               "desc": "Show structure of active Human record"},
        "hum.rm":         {"method": "human.rm",           "args": [],                                               "desc": "Soft-delete the active Human record"},
        "hum.name":       {"method": "human.name.add",     "args": ["name", "name_type"],                            "desc": "Add a name to the active Human"},
        "hum.birth":      {"method": "human.birth.set",    "args": ["date", "place"],                                "desc": "Set birth date/place"},
        "hum.death":      {"method": "human.death.set",    "args": ["date", "place"],                                "desc": "Set death date/place"},
        "hum.status":     {"method": "human.status.set",   "args": ["status"],                                       "desc": "Set status (alive/deceased/unknown/active/inactive/missing/disputed)"},
        "hum.pseudo":     {"method": "human.pseudo.add",   "args": ["pseudonym", "context"],                         "desc": "Add a pseudonym or alternate name"},
        "hum.assess":     {"method": "human.assess",       "args": ["assessment_type", "content", "source_id"],      "desc": "Add an evidence-backed assessment (trait/policy/risk/...)"},
        "hum.est":        {"method": "human.estimate",     "args": ["estimate_type", "value", "basis"],              "desc": "Add an estimated attribute with basis evidence"},
        "hum.merge.link": {"method": "human.merge.link",   "args": ["other_human_id", "reason"],                     "desc": "Flag two Human records as possibly the same person"},
        "hum.merge.ok":   {"method": "human.merge.confirm","args": ["merge_link_id"],                                "desc": "Confirm a merge link (mark as same person)"},
        "hum.alias":      {"method": "human.alias",        "args": ["alias"],                                        "desc": "Add a contextual alias to the Human"},
        "hum.dispute":    {"method": "human.dispute",      "args": ["target_id", "reason"],                          "desc": "Record a dispute against a Human atom"},
        "hum.fict":       {"method": "human.fictionalize", "args": ["cast_id", "transformation"],                    "desc": "Link Human to a fictional Cast projection"},
        "hum.bond":       {"method": "human.bond.add",     "args": ["target_id", "relation", "strength"],            "desc": "Record a relationship bond to another entity"},
        "hum.bond.up":    {"method": "human.bond.update",  "args": ["bond_id", "delta", "event_id"],                 "desc": "Record a change to an existing bond"},
        "hum.obs":        {"method": "human.observable",   "args": [],                                               "desc": "Show externally evidenced facts linked to this Human"},
        "hum.timeline":   {"method": "human.timeline",     "args": [],                                               "desc": "Show chronological event timeline for this Human"},
        "hum.profile":    {"method": "human.profile",      "args": [],                                               "desc": "Show full profile of the active Human"},
        "hum.diagnose":   {"method": "human.diagnose",     "args": [],                                               "desc": "Diagnose completeness and evidence quality"},
        "hum.trace":      {"method": "human.trace",        "args": ["target_id"],                                    "desc": "Trace evidence chain for a Human atom"},
        # ── Correspondence (cross-system mapping layer) ───────────────
        "corr.new":       {"method": "corr.new",          "args": ["title", "description"],                                      "desc": "Create a new Correspondence root"},
        "corr.open":      {"method": "corr.open",         "args": ["corr_id"],                                                   "desc": "Open an existing Correspondence root"},
        "corr.ls":        {"method": "corr.ls",           "args": [],                                                            "desc": "List all Correspondence roots"},
        "corr.map":       {"method": "corr.map",          "args": [],                                                            "desc": "Show structure of active Correspondence"},
        "corr.rm":        {"method": "corr.rm",           "args": [],                                                            "desc": "Soft-delete the active Correspondence root"},
        "corr.sys":       {"method": "corr.system.add",   "args": ["label", "system_type", "ref_id"],                           "desc": "Register a coordinate/conceptual system"},
        "corr.src":       {"method": "corr.source.add",   "args": ["kind", "title", "credibility"],                             "desc": "Add a source for correspondence evidence"},
        "corr.src.eval":  {"method": "corr.source.eval",  "args": ["source_id", "credibility", "independence"],                 "desc": "Event-sourced re-evaluation of a source"},
        "corr.link":      {"method": "corr.link.add",     "args": ["src_id", "dst_id", "relation", "source_id"],                "desc": "Add a direct evidenced correspondence link"},
        "corr.infer":     {"method": "corr.link.infer",   "args": ["src_id", "dst_id", "relation", "inputs"],                   "desc": "Add an inferred correspondence link with provenance"},
        "corr.proj":      {"method": "corr.project.add",  "args": ["link_id", "target_system_id"],                              "desc": "Project a link into another system"},
        "corr.eval":      {"method": "corr.eval.add",     "args": ["link_id", "confidence", "status"],                         "desc": "Event-sourced re-evaluation of a link"},
        "corr.dispute":   {"method": "corr.dispute.add",  "args": ["target_id", "reason", "severity"],                         "desc": "Record a dispute against a correspondence atom"},
        "corr.trace":     {"method": "corr.trace",        "args": ["link_id"],                                                  "desc": "Trace provenance and evidence chain for a link"},
        "corr.diagnose":  {"method": "corr.diagnose",     "args": [],                                                           "desc": "Diagnose correspondence quality and modeling gaps"},
        # ── Fact (fact recording and source tracking) ─────────────────
        "ft.new":       {"method": "fact.new",         "args": ["title", "description"],                          "desc": "Create a new Fact collection"},
        "ft.open":      {"method": "fact.open",        "args": ["fact_root_id"],                                  "desc": "Open an existing Fact collection"},
        "ft.ls":        {"method": "fact.ls",          "args": [],                                                "desc": "List all Fact collections"},
        "ft.map":       {"method": "fact.map",         "args": [],                                                "desc": "Show structure of active Fact collection"},
        "ft.rm":        {"method": "fact.rm",          "args": [],                                                "desc": "Soft-delete the active Fact collection"},
        "ft.src.add":   {"method": "fact.source.add",  "args": ["url", "kind", "title", "credibility"],          "desc": "Add a Source (evidentiary anchor)"},
        "ft.src.eval":  {"method": "fact.source.eval", "args": ["source_id", "credibility"],                     "desc": "Record an updated credibility evaluation for a Source"},
        "ft.add":       {"method": "fact.add",         "args": ["fact_type", "content", "source_id"],            "desc": "Add a Direct Fact (event/state/relation/absence)"},
        "ft.claim":     {"method": "fact.claim",       "args": ["speaker", "content", "source_id"],              "desc": "Record what someone said (Claim Fact)"},
        "ft.absent":    {"method": "fact.absent",      "args": ["description", "source_id"],                     "desc": "Record an expected-but-missing fact (Absence / Gap)"},
        "ft.infer":     {"method": "fact.infer",       "args": ["fact_type", "content", "inputs"],               "desc": "Add an Inferred Fact derived from multiple Sources"},
        "ft.set.new":   {"method": "fact.set.new",     "args": ["label"],                                        "desc": "Create a FactSet (purpose-driven subset of Facts)"},
        "ft.set.add":   {"method": "fact.set.add",     "args": ["factset_id", "fact_id"],                        "desc": "Add a Fact to a FactSet"},
        "ft.ent.link":  {"method": "fact.entity.link", "args": ["fact_id", "entity_id", "entity_type", "role"],  "desc": "Link a Fact to an Entity"},
        "ft.diagnose":  {"method": "fact.diagnose",    "args": [],                                               "desc": "Diagnose quality and completeness of the Fact collection"},
        "ft.trace":     {"method": "fact.trace",       "args": ["fact_id"],                                      "desc": "Trace a Fact back to its Sources and provenance"},
        # ── Curation (premise-bound reconciliation / view construction) ─
        "cur.new":         {"method": "curation.new",            "args": ["title", "description"],                                "desc": "Create a new Curation workspace"},
        "cur.open":        {"method": "curation.open",           "args": ["curation_id"],                                         "desc": "Open an existing Curation workspace"},
        "cur.ls":          {"method": "curation.ls",             "args": [],                                                      "desc": "List all Curation workspaces"},
        "cur.map":         {"method": "curation.map",            "args": [],                                                      "desc": "Show structure of active Curation workspace"},
        "cur.rm":          {"method": "curation.rm",             "args": [],                                                      "desc": "Soft-delete the active Curation workspace"},
        "cur.premise":     {"method": "curation.premise.add",    "args": ["label", "as_of", "perspective", "conflict_policy"],    "desc": "Add a Premise (world-view under which conflicts fold)"},
        "cur.input":       {"method": "curation.input.add",      "args": ["ref_id", "role", "premise_id", "confidence"],         "desc": "Register an evidence-bearing atom as input"},
        "cur.view":        {"method": "curation.view.run",       "args": ["premise_id", "label", "input_ids"],                   "desc": "Create a View under a Premise"},
        "cur.fold":        {"method": "curation.fold.add",       "args": ["view_id", "resolution_scope", "competing_input_ids"], "desc": "Record a conflict fold (winner, dropped, or unresolved)"},
        "cur.conclude":    {"method": "curation.conclusion.add", "args": ["view_id", "statement", "conclusion_type"],            "desc": "Add a structured conclusion inside a View"},
        "cur.dispute":     {"method": "curation.dispute.add",    "args": ["target_id", "reason", "severity"],                    "desc": "Flag a dispute against a View, Fold, or Conclusion"},
        "cur.trace":       {"method": "curation.trace",          "args": ["target_id"],                                          "desc": "Trace a View, Fold, or Conclusion back to its inputs"},
        "cur.diagnose":    {"method": "curation.diagnose",       "args": [],                                                     "desc": "Diagnose unresolved folds, low-confidence conclusions, coverage gaps"},
        # ── Intelligence (decision-cycle orchestration) ─────────────────
        "intel.new":      {"method": "intelligence.new",            "args": ["title", "description"],                                               "desc": "Create a new Intelligence workspace"},
        "intel.open":     {"method": "intelligence.open",           "args": ["intelligence_id"],                                                     "desc": "Open an existing Intelligence workspace"},
        "intel.ls":       {"method": "intelligence.ls",             "args": [],                                                                      "desc": "List all Intelligence workspaces"},
        "intel.map":      {"method": "intelligence.map",            "args": [],                                                                      "desc": "Show structure of active Intelligence workspace"},
        "intel.rm":       {"method": "intelligence.rm",             "args": [],                                                                      "desc": "Soft-delete the active Intelligence workspace"},
        "intel.req":      {"method": "intelligence.req.add",        "args": ["question", "requirement_type", "priority"],                           "desc": "Add an intelligence Requirement (the central question)"},
        "intel.scan":     {"method": "intelligence.scan.add",       "args": ["requirement_id", "target_id", "scan_type", "signal"],                 "desc": "Record a signal from an existing atom (observe, do not judge)"},
        "intel.gap":      {"method": "intelligence.gap.add",        "args": ["requirement_id", "description", "gap_type", "severity"],              "desc": "Record a knowledge gap (missing, low-confidence, contradicting)"},
        "intel.task":     {"method": "intelligence.task.add",       "args": ["requirement_id", "description", "tasking_type", "gap_id"],            "desc": "Issue a Tasking instruction (collect, verify, analyze, etc.)"},
        "intel.assess":   {"method": "intelligence.assess.add",     "args": ["requirement_id", "assessment_type", "judgment", "basis"],             "desc": "Add an Assessment (judgment grounded in Curation/Fact/Synthesis)"},
        "intel.estimate": {"method": "intelligence.estimate.add",   "args": ["requirement_id", "estimate_type", "statement", "basis"],              "desc": "Add an Estimate (probability, timeline, scenario, range)"},
        "intel.option":   {"method": "intelligence.option.add",     "args": ["requirement_id", "title", "option_type", "basis"],                   "desc": "Add a decision Option with benefits, risks, feasibility"},
        "intel.recommend":{"method": "intelligence.recommend.add",  "args": ["requirement_id", "statement", "recommended_option_id", "basis"],      "desc": "Issue a Recommendation (draft/reviewed/issued)"},
        "intel.decision": {"method": "intelligence.decision.add",   "args": ["recommendation_id", "decision_status", "decided_by", "reason"],      "desc": "Record a Decision against a Recommendation (event-sourced)"},
        "intel.dispute":  {"method": "intelligence.dispute.add",    "args": ["target_id", "reason", "severity"],                                   "desc": "Flag a dispute against any Intelligence atom"},
        "intel.cycle":    {"method": "intelligence.cycle",          "args": ["requirement_id"],                                                     "desc": "Return the full cycle view for a Requirement"},
        "intel.trace":    {"method": "intelligence.trace",          "args": ["target_id"],                                                          "desc": "Trace an Intelligence atom to its requirement and basis"},
        "intel.diagnose": {"method": "intelligence.diagnose",       "args": [],                                                                     "desc": "Diagnose open gaps, orphaned work products, undecided recommendations"},
        # ── JCL (Job Control Layer) ── admin/librarian only for submit/cancel ──
        "job.submit": {"method": "job.submit", "args": ["steps", "label", "fail_fast"], "desc": "Submit a JCL job (admin/librarian only); steps= JSON array of {method, params}"},
        "job.ls":     {"method": "job.ls",     "args": ["owner"],        "desc": "List background JCL jobs (owner filter for admins)"},
        "job.stat":   {"method": "job.stat",   "args": ["job_id"],       "desc": "Show status of a specific JCL job"},
        "job.cancel": {"method": "job.cancel", "args": ["job_id"],       "desc": "Cancel a pending JCL job (admin/librarian only)"},
        # ── CSL (Concept Scripting Language) ─────────────────────────
        "csl":        {"method": "csl",        "args": ["script"], "desc": "Check + transpile + execute CSL (inline text or .csl file path)"},
        "csl.check":  {"method": "csl.check",  "args": ["script"], "desc": "Validate CSL syntax and semantics"},
        "csl.build":  {"method": "csl.build",  "args": ["script"], "desc": "Transpile CSL to .ak (optional: out=<path>)"},
        "csl.run":    {"method": "csl.run",    "args": ["script"], "desc": "Check, transpile and execute CSL as Harmonia job"},
        # ── Country (evidence-grounded country / polity / entity) ────
        "country.new":           {"method": "country.new",           "args": ["name", "description", "country_type"],                     "desc": "Create a new Country root"},
        "country.open":          {"method": "country.open",          "args": ["country_id"],                                               "desc": "Open an existing Country root"},
        "country.ls":            {"method": "country.ls",            "args": [],                                                           "desc": "List all Country roots"},
        "country.map":           {"method": "country.map",           "args": [],                                                           "desc": "Show structure of active Country"},
        "country.rm":            {"method": "country.rm",            "args": [],                                                           "desc": "Soft-delete the active Country root"},
        "country.name":          {"method": "country.name.add",      "args": ["name", "name_type", "language", "valid_from", "valid_to"],  "desc": "Add a country name (event-sourced)"},
        "country.territory":     {"method": "country.territory.add", "args": ["territory_type", "place_id", "label", "valid_from"],       "desc": "Add a territory reference"},
        "country.capital":       {"method": "country.capital.set",   "args": ["name", "place_id", "capital_type", "valid_from"],          "desc": "Record a capital (event-sourced)"},
        "country.gov":           {"method": "country.gov.set",       "args": ["government_type", "head_of_state", "valid_from"],          "desc": "Record a government form or regime"},
        "country.pop":           {"method": "country.pop.set",       "args": ["value", "year", "unit"],                                   "desc": "Record a population value"},
        "country.econ":          {"method": "country.econ.add",      "args": ["economy_type", "value", "unit", "year"],                                     "desc": "Record an economic datum"},
        "country.sovereignty":   {"method": "country.sovereignty.set","args": ["sovereignty_type", "valid_from", "valid_to", "basis"],                       "desc": "Record sovereignty status (event-sourced)"},
        "country.claim":         {"method": "country.claim.add",      "args": ["claim_type", "target_id", "description", "valid_from"],                      "desc": "Record a territorial or political claim"},
        "country.admin":         {"method": "country.admin.add",      "args": ["target_id", "administration_type", "valid_from"],                           "desc": "Record administrative control over an entity"},
        "country.law":           {"method": "country.law.add",        "args": ["title", "law_type", "status", "valid_from"],                                "desc": "Record a law, treaty, constitution, or decree"},
        "country.law.change":    {"method": "country.law.change",     "args": ["law_id", "change", "new_status", "effective_from"],                         "desc": "Record an immutable law change event"},
        "country.event":         {"method": "country.event.add",      "args": ["event_type", "description", "event_time"],                                  "desc": "Record a country-level historical or political event"},
        "country.corr":          {"method": "country.corr.link",      "args": ["corr_id", "relation", "target_id"],                                         "desc": "Link Country to a CorrespondenceConcept atom"},
        "country.profile":       {"method": "country.profile",        "args": [],                                                                              "desc": "Show structured profile of active Country"},
        "country.timeline":      {"method": "country.timeline",       "args": [],                                                                              "desc": "Show chronological event timeline of active Country"},
        "country.observable":    {"method": "country.observable",     "args": [],                                                                              "desc": "Show externally linked observable atoms"},
        "country.diagnose":      {"method": "country.diagnose",       "args": [],                                                                              "desc": "Diagnose completeness and evidence quality"},
        "country.trace":         {"method": "country.trace",          "args": ["target_id"],                                                                   "desc": "Trace evidence chain for a Country atom"},
        # ── Homonoia (game city model) ────────────────────────────────
        "hom.new":       {"method": "homonoia.new",          "args": ["name", "description"],            "desc": "Create a new Homonoia city root"},
        "hom.open":      {"method": "homonoia.open",         "args": ["homonoia_id"],                    "desc": "Open an existing Homonoia city"},
        "hom.ls":        {"method": "homonoia.ls",           "args": [],                                 "desc": "List all Homonoia city roots"},
        "hom.map":       {"method": "homonoia.map",          "args": [],                                 "desc": "Show structure of active Homonoia city"},
        "hom.rm":        {"method": "homonoia.rm",           "args": [],                                 "desc": "Delete the active Homonoia city root"},
        "hom.district":  {"method": "homonoia.district.add", "args": ["name", "district_type"],          "desc": "Add a district (quarter, ward, zone)"},
        "hom.faction":   {"method": "homonoia.faction.add",  "args": ["name", "faction_type"],           "desc": "Add a social faction or organisation"},
        "hom.law":       {"method": "homonoia.law.add",      "args": ["title", "law_type"],              "desc": "Record a city law or ordinance"},
        "hom.event":     {"method": "homonoia.event.add",    "args": ["description", "event_type"],      "desc": "Record a city event"},
        "hom.profile":   {"method": "homonoia.profile",      "args": [],                                 "desc": "Show full profile of active Homonoia city"},
        "hom.dx":        {"method": "homonoia.diagnose",     "args": [],                                 "desc": "Diagnose structural gaps in active Homonoia city"},
        # ── Cast (fictional character model) ─────────────────────────
        "cs.new":       {"method": "cast.new",          "args": ["name", "identity"],                            "desc": "Create a new Cast character"},
        "cs.open":      {"method": "cast.open",         "args": ["cast_id"],                                     "desc": "Open an existing Cast"},
        "cs.ls":        {"method": "cast.ls",           "args": [],                                              "desc": "List all Cast records"},
        "cs.map":       {"method": "cast.map",          "args": [],                                              "desc": "Show full structure of active Cast"},
        "cs.clone":     {"method": "cast.clone",        "args": ["name"],                                        "desc": "Clone active Cast to a new named cast"},
        "cs.rm":        {"method": "cast.rm",           "args": [],                                              "desc": "Delete the active Cast"},
        "cs.id":        {"method": "cast.identity.set", "args": ["text"],                                        "desc": "Set identity text on active Cast"},
        "cs.look":      {"method": "cast.appear.set",   "args": ["vector"],                                      "desc": "Set appearance vector"},
        "cs.able":      {"method": "cast.ability.set",  "args": ["vector"],                                      "desc": "Set ability vector"},
        "cs.adorn":     {"method": "cast.adorn.add",    "args": ["item"],                                        "desc": "Add an adornment item"},
        "cs.skill":     {"method": "cast.skill.add",    "args": ["name", "level"],                               "desc": "Add a skill with level (0–1)"},
        "cs.own":       {"method": "cast.possess.add",  "args": ["item"],                                        "desc": "Add a possession"},
        "cs.pos":       {"method": "cast.pos.set",      "args": ["position"],                                    "desc": "Set social position"},
        "cs.feel":      {"method": "cast.emotion.add",  "args": ["verb", "obj", "intensity"],                    "desc": "Add an emotion (verb + object + intensity)"},
        "cs.wound":     {"method": "cast.wound.add",    "args": ["event", "depth"],                              "desc": "Record a formative wound event"},
        "cs.policy":    {"method": "cast.policy.add",   "args": ["logic"],                                       "desc": "Add a behavioural policy"},
        "cs.rule":      {"method": "cast.rule.add",     "args": ["text", "strength"],                            "desc": "Add a hard behavioural rule"},
        "cs.trait":     {"method": "cast.trait.set",    "args": ["trait"],                                       "desc": "Set trait vector (energy/process/response/trust/flexibility)"},
        "cs.state":     {"method": "cast.state.set",    "args": ["state"],                                       "desc": "Record current runtime state"},
        "cs.mask":      {"method": "cast.mask.add",     "args": ["presentation", "hides"],                       "desc": "Add a social mask"},
        "cs.secret":    {"method": "cast.secret.add",   "args": ["content", "protection"],                       "desc": "Add a secret with protection score"},
        "cs.output":    {"method": "cast.output.add",   "args": ["modality", "content"],                         "desc": "Record an observable output"},
        "cs.conflict":  {"method": "cast.conflict.add", "args": ["a", "b", "tension"],                           "desc": "Record a tension between two values/drives"},
        "cs.shadow":    {"method": "cast.shadow.add",   "args": ["kind", "content"],                             "desc": "Add a shadow (suppressed/projected/disowned) element"},
        "cs.bond":      {"method": "cast.bond.add",     "args": ["target_id", "types", "trust"],                 "desc": "Create a relational bond to another cast atom"},
        "cs.bond.up":   {"method": "cast.bond.update",  "args": ["bond_id", "delta"],                            "desc": "Append a delta event to an existing bond"},
        "cs.fate":      {"method": "cast.fate.set",     "args": ["event", "certainty"],                          "desc": "Record a destined event"},
        "cs.calling":   {"method": "cast.calling.set",  "args": ["mission"],                                     "desc": "Record the character's calling/mission"},
        "cs.role":      {"method": "cast.role.set",     "args": ["role"],                                        "desc": "Assign a narrative role (e.g. Proppian function)"},
        "cs.myth":      {"method": "cast.myth.set",     "args": ["archetype", "symbol"],                         "desc": "Attach a mythic archetype and symbol"},
        "cs.arc":       {"method": "cast.arc.add",      "args": ["arc_type", "initial_state", "conflict_state"], "desc": "Define a character arc (growth/fall/flat/corruption/healing)"},
        "cs.react":     {"method": "cast.react",        "args": ["event"],                                       "desc": "Simulate Cast's reaction to an event"},
        "cs.dx":        {"method": "cast.diagnose",     "args": [],                                              "desc": "Diagnose pressure and arc-readiness of active Cast"},
        # ── Geo (geospatial model) ────────────────────────────────────
        "ge.new":       {"method": "geo.new",           "args": ["title", "description", "coordinate_system"],   "desc": "Create a new Geo root"},
        "ge.open":      {"method": "geo.open",          "args": ["geo_id"],                                      "desc": "Open an existing Geo root"},
        "ge.ls":        {"method": "geo.ls",            "args": [],                                              "desc": "List all Geo roots"},
        "ge.map":       {"method": "geo.map",           "args": [],                                              "desc": "Show full structure of active Geo"},
        "ge.rm":        {"method": "geo.rm",            "args": [],                                              "desc": "Delete the active Geo root"},
        "ge.coord":     {"method": "geo.coord.add",     "args": ["target_id", "lat", "lon", "alt"],              "desc": "Add a coordinate point to a place"},
        "ge.place":     {"method": "geo.place.add",     "args": ["name", "place_type"],                          "desc": "Add a named place"},
        "ge.state":     {"method": "geo.place.state",   "args": ["place_id", "state"],                           "desc": "Record a place state (event-sourced)"},
        "ge.feat":      {"method": "geo.feature.add",   "args": ["place_id", "feature_type"],                    "desc": "Add a spatial feature to a place"},
        "ge.obs":       {"method": "geo.observe.add",   "args": ["target_id", "method"],                         "desc": "Record an observation of a spatial target"},
        "ge.event":     {"method": "geo.event.add",     "args": ["place_id", "event_type", "description"],       "desc": "Record a geo event at a place"},
        "ge.layer":     {"method": "geo.layer.add",     "args": ["label"],                                       "desc": "Create a named spatial data layer"},
        "ge.snap":      {"method": "geo.snapshot.add",  "args": ["label", "captured_at"],                        "desc": "Capture a temporal snapshot of spatial members"},
        "ge.link":      {"method": "geo.connect",       "args": ["from_id", "to_id", "relation"],                "desc": "Create a typed spatial connection between two atoms"},
        "ge.affine":    {"method": "geo.affine.add",    "args": ["src_sys", "dst_sys", "matrix"],                "desc": "Register an affine transform between coordinate systems"},
        "ge.clone":     {"method": "geo.clone",         "args": ["place_id", "label"],                           "desc": "Clone a place as alternate/disputed/fictional"},
        "ge.trans":     {"method": "geo.transition.add","args": ["target_id", "transition_type", "occurred_at"], "desc": "Record a spatial state transition (event-sourced)"},
        "ge.nearby":    {"method": "geo.nearby",        "args": ["place_id", "depth"],                           "desc": "Find connected places within a given depth"},
        "ge.path":      {"method": "geo.path",          "args": ["from_id", "to_id"],                            "desc": "Find shortest path between two spatial atoms"},
        "ge.reveal":    {"method": "geo.reveal",        "args": ["place_id"],                                    "desc": "Reveal a hidden place (event-sourced)"},
        "ge.hist":      {"method": "geo.history",       "args": [],                                              "desc": "Show temporal event history of active Geo"},
        "ge.time":      {"method": "geo.time.rebuild",  "args": [],                                              "desc": "Rebuild the temporal index of active Geo"},
        "ge.dx":        {"method": "geo.diagnose",      "args": [],                                              "desc": "Diagnose coordinate gaps and orphaned connections"},
        # ── Synthesis (qualitative analysis) ─────────────────────────
        "sy.new":       {"method": "synth.new",          "args": ["title"],                                       "desc": "Create a new Synthesis root"},
        "sy.open":      {"method": "synth.open",         "args": ["synth_id"],                                    "desc": "Open an existing Synthesis"},
        "sy.ls":        {"method": "synth.ls",           "args": [],                                              "desc": "List all Synthesis roots"},
        "sy.map":       {"method": "synth.map",          "args": [],                                              "desc": "Show structure of active Synthesis"},
        "sy.rm":        {"method": "synth.rm",           "args": [],                                              "desc": "Delete the active Synthesis root"},
        "sy.src":       {"method": "synth.source.add",   "args": ["ref_id"],                                      "desc": "Index an atom as a source"},
        "sy.code":      {"method": "synth.code.add",     "args": ["label"],                                       "desc": "Create a qualitative code label"},
        "sy.theme":     {"method": "synth.theme.add",    "args": ["label"],                                       "desc": "Create a theme grouping one or more codes"},
        "sy.interp":    {"method": "synth.interp.add",   "args": ["stance", "theme_id"],                          "desc": "Record an interpretation grounded in a theme"},
        "sy.claim":     {"method": "synth.claim.add",    "args": ["content"],                                     "desc": "Assert a claim backed by interpretations/evidence"},
        "sy.thread":    {"method": "synth.thread.new",   "args": ["label"],                                       "desc": "Create a named reasoning thread"},
        "sy.step":      {"method": "synth.thread.add",   "args": ["thread_id", "ref_id"],                         "desc": "Append an atom as the next step in a thread"},
        "sy.trace":     {"method": "synth.trace",        "args": ["claim_id"],                                    "desc": "Trace a claim back to raw sources"},
        # ── Presentation (slide/layout model) ────────────────────────
        "pr.new":       {"method": "pres.new",           "args": ["title"],                                       "desc": "Create a new Presentation root"},
        "pr.open":      {"method": "pres.open",          "args": ["pres_id"],                                     "desc": "Open an existing Presentation"},
        "pr.ls":        {"method": "pres.ls",            "args": [],                                              "desc": "List all Presentations"},
        "pr.list":      {"method": "pres.list",          "args": [],                                              "desc": "Show structure of active Presentation"},
        "pr.rm":        {"method": "pres.rm",            "args": [],                                              "desc": "Delete the active Presentation"},
        "pr.deck":      {"method": "pres.deck.add",      "args": ["title"],                                       "desc": "Add a slide-deck section"},
        "pr.frame":     {"method": "pres.frame.add",     "args": ["deck_id", "title"],                            "desc": "Add a frame/slide to a deck"},
        "pr.region":    {"method": "pres.region.add",    "args": ["frame_id", "label"],                           "desc": "Add a layout region within a frame"},
        "pr.node":      {"method": "pres.node.add",      "args": ["region_id", "ref_id"],                         "desc": "Attach a content reference node to a region"},
        # ── Aggregation (grouping and statistical summary) ────────────
        "ag.new":       {"method": "agg.new",            "args": ["title", "corpus_id"],                          "desc": "Create a new Aggregation root linked to a corpus atom"},
        "ag.open":      {"method": "agg.open",           "args": ["agg_id"],                                      "desc": "Open an existing Aggregation"},
        "ag.ls":        {"method": "agg.ls",             "args": [],                                              "desc": "List all Aggregations"},
        "ag.list":      {"method": "agg.list",           "args": [],                                              "desc": "Show structure of active Aggregation"},
        "ag.rm":        {"method": "agg.rm",             "args": [],                                              "desc": "Delete the active Aggregation"},
        "ag.unit":      {"method": "agg.unit.add",       "args": ["ref_id"],                                      "desc": "Index an atom as an aggregation unit"},
        "ag.group":     {"method": "agg.group.add",      "args": ["label"],                                       "desc": "Create a labelled group"},
        "ag.measure":   {"method": "agg.measure.add",    "args": ["group_id", "key", "value"],                    "desc": "Attach a key/value statistic to a group"},
        "ag.analysis":  {"method": "agg.analysis.add",   "args": ["from_id", "to_id", "score"],                   "desc": "Record a directed relation between two groups"},
        "ag.hier":      {"method": "agg.hier.add",       "args": ["label"],                                       "desc": "Create a hierarchy node"},
        # ── Map (cartographic depiction model) ───────────────────────
        "mp.new":    {"method": "map.new",            "args": ["title", "description"],                                          "desc": "Create a new Map root"},
        "mp.open":   {"method": "map.open",           "args": ["map_id"],                                                        "desc": "Open an existing Map root"},
        "mp.ls":     {"method": "map.ls",             "args": [],                                                                "desc": "List all Map roots"},
        "mp.map":    {"method": "map.map",            "args": [],                                                                "desc": "Show structure of active Map"},
        "mp.rm":     {"method": "map.rm",             "args": [],                                                                "desc": "Soft-delete the active Map root"},
        "mp.ed":     {"method": "map.edition.add",    "args": ["title", "maker", "created_at", "coordinate_system"],             "desc": "Add a map edition (source document)"},
        "mp.feat":   {"method": "map.feature.add",    "args": ["edition_id", "name", "feature_type"],                           "desc": "Add a cartographic feature to an edition"},
        "mp.geom":   {"method": "map.geometry.add",   "args": ["feature_id", "geometry_type", "coordinates"],                   "desc": "Add geometry to a feature"},
        "mp.label":  {"method": "map.label.add",      "args": ["edition_id", "target_id", "text", "language"],                  "desc": "Add a label to a map atom"},
        "mp.proj":   {"method": "map.projection.add", "args": ["edition_id", "target_system", "method"],                        "desc": "Add a cartographic projection transform"},
        "mp.ground": {"method": "map.ground",         "args": ["src_id", "dst_id", "relation", "source_id"],                    "desc": "Record a map-local grounding claim"},
        "mp.snap":   {"method": "map.snapshot.add",   "args": ["label", "captured_at"],                                         "desc": "Add a temporal snapshot of the map"},
        "mp.trans":  {"method": "map.transition.add", "args": ["target_id", "transition_type", "description", "occurred_at"],   "desc": "Record a cartographic state transition"},
        "mp.hist":   {"method": "map.history",        "args": [],                                                               "desc": "Show temporal event history of active Map"},
        "mp.time":   {"method": "map.time.rebuild",   "args": [],                                                               "desc": "Rebuild the temporal index of active Map"},
        "mp.eval":   {"method": "map.eval",           "args": ["target_id", "target_type", "confidence"],                       "desc": "Event-sourced re-evaluation of a map atom"},
        "mp.trace":  {"method": "map.trace",          "args": ["target_id"],                                                    "desc": "Trace provenance and evidence chain for a map atom"},
        "mp.dx":     {"method": "map.diagnose",       "args": [],                                                               "desc": "Diagnose cartographic quality and modeling gaps"},
        # Map — full-name aliases (map.* prefix)
        "map.new":          {"method": "map.new",            "args": ["title", "description"],                                        "desc": "Create a new Map root"},
        "map.open":         {"method": "map.open",           "args": ["map_id"],                                                      "desc": "Open an existing Map root"},
        "map.ls":           {"method": "map.ls",             "args": [],                                                              "desc": "List all Map roots"},
        "map.show":         {"method": "map.show",           "args": [],                                                              "desc": "Show structure of active Map"},
        "map.rm":           {"method": "map.rm",             "args": [],                                                              "desc": "Soft-delete the active Map root"},
        "map.ed":           {"method": "map.edition.add",    "args": ["title", "maker", "created_at", "coordinate_system"],          "desc": "Add a map edition (source document)"},
        "map.edition":      {"method": "map.edition.add",    "args": ["title", "maker", "created_at", "coordinate_system"],          "desc": "Add a map edition (alias: map.ed)"},
        "map.feat":         {"method": "map.feature.add",    "args": ["edition_id", "name", "feature_type"],                        "desc": "Add a depicted feature to an edition"},
        "map.geom":         {"method": "map.geometry.add",   "args": ["feature_id", "geometry_type", "coordinates"],                "desc": "Add geometry to a feature"},
        "map.label":        {"method": "map.label.add",      "args": ["edition_id", "target_id", "text", "language"],               "desc": "Add label text to a map atom"},
        "map.proj":         {"method": "map.projection.add", "args": ["edition_id", "target_system", "method"],                     "desc": "Add a cartographic projection transform"},
        "map.ground":       {"method": "map.ground",         "args": ["src_id", "dst_id", "relation", "source_id"],                 "desc": "Record a map-local grounding claim"},
        "map.snap":         {"method": "map.snapshot.add",   "args": ["label", "captured_at"],                                      "desc": "Add a temporal snapshot of the map"},
        "map.trans":        {"method": "map.transition.add", "args": ["target_id", "transition_type", "description", "occurred_at"],"desc": "Record a cartographic state transition"},
        "map.history":      {"method": "map.history",        "args": [],                                                             "desc": "Show temporal event history of active Map"},
        "map.timeview":     {"method": "map.history",        "args": [],                                                             "desc": "Alias for map.history"},
        "map.time.rebuild": {"method": "map.time.rebuild",   "args": [],                                                             "desc": "Rebuild the temporal index of active Map"},
        "map.eval":         {"method": "map.eval",           "args": ["target_id", "target_type", "confidence"],                    "desc": "Event-sourced re-evaluation of a map atom"},
        "map.diagnose":     {"method": "map.diagnose",       "args": [],                                                             "desc": "Diagnose cartographic quality and modeling gaps"},
        "map.trace":        {"method": "map.trace",          "args": ["target_id"],                                                  "desc": "Trace provenance and evidence chain for a map atom"},
        # ── World ─────────────────────────────────────────────────────
        "wd.new":    {"method": "world.new",         "args": ["title", "description", "time_type"], "desc": "Create a new World"},
        "wd.open":   {"method": "world.open",        "args": ["world_id"],                          "desc": "Open an existing World"},
        "wd.ls":     {"method": "world.ls",          "args": [],                                    "desc": "List all Worlds"},
        "wd.map":    {"method": "world.map",         "args": [],                                    "desc": "Show full topology of active World"},
        "wd.rm":     {"method": "world.rm",          "args": [],                                    "desc": "Delete the active World root"},
        "wd.place":  {"method": "world.place.add",   "args": ["name", "place_type", "category"],   "desc": "Add a place to the active World"},
        "wd.state":  {"method": "world.place.state", "args": ["place_id", "state"],                "desc": "Record a place state change"},
        "wd.obj":    {"method": "world.object.add",  "args": ["place_id", "name"],                 "desc": "Add an object to a place"},
        "wd.prop":   {"method": "world.prop.add",    "args": ["place_id", "item"],                 "desc": "Add a prop/suggester to a place"},
        "wd.col":    {"method": "world.collect.add", "args": ["label", "collection_type"],         "desc": "Create a collection"},
        "wd.put":    {"method": "world.collect.put", "args": ["collect_id", "member_id"],          "desc": "Add a member to a collection"},
        "wd.link":   {"method": "world.connect",     "args": ["from_id", "to_id", "connection_type"], "desc": "Connect two places"},
        "wd.portal": {"method": "world.portal.add",  "args": ["place_id", "direction"],            "desc": "Add a portal to a place"},
        "wd.law":    {"method": "world.law.add",     "args": ["law_type", "content"],              "desc": "Add a law to the World"},
        "wd.amend":  {"method": "world.law.change",  "args": ["law_id", "new_state"],              "desc": "Record a law state change"},
        "wd.hide":   {"method": "world.hidden.add",  "args": ["hint"],                             "desc": "Add a hidden layer element"},
        "wd.event":  {"method": "world.event",       "args": ["description", "intensity"],         "desc": "Record a world event"},
        "wd.dx":     {"method": "world.diagnose",    "args": [],                                   "desc": "Diagnose tensions in the active World"},
        # ── Session Instance Layer ────────────────────────────────────────────
        "instance.mount":   {"method": "instance.mount",   "args": ["model", "slot"],       "desc": "Mount a concept model instance into this space"},
        "instance.join":    {"method": "instance.join",    "args": ["concept_id", "slot"],  "desc": "Borrow an external instance into this space"},
        "instance.focus":   {"method": "instance.focus",   "args": ["slot"],                "desc": "Route a model class to the given slot"},
        "instance.blur":    {"method": "instance.blur",    "args": ["model"],               "desc": "Clear routing focus for a model class"},
        "instance.bind":    {"method": "instance.bind",    "args": ["slot", "atom"],        "desc": "Link a mounted instance to its ontology atom (instance_of)"},
        "instance.ls":      {"method": "instance.ls",      "args": [],                      "desc": "List all instances in this space"},
        "instance.unmount": {"method": "instance.unmount", "args": ["slot"],                "desc": "Remove a slot from this space (instance is not deleted)"},
        # ── Record (schema-free) ─────────────────────────────────────────
        "rec.new": {"method": "rec.new", "args": ["type"],          "desc": "Create a record atom (type=<concept> content=<text> <attr>=<val> …)"},
        "rec.set": {"method": "rec.set", "args": ["key", "attr", "val"], "desc": "Set an attribute on a record"},
        "rec.idx": {"method": "rec.idx", "args": ["key", "sets"],   "desc": "Add record to index sets (comma-separated set names)"},
        "rec.get": {"method": "rec.get", "args": ["key"],           "desc": "Get record with all attributes"},
        "rec.ls":  {"method": "rec.ls",  "args": [],                "desc": "List records: rec.ls [type=<t>] [in_set=<s>]"},
        "rec.sum": {"method": "rec.sum", "args": ["attr"],          "desc": "Sum a numeric attribute: rec.sum attr=amount [in_set=<s>] [type=<t>]"},
        "rec.rm":  {"method": "rec.rm",  "args": ["key"],           "desc": "Delete a record"},
        # ── Table (schema-first, CSV/RDB-compatible) ──────────────────
        "table.new":     {"method": "table.new",     "args": ["name", "cols"],       "desc": "Create a table: table.new name=<n> cols=\"col:type,...\" [description=<text>]"},
        "table.get":     {"method": "table.get",     "args": ["table"],              "desc": "Show table schema and row count"},
        "table.rm":      {"method": "table.rm",      "args": ["table"],              "desc": "Drop a table and all its rows (irreversible)"},
        "table.col.add": {"method": "table.col.add", "args": ["table", "name"],      "desc": "Add a column: table.col.add table=<t> name=<col> [type=text|int|float|bool|date]"},
        "table.col.ls":  {"method": "table.col.ls",  "args": ["table"],              "desc": "List columns of a table in ordinal order"},
        "table.row.add": {"method": "table.row.add", "args": ["table"],              "desc": "Insert a row: table.row.add table=<t> col1=val1 col2=val2 ..."},
        "table.row.get": {"method": "table.row.get", "args": ["table", "row"],       "desc": "Retrieve a single row by key"},
        "table.row.rm":  {"method": "table.row.rm",  "args": ["table", "row"],       "desc": "Remove a single row"},
        "table.ls":      {"method": "table.ls",      "args": ["table"],              "desc": "List rows: table.ls table=<t> [limit=100]"},
        "table.export":  {"method": "table.export",  "args": ["table"],              "desc": "Export table as CSV text"},
        "table.import":  {"method": "table.import",  "args": ["table"],              "desc": "Import CSV: table.import table=<t> csv=\"header\\nrow1\\nrow2\""},
        # ── Lens (source scanner + concept-model projection engine) ──
        "lens":      {"method": "lens.scan", "args": ["src", "follow", "depth"], "desc": "Scan a set/tree and list compatible concept model targets: lens src=<set|key> [follow=<rel>] [depth=2]"},
        "lens.cast": {"method": "lens.cast", "args": ["signpost", "into", "model"], "desc": "Project scanned nodes into chosen concept model: lens.cast signpost=1 [into=<name>]"},
        # ── Ref slots ($who / $where / $why / …) ─────────────────────
        "ref.set": {"method": "ref.set", "args": ["dim", "target"], "desc": "Set typed context variable: ref.set who <atom>"},
        "ref.get": {"method": "ref.get", "args": ["dim"],           "desc": "Get typed context variable(s): ref.get [dim]"},
        # ── Sys ───────────────────────────────────────────────────────
        "status": {"method": "sys.status.full", "args": [],    "desc": "System status: memory, session, focus, JCL queue"},
        "ping":   {"method": "sys.ping",    "args": [],        "desc": "Consciousness liveness check"},
        "cog":    {"method": "sys.cogito",  "args": [],        "desc": "Full self-awareness pulse"},
        "hist":   {"method": "sys.history", "args": [],        "desc": "Recent atom stream"},
        "ls":     {"method": "sys.ls",      "args": ["limit"], "desc": "List last N atoms"},
        "passwd": {"method": "sys.passwd",  "args": [],        "desc": "Change your passphrase"},
    }

    # ── Concept-model prefix → group name ────────────────────────────────────
    # Commands whose keys start with one of these prefixes belong to that
    # concept model and are hidden from the default help listing.
    CONCEPT_PREFIXES: dict = {
        "n.":        "note",
        "fn.":       "fieldnote",
        "sv.":       "survey",
        "cp.":       "cockpit",
        "log.":      "log",
        "wb.":       "whiteboard",
        "hum.":      "human",
        "corr.":     "correspondence",
        "ft.":       "fact",
        "cur.":      "curation",
        "intel.":    "intelligence",
        "country.":  "country",
        "hom.":      "homonoia",
        "cs.":       "cast",
        "ge.":       "geo",
        "sy.":       "synthesis",
        "pr.":       "presentation",
        "ag.":       "aggregation",
        "mp.":       "map",
        "map.":      "map",
        "wd.":       "world",
        "soma.":     "soma",
        "engram.":   "engram",
        "eidolon.":  "eidolon",
        "operator.": "operator",
        "lens.":     "lens",
    }

    @classmethod
    def _get_concept_group(cls, cmd: str) -> "str | None":
        for prefix, group in cls.CONCEPT_PREFIXES.items():
            if cmd.startswith(prefix):
                return group
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
    CONCEPT_LABELS: dict = {
        "note":           "Structured notes and documents with sections, chapters, and versioned edits",
        "fieldnote":      "Field observation logs with project, region, and season context",
        "survey":         "Survey forms — questions, options, respondents, and response recording",
        "cockpit":        "Dimensional lens navigator with focal point locking and beacon trail",
        "log":            "Exploration log — checkpoints, annotations, and replay",
        "whiteboard":     "Concept pinboard for ideas under active exploration",
        "human":          "Evidence-based actor records — bonds, assessments, timeline, merge detection",
        "correspondence": "Cross-system conceptual mapping with evidence provenance and dispute tracking",
        "fact":           "Fact collections — direct facts, claims, absences, inferred facts, source tracking",
        "curation":       "Premise-bound view construction and conflict-fold resolution",
        "intelligence":   "Decision-cycle orchestration: requirements → gaps → tasking → assessment → recommendation",
        "country":        "Evidence-grounded country / polity / entity records with law and event sourcing",
        "homonoia":       "Game city model — districts, factions, laws, and events for Homonoia (ὁμόνοια), the city where everyone lives in harmony",
        "cast":           "Fictional character model — identity, emotions, wounds, bonds, masks, secrets, arcs, and reaction simulation",
        "geo":            "Geospatial model — places, features, observations, events, connections, and temporal snapshots",
        "synthesis":      "Qualitative analysis — sources, codes, themes, interpretations, claims, and reasoning threads",
        "presentation":   "Slide/layout model — decks, frames, layout regions, and cross-universe content reference nodes",
        "aggregation":    "Grouping and statistical summary — units, groups, measures, directed analysis, and hierarchies",
        "map":            "Cartographic depiction model — editions, features, labels, projections, temporal snapshots",
        "world":          "Fictional / narrative world builder — places, objects, laws, portals, hidden layers",
        "soma":           "Mech frame — slot constraints, equipment, capacity budget, and damage state (game, under development)",
        "engram":         "Psyche / memory carrier — utterances, resonance bonds, and message generation (game, under development)",
        "eidolon":        "Dark outer world surrounding Homonoia — invisible, malevolent realm whose topology can be mapped (game, under development)",
        "operator":       "Tactician terminal — stateless combat resolution (game, under development)",
        "lens":           "Source scanner and concept-model projection engine — scan sets/trees, match importable models, cast into tables and other structures",
    }

    # ── Auto-augmentation from ConceptRegistry ───────────────────────────────
    # Populated lazily on first use; never overwrites hand-written entries.
    _augmented: bool = False

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
        for prefix, group in registry.get_concept_prefixes().items():
            if prefix not in cls.CONCEPT_PREFIXES:
                cls.CONCEPT_PREFIXES[prefix] = group
        for name, label in registry.get_concept_labels().items():
            if name not in cls.CONCEPT_LABELS:
                cls.CONCEPT_LABELS[name] = label
        cls._augmented = True

    @classmethod
    def _ensure_augmented(cls) -> None:
        """Augment from the active ConceptRegistry if not yet done."""
        if cls._augmented:
            return
        try:
            from lib.akasha.concepts.registry import get_active
            reg = get_active()
            if reg is not None:
                cls.augment_from_registry(reg)
        except ImportError:
            cls._augmented = True  # don't retry if import fails

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
            if _sub in cls.COMMAND_SPECS:
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

        if cmd == "grp.ls":
            return cls._create_payload("grp.ls", {"group_id": args[0] if args else ""}, session_token)
        if cmd == "grp.new":
            gid = args[0] if args else ""; adm = args[1] if len(args) > 1 else ""
            return cls._create_payload("grp.new", {"group_id": gid, "admin_id": adm}, session_token)
        if cmd == "grp.add":
            gid = args[0] if args else ""; mid = args[1] if len(args) > 1 else ""
            return cls._create_payload("grp.add", {"group_id": gid, "member_id": mid}, session_token)
        if cmd == "grp.rm":
            gid = args[0] if args else ""; mid = args[1] if len(args) > 1 else ""
            return cls._create_payload("grp.rm", {"group_id": gid, "member_id": mid}, session_token)
        if cmd == "grp.lib":
            gid = args[0] if args else ""; act = args[1] if len(args) > 1 else ""; mid = args[2] if len(args) > 2 else ""
            return cls._create_payload("grp.lib", {"group_id": gid, "action": act, "member_id": mid}, session_token)
        if cmd == "grp.del":
            return cls._create_payload("grp.del", {"group_id": args[0] if args else ""}, session_token)

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

        # Special handling for 'exp' — explore with key=value filter syntax
        # exp ns=myth  |  exp set=deity  |  exp type=rec  |  exp icarus%  |  exp myth
        if cmd == "exp":
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

        if cmd not in cls.COMMAND_SPECS:
            return None

        spec = cls.COMMAND_SPECS[cmd]
        method = spec["method"]
        expected = spec.get("args", [])

        params = {}
        for i, arg_name in enumerate(expected):
            if i < len(args):
                # Last declared arg absorbs all remaining tokens
                params[arg_name] = " ".join(args[i:]) if i == len(expected) - 1 else args[i]

        return cls._create_payload(method, params, session_token)

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
