"""MongoDB connection — optional; app runs fully in-memory without it."""
from __future__ import annotations
import os

_client = None


def get_db():
    global _client
    uri = os.getenv("MONGO_URI")
    if not uri:
        return None
    try:
        from pymongo import MongoClient  # type: ignore
        if _client is None:
            _client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        return _client[os.getenv("MONGO_DB", "campusfix")]
    except Exception:
        return None
