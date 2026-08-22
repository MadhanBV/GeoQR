import time
import unittest
from utils.geo import calculate_haversine_distance, is_within_radius
from utils.token_generator import generate_qr_token, verify_qr_token
from utils.qr_generator import generate_qr_base64


class TestPhase2Utilities(unittest.TestCase):

    def test_haversine_same_point(self):
        """Distance between identical coordinates should be 0.0 meters."""
        lat, lon = 12.9716, 77.5946  # Bangalore coordinates
        distance = calculate_haversine_distance(lat, lon, lat, lon)
        self.assertEqual(distance, 0.0)

    def test_haversine_known_offset(self):
        """Test distance for ~111 meters North (approx 0.001 degree lat)."""
        lat1, lon1 = 12.9716, 77.5946
        lat2, lon2 = 12.9726, 77.5946  # 0.001 degree north is ~111 meters
        distance = calculate_haversine_distance(lat1, lon1, lat2, lon2)
        self.assertTrue(110.0 <= distance <= 112.0, f"Distance was {distance}m")

    def test_geofence_boundary(self):
        """Test is_within_radius helper function."""
        center_lat, center_lon = 28.6139, 77.2090  # New Delhi
        # Point ~55 meters away
        student_lat, student_lon = 28.6144, 77.2090
        
        # Test with 100m radius -> Should be True
        in_radius, dist = is_within_radius(center_lat, center_lon, student_lat, student_lon, allowed_radius_meters=100.0)
        self.assertTrue(in_radius)
        self.assertTrue(dist < 100.0)

        # Test with 30m radius -> Should be False
        in_radius, dist = is_within_radius(center_lat, center_lon, student_lat, student_lon, allowed_radius_meters=30.0)
        self.assertFalse(in_radius)
        self.assertTrue(dist > 30.0)

    def test_token_generation_and_valid_verification(self):
        """A freshly generated token should be verified successfully within max_age."""
        event_id = "test-event-456"
        token, created_at = generate_qr_token(event_id)
        
        is_valid, payload, msg = verify_qr_token(token, max_age_seconds=25)
        self.assertTrue(is_valid)
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get("event_id"), event_id)
        self.assertEqual(payload.get("created_at"), created_at)

    def test_token_expiration(self):
        """A token older than max_age_seconds must be rejected with SignatureExpired."""
        event_id = "expired-event-999"
        token, _ = generate_qr_token(event_id)
        
        # Simulate expiry: URLSafeTimedSerializer uses integer epoch seconds.
        # Sleeping 2.1s guarantees delta >= 2s which exceeds max_age_seconds=1.
        time.sleep(2.1)
        is_valid, payload, msg = verify_qr_token(token, max_age_seconds=1)
        self.assertFalse(is_valid)
        self.assertIsNone(payload)
        self.assertIn("expired", msg.lower())

    def test_token_tampering_rejection(self):
        """A tampered token string must be immediately rejected."""
        event_id = "tamper-event"
        token, _ = generate_qr_token(event_id)
        tampered_token = token[:-4] + "fake"
        
        is_valid, payload, msg = verify_qr_token(tampered_token, max_age_seconds=25)
        self.assertFalse(is_valid)
        self.assertIsNone(payload)
        self.assertIn("invalid or tampered", msg.lower())

    def test_qr_generator_base64(self):
        """QR generator must produce a non-empty data URI png string."""
        sample_url = "https://geoqr.app/checkin/event-123?token=abc"
        data_uri = generate_qr_base64(sample_url)
        self.assertTrue(data_uri.startswith("data:image/png;base64,"))
        self.assertTrue(len(data_uri) > 100)


if __name__ == "__main__":
    unittest.main()
