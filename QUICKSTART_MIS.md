# HAR Automation - Quick Start Guide for MIS/GEOMHAS
## Local Server Deployment - Step-by-Step Instructions

**Target Audience**: PHIVOLCS MIS/GEOMHAS IT Team
**Estimated Time**: 2-3 hours
**Difficulty**: Intermediate

---

## OVERVIEW

This guide provides streamlined instructions for deploying the HAR Automation web application on a PHIVOLCS internal server.

**What you'll deploy**:
- Flask web application (Python)
- Gunicorn WSGI server
- Nginx reverse proxy
- Systemd service for auto-start

**End result**: Internal web application accessible at `http://har-automation.phivolcs.local` (or chosen hostname)

---

## PRE-REQUISITES

### Server Requirements

**Minimum specifications**:
- OS: Ubuntu 22.04 LTS (or RHEL 8+)
- CPU: 2 cores
- RAM: 4 GB
- Storage: 20 GB
- Network: Internal network access

**Network configuration**:
- Static IP address assigned
- Internal DNS entry (optional): `har-automation.phivolcs.local`
- Firewall: Allow port 80 (HTTP) from internal network only

### Access Requirements

- Root or sudo access to server
- Access to PHIVOLCS code repository (or USB drive with code)
- (Optional) LDAP/Active Directory credentials for authentication

---

## STEP 1: SERVER SETUP

### 1.1 Connect to Server

```bash
ssh admin@<server-ip>
```

### 1.2 Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.3 Install System Dependencies

```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Install Nginx
sudo apt install -y nginx

# Install Git
sudo apt install -y git

# Install development libraries (for Python packages)
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev

# (Optional) Install LDAP libraries if using LDAP authentication
sudo apt install -y libldap2-dev libsasl2-dev
```

### 1.4 Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash harauto

# Set password (optional, for direct login)
sudo passwd harauto
```

---

## STEP 2: DEPLOY APPLICATION CODE

### 2.1 Switch to Application User

```bash
sudo su - harauto
```

### 2.2 Clone Repository

**Option A: From Git repository**
```bash
git clone <repository-url> har-automation
cd har-automation
```

**Option B: From USB drive or network share**
```bash
# Copy files from USB/network to home directory
cp -r /path/to/har-automation ~/har-automation
cd har-automation
```

### 2.3 Verify Files

```bash
# Check directory structure
ls -la

# Should see:
# - src/            (decision engine code)
# - docs/           (schema file)
# - requirements.txt
# - (web application files - to be created in next step)
```

---

## STEP 3: CREATE WEB APPLICATION

### 3.1 Create Directory Structure

```bash
# Still as harauto user
cd ~/har-automation

# Create web application directories
mkdir -p app/{routes,templates,static/{css,js},auth}
mkdir -p config logs

# Create __init__.py files
touch app/__init__.py
touch app/routes/__init__.py
touch app/auth/__init__.py
```

### 3.2 Create Configuration File

```bash
nano config/config.py
```

**Paste this content**:
```python
import os

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 28800  # 8 hours

    # Application
    SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'hazard_rules_schema_refined.json')

    # Logging
    LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log')

    # Authentication (set to False for simple deployment without auth)
    USE_AUTHENTICATION = False

    # LDAP settings (only if USE_AUTHENTICATION = True)
    LDAP_HOST = 'ldap://ldap.phivolcs.local'
    LDAP_BASE_DN = 'dc=phivolcs,dc=local'
    LDAP_USER_DN = 'ou=users'
```

Save and exit (Ctrl+X, Y, Enter)

### 3.3 Create Flask Application

```bash
nano app/__init__.py
```

**Paste this content**:
```python
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.config.Config')

    # Register routes
    from app.routes.main import main_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
```

### 3.4 Create Main Routes

```bash
nano app/routes/main.py
```

**Paste this content**:
```python
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main HAR generator page."""
    return render_template('index.html')

@main_bp.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok', 'version': '1.0'}
```

### 3.5 Create API Routes

```bash
nano app/routes/api.py
```

**Paste this content**:
```python
from flask import Blueprint, request, jsonify
import sys
from pathlib import Path

# Add decision engine to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine

api_bp = Blueprint('api', __name__)

# Load schema once at startup
schema_loader = SchemaLoader()
schema = schema_loader.load()
engine = DecisionEngine(schema)

@api_bp.route('/generate', methods=['POST'])
def generate_har():
    """Generate HAR from summary table."""
    try:
        data = request.get_json()
        summary_table = data.get('summary_table', '').strip()

        if not summary_table:
            return jsonify({'error': 'No summary table provided'}), 400

        # Parse assessments
        assessments = OHASParser.parse_from_table(summary_table)

        # Generate HARs
        results = []
        for assessment in assessments:
            har = engine.process_assessment(assessment)
            results.append({
                'assessment_id': assessment.id,
                'category': assessment.category.value,
                'har_text': har.to_text()
            })

        return jsonify({'success': True, 'hars': results})

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
```

### 3.6 Create HTML Template

```bash
nano app/templates/index.html
```

**Paste this content**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HAR Automation - PHIVOLCS</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .loading { display: none; }
        .loading.active { display: block; }
        #summaryTable { font-family: monospace; font-size: 0.9em; }
        #harOutput { font-family: monospace; font-size: 0.85em; white-space: pre-wrap; }
        .alert { margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <h1 class="mb-4">
                    <img src="https://www.phivolcs.dost.gov.ph/images/phivolcs_seal.png" alt="PHIVOLCS" height="60" class="me-3">
                    HAR Automation System
                </h1>
                <hr>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">Instructions</h5>
                    </div>
                    <div class="card-body">
                        <ol>
                            <li>Copy the summary table from the OHAS assessment page</li>
                            <li>Paste it into the text area below</li>
                            <li>Click "Generate HAR"</li>
                            <li>Copy the generated HAR text and paste into your report</li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">Summary Table Input</h5>
                    </div>
                    <div class="card-body">
                        <textarea
                            id="summaryTable"
                            class="form-control"
                            rows="8"
                            placeholder="Paste summary table here..."
                        ></textarea>
                        <div class="mt-3">
                            <button id="generateBtn" class="btn btn-primary btn-lg">
                                Generate HAR
                            </button>
                            <button id="clearBtn" class="btn btn-secondary btn-lg ms-2">
                                Clear
                            </button>
                        </div>
                        <div class="loading active text-center mt-3" id="loadingIndicator">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-2">Generating HAR...</p>
                        </div>
                        <div id="errorAlert" class="alert alert-danger" style="display:none;"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row" id="outputSection" style="display:none;">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0">Generated HAR</h5>
                    </div>
                    <div class="card-body">
                        <div id="harOutputContainer"></div>
                        <div class="mt-3">
                            <button id="copyBtn" class="btn btn-success">
                                Copy to Clipboard
                            </button>
                            <button id="downloadBtn" class="btn btn-secondary ms-2">
                                Download as .txt
                            </button>
                        </div>
                        <div id="successAlert" class="alert alert-success" style="display:none;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const summaryTable = document.getElementById('summaryTable');
        const generateBtn = document.getElementById('generateBtn');
        const clearBtn = document.getElementById('clearBtn');
        const loadingIndicator = document.getElementById('loadingIndicator');
        const errorAlert = document.getElementById('errorAlert');
        const outputSection = document.getElementById('outputSection');
        const harOutputContainer = document.getElementById('harOutputContainer');
        const copyBtn = document.getElementById('copyBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const successAlert = document.getElementById('successAlert');

        // Hide loading initially
        loadingIndicator.classList.remove('active');

        generateBtn.addEventListener('click', async () => {
            const tableText = summaryTable.value.trim();

            if (!tableText) {
                showError('Please paste a summary table first.');
                return;
            }

            // Show loading, hide errors and output
            loadingIndicator.classList.add('active');
            errorAlert.style.display = 'none';
            outputSection.style.display = 'none';
            generateBtn.disabled = true;

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ summary_table: tableText })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Unknown error');
                }

                // Display results
                displayHARs(data.hars);
                outputSection.style.display = 'block';

            } catch (error) {
                showError('Error: ' + error.message);
            } finally {
                loadingIndicator.classList.remove('active');
                generateBtn.disabled = false;
            }
        });

        clearBtn.addEventListener('click', () => {
            summaryTable.value = '';
            outputSection.style.display = 'none';
            errorAlert.style.display = 'none';
            successAlert.style.display = 'none';
        });

        copyBtn.addEventListener('click', () => {
            const text = harOutputContainer.textContent;
            navigator.clipboard.writeText(text).then(() => {
                showSuccess('HAR copied to clipboard!');
            }).catch(err => {
                showError('Failed to copy: ' + err.message);
            });
        });

        downloadBtn.addEventListener('click', () => {
            const text = harOutputContainer.textContent;
            const blob = new Blob([text], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'har_output.txt';
            a.click();
            URL.revokeObjectURL(url);
        });

        function displayHARs(hars) {
            harOutputContainer.innerHTML = '';
            hars.forEach((har, index) => {
                const div = document.createElement('div');
                div.className = 'mb-4';

                const header = document.createElement('h6');
                header.textContent = `Assessment ${har.assessment_id} - ${har.category}`;
                header.className = 'text-primary';

                const pre = document.createElement('pre');
                pre.id = 'harOutput';
                pre.className = 'border p-3 bg-light';
                pre.textContent = har.har_text;

                div.appendChild(header);
                div.appendChild(pre);

                if (index < hars.length - 1) {
                    div.appendChild(document.createElement('hr'));
                }

                harOutputContainer.appendChild(div);
            });
        }

        function showError(message) {
            errorAlert.textContent = message;
            errorAlert.style.display = 'block';
        }

        function showSuccess(message) {
            successAlert.textContent = message;
            successAlert.style.display = 'block';
            setTimeout(() => {
                successAlert.style.display = 'none';
            }, 3000);
        }
    </script>
</body>
</html>
```

### 3.7 Create WSGI Entry Point

```bash
cd ~/har-automation
nano wsgi.py
```

**Paste this content**:
```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
```

### 3.8 Create Development Runner (optional)

```bash
nano run.py
```

**Paste this content**:
```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## STEP 4: INSTALL PYTHON DEPENDENCIES

### 4.1 Create Virtual Environment

```bash
cd ~/har-automation
python3 -m venv venv
source venv/bin/activate
```

### 4.2 Update requirements.txt

```bash
nano requirements.txt
```

**Add these lines** (keep existing pyperclip if present):
```
flask>=3.0.0
gunicorn>=21.2.0
```

### 4.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## STEP 5: TEST APPLICATION

### 5.1 Run Development Server

```bash
# Still as harauto user with venv activated
python run.py
```

**Expected output**:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### 5.2 Test from Another Terminal

Open new terminal:
```bash
curl http://<server-ip>:5000/health

# Expected response:
# {"status":"ok","version":"1.0"}
```

### 5.3 Test in Browser

Open browser and go to: `http://<server-ip>:5000`

You should see the HAR Automation interface.

### 5.4 Test HAR Generation

1. Copy a sample summary table from OHAS
2. Paste into the text area
3. Click "Generate HAR"
4. Verify HAR text appears

### 5.5 Stop Development Server

Press `Ctrl+C` in the terminal running the dev server.

---

## STEP 6: CONFIGURE GUNICORN

### 6.1 Create Gunicorn Config

```bash
cd ~/har-automation
nano gunicorn.conf.py
```

**Paste this content**:
```python
import multiprocessing

# Server socket
bind = '127.0.0.1:8000'
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 60
keepalive = 2

# Logging
accesslog = '/home/harauto/har-automation/logs/access.log'
errorlog = '/home/harauto/har-automation/logs/error.log'
loglevel = 'info'

# Process naming
proc_name = 'har-automation'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None
```

### 6.2 Test Gunicorn

```bash
# Make sure venv is activated
source venv/bin/activate

# Create logs directory
mkdir -p logs

# Run Gunicorn
gunicorn -c gunicorn.conf.py wsgi:app
```

**Expected output**:
```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://127.0.0.1:8000
[INFO] Using worker: sync
[INFO] Booting worker with pid: ...
```

### 6.3 Test Gunicorn

In another terminal:
```bash
curl http://localhost:8000/health
```

### 6.4 Stop Gunicorn

Press `Ctrl+C`

---

## STEP 7: CREATE SYSTEMD SERVICE

### 7.1 Exit to Root User

```bash
# Exit from harauto user
exit

# You should now be back as admin/root user
```

### 7.2 Create Service File

```bash
sudo nano /etc/systemd/system/har-automation.service
```

**Paste this content**:
```ini
[Unit]
Description=HAR Automation Web Service
After=network.target

[Service]
Type=notify
User=harauto
Group=harauto
WorkingDirectory=/home/harauto/har-automation
Environment="PATH=/home/harauto/har-automation/venv/bin"
ExecStart=/home/harauto/har-automation/venv/bin/gunicorn \
    -c /home/harauto/har-automation/gunicorn.conf.py \
    wsgi:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 7.3 Reload Systemd and Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable har-automation
sudo systemctl start har-automation
```

### 7.4 Check Service Status

```bash
sudo systemctl status har-automation
```

**Expected output** (should show "active (running)"):
```
● har-automation.service - HAR Automation Web Service
     Loaded: loaded (/etc/systemd/system/har-automation.service; enabled)
     Active: active (running) since ...
```

### 7.5 Check Logs

```bash
sudo journalctl -u har-automation -f
```

Press `Ctrl+C` to exit log viewer.

---

## STEP 8: CONFIGURE NGINX

### 8.1 Create Nginx Site Configuration

```bash
sudo nano /etc/nginx/sites-available/har-automation
```

**Paste this content**:
```nginx
server {
    listen 80;
    server_name har-automation.phivolcs.local;  # Change to your hostname or IP

    # Logging
    access_log /var/log/nginx/har-automation-access.log;
    error_log /var/log/nginx/har-automation-error.log;

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Max request size
    client_max_body_size 10M;
}
```

### 8.2 Enable Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/har-automation /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t
```

**Expected output**:
```
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 8.3 Restart Nginx

```bash
sudo systemctl restart nginx
```

### 8.4 Check Nginx Status

```bash
sudo systemctl status nginx
```

---

## STEP 9: CONFIGURE FIREWALL

### 9.1 Install UFW (if not installed)

```bash
sudo apt install -y ufw
```

### 9.2 Configure Firewall Rules

```bash
# Allow SSH (important - don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow HTTP from internal network only
# Replace 10.0.0.0/8 with your actual internal network range
sudo ufw allow from 10.0.0.0/8 to any port 80

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## STEP 10: FINAL TESTING

### 10.1 Access from Browser

Open browser and navigate to:
- `http://<server-ip>/`
- Or `http://har-automation.phivolcs.local/` (if DNS is configured)

### 10.2 Test HAR Generation

1. Paste sample summary table
2. Click "Generate HAR"
3. Verify output appears
4. Test "Copy to Clipboard" button
5. Test "Download as .txt" button

### 10.3 Test Health Endpoint

```bash
curl http://<server-ip>/health
```

### 10.4 Test Multiple Concurrent Requests

```bash
# Run multiple requests simultaneously
for i in {1..5}; do
    curl http://<server-ip>/health &
done
wait
```

---

## STEP 11: MONITORING & LOGS

### 11.1 View Application Logs

```bash
# View systemd logs
sudo journalctl -u har-automation -n 100 -f

# View Gunicorn logs
sudo tail -f /home/harauto/har-automation/logs/error.log
sudo tail -f /home/harauto/har-automation/logs/access.log

# View Nginx logs
sudo tail -f /var/log/nginx/har-automation-access.log
sudo tail -f /var/log/nginx/har-automation-error.log
```

### 11.2 Configure Log Rotation

```bash
sudo nano /etc/logrotate.d/har-automation
```

**Paste this content**:
```
/home/harauto/har-automation/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 harauto harauto
    sharedscripts
    postrotate
        systemctl reload har-automation > /dev/null 2>&1 || true
    endscript
}
```

---

## TROUBLESHOOTING

### Application Won't Start

**Check service status**:
```bash
sudo systemctl status har-automation
sudo journalctl -u har-automation -n 50
```

**Common issues**:
- Missing Python dependencies: `sudo su - harauto`, then `source venv/bin/activate && pip install -r requirements.txt`
- Permissions: `sudo chown -R harauto:harauto /home/harauto/har-automation`
- Port already in use: `sudo lsof -i :8000`

### Nginx Returns 502 Bad Gateway

**Check Gunicorn is running**:
```bash
sudo systemctl status har-automation
curl http://localhost:8000/health
```

**Check Nginx configuration**:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### HAR Generation Fails

**Check schema file exists**:
```bash
ls -la /home/harauto/har-automation/docs/hazard_rules_schema_refined.json
```

**Check application logs**:
```bash
sudo journalctl -u har-automation -n 100
```

### Can't Access from Browser

**Check firewall**:
```bash
sudo ufw status
```

**Check Nginx is running**:
```bash
sudo systemctl status nginx
```

**Test from server itself**:
```bash
curl http://localhost/health
```

---

## MAINTENANCE COMMANDS

### Restart Application

```bash
sudo systemctl restart har-automation
```

### Restart Nginx

```bash
sudo systemctl restart nginx
```

### Update Application Code

```bash
# As harauto user
sudo su - harauto
cd har-automation
git pull  # or copy new files
source venv/bin/activate
pip install -r requirements.txt --upgrade
exit

# Restart service
sudo systemctl restart har-automation
```

### View Service Logs

```bash
sudo journalctl -u har-automation -f
```

### Check Disk Space

```bash
df -h
du -sh /home/harauto/har-automation/logs
```

---

## SECURITY NOTES

### Change Default Secret Key

```bash
sudo su - harauto
cd har-automation
nano config/config.py

# Change this line:
# SECRET_KEY = 'dev-secret-key-change-in-production'
# To a random string (generate with: python3 -c "import secrets; print(secrets.token_hex(32))")
```

Restart application after changing.

### Restrict Network Access

Ensure firewall only allows internal network:
```bash
sudo ufw status numbered
# Verify port 80 only allows from internal network
```

### Enable Authentication (Optional)

Edit `config/config.py`:
```python
USE_AUTHENTICATION = True
LDAP_HOST = 'ldap://your-ldap-server'
LDAP_BASE_DN = 'dc=phivolcs,dc=local'
```

(Requires additional LDAP configuration - see full deployment plan)

---

## NEXT STEPS

1. ✅ **Test thoroughly** with real OHAS data
2. ✅ **Train assessors** on how to use the system
3. ✅ **Configure DNS** (optional): Add `har-automation.phivolcs.local` to internal DNS
4. ✅ **Set up backups** for logs (if audit logging implemented)
5. ✅ **Schedule maintenance** window for updates
6. ✅ **Document** any customizations for your environment

---

## SUPPORT

**For technical issues**:
- Check logs: `sudo journalctl -u har-automation -n 100`
- Check application logs: `/home/harauto/har-automation/logs/error.log`
- Verify services: `sudo systemctl status har-automation nginx`

**For questions about this deployment**:
- Contact: [Your contact information]
- Documentation: `/home/harauto/har-automation/DEPLOYMENT_PLAN.md`

---

**Deployment completed successfully!** 🎉

The HAR Automation system is now running at: `http://<server-ip>/`
