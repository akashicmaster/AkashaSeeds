#!/usr/bin/env python3
"""
Enrich geo:country:* atoms in the Akasha nucleus.

For each of the 221 country atoms imported by import_plotly_geo.py, adds:
  - thesaurus:hypernym  → geo:continent:*
  - thesaurus:hypernym  → geo:region:*   (UN M.49 subregion)
  - thesaurus:hypernym  → geo:gdp_tier:* (derived from gdp_billions in meta)
  - geo:official_language → lang:*       (primary official language(s))
  - thesaurus:external_ref → Wikipedia   (stored as meta on the link atom)
  - sys:part_of         → org:united_nations (UN members only)

Requires ua_earth_enrichment.csl to have been loaded into the nucleus first
(continent/region/GDP-tier/language/org atoms must exist as named aliases).

Idempotent: checks existing outgoing link relations before creating new ones.

Run from project root:
  python app/seeds/enrich_geo_countries.py
"""

import sys
import os
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from lib.akasha.composite import NucleusEngine

BASE_DIR    = os.path.join(_ROOT, "data")
NUCLEUS_DB  = os.path.join(BASE_DIR, "central", "nucleus.db")
AUTHOR      = "system:import:geo_enrichment"
WIKI_BASE   = "https://en.wikipedia.org/wiki/"


# ── Continent mapping (ISO3 → continent alias) ────────────────────────────────

CONTINENT = {
    # Africa
    "DZA": "geo:continent:africa", "AGO": "geo:continent:africa",
    "BEN": "geo:continent:africa", "BWA": "geo:continent:africa",
    "BFA": "geo:continent:africa", "BDI": "geo:continent:africa",
    "CMR": "geo:continent:africa", "CPV": "geo:continent:africa",
    "CAF": "geo:continent:africa", "TCD": "geo:continent:africa",
    "COM": "geo:continent:africa", "COD": "geo:continent:africa",
    "COG": "geo:continent:africa", "CIV": "geo:continent:africa",
    "DJI": "geo:continent:africa", "EGY": "geo:continent:africa",
    "GNQ": "geo:continent:africa", "ERI": "geo:continent:africa",
    "ETH": "geo:continent:africa", "GAB": "geo:continent:africa",
    "GMB": "geo:continent:africa", "GHA": "geo:continent:africa",
    "GIN": "geo:continent:africa", "GNB": "geo:continent:africa",
    "KEN": "geo:continent:africa", "LSO": "geo:continent:africa",
    "LBR": "geo:continent:africa", "LBY": "geo:continent:africa",
    "MDG": "geo:continent:africa", "MWI": "geo:continent:africa",
    "MLI": "geo:continent:africa", "MRT": "geo:continent:africa",
    "MUS": "geo:continent:africa", "MAR": "geo:continent:africa",
    "MOZ": "geo:continent:africa", "NAM": "geo:continent:africa",
    "NER": "geo:continent:africa", "NGA": "geo:continent:africa",
    "RWA": "geo:continent:africa", "STP": "geo:continent:africa",
    "SEN": "geo:continent:africa", "SLE": "geo:continent:africa",
    "SOM": "geo:continent:africa", "ZAF": "geo:continent:africa",
    "SSD": "geo:continent:africa", "SDN": "geo:continent:africa",
    "SWZ": "geo:continent:africa", "TZA": "geo:continent:africa",
    "TGO": "geo:continent:africa", "TUN": "geo:continent:africa",
    "UGA": "geo:continent:africa", "ZMB": "geo:continent:africa",
    "ZWE": "geo:continent:africa", "ESH": "geo:continent:africa",
    # Asia
    "AFG": "geo:continent:asia",   "ARM": "geo:continent:asia",
    "AZE": "geo:continent:asia",   "BHR": "geo:continent:asia",
    "BGD": "geo:continent:asia",   "BTN": "geo:continent:asia",
    "BRN": "geo:continent:asia",   "KHM": "geo:continent:asia",
    "CHN": "geo:continent:asia",   "CYP": "geo:continent:asia",
    "GEO": "geo:continent:asia",   "IND": "geo:continent:asia",
    "IDN": "geo:continent:asia",   "IRN": "geo:continent:asia",
    "IRQ": "geo:continent:asia",   "ISR": "geo:continent:asia",
    "JPN": "geo:continent:asia",   "JOR": "geo:continent:asia",
    "KAZ": "geo:continent:asia",   "KWT": "geo:continent:asia",
    "KGZ": "geo:continent:asia",   "LAO": "geo:continent:asia",
    "LBN": "geo:continent:asia",   "MYS": "geo:continent:asia",
    "MDV": "geo:continent:asia",   "MNG": "geo:continent:asia",
    "MMR": "geo:continent:asia",   "NPL": "geo:continent:asia",
    "PRK": "geo:continent:asia",   "OMN": "geo:continent:asia",
    "PAK": "geo:continent:asia",   "PSE": "geo:continent:asia",
    "PHL": "geo:continent:asia",   "QAT": "geo:continent:asia",
    "SAU": "geo:continent:asia",   "SGP": "geo:continent:asia",
    "KOR": "geo:continent:asia",   "LKA": "geo:continent:asia",
    "SYR": "geo:continent:asia",   "TWN": "geo:continent:asia",
    "TJK": "geo:continent:asia",   "THA": "geo:continent:asia",
    "TLS": "geo:continent:asia",   "TUR": "geo:continent:asia",
    "TKM": "geo:continent:asia",   "ARE": "geo:continent:asia",
    "UZB": "geo:continent:asia",   "VNM": "geo:continent:asia",
    "YEM": "geo:continent:asia",
    # Europe
    "ALB": "geo:continent:europe", "AND": "geo:continent:europe",
    "AUT": "geo:continent:europe", "BLR": "geo:continent:europe",
    "BEL": "geo:continent:europe", "BIH": "geo:continent:europe",
    "BGR": "geo:continent:europe", "HRV": "geo:continent:europe",
    "CZE": "geo:continent:europe", "DNK": "geo:continent:europe",
    "EST": "geo:continent:europe", "FIN": "geo:continent:europe",
    "FRA": "geo:continent:europe", "DEU": "geo:continent:europe",
    "GRC": "geo:continent:europe", "HUN": "geo:continent:europe",
    "ISL": "geo:continent:europe", "IRL": "geo:continent:europe",
    "ITA": "geo:continent:europe", "XKX": "geo:continent:europe",
    "LVA": "geo:continent:europe", "LIE": "geo:continent:europe",
    "LTU": "geo:continent:europe", "LUX": "geo:continent:europe",
    "MKD": "geo:continent:europe", "MLT": "geo:continent:europe",
    "MDA": "geo:continent:europe", "MCO": "geo:continent:europe",
    "MNE": "geo:continent:europe", "NLD": "geo:continent:europe",
    "NOR": "geo:continent:europe", "POL": "geo:continent:europe",
    "PRT": "geo:continent:europe", "ROU": "geo:continent:europe",
    "RUS": "geo:continent:europe", "SMR": "geo:continent:europe",
    "SRB": "geo:continent:europe", "SVK": "geo:continent:europe",
    "SVN": "geo:continent:europe", "ESP": "geo:continent:europe",
    "SWE": "geo:continent:europe", "CHE": "geo:continent:europe",
    "UKR": "geo:continent:europe", "GBR": "geo:continent:europe",
    "VAT": "geo:continent:europe",
    # North America
    "ATG": "geo:continent:north_america", "BHS": "geo:continent:north_america",
    "BLZ": "geo:continent:north_america", "CAN": "geo:continent:north_america",
    "CRI": "geo:continent:north_america", "CUB": "geo:continent:north_america",
    "DMA": "geo:continent:north_america", "DOM": "geo:continent:north_america",
    "SLV": "geo:continent:north_america", "GRD": "geo:continent:north_america",
    "GTM": "geo:continent:north_america", "HTI": "geo:continent:north_america",
    "HND": "geo:continent:north_america", "JAM": "geo:continent:north_america",
    "MEX": "geo:continent:north_america", "NIC": "geo:continent:north_america",
    "PAN": "geo:continent:north_america", "KNA": "geo:continent:north_america",
    "LCA": "geo:continent:north_america", "VCT": "geo:continent:north_america",
    "TTO": "geo:continent:north_america", "USA": "geo:continent:north_america",
    "PRI": "geo:continent:north_america",
    # South America
    "ARG": "geo:continent:south_america", "BOL": "geo:continent:south_america",
    "BRA": "geo:continent:south_america", "CHL": "geo:continent:south_america",
    "COL": "geo:continent:south_america", "ECU": "geo:continent:south_america",
    "GUY": "geo:continent:south_america", "PRY": "geo:continent:south_america",
    "PER": "geo:continent:south_america", "SUR": "geo:continent:south_america",
    "URY": "geo:continent:south_america", "VEN": "geo:continent:south_america",
    # Oceania
    "AUS": "geo:continent:oceania", "FJI": "geo:continent:oceania",
    "KIR": "geo:continent:oceania", "MHL": "geo:continent:oceania",
    "FSM": "geo:continent:oceania", "NRU": "geo:continent:oceania",
    "NZL": "geo:continent:oceania", "PLW": "geo:continent:oceania",
    "PNG": "geo:continent:oceania", "WSM": "geo:continent:oceania",
    "SLB": "geo:continent:oceania", "TON": "geo:continent:oceania",
    "TUV": "geo:continent:oceania", "VUT": "geo:continent:oceania",
    # Territories, SAR, dependent territories — plotly non-standard codes
    "ABW": "geo:continent:north_america",  # Aruba
    "AIA": "geo:continent:north_america",  # Anguilla
    "ASM": "geo:continent:oceania",        # American Samoa
    "BHM": "geo:continent:north_america",  # Bahamas (plotly code, standard=BHS)
    "BMU": "geo:continent:north_america",  # Bermuda
    "BRB": "geo:continent:north_america",  # Barbados
    "COK": "geo:continent:oceania",        # Cook Islands
    "CUW": "geo:continent:north_america",  # Curaçao
    "CYM": "geo:continent:north_america",  # Cayman Islands
    "FLK": "geo:continent:south_america",  # Falkland Islands
    "FRO": "geo:continent:europe",         # Faroe Islands
    "GGY": "geo:continent:europe",         # Guernsey
    "GIB": "geo:continent:europe",         # Gibraltar
    "GRL": "geo:continent:north_america",  # Greenland
    "GUM": "geo:continent:oceania",        # Guam
    "HKG": "geo:continent:asia",           # Hong Kong
    "IMN": "geo:continent:europe",         # Isle of Man
    "JEY": "geo:continent:europe",         # Jersey
    "KSV": "geo:continent:europe",         # Kosovo (plotly code)
    "MAC": "geo:continent:asia",           # Macau
    "MAF": "geo:continent:north_america",  # Saint Martin
    "MNP": "geo:continent:oceania",        # Northern Mariana Islands
    "NCL": "geo:continent:oceania",        # New Caledonia
    "NIU": "geo:continent:oceania",        # Niue
    "PYF": "geo:continent:oceania",        # French Polynesia
    "SPM": "geo:continent:north_america",  # Saint Pierre and Miquelon
    "SXM": "geo:continent:north_america",  # Sint Maarten
    "SYC": "geo:continent:africa",         # Seychelles
    "VGB": "geo:continent:north_america",  # British Virgin Islands
    "WBG": "geo:continent:asia",           # West Bank (plotly code for PSE)
}


# ── UN M.49 Subregion mapping (ISO3 → region alias) ─────────────────────────

REGION = {
    # Northern Africa
    "DZA": "geo:region:northern_africa", "EGY": "geo:region:northern_africa",
    "LBY": "geo:region:northern_africa", "MAR": "geo:region:northern_africa",
    "SDN": "geo:region:northern_africa", "TUN": "geo:region:northern_africa",
    "ESH": "geo:region:northern_africa",
    # Western Africa
    "BEN": "geo:region:western_africa",  "BFA": "geo:region:western_africa",
    "CPV": "geo:region:western_africa",  "CIV": "geo:region:western_africa",
    "GMB": "geo:region:western_africa",  "GHA": "geo:region:western_africa",
    "GIN": "geo:region:western_africa",  "GNB": "geo:region:western_africa",
    "LBR": "geo:region:western_africa",  "MLI": "geo:region:western_africa",
    "MRT": "geo:region:western_africa",  "NER": "geo:region:western_africa",
    "NGA": "geo:region:western_africa",  "SEN": "geo:region:western_africa",
    "SLE": "geo:region:western_africa",  "TGO": "geo:region:western_africa",
    # Eastern Africa
    "BDI": "geo:region:eastern_africa",  "COM": "geo:region:eastern_africa",
    "DJI": "geo:region:eastern_africa",  "ERI": "geo:region:eastern_africa",
    "ETH": "geo:region:eastern_africa",  "KEN": "geo:region:eastern_africa",
    "MDG": "geo:region:eastern_africa",  "MWI": "geo:region:eastern_africa",
    "MUS": "geo:region:eastern_africa",  "MOZ": "geo:region:eastern_africa",
    "RWA": "geo:region:eastern_africa",  "SOM": "geo:region:eastern_africa",
    "SSD": "geo:region:eastern_africa",  "STP": "geo:region:eastern_africa",
    "TZA": "geo:region:eastern_africa",  "UGA": "geo:region:eastern_africa",
    "ZMB": "geo:region:eastern_africa",  "ZWE": "geo:region:eastern_africa",
    # Middle Africa
    "AGO": "geo:region:middle_africa",   "CMR": "geo:region:middle_africa",
    "CAF": "geo:region:middle_africa",   "TCD": "geo:region:middle_africa",
    "COD": "geo:region:middle_africa",   "COG": "geo:region:middle_africa",
    "GNQ": "geo:region:middle_africa",   "GAB": "geo:region:middle_africa",
    # Southern Africa
    "BWA": "geo:region:southern_africa", "LSO": "geo:region:southern_africa",
    "NAM": "geo:region:southern_africa", "ZAF": "geo:region:southern_africa",
    "SWZ": "geo:region:southern_africa",
    # Central Asia
    "KAZ": "geo:region:central_asia",   "KGZ": "geo:region:central_asia",
    "TJK": "geo:region:central_asia",   "TKM": "geo:region:central_asia",
    "UZB": "geo:region:central_asia",
    # Eastern Asia
    "CHN": "geo:region:eastern_asia",   "JPN": "geo:region:eastern_asia",
    "PRK": "geo:region:eastern_asia",   "KOR": "geo:region:eastern_asia",
    "MNG": "geo:region:eastern_asia",   "TWN": "geo:region:eastern_asia",
    # South-eastern Asia
    "BRN": "geo:region:southeastern_asia", "KHM": "geo:region:southeastern_asia",
    "IDN": "geo:region:southeastern_asia", "LAO": "geo:region:southeastern_asia",
    "MYS": "geo:region:southeastern_asia", "MMR": "geo:region:southeastern_asia",
    "PHL": "geo:region:southeastern_asia", "SGP": "geo:region:southeastern_asia",
    "THA": "geo:region:southeastern_asia", "TLS": "geo:region:southeastern_asia",
    "VNM": "geo:region:southeastern_asia",
    # Southern Asia
    "AFG": "geo:region:southern_asia",  "BGD": "geo:region:southern_asia",
    "BTN": "geo:region:southern_asia",  "IND": "geo:region:southern_asia",
    "IRN": "geo:region:southern_asia",  "MDV": "geo:region:southern_asia",
    "NPL": "geo:region:southern_asia",  "PAK": "geo:region:southern_asia",
    "LKA": "geo:region:southern_asia",
    # Western Asia
    "ARM": "geo:region:western_asia",   "AZE": "geo:region:western_asia",
    "BHR": "geo:region:western_asia",   "CYP": "geo:region:western_asia",
    "GEO": "geo:region:western_asia",   "IRQ": "geo:region:western_asia",
    "ISR": "geo:region:western_asia",   "JOR": "geo:region:western_asia",
    "KWT": "geo:region:western_asia",   "LBN": "geo:region:western_asia",
    "OMN": "geo:region:western_asia",   "PSE": "geo:region:western_asia",
    "QAT": "geo:region:western_asia",   "SAU": "geo:region:western_asia",
    "SYR": "geo:region:western_asia",   "TUR": "geo:region:western_asia",
    "ARE": "geo:region:western_asia",   "YEM": "geo:region:western_asia",
    # Eastern Europe
    "BLR": "geo:region:eastern_europe", "BGR": "geo:region:eastern_europe",
    "CZE": "geo:region:eastern_europe", "HUN": "geo:region:eastern_europe",
    "MDA": "geo:region:eastern_europe", "POL": "geo:region:eastern_europe",
    "ROU": "geo:region:eastern_europe", "RUS": "geo:region:eastern_europe",
    "SVK": "geo:region:eastern_europe", "UKR": "geo:region:eastern_europe",
    # Northern Europe
    "DNK": "geo:region:northern_europe", "EST": "geo:region:northern_europe",
    "FIN": "geo:region:northern_europe", "ISL": "geo:region:northern_europe",
    "IRL": "geo:region:northern_europe", "LVA": "geo:region:northern_europe",
    "LTU": "geo:region:northern_europe", "NOR": "geo:region:northern_europe",
    "SWE": "geo:region:northern_europe", "GBR": "geo:region:northern_europe",
    # Southern Europe
    "ALB": "geo:region:southern_europe", "AND": "geo:region:southern_europe",
    "BIH": "geo:region:southern_europe", "HRV": "geo:region:southern_europe",
    "GRC": "geo:region:southern_europe", "ITA": "geo:region:southern_europe",
    "XKX": "geo:region:southern_europe", "MLT": "geo:region:southern_europe",
    "MCO": "geo:region:southern_europe", "MNE": "geo:region:southern_europe",
    "MKD": "geo:region:southern_europe", "PRT": "geo:region:southern_europe",
    "SMR": "geo:region:southern_europe", "SRB": "geo:region:southern_europe",
    "SVN": "geo:region:southern_europe", "ESP": "geo:region:southern_europe",
    "VAT": "geo:region:southern_europe",
    # Western Europe
    "AUT": "geo:region:western_europe", "BEL": "geo:region:western_europe",
    "FRA": "geo:region:western_europe", "DEU": "geo:region:western_europe",
    "LIE": "geo:region:western_europe", "LUX": "geo:region:western_europe",
    "NLD": "geo:region:western_europe", "CHE": "geo:region:western_europe",
    # Caribbean
    "ATG": "geo:region:caribbean",  "BHS": "geo:region:caribbean",
    "BRB": "geo:region:caribbean",  "CUB": "geo:region:caribbean",
    "DMA": "geo:region:caribbean",  "DOM": "geo:region:caribbean",
    "GRD": "geo:region:caribbean",  "HTI": "geo:region:caribbean",
    "JAM": "geo:region:caribbean",  "KNA": "geo:region:caribbean",
    "LCA": "geo:region:caribbean",  "VCT": "geo:region:caribbean",
    "TTO": "geo:region:caribbean",  "PRI": "geo:region:caribbean",
    # Central America
    "BLZ": "geo:region:central_america", "CRI": "geo:region:central_america",
    "SLV": "geo:region:central_america", "GTM": "geo:region:central_america",
    "HND": "geo:region:central_america", "MEX": "geo:region:central_america",
    "NIC": "geo:region:central_america", "PAN": "geo:region:central_america",
    # Northern America
    "CAN": "geo:region:northern_america", "USA": "geo:region:northern_america",
    # South America
    "ARG": "geo:region:south_america", "BOL": "geo:region:south_america",
    "BRA": "geo:region:south_america", "CHL": "geo:region:south_america",
    "COL": "geo:region:south_america", "ECU": "geo:region:south_america",
    "GUY": "geo:region:south_america", "PRY": "geo:region:south_america",
    "PER": "geo:region:south_america", "SUR": "geo:region:south_america",
    "URY": "geo:region:south_america", "VEN": "geo:region:south_america",
    # Australia and New Zealand
    "AUS": "geo:region:australia_new_zealand", "NZL": "geo:region:australia_new_zealand",
    # Melanesia
    "FJI": "geo:region:melanesia",   "PNG": "geo:region:melanesia",
    "SLB": "geo:region:melanesia",   "VUT": "geo:region:melanesia",
    # Micronesia
    "KIR": "geo:region:micronesia",  "MHL": "geo:region:micronesia",
    "FSM": "geo:region:micronesia",  "NRU": "geo:region:micronesia",
    "PLW": "geo:region:micronesia",
    # Polynesia
    "WSM": "geo:region:polynesia",   "TON": "geo:region:polynesia",
    "TUV": "geo:region:polynesia",
    # Territories — plotly non-standard codes
    "ABW": "geo:region:caribbean",         # Aruba
    "AIA": "geo:region:caribbean",         # Anguilla
    "ASM": "geo:region:polynesia",         # American Samoa
    "BHM": "geo:region:caribbean",         # Bahamas (BHM = plotly, standard BHS)
    "BMU": "geo:region:northern_america",  # Bermuda
    "BRB": "geo:region:caribbean",         # Barbados (also in standard BRB above)
    "COK": "geo:region:polynesia",         # Cook Islands
    "CUW": "geo:region:caribbean",         # Curaçao
    "CYM": "geo:region:caribbean",         # Cayman Islands
    "FLK": "geo:region:south_america",     # Falkland Islands
    "FRO": "geo:region:northern_europe",   # Faroe Islands
    "GGY": "geo:region:northern_europe",   # Guernsey
    "GIB": "geo:region:southern_europe",   # Gibraltar
    "GRL": "geo:region:northern_america",  # Greenland
    "GUM": "geo:region:micronesia",        # Guam
    "HKG": "geo:region:eastern_asia",      # Hong Kong
    "IMN": "geo:region:northern_europe",   # Isle of Man
    "JEY": "geo:region:northern_europe",   # Jersey
    "KSV": "geo:region:southern_europe",   # Kosovo (plotly code)
    "MAC": "geo:region:eastern_asia",      # Macau
    "MAF": "geo:region:caribbean",         # Saint Martin
    "MNP": "geo:region:micronesia",        # Northern Mariana Islands
    "NCL": "geo:region:melanesia",         # New Caledonia
    "NIU": "geo:region:polynesia",         # Niue
    "PYF": "geo:region:polynesia",         # French Polynesia
    "SPM": "geo:region:northern_america",  # Saint Pierre and Miquelon
    "SXM": "geo:region:caribbean",         # Sint Maarten
    "SYC": "geo:region:eastern_africa",    # Seychelles
    "VGB": "geo:region:caribbean",         # British Virgin Islands
    "WBG": "geo:region:western_asia",      # West Bank (plotly code)
}


# ── Primary official language(s) (ISO3 → [lang alias, ...]) ──────────────────

LANGUAGES = {
    "AFG": ["lang:fa", "lang:ur"],
    "AGO": ["lang:pt"],
    "ALB": ["lang:sq"],
    "DZA": ["lang:ar"],
    "AND": ["lang:ca"],
    "AGO": ["lang:pt"],
    "ARG": ["lang:es"],
    "ARM": ["lang:hy"],
    "AUS": ["lang:en"],
    "AUT": ["lang:de"],
    "AZE": ["lang:az"],
    "BHS": ["lang:en"],
    "BHR": ["lang:ar"],
    "BGD": ["lang:bn"],
    "BLR": ["lang:ru", "lang:be"],
    "BEL": ["lang:nl", "lang:fr", "lang:de"],
    "BLZ": ["lang:en"],
    "BEN": ["lang:fr"],
    "BTN": ["lang:dz"],
    "BOL": ["lang:es"],
    "BIH": ["lang:bs"],
    "BWA": ["lang:en"],
    "BRA": ["lang:pt"],
    "BRN": ["lang:ms"],
    "BGR": ["lang:bg"],
    "BFA": ["lang:fr"],
    "BDI": ["lang:fr"],
    "KHM": ["lang:km"],
    "CMR": ["lang:fr", "lang:en"],
    "CAN": ["lang:en", "lang:fr"],
    "CPV": ["lang:pt"],
    "CAF": ["lang:fr"],
    "TCD": ["lang:fr", "lang:ar"],
    "CHL": ["lang:es"],
    "CHN": ["lang:zh"],
    "COL": ["lang:es"],
    "COM": ["lang:ar", "lang:fr"],
    "COD": ["lang:fr"],
    "COG": ["lang:fr"],
    "CRI": ["lang:es"],
    "HRV": ["lang:hr"],
    "CUB": ["lang:es"],
    "CYP": ["lang:el", "lang:tr"],
    "CZE": ["lang:cs"],
    "DNK": ["lang:da"],
    "DJI": ["lang:fr", "lang:ar"],
    "DMA": ["lang:en"],
    "DOM": ["lang:es"],
    "ECU": ["lang:es"],
    "EGY": ["lang:ar"],
    "SLV": ["lang:es"],
    "GNQ": ["lang:es", "lang:fr", "lang:pt"],
    "ERI": ["lang:ar"],
    "EST": ["lang:et"],
    "ETH": ["lang:am"],
    "FJI": ["lang:en"],
    "FIN": ["lang:fi"],
    "FRA": ["lang:fr"],
    "GAB": ["lang:fr"],
    "GMB": ["lang:en"],
    "GEO": ["lang:ka"],
    "DEU": ["lang:de"],
    "GHA": ["lang:en"],
    "GRC": ["lang:el"],
    "GRD": ["lang:en"],
    "GTM": ["lang:es"],
    "GIN": ["lang:fr"],
    "GNB": ["lang:pt"],
    "GUY": ["lang:en"],
    "HTI": ["lang:fr"],
    "HND": ["lang:es"],
    "HUN": ["lang:hu"],
    "ISL": ["lang:is"],
    "IND": ["lang:hi", "lang:en"],
    "IDN": ["lang:id"],
    "IRN": ["lang:fa"],
    "IRQ": ["lang:ar"],
    "IRL": ["lang:en", "lang:ga"],
    "ISR": ["lang:he"],
    "ITA": ["lang:it"],
    "JAM": ["lang:en"],
    "JPN": ["lang:ja"],
    "JOR": ["lang:ar"],
    "KAZ": ["lang:kk", "lang:ru"],
    "KEN": ["lang:sw", "lang:en"],
    "KIR": ["lang:en"],
    "PRK": ["lang:ko"],
    "KOR": ["lang:ko"],
    "KWT": ["lang:ar"],
    "KGZ": ["lang:ky", "lang:ru"],
    "LAO": ["lang:lo"],
    "LVA": ["lang:lv"],
    "LBN": ["lang:ar"],
    "LSO": ["lang:st", "lang:en"],
    "LBR": ["lang:en"],
    "LBY": ["lang:ar"],
    "LIE": ["lang:de"],
    "LTU": ["lang:lt"],
    "LUX": ["lang:fr", "lang:de"],
    "MDG": ["lang:fr"],
    "MWI": ["lang:en"],
    "MYS": ["lang:ms"],
    "MDV": ["lang:dv"],
    "MLI": ["lang:fr"],
    "MLT": ["lang:mt", "lang:en"],
    "MHL": ["lang:en"],
    "MRT": ["lang:ar"],
    "MUS": ["lang:en", "lang:fr"],
    "MEX": ["lang:es"],
    "FSM": ["lang:en"],
    "MDA": ["lang:ro"],
    "MCO": ["lang:fr"],
    "MNG": ["lang:mn"],
    "MNE": ["lang:sr"],
    "MAR": ["lang:ar"],
    "MOZ": ["lang:pt"],
    "MMR": ["lang:my"],
    "NAM": ["lang:en"],
    "NRU": ["lang:en"],
    "NPL": ["lang:ne"],
    "NLD": ["lang:nl"],
    "NZL": ["lang:en"],
    "NIC": ["lang:es"],
    "NER": ["lang:fr"],
    "NGA": ["lang:en"],
    "NOR": ["lang:no"],
    "OMN": ["lang:ar"],
    "PAK": ["lang:ur", "lang:en"],
    "PLW": ["lang:en"],
    "PSE": ["lang:ar"],
    "PAN": ["lang:es"],
    "PNG": ["lang:en"],
    "PRY": ["lang:es"],
    "PER": ["lang:es"],
    "PHL": ["lang:tl", "lang:en"],
    "POL": ["lang:pl"],
    "PRT": ["lang:pt"],
    "PRI": ["lang:es", "lang:en"],
    "QAT": ["lang:ar"],
    "ROU": ["lang:ro"],
    "RUS": ["lang:ru"],
    "RWA": ["lang:rw", "lang:fr", "lang:en"],
    "KNA": ["lang:en"],
    "LCA": ["lang:en"],
    "VCT": ["lang:en"],
    "WSM": ["lang:sm", "lang:en"],
    "SMR": ["lang:it"],
    "STP": ["lang:pt"],
    "SAU": ["lang:ar"],
    "SEN": ["lang:fr"],
    "SRB": ["lang:sr"],
    "SLE": ["lang:en"],
    "SGP": ["lang:en", "lang:ms", "lang:zh"],
    "SVK": ["lang:sk"],
    "SVN": ["lang:sl"],
    "SLB": ["lang:en"],
    "SOM": ["lang:so", "lang:ar"],
    "ZAF": ["lang:en", "lang:af", "lang:zu"],
    "SSD": ["lang:en"],
    "ESP": ["lang:es"],
    "LKA": ["lang:si", "lang:ta"],
    "SDN": ["lang:ar"],
    "SUR": ["lang:nl"],
    "SWZ": ["lang:en"],
    "SWE": ["lang:sv"],
    "CHE": ["lang:de", "lang:fr", "lang:it"],
    "SYR": ["lang:ar"],
    "TWN": ["lang:zh"],
    "TJK": ["lang:tg"],
    "TZA": ["lang:sw", "lang:en"],
    "THA": ["lang:th"],
    "TLS": ["lang:pt"],
    "TGO": ["lang:fr"],
    "TON": ["lang:en"],
    "TTO": ["lang:en"],
    "TUN": ["lang:ar"],
    "TUR": ["lang:tr"],
    "TKM": ["lang:tk"],
    "TUV": ["lang:en"],
    "UGA": ["lang:en", "lang:sw"],
    "UKR": ["lang:uk"],
    "ARE": ["lang:ar"],
    "GBR": ["lang:en"],
    "USA": ["lang:en"],
    "URY": ["lang:es"],
    "UZB": ["lang:uz"],
    "VUT": ["lang:bi", "lang:en", "lang:fr"],
    "VAT": ["lang:it", "lang:la"],
    "VEN": ["lang:es"],
    "VNM": ["lang:vi"],
    "YEM": ["lang:ar"],
    "ZMB": ["lang:en"],
    "ZWE": ["lang:en"],
    "XKX": ["lang:sq", "lang:sr"],
    "ESH": ["lang:ar"],
    # Territories / plotly non-standard codes
    "ABW": ["lang:nl"],   "AIA": ["lang:en"],   "ASM": ["lang:sm", "lang:en"],
    "BHM": ["lang:en"],   "BMU": ["lang:en"],   "BRB": ["lang:en"],
    "COK": ["lang:en"],   "CUW": ["lang:nl"],   "CYM": ["lang:en"],
    "FLK": ["lang:en"],   "FRO": ["lang:fo", "lang:da"],
    "GGY": ["lang:en"],   "GIB": ["lang:en"],   "GRL": ["lang:kl", "lang:da"],
    "GUM": ["lang:en"],   "HKG": ["lang:zh", "lang:en"],
    "IMN": ["lang:en"],   "JEY": ["lang:en"],
    "KSV": ["lang:sq", "lang:sr"],
    "MAC": ["lang:zh", "lang:pt"],
    "MAF": ["lang:fr"],   "MNP": ["lang:en"],   "NCL": ["lang:fr"],
    "NIU": ["lang:en"],   "PYF": ["lang:fr"],   "SPM": ["lang:fr"],
    "SXM": ["lang:nl", "lang:en"],
    "SYC": ["lang:fr", "lang:en"],
    "VGB": ["lang:en"],   "WBG": ["lang:ar"],
}


# ── Wikipedia title overrides (ISO3 → title string, URL-encoded manually) ────
# Default: use the atom's name field directly.

WIKI_OVERRIDE = {
    "PRK": "North_Korea",
    "KOR": "South_Korea",
    "TWN": "Taiwan",
    "IRN": "Iran",
    "SYR": "Syria",
    "BOL": "Bolivia",
    "VEN": "Venezuela",
    "TZA": "Tanzania",
    "MKD": "North_Macedonia",
    "COD": "Democratic_Republic_of_the_Congo",
    "COG": "Republic_of_the_Congo",
    "CAF": "Central_African_Republic",
    "GNB": "Guinea-Bissau",
    "CIV": "Ivory_Coast",
    "STP": "S%C3%A3o_Tom%C3%A9_and_Pr%C3%ADncipe",
    "BIH": "Bosnia_and_Herzegovina",
    "MNE": "Montenegro",
    "SRB": "Serbia",
    "XKX": "Kosovo",
    "VAT": "Vatican_City",
    "SMR": "San_Marino",
    "LIE": "Liechtenstein",
    "MCO": "Monaco",
    "AND": "Andorra",
    "USA": "United_States",
    "GBR": "United_Kingdom",
    "CHN": "China",
    "RUS": "Russia",
    "KNA": "Saint_Kitts_and_Nevis",
    "LCA": "Saint_Lucia",
    "VCT": "Saint_Vincent_and_the_Grenadines",
    "ATG": "Antigua_and_Barbuda",
    "TTO": "Trinidad_and_Tobago",
    "SLB": "Solomon_Islands",
    "MHL": "Marshall_Islands",
    "FSM": "Federated_States_of_Micronesia",
    "PNG": "Papua_New_Guinea",
    "NZL": "New_Zealand",
    "ZAF": "South_Africa",
    "SSD": "South_Sudan",
    "ESH": "Western_Sahara",
    "PSE": "State_of_Palestine",
    "ARE": "United_Arab_Emirates",
    "SAU": "Saudi_Arabia",
    "TLS": "East_Timor",
    "MDV": "Maldives",
    "LKA": "Sri_Lanka",
    "MYS": "Malaysia",
    "PHL": "Philippines",
    "IDN": "Indonesia",
    "VNM": "Vietnam",
    "MMR": "Myanmar",
    "PRK": "North_Korea",
    "LAO": "Laos",
    "KHM": "Cambodia",
    "BRN": "Brunei",
    "SGP": "Singapore",
    "TKM": "Turkmenistan",
    "KGZ": "Kyrgyzstan",
    "TJK": "Tajikistan",
    "UZB": "Uzbekistan",
    "KAZ": "Kazakhstan",
    "IRQ": "Iraq",
    "ISR": "Israel",
    "JOR": "Jordan",
    "LBN": "Lebanon",
    "SYR": "Syria",
    "YEM": "Yemen",
    "OMN": "Oman",
    "BHR": "Bahrain",
    "QAT": "Qatar",
    "KWT": "Kuwait",
    "GEO": "Georgia_(country)",
    "ARM": "Armenia",
    "AZE": "Azerbaijan",
    "CPV": "Cape_Verde",
    "GNQ": "Equatorial_Guinea",
    "SWZ": "Eswatini",
    "LSO": "Lesotho",
    "BWA": "Botswana",
    "ZMB": "Zambia",
    "ZWE": "Zimbabwe",
    "MWI": "Malawi",
    "MOZ": "Mozambique",
    "MDG": "Madagascar",
    "MUS": "Mauritius",
    "COM": "Comoros",
    "ERI": "Eritrea",
    "DJI": "Djibouti",
    "SOM": "Somalia",
    "ETH": "Ethiopia",
    "UGA": "Uganda",
    "RWA": "Rwanda",
    "BDI": "Burundi",
    "TZA": "Tanzania",
    "KEN": "Kenya",
    "SDN": "Sudan",
    "SSD": "South_Sudan",
    "LBR": "Liberia",
    "SLE": "Sierra_Leone",
    "GIN": "Guinea",
    "BFA": "Burkina_Faso",
    "NER": "Niger",
    "TCD": "Chad",
    "CMR": "Cameroon",
    "NGA": "Nigeria",
    "GHA": "Ghana",
    "BEN": "Benin",
    "MLI": "Mali",
    "MRT": "Mauritania",
    "SEN": "Senegal",
    "GMB": "Gambia",
    "DMA": "Dominica",
    "GRD": "Grenada",
    "SUR": "Suriname",
    "GUY": "Guyana",
    "PRI": "Puerto_Rico",
    "HTI": "Haiti",
    "DOM": "Dominican_Republic",
    "CUB": "Cuba",
    "JAM": "Jamaica",
    "TTO": "Trinidad_and_Tobago",
    "BHS": "Bahamas",
    "BLZ": "Belize",
    "GTM": "Guatemala",
    "HND": "Honduras",
    "SLV": "El_Salvador",
    "NIC": "Nicaragua",
    "CRI": "Costa_Rica",
    "PAN": "Panama",
    "MEX": "Mexico",
    "BOL": "Bolivia",
    "PRY": "Paraguay",
    "URY": "Uruguay",
    "ECU": "Ecuador",
    "COL": "Colombia",
    "VEN": "Venezuela",
    "PER": "Peru",
    "CHL": "Chile",
    "ARG": "Argentina",
    "BRA": "Brazil",
    # Territories / plotly non-standard codes
    "ABW": "Aruba",
    "AIA": "Anguilla",
    "ASM": "American_Samoa",
    "BHM": "The_Bahamas",
    "BMU": "Bermuda",
    "BRB": "Barbados",
    "COK": "Cook_Islands",
    "CUW": "Cura%C3%A7ao",
    "CYM": "Cayman_Islands",
    "FLK": "Falkland_Islands",
    "FRO": "Faroe_Islands",
    "GGY": "Guernsey",
    "GIB": "Gibraltar",
    "GRL": "Greenland",
    "GUM": "Guam",
    "HKG": "Hong_Kong",
    "IMN": "Isle_of_Man",
    "JEY": "Jersey",
    "KSV": "Kosovo",
    "MAC": "Macau",
    "MAF": "Collectivity_of_Saint_Martin",
    "MNP": "Northern_Mariana_Islands",
    "NCL": "New_Caledonia",
    "NIU": "Niue",
    "PYF": "French_Polynesia",
    "SPM": "Saint_Pierre_and_Miquelon",
    "SXM": "Sint_Maarten",
    "SYC": "Seychelles",
    "VGB": "British_Virgin_Islands",
    "WBG": "West_Bank",
}

# Non-UN members / observer states / territories
NON_UN_MEMBERS = {
    "TWN", "XKX", "KSV", "VAT", "PSE", "ESH", "ATA",
    "ABW", "AIA", "ASM", "BMU", "COK", "CUW", "CYM", "FLK",
    "FRO", "GGY", "GIB", "GRL", "GUM", "HKG", "IMN", "JEY",
    "MAC", "MAF", "MNP", "NCL", "NIU", "PYF", "SPM", "SXM",
    "VGB", "WBG",
}


VOCAB = {
    # Continents
    "geo:continent:africa":        "Africa — second-largest continent by area and population; 54 recognised sovereign states.",
    "geo:continent:asia":          "Asia — largest continent by area and population; home to more than 60% of the world's people.",
    "geo:continent:europe":        "Europe — western peninsula of Eurasia; bounded by the Atlantic, Arctic, and Mediterranean.",
    "geo:continent:north_america": "North America — continent comprising Canada, the United States, Mexico, Central America, and the Caribbean.",
    "geo:continent:south_america": "South America — continent comprising twelve sovereign countries south of the Panama isthmus.",
    "geo:continent:oceania":       "Oceania — Australia, New Zealand, and the Pacific island nations of Melanesia, Micronesia, and Polynesia.",
    "geo:continent:antarctica":    "Antarctica — southernmost continent; governed by the Antarctic Treaty System; no permanent population.",
    # Subregions
    "geo:region:northern_africa":       "Northern Africa — Algeria, Egypt, Libya, Morocco, Sudan, Tunisia, Western Sahara.",
    "geo:region:western_africa":        "Western Africa — Benin, Burkina Faso, Cape Verde, Côte d'Ivoire, Gambia, Ghana, Guinea, Guinea-Bissau, Liberia, Mali, Mauritania, Niger, Nigeria, Senegal, Sierra Leone, Togo.",
    "geo:region:eastern_africa":        "Eastern Africa — Burundi, Comoros, Djibouti, Eritrea, Ethiopia, Kenya, Madagascar, Malawi, Mauritius, Mozambique, Rwanda, Somalia, South Sudan, Tanzania, Uganda, Zambia, Zimbabwe.",
    "geo:region:middle_africa":         "Middle Africa — Angola, Cameroon, Central African Republic, Chad, Congo, DRC, Equatorial Guinea, Gabon.",
    "geo:region:southern_africa":       "Southern Africa — Botswana, Eswatini, Lesotho, Namibia, South Africa.",
    "geo:region:central_asia":          "Central Asia — Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan.",
    "geo:region:eastern_asia":          "Eastern Asia — China, Japan, North Korea, South Korea, Mongolia, Taiwan.",
    "geo:region:southeastern_asia":     "South-eastern Asia — Brunei, Cambodia, Indonesia, Laos, Malaysia, Myanmar, Philippines, Singapore, Thailand, Timor-Leste, Vietnam.",
    "geo:region:southern_asia":         "Southern Asia — Afghanistan, Bangladesh, Bhutan, India, Iran, Maldives, Nepal, Pakistan, Sri Lanka.",
    "geo:region:western_asia":          "Western Asia — Armenia, Azerbaijan, Bahrain, Cyprus, Georgia, Iraq, Israel, Jordan, Kuwait, Lebanon, Oman, Palestine, Qatar, Saudi Arabia, Syria, Turkey, UAE, Yemen.",
    "geo:region:eastern_europe":        "Eastern Europe — Belarus, Bulgaria, Czech Republic, Hungary, Moldova, Poland, Romania, Russia, Slovakia, Ukraine.",
    "geo:region:northern_europe":       "Northern Europe — Denmark, Estonia, Finland, Iceland, Ireland, Latvia, Lithuania, Norway, Sweden, United Kingdom.",
    "geo:region:southern_europe":       "Southern Europe — Albania, Andorra, Bosnia and Herzegovina, Croatia, Greece, Italy, Kosovo, Malta, Monaco, Montenegro, North Macedonia, Portugal, San Marino, Serbia, Slovenia, Spain, Vatican.",
    "geo:region:western_europe":        "Western Europe — Austria, Belgium, France, Germany, Liechtenstein, Luxembourg, Netherlands, Switzerland.",
    "geo:region:caribbean":             "Caribbean — Antigua and Barbuda, Bahamas, Barbados, Cuba, Dominica, Dominican Republic, Grenada, Haiti, Jamaica, Saint Kitts and Nevis, Saint Lucia, Saint Vincent, Trinidad and Tobago.",
    "geo:region:central_america":       "Central America — Belize, Costa Rica, El Salvador, Guatemala, Honduras, Mexico, Nicaragua, Panama.",
    "geo:region:northern_america":      "Northern America — Canada, United States.",
    "geo:region:south_america":         "South America — Argentina, Bolivia, Brazil, Chile, Colombia, Ecuador, Guyana, Paraguay, Peru, Suriname, Uruguay, Venezuela.",
    "geo:region:australia_new_zealand": "Australia and New Zealand.",
    "geo:region:melanesia":             "Melanesia — Fiji, Papua New Guinea, Solomon Islands, Vanuatu.",
    "geo:region:micronesia":            "Micronesia — Kiribati, Marshall Islands, Micronesia, Nauru, Palau.",
    "geo:region:polynesia":             "Polynesia — Samoa, Tonga, Tuvalu.",
    # GDP tiers
    "geo:gdp_tier:high":         "High GDP — national GDP above $500 billion (2014 USD).",
    "geo:gdp_tier:upper_middle": "Upper-middle GDP — national GDP $50–500 billion (2014 USD).",
    "geo:gdp_tier:lower_middle": "Lower-middle GDP — national GDP $5–50 billion (2014 USD).",
    "geo:gdp_tier:low":          "Low GDP — national GDP below $5 billion (2014 USD).",
    # Languages
    "lang:af": "Afrikaans", "lang:am": "Amharic", "lang:ar": "Arabic",
    "lang:az": "Azerbaijani", "lang:be": "Belarusian", "lang:bg": "Bulgarian",
    "lang:bi": "Bislama", "lang:bn": "Bengali", "lang:bs": "Bosnian",
    "lang:ca": "Catalan", "lang:cs": "Czech", "lang:da": "Danish",
    "lang:de": "German", "lang:dv": "Dhivehi", "lang:dz": "Dzongkha",
    "lang:el": "Greek", "lang:en": "English", "lang:es": "Spanish",
    "lang:et": "Estonian", "lang:fa": "Persian", "lang:fi": "Finnish",
    "lang:fr": "French", "lang:ga": "Irish", "lang:he": "Hebrew",
    "lang:hi": "Hindi", "lang:hr": "Croatian", "lang:hu": "Hungarian",
    "lang:hy": "Armenian", "lang:id": "Indonesian", "lang:is": "Icelandic",
    "lang:it": "Italian", "lang:ja": "Japanese", "lang:ka": "Georgian",
    "lang:kk": "Kazakh", "lang:km": "Khmer", "lang:ko": "Korean",
    "lang:ky": "Kyrgyz", "lang:la": "Latin", "lang:lo": "Lao",
    "lang:lt": "Lithuanian", "lang:lv": "Latvian", "lang:mn": "Mongolian",
    "lang:ms": "Malay", "lang:mt": "Maltese", "lang:my": "Burmese",
    "lang:ne": "Nepali", "lang:nl": "Dutch", "lang:no": "Norwegian",
    "lang:pl": "Polish", "lang:pt": "Portuguese", "lang:ro": "Romanian",
    "lang:ru": "Russian", "lang:rw": "Kinyarwanda", "lang:si": "Sinhala",
    "lang:sk": "Slovak", "lang:sl": "Slovenian", "lang:sm": "Samoan",
    "lang:so": "Somali", "lang:sq": "Albanian", "lang:sr": "Serbian",
    "lang:st": "Sesotho", "lang:sv": "Swedish", "lang:sw": "Swahili",
    "lang:ta": "Tamil", "lang:tg": "Tajik", "lang:th": "Thai",
    "lang:tk": "Turkmen", "lang:tl": "Filipino", "lang:tr": "Turkish",
    "lang:uk": "Ukrainian", "lang:ur": "Urdu", "lang:uz": "Uzbek",
    "lang:vi": "Vietnamese", "lang:yo": "Yoruba", "lang:zh": "Chinese",
    "lang:zu": "Zulu",
    # Organisation
    "org:united_nations": "United Nations — intergovernmental organisation founded 1945; 193 member states as of 2024.",
}


def _ensure_vocab(nucleus) -> None:
    """Create all vocabulary atoms in nucleus if they don't already exist."""
    for alias, description in VOCAB.items():
        if nucleus.resolve_alias(alias):
            continue
        meta = {"type": "geo_vocab"}
        nucleus.put_atom(description, meta, AUTHOR, alias=alias)
    print("  Vocabulary atoms ensured.")


def _wiki_url(iso3: str, name: str) -> str:
    title = WIKI_OVERRIDE.get(iso3)
    if not title:
        title = name.replace(" ", "_")
    return WIKI_BASE + title


def _gdp_tier(gdp_billions) -> str | None:
    if gdp_billions is None:
        return None
    if gdp_billions >= 500:
        return "geo:gdp_tier:high"
    if gdp_billions >= 50:
        return "geo:gdp_tier:upper_middle"
    if gdp_billions >= 5:
        return "geo:gdp_tier:lower_middle"
    return "geo:gdp_tier:low"


def _existing_rels(nucleus, key: str) -> set:
    """Return set of relation types already going out from key."""
    import sqlite3
    con = sqlite3.connect(NUCLEUS_DB)
    rows = con.execute(
        "SELECT rel FROM links WHERE src=?", (key,)
    ).fetchall()
    con.close()
    return {r[0] for r in rows}


def _has_link(nucleus, src: str, dst: str, rel: str) -> bool:
    """Check if a specific src→dst link with given rel exists."""
    import sqlite3
    con = sqlite3.connect(NUCLEUS_DB)
    row = con.execute(
        "SELECT 1 FROM links WHERE src=? AND dst=? AND rel=?", (src, dst, rel)
    ).fetchone()
    con.close()
    return row is not None


def main():
    print("Akasha — Geo Country Enrichment")
    print(f"Nucleus: {NUCLEUS_DB}\n")

    if not os.path.exists(NUCLEUS_DB):
        print(f"[!] Nucleus DB not found: {NUCLEUS_DB}")
        sys.exit(1)

    nucleus = NucleusEngine(NUCLEUS_DB)

    print("Ensuring vocabulary atoms (continents, regions, GDP tiers, languages, org)…")
    _ensure_vocab(nucleus)

    # Load all country atom keys from the set
    import sqlite3
    con = sqlite3.connect(NUCLEUS_DB)
    country_keys = [r[0] for r in con.execute(
        "SELECT key FROM collections WHERE name='set:geo:countries'"
    ).fetchall()]
    con.close()

    print(f"Found {len(country_keys)} country atoms\n")

    stats = {
        "continent": 0, "region": 0, "gdp_tier": 0,
        "language": 0, "wikipedia": 0, "un": 0, "skipped": 0,
    }

    un_key = nucleus.resolve_alias("org:united_nations")

    for key in country_keys:
        raw = nucleus.core.get_chunk_raw(key)
        if not raw:
            continue

        try:
            meta_str = raw.get("meta") or "{}"
            meta = json.loads(meta_str) if isinstance(meta_str, str) else (meta_str or {})
        except (json.JSONDecodeError, AttributeError):
            meta = {}

        iso3 = meta.get("iso3", "")
        name = meta.get("name", "")
        gdp  = meta.get("gdp_billions")

        if not iso3:
            stats["skipped"] += 1
            continue

        # ── Continent ──
        cont_alias = CONTINENT.get(iso3)
        if cont_alias:
            cont_key = nucleus.resolve_alias(cont_alias)
            if cont_key and not _has_link(nucleus, key, cont_key, "thesaurus:hypernym"):
                nucleus.put_link(key, cont_key, "thesaurus:hypernym")
                stats["continent"] += 1

        # ── Subregion ──
        reg_alias = REGION.get(iso3)
        if reg_alias:
            reg_key = nucleus.resolve_alias(reg_alias)
            if reg_key and not _has_link(nucleus, key, reg_key, "thesaurus:hypernym"):
                nucleus.put_link(key, reg_key, "thesaurus:hypernym")
                stats["region"] += 1

        # ── GDP tier ──
        tier_alias = _gdp_tier(gdp)
        if tier_alias:
            tier_key = nucleus.resolve_alias(tier_alias)
            if tier_key and not _has_link(nucleus, key, tier_key, "thesaurus:hypernym"):
                nucleus.put_link(key, tier_key, "thesaurus:hypernym")
                stats["gdp_tier"] += 1

        # ── Official languages ──
        for lang_alias in LANGUAGES.get(iso3, []):
            lang_key = nucleus.resolve_alias(lang_alias)
            if lang_key and not _has_link(nucleus, key, lang_key, "geo:official_language"):
                nucleus.put_link(key, lang_key, "geo:official_language")
                stats["language"] += 1

        # ── Wikipedia external ref ──
        if name:
            wiki_url = _wiki_url(iso3, name)
            # Store as a link to an external ref atom
            wiki_alias = f"ext:wikipedia:{iso3.lower()}"
            wiki_key = nucleus.resolve_alias(wiki_alias)
            if not wiki_key:
                ref_meta = {
                    "type": "thesaurus:ExternalRef",
                    "label": "Wikipedia",
                    "url": wiki_url,
                    "iso3": iso3,
                }
                wiki_key = nucleus.put_atom(
                    wiki_url, ref_meta, AUTHOR, alias=wiki_alias
                )
                stats["wikipedia"] += 1
            if wiki_key and not _has_link(nucleus, key, wiki_key, "thesaurus:external_ref"):
                nucleus.put_link(key, wiki_key, "thesaurus:external_ref")

        # ── UN membership ──
        if iso3 not in NON_UN_MEMBERS:
            if un_key and not _has_link(nucleus, key, un_key, "sys:part_of"):
                nucleus.put_link(key, un_key, "sys:part_of")
                stats["un"] += 1

    print("Enrichment complete:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("\nDone.")


if __name__ == "__main__":
    main()
