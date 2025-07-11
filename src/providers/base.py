from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class Meeting:
    """Standardized representation of a meeting."""
    id: str
    name: str
    start_time: datetime
    original_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Transcript:
    """Standardized representation of a transcript."""
    text: str
    original_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Note:
    """Standardized representation of notes or highlights."""
    content: str
    original_data: Dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """
    Abstract base class for all transcript providers (connectors).
    Defines a standard interface for the application to interact with
    different transcript sources (APIs, local files, etc.).
    """

    @abstractmethod
    def get_meetings(self, days: float) -> List['Meeting']:
        """
        Fetches a list of available meetings from the source within a given timeframe.

        Args:
            days: The number of past days to search for meetings.

        Returns:
            A list of Meeting objects.
        """
        pass

    @abstractmethod
    def get_transcript(self, meeting: 'Meeting') -> Optional['Transcript']:
        """
        Fetches the full transcript for a specific meeting.

        Args:
            meeting: The Meeting object for which to fetch the transcript.

        Returns:
            A Transcript object or None if not found.
        """
        pass

    @abstractmethod
    def get_notes(self, meeting: 'Meeting') -> Optional['Note']:
        """
        Fetches summarized notes or highlights for a specific meeting.

        Args:
            meeting: The Meeting object for which to fetch the notes.

        Returns:
            A Note object or None if not found.
        """
        pass
