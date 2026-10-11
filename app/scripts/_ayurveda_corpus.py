"""
Ayurveda stylometry corpus — data only (no code).

Two stratified classical saṃhitās (the Dṛḍhabala redaction of the Caraka Saṃhitā; the Uttaratantra
appended to the Suśruta Saṃhitā), the upstream source-stream nodes (Atharvaveda → Agniveśa-tantra;
the surgical Dhanvantari root), and the downstream synthesis (Vāgbhaṭa's Aṣṭāṅgahṛdaya). Consumed by
app/scripts/stylometry_lab.py (the driver) and app/scripts/gen_stylometry_ak.py (the durable .ak + matrix).

The matrices are DEFENSIBLE ILLUSTRATIVE tables grounded in the philology (Meulenbeld, HIML): the
Caraka seam falls where Dṛḍhabala's supplement begins (Cikitsāsthāna ch. XIV, + Kalpa + Siddhi); the
Suśruta seam falls before the Uttaratantra. Replace with measured values via io.ingest model=sty.
"""

# ── the Caraka Saṃhitā (Ātreya school; Agniveśa → Caraka → Dṛḍhabala) ──
CARAKA = {
    "id": "caraka_samhita",
    "title": "Caraka Saṃhitā — the Ātreya-school compendium",
    "lang": "sa",
    "derives": ["agnivesha_tantra"],
    "cross": ["tradition:ayurveda", "textcrit:recension", "textcrit:interpolation"],
    "witnesses": [
        ("caraka_pali_ed", "The vulgate Sanskrit text (Yādavaśarman ed.)", "sa"),
        ("caraka_tibetan", "The Tibetan Tanjur version", "bo"),
    ],
    "layers": [
        ("cs_caraka_core", "Caraka's redaction (Ātreya–Agniveśa core)",
            "The five-and-a-half sthānas transmitted from Agniveśa and redacted by Caraka."),
        ("cs_dridhabala", "Dṛḍhabala's supplement",
            "The final ~third (Cikitsā XIV–XXX, Kalpa, Siddhi), supplied by Dṛḍhabala (c. 4th–5th c.)."),
    ],
    # id, title, layer, attested-in
    "loci": [
        ("cs_sutra",     "Sūtrasthāna",              "cs_caraka_core", "caraka_pali_ed,caraka_tibetan"),
        ("cs_nidana",    "Nidānasthāna",             "cs_caraka_core", "caraka_pali_ed,caraka_tibetan"),
        ("cs_vimana",    "Vimānasthāna",             "cs_caraka_core", "caraka_pali_ed,caraka_tibetan"),
        ("cs_sharira",   "Śārīrasthāna",             "cs_caraka_core", "caraka_pali_ed,caraka_tibetan"),
        ("cs_indriya",   "Indriyasthāna",            "cs_caraka_core", "caraka_pali_ed,caraka_tibetan"),
        ("cs_cikitsa_a", "Cikitsāsthāna I–XIII",     "cs_caraka_core", "caraka_pali_ed,caraka_tibetan"),
        ("cs_cikitsa_b", "Cikitsāsthāna XIV–XXX",    "cs_dridhabala",  "caraka_pali_ed"),
        ("cs_kalpa",     "Kalpasthāna",              "cs_dridhabala",  "caraka_pali_ed"),
        ("cs_siddhi",    "Siddhisthāna",             "cs_dridhabala",  "caraka_pali_ed"),
    ],
    # feature = (id, title, desc, higher, LENS) — the interdisciplinary move: one work, many
    # feature spaces measured across the SAME loci (stylometry · attestation · chronology ·
    # geography · concept). sty.cross overlays their boundaries.
    "features": [
        ("cs_lexical_richness",  "Lexical richness",       "Moving-average type–token ratio.", "", "stylometry"),
        ("cs_verse_ratio",       "Verse:prose ratio",      "Share of the section in metrical verse (Dṛḍhabala versifies more).", "", "stylometry"),
        ("cs_colophon_selfref",  "Colophon self-reference","Rate of redactor self-naming / restoration formulae.", "", "stylometry"),
        ("cs_term_density",      "Technical-term density", "Density of nosological / pharmacological technical terms.", "", "stylometry"),
        ("cs_meter_regularity",  "Metre regularity",       "Regularity of the śloka metre.", "", "stylometry"),
        ("cs_parallel_attest",   "Parallel attestation",   "External parallel present (Tibetan / early quotation): 1 core, 0 supplement.", "", "attestation"),
        ("cs_date_ce",           "Composition date (CE)",  "Estimated century of the stratum, CE (Caraka's redaction vs Dṛḍhabala's supplement).", "", "chronology"),
        ("cs_region_lon",        "Region (longitude °E)",  "Approx. longitude of composition — both strata are north-west Indian (≈ 75–76 °E).", "", "geography"),
        ("cs_doctrine_novelty",  "Doctrinal novelty",      "Density of newly-introduced doctrine / technical concepts (via thesaurus drift).", "", "concept"),
    ],
    "seams": [
        ("cs_dridhabala_seam", "cs_cikitsa_a", "Core ▸ Dṛḍhabala — where the supplement begins (Cikitsā XIV). The principal join."),
    ],
    "hyps": [
        ("cs_third", "Dṛḍhabala supplied a third (mainstream)",
            "Dṛḍhabala restored the last seventeen Cikitsā chapters plus the whole Kalpa- and Siddhi-sthānas — about a third of the work.",
            "cs_dridhabala_seam", "cs_caraka_core,cs_dridhabala"),
        ("cs_minimal", "Only Kalpa and Siddhi restored",
            "A minimal reading: Dṛḍhabala restored only the two lost final sthānas; the Cikitsāsthāna is substantially Caraka's.",
            "", "cs_caraka_core,cs_dridhabala"),
        ("cs_unitary", "Substantially Caraka's",
            "A minority view: the received text is essentially Caraka's redaction, the Dṛḍhabala note a late colophon.",
            "", ""),
    ],
    # stylometry+attestation+chronology+concept all break at cs_cikitsa_a → cs_cikitsa_b (the seam);
    # GEOGRAPHY is deliberately continuous (both strata NW Indian) → the lens that ABSTAINS.
    "matrix": {
        "cs_sutra":     {"cs_lexical_richness": 0.72, "cs_verse_ratio": 0.50, "cs_colophon_selfref": 0.02, "cs_term_density": 0.60, "cs_meter_regularity": 0.60, "cs_parallel_attest": 1, "cs_date_ce": 150, "cs_region_lon": 76.0, "cs_doctrine_novelty": 0.25},
        "cs_nidana":    {"cs_lexical_richness": 0.70, "cs_verse_ratio": 0.54, "cs_colophon_selfref": 0.02, "cs_term_density": 0.68, "cs_meter_regularity": 0.61, "cs_parallel_attest": 1, "cs_date_ce": 150, "cs_region_lon": 75.4, "cs_doctrine_novelty": 0.22},
        "cs_vimana":    {"cs_lexical_richness": 0.69, "cs_verse_ratio": 0.50, "cs_colophon_selfref": 0.03, "cs_term_density": 0.62, "cs_meter_regularity": 0.60, "cs_parallel_attest": 1, "cs_date_ce": 160, "cs_region_lon": 76.2, "cs_doctrine_novelty": 0.24},
        "cs_sharira":   {"cs_lexical_richness": 0.71, "cs_verse_ratio": 0.56, "cs_colophon_selfref": 0.02, "cs_term_density": 0.55, "cs_meter_regularity": 0.62, "cs_parallel_attest": 1, "cs_date_ce": 150, "cs_region_lon": 75.6, "cs_doctrine_novelty": 0.20},
        "cs_indriya":   {"cs_lexical_richness": 0.68, "cs_verse_ratio": 0.52, "cs_colophon_selfref": 0.03, "cs_term_density": 0.60, "cs_meter_regularity": 0.60, "cs_parallel_attest": 1, "cs_date_ce": 150, "cs_region_lon": 76.1, "cs_doctrine_novelty": 0.23},
        "cs_cikitsa_a": {"cs_lexical_richness": 0.70, "cs_verse_ratio": 0.50, "cs_colophon_selfref": 0.04, "cs_term_density": 0.72, "cs_meter_regularity": 0.60, "cs_parallel_attest": 1, "cs_date_ce": 160, "cs_region_lon": 75.5, "cs_doctrine_novelty": 0.28},
        "cs_cikitsa_b": {"cs_lexical_richness": 0.62, "cs_verse_ratio": 0.74, "cs_colophon_selfref": 0.55, "cs_term_density": 0.66, "cs_meter_regularity": 0.78, "cs_parallel_attest": 0, "cs_date_ce": 450, "cs_region_lon": 75.9, "cs_doctrine_novelty": 0.70},
        "cs_kalpa":     {"cs_lexical_richness": 0.60, "cs_verse_ratio": 0.80, "cs_colophon_selfref": 0.60, "cs_term_density": 0.70, "cs_meter_regularity": 0.80, "cs_parallel_attest": 0, "cs_date_ce": 460, "cs_region_lon": 75.3, "cs_doctrine_novelty": 0.78},
        "cs_siddhi":    {"cs_lexical_richness": 0.61, "cs_verse_ratio": 0.78, "cs_colophon_selfref": 0.58, "cs_term_density": 0.72, "cs_meter_regularity": 0.79, "cs_parallel_attest": 0, "cs_date_ce": 450, "cs_region_lon": 75.8, "cs_doctrine_novelty": 0.72},
    },
}

# ── the Suśruta Saṃhitā (Dhanvantari surgical school; core + Uttaratantra) ──
SUSRUTA = {
    "id": "susruta_samhita",
    "title": "Suśruta Saṃhitā — the surgical compendium",
    "lang": "sa",
    "derives": ["atharvaveda"],
    "cross": ["tradition:ayurveda", "textcrit:interpolation"],
    "witnesses": [("susruta_ed", "The vulgate Sanskrit text (Trikamji ed.)", "sa")],
    "layers": [
        ("ss_core", "The surgical core", "The original five sthānas of the surgical treatise."),
        ("ss_uttara", "The Uttaratantra", "The appended supplement — ophthalmology, ENT, toxicology, later doctrine."),
    ],
    "loci": [
        ("ss_sutra",   "Sūtrasthāna",   "ss_core",   "susruta_ed"),
        ("ss_nidana",  "Nidānasthāna",  "ss_core",   "susruta_ed"),
        ("ss_sharira", "Śārīrasthāna",  "ss_core",   "susruta_ed"),
        ("ss_cikitsa", "Cikitsāsthāna", "ss_core",   "susruta_ed"),
        ("ss_kalpa",   "Kalpasthāna",   "ss_core",   "susruta_ed"),
        ("ss_uttara",  "Uttaratantra",  "ss_uttara", "susruta_ed"),
    ],
    "features": [
        ("ss_lexical_richness",  "Lexical richness",       "Moving-average type–token ratio.", "", "stylometry"),
        ("ss_surgical_density",  "Surgical-term density",  "Density of the śalya (surgical) vocabulary — high in the core.", "", "stylometry"),
        ("ss_ophthalmic_density","Ophthalmic/ENT density", "Density of the netra/karṇa vocabulary — high in the Uttaratantra.", "", "stylometry"),
        ("ss_meter_regularity",  "Metre regularity",       "Regularity of the śloka metre.", "", "stylometry"),
        ("ss_parallel_attest",   "Parallel attestation",   "External parallel present: 1 core, 0 Uttaratantra.", "", "attestation"),
        ("ss_date_ce",           "Composition date (CE)",  "Estimated century of the stratum, CE.", "", "chronology"),
        ("ss_region_lon",        "Region (longitude °E)",  "Approx. longitude of composition — broadly north Indian.", "", "geography"),
        ("ss_doctrine_novelty",  "Doctrinal novelty",      "Density of newly-introduced doctrine / topics.", "", "concept"),
    ],
    "seams": [
        ("ss_uttara_seam", "ss_kalpa", "Core ▸ Uttaratantra — where the appended supplement begins."),
    ],
    "hyps": [
        ("ss_later", "The Uttaratantra is a later addition (mainstream)",
            "The five original sthānas form the surgical treatise; the Uttaratantra is a later supplement of distinct topics and doctrine.",
            "ss_uttara_seam", "ss_core,ss_uttara"),
        ("ss_unitary", "Substantially unified",
            "A minority view: the Uttaratantra belongs to the original design.",
            "", ""),
    ],
    "matrix": {
        "ss_sutra":   {"ss_lexical_richness": 0.70, "ss_surgical_density": 0.80, "ss_ophthalmic_density": 0.10, "ss_meter_regularity": 0.60, "ss_parallel_attest": 1, "ss_date_ce": 100, "ss_region_lon": 83.0, "ss_doctrine_novelty": 0.20},
        "ss_nidana":  {"ss_lexical_richness": 0.69, "ss_surgical_density": 0.62, "ss_ophthalmic_density": 0.14, "ss_meter_regularity": 0.60, "ss_parallel_attest": 1, "ss_date_ce": 110, "ss_region_lon": 82.4, "ss_doctrine_novelty": 0.22},
        "ss_sharira": {"ss_lexical_richness": 0.71, "ss_surgical_density": 0.52, "ss_ophthalmic_density": 0.10, "ss_meter_regularity": 0.61, "ss_parallel_attest": 1, "ss_date_ce": 100, "ss_region_lon": 83.2, "ss_doctrine_novelty": 0.19},
        "ss_cikitsa": {"ss_lexical_richness": 0.70, "ss_surgical_density": 0.78, "ss_ophthalmic_density": 0.18, "ss_meter_regularity": 0.60, "ss_parallel_attest": 1, "ss_date_ce": 110, "ss_region_lon": 82.6, "ss_doctrine_novelty": 0.24},
        "ss_kalpa":   {"ss_lexical_richness": 0.68, "ss_surgical_density": 0.55, "ss_ophthalmic_density": 0.12, "ss_meter_regularity": 0.60, "ss_parallel_attest": 1, "ss_date_ce": 120, "ss_region_lon": 83.1, "ss_doctrine_novelty": 0.23},
        "ss_uttara":  {"ss_lexical_richness": 0.63, "ss_surgical_density": 0.30, "ss_ophthalmic_density": 0.85, "ss_meter_regularity": 0.72, "ss_parallel_attest": 0, "ss_date_ce": 500, "ss_region_lon": 82.7, "ss_doctrine_novelty": 0.80},
    },
}

STRATIFIED = [CARAKA, SUSRUTA]

# ── genealogy-only nodes (no matrix) : the upstream streams + the downstream synthesis ──
# id, title, note, kind, derives-from
SOURCE_NODES = [
    ("atharvaveda", "Atharvaveda", "The Vedic hymns of healing (bhaiṣajyāni) — the pre-classical root of Indian medicine.", "source", []),
    ("agnivesha_tantra", "Agniveśa-tantra", "The lost ur-text of the Ātreya school, the base Caraka redacted.", "source", ["atharvaveda"]),
    ("astangahrdaya", "Aṣṭāṅgahṛdaya (Vāgbhaṭa)", "Vāgbhaṭa's synthesis (c. 7th c.) — the confluence of the Caraka and Suśruta streams.", "synthesis", ["caraka_samhita", "susruta_samhita"]),
]

# cross-links from the genealogy nodes into the existing ontology
NODE_CROSS = {
    "atharvaveda": ["ancient:vedic", "tradition:ayurveda"],
    "agnivesha_tantra": ["tradition:ayurveda"],
    "astangahrdaya": ["tradition:ayurveda"],
}

# shared sources (added to sty:sources; support/contest the Ayurveda hypotheses)
SOURCES = [
    ("meulenbeld_himl", "A History of Indian Medical Literature (HIML)", "G. Jan Meulenbeld", "1999",
        "cs_third,ss_later", "cs_unitary,ss_unitary", "vol. IA–IIB (1999–2002) — the definitive dating & authorship study"),
    ("dridhabala_colophon", "Dṛḍhabala's colophon verse", "Dṛḍhabala", "c. 400",
        "cs_third", "", "Siddhisthāna, closing verses — the redactor names his supplement"),
    ("sharma_dash", "Caraka Saṃhitā (text · translation · notes)", "R.K. Sharma & Bhagwan Dash", "1976",
        "cs_third", "", "Chowkhamba, with critical notes on the strata"),
    ("hoernle_1907", "Studies in the Medicine of Ancient India", "A.F.R. Hoernle", "1907",
        "cs_third", "", "osteology; early stratification scholarship"),
    ("susruta_uttara_note", "On the Uttaratantra of the Suśruta Saṃhitā", "P. V. Sharma", "1999",
        "ss_later", "", "the supplement's distinct topics and later doctrine"),
]


# ── DEMO ENRICHMENT ─────────────────────────────────────────────────────────────
# Break out of the philology frame: two NON-TEXTUAL lenses (botany — the density of named
# plant-drug material; tradition — the teaching lineage), and real materia-medica links from
# each stratum into the existing ayurveda:* ontology (herbs, formulas, doshas, dhātus …).
# The botanical structure of the text breaks where THERAPEUTICS begins (Cikitsā), one section
# before the authorial Dṛḍhabala seam — a genuinely different structure the cross reveals.
DEMO = {
    "caraka_samhita": {
        "features": [
            ("cs_materia_medica", "Materia-medica density", "Density of named plant-drug material (dravya) — the botanical signal, beyond the words.", "", "botany"),
            ("cs_lineage",        "Transmission lineage",   "The teaching lineage a stratum belongs to (Ātreya–Caraka core = 1, Dṛḍhabala = 0).", "", "tradition"),
        ],
        "matrix": {
            "cs_sutra":     {"cs_materia_medica": 0.20, "cs_lineage": 1},
            "cs_nidana":    {"cs_materia_medica": 0.25, "cs_lineage": 1},
            "cs_vimana":    {"cs_materia_medica": 0.20, "cs_lineage": 1},
            "cs_sharira":   {"cs_materia_medica": 0.15, "cs_lineage": 1},
            "cs_indriya":   {"cs_materia_medica": 0.10, "cs_lineage": 1},
            "cs_cikitsa_a": {"cs_materia_medica": 0.85, "cs_lineage": 1},
            "cs_cikitsa_b": {"cs_materia_medica": 0.80, "cs_lineage": 0},
            "cs_kalpa":     {"cs_materia_medica": 0.92, "cs_lineage": 0},
            "cs_siddhi":    {"cs_materia_medica": 0.55, "cs_lineage": 0},
        },
        # real ayurveda:* atoms each stratum discusses — the "beyond the text" panel + @discusses links
        "context": {
            "cs_sutra":     ["ayurveda:dosha:vata", "ayurveda:dosha:pitta", "ayurveda:dosha:kapha", "ayurveda:rasa:sweet", "ayurveda:agni"],
            "cs_nidana":    ["ayurveda:vikriti", "ayurveda:ama"],
            "cs_vimana":    ["ayurveda:agni", "ayurveda:prakriti"],
            "cs_sharira":   ["ayurveda:dhatu", "ayurveda:srotas"],
            "cs_indriya":   ["ayurveda:ama"],
            "cs_cikitsa_a": ["ayurveda:herb:ashwagandha", "ayurveda:herb:guduchi", "ayurveda:rasayana", "ayurveda:formula:chyawanprash"],
            "cs_cikitsa_b": ["ayurveda:herb:haridra", "ayurveda:herb:tulsi", "ayurveda:herb:neem"],
            "cs_kalpa":     ["ayurveda:formula:triphala", "ayurveda:herb:haritaki", "ayurveda:herb:amalaki", "ayurveda:herb:bibhitaki",
                             "ayurveda:formula:trikatu", "ayurveda:herb:pippali", "ayurveda:herb:shunthi", "ayurveda:herb:maricha"],
            "cs_siddhi":    ["ayurveda:herb:yashtimadhu"],
        },
    },
    "susruta_samhita": {
        "features": [
            ("ss_materia_medica", "Materia-medica density", "Density of named plant-drug material (dravya).", "", "botany"),
            ("ss_lineage",        "Transmission lineage",   "The teaching lineage (Dhanvantari core = 1, Uttaratantra = 0).", "", "tradition"),
        ],
        "matrix": {
            "ss_sutra":   {"ss_materia_medica": 0.25, "ss_lineage": 1},
            "ss_nidana":  {"ss_materia_medica": 0.20, "ss_lineage": 1},
            "ss_sharira": {"ss_materia_medica": 0.15, "ss_lineage": 1},
            "ss_cikitsa": {"ss_materia_medica": 0.70, "ss_lineage": 1},
            "ss_kalpa":   {"ss_materia_medica": 0.85, "ss_lineage": 1},
            "ss_uttara":  {"ss_materia_medica": 0.40, "ss_lineage": 0},
        },
        "context": {
            "ss_sutra":   ["ayurveda:dosha:vata", "ayurveda:rasa:sweet"],
            "ss_cikitsa": ["ayurveda:herb:haridra", "ayurveda:herb:yashtimadhu"],
            "ss_kalpa":   ["ayurveda:herb:neem"],
            "ss_uttara":  ["ayurveda:srotas"],
        },
    },
}
for _spec in STRATIFIED:
    _d = DEMO.get(_spec["id"])
    if _d:
        _spec["features"] = list(_spec["features"]) + _d["features"]
        for _loc, _add in _d["matrix"].items():
            _spec["matrix"][_loc].update(_add)
        _spec["context"] = _d["context"]
