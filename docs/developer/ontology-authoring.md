# Authoring an ontology pack

**Audience: the development user.** How to add meaning to Akasha — a pack of `.ak` files, its
manifest, its place in the registry, and the lexicon entries without which a term reaches a user as
a bare undefined string.

The specification of what an ontology *is* — the three layers, the epistemology — is
[`../ontology/ontology-spec.md`](../ontology/ontology-spec.md). This page is the procedure.

---

## 1. The whole vocabulary of a release `.ak` file

Four commands. There are no others in a release pack.

```text
def "atom:id" "The description. The head, before the em dash, is the atom's full spelling."
ln  src dst rel                       # a typed link
al  atom:id alias                     # register an alias
set.add name="collection" id="atom:id"
# a comment — ignored by the loader
```

Variables, `link.create`, `define:` blocks and `scope=` are **not** used in `.ak`. If you want
expressiveness, write CSL and transpile it (`onto.csl.transpile`) before placing the result; CSL is
not placed in `ontology/`.

**Duplicate-safe by design.** Atoms are content-addressed, so reloading a file that overlaps with
existing content is idempotent — duplicates are unified, never rejected. You do not need to check
whether a term is already defined before defining it.

**Write ids without whitespace.** An id containing a space is re-split by the loader, and the tail
becomes a relation nobody defined. That has happened: `shelf:dibdin:page:[t.p. verso]` minted a
`reldef:verso]`. Slug the id at the point it is generated.

## 2. The directory and its manifest

One directory per pack, under `app/ontology/<name>/`, with a `PACK.json`:

```json
{
  "label": "NCBI Taxonomy (Biology)",
  "description": "What is in it, and what the atom ids look like: bio:{rank}:{scientific_name}.",
  "license": "Public domain (National Center for Biotechnology Information)",
  "source": "https://www.ncbi.nlm.nih.gov/taxonomy",
  "attribution": "NCBI Taxonomy, National Center for Biotechnology Information"
}
```

`license`, `source` and `attribution` are not paperwork. A pack whose provenance is not recorded
cannot be shipped, cannot be cited, and cannot be defended if someone asks where a claim came from.

One `.ak` file per topic inside the directory (`ontology/base/color.ak`,
`ontology/base/country.ak`). To produce one from a running cell:

```bash
python akasha.py onto.export ns=<ns> split=single
```

Review the output, then place it and register it.

## 3. The tier — which seeds carry it, and whether it autoloads

Every pack is listed in `ontology/REGISTRY.json` with a tier. The tier decides bundling **and**
autoload, per release series:

| tier | content | bundled in | autoloads |
|---|---|---|---|
| **A** | core — words, feelings, the table, the knowledge canopy (`base1/2/3`, `lexicon`, `curation`, `recipe`) | every series | always, every series |
| **B** | a discipline pack (`world`, `tech`, `law`, `art`, `wine`, …) | every series | seeds: **no** (opt in with `onto.pack.enable`); thesaurus / service: **yes** |
| **C** | a deep reference layer (`nutrition`, `drinks_c`, `blvh`, a corpus) | **not** in seeds; **always** in every thesaurus / service tier | thesaurus / service: always, in full |

The rule that matters when you add a C pack: **the thesaurus line always carries the whole tier-C
layer, bundled and autoloaded, never a hand-picked subset.** A C pack that ships un-loaded there is a
bug. This is enforced in code (`_resolve_onto(..., include_c=load_all)`), so adding a C pack needs
**zero** extra wiring — and hand-listing the C packs anywhere is how `blvh` once shipped un-loaded.

## 4. Register the vocabulary — the step that is always forgotten

**Every string that can surface is defined. Nothing is defined implicitly.** A bare namespace or a
bare relation reaching a user is a defect, not a gap.

- A **domain** relation or namespace goes in the pack's own `_lexicon.ak`.
- A **core** relation or namespace — one the platform's code uses — goes in
  `scripts/gen_lexicon.py` (`CORE_RELS` / `CORE_NS`), and the file is regenerated:

```bash
python scripts/gen_lexicon.py
python test/verify_lexicon.py --all
# RESULT: PASS — every used relation and namespace is defined, and every vocabulary id
# the code compares against exists as an atom.
```

`00_namespaces_core.ak` is **generated**. Editing it by hand works until the next regeneration
silently reverts you.

The regression that made this a standing rule: the Product·Component·Method canon introduced
`role:product` / `role:component` / `role:method` and no `nsdef:role`, so the namespace was undefined
until `role` was added to `CORE_NS`. The coverage check is the only thing that catches this, and it
takes a second.

**A value the code compares against is vocabulary.** If a Python module has a constant whose value is
an atom id, that id must exist as an atom — `verify_lexicon --all` checks the ids the code declares,
not only the ones the packs use.

## 5. If the pack is an external dataset

An externally acquired dataset enters as an **ontology pack prepared off-line**. The deploy target
does `onto` load only: no runtime corpus bootstrap, no data file in RAM on the host.

- **Raw layer** — one line, one Atom, verbatim JSON as the content, in `source:item:<corpus>:*`,
  ordered by `chronon:next` so the source's own topology survives.
- **Derived layer** — parsed ONCE at preparation: coded fields become Sets
  (`set:<corpus>:<field>:<value>`), free text becomes weavable `txt:` atoms.
- The raw JSON atom is **NLP-exempt** (tokenising JSON syntax pollutes the proto-word space); the
  extracted free text is weaved. The pack declares `{"raw": true, "tier": "C"}`.

Generator: `scripts/corpus_to_ak.py`. Full specification:
`docs/for-llm/source-data-ontology-ingestion.md`.

### A generated file is regenerated, never edited — an edit is a reload

If a pack's `.ak` files carry a `# Generated by …` header, **they are output**. Change the
generator and run it; do not open the output and fix it by hand, however small the fix looks.

This is not tidiness. The loader decides "did this pack change?" from each `.ak` file's name and
**byte size**, so a one-word edit to a header is indistinguishable from new content: the pack
re-enters load, re-materialises its keys for reconcile, and takes the global-relations pass with
it. On 2026-09-22 a path in seventeen generated headers was corrected by hand — `scripts/…` →
`app/scripts/…`, a rename that was itself correct — and the reload chain ran on every one of
them.

For the same reason a generated header names **no path**: write `# Generated by wordnet_import`,
not `# Generated by app/scripts/wordnet_import.py`. A path is where a tool lives today, which is
exactly the kind of fact that changes and then tempts somebody to edit seventeen files. The
generator's own name does not move. `PACK.json`'s `source` field follows the same rule (that file
is outside the size gate, so correcting one is safe — but a reader should not have to know which
files are safe to touch).

## 6. Check it loads

```bash
python akasha.py onto.pack.list                  # is it registered, and at what tier?
python akasha.py onto.pack.enable <name>         # a B or C pack on a seeds cell
python akasha.py onto.reload                     # re-run the load
python akasha.py onto.report                     # what loaded, and what it cost
```

Two things happen automatically on every load, and neither is a command you run:

- **the Product·Component·Method normalizer** derives the canonical `sys:made_from` /
  `sys:method_of` / `sys:made_by` shape for any domain in `canon.DOMAINS`. Packs author their own
  descriptive links and need not know the canonical shape. Do not hand-author the canonical links,
  and do not ask a user to run a migration;
- **reconciliation** retires atoms a pack no longer contributes, fenced to `provenance="ontology"`
  with a cross-pack reference count, and soft-evicting so the removal is recoverable.

## 7. The checklist

```text
[ ] `.ak` only, four commands only; no whitespace in an id
[ ] one file per topic, under app/ontology/<name>/, with a PACK.json carrying licence + source +
    attribution
[ ] registered in ontology/REGISTRY.json at the right tier (A / B / C)
[ ] every namespace and relation defined — the pack's _lexicon.ak, or CORE_NS / CORE_RELS +
    `python scripts/gen_lexicon.py`
[ ] `python test/verify_lexicon.py --all` PASS
[ ] a dataset pack is prepared off-line, raw + derived, raw NLP-exempt, tier C
[ ] `onto.reload` loads it; `onto.report` shows what it cost
[ ] no migration command asked of a user
```

---

### Further reading

- [`../ontology/ontology-spec.md`](../ontology/ontology-spec.md) — what an ontology is here: the
  three layers, and the epistemology behind them.
- [`../ontology/pack-manifest.md`](../ontology/pack-manifest.md) — the generated inventory of every
  pack, its tier and its step count.
- `docs/for-llm/rel-definition-spec.md` — `reldef:` / `nsdef:` and the display rule.
- `docs/for-llm/source-data-ontology-ingestion.md` — the law for external datasets.
- `docs/for-llm/ontology-reconciliation-spec.md` — how a pack's removals are retired.
