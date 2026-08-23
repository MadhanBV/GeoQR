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
_B64_CREDENTIALS = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiZ2VvcXIyIiwKICAicHJpdmF0ZV9rZXlfaWQiOiAiOTc3ZTY5NmRjMDRiODczZTYzOGUzNGMwY2M0NThlODc4ZTYyMzdjNiIsCiAgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZRSUJBREFOQmdrcWhraUc5dzBCQVFFRkFBU0NCS2N3Z2dTakFnRUFBb0lCQVFEQjlUNEY4YWszWU1paVxuME9wU1dWU1hiNmpXaFpuMHlzZzhhRlVEM1RuNjVkc004N0dCZlN1UmNVNTF5TnZVQXplV05DNVhSTTJ3R3pzc1xuZGx5Q1BGOVRsd2pMdUZCQ2Z3ZFpXMEIrcGVGTTk3NDhWZ1F6TFlrMGU4QlBzNFVqZ0czYWh0R3VBVXNONHE5U1xuTnREZG15bFllN05NeVRwdnQ1U1FFQlNZWkNUZFJGazFsU2FYUyt6L3lGVmt4QVZxcFRVVG94RjdBNTFvOTJPelxubXRrTyt1cjl6ekJYd2VmTFgyYzR1KzNhNklUY09TZVMvamNXd0s4VHVhYzhmK1loNnBNeVJKZHZoWTREck5mblxuQllnSXh3c01IcngvNk9LbHZPamVqQ2g0S3F6eStrODJEU3lEbDhKTXphc3lvRld5UC9NeG16S25zN09RYUNaR1xubG1ObGh5ZkxBZ01CQUFFQ2dnRUFCU2srSi9kVndVajhoQ3NCTDU3SXRWemtMSTBzSitUbEZJalNsazg4YU5TaVxuWHcvMVoxU1cxN09nMnNBYmE4bFU3ZFRHb2JRTmZsRGN5U0tZd1dJR2V2TUxOcEx6RnYwVzhkOTJDNVYrbS9wblxuUm1jajgwVVVPZUJsaDcvTnFVQjY2OXJPV1BSK2RFaWlua1dJaWtoRHkzeDJYOWt6Vnl5d1MyL2dnVGhta2xLdFxuUmFtVU9RZ3ZNN0VKc0VDSEVXZlZoT203Q0lNN2UvSUxPU05MM2hGcXNPOHJoeTkvYkZJZlNYR2VuNGs4SW9qMVxuL3FyaWZkSkxIYi90L0U0bDNtYXFsTkZUb1RlY2lZaTY5eUxrNkowSUZOVFhLV1FoZlNsRUMyeDZLTTdLYW9NL1xuQzF4SEV6QUVzR2wyQnd1UEE0VlUyOWhPYTJCdlZ2cERGdTV5Q1hRcWRRS0JnUUR5c25rek1HeUp3UXhyQmhKZVxuMmdPTlRKQTRjdUNmNGRLTXNQVjZLZWtJWnJTTHpuVzBoLzNlejRncGpScjdPYTUxYytoZkEyRVltUk5iU3VISFxuTHdmbndRRzAyMjE3ZWVPWitENXM0TnpmaTFQNzlKUEV0cnJsRERRMDJJbjJpcmN5WFMzVVY3MXEwaGpUYVZzcVxuR2VvZGtuZWFrNjd3dEhMeTIyK3d5bnBMTHdLQmdRRE1sdHhRK0FvZGpKYnM3UGUyejRFbW1vcnIyRWtvZSt5cVxuUk9oUFBKdURnSWhHekVyTjdSMjluWVVWTGwxeWlJOHJNaHoveE05RUNBWUEzZE1QVW9UUFhiaXJHT2tIMExrdVxucjNTT0oraW9uN3ZTNTJ0ckd5K1VlalFFbzdzUzUyRXJIV2l1MFBUNVpIV1JRNG92ajhVMmNCLzg4ZmZpZG4yOVxuOEFNcHBNL1dKUUtCZ0FSS3diZjFDRVpiWXFQVjVLZEd4YjlPOWxINVBoMjF1YXFCU3FZUmJheVhYR1FJajY1VVxucFZtMlk5c1FRc1RrblVBNGY0aUduOFgybHhBTFAvanN6UC85T3RGKysrMnVGeWRXNjR1ellsU1Z1ek4rZk1xQ1xuek1WV05Pb21WakpFKzc1cFJYRTI2QU9tbVlmTG1qQWhhekdBc0pyTU45REw4Q2g1VnYxU1oxMURBb0dCQUxsS1xuYkpFY2hEVE03cWYzMmtZRVd3ajJjSmszVXRMS29jWjRFQm9yWHdGVGVKaitUMFYvMmk2d0tpYkx6akI4QTRad1xucFpqenkyL25BR0RxaGt2YlJaTjFZMW42ZnByb2E3OGZneVY0ZVp1MngybzAwN0cyZG5vM3owTGdjdjZrOWZrUlxuY296WmpQVU9DZmlkUGRyamtBNUVzSVByTmNFeDVhSVBiUjNiT2F6TkFvR0FHZnZNRXk1ZmdaT3Bscy93SUw3clxuSE5nWVJRZ3dKRlBnNDBmUkliV0U0SEZCTlhRdnFpaGJMYkxTZ0NuTHM1TzlFSFJYZlcyQ2VaT0ZsTnYrTkIwTlxuY2JXbnVkNTM1T3ozeXUyWGN0c1k4UEkyT0hCVXNPSlFESk1KMzRtdTZmaytCU2ZOTmJLOW5FUGo5b0t2Zk9aUFxucVh5d2hVMlp3S3AxQ1FrakY5MHhNUkE9XG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLAogICJjbGllbnRfZW1haWwiOiAiZmlyZWJhc2UtYWRtaW5zZGstZmJzdmNAZ2VvcXIyLmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAiY2xpZW50X2lkIjogIjExMzI5MTI5MDY4NzY2NDQ1NzI5OCIsCiAgImF1dGhfdXJpIjogImh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwKICAidG9rZW5fdXJpIjogImh0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VuIiwKICAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsCiAgImNsaWVudF94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3JvYm90L3YxL21ldGFkYXRhL3g1MDkvZmlyZWJhc2UtYWRtaW5zZGstZmJzdmMlNDBnZW9xcjIuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLAogICJ1bml2ZXJzZV9kb21haW4iOiAiZ29vZ2xlYXBpcy5jb20iCn0K"

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
            "source": f"Built-in project credentials ({cred_dict.get('project_id')})"
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
