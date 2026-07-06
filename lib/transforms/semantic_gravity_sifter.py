"""
Transform Plugin: Semantic Gravity Sifter (Fuzzy Enhanced)
Combined Morphism for Semantic Filtering and Concentric Layering.
Now supports 'Fuzzy Descriptors' to automatically set resolution and thresholds.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any

TRANSFORM_NAME = "semantic_gravity_sifter"

# Fuzzy Descriptor Mapping (Internal Dictionary)
FUZZY_MAP = {
    "exactly": {"threshold": 0.95, "resolution": 1},
    "around":   {"threshold": 0.75, "resolution": 5},
    "near":     {"threshold": 0.60, "resolution": 8},
    "fuzzy":    {"threshold": 0.40, "resolution": 12},
}

def transform(content: str, meta: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Applies gravitational sifting with support for fuzzy descriptors.
    The descriptor can be passed via meta['_fuzzy_type'].
    """
    target_vector = meta.get("_target_vector")
    current_vector = meta.get("embedding")
    
    # Resolve Fuzziness from Descriptor
    descriptor = meta.get("_fuzzy_type", "default").lower()
    spec = FUZZY_MAP.get(descriptor, {
        "threshold": float(meta.get("_threshold", 0.5)),
        "resolution": int(meta.get("_resolution", 5))
    })
    
    threshold = spec["threshold"]
    resolution = spec["resolution"]

    if target_vector is None or current_vector is None:
        return content, meta

    # 1. Similarity Calculation
    v1, v2 = np.array(target_vector), np.array(current_vector)
    norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm_product == 0: return content, meta
    
    similarity = float(np.dot(v1, v2) / norm_product)
    
    # 2. Sift (Filtering)
    if similarity < threshold:
        return None

    # 3. Shell Assignment (Mapping Similarity to fog depth)
    # Range [threshold...1.0] -> [resolution-1...0]
    normalized_sim = (similarity - threshold) / (1.0 - threshold) if 1.0 > threshold else 1.0
    shell_id = int((1.0 - normalized_sim) * resolution)
    shell_id = max(0, min(shell_id, resolution - 1))
    
    # 4. Gravity Intensity
    intensity = float(np.exp(-shell_id))

    # 5. Metadata Update
    meta["mapped_by"] = TRANSFORM_NAME
    meta["semantic_score"] = similarity
    meta["shell_id"] = shell_id
    meta["gravity_intensity"] = intensity
    meta["_viz_opacity"] = float(max(0.1, normalized_sim))
    meta["_viz_size"] = float(max(5, 25 * (normalized_sim ** 2)))
    
    return content, meta
