import time
import uuid
from typing import Dict, Any, Optional


class AttendanceRecord:
    """Represents a student's verified attendance record."""

    def __init__(
        self,
        event_id: str,
        student_id: str,
        student_name: str,
        student_lat: float,
        student_lon: float,
        distance_meters: float,
        status: str = "VERIFIED",
        record_id: Optional[str] = None,
        timestamp: Optional[int] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        self.id = record_id or f"att_{uuid.uuid4().hex[:12]}"
        self.event_id = str(event_id)
        self.student_id = str(student_id).strip().upper()
        self.student_name = str(student_name).strip()
        self.student_lat = float(student_lat)
        self.student_lon = float(student_lon)
        self.distance_meters = round(float(distance_meters), 2)
        self.status = status
        self.timestamp = timestamp or int(time.time())
        self.user_agent = user_agent or "Unknown"
        self.ip_address = ip_address or "Unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the AttendanceRecord to a Firestore-compatible dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "student_lat": self.student_lat,
            "student_lon": self.student_lon,
            "distance_meters": self.distance_meters,
            "status": self.status,
            "timestamp": self.timestamp,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address
        }

    @classmethod
    def from_dict(cls, doc_id: str, data: Dict[str, Any]) -> "AttendanceRecord":
        """Constructs an AttendanceRecord object from a Firestore document dictionary."""
        return cls(
            record_id=doc_id or data.get("id"),
            event_id=data.get("event_id", ""),
            student_id=data.get("student_id", ""),
            student_name=data.get("student_name", ""),
            student_lat=data.get("student_lat", 0.0),
            student_lon=data.get("student_lon", 0.0),
            distance_meters=data.get("distance_meters", 0.0),
            status=data.get("status", "VERIFIED"),
            timestamp=data.get("timestamp"),
            user_agent=data.get("user_agent"),
            ip_address=data.get("ip_address")
        )
