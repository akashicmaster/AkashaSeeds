# -*- coding: utf-8 -*-
"""Atlas data for the Ancient Civilizations room — the SINGLE SOURCE OF TRUTH.

Edit here, then run `python scripts/gen_civ_atlas.py`; that one generator emits BOTH
  • app/ontology/world/civilizations_atlas.ak   (the geo layer, imported into the graph)
  • app/archives/ancient/atlas.json             (the read-only data the /ancient/ overlay renders)
and then run `python scripts/gen_lexicon.py` + `python test/verify_lexicon.py --all`.

Per civilization (keyed by its `ancient:*` atom):
  c     : list of ISO-3166-1 alpha-3 codes — the MODERN countries overlapping the
          historical CORE range (approximate; drives the map's country highlight).
          Not the maximal empire extent — the core, matching the legend "modern country of the core".
  note  : one short geographic phrase (the overlay subtitle — WHERE the culture sat).
  hull  : OPTIONAL [[lon,lat], …] — a SCHEMATIC, approximate core outline (a stylised
          hand-outline after standard historical atlases, NOT a surveyed border). Absent
          where no responsible outline is drawn yet.
  sites : OPTIONAL list of (site_key, display_name, lat, lon, blurb, source_url) — excavation
          sites plotted as pins. site_key binds to the ontology atom `ancient:site:<key>`
          (minted by the generator if the depth layer does not already carry it). Coordinates
          are FACTS (not copyrightable); each carries the source it was taken from. Absent
          where coordinates have not yet been sourced — the country highlight still renders.

RULE 0 (non-negotiable): never assert a coordinate or border as fact without a source.
Every site coordinate below was verified against its cited public source (the Wikipedia
coordinate record, cross-checked against gazetteer values) in Sept 2026. Territorial hulls
are explicitly schematic. Country membership is labelled approximate. Nothing is fabricated
precision; where a source gave only a culture-area centroid (e.g. Nok) the pin is that centroid.
"""

# Wikipedia article base — the public, verifiable coordinate record for each named site.
W = "https://en.wikipedia.org/wiki/"


def _e(c, note, hull=None, sites=None, maps=None):
    # maps: list of (title, date, attribution, url) — a HISTORICAL map from (or depicting) the era
    # the civilization flourished. A genuine contemporary map, cited; recorded so the ontology can
    # carry old-map links and a future renderer can overlay / georeference them.
    return {"c": c, "note": note, "hull": hull or [], "sites": sites or [], "maps": maps or []}


ATLAS = {
    # ══ 1 · Mesopotamia & the Near East ══
    "ancient:sumer": _e(
        ["IRQ"], "Southern Mesopotamia — the lower Tigris–Euphrates plain.",
        hull=[[44.0, 33.3], [45.6, 32.9], [47.2, 31.3], [48.3, 30.2], [46.4, 29.9], [44.9, 30.9], [44.1, 32.1], [44.0, 33.3]],
        sites=[
            ("uruk", "Uruk", 31.3242, 45.6372, "the first city; cuneiform", W + "Uruk"),
            ("ur", "Ur", 30.9625, 46.1031, "ziggurat; the royal tombs", W + "Ur"),
            ("eridu", "Eridu", 30.8158, 45.9961, "the earliest temple layers", W + "Eridu"),
            ("nippur", "Nippur", 32.1261, 45.2309, "sacred city of Enlil", W + "Nippur"),
        ]),
    "ancient:akkad": _e(
        ["IRQ", "SYR"], "Central Mesopotamia — from Sumer north to the middle Euphrates."),
    "ancient:babylon": _e(
        ["IRQ"], "Central–southern Mesopotamia, on the Euphrates below Baghdad.",
        sites=[("babylon", "Babylon", 32.5425, 44.4211, "Hammurabi's capital; the Ishtar Gate", W + "Babylon")],
        maps=[("Babylonian Map of the World (Imago Mundi)", "c.700 BCE", "British Museum, BM 92687",
               W + "Babylonian_Map_of_the_World")]),
    "ancient:assyria": _e(
        ["IRQ", "SYR", "TUR"], "Upper Mesopotamia — the Tigris around Mosul.",
        sites=[
            ("nineveh", "Nineveh", 36.3594, 43.1528, "Ashurbanipal's great library", W + "Nineveh"),
            ("assur", "Assur", 35.4567, 43.2625, "the first Assyrian capital", W + "Assur"),
            ("nimrud", "Nimrud", 36.0992, 43.3275, "Kalhu, the palace-city", W + "Nimrud"),
        ]),
    "ancient:elam": _e(
        ["IRN"], "Southwestern Iran — the Susiana plain and the Zagros.",
        sites=[("susa", "Susa", 32.1892, 48.2578, "the ancient capital of Elam", W + "Susa")]),
    "ancient:hittite": _e(
        ["TUR", "SYR"], "Central Anatolia — the Halys river bend.",
        sites=[("hattusa", "Hattusa", 40.0197, 34.6153, "the Hittite capital", W + "Hattusa")]),
    "ancient:phoenicia": _e(
        ["LBN", "SYR", "ISR"], "The Levantine coast — the ports of Tyre, Sidon, Byblos.",
        sites=[
            ("tyre", "Tyre", 33.2708, 35.1961, "island city of purple dye", W + "Tyre,_Lebanon"),
            ("byblos", "Byblos", 34.1236, 35.6519, "the oldest port; the alphabet", W + "Byblos"),
        ]),

    # ══ 2 · Ancient Egypt & the Nile ══
    "ancient:egypt:old_kingdom": _e(
        ["EGY"], "The Nile valley and delta — delta to the first cataract.",
        hull=[[30.0, 31.6], [32.2, 31.4], [31.4, 30.0], [31.0, 27.5], [32.2, 25.0], [32.9, 24.0], [32.5, 24.0], [31.6, 25.2], [30.7, 27.8], [30.4, 30.1], [29.7, 31.4], [30.0, 31.6]],
        sites=[
            ("giza", "Giza", 29.9761, 31.1328, "the great pyramids", W + "Giza_pyramid_complex"),
            ("saqqara", "Saqqara", 29.8711, 31.2164, "the Step Pyramid of Djoser", W + "Saqqara"),
            ("memphis", "Memphis", 29.8494, 31.2550, "the Old Kingdom capital", W + "Memphis,_Egypt"),
        ]),
    "ancient:egypt:new_kingdom": _e(
        ["EGY"], "The Nile from the delta to Nubia — the age of Thebes.",
        sites=[
            ("thebes", "Thebes", 25.7206, 32.6103, "Karnak, Luxor, the royal capital", W + "Thebes,_Egypt"),
            ("valley_of_the_kings", "Valley of the Kings", 25.7404, 32.6013, "the royal rock-cut tombs", W + "Valley_of_the_Kings"),
        ],
        maps=[("Turin Papyrus Map", "c.1150 BCE", "Museo Egizio, Turin",
               W + "Turin_Papyrus_Map")]),
    "ancient:kush": _e(
        ["SDN"], "Nubia — the middle Nile above the cataracts.",
        sites=[("kerma", "Kerma", 19.6008, 30.4097, "the earliest Kushite capital", W + "Kerma")]),
    "ancient:meroe": _e(
        ["SDN"], "The Nile between the fifth and sixth cataracts.",
        sites=[("meroe", "Meroë", 16.9383, 33.7492, "the pyramids of the Kushite kings", W + "Pyramids_of_Mero%C3%AB")]),

    # ══ 3 · The Indian Subcontinent ══
    "ancient:indus": _e(
        ["PAK", "IND"], "The Indus and Ghaggar–Hakra basins, reaching into Gujarat.",
        hull=[[73.5, 31.5], [74.6, 29.5], [73.2, 26.8], [72.6, 24.0], [72.6, 22.2], [70.0, 22.6], [68.0, 25.0], [67.1, 27.4], [68.6, 29.1], [70.6, 30.6], [73.5, 31.5]],
        sites=[
            ("mohenjo_daro", "Mohenjo-daro", 27.3292, 68.1389, "the great bath; grid streets", W + "Mohenjo-daro"),
            ("harappa", "Harappa", 30.6289, 72.8639, "the type-site of the culture", W + "Harappa"),
            ("dholavira", "Dholavira", 23.8886, 70.2136, "reservoirs; a stone signboard", W + "Dholavira"),
            ("lothal", "Lothal", 22.5227, 72.2488, "a tidal dockyard", W + "Lothal"),
        ]),
    "ancient:vedic": _e(
        ["IND", "PAK"], "The Punjab and the Ganga–Yamuna plain — the Vedic homeland.",
        sites=[("hastinapur", "Hastinapur", 29.1700, 78.0200, "Painted Grey Ware; the Mahabharata city", W + "Hastinapur")]),
    "ancient:maurya": _e(
        ["IND", "PAK", "BGD", "NPL", "AFG"], "The subcontinent from the Hindu Kush to the Deccan — Ashoka's empire.",
        sites=[("pataliputra", "Pataliputra", 25.6110, 85.1440, "the Mauryan capital (Patna)", W + "Pataliputra")]),
    "ancient:gupta": _e(
        ["IND", "BGD", "PAK"], "The Ganges plain — the classical 'golden age' of north India.",
        sites=[("udayagiri_caves", "Udayagiri Caves", 23.5364, 77.7722, "Gupta rock-cut Hindu shrines", W + "Udayagiri_Caves")]),

    # ══ 4 · Ancient China & East Asia ══
    "ancient:shang": _e(
        ["CHN"], "The middle-lower Yellow River — the Central Plain.",
        sites=[("yinxu", "Yinxu (Anyang)", 36.1225, 114.3186, "oracle bones; the Shang capital", W + "Yinxu")]),
    "ancient:zhou": _e(
        ["CHN"], "The Yellow River valley and the Wei plain.",
        sites=[("haojing", "Haojing (Fenghao)", 34.2167, 108.7167, "the Western Zhou capital near Xi'an", W + "Fenghao")]),
    "ancient:qin": _e(
        ["CHN"], "The Wei valley and the first unified China.",
        sites=[("xianyang", "Xianyang", 34.4139, 108.8578, "the Qin capital; the Terracotta Army nearby", W + "Xianyang_(Qin)")]),
    "ancient:han": _e(
        ["CHN"], "The Yellow and Yangtze basins — the Han heartland.",
        sites=[("changan", "Chang'an", 34.3044, 108.8572, "the great Han capital (Xi'an)", W + "Chang%27an")],
        maps=[("Mawangdui silk maps", "168 BCE", "Hunan Museum, Changsha",
               W + "Mawangdui")]),
    "ancient:gojoseon": _e(
        ["PRK", "KOR", "CHN"], "The Korean peninsula and southern Manchuria.",
        sites=[("wanggeom_seong", "Wanggeom-seong", 39.0167, 125.7475, "the reputed capital (near Pyongyang; disputed)", W + "Wanggeom-seong")]),
    "ancient:yayoi": _e(
        ["JPN"], "Kyushu and western Honshu — the coming of wet rice.",
        sites=[("yoshinogari", "Yoshinogari", 33.3236, 130.3907, "a great moated Yayoi settlement", W + "Yoshinogari_site")]),

    # ══ 5 · The Aegean & Classical Mediterranean ══
    "ancient:minoan": _e(
        ["GRC"], "Crete and the Aegean isles.",
        sites=[("knossos", "Knossos", 35.2981, 25.1631, "the palace of the labyrinth", W + "Knossos")]),
    "ancient:mycenae": _e(
        ["GRC"], "The Peloponnese and mainland Greece.",
        sites=[("mycenae", "Mycenae", 37.7303, 22.7575, "the Lion Gate; the shaft graves", W + "Mycenae")]),
    "ancient:greece": _e(
        ["GRC", "TUR"], "The Greek mainland, the Aegean, and the Ionian coast.",
        sites=[
            ("athens", "Athens", 37.9717, 23.7261, "the Acropolis; the Parthenon", W + "Acropolis_of_Athens"),
            ("delphi", "Delphi", 38.4823, 22.5013, "the oracle of Apollo", W + "Delphi"),
        ]),
    "ancient:etruscan": _e(
        ["ITA"], "Etruria — Tuscany and the Tyrrhenian coast of central Italy.",
        sites=[("cerveteri", "Cerveteri", 42.0055, 12.1009, "the Banditaccia necropolis", W + "Cerveteri")]),
    "ancient:rome": _e(
        ["ITA"], "From the city on the Tiber to an empire around the whole sea.",
        sites=[("rome", "Rome", 41.8925, 12.4853, "the Forum, the Colosseum, the capital", W + "Roman_Forum")],
        maps=[("Tabula Peutingeriana", "Roman itinerarium; surviving copy c.1200", "Österreichische Nationalbibliothek, Vienna",
               W + "Tabula_Peutingeriana"),
              ("Forma Urbis Romae (Severan Marble Plan)", "203–211 CE", "Rome",
               W + "Forma_Urbis_Romae")]),
    "ancient:carthage": _e(
        ["TUN"], "The North African coast and the western Mediterranean.",
        sites=[("carthage", "Carthage", 36.8529, 10.3217, "the great Punic sea-power", W + "Carthage")]),

    # ══ 6 · Persia & the Iranian world ══
    "ancient:achaemenid": _e(
        ["IRN"], "From the Indus to the Aegean — centred on Fars in Iran.",
        sites=[
            ("persepolis", "Persepolis", 29.9355, 52.8916, "the ceremonial capital", W + "Persepolis"),
            ("pasargadae", "Pasargadae", 30.1939, 53.1672, "Cyrus's capital and tomb", W + "Pasargadae"),
        ]),
    "ancient:parthia": _e(
        ["IRN", "IRQ", "TKM"], "The Iranian plateau and Mesopotamia — Rome's eastern rival.",
        sites=[("ctesiphon", "Ctesiphon", 33.0936, 44.5808, "the great arched palace", W + "Ctesiphon")]),
    "ancient:sasanian": _e(
        ["IRN", "IRQ"], "The Iranian plateau and Mesopotamia — the last pre-Islamic Persia.",
        sites=[("firuzabad", "Firuzabad (Gor)", 28.8529, 52.5327, "Ardashir's round city and palace", W + "Palace_of_Ardashir")]),
    "ancient:media": _e(
        ["IRN"], "Northwestern Iran — the Zagros around Hamadan.",
        sites=[("ecbatana", "Ecbatana", 34.8064, 48.5161, "the Median capital (Hamadan)", W + "Ecbatana")]),
    "ancient:scythian": _e(
        ["UKR", "RUS", "KAZ"], "The Pontic–Caspian steppe — mounted nomads of the grasslands.",
        sites=[("chertomlyk", "Chertomlyk", 47.7176, 34.2993, "a royal Scythian kurgan", "https://www.megalithic.co.uk/article.php?sid=56468")]),
    "ancient:xiongnu": _e(
        ["MNG", "CHN"], "The Mongolian steppe — the great northern confederation.",
        sites=[("noin_ula", "Noin-Ula", 48.3862, 106.7550, "royal Xiongnu burial mounds", W + "Noin-Ula_burial_site")]),
    "ancient:sogdia": _e(
        ["UZB", "TJK"], "Transoxiana — the Zeravshan valley on the Silk Road.",
        sites=[("samarkand", "Samarkand (Afrasiab)", 39.6714, 66.9878, "the Sogdian merchant city", W + "Afrasiyab_(Samarkand)")]),
    "ancient:kushan": _e(
        ["AFG", "PAK", "IND", "TJK", "UZB"], "Bactria to the Ganges — the Silk-Road empire.",
        sites=[("begram", "Begram", 34.9403, 69.2550, "the Kushan royal treasure", W + "Bagram")]),

    # ══ 7 · Northern & Western Europe ══
    "ancient:celt": _e(
        ["FRA", "GBR", "IRL", "DEU"], "Iron-age western and central Europe.",
        sites=[("hallstatt", "Hallstatt", 47.5635, 13.6367, "the salt-mine culture", W + "Hallstatt")]),
    "ancient:thracian": _e(
        ["BGR", "ROU", "GRC", "TUR"], "The eastern Balkans — between the Danube and the Aegean.",
        sites=[("kazanlak", "Kazanlak", 42.6258, 25.3992, "the painted Thracian tomb", W + "Thracian_Tomb_of_Kazanlak")]),
    "ancient:norse": _e(
        ["NOR", "SWE", "DNK", "ISL"], "Scandinavia and the North Atlantic.",
        sites=[("jelling", "Jelling", 55.7567, 9.4194, "the royal runestones", W + "Jelling_stones")]),
    "ancient:iberian": _e(
        ["ESP", "PRT"], "The pre-Roman Iberian peninsula.",
        sites=[("dama_de_elche_site", "Elche (La Alcudia)", 38.2392, -0.6953, "site of the Lady of Elche", W + "La_Alcudia")]),

    # ══ 8 · Mesoamerica ══
    "ancient:olmec": _e(
        ["MEX"], "The Gulf coast lowlands of southern Mexico.",
        sites=[("la_venta", "La Venta", 18.1033, -94.0402, "the colossal stone heads", W + "La_Venta")]),
    "ancient:maya": _e(
        ["MEX", "GTM", "BLZ", "HND", "SLV"], "The Yucatán and the highlands of Central America.",
        sites=[
            ("tikal", "Tikal", 17.2219, -89.6236, "the great jungle city", W + "Tikal"),
            ("chichen_itza", "Chichén Itzá", 20.6829, -88.5686, "El Castillo pyramid", W + "Chichen_Itza"),
        ]),
    "ancient:zapotec": _e(
        ["MEX"], "The valley of Oaxaca in southern Mexico.",
        sites=[("monte_alban", "Monte Albán", 17.0439, -96.7678, "the mountaintop capital", W + "Monte_Alb%C3%A1n")]),
    "ancient:teotihuacan": _e(
        ["MEX"], "The basin of Mexico, northeast of the lake.",
        sites=[("teotihuacan", "Teotihuacan", 19.6925, -98.8438, "the Pyramids of the Sun and Moon", W + "Teotihuacan")]),
    "ancient:toltec": _e(
        ["MEX"], "Central Mexico — the Toltec capital north of the basin.",
        sites=[("tula", "Tula", 20.0642, -99.3408, "the Atlantean warrior columns", W + "Tula_(Mesoamerican_site)")]),
    "ancient:aztec": _e(
        ["MEX"], "The basin of Mexico — the island capital in the lake.",
        sites=[("tenochtitlan", "Tenochtitlan", 19.4349, -99.1314, "the Templo Mayor; Mexico City", W + "Templo_Mayor")]),

    # ══ 9 · The Andes & South America ══
    "ancient:caral": _e(
        ["PER"], "The Supe valley on the central Peruvian coast.",
        sites=[("caral", "Caral", -10.8936, -77.5203, "the oldest city in the Americas", W + "Caral")]),
    "ancient:chavin": _e(
        ["PER"], "The Peruvian highlands, east of the coastal range.",
        sites=[("chavin_de_huantar", "Chavín de Huántar", -9.5928, -77.1785, "the carved stone temple", W + "Chav%C3%ADn_de_Hu%C3%A1ntar")]),
    "ancient:nazca": _e(
        ["PER"], "The southern desert coast of Peru.",
        sites=[("nazca_lines", "Nazca", -14.7390, -75.1301, "the great desert geoglyphs", W + "Nazca_Lines")]),
    "ancient:moche": _e(
        ["PER"], "The northern desert coast river valleys of Peru.",
        sites=[("huacas_de_moche", "Huacas de Moche", -8.1322, -78.9947, "the Huaca del Sol and de la Luna", W + "Huaca_del_Sol")]),
    "ancient:tiwanaku": _e(
        ["BOL", "PER"], "The Lake Titicaca altiplano.",
        sites=[("tiwanaku", "Tiwanaku", -16.5547, -68.6733, "the Gate of the Sun", W + "Tiwanaku")]),
    "ancient:wari": _e(
        ["PER"], "The central Peruvian highlands around Ayacucho.",
        sites=[("wari", "Wari", -13.0606, -74.1989, "the highland imperial capital", W + "Wari_(archaeological_site)")]),
    "ancient:chimu": _e(
        ["PER"], "The northern coast of Peru — the Moche valley.",
        sites=[("chan_chan", "Chan Chan", -8.1058, -79.0744, "the great adobe city", W + "Chan_Chan")]),
    "ancient:inca": _e(
        ["PER", "BOL", "ECU", "CHL", "ARG", "COL"], "The Andes from Ecuador to Chile — Tawantinsuyu.",
        sites=[
            ("cusco", "Cusco", -13.5173, -71.9800, "the Inca capital", W + "Cusco"),
            ("machu_picchu", "Machu Picchu", -13.1631, -72.5450, "the royal estate in the clouds", W + "Machu_Picchu"),
        ]),

    # ══ 10 · Ancient North America ══
    "ancient:puebloan": _e(
        ["USA"], "The Four Corners of the American Southwest.",
        sites=[("mesa_verde", "Mesa Verde (Cliff Palace)", 37.1666, -108.4733, "the cliff dwellings", W + "Mesa_Verde_National_Park")]),
    "ancient:hohokam": _e(
        ["USA"], "The Sonoran desert of southern Arizona.",
        sites=[("snaketown", "Snaketown", 33.1875, -111.9245, "the great canal-irrigation town", W + "Snaketown")]),
    "ancient:hopewell": _e(
        ["USA"], "The Ohio and Mississippi valleys of the Eastern Woodlands.",
        sites=[("hopewell_mounds", "Mound City", 39.3760, -83.0070, "the great earthwork mounds", W + "Hopewell_Culture_National_Historical_Park")]),
    "ancient:cahokia": _e(
        ["USA"], "The Mississippi floodplain opposite modern St. Louis.",
        sites=[("cahokia", "Cahokia", 38.6607, -90.0620, "Monks Mound; the great plaza", W + "Cahokia")]),

    # ══ 11 · Sub-Saharan Africa ══
    "ancient:nok": _e(
        ["NGA"], "The Jos plateau of central Nigeria.",
        sites=[("nok", "Nok", 9.5000, 8.0000, "the terracotta sculpture culture (area centroid)", "https://latitude.to/satellite-map/ng/nigeria/7348/nok-culture")]),
    "ancient:aksum": _e(
        ["ETH", "ERI"], "The Ethiopian highlands near the Red Sea.",
        sites=[("axum", "Aksum", 14.1322, 38.7197, "the great carved stelae", W + "Axum")]),
    "ancient:ghana": _e(
        ["MRT", "MLI"], "The western Sahel — the gold trade of the upper Niger (NOT modern Ghana).",
        sites=[("koumbi_saleh", "Koumbi Saleh", 15.7656, -7.9686, "the reputed capital of Ghana", W + "Koumbi_Saleh")]),
    "ancient:mali": _e(
        ["MLI", "GIN", "SEN", "MRT"], "The upper Niger — the empire of Mansa Musa.",
        sites=[("timbuktu", "Timbuktu", 16.7666, -3.0026, "the Saharan city of gold and learning", W + "Timbuktu")]),
    "ancient:songhai": _e(
        ["MLI", "NER"], "The Niger bend — the greatest of the Sahelian empires.",
        sites=[("gao", "Gao", 16.2670, -0.0500, "the Songhai capital", W + "Gao")]),
    "ancient:benin": _e(
        ["NGA"], "The southern Nigerian forest — the kingdom of Benin.",
        sites=[("benin_city", "Benin City", 6.3333, 5.6222, "the walled city; the bronzes", W + "Benin_City")]),
    "ancient:great_zimbabwe": _e(
        ["ZWE"], "The Zimbabwe plateau between the Zambezi and Limpopo.",
        sites=[("great_zimbabwe", "Great Zimbabwe", -20.2674, 30.9335, "the great dry-stone enclosures", W + "Great_Zimbabwe")]),
    "ancient:swahili": _e(
        ["KEN", "TZA", "MOZ", "SOM"], "The East African coast — the Indian Ocean trade towns.",
        sites=[("kilwa", "Kilwa Kisiwani", -8.9600, 39.5128, "the great coral-stone port", W + "Kilwa_Kisiwani")]),

    # ══ 12 · Oceania & the Pacific ══
    "ancient:lapita": _e(
        ["PNG", "FJI", "VUT", "TON"], "Island Melanesia into western Polynesia — the great ocean expansion.",
        sites=[("teouma", "Teouma", -17.7856, 168.3862, "the oldest cemetery in the Pacific", W + "Teouma")]),
    "ancient:polynesia": _e(
        ["WSM", "TON", "PYF"], "The central Pacific — the triangle of island voyagers.",
        sites=[("taputapuatea", "Taputapuatea", -16.8361, -151.3592, "the great ocean-voyaging marae", W + "Taputapuatea_marae")]),
    "ancient:rapa_nui": _e(
        ["CHL"], "Easter Island — the loneliest inhabited island.",
        sites=[("rano_raraku", "Rano Raraku", -27.1242, -109.2859, "the moai quarry", W + "Rano_Raraku")]),
    "ancient:maori": _e(
        ["NZL"], "Aotearoa / New Zealand — the last great landfall.",
        sites=[("wairau_bar", "Wairau Bar", -41.5094, 174.0638, "the earliest Māori settlement", W + "Wairau_Bar")]),
    "ancient:tonga": _e(
        ["TON"], "The Tongan archipelago — the Pacific's maritime chiefdom.",
        sites=[("haamonga", "Haʻamonga ʻa Maui", -21.1367, -175.0481, "the great stone trilithon", W + "Ha%CA%BBamonga_%CA%BBa_Maui")]),
    "ancient:aboriginal_australia": _e(
        ["AUS"], "The Australian continent — the oldest continuous culture on earth.",
        sites=[("uluru", "Uluru", -25.3450, 131.0361, "the sacred monolith", W + "Uluru")]),

    # ══ 13 · Southeast Asia ══
    "ancient:funan": _e(
        ["KHM", "VNM"], "The Mekong delta — the first great Southeast-Asian state.",
        sites=[("oc_eo", "Óc Eo", 10.2328, 105.1517, "the delta trading port", W + "%C3%93c_Eo")]),
    "ancient:champa": _e(
        ["VNM"], "The central Vietnamese coast — the Cham maritime kingdoms.",
        sites=[("my_son", "Mỹ Sơn", 15.7670, 108.1170, "the brick Hindu temple valley", W + "M%E1%BB%B9_S%C6%A1n")]),
    "ancient:srivijaya": _e(
        ["IDN", "MYS"], "Sumatra and the Malacca strait — the sea-trade thalassocracy.",
        sites=[("palembang", "Palembang", -2.9909, 104.7566, "the reputed Srivijayan capital", W + "Palembang")]),
    "ancient:khmer": _e(
        ["KHM", "THA", "LAO"], "The lower Mekong and the Tonlé Sap — the Angkorian empire.",
        sites=[("angkor", "Angkor", 13.4125, 103.8667, "Angkor Wat; the great temple-city", W + "Angkor")]),
    "ancient:pagan": _e(
        ["MMR"], "The dry zone of the Irrawaddy — the first Burmese kingdom.",
        sites=[("bagan", "Bagan", 21.1725, 94.8600, "the plain of a thousand temples", W + "Bagan")]),
    "ancient:majapahit": _e(
        ["IDN"], "Eastern Java and the archipelago — the last great Hindu-Buddhist empire.",
        sites=[("trowulan", "Trowulan", -7.5419, 112.3910, "the reputed Majapahit capital", W + "Trowulan")]),
}
