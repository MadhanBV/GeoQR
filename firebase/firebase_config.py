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


# Global database instance
_db_client = None


def get_firestore_client():
    """
    Initializes and returns the Firestore client instance.
    If a valid serviceAccountKey.json is found, connects to live Google Firebase Firestore.
    Otherwise, automatically falls back to MockFirestoreClient for local development/testing.
    """
    global _db_client
    if _db_client is not None:
        return _db_client

    credentials_path = Config.FIREBASE_CREDENTIALS_PATH
    credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if credentials_json:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                cred_dict = json.loads(credentials_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)

            _db_client = firestore.client()
            print("[FIREBASE] Connected to Live Firebase Firestore via environment variable.")
            return _db_client
        except Exception as e:
            print(f"[WARNING] Failed to connect to Firebase via environment variable: {e}")

    if os.path.exists(credentials_path):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)

            _db_client = firestore.client()
            print(f"[FIREBASE] Connected to Live Firebase Firestore via '{credentials_path}'")
            return _db_client
        except Exception as e:
            print(f"[WARNING] Failed to connect to Live Firebase: {e}. Falling back to In-Memory Firestore.")
    else:
        print(f"[INFO] Firebase credentials not found at '{credentials_path}'.")
        print("[INFO] Using In-Memory Firestore Emulator (All features active for local testing).")

    _db_client = MockFirestoreClient()
    return _db_client
