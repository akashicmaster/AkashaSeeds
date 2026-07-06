# Akasha ontology — namespace: concept (bridges)
# Connects common bare-word proto-words to richer namespace atoms and bridges
# the dna:* perceptual namespace to the sense:* / color:* emotional hubs.
#
# Without these links, proto-words such as "mother", "friend", "school",
# "apple" are near-isolated — they specialise word:en:* atoms but don't
# reach the kinship, social-relation or sensory atoms that carry emotion links.
#
# Rule: ln <bare-alias> <namespace:atom> rel — the bare alias resolves to the
# proto-word; if it does not yet exist it is created as a new atom here.
# atoms: 0  (only links — no new def atoms)

# ── Kinship words → kin namespace ─────────────────────────────────────────────

ln mother kin:parent_of thesaurus:related
ln father kin:parent_of thesaurus:related
ln mom kin:parent_of thesaurus:related
ln dad kin:parent_of thesaurus:related
ln parents kin:parent_of thesaurus:related
ln child kin:child_of thesaurus:related
ln children kin:child_of thesaurus:related
ln son kin:child_of thesaurus:related
ln daughter kin:child_of thesaurus:related
ln sibling kin:sibling_of thesaurus:related
ln brother kin:sibling_of thesaurus:related
ln sister kin:sibling_of thesaurus:related
ln ancestor kin:ancestor_of thesaurus:related
ln descendant kin:descendant_of thesaurus:related
ln partner kin:partner_of thesaurus:related
ln spouse kin:partner_of thesaurus:related

# ── Social relation words → social namespace ───────────────────────────────────

ln friend social:friend_of thesaurus:related
ln friendship social:friend_of thesaurus:related
ln companion social:friend_of thesaurus:related
ln teacher social:teacher_of thesaurus:related
ln professor social:teacher_of thesaurus:related
ln student social:student_of thesaurus:related
ln pupil social:student_of thesaurus:related
ln leader social:leader_of thesaurus:related
ln member social:member_of thesaurus:related

# ── School — connect to social and emotion atoms ───────────────────────────────

ln school social:student_of thesaurus:related
ln school social:teacher_of thesaurus:related
ln school emo:anxiety calc:associated_with
ln school emo:interest calc:associated_with
ln school emo:anticipation calc:associated_with
ln school emo:admiration calc:associated_with
ln school emo:nostalgia calc:associated_with

# ── Apple — taste, colour and emotion connections ──────────────────────────────
# ingred:fruit:apple already exists and apple proto-word specialises it;
# add direct links so a single-hop look() surfaces the emotional dimension.

ln apple sense:taste_sweet thesaurus:related
ln apple sense:taste_sour thesaurus:related
ln apple color:red thesaurus:related
ln apple color:green thesaurus:related
ln apple emo:nostalgia calc:associated_with
ln apple emo:satisfaction calc:associated_with
ln apple concept:food thesaurus:related

# ── dna:color → color:* bridges ───────────────────────────────────────────────
# ingred:* atoms link to dna:color:* for visual labelling but those atoms
# have no emotion links.  Bridge each dna colour to its color:* counterpart.

ln dna:color:red color:red thesaurus:related
ln dna:color:green color:green thesaurus:related
ln dna:color:blue color:blue thesaurus:related
ln dna:color:yellow color:yellow thesaurus:related
ln dna:color:orange color:orange thesaurus:related
ln dna:color:purple color:purple thesaurus:related
ln dna:color:white color:white thesaurus:related
ln dna:color:black color:black thesaurus:related

# ── dna:taste → sense:taste_* bridges ─────────────────────────────────────────

ln dna:taste:sweet sense:taste_sweet thesaurus:related
ln dna:taste:sour sense:taste_sour thesaurus:related
ln dna:taste:bitter sense:taste_bitter thesaurus:related
ln dna:taste:umami sense:taste_umami thesaurus:related

# ── dna:texture → sense:texture_* bridges ─────────────────────────────────────

ln dna:texture:soft sense:texture_soft thesaurus:related
ln dna:texture:rough sense:texture_rough thesaurus:related

# ── dna:touch → sense:* bridges ───────────────────────────────────────────────

ln dna:touch:warm sense:warmth thesaurus:related
ln dna:touch:cold sense:cold thesaurus:related
ln dna:touch:cool sense:cold thesaurus:related

# ── Concept proto-word bridges ─────────────────────────────────────────────────
# Connect common bare words to the richly-linked concept:* atoms so that
# a single-hop traversal from any common noun reaches emotion and sense atoms.

ln fire concept:fire thesaurus:related
ln water concept:water thesaurus:related
ln earth concept:earth thesaurus:related
ln sun concept:sun thesaurus:related
ln moon concept:moon thesaurus:related
ln wind concept:wind thesaurus:related
ln rain concept:rain thesaurus:related
ln light concept:light thesaurus:related
ln darkness concept:darkness thesaurus:related
ln dark concept:darkness thesaurus:related
ln life concept:life thesaurus:related
ln death concept:death thesaurus:related
ln love concept:love thesaurus:related
ln peace concept:peace thesaurus:related
ln time concept:time thesaurus:related
ln home concept:home thesaurus:related
ln house concept:home thesaurus:related
ln journey concept:journey thesaurus:related
ln travel concept:journey thesaurus:related
ln trip concept:journey thesaurus:related
ln nature concept:nature thesaurus:related
ln music concept:music thesaurus:related
ln song concept:music thesaurus:related
ln silence concept:silence thesaurus:related
ln quiet concept:silence thesaurus:related
ln growth concept:growth thesaurus:related
ln food concept:food thesaurus:related
ln protection concept:protection thesaurus:related
ln friendship concept:friendship thesaurus:related
ln autumn concept:autumn thesaurus:related
ln fall concept:autumn thesaurus:related
ln snow concept:snow thesaurus:related
ln night concept:night thesaurus:related
ln sky concept:sky thesaurus:related
ln dusk concept:dusk thesaurus:related

# ── Seasonal proto-word bridges ────────────────────────────────────────────────

ln spring concept:spring thesaurus:related
ln summer concept:summer thesaurus:related
ln winter concept:winter thesaurus:related

# ── Landscape proto-word bridges ───────────────────────────────────────────────

ln ocean concept:ocean thesaurus:related
ln sea concept:ocean thesaurus:related
ln seas concept:ocean thesaurus:related
ln forest concept:forest thesaurus:related
ln woods concept:forest thesaurus:related
ln tree concept:forest thesaurus:related
ln mountain concept:mountain thesaurus:related
ln mountains concept:mountain thesaurus:related
ln hill concept:mountain thesaurus:related
ln star concept:star thesaurus:related
ln stars concept:star thesaurus:related

# ── Kinship extended ───────────────────────────────────────────────────────────

ln grandmother kin:ancestor_of thesaurus:related
ln grandfather kin:ancestor_of thesaurus:related
ln grandma kin:ancestor_of thesaurus:related
ln grandpa kin:ancestor_of thesaurus:related
ln grandchild kin:descendant_of thesaurus:related
ln grandson kin:descendant_of thesaurus:related
ln granddaughter kin:descendant_of thesaurus:related
ln uncle kin:sibling_of thesaurus:related
ln aunt kin:sibling_of thesaurus:related
ln cousin kin:sibling_of thesaurus:related
ln husband kin:partner_of thesaurus:related
ln wife kin:partner_of thesaurus:related
ln twin kin:sibling_of thesaurus:related
ln family kin:parent_of thesaurus:related
ln family kin:child_of thesaurus:related

# ── Social extended ────────────────────────────────────────────────────────────

ln colleague social:member_of thesaurus:related
ln coworker social:member_of thesaurus:related
ln boss social:leader_of thesaurus:related
ln manager social:leader_of thesaurus:related
ln neighbor social:friend_of thesaurus:related
ln neighbour social:friend_of thesaurus:related
ln mentor social:teacher_of thesaurus:related
ln coach social:teacher_of thesaurus:related
ln rival social:member_of thesaurus:related
ln team social:member_of thesaurus:related
ln community social:member_of thesaurus:related
