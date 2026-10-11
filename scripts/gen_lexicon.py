#!/usr/bin/env python3
"""
gen_lexicon.py — author the relation / namespace definition layer as `.ak`.

Every relation and namespace used in the ontology is registered as a first-class, self-describing
atom (`reldef:<rel>` / `nsdef:<ns>`) the reader (lib/akasha/lexicon.py) resolves and surfaces.

It runs over BOTH pack roots — the platform's `ontology/` and the application's packs root — and
names nothing of the application's: the application's curated descriptions, salient-relation
profiles and is-a spines are DATA in its lexicon declaration (`config/lexicon.json` under the
application root; platform-spec "Lexicon declaration").

Output:
  ontology/lexicon/                     the platform's pack (autoloaded, loads first)
    00_namespaces_core.ak   nsdef:<ns> for every namespace a platform autoload pack uses, plus the
    01_relations_core.ak    reldef:<rel> for every relation one uses, plus the curated list below
  <application packs>/<pack>/           the application's lexicon pack (`pack` in its declaration;
    00_namespaces.ak        registered first, autoload): what the application's autoload packs and
    01_relations.ak         curated list add beyond the platform's,
    02_salient.ak           and its salient-relation profiles + is-a spines
  <root>/<pack>/_lexicon.ak             per non-autoloaded pack: what it introduces beyond both

Idempotent: atoms are content-addressed; re-running is safe. Descriptions follow
`"<full-spelling> — <meaning>."` so the reader's edge/namespace label is clean.
"""
import glob
import json
import os
import shlex
from collections import defaultdict

import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lib.akasha.api import reserved as _reserved  # noqa: E402

ONT = os.path.join(ROOT, "ontology")
APP_ONT = _reserved.root("packs")
APP_DECL = _reserved.root("lexicon")


def app_declaration() -> dict:
    """The application's lexicon declaration, or {} when there is none (the platform alone)."""
    try:
        with open(APP_DECL, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}

# ── the PLATFORM's curated descriptions: the relations and namespaces the platform's own code and
# packs use. The application's live in its lexicon declaration (`config/lexicon.json` under the
# application root). Head before the em-dash is the readable edge label the explorer shows.
CORE_RELS = {
    'sys:is_a': 'is a — the source is a kind or instance of the target (taxonomic type).',
    'sys:part_of': 'part of — the source is a component or member of the target whole.',
    'sys:antonym': 'antonym — the two concepts are opposite in meaning.',
    'sys:synonym': 'synonym — the two concepts share the same meaning.',
    'sys:same_as': 'same as — the two atoms denote the same thing.',
    'sys:associated_with': 'associated with — the source is commonly associated with the target.',
    'sys:refers_to': 'refers to — the source atom refers to the target proto-word or concept.',
    'sys:in_world': 'in world — the source (e.g. a society / dialogue space) is placed inside the target world (crosses a space with a worldview).',
    'society:connected': 'connected — the source society is connected to the target research bench; its admitted agents operate on the bench per their responsible:operator:<family> grants.',
    'cronon:at': 'cronon at — the source event atom is located at the target cronon (Akasha-Time position); the cronon does not execute the event.',
    'cronon:maps_to': 'cronon maps to — the source cronon maps to the target external temporal frame (the mapping is external to the cronon; temporal relativity).',
    'cronon:follows': 'cronon follows — the source cronon is the next Akasha-Time position after the target (a coordinate order, not execution).',
    'cronon:sync': 'sync — the source WORLD coordinate is synchronized with the target WORKBENCH coordinate (G4: a link joins world and workbench time only; a workflow/branch coordinate is never synced).',
    'cronon:executes': "executes — the source WORKBENCH coordinate (mode=execution) carried out the target workflow plan position (the entry key it read); a step's executions are the bench coordinates that execute it (a Set, not a stored list).",
    'cronon:rehearses': 'rehearses — the source WORKBENCH coordinate (mode=thought) rehearsed the target workflow plan position without leaving a footprint (wf.advance mode=thought, a rewind/branch/plan revision); rehearsal is preserved beside execution and stays distinguishable.',
    'cronon:forked_from': "forked from — the source workflow branch's first coordinate was forked from the target parent coordinate (wf.branch); the fork link stays on the branch clocks.",
    'bench:superseded_by': 'superseded by — the source (new) bench artifact — a model identity, a frozen frame, a metrics atom, or a promotion record — supersedes the target (old) one after a re-train changed the file/corpus; the old atom is retained (immutable per file, reachable for audit) with the alias re-pointed to the new content (A46).',
    'exec:covers': 'covers — the source execution membrane (a dispatched workflow run) covers the target workflow entry atom (§4.7 sync granularity: one exec record over a run of entries).',
    'wf:superseded_by': 'superseded by — the source (new) workflow entry atom supersedes the target (old) one after a reload replaced a changed .ak line; the old atom is retained (history is knowledge, reachable for rollback) with the alias re-pointed to the new content (A43).',
    'wf:retired_by': 'retired by — the source workflow entry atom was retired because a shorter reload no longer wrote its position; it is kept (linked to the target workflow head) but excluded from the active script and wf.advance until a longer reload re-activates it (A43).',
    'deviates_from': 'deviates from — the source deviation atom (a fact: actual diverged from plan during an execution) points at the target plan entry it deviated from (B1 §A3).',
    'observed_in': 'observed in — the source deviation atom was observed in the target execution coordinate (the bench coordinate the divergence happened at; coordinate = Set membership, no cronon:at) (B1 §A3).',
    'evidenced_by': "evidenced by — the source claim atom is evidenced by the target atom (an execution coordinate, an observation, or an evaluation row); a claim's status is derived from whether its evidence resolves and holds (B1 §A6).",
    'sys:hit_of': 'hit of — the source access event records a hit on the target concept (pulse analytics; the event rides on the real concept seen).',
    'sys:hit_prev': 'hit prev — the source access event follows the target event in the same visit (pulse analytics clickpath edge).',
    'society:decider': 'decider — the target cast is the designated responsible decision-maker for the source society (coworking governance anchor).',
    'society:workflow': 'workflow — the source society is bound to the target workflow root chronon; the society IS its workflow (society ≡ workflow), described in the chronon network.',
    'society:now': "now — the target chronon is a current frontier of the source society's chronon network (Akasha Time's present); a society may hold several frontiers (branches).",
    'responsible:chairman': 'chairman (進行役) — the target agent is responsible for progress in the source society; holds the two admin-delegated powers (admit casts, set responsibles) for that society. Generalises society:decider.',
    'responsible:scribe': 'scribe (記録役) — the target agent is responsible for the record of the source society and decides chronon granularity (who may seal).',
    'responsible:broadcaster': 'broadcaster (広報役) — the target agent is responsible for outward publication of the source society (society.broadcast / the public gate).',
    'responsible:host': 'host (司会) — the target agent (cast) is the MC/host of the source talk-show society: it frames each segment (the ネタ) and invites the panel; the anchor role of a broadcast program.',
    'chronon:next': 'next — the source chronon is succeeded by the target chronon (temporal succession; forward = future, reverse = past; multiple successors = branches / alternative futures).',
    'chronon:mutates': 'mutates — the source chronon is a variation/derivation of the target chronon (records HOW the state changed, orthogonal to THAT it advanced).',
    'chronon:of': 'of — the source chronon belongs to the target society (chronon:<sid>:<id> → society:<sid>).',
    'agent:as': "as — the source agent acts AS the target cast (the agent's persona side of the cast×society binding).",
    'agent:in': 'in — the source agent is an agent IN the target society (the society side of the binding).',
    'agent:state': "state — the source agent's per-workflow state is held on the target state atom (the reserved CSL-state seam: state lives on the agent, not in CSL; keyed by workflow).",
    'lex:bridge': "bridge — the source foreign-language proto-word bridges to the target English proto-word (same lemma/sense): the one interlingual link that lets a non-English atom reuse the English graph's links and sets. Bridge the proto-words only; traversal reuses everything downstream.",
    'specializes': 'specializes — the source is a more specific sense of the target lemma or concept; a lexical/sense subsumption and therefore a kind of is-a (see reldef:specializes sys:is_a reldef:sys:is_a).',
    'thesaurus:related': 'related — links two concepts that share meaning (thesaurus relation).',
    'thesaurus:antonym': 'antonym — the two words are opposite in sense.',
    'calc:associated_with': 'associated with — a computed or curated association between two atoms.',
    'source:supplied_by': 'supplied by — the source item/pool/stream was supplied by the target external source. A provenance edge, not a claim.',
    'source:acquired_by': 'acquired by — the target is the recorded acquisition event that created this source item (when/how it was obtained).',
    'source:in_pool': 'in pool — the source item is a member of the target Source Pool (the eligible sampling frame).',
    'source:pool_of': 'pool of — the Source Pool draws its members from the target external source.',
    'source:derived_from': 'derived from — the target is the earlier version this pool descends from, or the stream this snapshot was cut from (never a rewrite of history).',
    'source:samples_from': 'samples from — the source laboratory/experiment selects its samples from the target Source Pool (the visible sampling frame).',
    'source:observes_from': 'observes from — the source laboratory observes from the target Source Stream (continuous external observations).',
    'source:snapshot_of': 'snapshot of — the frozen snapshot is a reproducible time-bounded window of the target stream.',
    'source:in_stream': 'in stream — the observation belongs to the target Source Stream, ordered by Akasha Time.',
    'source:authored_scope': "authored scope — the source laboratory's evidence is the target explicitly authored set (no external sampling frame).",
    'source:has_text': 'has text — the raw source row (a verbatim-JSON source:item atom) has this extracted free-text field as a weavable txt: atom (the parse-once derived layer; the raw container stays NLP-exempt).',
    'source:generated_by': 'generated by — the target model/process/query produced this acquisition or interpretation bridge.',
    'source:selected_from': 'selected from — the source interpreted atom was SELECTED from the target source item (an interpretation bridge, additive).',
    'source:observed_from': 'observed from — the source interpreted atom was OBSERVED from the target source item/observation.',
    'source:interprets': 'interprets — the source interpreted atom interprets the target source item (the raw atom is never mutated).',
    'source:rejects': 'rejects — the source interpreted atom rejected the target source item (rejection stays queryable, not deleted).',
    'source:based_on': 'based on — the source interpreted claim/observation/opinion is based on the target source item (an interpretation bridge; the raw atom is never mutated).',
    'source:bridge_interp': 'bridge interp — the bridge event records an operation on the target interpreted atom.',
    'source:bridge_src': 'bridge src — the bridge event records an operation that used the target source item.',
}

CORE_NS = {
    'sys': 'sys — built-in structural relations and system atoms.',
    'model': 'model — an immutable machine-vision model identity (model:<family>:<variant>:<version>) carrying full provenance (weights, framework+version, thresholds, input resolution, preprocess). A new config is a new model atom, never an overwrite.',
    'comparison': 'comparison — a model-comparison record (comparison:vision:<obj>:<a>:<b>) between two observers on one artwork: shared/only classes, count/confidence differences, bbox overlap, agreement score. Model disagreement is first-class data, not debugging noise.',
    'role': 'role — upper-ontology role of a domain super-concept (role:product 成果物, role:component 構成要素, role:method 製法) in the Product·Component·Method canon.',
    'rel': 'rel — relation-declaration namespace (rel:salient marks a relation as salient for a category).',
    'society': 'society — a virtual dialogue space (avatar-mediated chat) on a group; society:<group>:<name> names a space.',
    'agent': 'agent — a cast admitted to a society (the cast×society binding); agent:<gid>:<space>:<cast> is that junction. There is no general agent — always an agent OF a society.',
    'responsible': 'responsible — the accountability relation an agent bears in a society (責務), separate from the permission role:; responsible:<kind> (chairman/scribe/broadcaster/approve:<step>/exec:<step>) links a society to the agent who holds that duty.',
    'wb': "wb — a WORKBENCH on the shared world: the surface a scheduled workload runs on, whether that workload is a research experiment, a broadcast programme or an operational business process. It is NOT a laboratory with extra steps — one driver serves all three, and what differs between them is the DUTY each declares (wb:duty:continuous | wb:duty:best_effort), not the machinery. wb:<name> names a bench and wb:<name>:hyp|evidence|proof|note|source:<n> its records. A closed bench (created with a group) lives in that society's group engine — member-only (F53 scope:wb:<name>). It also stores a whiteboard's pins (set:wb:whiteboard:<board>:pins) — the storage is the bench's, the vocabulary and the ops are the whiteboard's (nsdef:whiteboard; the op family is whiteboard.*, renamed from wb.* so an op family is not spelled like this namespace).",
    'wl': 'wl — a WORKLOAD: one scheduled unit of work on a workbench, declared in a single file under config/workbench/workloads/ and read by one driver. wl:workload names the concept, wl:effect|trigger|appetite|budget|pins its declared fields, and wl:state:*/wl:reason:* are a second alias on the state and reason atoms the programme guide already stores as station:* — one atom, two names, so the driver has one vocabulary for a broadcast programme, a research bench and an operational process alike. Every field is also a membership on the workload atom (set:wl:*), which is what makes a declaration inspectable as data.',
    'whiteboard': "whiteboard — a NAMED bundle of a client's self-directed state (its pins and its focus), the client's own layer: world-ignorable, dying with the session, and never able to widen an IAM grant. A board IS its pins Set (set:wb:whiteboard:<board>:pins, stored on the Workbench); a pin is a MEMBERSHIP taken at the bench clock, so pinning adds and unpinning ends one, and what a board held at a given moment stays readable. The focus is a coordinate, not a pin: it moves while the pins stay, and switching or recreating a board erases neither. Ops are whiteboard.* (renamed from wb.*, which is the bench namespace).",
    'aspect': 'aspect — where a coordinate stands in Akasha Time, held as SET MEMBERSHIP rather than a field: aspect:prospective (authored in advance — a plan or a scenario step) and aspect:perfective (the record: it happened), with set:aspect:prospective / set:aspect:perfective holding the coordinates. Membership is ADDITIVE and never removed — running a scenario adds perfective and keeps prospective, so plan and occurrence are two readable memberships instead of one overwritten value, and where they differ is exactly what a record is for (seeds13 law 2: chronon = PERFECTIVE, scenario = PROSPECTIVE, one structure read in opposite times).',
    'bench': "bench — workbench relations binding a bench's records: bench:references (a Source pool/stream reference, never a copy), bench:about, bench:evidence_for, bench:cites, bench:proves, bench:refers_to.",
    'claim': 'claim — a stated assertion about a bench; claim:<sha8> holds the statement + its maker + the bench coordinate it was made at. Its status (attached / unattached / contradicted) is DERIVED from its evidenced_by evidence, never stored. A guest reads only counts (B1 §A6).',
    'cap': "cap — a capability a role is OFFERED: cap:<name>@<fingerprint8> names one, the fingerprint being the running seed's content_fingerprint (the P3 identity rule). Membership of set:cap:offered:<society>:<role> is what a role MAY be granted; the grant check decides what it IS granted (offered ≠ granted, B5 §A7).",
    'llm': "llm — the shared LLM resource allocation namespace (B10): llm:pool:<provider>:<day> is the visible per-provider per-day aggregate atom (capacity / reserved / spent / refused / by[program]) — COUNTS only, never keys or prompts — joined to the telemetry day Set so retention compacts it; llm:credit:<program> is a refused programme's carry-over credit. A programme reserves its per-run calls at admission and runs prepaid; the one gate (llm_provider.generate) debits the reservation and enforces the hard daily/monthly floor.",
    'valid': 'valid — the validity membrane: valid:until:<clock>:<pos> indexes the atoms that expire at position <pos> on <clock>. Once the clock passes <pos> the nightly retention sweep evicts the members from the horizon; the store is never touched (B3 §A8).',
    'workflow': "workflow — a bench's script-and-log in one structure; workflow:<bench> heads it and workflow:<bench>:<branch>:<pos> names one entry (ahead of the cursor = plan, behind = record). A bench-scoped layer distinct from the old CSL wf: definition space.",
    'exec': 'exec — a dispatched workflow run: exec:<bench>:<n> is an immutable membrane over a run of workflow entries (exec:covers), recorded as ONE world-axis sync chronon; a corrected dispatch mints a NEW exec, never edits an old one.',
    'chronon': 'chronon — a semantic state boundary (意味状態境界) held in the network as links+sets; chronon:<sid>:<id> names one. Its members are meaning-bound references (neither snapshot nor delta); succession + variation of chronons is Akasha Time.',
    'scenario': "scenario — a prospective chronon sub-network written in advance; the same structure as a chronon record, read in the opposite time. Running it does NOT rewrite a chronon's aspect: it ADDS the aspect:perfective membership to each coordinate it walks, and the aspect:prospective membership taken when the scenario was authored is kept. A coordinate holding both was planned and then occurred; one holding only prospective is still outstanding; one holding only perfective happened unplanned — a difference a field rewritten in place would destroy. See nsdef:aspect.",
    'lex': 'lex — lexical / interlingual relations over proto-words (祖語); lex:bridge links a foreign proto-word to its English proto-word so a non-English atom reuses the English graph.',
    'kind': 'kind — the telemetry taxonomy; kind:<domain>:<type> (kind:seismic:quake, kind:orbit:satellite) classifies what a subject/observation is.',
    'reldef': "reldef — relation-definition atoms; reldef:<rel> holds a relation's full-spelling description.",
    'nsdef': "nsdef — namespace-definition atoms; nsdef:<ns> holds a namespace's description.",
    'site': 'site — outward web properties of this deployment (analytics anchors for pages that are not concept atoms themselves).',
    'word': 'word — WordNet-derived vocabulary and proto-words.',
    'thesaurus': 'thesaurus — thesaurus relations and cross-references.',
    'calc': 'calc — computed / curated associations and derived values.',
    'emo': 'emo — Plutchik emotion axes (joy, trust, fear, ...).',
    'dna': "dna — innate sensory qualities keyed to a food's identity.",
    'dna:taste': 'dna:taste — innate gustatory qualities (sweet, sour, bitter, salty, umami).',
    'dna:smell': 'dna:smell — innate olfactory qualities.',
    'dna:texture': 'dna:texture — innate textural qualities.',
    'dna:sound': 'dna:sound — innate sound qualities.',
    'sense': 'sense — sensory descriptors.',
    'color': 'color — colour terms and palette.',
    'word:sense': 'word:sense — sense descriptors of a word.',
    'word:color': 'word:color — colour senses of a word.',
    'geo': 'geo — geography: places, borders, countries, languages.',
    'region': 'region — geographic and culinary regions.',
    'rec': 'rec — recipe / tasting attributes (sweetness, acidity, heat).',
    'chrono': 'chrono — temporal placement (before / after).',
    'era': 'era — historical eras.',
    'tool': 'tool — tools and implements.',
    'admin': 'admin — administrative divisions and scale.',
    'ref': 'ref — external references and citations.',
    'broadcast': 'broadcast — public-broadcast mirror namespace: a broadcaster mirrors a PUBLIC society feed into the shared nucleus (broadcast:<gid>:<space> timeline, broadcast:msg:* messages) so guests read it with AI disclosure via society.broadcast.live, without group scope.',
    'pulse': 'pulse — access-analytics namespace: event atoms and their index sets (pulse:day:*, pulse:concept:*, pulse:src:*); admin/telemetry-only, private.',
    'src': 'src — access-analytics referrer/acquisition bucket (pulse:src:<referrer>); a coarse arrival class, never PII.',
    'visit': "visit — access-analytics session bucket (visit:<id>); a within-day pseudonymous grouping of one visitor's events, unrecoverable across days.",
    'concept': 'concept — abstract concepts.',
    'nar': 'nar — narrative craft (structure, character, conflict, device).',
    'polti': "polti — Polti's dramatic situations.",
    'source': 'source — the Source Data Layer: externally acquired or directly observed data preserved BEFORE analytical interpretation (Source Atoms, Pools, Streams, Snapshots, acquisition events, interpretation bridges). Concept Labo is one consumer, not its owner. `source:item:*` holds RAW ROWS ONLY (verbatim JSON, NLP-exempt, chronon:next-ordered).',
    'txt': "txt — extracted free-text/natural-language fields lifted from a raw source row at prep time (`txt:<corpus>:<id>:<field>`). Unlike the raw JSON container, txt atoms ARE weavable: the Weaver decomposes them so the corpus's meaning joins the semantic graph.",
    'cronon': 'cronon — a primitive operand: a discrete position/unit in Akasha Time (a COORDINATE, not a scheduler/event/execution step). Execution may synchronize on Akasha Time; Akasha Time executes nothing. External time is an EXTERNAL mapping, not part of the cronon.',
    'labo': 'labo — a bounded research namespace observed through four canonical projections (Source, Concept, Society, Notebook); labo:<name> names one. A Society observes/operates/governs it, never owns it.',
    'timeframe': 'timeframe — an external temporal frame a cronon maps to (timeframe:<frame> — wall_clock, historical, simulation_step, geological, …); the mapping lives outside the cronon (temporal relativity).',
}


def _sanitize(desc: str) -> str:
    """Descriptions live inside a double-quoted `.ak` argument — strip any stray
    double quotes so the token stays balanced."""
    return desc.replace('"', "'").strip()


def humanize_rel(rel: str) -> str:
    """Templated `"<label> — <meaning>."` for a relation with no curated entry."""
    if rel.startswith("@"):
        label = rel[1:].replace("_", " ").strip()
        return f"{label} — '{label}' relation asserted between two atoms."
    label = rel.replace(":", " ").replace("_", " ").strip()
    ns = rel.split(":", 1)[0] if ":" in rel else ""
    if ns:
        return f"{label} — {ns} relation ({label})."
    return f"{label} — '{label}' relation between two atoms."


def humanize_ns(ns: str) -> str:
    """Templated description for a namespace with no curated entry."""
    label = ns.replace(":", " ").replace("_", " ").strip()
    return f"{ns} — the {label} namespace."


_APP = app_declaration()


def rel_desc(rel: str) -> str:
    return _sanitize(CORE_RELS.get(rel) or (_APP.get("relations") or {}).get(rel)
                     or humanize_rel(rel))


def ns_desc(ns: str) -> str:
    return _sanitize(CORE_NS.get(ns) or (_APP.get("namespaces") or {}).get(ns) or humanize_ns(ns))


# ── ontology scan ─────────────────────────────────────────────────────────────
def _pack_of(fp: str, ont: str) -> str:
    return os.path.relpath(fp, ont).split(os.sep)[0]


def _top_ns(tok: str):
    if ":" in tok and not tok.startswith("{") and not tok.startswith("'") \
            and not tok.startswith('"'):
        return tok.split(":")[0]
    return None


def scan(ont: str, skip_pack: str, spine_prefixes=()):
    """Return (pack_rels, pack_ns, spine_atoms) for the packs under `ont`.

    pack_rels[pack] = set of relation strings used in that pack.
    pack_ns[pack]   = set of top-level namespaces used in that pack.
    spine_atoms     = sorted `<prefix>:<cat>:<name>` atom ids for each declared spine prefix.
    """
    pack_rels = defaultdict(set)
    pack_ns = defaultdict(set)
    ingred = set()
    for fp in glob.glob(os.path.join(ont, "**", "*.ak"), recursive=True):
        if os.path.basename(fp) == "_lexicon.ak":
            continue                       # never read our own output
        pack = _pack_of(fp, ont)
        if pack == skip_pack or pack == "user":
            continue
        for raw in open(fp, encoding="utf-8", errors="replace"):
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            cmd = parts[0]
            if cmd == "ln" and len(parts) >= 4:
                pack_rels[pack].add(parts[3])
                for t in (parts[1], parts[2], parts[3]):
                    n = _top_ns(t)
                    if n:
                        pack_ns[pack].add(n)
            elif cmd == "def" and len(parts) >= 2:
                try:
                    did = shlex.split(s)[1]
                except ValueError:
                    continue
                n = _top_ns(did)
                if n:
                    pack_ns[pack].add(n)
                if did.split(":")[0] in spine_prefixes and did.count(":") >= 2:
                    ingred.add(did)
            elif cmd == "al" and len(parts) >= 3:
                n = _top_ns(parts[1])
                if n:
                    pack_ns[pack].add(n)
    return pack_rels, pack_ns, sorted(ingred)


# ── emission ──────────────────────────────────────────────────────────────────
HEADER = ("# Generated by scripts/gen_lexicon.py — relation / namespace definition "
          "layer.\n# See docs/for-llm/rel-definition-spec.md. Do not edit by hand; "
          "re-run the generator.\n")


# Relation subsumption — a relation that IS a kind of another relation. Encoded as a sys:is_a
# lattice over the reldef atoms themselves (self-describing, self-extending): the navigator that
# walks the concept `sys:is_a` family reads this to learn which relations to follow. A word-sense
# `specializes` its lemma, which is a more specific → more general step = a kind of is-a.
REL_SUBSUMES = {
    "specializes": "sys:is_a",
}


def emit_reldefs(rels, subsumes):
    lines = []
    for rel in sorted(rels):
        aid = f"reldef:{rel}"
        lines.append(f'def "{aid}" "{rel_desc(rel)}"')
        lines.append(f'set.add name="rels" id="{aid}"')
        parent = subsumes.get(rel)
        if parent:
            # the relation is a sub-relation of `parent` (reldef atoms form a small is-a lattice)
            lines.append(f'ln {aid} reldef:{parent} sys:is_a')
    return lines


def emit_nsdefs(nss):
    lines = []
    for ns in sorted(nss):
        aid = f"nsdef:{ns}"
        lines.append(f'def "{aid}" "{ns_desc(ns)}"')
        lines.append(f'set.add name="namespaces" id="{aid}"')
    return lines


# Extra granular namespaces worth surfacing (progressive fallback in the reader).
EXTRA_NS = ["dna:taste", "dna:smell", "rec:color", "dna:texture", "dna:sound",
            "word:sense", "word:color"]

def emit_salient(spines, spine_atoms, salient):
    """Each declared spine `{prefix, root}`: every `<prefix>:<cat>:<name>` atom is_a its category
    proto-word, and every category found is_a `root` — so a category's salient profile inherits down
    to every atom. Then the salient-relation profiles (most important relation first)."""
    roots = {sp["prefix"]: sp["root"] for sp in spines}
    cats_seen, spine = {}, []
    for aid in spine_atoms:
        pfx, cat = aid.split(":")[0], aid.split(":")[1]
        cats_seen.setdefault(cat, roots[pfx])
        spine.append(f"ln {aid} {cat} sys:is_a")
    lines = ["", "# ── category spine (so salient profiles inherit down) ──"]
    for cat in sorted(cats_seen):
        lines.append(f"ln {cat} {cats_seen[cat]} sys:is_a")
    lines.append("")
    lines.append("# ── each atom is a kind of its category ──")
    lines += spine
    lines.append("")
    lines.append("# ── salient-relation profiles (importance order) ──")
    root_names = set(roots.values())
    for cat, rels in salient.items():
        if cat not in root_names and cat not in cats_seen:
            continue
        lines.append(f"# {cat}: " + ", ".join(rels))
        for rel in rels:
            lines.append(f"ln {cat} reldef:{rel} rel:salient")
    return lines, sorted(cats_seen)


def write_pack_json(pack_dir: str, label: str, description: str):
    pj = {"label": label, "description": description, "theme": label, "license": "MIT",
          "source": "internal", "version": "1.0"}
    os.makedirs(pack_dir, exist_ok=True)
    with open(os.path.join(pack_dir, "PACK.json"), "w", encoding="utf-8") as f:
        json.dump(pj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def register_first(ont: str, name: str) -> bool:
    """List `name` FIRST in `<ont>/REGISTRY.json` (autoload, tier A) so it loads before its packs."""
    rp = os.path.join(ont, "REGISTRY.json")
    reg = json.load(open(rp, encoding="utf-8"))
    if any(p["name"] == name for p in reg["packages"]):
        return False
    reg["packages"].insert(0, {"name": name, "autoload": True, "tier": "A"})
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return True


def _autoload(ont: str) -> set:
    try:
        reg = json.load(open(os.path.join(ont, "REGISTRY.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {p["name"] for p in reg["packages"] if p.get("autoload")}


def _write(path: str, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _domain_files(ont: str, autoload: set, pack_rels, pack_ns, core_rels, core_ns) -> int:
    n = 0
    for pack in sorted(set(pack_rels) | set(pack_ns)):
        if pack in autoload or not os.path.isdir(os.path.join(ont, pack)):
            continue
        drels = pack_rels.get(pack, set()) - core_rels
        dns = pack_ns.get(pack, set()) - core_ns
        if not drels and not dns:
            continue
        lines = [HEADER]
        if dns:
            lines.append("\n# ── namespaces introduced by this pack ──")
            lines += emit_nsdefs(dns)
        if drels:
            lines.append("\n# ── relations introduced by this pack ──")
            lines += emit_reldefs(drels, {})
        _write(os.path.join(ont, pack, "_lexicon.ak"), lines)
        n += 1
    return n


def main():
    # ── the platform: its autoload packs' usage + its curated list → ontology/lexicon/ ──
    p_rels, p_ns, _ = scan(ONT, "lexicon")
    p_auto = _autoload(ONT) | {"lexicon"}
    core_rels = set(CORE_RELS)
    core_ns = set(CORE_NS) | set(EXTRA_NS)
    for pack in p_auto:
        core_rels |= p_rels.get(pack, set())
        core_ns |= p_ns.get(pack, set())
    lx = os.path.join(ONT, "lexicon")
    write_pack_json(lx, "Lexicon — Relation & Namespace Definitions",
                    "First-class, self-describing definitions for every relation and namespace the "
                    "platform uses (reldef:/nsdef:). Loads first so cryptic identifiers read as plain "
                    "words from first boot.")
    _write(os.path.join(lx, "00_namespaces_core.ak"), [HEADER] + emit_nsdefs(core_ns))
    _write(os.path.join(lx, "01_relations_core.ak"), [HEADER] + emit_reldefs(core_rels, REL_SUBSUMES))
    stale = os.path.join(lx, "02_salient.ak")
    if os.path.exists(stale):
        os.remove(stale)
    n_dom = _domain_files(ONT, p_auto, p_rels, p_ns, core_rels, core_ns)
    print(f"platform     : {len(core_rels)} reldefs, {len(core_ns)} nsdefs, {n_dom} domain files")

    # ── the application: what its autoload packs and curated list add beyond the platform ──
    decl = _APP
    if not decl or not os.path.isdir(APP_ONT):
        print("application  : none (no lexicon declaration)")
        return
    name = decl["pack"]
    spines = decl.get("spines") or []
    a_rels, a_ns, spine_atoms = scan(APP_ONT, name, tuple(sp["prefix"] for sp in spines))
    a_auto = _autoload(APP_ONT) | {name}
    app_rels = set(decl.get("relations") or {})
    app_ns = set(decl.get("namespaces") or {}) | set(decl.get("extra_namespaces") or [])
    for pack in a_auto:
        app_rels |= a_rels.get(pack, set())
        app_ns |= a_ns.get(pack, set())
    app_rels -= core_rels
    app_ns -= core_ns
    ax = os.path.join(APP_ONT, name)
    write_pack_json(ax, "Lexicon — the application's relations and namespaces",
                    "The application's relation / namespace definitions and salient-relation profiles, "
                    "generated by the platform's lexicon generator from the application's lexicon "
                    "declaration.")
    _write(os.path.join(ax, "00_namespaces.ak"), [HEADER] + emit_nsdefs(app_ns))
    _write(os.path.join(ax, "01_relations.ak"),
           [HEADER] + emit_reldefs(app_rels, decl.get("rel_subsumes") or {}))
    salient_lines, cats = emit_salient(spines, spine_atoms, decl.get("salient") or {})
    _write(os.path.join(ax, "02_salient.ak"),
           [HEADER + "# Salient-relation profiles + the declared is-a spines.\n"
            "# Precedence is by category depth (nearer category first). Intra-category order is\n"
            "# NOT guaranteed: `.ak` carries no edge weight, so the reader falls back to link-return\n"
            "# order within one category. Author most-important-first anyway."] + salient_lines)
    registered = register_first(APP_ONT, name)
    n_dom = _domain_files(APP_ONT, a_auto, a_rels, a_ns, core_rels | app_rels, core_ns | app_ns)
    print(f"application  : {len(app_rels)} reldefs, {len(app_ns)} nsdefs, "
          f"{len(spine_atoms)} spine atoms in {len(cats)} categories, {n_dom} domain files"
          f"{'; registered ' + name if registered else ''}")


if __name__ == "__main__":
    main()
