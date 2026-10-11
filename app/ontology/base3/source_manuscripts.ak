# Akasha ontology — manuscripts, codicology & palaeography.
# Primary-source scholarship on the handwritten book. Specialist vocabulary,
# bridged to GLAM (lib:/mus:), DH (dh:), and TEI. Base pack.

def "ms" "The handwritten book and its study."
def "ms:codex" "A book of folded leaves bound together — the form that replaced the scroll (写本)."
ln ms:codex ms thesaurus:related
def "ms:scroll" "A rolled writing support (巻子本); a rotulus rolls vertically, a volumen horizontally."
ln ms:scroll ms thesaurus:related
def "ms:palimpsest" "A leaf scraped and reused, the older (scriptio inferior) recoverable beneath the new (重ね書き写本)."
ln ms:palimpsest ms thesaurus:related
def "ms:illuminated_manuscript" "A manuscript decorated with gold, silver and painted imagery."
ln ms:illuminated_manuscript ms thesaurus:related
def "ms:book_of_hours" "A late-medieval lay devotional book (時祷書)."
ln ms:book_of_hours ms thesaurus:related
def "ms:psalter" "A book of the Psalms, often illuminated."
ln ms:psalter ms thesaurus:related
def "ms:breviary" "A book of the daily divine office."
ln ms:breviary ms thesaurus:related
def "ms:gospel_book" "A deluxe copy of the four Gospels."
ln ms:gospel_book ms thesaurus:related
def "ms:lectionary" "A book of scriptural readings arranged for the liturgical year."
ln ms:lectionary ms thesaurus:related
def "ms:cartulary" "A register copying a house's charters into one volume."
ln ms:cartulary ms thesaurus:related
def "ms:incunabulum" "A book printed before 1501 (揺籃期本)."
ln ms:incunabulum ms thesaurus:related
def "ms:fragment" "A detached leaf or portion of a lost manuscript."
ln ms:fragment ms thesaurus:related
def "ms:autograph" "A manuscript in the author's own hand (自筆本)."
ln ms:autograph ms thesaurus:related
# ── codicology ──
def "ms:quire" "A gathering of folded leaves, the building block of the codex (折丁)."
ln ms:quire ms thesaurus:related
def "ms:bifolium" "A single sheet folded to make two conjoint leaves."
ln ms:bifolium ms thesaurus:related
def "ms:folio" "A leaf; cited by number with recto (front) and verso (back)."
ln ms:folio ms thesaurus:related
def "ms:recto" "The front side of a leaf."
ln ms:recto ms thesaurus:related
def "ms:verso" "The back side of a leaf."
ln ms:verso ms thesaurus:related
def "ms:ruling" "Lines laid to guide the script, drilled or drawn."
ln ms:ruling ms thesaurus:related
def "ms:pricking" "Prick-marks guiding the ruling."
ln ms:pricking ms thesaurus:related
def "ms:hair_side" "The (darker) outer skin side of parchment; flesh side is smoother."
ln ms:hair_side ms thesaurus:related
def "ms:watermark" "A translucent maker's mark in paper, aiding dating."
ln ms:watermark ms thesaurus:related
ln ms:watermark ms:codex thesaurus:related
def "ms:collation_formula" "A shorthand describing the quire structure of a volume."
ln ms:collation_formula ms thesaurus:related
def "ms:catchword" "The first word of the next quire written at the foot of the previous, to keep order."
ln ms:catchword ms thesaurus:related
def "ms:foliation" "Numbering by leaf (vs pagination by page)."
ln ms:foliation ms thesaurus:related
def "ms:colophon" "A scribe's closing note giving place, date or name (奥書)."
ln ms:colophon ms thesaurus:related
ln ms:colophon lib:cataloging thesaurus:related
def "ms:incipit" "The opening words of a text ('here begins…')."
ln ms:incipit ms thesaurus:related
def "ms:explicit" "The closing words ('here ends…')."
ln ms:explicit ms thesaurus:related
def "ms:rubric" "Text (often a heading) written in red (朱書)."
ln ms:rubric ms thesaurus:related
def "ms:marginalia" "Notes and drawings in the margins (欄外注)."
ln ms:marginalia ms thesaurus:related
ln ms:marginalia dh:close_reading thesaurus:related
def "ms:gloss" "An explanatory note between lines (interlinear) or in the margin."
ln ms:gloss ms thesaurus:related
def "ms:parchment" "Prepared animal skin as a writing support; fine calf skin is vellum."
ln ms:parchment ms thesaurus:related
def "ms:vellum" "Fine parchment, typically calfskin."
ln ms:vellum ms thesaurus:related
def "ms:iron_gall_ink" "The standard black-brown medieval ink of gall, iron and gum."
ln ms:iron_gall_ink ms thesaurus:related
# ── palaeography ──
def "ms:script" "A style of writing shared by many hands (書体); a 'hand' is one scribe's realisation."
ln ms:script ms thesaurus:related
def "ms:majuscule" "Capital-form script contained between two lines."
ln ms:majuscule ms thesaurus:related
def "ms:minuscule" "Small-letter script with ascenders and descenders."
ln ms:minuscule ms thesaurus:related
def "ms:uncial" "A rounded majuscule book-hand of late antiquity."
ln ms:uncial ms thesaurus:related
def "ms:half_uncial" "A transitional book-hand with minuscule features."
ln ms:half_uncial ms thesaurus:related
def "ms:carolingian_minuscule" "The clear reformed minuscule of the Carolingian renewal, ancestor of roman type."
ln ms:carolingian_minuscule ms thesaurus:related
ln ms:carolingian_minuscule dh:htr thesaurus:related
def "ms:insular_script" "The distinctive scripts of Ireland and Britain."
ln ms:insular_script ms thesaurus:related
def "ms:gothic_textualis" "The formal angular book-hand of the high Middle Ages."
ln ms:gothic_textualis ms thesaurus:related
def "ms:humanist_minuscule" "The Renaissance revival of Carolingian forms."
ln ms:humanist_minuscule ms thesaurus:related
def "ms:cursive" "A rapid joined hand for documents."
ln ms:cursive ms thesaurus:related
def "ms:abbreviation" "Contracted forms (suspension, contraction, brevigraph) saving space."
ln ms:abbreviation ms thesaurus:related
def "ms:ligature" "Two letters joined as one form."
ln ms:ligature ms thesaurus:related
def "ms:nomina_sacra" "Contracted sacred names marked by a superscript bar."
ln ms:nomina_sacra ms thesaurus:related
def "ms:tironian_notes" "An ancient shorthand; 'et' survives as the Tironian ⁊."
ln ms:tironian_notes ms thesaurus:related
def "ms:scriptorium" "The room/workshop where monastic scribes copied books."
ln ms:scriptorium ms thesaurus:related
def "ms:diplomatic_transcription" "A transcription reproducing the source's forms exactly."
ln ms:diplomatic_transcription ms thesaurus:related
ln ms:diplomatic_transcription dh:transcription thesaurus:related
ln ms:diplomatic_transcription metastd:tei thesaurus:related
