import unittest
from app import create_app
from services.event_service import EventService
from firebase.firebase_config import get_firestore_client


class TestPhase4HostPortal(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Clear mock firestore
        db = get_firestore_client()
        if hasattr(db, "clear"):
            db.clear()

        # Seed sample event
        self.event = EventService.create_event(
            title="Advanced Algorithms Lecture",
            description="Room 101, Computer Science Wing",
            date="2026-08-30",
            organizer_lat=13.0827,
            organizer_lon=80.2707,
            radius_meters=40.0
        )

    def test_create_event_page_render(self):
        """GET /host/create should return HTTP 200."""
        response = self.client.get("/host/create")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Create New Event", response.data)

    def test_create_event_post_submission(self):
        """POST /host/create with valid fields should create event and redirect."""
        data = {
            "title": "Machine Learning Lab",
            "description": "AI Research Lab 3",
            "date": "2026-09-01",
            "organizer_lat": "12.9716",
            "organizer_lon": "77.5946",
            "radius_meters": "35"
        }
        response = self.client.post("/host/create", data=data, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/host/event/", response.headers["Location"])

    def test_host_dashboard_render(self):
        """GET /host/event/<event_id> should render host live dashboard."""
        response = self.client.get(f"/host/event/{self.event.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Advanced Algorithms Lecture", response.data)
        self.assertIn(b"Anti-Proxy Security Engine", response.data)

    def test_dynamic_qr_token_api(self):
        """GET /api/event/<event_id>/qr-token should return valid rolling token and base64 QR."""
        response = self.client.get(f"/api/event/{self.event.id}/qr-token")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertTrue(len(json_data["token"]) > 20)
        self.assertTrue(json_data["qr_image"].startswith("data:image/png;base64,"))
        self.assertEqual(json_data["expires_in"], 25)
        self.assertIn(self.event.id, json_data["checkin_url"])

    def test_event_attendees_api(self):
        """GET /api/event/<event_id>/attendees should return current attendee list."""
        response = self.client.get(f"/api/event/{self.event.id}/attendees")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["count"], 0)
        self.assertEqual(json_data["attendees"], [])


if __name__ == "__main__":
    unittest.main()
