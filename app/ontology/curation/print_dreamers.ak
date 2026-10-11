# print_dreamers.ak — atoms for the AUTHORED curation "The Dream of Printing & Publishing".
# Second installment of the exhibition series 「夢追い人の系譜」 (A Genealogy of Dream-Chasers).
#
# The story is a TWO-BRANCH tree rooted in East Asian woodblock: the technique forks —
#   WEST — woodblock → copperplate/metal engraving, and movable type (Bi Sheng → Jikji) →
#          Gutenberg's press → Aldus's publishing → the steam press → offset. Text mechanised.
#   EAST — woodblock stays woodblock, crosses to Japan, and flowers into the secular
#          commercial ukiyo-e of the late Edo/幕末 — which, via Japonisme, reshapes
#          Art Nouveau: the birth of modern commercial design.
# The fork and the two spines are cut into the graph with `chrono:before` (earlier → later),
# all edges intra-pack (both ends defined here) so the demo stays self-contained and loads
# cleanly in every series. The ORDER of the reading is authored in the CSL.
#
# Figures/events: public-domain history. Editorial text: MIT.

# ── The root ─────────────────────────────────────────────────────────────────
def "print:origin:woodblock"     "Woodblock printing (China, Tang dynasty) — whole pages carved into wood and inked; the Diamond Sutra of 868 is the earliest dated printed book. The common root: from here the craft forks — West toward metal and the press, East staying with the block."

# ── WEST branch — movable type + the metal plate → the press → offset ─────────
def "print:origin:bi_sheng"      "Bi Sheng's movable type (Song China, c.1040) — individual clay characters, reusable and rearranged. The idea that would remake the world, four centuries before Europe."
def "print:origin:jikji"         "Jikji (Korea, 1377) — the oldest surviving book printed with metal movable type, cast in a Buddhist temple; metal type predating Gutenberg by decades."
def "print:west:copperplate"     "Copperplate engraving (銅版, Europe, 15th c.) — the intaglio line incised into metal to reproduce fine images. The Western branch turns woodblock into metal craft, and image-printing joins the coming age of type."
def "print:milestone:gutenberg"  "Johannes Gutenberg (Mainz, c.1440) — a press with cast metal type, oil-based ink and the screw press; the 42-line Bible (c.1455). Movable type and metal-plate craft converge; mechanised printing ignites Europe's knowledge revolution."
def "print:milestone:aldus"      "Aldus Manutius (Venice, c.1500) — italic type and the portable octavo book; the printer as publisher. The dream turns from making pages to making readers — the birth of modern publishing."
def "print:milestone:steam_press" "Friedrich Koenig's steam press (London, 1814) — the first newspaper (The Times) printed by steam-driven cylinders; printing leaves the workshop for industry, and the page becomes the daily many."
def "print:milestone:offset"     "Ira Rubel's offset lithography (1904) — the image is offset from plate to rubber blanket to paper; fast, cheap, universal. The Western branch's modern end: the world printed at scale."

# ── EAST branch — woodblock stays woodblock → ukiyo-e → Art Nouveau ───────────
def "print:east:ukiyoe"          "Ukiyo-e (Japan, Edo through 幕末) — woodblock carried east and kept, flowering into a secular, commercial print culture: colour prints of actors, courtesans, and landscapes sold cheaply to the townspeople. The block becomes a people's mass medium."
def "print:east:artnouveau"      "Art Nouveau (Europe, c.1890–1910) — through Japonisme, ukiyo-e's flat colour, bold outline and asymmetry remake Western design (Mucha's posters, Toulouse-Lautrec). The East branch's fruit: the birth of modern commercial and graphic design."

# ── The fork + the two spines (chrono:before = earlier → later, intra-pack) ───
ln print:origin:woodblock print:origin:bi_sheng   chrono:before
ln print:origin:bi_sheng  print:origin:jikji      chrono:before
ln print:origin:jikji     print:milestone:gutenberg chrono:before
ln print:origin:woodblock print:west:copperplate  chrono:before
ln print:west:copperplate print:milestone:gutenberg chrono:before
ln print:milestone:gutenberg  print:milestone:aldus       chrono:before
ln print:milestone:aldus      print:milestone:steam_press chrono:before
ln print:milestone:steam_press print:milestone:offset     chrono:before
ln print:origin:woodblock print:east:ukiyoe       chrono:before
ln print:east:ukiyoe      print:east:artnouveau   chrono:before

# ── The curated set (the CSL orders these by ids=) ───────────────────────────
set.add name="curation:demo:print_dreamers" id="print:origin:woodblock"
set.add name="curation:demo:print_dreamers" id="print:origin:bi_sheng"
set.add name="curation:demo:print_dreamers" id="print:origin:jikji"
set.add name="curation:demo:print_dreamers" id="print:west:copperplate"
set.add name="curation:demo:print_dreamers" id="print:milestone:gutenberg"
set.add name="curation:demo:print_dreamers" id="print:milestone:aldus"
set.add name="curation:demo:print_dreamers" id="print:milestone:steam_press"
set.add name="curation:demo:print_dreamers" id="print:milestone:offset"
set.add name="curation:demo:print_dreamers" id="print:east:ukiyoe"
set.add name="curation:demo:print_dreamers" id="print:east:artnouveau"
