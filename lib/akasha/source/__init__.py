"""
`source` — Source management: pools, packs, bootstraps, fetch (Part II §A21).

    bootstrap.py    the seed-time corpus bootstraps (the source packs and every declared corpus)
                    and the pool readiness probe
    fetch.py        the web fetch into the graph (contexa.fetch / gap.fetch use it)
    MANIFEST.json   what this package contributes: its post-load bodies

The source engine RECORDS and ANNOUNCES; it drives no Concept Model (group 4, 4.11). The feed poller,
the analysis ops and the media / analysis precompute passes drove application models by name, so
they moved to the application (`concepts/feed_poll.py`, `concepts/analysis_ops.py`,
`concepts/precompute.py`), unchanged in behaviour, their manifest entries with them.

It imports the heart only through `lib.akasha.api` and may import `ontology`; nothing rightward
(concepts / workbench) — those import it.
"""
