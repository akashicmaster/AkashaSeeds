#!/usr/bin/env python3
"""
blvh_mock_image.py — create ONE mock blvh image atom (coordinates only, NO binary) so the front end
can dive it and test the embed pipeline end to end (view → focus.meta → HF /rows → inline image).

This is a TEST FIXTURE, not corpus data: the mock atoms are aliased blvh:image:mock:* /
blvh:obs:seg:mock:* and are NOT added to blvh:all or any sample set, so they never pollute the
diveable corpus. Written at scope=universal so a guest session (the real GUI) can dive them.

Start a daemon first (python akasha.py --serve), then:
    python app/scripts/blvh_mock_image.py --as <admin_id>   # create (write as THIS cell's admin)
    python app/scripts/blvh_mock_image.py --remove --as <admin_id>   # delete it
`--as` must be the id that ran genesis (often not literally "admin" — e.g. --as henri): the
universal write runs as that identity, and a non-admin id lands in a private cortex the GUI's
guest session can't read. The script self-verifies guest-readability and tells you if it didn't.

The image field values point at a VERIFIED row (config=plates / split=train / offset=10432), which
resolves to a real British Library plate ("The History of Ogle County, Illinois Illustrated", 1878)
via the HF /rows API — so the GUI resolves + embeds a real image browser-side. Swap in another
verified row freely; the point is a live focus.meta the GUI resolves.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

IMG = "blvh:image:mock:0001"
SEG = "blvh:obs:seg:mock:0001:00"

IMG_META = {
    "concept": "blvh_image",
    "dataset_id": "biglam/british-library-book-images", "dataset_revision": "",
    # VERIFIED row: config=plates / split=train / offset=10432 resolves to a real BL plate
    # ("The History of Ogle County, Illinois Illustrated", 1878) via the HF /rows API.
    "config": "plates", "split": "train", "row_index": 10432, "file_row_number": None,
    "source_filename": "002698018_0_000032_1_The History of Ogle County  Illinois Illustrated_1878.jpg",
    "record_id": "002698018", "date": "1878", "image_type": "plates",
    "media_type": "image/jpeg", "presentation_mode": "external_resolved_image",
    "source_record_url": "", "attribution": "British Library",
    "rights": "Public Domain Mark / CC0-1.0 dataset tag", "display_status": "ok",
    "last_resolved_at": None,
}
SEG_META = {
    "concept": "blvh_seg_observation", "observation_status": "machine_prediction",
    "target_image": IMG, "instance_index": 0, "bbox_xywh": [112, 340, 486, 502],
    "score": 0.27, "area": 243972, "rectangularity": 0.71,
    "model_id": "davanstrien/bl-crop-tighten-rfdetrseg-clip10", "model_sha": "<sha>",
    "threshold_at_source": 0.10, "local_selection_threshold": 0.10,
    "src_width": 1024, "src_height": 1536,
    "mask_note": "Machine-predicted segmentation — not hand-verified",
}


def main():
    ap = argparse.ArgumentParser(description="Create/remove the blvh mock image fixture.")
    ap.add_argument("--remove", action="store_true", help="delete the mock atoms instead of creating them")
    ap.add_argument("--base", default=None, help="daemon data dir (default AKASHA_DATA_DIR or ./data)")
    # The universal (nucleus) write must run as THIS cell's admin/librarian — NOT a hardcoded
    # name. The admin is whoever ran genesis (often not literally "admin", e.g. "henri"), and a
    # non-admin client_id over the local socket writes into a private cortex the GUI's guest
    # session can't read (→ "Focal point dissolved"). system.* is socket-denied. So take the id.
    ap.add_argument("--as", dest="as_id", default="admin",
                    help="admin/librarian user id to write as (default 'admin'; use your genesis "
                         "admin id, e.g. --as henri, if the atom ends up unreadable)")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not client.ping(base):
        print(f"[!] No Cell daemon at {base}. Start one:  python akasha.py --serve", file=sys.stderr)
        sys.exit(2)
    gw = client.connect(base)

    def d(method, data, tok=None):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": tok or args.as_id, "data": data}, "id": "m"}, "local")
        return r.get("result") if isinstance(r, dict) and "result" in r else r

    def guest_can_read(atom_id):
        """Confirm the atom is universal/guest-readable — the whole point of the fixture."""
        g = d("session.guest.create", {})
        gt = (g or {}).get("binding_key") if isinstance(g, dict) else None
        if not gt:
            return None   # couldn't mint a guest — skip the check rather than false-alarm
        r = d("view", {"id": atom_id}, tok=gt)
        return isinstance(r, dict) and "focus" in r

    if args.remove:
        for a in (SEG, IMG):
            d("rm", {"id": a})
        print(f"  removed {IMG} + {SEG}")
        gw.close()
        return

    # image atom — write (content + meta) at universal scope, then alias it (w takes no alias arg)
    w = d("w", {"text": "[blvh:image:mock:0001] MOCK British Library book-image crop (coordinates only, "
                        "no binary) — front-end embed fixture.", "meta": IMG_META, "scope": "universal"})
    img_key = (w or {}).get("key")
    d("alias", {"id": img_key, "name": IMG})
    # a near-threshold segmentation observation OF the image, generated by RF-DETR
    ws = d("w", {"text": "[blvh:obs:seg:mock:0001:00] MOCK RF-DETR segmentation prediction of "
                         "blvh:image:mock:0001 (score 0.27 — near threshold).", "meta": SEG_META, "scope": "universal"})
    d("alias", {"id": (ws or {}).get("key"), "name": SEG})
    d("ln", {"src": SEG, "dst": IMG, "rel": "blvh:observation_of"})
    d("ln", {"src": SEG, "dst": "blvh:model:rfdetr_crop_tighten", "rel": "blvh:generated_by"})
    d("ln", {"src": IMG, "dst": "blvh:dataset:book_images", "rel": "blvh:derived_from"})

    # Self-verify: the fixture is worthless unless a GUEST (the real GUI session) can read it.
    # If not, the write landed in a private cortex — almost always because --as isn't this cell's
    # admin id. Fail loudly with the fix instead of leaving a silently-unreadable atom.
    readable = guest_can_read(IMG)
    if readable is False:
        print(f"\n[!] Created blvh:image:mock:0001 as '{args.as_id}', but a GUEST session cannot read "
              f"it — it did not land in the universal (nucleus) store.", file=sys.stderr)
        print(f"    '{args.as_id}' is probably not THIS cell's admin/librarian. Re-run pointing at your "
              f"genesis admin id, e.g.:", file=sys.stderr)
        print(f"        python app/scripts/blvh_mock_image.py --remove --as {args.as_id}", file=sys.stderr)
        print(f"        python app/scripts/blvh_mock_image.py --as <your_admin_id>   # e.g. --as henri",
              file=sys.stderr)
        gw.close()
        sys.exit(3)

    m = IMG_META
    rows = (f"https://datasets-server.huggingface.co/rows?dataset=biglam%2Fbritish-library-book-images"
            f"&config={m['config']}&split={m['split']}&offset={m['row_index']}&length=1")
    _ok = "" if readable is None else "  ✓ guest-readable (universal)\n"
    print(("\n" + _ok) + f"  Created the mock fixture (universal scope; NOT in blvh:all / sample sets):")
    print(f"    {IMG}   (blvh_image — the coordinates the GUI resolves)")
    print(f"    {SEG}   (blvh_seg_observation — the near-threshold mask, observation_of the image)")
    print(f"\n  Dive it (guest-safe):")
    print(f"    view id=\"{IMG}\"      # focus.meta carries the coordinates below; ignore semantic_vector")
    print(f"    view id=\"{SEG}\"      # the mask observation; label it 'Machine-predicted … not hand-verified'")
    print(f"\n  Browser-side resolution the GUI performs (docs/for-llm/blvh-image-presentation.md §2):")
    print(f"    GET {rows}")
    print(f"    → rows[0].row.image.src  (signed, expiring — render, never persist)\n")
    print(f"  Remove when done:  python app/scripts/blvh_mock_image.py --remove\n")
    gw.close()


if __name__ == "__main__":
    main()
