"""
Transform Plugin: Field Note Refiner
Heuristic-based semantic structuralizer for environments without heavy NLP.
Refines 'Low-Res' raw notes into 'High-Res' structured records using 
pattern matching and ontological templates.
"""
import re
import time
from typing import Tuple, Optional

TRANSFORM_NAME = "field_note_refiner"

def transform(content: str, meta: dict) -> Tuple[str, dict]:
    """
    Detects patterns like [Location], [Action], or [Target] in raw text and 
    promotes them to formal metadata, refining the atom's resolution.
    """
    refined_content = content
    
    # 1. Pattern: "At [Location]" -> geo:at
    loc_match = re.search(r'(?:at|@|場所[:：])\s*([^\s,，。]+)', content, re.I)
    if loc_match:
        loc_name = loc_match.group(1)
        meta["geo_label"] = loc_name
        meta["status"] = "structuring"

    # 2. Pattern: "During [Era/Time]" -> chrono:period
    time_match = re.search(r'(?:in|during|時期[:：])\s*([^\s,，。]+)', content, re.I)
    if time_match:
        meta["period"] = time_match.group(1)

    # 3. Structural Refinement (Generating a High-Res Template)
    # If the note is very raw, wrap it in a formal record structure
    if len(content.split()) < 10 and not content.startswith("[RECORD]"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        refined_content = (
            f"[RECORD] {timestamp}\n"
            f"REF_ORIGIN: {content}\n"
            f"RESOLUTION: high_refined"
        )
        meta["refined_at"] = timestamp

    meta["mapped_by"] = TRANSFORM_NAME
    meta["refinement_level"] = 1.0
    
    return refined_content, meta
