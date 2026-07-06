"""
Transform Plugin: Affine 2D Mapping
Transforms historical/local coordinates to modern geographic coordinates.
This is a pure function. It handles no database operations.
"""
import re

# The name used in the CLI (e.g., s.map affine_2d src dst)
TRANSFORM_NAME = "affine_2d"

def transform(content: str, meta: dict) -> tuple[str, dict]:
    """
    Applies an affine transformation matrix to coordinates found in the atom.
    """
    old_x, old_y = 0.0, 0.0
    coords_found = False
    
    # 1. Extract coordinates — prefer metadata fields, fall back to inline geo tag
    if "geo_x" in meta and "geo_y" in meta:
        old_x, old_y = float(meta["geo_x"]), float(meta["geo_y"])
        coords_found = True
    else:
        # Search for a geo:at:lat,lng tag embedded in the content
        match = re.search(r'geo:at:(-?\d+\.?\d*),(-?\d+\.?\d*)', content)
        if match:
            old_x, old_y = float(match.group(1)), float(match.group(2))
            coords_found = True

    if not coords_found:
        # No coordinates found — return atom unchanged
        return content, meta

    # 2. Apply affine transformation (placeholder coefficients; replace with a
    #    calibrated matrix derived from ground-control-point alignment)
    new_x = old_x * 1.5 + 2.0
    new_y = old_y * 0.8 - 1.0

    # 3. Produce updated content and metadata
    new_content = f"{content}\n[Jataka] Modern Geo: {new_x:.4f}, {new_y:.4f}"
    
    meta["mapped_by"] = TRANSFORM_NAME
    meta["modern_geo_x"] = new_x
    meta["modern_geo_y"] = new_y
    
    return new_content, meta
