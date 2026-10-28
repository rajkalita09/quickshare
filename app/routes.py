"""HTTP routes for upload, share, download, and QR."""




from __future__ import annotations

from datetime import timedelta
from io import BytesIO

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)
from werkzeug.exceptions import RequestEntityTooLarge


import secrets
import string

from app.cleanup import cleanup_expired
from app.db import (
    from_iso,
    get_share,
    get_share_by_code,
    insert_share,
    utc_now,
)
from app.qrcode_util import make_qr_png
from app.storage import delete_file, sanitize_download_name, save_upload, stored_path

bp = Blueprint("main", __name__)

CODE_ALPHABET = string.ascii_uppercase + string.digits
CODE_LENGTH = 6


def _new_transfer_code() -> str:
    connection = current_app.config["DB"]

    # Retry in the extremely unlikely event of a collision.
    for _ in range(20):
        code = "".join(
            secrets.choice(CODE_ALPHABET)
            for _ in range(CODE_LENGTH)
        )
        existing = get_share_by_code(connection, code)
        if existing is None:
            return code

    raise RuntimeError("Could not generate a unique transfer code.")


def _public_share_url(token: str) -> str:
    return f"{current_app.config['PUBLIC_BASE_URL']}/share/{token}"


def _share_is_expired(row) -> bool:
    return utc_now() >= from_iso(row["expires_at"])


def _public_share_payload(row) -> dict:
    token = row["token"]
    return {
        "token": token,
        "filename": row["original_name"],
        "size": row["file_size"],
        "created_at": row["created_at"],
        "expires_at": row["expires_at"],
        "transfer_code": row["transfer_code"],
        "share_url": _public_share_url(token),
        "download_url": f"/download/{token}",
        "qr_url": f"/qr/{token}",
        "expiry_seconds": current_app.config["EXPIRY_SECONDS"],
    }


def _format_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            rounded = round(size, 1)
            if abs(rounded - int(rounded)) < 0.05:
                return f"{int(round(rounded))} {unit}"
            return f"{rounded:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


@bp.get("/")
def index():
    return render_template(
        "index.html",
        max_upload_bytes=current_app.config["MAX_UPLOAD_BYTES"],
        expiry_seconds=current_app.config["EXPIRY_SECONDS"],
    )


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "quickshare"})


@bp.get("/api/config")
def api_config():
    return jsonify(
        {
            "max_upload_bytes": current_app.config["MAX_UPLOAD_BYTES"],
            "expiry_seconds": current_app.config["EXPIRY_SECONDS"],
        }
    )


@bp.post("/api/upload")
def api_upload():
    limiter = current_app.config["RATE_LIMITER"]
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
    client_ip = client_ip.split(",")[0].strip()
    if not limiter.allow(f"upload:{client_ip}"):
        return jsonify({"error": "Too many uploads from this address. Please wait and try again."}), 429

    uploaded = request.files.get("file")
    if uploaded is None or uploaded.filename is None or uploaded.filename.strip() == "":
        return jsonify({"error": "Please choose a file to upload."}), 400

    uploaded.stream.seek(0, 2)
    incoming_size = uploaded.stream.tell()
    uploaded.stream.seek(0)

    if incoming_size <= 0:
        return jsonify({"error": "Empty files are not allowed."}), 400

    max_bytes = current_app.config["MAX_UPLOAD_BYTES"]
    if incoming_size > max_bytes:
        return jsonify({"error": f"File is too large. Maximum size is {_format_size(max_bytes)}."}), 413

    original_name = sanitize_download_name(uploaded.filename)
    stored_name = None
    try:
        stored_name, stored_size = save_upload(current_app.config["UPLOAD_DIR"], uploaded)
        if stored_size <= 0:
            delete_file(current_app.config["UPLOAD_DIR"], stored_name)
            return jsonify({"error": "Empty files are not allowed."}), 400
        if stored_size > max_bytes:
            delete_file(current_app.config["UPLOAD_DIR"], stored_name)
            return jsonify({"error": f"File is too large. Maximum size is {_format_size(max_bytes)}."}), 413

        created_at = utc_now()
        expires_at = created_at + timedelta(seconds=current_app.config["EXPIRY_SECONDS"])
        token = current_app.config["TOKEN_FACTORY"]()
        transfer_code = _new_transfer_code()
        insert_share(
            current_app.config["DB"],
            token=token,
            stored_name=stored_name,
            original_name=original_name,
            file_size=stored_size,
            created_at=created_at,
            expires_at=expires_at,
            transfer_code=transfer_code
        )
        
        row = get_share(current_app.config["DB"], token)
        return jsonify(_public_share_payload(row)), 201
    except Exception:
        current_app.logger.exception("Upload failed")
        if stored_name:
            delete_file(current_app.config["UPLOAD_DIR"], stored_name)
        return jsonify({"error": "Upload failed. Please try again."}), 500


@bp.get("/share/<token>")
def share_page(token: str):
    row = get_share(current_app.config["DB"], token)
    if row is None or _share_is_expired(row):
        return render_template("expired.html"), 410

    payload = _public_share_payload(row)
    return render_template(
        "share.html",
        share=payload,
        file_size_label=_format_size(row["file_size"]),
    )


@bp.get("/api/share/<token>")
def api_share(token: str):
    row = get_share(current_app.config["DB"], token)
    if row is None or _share_is_expired(row):
        return jsonify({"error": "This link has expired or is invalid."}), 410
    path = stored_path(current_app.config["UPLOAD_DIR"], row["stored_name"])
    if not path.is_file():
        return jsonify({"error": "This file is no longer available."}), 410
    return jsonify(_public_share_payload(row))


@bp.post("/api/receive-code")
def api_receive_code():
    limiter = current_app.config["CODE_LOOKUP_RATE_LIMITER"]

    client_ip = request.headers.get(
        "X-Forwarded-For",
        request.remote_addr or "unknown",
    ).split(",")[0].strip()

    if not limiter.allow(f"code-lookup:{client_ip}"):
        return jsonify({
            "error": "Too many attempts. Please wait and try again."
        }), 429

    body = request.get_json(silent=True) or {}
    code = body.get("code", "")

    if not isinstance(code, str):
        code = ""

    code = code.strip().upper()

    if (
        len(code) != CODE_LENGTH
        or any(character not in CODE_ALPHABET for character in code)
    ):
        return jsonify({
            "error": "This code is invalid or has expired."
        }), 404

    row = get_share_by_code(current_app.config["DB"], code)

    if row is None or _share_is_expired(row):
        return jsonify({
            "error": "This code is invalid or has expired."
        }), 404

    path = stored_path(current_app.config["UPLOAD_DIR"], row["stored_name"])

    if not path.is_file():
        return jsonify({
            "error": "This code is invalid or has expired."
        }), 404

    return jsonify({
        "filename": row["original_name"],
        "size": row["file_size"],
        "expires_at": row["expires_at"],
        "download_url": f"/download/{row['token']}",
    })


@bp.post("/api/receive-code/download")
def api_receive_code_download():
    body = request.get_json(silent=True) or {}
    code = body.get("code", "")

    if not isinstance(code, str):
        code = ""

    code = code.strip().upper()

    if (
        len(code) != CODE_LENGTH
        or any(character not in CODE_ALPHABET for character in code)
    ):
        return jsonify({
            "error": "This code is invalid or has expired."
        }), 404

    row = get_share_by_code(current_app.config["DB"], code)

    if row is None or _share_is_expired(row):
        return jsonify({
            "error": "This code is invalid or has expired."
        }), 404

    path = stored_path(current_app.config["UPLOAD_DIR"], row["stored_name"])

    if not path.is_file():
        return jsonify({
            "error": "This code is invalid or has expired."
        }), 404

    return send_file(
        path,
        as_attachment=True,
        download_name=row["original_name"],
        max_age=0,
    )


@bp.get("/download/<token>")
def download(token: str):
    row = get_share(current_app.config["DB"], token)
    if row is None or _share_is_expired(row):
        if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
            return render_template("expired.html"), 410
        return jsonify({"error": "This link has expired or is invalid."}), 410

    path = stored_path(current_app.config["UPLOAD_DIR"], row["stored_name"])
    if not path.is_file():
        return render_template("expired.html"), 410

    return send_from_directory(
        directory=current_app.config["UPLOAD_DIR"],
        path=row["stored_name"],
        as_attachment=True,
        download_name=row["original_name"],
        max_age=0,
    )


@bp.get("/qr/<token>")
def qr_image(token: str):
    row = get_share(current_app.config["DB"], token)
    if row is None or _share_is_expired(row):
        return jsonify({"error": "This link has expired or is invalid."}), 410

    png = make_qr_png(_public_share_url(token))
    return send_file(
        path_or_file=BytesIO(png),
        mimetype="image/png",
        download_name=f"quickshare-{token[:8]}.png",
        max_age=0,
        as_attachment=False,
    )


@bp.errorhandler(RequestEntityTooLarge)
def too_large(_error):
    max_bytes = current_app.config["MAX_UPLOAD_BYTES"]
    return jsonify({"error": f"File is too large. Maximum size is {_format_size(max_bytes)}."}), 413


@bp.get("/internal/cleanup")
def run_cleanup_now():
    """Used by tests. Disabled unless TESTING is on."""
    if not current_app.config.get("TESTING"):
        return jsonify({"error": "Not found"}), 404
    removed = cleanup_expired(current_app)
    return jsonify({"removed": removed})
