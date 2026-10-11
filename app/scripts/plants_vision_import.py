#!/usr/bin/env python3
"""
plants_vision_import.py — import the B2 photo-REFERENCE corpus into a live Cell.

One `vlab.source.add` per photo (image_ref = remote medium-size URL — the binary is NEVER stored),
with the PLANTS species symbol as the supervised label and the verbatim iNat license/attribution as
provenance. Registers the iNaturalist source + the pool FIRST (so the pool carries its source from
the start), freezes the pool at the end. Idempotent: photos are content-addressed by alias.

  python app/scripts/plants_vision_import.py --as admin \
      [--records plants_data/vision/records.jsonl] [--manifest plants_data/vision/manifest.json] \
      [--base <data dir>]
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

SOURCE_ID = "source:src:inat_plants_vision"
POOL_NAME = "plants_images"


def run(dispatch, records, manifest, log=print, version="v1", derived_from="",
        id_prefix=""):
    pool_id = f"source:pool:{POOL_NAME}:{version}"
    prov_rule = (manifest or {}).get("selection_rule", "B1/B2 declared selection")
    dispatch("source.register", {"provider": (manifest or {}).get("provider", "iNaturalist"),
                                 "collection": (manifest or {}).get("collection",
                                                                    "PLANTS vision corpus"),
                                 "name": "inat_plants_vision",
                                 "uri": "https://www.inaturalist.org/",
                                 "retrieval_uri": (manifest or {}).get("api", ""),
                                 "rights": (manifest or {}).get("rights",
                                                                "CC0/CC-BY per record")})
    log(f"  [1] source: {SOURCE_ID}")
    dispatch("source.pool.create", {"name": POOL_NAME, "version": version,
                                    "derived_from": derived_from,
                                    "source": SOURCE_ID,
                                    "dataset_version": (manifest or {}).get("snapshot_date", ""),
                                    "retrieval": (manifest or {}).get("api", ""),
                                    "rule": prov_rule})
    log(f"  [2] pool: {pool_id}")
    added = failed = collapsed = 0
    seen_keys = set()
    for rec in records:
        oid = id_prefix + str(rec.get("id") or "")
        img = rec.get("image_url") or ""
        if not oid or not img:
            failed += 1
            continue
        try:
            res = dispatch("vlab.source.add", {
                "pool": pool_id, "object_id": oid, "image": img, "scheme": "remote",
                "title": f"{rec.get('binomial', '')} ({rec.get('species_symbol', '')}) · {oid}",
                "provider": "inat",
                # supervised label + verbatim provenance (license law: attribution kept)
                "species_symbol": rec.get("species_symbol", ""),
                "binomial": rec.get("binomial", ""), "family": rec.get("family", ""),
                "taxon_id": rec.get("taxon_id", ""),
                "license_code": rec.get("license_code", ""),
                "attribution": rec.get("attribution", ""),
                "observer": rec.get("observer", ""),
                "observed_on": rec.get("observed_on", ""),
                "observation_url": rec.get("observation_url", ""),
            })
            # COLLAPSE GUARD: _mk is idempotent-by-alias and put_atom is content-addressed, so a
            # stale alias or a duplicated minted content silently returns an EXISTING key — the
            # pool then holds fewer members than "added" claims. Two distinct records resolving to
            # one key is a defect to surface, never to hide.
            k = (res or {}).get("key")
            if k and k in seen_keys:
                collapsed += 1
                log(f"      [!] COLLAPSED: {oid} resolved to an already-seen atom key")
            elif k:
                seen_keys.add(k)
            added += 1
        except Exception as e:
            failed += 1
            log(f"      [!] {oid}: {e}")
        if added and added % 100 == 0:
            log(f"      added {added} photo refs…")
    log(f"  [3] imported {added} photo-reference Source Atoms ({failed} failed, "
        f"{collapsed} collapsed) into {pool_id}")
    if collapsed:
        log(f"  [!] {collapsed} records collapsed onto existing atoms — the pool is SMALLER than "
            f"the record count. Stale aliases from an earlier import? Re-run with --id-prefix "
            f"<tag> (fresh aliases) into a NEW --pool-version.")
    fr = dispatch("source.pool.freeze", {"pool": pool_id})
    log(f"  [4] pool FROZEN: {fr.get('member_count')} members, at_seq={fr.get('at_seq')}")
    mo = dispatch("source.modalities", {"pool": pool_id})
    log(f"  done → modalities={mo.get('modalities')}")
    return {"pool": pool_id, "added": added, "failed": failed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as", dest="as_id", default="admin")
    ap.add_argument("--records", default="plants_data/vision/records.jsonl")
    ap.add_argument("--manifest", default="plants_data/vision/manifest.json")
    ap.add_argument("--base", default=None)
    ap.add_argument("--rpc-timeout", type=float, default=300.0)
    ap.add_argument("--pool-version", default="v1")
    ap.add_argument("--derived-from", default="")
    ap.add_argument("--id-prefix", default="",
                    help="prefix object ids (fresh aliases) when a prior import left stale ones")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not client.ping(base):
        print(f"[!] No Cell daemon at {base}. Start one: python akasha.py --serve", file=sys.stderr)
        sys.exit(2)
    gw = client.connect(base, timeout=args.rpc_timeout)

    def d(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": args.as_id, "data": data}, "id": "v"}, "local")
        if isinstance(r, dict) and "error" in r:
            raise RuntimeError(f"{method}: {r['error'].get('message')}")
        return (r or {}).get("result") or {}

    records = [json.loads(l) for l in open(args.records, encoding="utf-8") if l.strip()]
    manifest = json.load(open(args.manifest, encoding="utf-8")) if os.path.exists(args.manifest) else {}
    out = run(d, records, manifest, version=args.pool_version,
              derived_from=args.derived_from, id_prefix=args.id_prefix)
    print(f"  done → {out}")
    gw.close()


if __name__ == "__main__":
    main()
