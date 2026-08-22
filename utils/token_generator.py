import uuid
import time
from typing import Dict, Any, Tuple, Optional
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature, BadTimeSignature
from config import Config


# Custom salt namespace to separate QR tokens from other sessions
TOKEN_SALT = "geoqr-attendance-token-v1"


def get_serializer(secret_key: Optional[str] = None) -> URLSafeTimedSerializer:
    """
    Constructs a URLSafeTimedSerializer instance with the app's secret key.
    """
    key = secret_key or Config.SECRET_KEY
    return URLSafeTimedSerializer(secret_key=key, salt=TOKEN_SALT)


def generate_qr_token(event_id: str, secret_key: Optional[str] = None) -> Tuple[str, int]:
    """
    Generates a cryptographically signed, timestamped token for an event.
    
    :param event_id: The unique event ID
    :param secret_key: Optional override for application secret key
    :return: Tuple of (signed_token_str: str, generated_epoch_timestamp: int)
    """
    serializer = get_serializer(secret_key)
    current_time = int(time.time())
    
    # Payload includes event ID, creation timestamp, and a random cryptographic nonce
    payload = {
        "event_id": str(event_id),
        "created_at": current_time,
        "nonce": uuid.uuid4().hex[:8]
    }
    
    token = serializer.dumps(payload)
    return token, current_time


def verify_qr_token(
    token: str,
    max_age_seconds: Optional[int] = None,
    secret_key: Optional[str] = None
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Verifies the cryptographic signature and ensures the token has not expired.

    :param token: The signed token string from the student request
    :param max_age_seconds: Expiration window (defaults to Config.QR_TOKEN_MAX_AGE_SECONDS, e.g. 25s)
    :param secret_key: Optional override for application secret key
    :return: Tuple of (is_valid: bool, payload_dict: Optional[Dict], error_message: str)
    """
    if not token or not isinstance(token, str):
        return False, None, "Missing or invalid token format."

    max_age = max_age_seconds if max_age_seconds is not None else Config.QR_TOKEN_MAX_AGE_SECONDS
    serializer = get_serializer(secret_key)

    try:
        # loads() cryptographically validates HMAC and checks timestamp against max_age
        payload = serializer.loads(token, max_age=max_age)
        return True, payload, "Token verified successfully."
    except SignatureExpired:
        return False, None, "QR code has expired. Please scan the newly refreshed QR code on the screen."
    except (BadSignature, BadTimeSignature):
        return False, None, "Invalid or tampered QR code token."
    except Exception as e:
        return False, None, f"Token verification failed: {str(e)}"
