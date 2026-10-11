# Akasha ontology — paleography / old-document studies (komonjo) and the auxiliary sciences of history.
# Focused general-education-level spine over the existing ms:/epig:/textcrit: atoms.
# ms (codicology) / epig (epigraphy) / textcrit already exist as tops — only linked.
# General-education breadth; research depth is reserved for level-C packs. Base pack.

def "auxhist" "歴史補助学 — the auxiliary (source-critical) sciences of history: the disciplines that let us read, date and authenticate the documents and objects of the past."
ln auxhist knowledge:branch:humanities knowledge:in_branch
ln auxhist archaeo thesaurus:related
ln auxhist historiography.method thesaurus:related

# ══ members of the auxiliary sciences of history ══
def "paleo:paleography" "古書体学・古文書学 — the study of ancient and medieval handwriting: reading old scripts and dating and localising the hand."
ln paleo:paleography auxhist sys:part_of
ln paleo:paleography ms thesaurus:related
ln paleo:paleography epig thesaurus:related
ln ms auxhist sys:part_of
ln epig auxhist sys:part_of
def "paleo:diplomatics" "文書学 (diplomatics) — the critical study of charters and documents: their forms, formulae and authenticity."
ln paleo:diplomatics auxhist sys:part_of
ln paleo:diplomatics textcrit:critical_edition thesaurus:related
def "textcrit:textual_criticism" "本文批判 (textual criticism) — reconstructing the most authentic text from its variant witnesses."
ln textcrit:textual_criticism auxhist sys:part_of
def "paleo:chronology" "年代学 (chronology) — establishing the dates of documents and events, and the calendars they used."
ln paleo:chronology auxhist sys:part_of
ln paleo:chronology archaeo:dating thesaurus:related
ln paleo:chronology hist:period:modern_era thesaurus:related
def "paleo:sigillography" "印章学 (sigillography) — the study of seals used to authenticate documents."
ln paleo:sigillography auxhist sys:part_of
ln paleo:sigillography ms:colophon thesaurus:related
def "paleo:numismatics" "貨幣学 (numismatics) — the study of coins and currency as historical evidence."
ln paleo:numismatics auxhist sys:part_of
ln paleo:numismatics archaeo thesaurus:related
def "paleo:papyrology" "パピルス学 (papyrology) — the study of texts written on papyrus, chiefly from the ancient world."
ln paleo:papyrology auxhist sys:part_of
ln paleo:papyrology epig:ostracon thesaurus:related
ln paleo:papyrology ms:scroll thesaurus:related
def "paleo:archival_science" "文書館学 (archival science) — the theory and practice of preserving and arranging archives."
ln paleo:archival_science auxhist sys:part_of
ln paleo:archival_science lib:accession thesaurus:related
ln paleo:archival_science digarch:digital_archive thesaurus:related
def "paleo:philology" "文献学 (philology) — the study of language in historical written sources."
ln paleo:philology auxhist sys:part_of
ln paleo:philology ling thesaurus:related
ln paleo:philology textcrit:critical_edition thesaurus:related

# ══ paleography — the scripts studied (existing ms: atoms) ══
ln ms:majuscule paleo:paleography paleo:script_studied
ln ms:uncial paleo:paleography paleo:script_studied
ln ms:half_uncial paleo:paleography paleo:script_studied
ln ms:insular_script paleo:paleography paleo:script_studied
ln ms:carolingian_minuscule paleo:paleography paleo:script_studied
ln ms:minuscule paleo:paleography paleo:script_studied
ln ms:gothic_textualis paleo:paleography paleo:script_studied
ln ms:humanist_minuscule paleo:paleography paleo:script_studied
ln ms:cursive paleo:paleography paleo:script_studied
ln ms:uncial ms:half_uncial chrono:before
ln ms:half_uncial ms:insular_script chrono:before
ln ms:insular_script ms:carolingian_minuscule chrono:before
ln ms:carolingian_minuscule ms:gothic_textualis chrono:before
ln ms:gothic_textualis ms:humanist_minuscule chrono:before

# ── the paleographer's toolkit (existing atoms) ──
ln ms:abbreviation paleo:paleography thesaurus:related
ln ms:tironian_notes paleo:paleography thesaurus:related
ln ms:ligature paleo:paleography thesaurus:related
ln ms:diplomatic_transcription paleo:paleography thesaurus:related
ln ms:palimpsest paleo:paleography thesaurus:related
ln ms:watermark paleo:paleography thesaurus:related
ln ms:scriptorium paleo:paleography thesaurus:related
ln ms:marginalia paleo:paleography thesaurus:related
ln ms:gloss paleo:paleography thesaurus:related
ln ms:colophon paleo:paleography thesaurus:related
ln epig:leiden_conventions paleo:paleography thesaurus:related
ln epig:lacuna paleo:paleography thesaurus:related
ln epig:squeeze paleo:paleography thesaurus:related
ln epig:rubbing paleo:paleography thesaurus:related
ln epig:formula paleo:paleography thesaurus:related

# ══ paleography concepts ══
def "paleo:concept:ductus" "The number, order and direction of the strokes that form a letter — a key to identifying a hand."
ln paleo:concept:ductus paleo:paleography sys:part_of
def "paleo:concept:letterform" "The shape of a written character, which changes by period, region and scribe (litterae)."
ln paleo:concept:letterform paleo:paleography sys:part_of
def "paleo:concept:scribal_hand" "The individual handwriting of one scribe, by which a text can be attributed and dated."
ln paleo:concept:scribal_hand paleo:paleography sys:part_of
def "paleo:concept:script_dating" "Assigning a date to a document from the style of its script (palaeographic dating)."
ln paleo:concept:script_dating paleo:paleography sys:part_of
def "paleo:concept:localisation" "Assigning a place of origin to a manuscript from its script, decoration and materials."
ln paleo:concept:localisation paleo:paleography sys:part_of
def "paleo:concept:abbreviation_system" "The systems of contraction and suspension that let scribes write faster and save costly parchment."
ln paleo:concept:abbreviation_system paleo:paleography sys:part_of
def "paleo:concept:transcription_convention" "Agreed rules for rendering a manuscript or inscription in modern type — diplomatic (as-written) or normalised."
ln paleo:concept:transcription_convention paleo:paleography sys:part_of
def "paleo:concept:forgery_detection" "Judging whether a document is authentic from its script, formulae, materials and internal consistency."
ln paleo:concept:forgery_detection paleo:paleography sys:part_of
def "paleo:concept:provenance" "The traced history of a document's ownership and custody, itself evidence for its authenticity."
ln paleo:concept:provenance paleo:paleography sys:part_of
def "paleo:concept:hand_shift" "A change of scribe within one manuscript, detected where the hand changes."
ln paleo:concept:hand_shift paleo:paleography sys:part_of
ln paleo:concept:abbreviation_system ms:abbreviation thesaurus:related
ln paleo:concept:transcription_convention ms:diplomatic_transcription thesaurus:related
ln paleo:concept:transcription_convention epig:leiden_conventions thesaurus:related
ln paleo:concept:forgery_detection paleo:diplomatics thesaurus:related
ln paleo:concept:script_dating paleo:chronology thesaurus:related
ln paleo:concept:scribal_hand ms:scriptorium thesaurus:related

# ══ diplomatics — the anatomy of a charter ══
def "paleo:diplomatics:protocol" "The opening formulae of a charter: invocation, address, greeting."
ln paleo:diplomatics:protocol paleo:diplomatics sys:part_of
def "paleo:diplomatics:text_body" "The central part of a charter (the 'text'), stating the act itself."
ln paleo:diplomatics:text_body paleo:diplomatics sys:part_of
def "paleo:diplomatics:eschatocol" "The closing formulae of a charter: dating clause, subscriptions, seal."
ln paleo:diplomatics:eschatocol paleo:diplomatics sys:part_of
def "paleo:diplomatics:chancery" "The office that drafted and issued a ruler's or bishop's documents, with its own house style."
ln paleo:diplomatics:chancery paleo:diplomatics sys:part_of
def "paleo:diplomatics:formula" "A set, repeated wording whose form helps date and authenticate a document."
ln paleo:diplomatics:formula paleo:diplomatics sys:part_of
def "paleo:diplomatics:authentication" "The means — seal, sign, subscription — by which a document was made valid."
ln paleo:diplomatics:authentication paleo:diplomatics sys:part_of
ln paleo:diplomatics:formula epig:formula thesaurus:related
ln paleo:diplomatics:authentication paleo:sigillography thesaurus:related

# ══ script traditions (inclusive) ══
def "paleo:tradition:latin" "The Latin book hands of the Western Middle Ages (uncial → Carolingian → Gothic → humanist)."
ln paleo:tradition:latin paleo:paleography sys:part_of
def "paleo:tradition:greek" "Greek scripts, from ancient majuscule to Byzantine minuscule."
ln paleo:tradition:greek paleo:paleography sys:part_of
def "paleo:tradition:east_asian" "East Asian document studies (Japanese 古文書学 komonjogaku): cursive kanji and kuzushiji hands."
ln paleo:tradition:east_asian paleo:paleography sys:part_of
def "paleo:tradition:arabic" "The Arabic scripts (kufic, naskh…) of manuscripts and documents."
ln paleo:tradition:arabic paleo:paleography sys:part_of
ln paleo:tradition:latin ms:carolingian_minuscule thesaurus:related
ln paleo:tradition:greek epig:inscription thesaurus:related

# ══ two concrete anchors ══
def "person:alcuin" "Alcuin of York (c.735-804), scholar at Charlemagne's court associated with the reform that spread the clear Carolingian minuscule."
ln person:alcuin person:figure thesaurus:related
ln person:alcuin ms:carolingian_minuscule thesaurus:related
ln person:alcuin paleo:paleography thesaurus:related
ln person:alcuin ms:scriptorium thesaurus:related
def "person:eadfrith" "Eadfrith of Lindisfarne (d.721), the bishop traditionally named as scribe and artist of the Lindisfarne Gospels, a masterpiece of the insular script."
ln person:eadfrith person:figure thesaurus:related
ln person:eadfrith ms:insular_script thesaurus:related
ln person:eadfrith ms:illuminated_manuscript thesaurus:related
