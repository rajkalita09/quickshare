# QuickShare

**Share Anything. Anywhere. In Seconds.**

QuickShare is a temporary file-sharing website. Upload a file, get a unique link and QR code, and let the receiver download it immediately. Every share expires **10 minutes** after the upload finishes. After expiry the server refuses access and a background job deletes the file.

This is a student mini project for AWS Cloud Computing and Docker. It is a working MVP, not a production security audit.

Expiry means the **server stops granting access**. It cannot erase a copy the receiver already saved.

## Features

- Drag-and-drop or click-to-browse single-file upload
- Unique, unguessable sharing token
- QR code for the full public URL
- Automatic download on the receiver page, plus a fallback button
- Live MM:SS countdown after the server confirms the upload
- Immediate rejection of expired links, even before cleanup runs
- Automatic deletion of expired files and database rows
- Persistent storage that survives container restarts

## Architecture

```
Sender browser
    POST /api/upload
        → save file under a random name in uploads/
        → insert metadata in SQLite (UTC created_at + expires_at)
        → return share URL, QR URL, expiry
Receiver browser
    GET /share/<token>     receiver page (410 if expired)
    GET /download/<token>  attachment download (re-checks expiry)
    GET /qr/<token>        PNG of PUBLIC_BASE_URL/share/<token>
Background thread
    every 30 seconds, delete expired files + rows
```

`PUBLIC_BASE_URL` is an environment variable so local QR codes use `http://127.0.0.1:5000` and AWS QR codes use your EC2 public URL.

Default limits: **25 MB** max file size, **10 minute** lifetime, **20 uploads / 10 minutes / IP**.

## Project layout

```
app/                Flask app, database, storage, cleanup, QR
templates/          Home, receiver, and expired pages
static/             CSS, JavaScript, favicon
tests/              Automated checks for upload, expiry, download
docs/               AWS guide and presentation outline
Dockerfile          Gunicorn image
docker-compose.yml  App + persistent volumes
run.py              Local Windows/macOS/Linux server
```

## Local setup (Windows)

Python 3.12 is enough. Docker is optional until you deploy.

```powershell
cd E:\quickshare
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

On another device on the same Wi-Fi, use your PC’s LAN IP instead of `127.0.0.1` and set `PUBLIC_BASE_URL` to that address so the QR code is reachable.

## Tests

```powershell
pytest -q
```

Covered automatically: PDF/image/video upload, empty and oversized rejection, QR PNG, invalid tokens, expiry before cleanup, cleanup deletion, duplicate filenames, missing files.

Manual demo checklist:

1. Upload a PDF, an image, and a small video under 25 MB.
2. Copy the link and scan the QR code.
3. Confirm the receiver page starts a download and that the fallback button works.
4. Wait until expiry (or set `EXPIRY_SECONDS=60` for a faster demo).
5. Confirm the old link shows **This Link Has Expired**.
6. Restart the process and confirm an unexpired file still downloads.

## Docker

Install Docker Desktop first, then:

```powershell
copy .env.example .env
# Set PUBLIC_BASE_URL=http://127.0.0.1:8000 in .env
docker compose up --build
```

App: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Host folders `./data` and `./uploads` are mounted into the container. Recreating the container does not wipe active shares.

```powershell
docker compose down
```

stops the app but keeps those folders.

## AWS EC2

See [docs/AWS.md](docs/AWS.md) for instance launch, SSH, Docker install, `PUBLIC_BASE_URL`, security groups, HTTPS, and how to stop resources after the demo to avoid extra charges.

## Presentation

See [docs/PRESENTATION.md](docs/PRESENTATION.md) for a viva-ready outline: problem, solution, stack, architecture, demo, conclusion, and likely questions.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Upload page |
| POST | `/api/upload` | Store file, return share metadata |
| GET | `/share/<token>` | Receiver page |
| GET | `/api/share/<token>` | JSON metadata (no file paths) |
| GET | `/download/<token>` | Attachment download |
| GET | `/qr/<token>` | QR PNG |
| GET | `/health` | Health check |
| GET | `/api/config` | Max size and expiry |

## Security notes for a student MVP

- Tokens are created with `secrets.token_urlsafe`.
- Stored filenames are UUIDs. User filenames are only used as download names after sanitizing.
- Uploads are not served as static site files.
- Size is enforced on the server.
- HTTPS and a tight security group are required for a public demo.

Do not describe this as production-secure without a real security review.
