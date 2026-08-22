from typing import List, Optional
from models.event import Event
from firebase.firebase_config import get_firestore_client


class EventService:
    """Handles business logic for event creation and retrieval."""

    @staticmethod
    def create_event(
        title: str,
        description: str,
        date: str,
        organizer_lat: float,
        organizer_lon: float,
        radius_meters: float = 50.0
    ) -> Event:
        """
        Creates and persists a new event in Firestore.
        """
        db = get_firestore_client()
        event = Event(
            title=title,
            description=description,
            date=date,
            organizer_lat=organizer_lat,
            organizer_lon=organizer_lon,
            radius_meters=radius_meters
        )
        db.collection("events").document(event.id).set(event.to_dict())
        return event

    @staticmethod
    def get_event_by_id(event_id: str) -> Optional[Event]:
        """
        Fetches an event by its unique ID.
        """
        if not event_id:
            return None
        db = get_firestore_client()
        doc = db.collection("events").document(event_id).get()
        if not doc.exists:
            return None
        return Event.from_dict(doc.id, doc.to_dict())

    @staticmethod
    def get_all_events() -> List[Event]:
        """
        Fetches all events ordered by creation time descending.
        """
        db = get_firestore_client()
        docs = db.collection("events").stream()
        events = [Event.from_dict(doc.id, doc.to_dict()) for doc in docs]
        events.sort(key=lambda e: e.created_at, reverse=True)
        return events

    @staticmethod
    def get_event_attendance_count(event_id: str) -> int:
        """
        Returns the total verified attendance count for an event.
        """
        db = get_firestore_client()
        records = list(db.collection("attendance").where("event_id", "==", event_id).where("status", "==", "VERIFIED").stream())
        return len(records)
