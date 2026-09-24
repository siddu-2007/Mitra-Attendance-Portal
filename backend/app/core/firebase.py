import json
import os
from typing import Any, Dict, List, Optional, Tuple
import firebase_admin
from firebase_admin import auth, credentials, firestore
from app.core.config import settings
from app.core.logging import logger

_firebase_app: Optional[firebase_admin.App] = None
_firestore_client: Any = None
_is_mock_mode: bool = False

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
LOCAL_DB_FILE = os.path.join(DATA_DIR, "local_firestore.json")


# -----------------------------------------------------------------------------
# Local File-Backed Mock Firestore for Local Dev / Testing
# -----------------------------------------------------------------------------
class MockDocumentSnapshot:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]], exists: bool = True):
        self.id = doc_id
        self._data = data or {}
        self.exists = exists

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)


class MockDocumentReference:
    def __init__(self, collection_store: Dict[str, Dict[str, Any]], doc_id: str, on_change: Optional[Any] = None):
        self._collection_store = collection_store
        self.id = doc_id
        self._on_change = on_change

    def get(self) -> MockDocumentSnapshot:
        if self.id in self._collection_store:
            return MockDocumentSnapshot(self.id, self._collection_store[self.id], exists=True)
        return MockDocumentSnapshot(self.id, None, exists=False)

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        if merge and self.id in self._collection_store:
            self._collection_store[self.id].update(data)
        else:
            self._collection_store[self.id] = dict(data)
        if self._on_change:
            self._on_change()

    def update(self, data: Dict[str, Any]) -> None:
        if self.id not in self._collection_store:
            raise KeyError(f"Document {self.id} does not exist.")
        self._collection_store[self.id].update(data)
        if self._on_change:
            self._on_change()

    def delete(self) -> None:
        if self.id in self._collection_store:
            del self._collection_store[self.id]
        if self._on_change:
            self._on_change()


class MockQuery:
    def __init__(self, collection_store: Dict[str, Dict[str, Any]], filters: Optional[List[Tuple[str, str, Any]]] = None):
        self._collection_store = collection_store
        self._filters: List[Tuple[str, str, Any]] = filters or []
        self._order_by: Optional[Tuple[str, str]] = None
        self._limit: Optional[int] = None

    def where(self, field: str, op: str, value: Any) -> "MockQuery":
        new_filters = list(self._filters)
        new_filters.append((field, op, value))
        q = MockQuery(self._collection_store, new_filters)
        q._order_by = self._order_by
        q._limit = self._limit
        return q

    def order_by(self, field: str, direction: str = "ASCENDING") -> "MockQuery":
        self._order_by = (field, direction)
        return self

    def limit(self, count: int) -> "MockQuery":
        self._limit = count
        return self

    def stream(self) -> List[MockDocumentSnapshot]:
        results: List[MockDocumentSnapshot] = []
        for doc_id, doc_data in list(self._collection_store.items()):
            match = True
            for field, op, val in self._filters:
                actual_val = doc_data.get(field)
                if op == "==":
                    if actual_val != val:
                        match = False
                        break
                elif op == ">=":
                    if actual_val is None or actual_val < val:
                        match = False
                        break
                elif op == "<=":
                    if actual_val is None or actual_val > val:
                        match = False
                        break
                elif op == "in":
                    if actual_val not in val:
                        match = False
                        break
                elif op == "array_contains":
                    if not isinstance(actual_val, list) or val not in actual_val:
                        match = False
                        break
            if match:
                results.append(MockDocumentSnapshot(doc_id, doc_data, exists=True))

        if self._order_by:
            field, direction = self._order_by
            reverse = direction.upper() in ("DESCENDING", "DESC")
            results.sort(key=lambda d: d.to_dict().get(field, ""), reverse=reverse)

        if self._limit is not None:
            results = results[: self._limit]

        return results


class MockCollectionReference(MockQuery):
    def __init__(self, db_store: Dict[str, Dict[str, Dict[str, Any]]], name: str, on_change: Optional[Any] = None):
        if name not in db_store:
            db_store[name] = {}
        self._db_store = db_store
        self._name = name
        self._on_change = on_change
        super().__init__(db_store[name])

    def document(self, doc_id: Optional[str] = None) -> MockDocumentReference:
        if not doc_id:
            import uuid
            doc_id = str(uuid.uuid4())
        return MockDocumentReference(self._db_store[self._name], doc_id, on_change=self._on_change)


class MockWriteBatch:
    def __init__(self, on_commit: Optional[Any] = None):
        self._operations: List[tuple] = []
        self._on_commit = on_commit

    def set(self, doc_ref: MockDocumentReference, data: Dict[str, Any], merge: bool = False):
        self._operations.append(("set", doc_ref, data, merge))

    def update(self, doc_ref: MockDocumentReference, data: Dict[str, Any]):
        self._operations.append(("update", doc_ref, data))

    def delete(self, doc_ref: MockDocumentReference):
        self._operations.append(("delete", doc_ref))

    def commit(self) -> None:
        for op in self._operations:
            if op[0] == "set":
                op[1].set(op[2], merge=op[3])
            elif op[0] == "update":
                op[1].update(op[2])
            elif op[0] == "delete":
                op[1].delete()
        self._operations.clear()
        if self._on_commit:
            self._on_commit()


class MockFirestoreClient:
    def __init__(self, persist_to_disk: bool = True):
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._persist_to_disk = persist_to_disk
        if self._persist_to_disk:
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load persisted mock collections from disk if available."""
        if os.path.exists(LOCAL_DB_FILE):
            try:
                with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._store = data
                        logger.info(f"Loaded persistent mock database from {LOCAL_DB_FILE}")
            except Exception as e:
                logger.warning(f"Could not load local database file: {e}")

    def save_to_disk(self) -> None:
        """Write current database state to JSON file on disk."""
        if not self._persist_to_disk:
            return
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self._store, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist database to disk: {e}")

    def collection(self, name: str) -> MockCollectionReference:
        return MockCollectionReference(self._store, name, on_change=self.save_to_disk)

    def batch(self) -> MockWriteBatch:
        return MockWriteBatch(on_commit=self.save_to_disk)

    def clear(self):
        """Reset mock database in-memory (does not overwrite disk)."""
        self._store.clear()


def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK or initialize mock client if credentials are absent."""
    global _firebase_app, _firestore_client, _is_mock_mode

    # If already initialized, return
    if _firestore_client is not None:
        return

    # Check for credentials in settings or environment
    has_env_credentials = bool(
        settings.FIREBASE_PROJECT_ID
        and settings.FIREBASE_CLIENT_EMAIL
        and settings.clean_private_key
        and not settings.FIREBASE_PROJECT_ID.startswith("your_")
    )
    has_file_credentials = bool(
        settings.GOOGLE_APPLICATION_CREDENTIALS
        and os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS)
    )

    if has_env_credentials:
        try:
            cred_dict = {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key": settings.clean_private_key,
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            _firestore_client = firestore.client()
            _is_mock_mode = False
            logger.info(f"Firebase Admin SDK initialized successfully with project: {settings.FIREBASE_PROJECT_ID}")
            return
        except Exception as e:
            logger.warning(f"Failed to initialize Firebase Admin with env credentials: {e}. Falling back to mock client.")

    elif has_file_credentials:
        try:
            cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
            _firebase_app = firebase_admin.initialize_app(cred)
            _firestore_client = firestore.client()
            _is_mock_mode = False
            logger.info("Firebase Admin SDK initialized successfully via file credentials.")
            return
        except Exception as e:
            logger.warning(f"Failed to initialize Firebase Admin with file credentials: {e}. Falling back to mock client.")

    # Fallback to in-memory mock client
    logger.info("No live Firebase credentials detected. Operating in mock/test mode for local development.")
    _firestore_client = MockFirestoreClient()
    _is_mock_mode = True


def get_db():
    """Dependency / accessor for Firestore client."""
    global _firestore_client
    if _firestore_client is None:
        initialize_firebase()
    return _firestore_client


def is_mock_mode() -> bool:
    """Check if Firebase is currently running in mock mode."""
    global _is_mock_mode
    return _is_mock_mode


def verify_firebase_id_token(token: str) -> Dict[str, Any]:
    """Verify Firebase ID token via Firebase Admin or mock decoder in mock mode."""
    if is_mock_mode():
        if token.startswith("mock-token:"):
            parts = token.split(":")
            # Format: mock-token:uid:email:role:name
            uid = parts[1] if len(parts) > 1 else "mock_admin_123"
            email = parts[2] if len(parts) > 2 else f"{uid}@mithra.vit.ac.in"
            role = parts[3] if len(parts) > 3 else ("STUDENT" if uid.startswith("VM") else "ADMIN")
            name = parts[4] if len(parts) > 4 else ("Student Member" if role == "STUDENT" else "Mock Administrator")
            return {"uid": uid, "email": email, "role": role, "name": name}
        return {"uid": "mock_admin_123", "email": "admin@mithra.vit.ac.in", "role": "ADMIN", "name": "VIT Mithra Admin"}

    # Production Firebase Admin verification
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as exc:
        logger.warning(f"Token verification failed: {exc}")
        raise ValueError("Invalid or expired Firebase ID token.") from exc
