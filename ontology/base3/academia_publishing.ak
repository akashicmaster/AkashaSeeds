# Akasha ontology — academia II: publications, peer review, conferences, societies.
# The paper lifecycle and the conference/society world. Built on academia.ak.
# Base pack.

def "pub" "A scholarly publication."
# ── publication types (論文・著作) ──
def "pub:paper" "Paper (論文) — a research paper."
ln pub:paper pub thesaurus:related
ln pub:paper academia thesaurus:related
def "pub:journal_article" "Journal article (学術論文) — a peer-reviewed article."
ln pub:journal_article pub thesaurus:related
ln pub:journal_article academia thesaurus:related
def "pub:thesis" "Thesis (修士論文) — a master's thesis."
ln pub:thesis pub thesaurus:related
ln pub:thesis academia thesaurus:related
def "pub:dissertation" "Dissertation (博士論文) — a doctoral dissertation."
ln pub:dissertation pub thesaurus:related
ln pub:dissertation academia thesaurus:related
def "pub:book_chapter" "Book chapter — a chapter in an edited book."
ln pub:book_chapter pub thesaurus:related
ln pub:book_chapter academia thesaurus:related
def "pub:monograph" "Monograph — a scholarly book."
ln pub:monograph pub thesaurus:related
ln pub:monograph academia thesaurus:related
def "pub:preprint" "Preprint (プレプリント) — an unrefereed early version."
ln pub:preprint pub thesaurus:related
ln pub:preprint academia thesaurus:related
def "pub:review_article" "Review article — a survey of a field."
ln pub:review_article pub thesaurus:related
ln pub:review_article academia thesaurus:related
def "pub:conference_paper" "Conference paper — a paper at a conference."
ln pub:conference_paper pub thesaurus:related
ln pub:conference_paper academia thesaurus:related
ln pub:thesis phil:thesis thesaurus:related

# ── paper anatomy (論文の構成) ──
def "pub:part:abstract" "Abstract (抄録)."
ln pub:part:abstract pub:paper sys:part_of
def "pub:part:introduction" "Introduction."
ln pub:part:introduction pub:paper sys:part_of
def "pub:part:methods_section" "Methods section."
ln pub:part:methods_section pub:paper sys:part_of
def "pub:part:results" "Results."
ln pub:part:results pub:paper sys:part_of
def "pub:part:discussion" "Discussion."
ln pub:part:discussion pub:paper sys:part_of
def "pub:part:conclusion" "Conclusion."
ln pub:part:conclusion pub:paper sys:part_of
def "pub:part:reference" "Reference."
ln pub:part:reference pub:paper sys:part_of
def "pub:part:bibliography" "Bibliography."
ln pub:part:bibliography pub:paper sys:part_of
def "pub:part:appendix" "Appendix."
ln pub:part:appendix pub:paper sys:part_of
def "pub:part:keyword" "Keyword."
ln pub:part:keyword pub:paper sys:part_of

# ── venues & metrics ──
def "pub:venue:journal" "Journal (学術雑誌) — a scholarly periodical."
ln pub:venue:journal pub thesaurus:related
def "pub:venue:preprint_server" "Preprint server — an open repository (e.g. arXiv)."
ln pub:venue:preprint_server pub thesaurus:related
def "pub:venue:publisher" "Publisher — a publishing body."
ln pub:venue:publisher pub thesaurus:related
def "pub:metric:citation" "Citation (引用) — a reference to a work."
ln pub:metric:citation pub thesaurus:related
def "pub:metric:citation_count" "Citation count — how often cited."
ln pub:metric:citation_count pub thesaurus:related
def "pub:metric:impact_factor" "Impact factor (インパクトファクター) — a journal's citation metric."
ln pub:metric:impact_factor pub thesaurus:related
def "pub:metric:h_index" "H index (h指数) — an author's productivity/impact index."
ln pub:metric:h_index pub thesaurus:related
def "pub:metric:doi" "Doi (DOI) — a digital object identifier."
ln pub:metric:doi pub thesaurus:related
def "pub:metric:issn" "Issn — a serial identifier."
ln pub:metric:issn pub thesaurus:related
ln pub:metric:citation meta:citation thesaurus:related

# ── authorship (著者) ──
def "pub:role:author" "Author."
ln pub:role:author pub thesaurus:related
def "pub:role:coauthor" "Coauthor (共著者)."
ln pub:role:coauthor pub thesaurus:related
def "pub:role:corresponding_author" "Corresponding author (責任著者)."
ln pub:role:corresponding_author pub thesaurus:related
def "pub:role:first_author" "First author."
ln pub:role:first_author pub thesaurus:related
def "pub:role:senior_author" "Senior author."
ln pub:role:senior_author pub thesaurus:related

# ── peer review lifecycle (査読プロセス) ──
def "pub:flow:manuscript" "Manuscript (原稿)."
ln pub:flow:manuscript pub thesaurus:related
ln pub:flow:manuscript pub:flow:submission chrono:before
def "pub:flow:submission" "Submission."
ln pub:flow:submission pub thesaurus:related
ln pub:flow:submission pub:flow:peer_review chrono:before
def "pub:flow:peer_review" "Peer review (査読)."
ln pub:flow:peer_review pub thesaurus:related
ln pub:flow:peer_review pub:flow:revision chrono:before
def "pub:flow:revision" "Revision."
ln pub:flow:revision pub thesaurus:related
ln pub:flow:revision pub:flow:acceptance chrono:before
def "pub:flow:acceptance" "Acceptance."
ln pub:flow:acceptance pub thesaurus:related
ln pub:flow:acceptance pub:flow:publication chrono:before
def "pub:flow:publication" "Publication."
ln pub:flow:publication pub thesaurus:related
def "pub:flow:reviewer" "Reviewer (査読者) — one who peer-reviews."
ln pub:flow:reviewer pub thesaurus:related
def "pub:flow:editor" "Editor — a journal editor."
ln pub:flow:editor pub thesaurus:related
def "pub:flow:major_revision" "Major revision — substantial changes required."
ln pub:flow:major_revision pub thesaurus:related
def "pub:flow:minor_revision" "Minor revision — small changes required."
ln pub:flow:minor_revision pub thesaurus:related
def "pub:flow:rejection" "Rejection — a declined manuscript."
ln pub:flow:rejection pub thesaurus:related
def "pub:flow:open_access" "Open access (オープンアクセス) — freely available."
ln pub:flow:open_access pub thesaurus:related
def "pub:flow:retraction" "Retraction (撤回) — a withdrawn paper."
ln pub:flow:retraction pub thesaurus:related
def "pub:flow:desk_reject" "Desk reject — rejected before review."
ln pub:flow:desk_reject pub thesaurus:related
ln pub:flow:peer_review research:peer_review thesaurus:related
ln pub:flow:reviewer social:colleague_of thesaurus:related
ln pub:flow:acceptance emo:satisfaction calc:associated_with
ln pub:flow:rejection emo:anxiety calc:associated_with

# ── conferences & societies (学会) ──
def "conf" "An academic gathering."
def "conf:academic_conference" "Academic conference (学会大会) — a research conference."
ln conf:academic_conference conf thesaurus:related
ln conf:academic_conference academia thesaurus:related
def "conf:symposium" "Symposium (シンポジウム) — a focused meeting."
ln conf:symposium conf thesaurus:related
ln conf:symposium academia thesaurus:related
def "conf:workshop" "Workshop — a hands-on meeting."
ln conf:workshop conf thesaurus:related
ln conf:workshop academia thesaurus:related
def "conf:colloquium" "Colloquium — a departmental talk series."
ln conf:colloquium conf thesaurus:related
ln conf:colloquium academia thesaurus:related
def "conf:summit" "Summit — a high-level meeting."
ln conf:summit conf thesaurus:related
ln conf:summit academia thesaurus:related
def "conf:element:keynote" "Keynote (基調講演)."
ln conf:element:keynote conf:academic_conference sys:part_of
def "conf:element:plenary" "Plenary."
ln conf:element:plenary conf:academic_conference sys:part_of
def "conf:element:oral_presentation" "Oral presentation (口頭発表)."
ln conf:element:oral_presentation conf:academic_conference sys:part_of
def "conf:element:poster_session" "Poster session (ポスター発表)."
ln conf:element:poster_session conf:academic_conference sys:part_of
def "conf:element:session" "Session."
ln conf:element:session conf:academic_conference sys:part_of
def "conf:element:track" "Track."
ln conf:element:track conf:academic_conference sys:part_of
def "conf:element:proceedings" "Proceedings (予稿集)."
ln conf:element:proceedings conf:academic_conference sys:part_of
def "conf:element:call_for_papers" "Call for papers (論文募集)."
ln conf:element:call_for_papers conf:academic_conference sys:part_of
def "conf:element:abstract_submission" "Abstract submission."
ln conf:element:abstract_submission conf:academic_conference sys:part_of
def "conf:element:registration" "Registration."
ln conf:element:registration conf:academic_conference sys:part_of
def "conf:element:networking" "Networking."
ln conf:element:networking conf:academic_conference sys:part_of
def "conf:role:keynote_speaker" "Keynote speaker."
ln conf:role:keynote_speaker conf thesaurus:related
def "conf:role:session_chair" "Session chair (座長)."
ln conf:role:session_chair conf thesaurus:related
def "conf:role:discussant" "Discussant."
ln conf:role:discussant conf thesaurus:related
def "conf:role:organizing_committee" "Organizing committee."
ln conf:role:organizing_committee conf thesaurus:related
def "conf:role:program_committee" "Program committee."
ln conf:role:program_committee conf thesaurus:related
def "conf:role:presenter" "Presenter."
ln conf:role:presenter conf thesaurus:related

def "society:academic_society" "Academic society (学会) — a learned society / disciplinary body."
def "society:membership" "Membership of a learned society."
def "society:fellow" "An elected fellow of a society."
ln society:academic_society academia thesaurus:related
ln society:membership social:member_of thesaurus:related
ln society:academic_society conf:academic_conference thesaurus:related
ln conf:element:proceedings pub:conference_paper thesaurus:related
ln conf:element:oral_presentation work:presentation thesaurus:related
