import os
from pathlib import Path

import pytest

os.environ.setdefault("CLEANUP_ENABLED", "false")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("PUBLIC_BASE_URL", "https://quickshare.test")
os.environ.setdefault("MAX_UPLOAD_BYTES", "2048")
os.environ.setdefault("EXPIRY_SECONDS", "600")
os.environ.setdefault("UPLOAD_RATE_LIMIT", "100")


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "data" / "quickshare.db"))
    monkeypatch.setenv("CLEANUP_ENABLED", "false")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://quickshare.test")
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "2048")
    from app import create_app

    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def upload_dir(app) -> Path:
    return Path(app.config["UPLOAD_DIR"])
