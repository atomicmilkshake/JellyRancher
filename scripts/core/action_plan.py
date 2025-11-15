#!/usr/bin/env python3
"""
Data Models for Action Plan - Point 5 of JellyRancher Workflow

Defines the data structures for representing proposed file operations
in the editable review table.

Architecture Reference: Section 6 (Data Models)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Dict, Any


class ActionType(Enum):
    """Enumeration for the type of file operation."""
    MOVE = auto()
    RENAME = auto()
    DELETE = auto()
    CREATE_NFO = auto()
    SKIP = auto()
    REVIEW = auto()


class Confidence(Enum):
    """Enumeration for the confidence level of a proposed operation."""
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()
    MANUAL = auto() # Requires manual intervention
    NONE = auto() # No action needed


@dataclass
class ProposedOperation:
    """
    Represents a single proposed action for a file.
    This will be one row in the review table.
    """
    source_path: Path
    destination_path: Optional[Path] = None
    action_type: ActionType = ActionType.SKIP
    confidence: Confidence = Confidence.NONE
    notes: str = ""
    
    # Jellyfin-related context
    jellyfin_status: str = "Unknown" # e.g., "New", "Already in Library", "Path Mismatch"
    jellyfin_id: Optional[str] = None
    current_provider_ids: Dict[str, str] = field(default_factory=dict)
    proposed_provider_ids: Dict[str, str] = field(default_factory=dict)
    
    # Metadata context
    canonical_metadata: Optional[Dict[str, Any]] = None
    
    # User override
    user_approved: Optional[bool] = None # None = no user action, True = approved, False = rejected

    def __post_init__(self):
        """Ensure Path objects are converted properly."""
        if isinstance(self.source_path, str):
            self.source_path = Path(self.source_path)
        if self.destination_path and isinstance(self.destination_path, str):
            self.destination_path = Path(self.destination_path)

