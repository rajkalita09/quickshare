import http.client
import json
import uuid
from pathlib import Path

def upload(filename: str, content: bytes) -> tuple[int, dict]:
    boundary = "----QS" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    conn = http.client.HTTPConnection("127.0.0.1", 5000)
    conn.request(
        "POST",
        "/api/upload",
        body,
        {"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    response = conn.getresponse()
    raw = response.read()
    conn.close()
    return response.status, json.loads(raw.decode())


if __name__ == "__main__":
    health = http.client.HTTPConnection("127.0.0.1", 5000)
    health.request("GET", "/health")
    print("health", health.getresponse().read().decode())
    health.close()

    status, payload = upload("demo.pdf", b"%PDF-1.4 live-demo")
    print("upload", status)
    print(json.dumps(payload, indent=2))
    Path("data").mkdir(exist_ok=True)
    Path("data/last_share.json").write_text(json.dumps(payload, indent=2))
