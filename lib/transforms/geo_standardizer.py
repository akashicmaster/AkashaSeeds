"""
Transform Plugin: Geo Standardizer (Affine Projector)
Maps local/historical coordinates to modern GPS coordinates using 
3-point affine calibration. Supports multi-layer map registration.
"""
import re
import numpy as np
from typing import Tuple, Optional, Dict, Any

# Name used in CLI: s.map geo_standardizer historical_set modern_set
TRANSFORM_NAME = "geo_standardizer"

def calculate_affine_matrix(src_points: list, dst_points: list) -> np.ndarray:
    """
    Calculates the 3x3 Affine Matrix from 3 pairs of points.
    src_points: [[x1, y1], [x2, y2], [x3, y3]] (Local/Old Map)
    dst_points: [[lat1, lng1], [lat2, lng2], [lat3, lng3]] (Modern GPS)
    """
    # Convert to homogeneous coordinates
    src = np.float32([list(p) + [1] for p in src_points])
    dst = np.float32([list(p) + [1] for p in dst_points])
    
    # Solve: dst.T = M * src.T  => M = (dst.T * inv(src.T))
    # Using transpose to match the coordinate mapping logic
    try:
        matrix = np.dot(dst.T, np.linalg.inv(src.T))
        return matrix
    except np.linalg.LinAlgError:
        # Fallback to Identity if points are collinear
        return np.eye(3)

def transform(content: str, meta: Dict[str, Any]) -> Tuple[str, dict]:
    """
    Standardizes local coordinates to GPS using calibration data.
    Looks for '_calibration' in meta or defaults to identity mapping.
    """
    # 1. Coordinate Extraction (Local/Historical)
    old_x, old_y = None, None
    if "geo_x" in meta and "geo_y" in meta:
        old_x, old_y = float(meta["geo_x"]), float(meta["geo_y"])
    else:
        match = re.search(r'geo:at:(-?\d+\.?\d*),(-?\d+\.?\d*)', content)
        if match:
            old_x, old_y = float(match.group(1)), float(match.group(2))

    if old_x is None or old_y is None:
        return content, meta

    # 2. Calibration Logic
    # Expects '_calibration' in meta: {"src": [[x1,y1]...], "dst": [[lat1,lng1]...]}
    calibration = meta.get("_calibration")
    if calibration and "src" in calibration and "dst" in calibration:
        matrix = calculate_affine_matrix(calibration["src"], calibration["dst"])
    else:
        # Use a pre-calculated matrix if provided, otherwise identity
        matrix = meta.get("_affine_matrix", np.eye(3))

    # 3. Projection (Matrix Multiplication)
    local_vec = np.array([old_x, old_y, 1.0])
    modern_vec = np.dot(matrix, local_vec)
    
    modern_lat = float(modern_vec[0])
    modern_lng = float(modern_vec[1])

    # 4. Meta Enrichment
    new_content = f"{content}\n[Geo] Standardized GPS: {modern_lat:.5f}, {modern_lng:.5f}"
    
    meta["mapped_by"] = TRANSFORM_NAME
    meta["modern_lat"] = modern_lat
    meta["modern_lng"] = modern_lng
    meta["layer_id"] = meta.get("layer_id", "unknown_strata")
    meta["status"] = "georeferenced"
    
    return new_content, meta
