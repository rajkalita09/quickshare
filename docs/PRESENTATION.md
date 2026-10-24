# QuickShare — Presentation Outline (5–7 minutes)

## 1. Problem (30–45 seconds)

Sharing files through chat and email is often inconvenient. Apps cap file size, change formats, or require both people to use the same service. Students and teammates still need a fast way to hand someone a file right now.

## 2. Solution (45 seconds)

**QuickShare** is a temporary file-sharing website.

1. The sender uploads one file.
2. The server stores it privately and returns a unique URL plus a QR code.
3. The receiver opens the link or scans the QR code and the download starts.
4. Exactly 10 minutes after upload, the server refuses access and deletes the file.

No accounts. No inbox. The link is the entire sharing workflow.

Expiry means the **server stops granting access**. A copy already saved on the receiver’s device is not remotely erased.

## 3. Technology stack (45 seconds)

| Layer | Choice | Why it fits a 2–3 day mini project |
| --- | --- | --- |
| Frontend | HTML, CSS, vanilla JavaScript | Easy to explain and demo |
| Backend | Python, Flask, Gunicorn | Small API, student-friendly |
| Database | SQLite | One file, persistent with a volume |
| QR | Python `qrcode` | Share URL encoded as an image |
| Containers | Docker Compose | Same app on laptop and AWS |
| Cloud | AWS EC2 | Public internet access for the QR code |

## 4. Architecture (60–90 seconds)

```
Browser  →  Flask/Gunicorn  →  SQLite metadata
                         ↘  uploads/ (random internal filenames)
                         ↘  background cleanup thread (every 30s)
```

- Tokens are long, random, and unguessable.
- Original filenames are never used as filesystem paths.
- Every download, metadata, and QR request checks `expires_at` in UTC.
- Cleanup deletes expired files even if nobody visits the site.
- `PUBLIC_BASE_URL` makes QR codes point at the real public URL on EC2, not localhost.

Docker mounts `./data` and `./uploads` from the host so a container restart does not lose active shares.

## 5. Live demo (2 minutes)

1. Open the homepage. Point out dark UI, 10-minute badge, drag-and-drop.
2. Upload a PDF. Show progress, then the QR and copy-link panel.
3. Open the link on a phone or second browser. Show auto-download and the fallback button.
4. Explain that the countdown is visual only; the server is the authority.
5. If time allows, show `/health` and `docker compose ps`.

## 6. Conclusion (30 seconds)

QuickShare solves a real sharing friction with a small, understandable cloud app: upload, unique link, QR, automatic download, 10-minute expiry, and automatic deletion — packaged with Docker for AWS EC2.

## Suggested viva questions

**What is stored in SQLite?** Token, internal filename, original download name, size, created time, expiry time.

**Why not trust the frontend timer?** Anyone can change JavaScript. The server checks expiry on every sensitive request.

**Why random internal filenames?** Stops path traversal, overwrites, and execution of uploaded files as site code.

**Why Docker?** Same runtime on your PC and EC2. Volumes keep files after restart.

**Why `PUBLIC_BASE_URL`?** QR codes must contain a URL the receiver can actually open on the internet.

**Is this production-secure?** It follows basic safe file handling for a student MVP. It is not a hardened production system.

**What happens after 10 minutes if cleanup is late?** Access is already denied. Cleanup later removes the bytes and the database row.
