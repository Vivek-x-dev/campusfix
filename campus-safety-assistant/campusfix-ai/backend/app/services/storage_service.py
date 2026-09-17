"""Storage stub — swap with Cloudinary/S3; local saves keep demo offline."""
from __future__ import annotations
from pathlib import Path

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def save_upload(filename: str, data: bytes) -> str:
    safe = "".join(c for c in filename if c.isalnum() or c in "._-")[-80:] or "upload.jpg"
    dest = UPLOAD_DIR / safe
    dest.write_bytes(data)
    return str(dest)
