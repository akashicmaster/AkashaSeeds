# Akasha ontology — epigraphy, papyrology, numismatics, seals, diplomatics.
# Material and documentary primary sources and their auxiliary sciences
#. Base pack.

def "epig" "Epigraphy — the study of inscriptions."
def "epig:inscription" "A text incised or applied on a durable object (碑文)."
ln epig:inscription epig thesaurus:related
def "epig:epitaph" "A funerary inscription commemorating the dead (墓碑銘)."
ln epig:epitaph epig thesaurus:related
def "epig:graffito" "An informal scratched inscription; a painted one is a dipinto."
ln epig:graffito epig thesaurus:related
def "epig:dedication" "An inscription dedicating a building or offering."
ln epig:dedication epig thesaurus:related
def "epig:milestone" "A road inscription marking distance (miliarium)."
ln epig:milestone epig thesaurus:related
def "epig:stele" "An upright inscribed slab or pillar (石碑)."
ln epig:stele epig thesaurus:related
def "epig:ostracon" "An inscribed potsherd used for notes, receipts or votes."
ln epig:ostracon epig thesaurus:related
def "epig:squeeze" "A paper or latex impression (estampage) recording an inscription's relief (拓本/型取り)."
ln epig:squeeze epig thesaurus:related
ln epig:squeeze mus:conservation thesaurus:related
def "epig:rubbing" "An impression taken by rubbing over a raised inscription (拓本)."
ln epig:rubbing epig thesaurus:related
def "epig:lacuna" "A gap where the text is lost or illegible."
ln epig:lacuna epig thesaurus:related
ln epig:lacuna textcrit:lacuna thesaurus:related
def "epig:leiden_conventions" "The standard sigla ([ ] ( ) < > … ) for editing damaged texts."
ln epig:leiden_conventions epig thesaurus:related
def "epig:formula" "A recurrent set phrase (e.g. D M — dis manibus)."
ln epig:formula epig thesaurus:related
def "epig:cuneiform" "Wedge-writing impressed in clay, the script of Mesopotamia (楔形文字)."
ln epig:cuneiform epig thesaurus:related
def "epig:hieroglyph" "The pictographic monumental script of ancient Egypt (神聖文字)."
ln epig:hieroglyph epig thesaurus:related
def "epig:runic" "The angular futhark alphabet of the Germanic peoples (ルーン文字)."
ln epig:runic epig thesaurus:related
ln epig:runic epig:inscription thesaurus:related
def "epig:ogham" "An early Irish script of strokes along an edge."
ln epig:ogham epig thesaurus:related
def "papyr" "Papyrology — the study of papyri and related texts."
def "papyr:papyrus" "Writing material of pressed reed strips; also a text on it (パピルス)."
ln papyr:papyrus papyr thesaurus:related
def "papyr:documentary_papyrus" "A papyrus of daily life — contract, letter, receipt, petition."
ln papyr:documentary_papyrus papyr thesaurus:related
def "papyr:literary_papyrus" "A papyrus preserving a literary work."
ln papyr:literary_papyrus papyr thesaurus:related
def "papyr:cartonnage" "Waste papyrus layered into mummy-casing, a source of recovered texts."
ln papyr:cartonnage papyr thesaurus:related
def "papyr:wax_tablet" "A reusable writing surface of wax on wood (蝋板)."
ln papyr:wax_tablet papyr thesaurus:related
def "papyr:kollema" "A single manufactured sheet; papyri were pasted into a roll."
ln papyr:kollema papyr thesaurus:related
def "papyr:docket" "A summary note added to a document."
ln papyr:docket papyr thesaurus:related
def "numis" "Numismatics — the study of coins and money."
def "numis:coin" "A stamped metal token of value, a dated dense historical source (貨幣)."
ln numis:coin numis thesaurus:related
def "numis:obverse" "The 'heads' side, usually bearing the ruler or authority."
ln numis:obverse numis thesaurus:related
def "numis:reverse" "The 'tails' side, bearing type and legend."
ln numis:reverse numis thesaurus:related
def "numis:legend" "The inscription running around a coin."
ln numis:legend numis thesaurus:related
def "numis:exergue" "The space below the main type, often giving mint or date."
ln numis:exergue numis thesaurus:related
def "numis:mint_mark" "A mark identifying the striking mint."
ln numis:mint_mark numis thesaurus:related
def "numis:die" "The engraved tool that stamps a coin; die-studies reconstruct output."
ln numis:die numis thesaurus:related
def "numis:hoard" "A buried group of coins, a tightly datable deposit."
ln numis:hoard numis thesaurus:related
ln numis:hoard numis:coin thesaurus:related
def "numis:denomination" "A coin's named value."
ln numis:denomination numis thesaurus:related
def "sigil" "Sigillography — the study of seals."
def "sigil:seal" "An impression in wax or lead authenticating a document (印章)."
ln sigil:seal sigil thesaurus:related
ln sigil:seal diplo:charter thesaurus:related
def "sigil:seal_matrix" "The engraved die that makes a seal impression."
ln sigil:seal_matrix sigil thesaurus:related
def "sigil:wax_seal" "A seal impressed in wax, often pendant on cords."
ln sigil:wax_seal sigil thesaurus:related
def "sigil:bulla" "A lead (or gold) seal, typical of papal and Byzantine documents."
ln sigil:bulla sigil thesaurus:related
def "sigil:counterseal" "A smaller seal on the reverse, reinforcing authenticity."
ln sigil:counterseal sigil thesaurus:related
def "diplo" "Diplomatics — the critical study of documents' form and authenticity."
def "diplo:charter" "A formal document granting rights or property (証書/特許状)."
ln diplo:charter diplo thesaurus:related
ln diplo:charter sigil:seal thesaurus:related
ln diplo:charter lib:accession thesaurus:related
def "diplo:diploma" "A solemn sovereign act in fixed form."
ln diplo:diploma diplo thesaurus:related
def "diplo:deed" "A sealed legal instrument of conveyance."
ln diplo:deed diplo thesaurus:related
def "diplo:cartulary" "A register of copied charters (also ms:cartulary)."
ln diplo:cartulary diplo thesaurus:related
def "diplo:chancery" "The office that drafts and issues documents; its usage aids dating."
ln diplo:chancery diplo thesaurus:related
def "diplo:protocol" "The opening formulae (invocation, intitulatio, address)."
ln diplo:protocol diplo thesaurus:related
def "diplo:eschatocol" "The closing formulae (dating clause, corroboration, subscriptions)."
ln diplo:eschatocol diplo thesaurus:related
def "diplo:arenga" "The rhetorical preamble stating a general motive."
ln diplo:arenga diplo thesaurus:related
def "diplo:dispositio" "The clause stating the act itself."
ln diplo:dispositio diplo thesaurus:related
def "diplo:dating_clause" "The formula fixing time and place of the act."
ln diplo:dating_clause diplo thesaurus:related
def "diplo:notarial_sign" "A notary's personal drawn mark authenticating an instrument."
ln diplo:notarial_sign diplo thesaurus:related
def "diplo:chirograph" "A document written in duplicate on one sheet and cut through a word for matching."
ln diplo:chirograph diplo thesaurus:related
def "diplo:forgery" "A spurious document — diplomatics exists largely to detect it."
ln diplo:forgery diplo thesaurus:related
ln diplo:forgery textcrit:textual_criticism thesaurus:related
