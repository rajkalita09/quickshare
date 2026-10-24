"""Background job that deletes expired files and database rows."""

from __future__ import annotations

import logging
import threading
import time

from flask import Flask

from app.db import delete_share, list_expired, utc_now
from app.storage import delete_file

logger = logging.getLogger(__name__)


def cleanup_expired(app: Flask) -> int:
    """Remove expired shares. Safe to run from multiple workers."""
    removed = 0
    connection = app.config["DB"]
    upload_dir = app.config["UPLOAD_DIR"]
    expired = list_expired(connection, utc_now())
    for row in expired:
        delete_file(upload_dir, row["stored_name"])
        delete_share(connection, row["token"])
        removed += 1
    if removed:
        logger.info("Removed %s expired share(s)", removed)
    return removed


def start_cleanup_thread(app: Flask) -> None:
    if not app.config["CLEANUP_ENABLED"]:
        return

    interval = max(5, int(app.config["CLEANUP_INTERVAL_SECONDS"]))

    def loop() -> None:
        # First pass shortly after startup, then on a regular interval.
        time.sleep(2)
        while True:
            try:
                with app.app_context():
                    cleanup_expired(app)
            except Exception:
                logger.exception("Expired-file cleanup failed")
            time.sleep(interval)

    thread = threading.Thread(target=loop, name="quickshare-cleanup", daemon=True)
    thread.start()
