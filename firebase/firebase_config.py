import os
import json
import logging
from typing import Dict, Any, List, Optional
from config import Config

logger = logging.getLogger("GeoQR.Firebase")


class MockDocumentSnapshot:
    """Simulates a Google Cloud Firestore DocumentSnapshot."""
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data) if self._data else {}


class MockDocumentReference:
    """Simulates a Google Cloud Firestore DocumentReference."""
    def __init__(self, collection_store: Dict[str, Dict[str, Any]], doc_id: str):
        self._store = collection_store
        self.id = doc_id

    def get(self) -> MockDocumentSnapshot:
        data = self._store.get(self.id)
        return MockDocumentSnapshot(self.id, data)

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        if merge and self.id in self._store:
            self._store[self.id].update(data)
        else:
            self._store[self.id] = dict(data)

    def update(self, data: Dict[str, Any]) -> None:
        if self.id in self._store:
            self._store[self.id].update(data)
        else:
            raise KeyError(f"Document {self.id} does not exist.")

    def delete(self) -> None:
        self._store.pop(self.id, None)


class MockQuery:
    """Simulates a Firestore Query with chained filtering."""
    def __init__(self, collection_store: Dict[str, Dict[str, Any]], filters: Optional[List[tuple]] = None):
        self._store = collection_store
        self._filters = filters or []

    def where(self, field: str, op: str, value: Any) -> "MockQuery":
        new_filters = list(self._filters)
        new_filters.append((field, op, value))
        return MockQuery(self._store, new_filters)

    def stream(self) -> List[MockDocumentSnapshot]:
        results = []
        for doc_id, doc_data in self._store.items():
            matches = True
            for field, op, val in self._filters:
                doc_val = doc_data.get(field)
                if op == "==" and doc_val != val:
                    matches = False
                    break
                elif op == "!=" and doc_val == val:
                    matches = False
                    break
                elif op == ">" and not (doc_val is not None and doc_val > val):
                    matches = False
                    break
                elif op == "<" and not (doc_val is not None and doc_val < val):
                    matches = False
                    break
            if matches:
                results.append(MockDocumentSnapshot(doc_id, doc_data))
        return results


class MockCollectionReference:
    """Simulates a Google Cloud Firestore CollectionReference."""
    def __init__(self, global_store: Dict[str, Dict[str, Dict[str, Any]]], collection_name: str):
        self._global_store = global_store
        self._collection_name = collection_name
        if collection_name not in self._global_store:
            self._global_store[collection_name] = {}
        self._store = self._global_store[collection_name]

    def document(self, doc_id: str) -> MockDocumentReference:
        return MockDocumentReference(self._store, doc_id)

    def where(self, field: str, op: str, value: Any) -> MockQuery:
        return MockQuery(self._store).where(field, op, value)

    def stream(self) -> List[MockDocumentSnapshot]:
        return [MockDocumentSnapshot(doc_id, data) for doc_id, data in self._store.items()]


class MockFirestoreClient:
    """In-memory Firestore client that mirrors the official google-cloud-firestore API."""
    def __init__(self):
        self._collections: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def collection(self, name: str) -> MockCollectionReference:
        return MockCollectionReference(self._collections, name)

    def clear(self):
        """Clears all in-memory collections (useful for unit tests)."""
        self._collections.clear()


# Built-in project fallback credentials for geoqr-ef535
_B64_CREDENTIALS = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiZ2VvcXItZWY1MzUiLAogICJwcml2YXRlX2tleV9pZCI6ICJhNzgxZmM1YzZmYmU3NGU2MjE1Njg0MzA0MjdjZjk5M2M4MmY3NjUxIiwKICAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUN2OVBnWHRJbjZ2OVMvXG5nSHhQZXE2MzBoYXV4OVo3YnQvSWd3UmRsK3FsZTlpMGZpcXo3SmRHclJTNTY3S016dzl4QlUrY3pyL1Jaa1ZSXG5tU0ZBMnpWQ0pIUHZtMmFzMGcvTXpPRzZFQjh0d2VhMzViQnA0RFlGTk5renhrSkdQYnhjTzdPOWt3RDA1OXpkXG5lVGhUNGsvbDM1Z2YzNjV0SklRMVIyK1gwZTFEdWdmc1FoWUFIcWFMbHduQ05WV1JseS8vUy8xUXE3aTNCbTI5XG5STTZDdC8vUXB2NFp3UTVJNXlVYVhjU1ZBVFc2bWhZUk5WQ1FWTzI5dGh4ejgxZWgxcGFzTEtqQ2IyR0U0RFprXG5BdWxzbElRZXB2N1JkL2FRUEI4c3N1V0tyaEdwN0R0L3VxcGNNWUdudFlCTFBlRjlaNHdEbE1KM25IaGJUdnM0XG5vOXBaSlNzVkFnTUJBQUVDZ2dFQUFKL3RPN1pYZC9CZUtGSHQrOCtscm93WEpNbDhBZEswVEtwdEZYQzg2ZUh1XG5ZT2RwbUxSMTArOUxZV0pxb0VveWRkTEYxSGpUR012U294aEVlbGtmY1hHV1ltV09kU3Y3cXlrS3RnbG5UK3V1XG4yc0lzK3J2VSswdjBGZTJDU1U3clBTT01xVWhNQnNvNUhLN2FzclJ4anRCdlBUVzdObUxxZjl1cVk3OS84TlZzXG5KZ1FZYXFubFZzRWllcnpUbEQ2cWFFV04xUG5MKzVFTk1GS0VZa2dzc0RJbW91M3NRbi9pK0hwaVJNLzNnOE9lXG5wdTdlV2lHNWs5Uzh5K0VYVDhKWEdDdzlEUm1xdlAvSVhXMGU4dTE2YUhNTGlPYXlRYXVIUDYrL2c5ck1wS3FOXG5sVFlLWldGMFNiRW1IS1dNOFg5ampHa1Y2cnE1a3kxYnpEU0VwQldCSVFLQmdRRGZyUnFnU3lieFpDaS9velJjXG5USU9aSkJBUGNkSVMwVXZaejk0ajFYWFQ5eXdEY1QwTVlWb2ZyUFpza1BKcFRPQm1jZy9KMC91MlBhalNWV1VZXG44cFZ4clA0cHZvSjVvSWhPUzloSjgxK0NkRElGN0hmVktranYvSG5TRmxUbmdIbllBT0dNSEQ1RitFdEc4djBNXG5OcWtURjRFSEZycnRrL2lrZHJxOExFS0hMUUtCZ1FESlluM09LalFmQkNZM0VFamZlTW5mOERaeER3TzFsaE90XG5lWXhKSTA3aGFJN2ZNU2dNKytsSitSL0I0aDlQQjFZOWlCTTU5WlkxUzBjUis4SnVTVTBuSko4VDcvd3pFdnZpXG5qZ1psc3M4OTVBdjVnd1NwS3NaZk8rb0pndHorYkJiTDZMRWxNMmdUMGlBZWh0RmRhVVEvNWxNbkNWNkpWdmNIXG53QzBKemZxa2lRS0JnQzVZUkpzUDF6ck80TzZNRjA1RWdFUGJ5QVFiTmthMTNQeDlhRzZPVFFLbFJSWlZnU3V1XG5oQ2pxQW9rT0kxd1VGSzdGVldZaEtSZGlnVGRMZ0U0Qi9WcjNXQlk0SmZxamUzcVZsblFFSERjQWNsanQzUXBxXG4zMy95RlIrbGh1UU1wN0pNeEc3dWJ5eTZQSWF2MUNTU3NzZUU2RFFhenBKcFJXeDJPVXpCOHVybEFvR0JBS1RmXG5qTzM0SVhudk5MWktEODlkbmJGSWdkbm9GL3BYcHo2VVQ2VWxVaFE3UFJVL3NuR0c0SVVlZjhDRk4yckZML2JxXG5iQXM4cEVCM28vVDJNRVdJbjdEWFM2SFFEYU5tL0crTUpYS25oUUkvclFvWEdQN0N0V3dNcWx3bEZuYjUyV1FSXG4yczRCRzBsMjg3THFYNGhoZ1czclROS2QyaGNJNnZBZWh3RUs4UlE1QW9HQUF6N3JRVkhhTCtXdmtkVm1nYWQvXG5oV0VlVnZMUklpZjVxaVQ0eElNM3RZUVZzeEJsUklFYnk2a3g3Q2h6OVFDUnkxZVI0dWhqRzU0ZHpQWFBIUlFjXG5tR045NTUzV3BVVWJVVDd0dUo4RlRseG9ldFF5emNJM1dHd1RwUUtFdG5WT1lBWndBNzV0bHkxNG9tZG8xUEVsXG4vc1ZrYTlvV3AvTTNmR3ZpQVp6MUltUT1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsCiAgImNsaWVudF9lbWFpbCI6ICJmaXJlYmFzZS1hZG1pbnNkay1mYnN2Y0BnZW9xci1lZjUzNS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMTc5NDMzNzU2OTYxOTQ1ODg0NTkiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2ZpcmViYXNlLWFkbWluc2RrLWZic3ZjJTQwZ2VvcXItZWY1MzUuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLAogICJ1bml2ZXJzZV9kb21haW4iOiAiZ29vZ2xlYXBpcy5jb20iCn0K"

# Global database instance and status
_db_client = None
_db_status = {
    "mode": "UNKNOWN",
    "project_id": None,
    "source": None,
    "error": None
}


def get_database_status() -> Dict[str, Any]:
    """Returns the current database connection mode and diagnostics."""
    if _db_client is None:
        get_firestore_client()
    return _db_status


def get_firestore_client():
    """
    Initializes and returns the Firestore client instance.
    Searches multiple potential credential sources in priority order:
    1. FIREBASE_CREDENTIALS_JSON (raw JSON string or Base64 in environment variables)
    2. Config.FIREBASE_CREDENTIALS_PATH (configured file path)
    3. /etc/secrets/serviceAccountKey.json (Render Secret Files default location)
    4. /etc/secrets/firebase/serviceAccountKey.json
    5. Local serviceAccountKey.json in project root or firebase/ folder
    6. _B64_CREDENTIALS (Built-in project fallback)
    7. Falls back to MockFirestoreClient with clear diagnostics.
    """
    global _db_client, _db_status
    if _db_client is not None:
        return _db_client

    import firebase_admin
    from firebase_admin import credentials, firestore
    import base64

    # 1. Check environment variable (Raw JSON or Base64)
    credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if credentials_json:
        try:
            raw_str = credentials_json.strip()
            if raw_str.startswith("{"):
                cred_dict = json.loads(raw_str)
            else:
                decoded = base64.b64decode(raw_str).decode("utf-8")
                cred_dict = json.loads(decoded)

            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)

            _db_client = firestore.client()
            project_id = cred_dict.get("project_id", "Unknown")
            _db_status = {
                "mode": "LIVE_FIREBASE",
                "project_id": project_id,
                "source": "FIREBASE_CREDENTIALS_JSON environment variable"
            }
            print(f"[FIREBASE] Connected to Live Firebase Firestore (Project: '{project_id}') via env variable.")
            return _db_client
        except Exception as e:
            err_msg = f"Failed to initialize Firebase from environment variable: {e}"
            print(f"[WARNING] {err_msg}")
            _db_status["error"] = err_msg

    # 2. Check candidate file paths
    candidate_paths = [
        Config.FIREBASE_CREDENTIALS_PATH,
        "/etc/secrets/serviceAccountKey.json",
        "/etc/secrets/firebase/serviceAccountKey.json",
        os.path.join(os.getcwd(), "firebase", "serviceAccountKey.json"),
        os.path.join(os.getcwd(), "serviceAccountKey.json"),
    ]

    for path in candidate_paths:
        if path and os.path.exists(path):
            try:
                if not firebase_admin._apps:
                    cred = credentials.Certificate(path)
                    firebase_admin.initialize_app(cred)

                _db_client = firestore.client()
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        file_data = json.load(f)
                        project_id = file_data.get("project_id", "Unknown")
                except Exception:
                    project_id = "Unknown"

                _db_status = {
                    "mode": "LIVE_FIREBASE",
                    "project_id": project_id,
                    "source": f"File at '{path}'"
                }
                print(f"[FIREBASE] Connected to Live Firebase Firestore via '{path}' (Project: '{project_id}')")
                return _db_client
            except Exception as e:
                err_msg = f"Failed to connect to Firebase via '{path}': {e}"
                print(f"[WARNING] {err_msg}")
                _db_status["error"] = err_msg

    # 3. Use built-in Base64 credentials fallback
    try:
        cred_dict = json.loads(base64.b64decode(_B64_CREDENTIALS).decode("utf-8"))
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)

        _db_client = firestore.client()
        _db_status = {
            "mode": "LIVE_FIREBASE",
            "project_id": cred_dict.get("project_id"),
            "source": "Built-in project credentials (geoqr-ef535)"
        }
        print(f"[FIREBASE] Connected to Live Firebase Firestore (Project: '{cred_dict.get('project_id')}') via built-in credentials.")
        return _db_client
    except Exception as e:
        err_msg = f"Failed to connect to Firebase via built-in credentials: {e}"
        print(f"[WARNING] {err_msg}")
        _db_status["error"] = err_msg

    # Fallback to In-Memory Emulator
    _db_status = {
        "mode": "IN_MEMORY_EMULATOR",
        "project_id": "local-emulator",
        "source": "In-Memory fallback (No valid credentials detected)",
        "error": _db_status.get("error")
    }
    print("[INFO] Firebase credentials not found or unreadable. Using In-Memory Firestore Emulator.")
    _db_client = MockFirestoreClient()
    return _db_client
