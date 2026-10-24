# AWS EC2 Deployment Guide

This guide deploys QuickShare with Docker on a single EC2 virtual machine. Eligibility for the AWS Free Tier and the exact price depend on your account, instance type, region, and current AWS pricing. Do not assume EC2 is free.

Do not put AWS access keys in the project. Use the AWS Console and SSH keys only.

## 1. Launch a small EC2 instance

1. Sign in to the AWS Console and open **EC2**.
2. Choose **Launch instance**.
3. Name it `quickshare`.
4. AMI: **Ubuntu Server 24.04 LTS**.
5. Instance type: **t3.micro** or **t2.micro** (small and inexpensive for a demo).
6. Key pair: create or select an SSH key. Download the `.pem` file and store it privately.
7. Network: allow inbound **SSH (22)** from your IP and **HTTP (80)**. For a first demo you may also allow **TCP 8000**. Prefer HTTP/HTTPS plus a reverse proxy for a real internet demo.
8. Storage: 8–16 GB is enough.
9. Launch the instance and copy its **public IPv4 address**.

## 2. Connect with SSH

On Windows PowerShell, from the folder that contains your key:

```powershell
ssh -i "your-key.pem" ubuntu@YOUR_EC2_PUBLIC_IP
```

If SSH refuses the key, run:

```powershell
icacls.exe your-key.pem /reset
icacls.exe your-key.pem /grant:r "$($env:USERNAME):(R)"
icacls.exe your-key.pem /inheritance:r
```

## 3. Install Docker on Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a644 /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu
newgrp docker
docker --version
```

## 4. Copy the project onto the instance

From your laptop (not from the EC2 shell):

```powershell
scp -i "your-key.pem" -r E:\quickshare ubuntu@YOUR_EC2_PUBLIC_IP:~/quickshare
```

Or clone from Git if you pushed the repo.

## 5. Configure environment variables

On the EC2 instance:

```bash
cd ~/quickshare
cp .env.example .env
nano .env
```

Set at least:

```
PUBLIC_BASE_URL=http://YOUR_EC2_PUBLIC_IP:8000
SECRET_KEY=a-long-random-string
```

`PUBLIC_BASE_URL` is what the QR code encodes. If this still says `127.0.0.1` or `localhost`, phones on another network cannot open the QR.

## 6–8. Persistent storage and start Docker

```bash
mkdir -p data uploads
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8000/health
```

`./data` and `./uploads` are bind-mounted into the container, so recreating the container does not delete active files or SQLite records.

## 9. Security group checklist

Allow only what you need:

- SSH 22 from your IP
- App port 8000, or 80/443 if you add Nginx
- No public access to database files
- Keep the `.pem` key private

## 10. Test from another network

1. Open `http://YOUR_EC2_PUBLIC_IP:8000` on your laptop.
2. Upload a PDF.
3. Scan the QR code with a phone that is **not** on the same Wi-Fi, or open the share URL in a second browser.
4. Confirm the download starts.
5. Confirm the QR URL is the public IP or domain, not localhost.
6. Wait 10 minutes (or temporarily set `EXPIRY_SECONDS=60` for a faster demo), then confirm the link is rejected.

## 11. Optional HTTPS with a domain and Nginx

If you have a domain pointing at the instance:

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Proxy `/` to `http://127.0.0.1:8000`, obtain a Let's Encrypt certificate, then set:

```
PUBLIC_BASE_URL=https://your-domain.example
```

Restart the container after changing `.env`:

```bash
docker compose up -d
```

HTTPS is the right choice for any internet-facing demo. This student MVP is not a production security audit.

## 12. Stop resources after the demonstration

```bash
docker compose down
```

In the AWS Console, **stop** the instance if you might reuse it, or **terminate** it if the demo is finished. Terminated instances and unused Elastic IPs can still create charges. Check the billing dashboard after the presentation.
