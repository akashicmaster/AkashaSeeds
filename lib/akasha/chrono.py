import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any

class TemporalAspect(Enum):
    """
    Defines the linguistic aspect of a memory or event.
    Essential for understanding the 'state' of a historical fact,
    and crucial for Jataka's Dream Simulations (distinguishing past facts from future possibilities).
    """
    PERFECTIVE = "perfective"  # Completed event (e.g., 'The temple was built')
    PROGRESSIVE = "progressive" # Ongoing action (e.g., 'The festival is being held')
    STATIVE     = "stative"     # Persistent state (e.g., 'The ruins remain')
    PROSPECTIVE = "prospective" # Future/Planned event (e.g., 'A new era will begin')

@dataclass
class TemporalContext:
    """
    Multi-axial Time Structure for Akashic Atoms.
    Bridges physical system time with historical narrative time.
    """
    # 1. Physical Axis (System Timestamp)
    system_time: float = field(default_factory=time.time)

    # 2. Narrative Axis (The 'When' in history)
    anchor_year: Optional[int] = None       # e.g., 1192
    period_name: Optional[str] = "unknown" # e.g., 'kamakura_era'

    # 3. Linguistic Aspect Axis
    aspect: TemporalAspect = TemporalAspect.STATIVE

    # 4. Relational Axis (Time relative to the current focus)
    # Allows for recursive time-layering: 'Before that', 'During the battle', etc.
    relative_to_key: Optional[str] = None 

    def __post_init__(self):
        """Automatic era inference if year is provided but period is unknown."""
        if self.anchor_year and self.period_name == "unknown":
            self.period_name = self.infer_period(self.anchor_year)

    @staticmethod
    def infer_period(year: int) -> str:
        """
        Maps a specific year to a known historical strata.
        (Currently tuned for Japanese history, but can be expanded via Ontology JSONs in the future)
        """
        if 1185 <= year <= 1333:
            return "kamakura_era"
        elif 1336 <= year <= 1573:
            return "muromachi_era"
        elif 1603 <= year <= 1868:
            return "edo_era"
        return "ancient" if year < 1185 else "modern"

    def to_trait(self) -> str:
        """
        Converts the temporal state into a searchable Akashic trait string.
        Format: chrono:[period]:[aspect]
        """
        p = self.period_name or "unknown"
        a = self.aspect.value
        return f"chrono:{p}:{a}"

    @classmethod
    def from_trait(cls, trait: str):
        """
        Reconstructs a TemporalContext from an Akashic trait string.
        """
        parts = trait.split(":")
        if len(parts) < 3 or parts[0] != "chrono":
            return cls()
        
        try:
            aspect_enum = TemporalAspect(parts[2])
        except ValueError:
            aspect_enum = TemporalAspect.STATIVE
            
        return cls(period_name=parts[1], aspect=aspect_enum)

    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata for Jataka spatiotemporal synchronization."""
        return {
            "year": self.anchor_year,
            "period": self.period_name,
            "aspect": self.aspect.value,
            "recorded_at": self.system_time,
            "relative_to": self.relative_to_key
        }

    def shift_context(self, year_delta: int):
        """Creates a new context shifted in time, preserving aspect."""
        if self.anchor_year:
            return TemporalContext(
                anchor_year=self.anchor_year + year_delta,
                aspect=self.aspect,
                relative_to_key=self.relative_to_key
            )
        return self

    def temporal_distance_to(self, other_context: 'TemporalContext') -> Optional[int]:
        """
        [NEW] Magnetic Neighborhood Foundation.
        Calculates the absolute distance in years between two historical contexts.
        Used by the Spatiotemporal Engine to compute temporal gravity (e.g., nodes within 10 years).
        """
        if self.anchor_year is not None and other_context.anchor_year is not None:
            return abs(self.anchor_year - other_context.anchor_year)
        return None
