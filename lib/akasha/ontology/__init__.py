"""
`ontology` — the application package that turns `.ak` packs into the graph (Part II §A21).

    loader.py            the boot load: REGISTRY / PACK.json → JCL jobs, per-pack sentinels, the
                         global-relations phase, the weave queue, the post-load phase
    ops.py               the `onto.*` RPC ops (dump, export, reload, reconcile, reset, pack.*,
                         report, status, genesis.redo, scope.drop)
    MANIFEST.json        what this package contributes: its ops, its `load`-phase body

It imports the heart only through `lib.akasha.api`; the heart reaches it only through the
manifest. Depends on nothing rightward (source / concepts / workbench).
"""
