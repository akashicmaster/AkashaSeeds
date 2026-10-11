# The Thinker's Shelf — the reading programme's vocabulary (Akasha Station · Workbench).
# A READING programme, not a summarising one: a Source is read aloud, a question is raised, and the
# archive is opened through it.  BOOK OPENETH BOOK (Dibdin, The Library Companion, 1824).
#
# This pack defines ONLY the vocabulary the programme runs on — the source decomposition, the four
# source strata, the four interpretation levels, the relation vocabulary, the society roles and the
# reading-cycle steps.  The BOOK ITSELF is never defined here: a work enters as a prepared source pack
# (see docs/for-llm/thinkers-shelf-data-acquisition.md), off-line, with every fragment anchored to its
# edition / page / OCR span / scan.  Keeping the vocabulary and the corpus apart is what lets a second
# book join the programme with no change to this file.

# ══ the programme ══
def "shelf:programme" "A reading programme of Akasha Station — a Source is read, a question is raised, and the archive is opened through it."
al shelf:programme thinkers_shelf_programme
def "shelf:programme:thinkers_shelf" "The Thinker's Shelf — the reading programme. Classics, rare and forgotten books read by a Reader, questioned by a Listener, and opened by a Commentator through the archive's semantic graph."
ln shelf:programme:thinkers_shelf shelf:programme sys:is_a
def "shelf:principle:book_openeth_book" "BOOK OPENETH BOOK — Dibdin's principle, and this programme's law: a book is not summarised but opened, and each opening leads to the next book, person, place or idea."
ln shelf:programme:thinkers_shelf shelf:principle:book_openeth_book shelf:governed_by

# ══ 1 · the source decomposition (a book is never one giant Source) ══
def "shelf:source_unit" "A unit of a read work — the grain a reading programme addresses. A book is decomposed into these; a whole volume is never a single Source."
def "shelf:book" "book — a read work as a bibliographic whole, independent of any one printing."
ln shelf:book shelf:source_unit sys:is_a
def "shelf:edition" "edition — one printing of a book (year, publisher, printer). The unit a page number is only meaningful inside."
ln shelf:edition shelf:source_unit sys:is_a
def "shelf:page" "page — one physical page of one edition; the anchor a scan image and an OCR span hang from."
ln shelf:page shelf:source_unit sys:is_a
def "shelf:section" "section — a named division of a book (chapter, part, bibliographical class) as the book itself divides it."
ln shelf:section shelf:source_unit sys:is_a
def "shelf:passage" "passage — the read grain: one paragraph, or part of one bibliographical entry. What a Reader reads in a single turn."
ln shelf:passage shelf:source_unit sys:is_a
def "shelf:bib_entry" "bibliographical entry — one book described INSIDE the read book; the entry is a source unit in its own right."
ln shelf:bib_entry shelf:source_unit sys:is_a
def "shelf:person" "person — an author, printer, collector, patron or figure named in the text."
ln shelf:person shelf:source_unit sys:is_a
def "shelf:work" "work — a book named or described inside the read book (distinct from the read book itself)."
ln shelf:work shelf:source_unit sys:is_a
def "shelf:place" "place — a place of printing, publication, travel or reference named in the text."
ln shelf:place shelf:source_unit sys:is_a
def "shelf:language" "language — a language a named work is written or printed in."
ln shelf:language shelf:source_unit sys:is_a
def "shelf:printer" "printer / publisher — the house that printed or issued a named work."
ln shelf:printer shelf:source_unit sys:is_a
def "shelf:historical_reference" "historical reference — an event, period or circumstance the text points at."
ln shelf:historical_reference shelf:source_unit sys:is_a
set.add name="shelf:classes" id="shelf:book"
set.add name="shelf:classes" id="shelf:edition"
set.add name="shelf:classes" id="shelf:page"
set.add name="shelf:classes" id="shelf:section"
set.add name="shelf:classes" id="shelf:passage"
set.add name="shelf:classes" id="shelf:bib_entry"
set.add name="shelf:classes" id="shelf:person"
set.add name="shelf:classes" id="shelf:work"
set.add name="shelf:classes" id="shelf:place"
set.add name="shelf:classes" id="shelf:language"
set.add name="shelf:classes" id="shelf:printer"
set.add name="shelf:classes" id="shelf:historical_reference"

# ══ 2 · the four strata — analysis is kept apart from the original ══
def "shelf:stratum" "A source stratum — how far a statement stands from the printed page. Analysis is never written back into the original."
def "shelf:stratum:original" "ORIGINAL — the text as printed, its scan and its page. Nothing inferred; the only stratum a reading may quote as the book's own words."
ln shelf:stratum:original shelf:stratum sys:is_a
def "shelf:stratum:structural" "STRUCTURAL — what is extracted DIRECTLY from the text: the persons, works, places, editions, citations and classes the book itself states."
ln shelf:stratum:structural shelf:stratum sys:is_a
def "shelf:stratum:analytical" "ANALYTICAL — what is derived ACROSS sources: semantic clusters, recovered constructs, historical correspondences, conceptual relations. Never the author's own words."
ln shelf:stratum:analytical shelf:stratum sys:is_a
def "shelf:stratum:commentary" "COMMENTARY — what comes from OUTSIDE: later scholarship, historical background, terminology, open problems. Always attributed."
ln shelf:stratum:commentary shelf:stratum sys:is_a
set.add name="shelf:strata" id="shelf:stratum:original"
set.add name="shelf:strata" id="shelf:stratum:structural"
set.add name="shelf:strata" id="shelf:stratum:analytical"
set.add name="shelf:strata" id="shelf:stratum:commentary"

# ══ 3 · the four interpretation levels — every statement carries one ══
def "shelf:level" "An interpretation level — the epistemic weight of a statement. Every fragment the programme utters carries exactly one; a role may never silently promote one to another."
def "shelf:level:source" "SOURCE — stated in the text itself, quotable as the book's own words."
ln shelf:level:source shelf:level sys:is_a
def "shelf:level:derived" "DERIVED — follows mechanically from sources (an index, a count, a date arithmetic); checkable without judgement."
ln shelf:level:derived shelf:level sys:is_a
def "shelf:level:interpretive" "INTERPRETIVE — a reading ACROSS sources. A recovered construct is INTERPRETIVE by default: it is not necessarily the author's own concept."
ln shelf:level:interpretive shelf:level sys:is_a
def "shelf:level:speculative" "SPECULATIVE — a possibility offered as a possibility. Never stated as fact, never left unmarked."
ln shelf:level:speculative shelf:level sys:is_a
set.add name="shelf:levels" id="shelf:level:source"
set.add name="shelf:levels" id="shelf:level:derived"
set.add name="shelf:levels" id="shelf:level:interpretive"
set.add name="shelf:levels" id="shelf:level:speculative"

# ══ 4 · the society roles — each role's scope is a law, not a style ══
def "shelf:role" "A role of the reading society. A role's scope, allowed sources and turn responsibility are declared; a role never performs another role's act."
def "shelf:role:reader" "READER (朗読者) — selects a short passage and reads it faithfully, holding its page / source anchor. May give a one-line setting. Never explains, never guesses intent, never anticipates the Listener, never reads a later interpretation as the text."
ln shelf:role:reader shelf:role sys:is_a
def "shelf:role:listener" "LISTENER (聞き手) — an intelligent NON-specialist. Voices the question an ordinary listener would actually have, and never pretends to understand. Asks; never answers."
ln shelf:role:listener shelf:role sys:is_a
def "shelf:role:commentator" "COMMENTATOR (解説者) — answers the Listener directly, then gives context, then opens one door. Separates source fact from interpretation, and never states an uncertain reading as settled. The ONLY role that explains."
ln shelf:role:commentator shelf:role sys:is_a
def "shelf:role:source_checker" "SOURCE CHECKER — backstage, not aired: verifies every quoted passage against its anchor (edition, page, OCR span, scan)."
ln shelf:role:source_checker shelf:role sys:is_a
def "shelf:role:fact_checker" "FACT CHECKER — backstage, not aired: verifies the Commentator's claims and their interpretation level."
ln shelf:role:fact_checker shelf:role sys:is_a
def "shelf:role:flow_moderator" "FLOW MODERATOR — backstage, not aired: holds the cycle to its depth limit and moves the programme on."
ln shelf:role:flow_moderator shelf:role sys:is_a
set.add name="shelf:roles" id="shelf:role:reader"
set.add name="shelf:roles" id="shelf:role:listener"
set.add name="shelf:roles" id="shelf:role:commentator"
set.add name="shelf:roles" id="shelf:role:source_checker"
set.add name="shelf:roles" id="shelf:role:fact_checker"
set.add name="shelf:roles" id="shelf:role:flow_moderator"

# ══ 5 · the reading cycle — the workflow steps ══
def "shelf:step" "A step of the reading cycle. The programme is a workflow on the Workbench; each aired turn is one step on the bench clock."
def "shelf:step:open" "OPEN — the programme opens."
ln shelf:step:open shelf:step sys:is_a
def "shelf:step:introduce" "INTRODUCE — the book or section is placed: what it is, when it was printed, why it is being read."
ln shelf:step:introduce shelf:step sys:is_a
def "shelf:step:select_passage" "SELECT PASSAGE — a passage is chosen (one paragraph, or part of one entry; 30 s–2 min read)."
ln shelf:step:select_passage shelf:step sys:is_a
def "shelf:step:read" "READ — the Reader reads the passage faithfully, holding its anchor."
ln shelf:step:read shelf:step sys:is_a
def "shelf:step:question" "QUESTION — the Listener asks what an ordinary listener would ask."
ln shelf:step:question shelf:step sys:is_a
def "shelf:step:explain" "EXPLAIN — the Commentator answers: direct answer, then context, then one semantic opening."
ln shelf:step:explain shelf:step sys:is_a
def "shelf:step:follow_up" "FOLLOW-UP — at most three exchanges on one point; the programme does not dwell."
ln shelf:step:follow_up shelf:step sys:is_a
def "shelf:step:semantic_bridge" "SEMANTIC BRIDGE — one or two related Sources are opened, and no more. This is where BOOK OPENETH BOOK is actually performed."
ln shelf:step:semantic_bridge shelf:step sys:is_a
def "shelf:step:next_passage" "NEXT PASSAGE — the cycle returns to the Reader."
ln shelf:step:next_passage shelf:step sys:is_a
def "shelf:step:recap" "EPISODE RECAP — what was read, what was asked, which doors were opened."
ln shelf:step:recap shelf:step sys:is_a
def "shelf:step:close" "CLOSE — the programme closes."
ln shelf:step:close shelf:step sys:is_a
set.add name="shelf:steps" id="shelf:step:open"
set.add name="shelf:steps" id="shelf:step:introduce"
set.add name="shelf:steps" id="shelf:step:select_passage"
set.add name="shelf:steps" id="shelf:step:read"
set.add name="shelf:steps" id="shelf:step:question"
set.add name="shelf:steps" id="shelf:step:explain"
set.add name="shelf:steps" id="shelf:step:follow_up"
set.add name="shelf:steps" id="shelf:step:semantic_bridge"
set.add name="shelf:steps" id="shelf:step:next_passage"
set.add name="shelf:steps" id="shelf:step:recap"
set.add name="shelf:steps" id="shelf:step:close"

# ══ 6 · a question is knowledge, not chat ══
def "shelf:question" "A Listener's question, kept as a first-class atom — not a chat line. A question that recurs becomes a candidate concept, an FAQ entry, or a semantic beacon."
def "shelf:construct" "A recovered construct — a structure read ACROSS sources that the original author did not necessarily name. INTERPRETIVE by default; it carries the sources that support it."
def "shelf:anchor" "A source anchor — the edition, page, source URI, OCR span and scan reference a fragment returns to. A fragment with no anchor may not be aired."

# ══ 7 · the relation vocabulary (the semantic bridge runs on these) ══
# Bibliographic spine — what the text itself states (STRUCTURAL).
ln shelf:work shelf:person shelf:has_author
ln shelf:work shelf:edition shelf:has_edition
ln shelf:edition shelf:printer shelf:printed_by
ln shelf:work shelf:language shelf:in_language
ln shelf:edition shelf:place shelf:published_at
ln shelf:work shelf:work shelf:cites_work
ln shelf:work shelf:person shelf:mentions_person
ln shelf:work shelf:historical_reference shelf:in_period
# Reading spine — what a passage is about and what it evidences.
ln shelf:passage shelf:section shelf:part_of_section
ln shelf:passage shelf:page shelf:anchored_in
ln shelf:passage shelf:construct shelf:evidences_construct
ln shelf:construct shelf:passage shelf:supported_by
ln shelf:construct shelf:construct shelf:related_construct
ln shelf:question shelf:passage shelf:asked_of
ln shelf:question shelf:construct shelf:opens_construct
# Every fragment declares its stratum and its interpretation level.
ln shelf:passage shelf:stratum:original shelf:in_stratum
ln shelf:construct shelf:level:interpretive shelf:at_level
# Cross-source readings (ANALYTICAL — never presented as the author's own).
ln shelf:construct shelf:work shelf:derived_from
ln shelf:construct shelf:construct shelf:intersects
ln shelf:work shelf:work shelf:historically_precedes
ln shelf:construct shelf:construct shelf:shares_sources_with
ln shelf:construct shelf:construct shelf:shares_method_with
ln shelf:construct shelf:construct shelf:later_fragmented_into
ln shelf:construct shelf:construct shelf:contrasts_with

set.add name="shelf:all" id="shelf:programme:thinkers_shelf"
set.add name="shelf:all" id="shelf:principle:book_openeth_book"
set.add name="shelf:all" id="shelf:question"
set.add name="shelf:all" id="shelf:construct"
set.add name="shelf:all" id="shelf:anchor"
