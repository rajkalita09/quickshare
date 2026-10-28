# QuickShare — Temporary File Sharing

**Share Anything. Anywhere. In Seconds.**

QuickShare is a cloud-based temporary file-sharing web application built with Flask, Python, SQLite, Docker, and AWS EC2.

Upload a file, generate a unique sharing link, scan a QR code, or share a six-character transfer code. The receiver can download the file without creating an account.

Each share is valid for **10 minutes after the upload finishes**. Once it expires, QuickShare refuses further access and automatically deletes the stored file and its database record.

This project was developed as a student mini project for AWS Cloud Computing and Docker.

> **Project status:** Working educational MVP. It is not a production security audit or a replacement for a professionally managed file-sharing service.

**Important:** Expiry prevents future downloads from the server. It cannot erase a copy that a receiver has already downloaded.

---

## Table of Contents

- [1. Features](#1-features)
- [2. Technology Stack](#2-technology-stack)
- [3. Architecture](#3-architecture)
- [4. Project Structure](#4-project-structure)
- [5. Run Locally on Windows](#5-run-locally-on-windows)
- [6. Test with Docker Locally](#6-test-with-docker-locally)
- [7. Upload the Project to GitHub](#7-upload-the-project-to-github)
- [8. Deploy on AWS EC2](#8-deploy-on-aws-ec2)
- [9. Configure a Domain and HTTPS](#9-configure-a-domain-and-https)
- [10. Update the Live Website](#10-update-the-live-website)
- [11. Test the Deployment](#11-test-the-deployment)
- [12. API Endpoints](#12-api-endpoints)
- [13. Troubleshooting](#13-troubleshooting)
- [14. Security Considerations](#14-security-considerations)
- [15. AWS Costs and Cleanup](#15-aws-costs-and-cleanup)
- [16. Presentation and Documentation](#16-presentation-and-documentation)

---

## 1. Features

- **File upload:** Upload a file by dragging and dropping it or using the file picker.
- **Shareable links:** Generate unique URLs for individual files.
- **QR code sharing:** Generate a QR code containing the public sharing URL.
- **Six-character transfer codes:** Let a receiver find a file using a short alphanumeric code.
- **Browser-native downloads:** Downloads can appear in the browser's normal download manager with progress information.
- **Automatic expiry:** Each share expires after 10 minutes.
- **Live countdown:** Display the remaining validity time.
- **Automatic cleanup:** Delete expired files and database records in the background.
- **Persistent storage:** Preserve active shares across Docker container restarts.
- **No account required:** Senders and receivers do not need to register.
- **Responsive interface:** Designed for desktop and mobile browsers.
- **Health endpoint:** Check whether the application is responding.

### Default limits

| Setting | Default |
|---|---|
| Maximum file size | 25 MB |
| Share validity | 10 minutes |
| Upload rate limit | 20 uploads per IP per 10 minutes |
| Cleanup interval | 30 seconds |
| Database | SQLite |
| Application server | Gunicorn |
| Container runtime | Docker |

The actual limits are controlled by the application's configuration and environment variables.

---

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| Flask | Web framework and API |
| SQLite | Share metadata and expiry records |
| HTML, CSS, JavaScript | Frontend and interactive interface |
| QR code library | Generate QR images |
| Gunicorn | Run Flask in production |
| Docker | Package the application |
| Docker Compose | Configure and run the container |
| AWS EC2 | Host the application |
| Nginx | Reverse proxy and HTTPS integration |
| Certbot | Obtain and renew Let's Encrypt certificates |
| Git and GitHub | Source control and deployment workflow |

---

## 3. Architecture

### File-sharing workflow

```text
SENDER BROWSER
      |
      | Upload file
      v
FLASK APPLICATION
      |
      | Generate random stored filename
      v
UPLOADS DIRECTORY
      |
      | Save metadata and expiry
      v
SQLITE DATABASE
      |
      | Return sharing information
      v
LINK + QR CODE + TRANSFER CODE
      |
      v
RECEIVER BROWSER
      |
      | Open link, scan QR, or enter code
      v
VALIDATE SHARE AND EXPIRY
      |
      v
DOWNLOAD FILE
```

### Expiry and cleanup

```text
Background cleanup process
          |
          | Runs periodically
          v
Find expired shares
          |
          v
Delete expired files
          |
          v
Delete corresponding database records
```

### Production architecture

```text
User's Browser
      |
      | HTTPS :443
      v
Nginx Reverse Proxy
      |
      | HTTP on localhost:8000
      v
Docker Compose
      |
      v
Gunicorn + Flask
      |
      +---- SQLite database
      |
      +---- Persistent uploads directory
```

`PUBLIC_BASE_URL` controls the public URL used for share links and QR codes.

For local development, it can be:

```text
http://127.0.0.1:5000
```

For a Docker-based local setup, it can be:

```text
http://127.0.0.1:8000
```

For a deployed website, use your actual public HTTPS address, for example:

```text
https://your-domain.example.com
```

Replace the example with a domain you control and have configured to point to your server.

---

## 4. Project Structure

```text
quickshare/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── cleanup.py
│   ├── routes.py
│   ├── storage.py
│   └── qrcode_util.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── share.html
│   └── expired.html
├── static/
│   ├── css/
│   ├── js/
│   └── favicon.svg
├── tests/
├── docs/
│   ├── AWS.md
│   └── PRESENTATION.md
├── data/
├── uploads/
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py
├── wsgi.py
├── pytest.ini
└── README.md
```

Some files or directories may differ between project versions. Use the files present in your repository as the source of truth.

---

## 5. Run Locally on Windows

### Prerequisites

Install:

- Python 3.12
- Git
- Visual Studio Code (recommended)

Docker is optional for local development.

### Step 1 — Clone the repository

Open PowerShell:

```powershell
git clone https://github.com/YOUR_USERNAME/quickshare.git
cd quickshare
```

Replace `YOUR_USERNAME` with the GitHub account that owns the repository.

Alternatively, download your repository as a ZIP file and extract it.

### Step 2 — Create a virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

This changes the execution policy for the current PowerShell process only.

### Step 3 — Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4 — Configure environment variables

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Open `.env` in VS Code.

For local development, set the public URL to match the address you use:

```dotenv
PUBLIC_BASE_URL=http://127.0.0.1:5000
```

Keep any other required settings from `.env.example`. Do not replace the whole file with this one-line example.

Never commit your real `.env` file or private credentials to GitHub.

### Step 5 — Start the application

```powershell
python run.py
```

Open:

**http://127.0.0.1:5000/**

Your local QuickShare application should now be available.

### Step 6 — Test the basic workflow

1. Upload an image or PDF.
2. Copy the generated sharing link.
3. Scan the QR code.
4. Copy the six-character transfer code.
5. Open another browser or an incognito window.
6. Test downloading using each sharing method.
7. Confirm the expiry countdown appears.

Stop the development server using `Ctrl + C`.

---

## 6. Test with Docker Locally

Docker provides a closer approximation of the production environment.

### Step 1 — Install Docker

Install Docker Desktop for Windows and make sure its Docker engine is running.

Official documentation:

https://docs.docker.com/desktop/setup/install/windows-install/

### Step 2 — Configure the environment

From the project root:

```powershell
Copy-Item .env.example .env
```

Set the public URL in `.env` to:

```dotenv
PUBLIC_BASE_URL=http://127.0.0.1:8000
```

Preserve all other required settings.

### Step 3 — Build and start QuickShare

```powershell
docker compose up -d --build
```

Check the container:

```powershell
docker compose ps
```

View application logs:

```powershell
docker compose logs --tail=100 web
```

If your Compose service has a different name, use the service name displayed by:

```powershell
docker compose config --services
```

### Step 4 — Open the website

Visit:

http://127.0.0.1:8000/

### Step 5 — Stop the application

```powershell
docker compose down
```

This stops and removes the Compose containers but normally preserves the host-mounted `data/` and `uploads/` folders.

**Do not delete those folders if you need to retain active shares.**

---

## 7. Upload the Project to GitHub

### Step 1 — Create a repository

Create a new repository at:

https://github.com/new

Choose a repository name such as `quickshare`.

### Step 2 — Check your project files

From PowerShell:

```powershell
cd E:\quickshare
git status
```

Confirm that sensitive files and generated data are excluded from version control.

Your `.gitignore` should exclude items such as:

```gitignore
.env
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
data/
uploads/
```

Review the existing `.gitignore` before adding these entries. Only exclude local data directories if your project is designed to create them at runtime.

### Step 3 — Initialize Git if needed

If the project is not already a Git repository:

```powershell
git init
git branch -M main
git add .
git commit -m "Initial QuickShare release"
git remote add origin https://github.com/YOUR_USERNAME/quickshare.git
git push -u origin main
```

Replace the repository URL with your own.

If the repository is already initialized and connected to GitHub, **do not repeat `git init` or `git remote add origin`**. Instead, commit and push your changes using your existing branch workflow.

### Step 4 — Verify the upload

Open your GitHub repository and confirm that the application code, templates, static assets, Docker files, and documentation are present.

Never upload:

- `.env` secrets
- AWS access keys
- SSH private keys
- Production databases or users' uploaded files

---

## 8. Deploy on AWS EC2

This section describes a typical Ubuntu EC2 deployment using Docker Compose and Nginx. Commands may need minor adjustments for your Ubuntu version and existing server configuration.

### What you need

- An AWS account
- An EC2 instance running Ubuntu
- Your QuickShare GitHub repository
- Docker and Docker Compose
- A public IPv4 address
- A domain name or a supported dynamic DNS hostname for HTTPS

AWS pricing, Free Tier eligibility, and included usage vary by account and region. Check the current pricing before launching resources.

### Step 1 — Launch an EC2 instance

Open:

https://console.aws.amazon.com/ec2/

1. Select **Launch instance**.
2. Enter an instance name, such as `quickshare-server`.
3. Select a supported Ubuntu Server LTS AMI.
4. Select an instance type appropriate for your expected workload.
5. Create or select an SSH key pair.
6. Configure the security group.
7. Launch the instance.

A small instance can be sufficient for a student demonstration, but performance depends on file size, network throughput, CPU, memory, and concurrent users.

### Step 2 — Configure the security group

For a public website using Nginx and HTTPS, the typical inbound rules are:

| Type | Port | Source |
|---|---:|---|
| SSH | 22 | Your trusted IP address |
| HTTP | 80 | `0.0.0.0/0` |
| HTTPS | 443 | `0.0.0.0/0` |

For IPv6, configure the corresponding IPv6 rules if needed.

Restrict SSH to your own trusted IP address rather than allowing SSH from everywhere.

Do not expose SQLite or other database ports publicly. If Nginx proxies to a container on the same EC2 host, the application port does not need to be open to the entire internet.

### Step 3 — Connect to EC2

You can use the AWS Console's EC2 Instance Connect terminal or SSH from your computer.

Example PowerShell command:

```powershell
ssh -i "C:\path\to\your-key.pem" ubuntu@YOUR_EC2_PUBLIC_IP
```

Replace the key path and IP with your actual values.

Once connected, check the system:

```bash
whoami
uname -a
ls -la
```

### Step 4 — Install Docker and Git

Update package information:

```bash
sudo apt update
```

Install Git, Docker, and the Compose plugin from the Ubuntu repositories:

```bash
sudo apt install -y git docker.io docker-compose-v2
```

If your Ubuntu release uses different package names, consult its package documentation.

Enable Docker:

```bash
sudo systemctl enable --now docker
```

Verify installation:

```bash
sudo docker --version
sudo docker compose version
```

Use `sudo docker` if your user does not have permission to access the Docker socket. Do not change Docker socket permissions to make it world-accessible.

### Step 5 — Clone your GitHub repository

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/quickshare.git
cd quickshare
```

Replace the URL with your own repository.

For a private repository, configure an appropriate authentication method rather than embedding credentials in the repository URL.

### Step 6 — Create the production environment file

Copy the example:

```bash
cp .env.example .env
nano .env
```

Set `PUBLIC_BASE_URL` to the actual public HTTPS URL you intend to use, for example:

```dotenv
PUBLIC_BASE_URL=https://your-domain.example.com
```

Preserve other required settings and set production-appropriate values according to the configuration supported by your application.

Save in Nano with `Ctrl + O`, press Enter, and exit with `Ctrl + X`.

Protect the file:

```bash
chmod 600 .env
```

Do not copy your local development secrets into production without reviewing them.

### Step 7 — Create persistent data directories

From the project root:

```bash
mkdir -p data uploads
```

Your Compose configuration should mount the persistent directories into the application container. For example:

```yaml
volumes:
  - ./data:/app/data
  - ./uploads:/app/uploads
```

Use the volume paths defined in your actual `docker-compose.yml`.

These host-mounted folders preserve application data when a container is recreated. They are not a substitute for backups.

### Step 8 — Build and start QuickShare

```bash
sudo docker compose up -d --build
```

Check the service:

```bash
sudo docker compose ps
```

Review logs:

```bash
sudo docker compose logs --tail=100 web
```

If your Compose service is not named `web`, replace it with the correct name.

Check the application's health endpoint:

```bash
curl -i http://127.0.0.1:8000/health
```

The URL assumes your Compose file maps the application to host port `8000`. Adjust the port if your configuration differs.

A successful health check should return HTTP `200 OK`.

**Important:** Do not proceed to public traffic until the application is healthy and there are no recurring startup errors.

### Step 9 — Configure Nginx as a reverse proxy

Install Nginx:

```bash
sudo apt install -y nginx
sudo systemctl enable --now nginx
```

Create a site configuration:

```bash
sudo nano /etc/nginx/sites-available/quickshare
```

For a deployment where the application listens on `127.0.0.1:8000`, a basic HTTP configuration is:

```nginx
server {
    listen 80;
    listen [::]:80;

    server_name your-domain.example.com;

    client_max_body_size 26m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
```

Replace `your-domain.example.com` with your real hostname.

The example upload limit allows some overhead beyond the application's 25 MB file limit. Ensure the Flask application enforces its own maximum size as well.

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/quickshare /etc/nginx/sites-enabled/quickshare
```

If the default Nginx site conflicts with your configuration, inspect it before disabling it.

Test the configuration:

```bash
sudo nginx -t
```

If the test succeeds:

```bash
sudo systemctl reload nginx
```

At this stage, the application may be accessible over HTTP. Complete the HTTPS setup before sharing sensitive files publicly.

### Step 10 — Verify the reverse proxy

From EC2:

```bash
curl -I http://127.0.0.1/
```

Check the Nginx status:

```bash
sudo systemctl status nginx --no-pager
```

If you see a `502 Bad Gateway`, confirm that the Docker container is healthy and Nginx's `proxy_pass` points to the correct host and port.

---

## 9. Configure a Domain and HTTPS

A public HTTPS URL is needed for QR codes and share links that other devices can open reliably.

### Step 1 — Configure DNS

Use a domain you control or a dynamic DNS service that supports your intended setup.

Create the appropriate DNS record pointing your hostname to the EC2 public IP address.

If your EC2 public IP changes, DNS may need updating. An Elastic IP can provide a stable IPv4 address, but AWS charges and allocation rules may apply.

Verify DNS resolution from your computer:

```powershell
nslookup your-domain.example.com
```

Replace the example hostname with your own.

### Step 2 — Confirm HTTP access

Before requesting a certificate, ensure:

- DNS resolves to your server.
- EC2 inbound rules allow ports 80 and 443.
- Nginx is running.
- The HTTP site configuration uses the correct hostname.

### Step 3 — Install Certbot

On Ubuntu, you can install Certbot and its Nginx integration using the supported packages for your release:

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

Request a certificate:

```bash
sudo certbot --nginx -d your-domain.example.com
```

Follow the prompts and select the HTTPS redirection option if offered.

Certbot must be able to validate your domain. Certificate issuance may fail if DNS, firewall rules, or the Nginx configuration is incorrect.

### Step 4 — Verify HTTPS

Open:

```text
https://your-domain.example.com/
```

Confirm that the browser reports a valid HTTPS connection.

Check automatic certificate renewal:

```bash
sudo certbot renew --dry-run
```

Keep `PUBLIC_BASE_URL` set to the final HTTPS URL, not the EC2 private IP or local development address.

---

## 10. Update the Live Website

After the initial deployment, updates can be published by pushing code to GitHub and rebuilding the Docker service on EC2.

### Step 1 — Update your local code

Test changes locally before deployment.

Run your automated tests:

```powershell
pytest -q
```

Commit and push the tested code using your existing Git branch workflow.

### Step 2 — Merge changes into `main`

If you use a feature branch:

1. Push the feature branch to GitHub.
2. Create a pull request targeting `main`.
3. Review the changed files.
4. Merge the pull request.

Only deploy code that has been tested and merged into the branch used by your server.

### Step 3 — Connect to EC2 and pull changes

```bash
cd ~/quickshare
git fetch origin
git switch main
git pull --ff-only origin main
```

If your deployment uses another branch, use that branch consistently.

Before deployment, check your production backup and ensure `.env`, `data/`, and `uploads/` are preserved.

### Step 4 — Rebuild the application

```bash
sudo docker compose up -d --build web
```

This command assumes the Compose service is named `web`.

### Step 5 — Verify the deployment

```bash
sudo docker compose ps
sudo docker compose logs --tail=100 web
curl -i http://127.0.0.1:8000/health
```

Check that the application is healthy and that no new database migration or startup errors appear.

### Step 6 — Test the live site

Open your public HTTPS URL and verify:

- Uploading works.
- Share links work.
- QR codes work.
- Transfer-code lookup and download work.
- The browser shows download progress.
- Expired links are rejected.
- Cleanup runs correctly.

### Important deployment rule

**Never delete the production database or uploaded files as part of a routine code update.**

Back up production data before migrations or risky deployments. Recreating a container should not erase properly mounted persistent data.

---

## 11. Test the Deployment

### Automated tests

From your local development environment:

```powershell
pytest -q
```

The test suite may cover:

- File upload
- Empty-file rejection
- Oversized-file rejection
- QR code generation
- Invalid tokens
- Expiry before cleanup
- Automatic deletion
- Duplicate filenames
- Missing files

Review the actual tests in `tests/` for the exact coverage of your repository version.

### Manual demo checklist

- [ ] Upload a PDF.
- [ ] Upload an image.
- [ ] Upload a small video.
- [ ] Copy and open the sharing link in another browser.
- [ ] Scan the QR code using a phone.
- [ ] Enter the six-character transfer code.
- [ ] Confirm browser-native download progress for all supported sharing methods.
- [ ] Confirm an invalid code is rejected.
- [ ] Confirm expired links cannot download files.
- [ ] Confirm expired files are eventually deleted.
- [ ] Restart the Docker container and verify active shares still work.
- [ ] Confirm HTTPS works without certificate warnings.

For a faster local expiry demonstration, configure a short expiry only if the application supports the `EXPIRY_SECONDS` environment variable.

---

## 12. API Endpoints

The exact API routes depend on the current application version.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Display the upload page |
| `POST` | `/api/upload` | Upload a file and return share metadata |
| `GET` | `/share/<token>` | Display the receiver page |
| `GET` | `/api/share/<token>` | Retrieve share metadata |
| `GET` | `/download/<token>` | Download a file by its share token |
| `GET` | `/qr/<token>` | Return a QR code image |
| `GET` | `/health` | Health check |
| `GET` | `/api/config` | Return client-facing configuration |
| `POST` | `/api/receive-code` | Find a share using a transfer code |
| `POST` | `/api/receive-code/download` | Download through the transfer-code flow in versions that use this endpoint |

The final endpoint may differ after changes to browser-native transfer-code downloads. Check `app/routes.py` for the routes implemented by your current version.

Do not expose internal server file paths through API responses.

---

## 13. Troubleshooting

### Docker permission denied

If `docker ps` returns a permission error, try:

```bash
sudo docker ps
```

Check the Docker service:

```bash
sudo systemctl status docker --no-pager
```

### Container fails to start

Inspect the logs:

```bash
sudo docker compose logs --tail=100 web
```

Check the health status:

```bash
sudo docker compose ps
```

Do not delete your database to solve an application startup or migration error.

### Nginx shows 502 Bad Gateway

Check the application container:

```bash
sudo docker compose ps
```

Check the Nginx configuration:

```bash
sudo nginx -t
```

Check Nginx logs:

```bash
sudo tail -n 100 /var/log/nginx/error.log
```

Confirm that the Nginx upstream address and port match the application's actual host port.

### Website cannot be opened

Check:

1. EC2 instance status.
2. Public IP and DNS resolution.
3. Security group inbound rules.
4. Nginx service status.
5. Docker container health.
6. HTTPS certificate validity.

### Transfer-code download is not starting

Inspect the browser console and Network tab.

Check the response from the transfer-code lookup endpoint and verify that the returned download URL is preserved by the frontend.

If you recently updated JavaScript, perform a hard refresh using `Ctrl + Shift + R`.

### QR code opens the wrong address

Check the `.env` value:

```dotenv
PUBLIC_BASE_URL=https://your-domain.example.com
```

Restart or rebuild the application only as required by your deployment configuration after changing environment variables.

### Database migration error

Review the application logs and migration code. Back up the database before applying a schema change.

Do not manually delete SQLite files, upload directories, or Docker volumes to work around a migration problem.

---

## 14. Security Considerations

QuickShare is an educational MVP. Before exposing it to substantial or sensitive workloads, conduct a proper security review.

- Use HTTPS for public access.
- Keep SSH restricted to trusted IP addresses.
- Never publish AWS credentials, private keys, or `.env` secrets.
- Use random, unguessable share tokens.
- Store uploaded files under server-generated names.
- Sanitize filenames used in download responses.
- Enforce upload size limits on the server.
- Do not expose the uploads directory as a public static directory.
- Reject expired shares even if background cleanup has not yet run.
- Ensure transfer-code lookup and download authorization are implemented consistently.
- Back up production data before database migrations.
- Keep Ubuntu, Docker, Python dependencies, and Nginx updated.
- Monitor storage usage and application errors.
- Do not assume a six-character code alone provides strong security against automated guessing; apply appropriate rate limits.
- Consider malware scanning, abuse prevention, authentication, quotas, and stronger operational controls before wider public use.

### Privacy and expiry

QuickShare automatically removes expired files from its managed storage. This does not erase copies downloaded by receivers, screenshots, backups, or other copies outside the server's control.

---

## 15. AWS Costs and Cleanup

AWS resources can incur charges even when the website is not receiving traffic.

Before launching an instance, review current AWS pricing and Free Tier eligibility for your account and region.

Potential costs include:

- EC2 instance usage
- EBS storage
- Public IPv4 addresses
- Elastic IP allocation
- Data transfer
- Domain registration
- Other networking or monitoring services

### Stop the application

To stop the Compose application while preserving its host data:

```bash
cd ~/quickshare
sudo docker compose down
```

This stops the containers but normally preserves bind-mounted `data/` and `uploads/` directories.

### Stop the EC2 instance

Use the AWS Console to stop the instance when you no longer need it temporarily. A stopped instance may still incur charges for attached storage and certain allocated networking resources.

### Remove resources when finished

If you no longer need the project, carefully review and delete the EC2 instance and associated resources that you no longer require.

Check for:

- EBS volumes and snapshots
- Elastic IP addresses
- Other provisioned services
- Domain or DNS service charges

**Stopping an instance is not the same as deleting every billable resource.** Review the AWS Billing dashboard to check for remaining charges.

---

## 16. Presentation and Documentation

For a project presentation, explain QuickShare in this order:

1. **Problem:** Sharing files can require exchanging contact details or creating accounts.
2. **Solution:** QuickShare provides temporary file sharing through links, QR codes, and transfer codes.
3. **Backend:** Flask handles uploads, authorization, downloads, and expiry.
4. **Database:** SQLite stores share metadata and expiration timestamps.
5. **Containerization:** Docker packages the application for consistent deployment.
6. **Cloud deployment:** AWS EC2 hosts the application.
7. **Networking:** Nginx routes public requests to the application and supports HTTPS.
8. **Cleanup:** A background task deletes expired files and database records.
9. **Demonstration:** Upload a file, share it, download it, and demonstrate expiry.
10. **Limitations:** Explain that this is an MVP and identify improvements needed before production use.

Additional project documentation:

- `docs/AWS.md` — AWS-specific instructions, if maintained in the repository.
- `docs/PRESENTATION.md` — Presentation outline and viva preparation, if maintained in the repository.

---

## Conclusion

QuickShare demonstrates how to build and deploy a full-stack file-sharing application using Python, Flask, SQLite, Docker, and AWS EC2.

It combines file upload, temporary storage, unique sharing links, QR codes, transfer codes, browser downloads, expiry validation, and automatic cleanup in one application.

The deployment workflow also demonstrates practical cloud skills: GitHub version control, Linux server administration, container management, reverse proxy configuration, HTTPS, health checks, and production troubleshooting.

**Built as a student mini project for learning cloud computing and containerized application deployment.**
