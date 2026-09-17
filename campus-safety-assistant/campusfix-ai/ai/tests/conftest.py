"""Pytest must be deterministic: force the offline engine (no quota burn)."""
import os

os.environ["CAMPUSFIX_OFFLINE"] = "1"
