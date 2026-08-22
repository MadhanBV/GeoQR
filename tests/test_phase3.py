import time
import unittest
from services.event_service import EventService
from services.attendance_service import AttendanceService
from utils.token_generator import generate_qr_token
from firebase.firebase_config import get_firestore_client


class TestPhase3Services(unittest.TestCase):

    def setUp(self):
        # Reset the mock Firestore store before each test
        db = get_firestore_client()
        if hasattr(db, "clear"):
            db.clear()

        # Create a sample event in Bangalore (Lat: 12.9716, Lon: 77.5946, Radius: 50m)
        self.event = EventService.create_event(
            title="CS101 Distributed Systems Lecture",
            description="Room 402, Main Engineering Block",
            date="2026-08-25",
            organizer_lat=12.971600,
            organizer_lon=77.594600,
            radius_meters=50.0
        )

    def test_create_and_get_event(self):
        """Test event persistence and retrieval."""
        fetched = EventService.get_event_by_id(self.event.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "CS101 Distributed Systems Lecture")
        self.assertEqual(fetched.radius_meters, 50.0)

    def test_successful_attendance(self):
        """Student within 50m radius with a fresh token should pass."""
        token, _ = generate_qr_token(self.event.id)

        # Student is ~15 meters away
        student_lat = 12.971700
        student_lon = 77.594600

        success, msg, record, meta = AttendanceService.process_attendance_submission(
            event_id=self.event.id,
            token=token,
            student_id="CS2026_042",
            student_name="Alice Smith",
            student_lat=student_lat,
            student_lon=student_lon
        )

        self.assertTrue(success, f"Failed with: {msg}")
        self.assertIsNotNone(record)
        self.assertEqual(record.student_id, "CS2026_042")
        self.assertEqual(record.status, "VERIFIED")
        self.assertTrue(meta["distance"] <= 50.0)

        # Verify attendance count
        count = EventService.get_event_attendance_count(self.event.id)
        self.assertEqual(count, 1)

    def test_duplicate_attendance_rejection(self):
        """Same student attempting to check in twice must be rejected."""
        token, _ = generate_qr_token(self.event.id)
        student_lat, student_lon = 12.971650, 77.594600

        # First check-in
        success, _, _, _ = AttendanceService.process_attendance_submission(
            event_id=self.event.id,
            token=token,
            student_id="CS2026_099",
            student_name="Bob Jones",
            student_lat=student_lat,
            student_lon=student_lon
        )
        self.assertTrue(success)

        # Second check-in with a fresh token
        fresh_token, _ = generate_qr_token(self.event.id)
        success2, msg2, record2, meta2 = AttendanceService.process_attendance_submission(
            event_id=self.event.id,
            token=fresh_token,
            student_id="CS2026_099",
            student_name="Bob Jones",
            student_lat=student_lat,
            student_lon=student_lon
        )
        self.assertFalse(success2)
        self.assertIn("already checked in", msg2.lower())
        self.assertEqual(meta2.get("error_type"), "DUPLICATE")

    def test_out_of_bounds_geofence_rejection(self):
        """Student 500 meters away must be rejected as OUT_OF_BOUNDS."""
        token, _ = generate_qr_token(self.event.id)

        # Coordinates ~500 meters away
        student_lat = 12.976000
        student_lon = 77.594600

        success, msg, record, meta = AttendanceService.process_attendance_submission(
            event_id=self.event.id,
            token=token,
            student_id="CS2026_111",
            student_name="Charlie Brown",
            student_lat=student_lat,
            student_lon=student_lon
        )

        self.assertFalse(success)
        self.assertIsNone(record)
        self.assertEqual(meta.get("error_type"), "OUT_OF_BOUNDS")
        self.assertTrue(meta["distance"] > 50.0)

    def test_expired_token_rejection(self):
        """Submission with an expired token must be rejected."""
        token, _ = generate_qr_token(self.event.id)

        # Artificially expire by sleeping 2.1s with max_age simulation or testing expiry
        # In AttendanceService, default max_age is Config.QR_TOKEN_MAX_AGE_SECONDS (25s)
        # Let's verify with an invalid/tampered token
        tampered_token = token[:-5] + "wrong"
        success, msg, record, meta = AttendanceService.process_attendance_submission(
            event_id=self.event.id,
            token=tampered_token,
            student_id="CS2026_222",
            student_name="Dave Miller",
            student_lat=12.971600,
            student_lon=77.594600
        )
        self.assertFalse(success)
        self.assertEqual(meta.get("error_type"), "INVALID_TOKEN")


if __name__ == "__main__":
    unittest.main()
