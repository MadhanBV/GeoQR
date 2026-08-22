from typing import Tuple, Optional, List, Dict, Any
from models.attendance import AttendanceRecord
from services.event_service import EventService
from utils.geo import calculate_haversine_distance
from utils.token_generator import verify_qr_token
from firebase.firebase_config import get_firestore_client


class AttendanceService:
    """
    Core verification and processing engine for student attendance submissions.
    Enforces the multi-layer Anti-Proxy defense pipeline.
    """

    @staticmethod
    def process_attendance_submission(
        event_id: str,
        token: str,
        student_id: str,
        student_name: str,
        student_lat: float,
        student_lon: float,
        accuracy: float = 0.0,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[AttendanceRecord], Optional[Dict[str, Any]]]:
        """
        Executes the multi-layer anti-proxy validation pipeline:
        1. Token signature and 25s expiration check
        2. Event active and ID match check
        3. Duplicate check (same student_id + event_id)
        4. Geofence distance calculation (Haversine formula)
        5. Atomic save into Firestore

        :return: (is_success: bool, message: str, record: Optional[AttendanceRecord], meta: Optional[Dict])
        """
        student_id_clean = (student_id or "").strip().upper()
        student_name_clean = (student_name or "").strip()

        # Basic input validation
        if not student_id_clean:
            return False, "Student ID is required.", None, {"error_type": "VALIDATION_ERROR"}
        if not student_name_clean:
            return False, "Full Name is required.", None, {"error_type": "VALIDATION_ERROR"}
        if student_lat is None or student_lon is None:
            return False, "GPS coordinates could not be retrieved. Please allow browser location access.", None, {"error_type": "GPS_MISSING"}

        try:
            lat_f = float(student_lat)
            lon_f = float(student_lon)
        except (ValueError, TypeError):
            return False, "Invalid GPS coordinate format.", None, {"error_type": "GPS_INVALID"}

        # LAYER 1: Token cryptographic signature and 25-second expiration check
        token_valid, payload, token_msg = verify_qr_token(token)
        if not token_valid:
            return False, token_msg, None, {"error_type": "EXPIRED_QR" if "expired" in token_msg.lower() else "INVALID_TOKEN"}

        # LAYER 2: Event existence & token match check
        token_event_id = payload.get("event_id") if payload else None
        if token_event_id != event_id:
            return False, "This QR code does not match the requested event.", None, {"error_type": "EVENT_MISMATCH"}

        event = EventService.get_event_by_id(event_id)
        if not event:
            return False, "Event does not exist or has been removed.", None, {"error_type": "INVALID_EVENT"}

        if not event.is_active:
            return False, "This event is currently closed for attendance.", None, {"error_type": "EVENT_CLOSED"}

        db = get_firestore_client()

        # LAYER 3: Duplicate attendance check
        existing_docs = (
            db.collection("attendance")
            .where("event_id", "==", event_id)
            .where("student_id", "==", student_id_clean)
            .stream()
        )

        for doc in existing_docs:
            rec = doc.to_dict()
            if rec.get("status") == "VERIFIED":
                return False, f"Student ID '{student_id_clean}' has already checked in for this event.", None, {
                    "error_type": "DUPLICATE",
                    "existing_timestamp": rec.get("timestamp")
                }

        # LAYER 4: Server-Side Geofence Haversine calculation with device accuracy tolerance
        distance = calculate_haversine_distance(
            event.organizer_lat,
            event.organizer_lon,
            lat_f,
            lon_f
        )

        # Consider device reported accuracy (capped at 150m buffer) for indoor Wi-Fi / cellular variance
        acc_buffer = min(max(0.0, float(accuracy or 0.0)), 150.0) * 0.6
        allowed_boundary = round(event.radius_meters + acc_buffer, 1)

        if distance > allowed_boundary:
            diff = round(distance - allowed_boundary, 1)
            return False, (
                f"Location out of bounds! You are {distance}m away from the event location. "
                f"Allowed boundary is {allowed_boundary}m (you are {diff}m outside)."
            ), None, {
                "error_type": "OUT_OF_BOUNDS",
                "distance": distance,
                "radius": event.radius_meters,
                "allowed_boundary": allowed_boundary
            }

        # LAYER 5: Save verified record
        record = AttendanceRecord(
            event_id=event.id,
            student_id=student_id_clean,
            student_name=student_name_clean,
            student_lat=lat_f,
            student_lon=lon_f,
            distance_meters=distance,
            status="VERIFIED",
            user_agent=user_agent,
            ip_address=ip_address
        )

        db.collection("attendance").document(record.id).set(record.to_dict())

        return True, "Attendance recorded successfully! Verified present at event.", record, {
            "distance": distance,
            "radius": event.radius_meters
        }

    @staticmethod
    def get_attendees_for_event(event_id: str) -> List[AttendanceRecord]:
        """
        Retrieves all verified attendees for an event.
        """
        db = get_firestore_client()
        docs = db.collection("attendance").where("event_id", "==", event_id).where("status", "==", "VERIFIED").stream()
        records = [AttendanceRecord.from_dict(doc.id, doc.to_dict()) for doc in docs]
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records
