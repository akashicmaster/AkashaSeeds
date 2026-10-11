#!/usr/bin/env python3
"""
Generate sample seed .akasha capsule files for first-login onboarding.

Seeds are stored under app/seeds/{app_name}/*.akasha and loaded automatically
when a user first opens a given app.  Run this script any time seed content
changes; it overwrites existing files in-place.

Usage:
    python app/scripts/generate_seeds.py

Future: replace this script with a sys.seed.export RPC that lets app
developers export any open document as a seed file directly from within the
running app (admin permission required).
"""

import hashlib
import json
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEEDS_ROOT   = PROJECT_ROOT / "seeds"
TIMESTAMP    = 1_700_000_000.0   # fixed timestamp keeps files stable under git diff
AUTHOR       = "system"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def atom_id(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def build_note_capsule(
    title: str,
    chunks: list[str],
    *,
    order: int = 1,
    category: str = "general",
    locale: str = "en",
    doc_type: str = "note",
) -> dict:
    """Build a note or loom:note capsule dict."""
    root_id   = atom_id(title)
    atoms     = {root_id: title}
    links     = []
    prev_id   = None

    for chunk in chunks:
        cid = atom_id(chunk)
        atoms[cid] = chunk
        rel = "sys:top" if prev_id is None else "sys:next"
        src = root_id if prev_id is None else prev_id
        links.append({"src": src, "dst": cid, "rel": rel,
                      "author": AUTHOR, "timestamp": TIMESTAMP})
        prev_id = cid

    return {
        "metadata": {
            "protocol":       "akasha_capsule_v1.2",
            "author":         AUTHOR,
            "timestamp":      TIMESTAMP,
            "doc_type":       doc_type,
            "concept_id":     root_id,
            "extracted_since": 0.0,
            "seed": {
                "kind":     "sample",
                "title":    title,
                "order":    order,
                "category": category,
                "locale":   locale,
            },
        },
        "atoms":    atoms,
        "links":    links,
        "telemetry": {},
    }


def build_fieldnote_capsule(
    title: str,
    observations: list[dict],
    *,
    order: int = 1,
    category: str = "general",
    project: str | None = None,
    region: str | None = None,
    season: str | None = None,
    locale: str = "en",
) -> dict:
    """
    Build a fieldnote capsule dict.

    Each entry in observations is:
        {"text": str, "role": str, "confidence": float | None, "period": str | None}
    """
    root_id   = atom_id(title)
    atoms     = {root_id: title}
    links     = []
    atom_meta = {}
    prev_id   = None

    for obs in observations:
        text = obs["text"]
        cid  = atom_id(text)
        atoms[cid] = text
        rel = "sys:top" if prev_id is None else "sys:next"
        src = root_id if prev_id is None else prev_id
        links.append({"src": src, "dst": cid, "rel": rel,
                      "author": AUTHOR, "timestamp": TIMESTAMP})
        atom_meta[cid] = {
            "role":       obs.get("role", "observation"),
            "confidence": obs.get("confidence"),
            "period":     obs.get("period"),
        }
        prev_id = cid

    return {
        "metadata": {
            "protocol":        "akasha_capsule_v1.2",
            "author":          AUTHOR,
            "timestamp":       TIMESTAMP,
            "doc_type":        "fieldnote",
            "concept_id":      root_id,
            "extracted_since": 0.0,
            "seed": {
                "kind":     "sample",
                "title":    title,
                "order":    order,
                "category": category,
                "project":  project,
                "region":   region,
                "season":   season,
                "locale":   locale,
            },
        },
        "atoms":     atoms,
        "links":     links,
        "atom_meta": atom_meta,
        "telemetry": {},
    }


def write_seed(app_name: str, filename: str, capsule: dict) -> None:
    out_dir  = SEEDS_ROOT / app_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    out_path.write_text(json.dumps(capsule, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {out_path.relative_to(PROJECT_ROOT)}")


# ─────────────────────────────────────────────────────────────────────────────
# Seed definitions
# ─────────────────────────────────────────────────────────────────────────────

def generate_note_seeds():
    print("note seeds:")

    write_seed("note", "001_welcome.akasha", build_note_capsule(
        title  = "Welcome to Note",
        order  = 1,
        chunks = [
            "This is your first note — feel free to edit or delete it.",
            "Notes are the primary place to capture and develop your thinking. "
            "Each note is made of chunks you can reorganise with drag-and-drop.",
            "Use the File menu to export your note as an Akasha capsule file (.akasha), "
            "or to import notes shared by others.",
            "Tip: open the Guide (? button) for a full list of keyboard shortcuts.",
        ],
    ))

    write_seed("note", "002_getting_started.akasha", build_note_capsule(
        title  = "Getting Started",
        order  = 2,
        chunks = [
            "Akasha stores everything as a graph of atoms linked by relationships.",
            "Every chunk you write becomes an atom in your local cortex. "
            "Links between atoms form the structure of your knowledge.",
            "You can connect notes to field notes, surveys, and loom pieces — "
            "the graph grows with your thinking.",
            "This sample note is yours to keep, edit, or delete. "
            "Duplicate it via File → Duplicate if you want to use it as a starting point.",
        ],
    ))


def generate_fieldnote_seeds():
    print("fieldnote seeds:")

    write_seed("fieldnote", "001_archaeology_sample.akasha", build_fieldnote_capsule(
        title    = "Sample: Archaeological Site Survey",
        order    = 1,
        category = "archaeology",
        project  = "Sample Project",
        region   = "Region A",
        season   = "2024-Spring",
        observations = [
            {
                "text":       "Survey grid established at 10 m intervals across the 2-hectare study area.",
                "role":       "method",
                "confidence": None,
                "period":     None,
            },
            {
                "text":       "Surface scatter of lithic debitage concentrated in the northeast quadrant.",
                "role":       "observation",
                "confidence": 0.9,
                "period":     None,
            },
            {
                "text":       "Possible hearth feature identified at Grid 4-N; charcoal present, pending dating.",
                "role":       "observation",
                "confidence": 0.7,
                "period":     "Indeterminate",
            },
            {
                "text":       "Ceramic sherds consistent with regional Late Bronze Age assemblages.",
                "role":       "interpretation",
                "confidence": 0.75,
                "period":     "Late Bronze Age",
            },
            {
                "text":       "Recommend targeted excavation of northeast quadrant in next season.",
                "role":       "recommendation",
                "confidence": None,
                "period":     None,
            },
        ],
    ))

    write_seed("fieldnote", "002_ecology_sample.akasha", build_fieldnote_capsule(
        title    = "Sample: Forest Inventory Transect",
        order    = 2,
        category = "ecology",
        project  = "Sample Project",
        region   = "Region B",
        season   = "2024-Autumn",
        observations = [
            {
                "text":       "50 m transect established along compass bearing 045°.",
                "role":       "method",
                "confidence": None,
                "period":     None,
            },
            {
                "text":       "Canopy dominated by Quercus robur; understorey sparse with Corylus avellana.",
                "role":       "observation",
                "confidence": 0.95,
                "period":     None,
            },
            {
                "text":       "DBH measurements recorded for 23 trees; mean 42 cm, range 12–110 cm.",
                "role":       "observation",
                "confidence": 1.0,
                "period":     None,
            },
            {
                "text":       "Stand age estimated at 80–120 years based on DBH distribution.",
                "role":       "interpretation",
                "confidence": 0.7,
                "period":     "Late 19th–early 20th century",
            },
        ],
    ))


def generate_loom_seeds():
    print("loom seeds:")

    write_seed("loom", "001_first_piece.akasha", build_note_capsule(
        title    = "My First Piece",
        order    = 1,
        doc_type = "loom:note",
        chunks   = [
            "Welcome to Loom — a space for longer-form writing and composition.",
            "Unlike Note, Loom pieces are meant to be developed over time into polished text. "
            "Each chunk is a paragraph or section you can rearrange freely.",
            "Start writing here, or delete this sample and create your own piece from scratch.",
        ],
    ))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Generating seeds under {SEEDS_ROOT.relative_to(PROJECT_ROOT)}/")
    generate_note_seeds()
    generate_fieldnote_seeds()
    generate_loom_seeds()
    print("Done.")
