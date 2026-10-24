"""Load runtime settings from environment variables."""

from __future__ import annotations

import os
from pathlib import Path


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def load_config() -> dict:
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = Path(os.getenv("DATA_DIR", str(base_dir / "data")))
    upload_dir = Path(os.getenv("UPLOAD_DIR", str(base_dir / "uploads")))
    database_path = Path(os.getenv("DATABASE_PATH", str(data_dir / "quickshare.db")))

    public_base_url = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    max_upload_bytes = _as_int("MAX_UPLOAD_BYTES", 25 * 1024 * 1024)

    return {
        "SECRET_KEY": os.getenv("SECRET_KEY", "dev-only-change-me"),
        "PUBLIC_BASE_URL": public_base_url,
        "MAX_UPLOAD_BYTES": max_upload_bytes,
        # Extra headroom for multipart wrappers around the original file.
        "MAX_CONTENT_LENGTH": max_upload_bytes + (1 * 1024 * 1024),
        "EXPIRY_SECONDS": _as_int("EXPIRY_SECONDS", 600),
        "DATA_DIR": data_dir,
        "UPLOAD_DIR": upload_dir,
        "DATABASE_PATH": database_path,
        "CLEANUP_INTERVAL_SECONDS": _as_int("CLEANUP_INTERVAL_SECONDS", 30),
        "CLEANUP_ENABLED": os.getenv("CLEANUP_ENABLED", "true").lower() not in {"0", "false", "no"},
        "UPLOAD_RATE_LIMIT": _as_int("UPLOAD_RATE_LIMIT", 20),
        "UPLOAD_RATE_WINDOW_SECONDS": _as_int("UPLOAD_RATE_WINDOW_SECONDS", 600),
    }
