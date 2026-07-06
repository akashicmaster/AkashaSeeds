"""
Transform Plugin: Chrono Standardizer
Maps varied historical and linguistic temporal expressions into normalized ISO-8601 timestamps.
Essential for cross-era synchronization in the Jataka Palimpsest.
"""
import re
from datetime import datetime
from typing import Tuple

# The name used in the CLI (e.g., s.map chrono_standardizer raw_events timeline)
TRANSFORM_NAME = "chrono_standardizer"

def transform(content: str, meta: dict) -> Tuple[str, dict]:
    """
    Standardizes chronological markers found in the content or meta.
    Examples: "Kamakura 1st year" -> "1185-01-01", "12th Century" -> "1100-01-01"
    """
    original_period = meta.get("period", "")
    normalized_date = None
    
    # 1. Japanese Era Mapping (Simple Example for Kamakura)
    # [FUTURE] Integrate with a full Era dictionary/ontology
    if "Kamakura" in original_period or "鎌倉" in original_period:
        match = re.search(r'(\d+)', original_period)
        year_offset = int(match.group(1)) if match else 1
        # Kamakura started approx 1185
        normalized_date = f"{1185 + year_offset - 1}-01-01"
    
    # 2. General Century Mapping
    century_match = re.search(r'(\d+)(st|nd|rd|th)\s+century', content.lower())
    if century_match:
        century = int(century_match.group(1))
        normalized_date = f"{(century - 1) * 100:04d}-01-01"

    if not normalized_date:
        return content, meta

    # 3. Apply the mapping
    new_content = f"{content}\n[Chrono] Standardized: {normalized_date}"
    
    meta["mapped_by"] = TRANSFORM_NAME
    meta["chrono_timestamp"] = normalized_date
    meta["status"] = "standardized"
    
    return new_content, meta
