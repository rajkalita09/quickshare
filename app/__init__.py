"""QuickShare Flask application factory."""

from __future__ import annotations

import logging
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from app.cleanup import start_cleanup_thread
from app.config import load_config
from app.db import connect, init_db
from app.ratelimit import RateLimiter
from app.routes import bp
from app.storage import ensure_upload_dir


def create_app() -> Flask:
    load_dotenv()
    settings = load_config()

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )
    app.config.update(settings)
    app.config["TOKEN_FACTORY"] = secrets.token_urlsafe

    logging.basicConfig(level=logging.INFO)

    Path(app.config["DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    ensure_upload_dir(Path(app.config["UPLOAD_DIR"]))

    connection = connect(Path(app.config["DATABASE_PATH"]))
    init_db(connection)
    app.config["DB"] = connection
    app.config["RATE_LIMITER"] = RateLimiter(
        limit=app.config["UPLOAD_RATE_LIMIT"],
        window_seconds=app.config["UPLOAD_RATE_WINDOW_SECONDS"],
    )
    app.config["CODE_LOOKUP_RATE_LIMITER"] = RateLimiter(
    limit=10,
    window_seconds=600,
)

    app.register_blueprint(bp)

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        max_bytes = app.config["MAX_UPLOAD_BYTES"]
        mb = max_bytes / (1024 * 1024)
        return jsonify({"error": f"File is too large. Maximum size is {mb:.0f} MB."}), 413

    start_cleanup_thread(app)
    return app
