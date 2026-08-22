import time
import unittest
from app import create_app
from services.event_service import EventService
from utils.token_generator import generate_qr_token
from firebase.firebase_config import get_firestore_client


class TestPhase5StudentPortal(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Seed sample event at Bangalore campus (Lat: 12.9716, Lon: 77.5946, Radius: 50m)
        self.event = EventService.create_event(
            title="CS204 Database Systems Lecture",
            description="Room 205, Tech Block",
            date="2026-08-25",
            organizer_lat=12.971600,
            organizer_lon=77.594600,
            radius_meters=50.0
        )

    def test_student_checkin_page_render(self):
        """GET /checkin/<event_id>?token=... should render the student form."""
        token, _ = generate_qr_token(self.event.id)
        response = self.client.get(f"/checkin/{self.event.id}?token={token}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CS204 Database Systems Lecture", response.data)
        self.assertIn(b"Anti-Proxy Verification", response.data)

    def test_valid_attendance_submission(self):
        """Submitting valid attendance within 50m should return HTTP 200 and redirect_url."""
        token, _ = generate_qr_token(self.event.id)
        payload = {
            "event_id": self.event.id,
            "token": token,
            "student_name": "Emma Watson",
            "student_id": "CS2026_WATSON",
            "student_lat": 12.971650,  # ~6m away
            "student_lon": 77.594600
        }
        response = self.client.post("/api/attendance/submit", json=payload)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["status_code"], "SUCCESS")
        self.assertIn("/attendance/status", json_data["redirect_url"])

    def test_out_of_bounds_submission(self):
        """Submitting attendance from outside the geofence should return OUT_OF_BOUNDS."""
        token, _ = generate_qr_token(self.event.id)
        payload = {
            "event_id": self.event.id,
            "token": token,
            "student_name": "Faraway Student",
            "student_id": "CS2026_FAR",
            "student_lat": 12.980000,  # ~900m away
            "student_lon": 77.594600
        }
        response = self.client.post("/api/attendance/submit", json=payload)
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["status_code"], "OUT_OF_BOUNDS")

    def test_duplicate_submission(self):
        """Submitting duplicate attendance for the same student ID must return DUPLICATE."""
        student_id = "CS2026_DUP"
        token1, _ = generate_qr_token(self.event.id)
        payload1 = {
            "event_id": self.event.id,
            "token": token1,
            "student_name": "Double Check",
            "student_id": student_id,
            "student_lat": 12.971600,
            "student_lon": 77.594600
        }
        # First submission
        res1 = self.client.post("/api/attendance/submit", json=payload1)
        self.assertEqual(res1.status_code, 200)

        # Second submission
        token2, _ = generate_qr_token(self.event.id)
        payload2 = {
            "event_id": self.event.id,
            "token": token2,
            "student_name": "Double Check",
            "student_id": student_id,
            "student_lat": 12.971600,
            "student_lon": 77.594600
        }
        res2 = self.client.post("/api/attendance/submit", json=payload2)
        self.assertEqual(res2.status_code, 400)
        json_data = res2.get_json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["status_code"], "DUPLICATE")

    def test_status_page_render(self):
        """GET /attendance/status should render the status page with success or error elements."""
        response = self.client.get("/attendance/status?status_code=SUCCESS&student_name=Emma&student_id=CS101&distance=12.5&radius=50")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Attendance Recorded!", response.data)
        self.assertIn(b"Verified Present", response.data)


if __name__ == "__main__":
    unittest.main()
