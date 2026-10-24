from datetime import timedelta
from io import BytesIO

from app.cleanup import cleanup_expired
from app.db import get_share, to_iso, utc_now


def upload(client, name="notes.pdf", data=b"%PDF-1.4 demo", content_type="application/pdf"):
    return client.post(
        "/api/upload",
        data={"file": (BytesIO(data), name)},
        content_type="multipart/form-data",
    )


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_upload_pdf_and_download(client, app):
    response = upload(client, "report.pdf", b"%PDF-1.4 hello")
    assert response.status_code == 201
    payload = response.json
    assert payload["filename"] == "report.pdf"
    assert payload["share_url"].startswith("https://quickshare.test/share/")
    assert "localhost" not in payload["share_url"]

    token = payload["token"]
    page = client.get(f"/share/{token}")
    assert page.status_code == 200
    assert b"report.pdf" in page.data

    download = client.get(f"/download/{token}")
    assert download.status_code == 200
    assert download.data == b"%PDF-1.4 hello"
    assert "attachment" in download.headers.get("Content-Disposition", "")


def test_upload_image(client):
    response = upload(client, "photo.png", b"\x89PNG\r\n\x1a\n" + b"0" * 40, "image/png")
    assert response.status_code == 201
    assert response.json["filename"] == "photo.png"


def test_upload_small_video(client):
    response = upload(client, "clip.mp4", b"\x00\x00\x00\x18ftypmp42" + b"1" * 80, "video/mp4")
    assert response.status_code == 201
    assert response.json["filename"] == "clip.mp4"


def test_reject_empty_file(client):
    response = upload(client, "empty.txt", b"")
    assert response.status_code == 400
    assert "Empty" in response.json["error"]


def test_reject_oversize_file(client):
    response = upload(client, "huge.bin", b"x" * 3000)
    assert response.status_code == 413


def test_qr_code_is_png_and_not_localhost(client):
    payload = upload(client).json
    qr = client.get(payload["qr_url"])
    assert qr.status_code == 200
    assert qr.data.startswith(b"\x89PNG")
    assert payload["share_url"] == f"https://quickshare.test/share/{payload['token']}"


def test_invalid_token_is_rejected(client):
    response = client.get("/share/does-not-exist")
    assert response.status_code == 410
    assert b"This Link Has Expired" in response.data
    download = client.get("/download/does-not-exist")
    assert download.status_code == 410


def test_expired_link_is_rejected_before_cleanup(client, app):
    payload = upload(client).json
    token = payload["token"]
    connection = app.config["DB"]
    expired_at = to_iso(utc_now() - timedelta(seconds=1))
    connection.execute("UPDATE shares SET expires_at = ? WHERE token = ?", (expired_at, token))
    connection.commit()

    assert client.get(f"/api/share/{token}").status_code == 410
    assert client.get(f"/download/{token}").status_code == 410
    assert client.get(f"/qr/{token}").status_code == 410
    stored = get_share(connection, token)
    assert stored is not None  # cleanup has not run, but access is already blocked


def test_cleanup_deletes_expired_files(client, app, upload_dir):
    payload = upload(client).json
    token = payload["token"]
    row = get_share(app.config["DB"], token)
    stored_path = upload_dir / row["stored_name"]
    assert stored_path.is_file()

    expired_at = to_iso(utc_now() - timedelta(seconds=1))
    app.config["DB"].execute("UPDATE shares SET expires_at = ? WHERE token = ?", (expired_at, token))
    app.config["DB"].commit()

    removed = cleanup_expired(app)
    assert removed == 1
    assert get_share(app.config["DB"], token) is None
    assert not stored_path.exists()


def test_duplicate_filenames_do_not_overwrite(client, app, upload_dir):
    first = upload(client, "same.txt", b"alpha").json
    second = upload(client, "same.txt", b"bravo").json
    assert first["token"] != second["token"]

    row_one = get_share(app.config["DB"], first["token"])
    row_two = get_share(app.config["DB"], second["token"])
    assert row_one["stored_name"] != row_two["stored_name"]
    assert (upload_dir / row_one["stored_name"]).read_bytes() == b"alpha"
    assert (upload_dir / row_two["stored_name"]).read_bytes() == b"bravo"


def test_missing_file_is_handled(client, app, upload_dir):
    payload = upload(client).json
    row = get_share(app.config["DB"], payload["token"])
    (upload_dir / row["stored_name"]).unlink()
    response = client.get(f"/download/{payload['token']}")
    assert response.status_code == 410


def test_home_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Your Files. One Scan Away." in response.data
    assert b"Upload &amp; Generate QR" in response.data
