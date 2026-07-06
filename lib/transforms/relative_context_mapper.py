"""
Transform Plugin: Relative Context Mapper
Resolves relative spatiotemporal expressions:
- "10 hours west from [Pivot]" -> Modern GPS coordinates.
- "13 years after [Pivot]" -> Normalized ISO Timestamp.
Calculates coordinates based on ancient travel speeds (e.g., Trireme knots).
"""
import re
import datetime
from typing import Tuple, Optional, Dict, Any

TRANSFORM_NAME = "relative_context_mapper"

# Ancient World Travel Constants
KNOTS_TRIREME = 4.0  # Approx 4 nautical miles per hour (avg speed)
KM_PER_NM = 1.852    # 1 Nautical Mile to Kilometers
DEGREE_LAT_KM = 111.0 # 1 Degree Latitude in KM (approx)

def transform(content: str, meta: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Parses relative expressions and maps them to absolute coordinates/time.
    Requires a 'pivot_atom' in meta to resolve the starting point.
    """
    pivot_meta = meta.get("_pivot_meta", {})
    
    # 1. Spatial Resolution: "X hours [Direction] from..."
    # Example: "10 hours west from Gibraltar"
    spatial_match = re.search(r'(\d+)\s*hours?\s*(west|east|north|south)', content, re.I)
    if spatial_match and pivot_meta:
        hours = float(spatial_match.group(1))
        direction = spatial_match.group(2).lower()
        
        start_lat = pivot_meta.get("modern_lat", pivot_meta.get("lat"))
        start_lng = pivot_meta.get("modern_lng", pivot_meta.get("lng"))
        
        if start_lat is not None and start_lng is not None:
            # Distance in Kilometers (Ancient speed * hours)
            distance_km = hours * KNOTS_TRIREME * KM_PER_NM
            
            # Simple vector offset (Approximation for test environment)
            delta_lat, delta_lng = 0.0, 0.0
            if direction == "north": delta_lat = distance_km / DEGREE_LAT_KM
            elif direction == "south": delta_lat = -distance_km / DEGREE_LAT_KM
            elif direction == "west":  delta_lng = -distance_km / (DEGREE_LAT_KM * 0.8) # Approx at mid-latitude
            elif direction == "east":  delta_lng = distance_km / (DEGREE_LAT_KM * 0.8)
            
            meta["modern_lat"] = float(start_lat) + delta_lat
            meta["modern_lng"] = float(start_lng) + delta_lng
            meta["status"] = "spatial_resolved"

    # 2. Temporal Resolution: "X years after/before [Pivot]"
    # Example: "13 years after the fall of Carthage"
    temporal_match = re.search(r'(\d+)\s*years?\s*(after|before)', content, re.I)
    if temporal_match and pivot_meta:
        years = int(temporal_match.group(1))
        direction = temporal_match.group(2).lower()
        
        pivot_time_str = pivot_meta.get("chrono_timestamp", pivot_meta.get("period"))
        # Simplified ancient year resolution
        try:
            pivot_year = int(re.search(r'(-?\d+)', str(pivot_time_str)).group(1))
            resolved_year = pivot_year + years if direction == "after" else pivot_year - years
            meta["chrono_timestamp"] = f"{resolved_year:04d}-01-01"
            meta["status"] = "temporal_resolved"
        except (AttributeError, ValueError):
            pass

    meta["mapped_by"] = TRANSFORM_NAME
    return content, meta
