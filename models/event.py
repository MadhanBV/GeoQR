import time
import uuid
from typing import Dict, Any, Optional


class Event:
    """Represents a scheduled college event or lecture."""

    def __init__(
        self,
        title: str,
        description: str,
        date: str,
        organizer_lat: float,
        organizer_lon: float,
        radius_meters: float = 50.0,
        event_id: Optional[str] = None,
        created_at: Optional[int] = None,
        is_active: bool = True
    ):
        self.id = event_id or f"evt_{uuid.uuid4().hex[:10]}"
        self.title = title.strip()
        self.description = description.strip()
        self.date = date
        self.organizer_lat = float(organizer_lat)
        self.organizer_lon = float(organizer_lon)
        self.radius_meters = float(radius_meters)
        self.created_at = created_at or int(time.time())
        self.is_active = is_active

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Event object to a Firestore-compatible dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "date": self.date,
            "organizer_lat": self.organizer_lat,
            "organizer_lon": self.organizer_lon,
            "radius_meters": self.radius_meters,
            "created_at": self.created_at,
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, doc_id: str, data: Dict[str, Any]) -> "Event":
        """Constructs an Event object from a Firestore document dictionary."""
        return cls(
            event_id=doc_id or data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            date=data.get("date", ""),
            organizer_lat=data.get("organizer_lat", 0.0),
            organizer_lon=data.get("organizer_lon", 0.0),
            radius_meters=data.get("radius_meters", 50.0),
            created_at=data.get("created_at"),
            is_active=data.get("is_active", True)
        )
