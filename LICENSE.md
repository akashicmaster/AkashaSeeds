# Licenses and Attributions

---

## Software License

```
MIT License

Copyright (c) 2026 Hirosuke Nishi Grohmann

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

---

## Bundled Ontology Data — Third-Party Attribution

Akasha includes a built-in ontology distributed as a set of **packs** (`.ak` files under `ontology/`). The ontology packs are not part of the software kernel. They are structured semantic data derived from various open data sources.

Only the **base** pack loads automatically at startup. All other packs are optional and are activated separately.

### Default Pack (loads at startup)

**Pack: `base`** — Core vocabulary and fundamental concepts

The `base` pack includes word definition data derived from **Princeton University WordNet 3.1**:

> Files: `ontology/base/word_core_01.ak` – `word_core_04.ak`
>
> WordNet Release 3.1  
> Copyright 2006 by Princeton University  
> License: https://wordnet.princeton.edu/license-and-commercial-use
>
> "WordNet" is a trademark of Princeton University. This software and database is provided "as is" and Princeton University makes no representations about the suitability of this software and database for any purpose.

The `base` pack also includes English frequency lemma data derived from the **Coxhead Academic Word List (AWL, 2000)**:

> File: `ontology/base/word_freq_core.ak`
>
> Academic Word List — Averil Coxhead, Victoria University of Wellington, 2000.  
> Used as a word-form reference for lemmatisation anchoring. The content stored in Akasha consists only of bare word tokens (not definitions or AWL text).

All remaining content in the `base` pack (geographic coordinates, historical periods, emotional vocabulary, logical relations, etc.) is original editorial content authored by the Akasha Protocol Project and is covered by the MIT license above.

---

### Optional Packs

The following packs are distributed with Akasha but **do not load automatically**. Each carries its own data origin and applicable terms.

| Pack | Contents | Data Origin | Terms |
| :--- | :--- | :--- | :--- |
| `vocab` | Extended English vocabulary (8,001–80,000+ words) | Princeton University WordNet 3.1 | [WordNet License](https://wordnet.princeton.edu/license-and-commercial-use) |
| `world` | Geography, world history, mythology, writing systems | Original editorial | MIT |
| `archaeology` | Ancient sites and archaeological cultures | [Pleiades Project](https://pleiades.stoa.org/) | CC BY 3.0 |
| `art` | Painting movements, architecture styles, techniques | [Metropolitan Museum Open Access](https://collectionapi.metmuseum.org/) · [Wikidata](https://www.wikidata.org/) | CC0 (Met) · CC BY-SA 4.0 (Wikidata) |
| `biology` | Taxonomic classification | [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy) | Public Domain |
| `film` | Film movements, cinematographic concepts, stage forms | [IMDb datasets](https://datasets.imdbws.com/) · [Wikidata](https://www.wikidata.org/) | **Non-commercial only** (IMDb) · CC BY-SA 4.0 (Wikidata) |
| `geology` | Geological periods, minerals, volcanoes, tectonic plates | [ICS](https://stratigraphy.org/) · [RRUFF](https://rruff.info/) · [Smithsonian GVP](https://volcano.si.edu/) · [IMA](https://www.mineralogicalassociation.ca/) | Public Domain (ICS, RRUFF, USGS) · CC BY 4.0 (IMA mineral data) |
| `law` | Legal concepts, historical codes, legal traditions | [Yale Avalon Project](https://avalon.law.yale.edu/) · [Wikidata](https://www.wikidata.org/) | Public Domain · CC BY-SA 4.0 (Wikidata) |
| `literature` | Authors, works, literary movements | [Project Gutenberg](https://www.gutenberg.org/) · [DBpedia](https://www.dbpedia.org/) | Public Domain (PG) · CC BY-SA 4.0 (DBpedia abstracts) |
| `medicine` | Medical terminology (MeSH headings) | [NLM Medical Subject Headings](https://www.nlm.nih.gov/mesh/) | Public Domain |
| `music` | Instruments, music forms, world music traditions, performing arts | [UNESCO ICH](https://ich.unesco.org/) · [IMSLP](https://imslp.org/) · [Wikidata](https://www.wikidata.org/) | Public Domain terminology · CC BY-SA 4.0 (Wikidata) |
| `nutrition` | Food composition data | [USDA FoodData Central](https://fdc.nal.usda.gov/) | Public Domain |
| `people` | Historical figures and notable persons | [Pantheon 2.0](https://pantheon.world/data/datasets) · [Wikidata](https://www.wikidata.org/) | CC0 (Pantheon) · CC BY-SA 4.0 (Wikidata) |
| `resources` | Natural resources, energy, minerals | [USGS NMIC](https://www.usgs.gov/programs/national-minerals-information-center) · [IEA](https://www.iea.org/) | Public Domain |
| `space` | Solar system, exoplanets, constellations, satellites | [NASA/JPL](https://ssd.jpl.nasa.gov/) · [IAU](https://www.iau.org/) · [Celestrak](https://celestrak.org/) · [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) | Public Domain |
| `tech` | Computing, software engineering, AI/ML, cybersecurity | Original editorial | MIT |
| `war` | Historical wars, conflict zones, military concepts | [UCDP](https://ucdp.uu.se/) · [ACLED](https://acleddata.com/) · [Wikidata](https://www.wikidata.org/) | Public Domain terminology · CC BY (UCDP) · CC BY-SA 4.0 (Wikidata) |
| `weather` | Meteorological vocabulary, climate classification | [WMO](https://public.wmo.int/) · [NOAA](https://www.noaa.gov/) | Public Domain |
| `wine` | Wine varietals, regions, gastronomy | [Wikidata](https://www.wikidata.org/) · Original editorial | CC BY-SA 4.0 (Wikidata) · MIT |
| `domain` | Domain-specific ontology extensions | Original editorial | MIT |

---

### Important Notices

#### WordNet — Required Attribution (base and vocab packs)

Any redistribution of Akasha that includes the `base` or `vocab` ontology pack must include the WordNet copyright notice and the license text, available at:

https://wordnet.princeton.edu/license-and-commercial-use

The copyright notice is reproduced above and within the header of each `word_core_*.ak` and `word_ext_*.ak` file.

#### IMDb — Non-Commercial Restriction (film pack)

The `film` pack incorporates data from [IMDb datasets](https://datasets.imdbws.com/). This data is provided by IMDb for personal, non-commercial use only.

> "Information courtesy of IMDb (https://www.imdb.com). Used with permission."

**The `film` pack may not be used for commercial purposes.** Any deployment of Akasha that loads the `film` pack must comply with IMDb's dataset terms of use.

#### Wikidata — CC BY-SA 4.0 (multiple packs)

Several packs incorporate structured data derived from [Wikidata](https://www.wikidata.org/), which is published under the Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).

CC BY-SA 4.0 requires attribution and that derivative works be distributed under the same license. This applies to the Wikidata-derived **content** within those packs, not to the Akasha software itself.

When distributing a modified version of a Wikidata-derived pack, provide attribution to Wikidata (https://www.wikidata.org/) and link to the CC BY-SA 4.0 license:

https://creativecommons.org/licenses/by/4.0/

#### Pleiades Project — CC BY 3.0 (archaeology pack)

Data from the [Pleiades Project](https://pleiades.stoa.org/) is used under the Creative Commons Attribution 3.0 Unported License (CC BY 3.0).

Attribution: *Pleiades: A Gazetteer of Past Places* (https://pleiades.stoa.org/)

#### IMA Mineral Data — CC BY 4.0 (geology pack)

Mineral data from the International Mineralogical Association (IMA) is used under CC BY 4.0.

Attribution: *IMA List of Minerals*, International Mineralogical Association (https://www.mineralogicalassociation.ca/)

#### UCDP — CC BY (war pack)

Conflict data from the Uppsala Conflict Data Program (UCDP) is used under a Creative Commons Attribution license.

Attribution: *UCDP Conflict Encyclopedia*, Uppsala University (https://ucdp.uu.se/)

---

### Ontology Files Carrying Inline Attributions

The following files contain explicit source attribution in their file headers. The headers should be preserved in any redistribution:

| File(s) | Source noted |
| :--- | :--- |
| `base/word_core_01.ak` – `word_core_04.ak` | Princeton University WordNet 3.1 |
| `vocab/word_ext_01.ak` – `word_ext_10.ak` | Princeton University WordNet 3.1 |
| `base/word_freq_core.ak` | Coxhead AWL (2000) · OpenSubtitles/Google frequency lists |
| `world/iau_constellations.ak` | IAU (1922/1930) — declared Public Domain |
| `base/si_units.ak` | BIPM · CODATA 2018/NIST — declared Public Domain |
| `world/geo_countries_core.ak` | plotly/datasets (world GDP 2014) · Wikipedia URLs (links only, not text) |
| `space/solar_system.ak` | IAU · JPL · NASA — declared Public Domain |
| `geology/tectonic_plates.ak` | USGS geological surveys — declared Public Domain |
| `music/instruments_hs.ak` | Hornbostel-Sachs 1914 / ICTM 2011 rev. · UNESCO ICH · Grove Music |

---

*The plain-text LICENSE file at the root of this repository contains the software MIT License only. This document (LICENSE.md) is the authoritative reference for all data attribution.*
