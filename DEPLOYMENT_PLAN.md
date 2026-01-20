# HAR Automation Deployment Plan
## Decision Engine Web Application - Deployment Options & Implementation

**Version**: 1.0
**Date**: 2025-12-21
**Status**: Planning Phase

---

## EXECUTIVE SUMMARY

This document outlines deployment strategies for the HAR (Hazard Assessment Report) automation decision engine with a minimal but functional web UI. Two deployment options are provided:

1. **Option A**: Vercel Cloud Deployment (Experimental/Development)
2. **Option B**: Local PHIVOLCS Server Deployment (Production/Secure)

**Recommended approach**: Start with **Option B (Local)** for security and data control, with Option A available for proof-of-concept demonstrations.

---

## CURRENT ARCHITECTURE ANALYSIS

### Core Components

**Decision Engine**: `/home/finch/repos/hasadmin/har-automation/src/pipeline/decision_engine.py`
- Pure Python implementation
- No external API dependencies
- Schema-driven text generation
- Stateless processing (no database required)

**Data Models**: `/home/finch/repos/hasadmin/har-automation/src/models/`
- `assessment.py`: Input data structures
- `har_output.py`: Generated report format
- `schema.py`: Rule definitions

**Parser**: `/home/finch/repos/hasadmin/har-automation/src/parser/`
- `ohas_parser.py`: Parses OHAS summary tables
- `table_parser.py`: Tab-separated value parsing
- `schema_loader.py`: Loads JSON schema

**Schema**: `/home/finch/repos/hasadmin/docs/hazard_rules_schema_refined.json`
- 2.0 MB JSON file with all hazard rules
- Earthquake rules (Active Fault, Liquefaction, EIL, Tsunami)
- Volcano rules (PDZ, Lahar, PDC, Lava, Ballistic, Base Surge, Fissure, etc.)
- Special cases (Pinatubo, Mayon, Taal)

### Dependencies

**Required**:
- Python 3.8+
- No external runtime dependencies (pyperclip only for CLI)

**Optional** (for web deployment):
- Web framework (Flask/FastAPI)
- WSGI server (Gunicorn/Uvicorn)
- Reverse proxy (Nginx - for local deployment)

### Current Interface

**CLI Mode**: `generate_har.py`
- Reads summary table from stdin
- Generates HAR text files
- No authentication or access control

---

## OPTION A: VERCEL CLOUD DEPLOYMENT

### Overview

Deploy as serverless Python function on Vercel with Next.js frontend.

**Pros**:
- Zero infrastructure management
- Auto-scaling
- Free tier available
- Fast global CDN
- Easy updates via Git push

**Cons**:
- Data leaves PHIVOLCS network
- Public internet exposure
- Limited control over security
- Cold start latency (~1-2s)
- NOT suitable for production with sensitive data

**Recommendation**: Use ONLY for demonstrations and proof-of-concept

### Architecture

```
User Browser
    ↓
Vercel Edge Network (CDN)
    ↓
Next.js Frontend (Static)
    ↓
Vercel Serverless Function (Python)
    ↓
Decision Engine + Schema (bundled)
    ↓
Return HAR text
```

### Technology Stack

- **Frontend**: Next.js 14 (React) with TypeScript
- **API**: Vercel Serverless Functions (Python 3.9)
- **Styling**: Tailwind CSS
- **Deployment**: Git-based (GitHub → Vercel auto-deploy)

### File Structure

```
har-automation-web/
├── api/
│   └── generate.py          # Serverless function endpoint
├── app/
│   ├── page.tsx             # Main UI page
│   ├── layout.tsx           # App layout
│   └── globals.css          # Global styles
├── public/
│   └── schema.json          # Copy of hazard_rules_schema_refined.json
├── lib/
│   ├── decision_engine/     # Copy of src/ directory
│   └── types.ts             # TypeScript types
├── package.json
├── vercel.json              # Vercel config
└── requirements.txt         # Python dependencies for API
```

### Implementation Steps

#### Phase 1: Project Setup (2 hours)
1. Create Next.js project with TypeScript
2. Copy decision engine code to `lib/decision_engine/`
3. Copy schema to `public/schema.json`
4. Create API endpoint `api/generate.py`

#### Phase 2: Frontend Development (4 hours)
1. Create form for summary table input
2. Add "Generate HAR" button
3. Display generated HAR with copy-to-clipboard
4. Add loading states and error handling
5. Implement basic validation

#### Phase 3: API Implementation (2 hours)
1. Create serverless function wrapper
2. Integrate decision engine
3. Add input validation
4. Return JSON response with HAR text

#### Phase 4: Testing & Deployment (2 hours)
1. Test with sample assessments
2. Configure Vercel project
3. Deploy to Vercel
4. Verify functionality

**Total estimated time**: 10 hours

### Security Considerations

⚠️ **CRITICAL SECURITY LIMITATIONS**:
- No authentication (anyone can access)
- No access logs
- Data transmitted over public internet
- Schema visible in browser
- Cannot restrict to PHIVOLCS network

**Mitigations for demo use**:
- Add basic API key authentication
- Rate limiting via Vercel config
- Disable after demonstration
- Use test data only (no real assessments)

### Cost Analysis

**Vercel Free Tier**:
- 100 GB bandwidth/month
- 100,000 serverless function invocations/month
- Sufficient for low-volume testing

**Estimated usage** (100 HARs/month):
- Bandwidth: ~1 MB/HAR = 100 MB/month (well under limit)
- Functions: 100 invocations/month (well under limit)
- **Cost**: $0/month

---

## OPTION B: LOCAL PHIVOLCS SERVER DEPLOYMENT (RECOMMENDED)

### Overview

Deploy as Python web application on PHIVOLCS internal server with Nginx reverse proxy.

**Pros**:
- Complete data control (never leaves PHIVOLCS network)
- Can integrate with OHAS authentication
- Full security control
- No internet dependency
- Audit logging possible
- Can access PHIVOLCS databases directly

**Cons**:
- Requires server infrastructure
- MIS/GEOMHAS coordination needed
- Manual updates required
- Need to manage backups

**Recommendation**: **PRIMARY DEPLOYMENT OPTION** for production use

### Architecture

```
PHIVOLCS Internal Network
    ↓
User Browser → Nginx (Reverse Proxy)
                  ↓
            Gunicorn (WSGI Server)
                  ↓
            Flask App (Python)
                  ↓
            Decision Engine + Schema
                  ↓
            Return HAR text
                  ↓
            (Optional) Log to database
```

### Technology Stack

- **Framework**: Flask 3.0 (lightweight, familiar to Python developers)
- **WSGI Server**: Gunicorn (production-ready)
- **Reverse Proxy**: Nginx (SSL termination, static files)
- **Authentication**: Flask-Login + LDAP/Active Directory (integrate with PHIVOLCS)
- **Database** (optional): PostgreSQL for audit logs
- **OS**: Ubuntu 22.04 LTS (or RHEL/CentOS if required by MIS)

### File Structure

```
har-automation-web/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py          # Main routes
│   │   └── api.py           # API endpoints
│   ├── templates/
│   │   ├── base.html        # Base template
│   │   ├── index.html       # Main UI
│   │   └── login.html       # Login page
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js       # Frontend logic
│   └── auth/
│       ├── __init__.py
│       └── ldap_auth.py     # LDAP authentication
├── decision_engine/         # Symlink to har-automation/src/
├── config/
│   ├── config.py            # App configuration
│   └── schema.json          # Symlink to hazard_rules_schema_refined.json
├── logs/
│   └── app.log
├── requirements.txt
├── wsgi.py                  # Gunicorn entry point
├── run.py                   # Development server
└── deploy/
    ├── nginx.conf           # Nginx configuration
    ├── gunicorn.conf.py     # Gunicorn configuration
    └── systemd/
        └── har-automation.service  # Systemd service
```

### Implementation Steps

#### Phase 1: Flask Application (4 hours)
1. Create Flask app structure
2. Integrate decision engine
3. Create HTML templates with Bootstrap
4. Add form validation
5. Implement HAR generation endpoint

#### Phase 2: Authentication (3 hours)
1. Set up Flask-Login
2. Integrate with PHIVOLCS LDAP/AD
3. Create login/logout routes
4. Add session management
5. Implement role-based access (assessor, admin)

#### Phase 3: UI Development (4 hours)
1. Create responsive form layout
2. Add textarea for summary table input
3. Display generated HAR with formatting
4. Add copy-to-clipboard button
5. Show loading spinner during processing
6. Error handling and validation messages

#### Phase 4: Deployment Configuration (3 hours)
1. Create Gunicorn configuration
2. Write Nginx reverse proxy config
3. Create systemd service file
4. Set up log rotation
5. Configure SSL certificates (if needed)

#### Phase 5: Testing & Documentation (3 hours)
1. Test with sample assessments
2. Load testing (concurrent users)
3. Write deployment documentation for MIS
4. Create user manual
5. Security audit

**Total estimated time**: 17 hours

### Server Requirements

#### Minimum Specifications

**Hardware**:
- CPU: 2 cores (2.0 GHz+)
- RAM: 4 GB
- Storage: 20 GB
- Network: 100 Mbps internal

**Software**:
- OS: Ubuntu 22.04 LTS (or RHEL 8+)
- Python: 3.8+
- Nginx: 1.18+
- Systemd for service management

**Expected load** (assumptions):
- 50 concurrent users (assessors)
- 500 HARs generated/day
- Each HAR generation: ~200ms processing time
- Peak: 10 requests/second

**Resource usage estimates**:
- CPU: <10% average, <50% peak
- RAM: ~500 MB per worker (4 workers = 2 GB)
- Storage: <1 GB (app + logs + schema)
- Network: Minimal (<1 Mbps)

### Security Implementation

#### Authentication & Authorization

**LDAP/Active Directory Integration**:
```python
# Authenticate against PHIVOLCS LDAP
- Users: PHIVOLCS staff only
- Roles: assessor, reviewer, admin
- Permissions: All authenticated users can generate HARs
```

**Session Management**:
- Secure session cookies (httponly, secure, samesite)
- 8-hour session timeout
- Force re-authentication on sensitive operations

#### Network Security

**Firewall Rules**:
```
Allow: PHIVOLCS internal network only (e.g., 10.x.x.x/8)
Deny: All external traffic
Port: 443 (HTTPS) or 80 (HTTP if internal only)
```

**SSL/TLS** (if required):
- Use PHIVOLCS internal CA certificate
- Or self-signed certificate for internal use
- Force HTTPS redirect

#### Application Security

**Input Validation**:
- Sanitize all user inputs
- Validate summary table format
- Rate limiting: 100 requests/user/hour
- Maximum input size: 10 KB

**Output Security**:
- No user data stored (stateless)
- Generated HARs only shown to requesting user
- No caching of sensitive data

**Audit Logging**:
```
Log to database/file:
- User ID + timestamp
- Assessment ID
- Input summary table hash
- Generated HAR hash
- Success/failure status
```

#### Data Protection

**At Rest**:
- Schema file: Read-only permissions (644)
- Application code: Read-only (644)
- Logs: Append-only (600)

**In Transit**:
- Internal network only (no internet exposure)
- Optional: HTTPS with internal certificate

**Backup**:
- Daily backup of audit logs (if implemented)
- Schema version control via Git

### Deployment Process

#### For MIS/GEOMHAS Team

**Step 1: Server Provisioning**
```bash
# Create VM or physical server
# Assign internal IP address
# Configure firewall rules
# Install Ubuntu 22.04 LTS
```

**Step 2: System Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8+
sudo apt install -y python3 python3-pip python3-venv

# Install Nginx
sudo apt install -y nginx

# Install Git
sudo apt install -y git

# Install LDAP client libraries (if using LDAP auth)
sudo apt install -y libldap2-dev libsasl2-dev
```

**Step 3: Application Setup**
```bash
# Create application user
sudo useradd -m -s /bin/bash harauto
sudo su - harauto

# Clone repository
git clone /path/to/har-automation.git
cd har-automation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install flask gunicorn flask-login python-ldap

# Configure environment variables
cp .env.example .env
nano .env  # Edit with LDAP settings, secret key, etc.
```

**Step 4: Gunicorn Setup**
```bash
# Test application
gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app

# Create systemd service
sudo nano /etc/systemd/system/har-automation.service
```

**systemd service file**:
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
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --access-logfile /home/harauto/har-automation/logs/access.log \
    --error-logfile /home/harauto/har-automation/logs/error.log \
    wsgi:app

Restart=always

[Install]
WantedBy=multi-user.target
```

**Step 5: Nginx Configuration**
```bash
sudo nano /etc/nginx/sites-available/har-automation
```

**Nginx config**:
```nginx
server {
    listen 80;
    server_name har-automation.phivolcs.local;  # Internal DNS name

    # Optional: Redirect to HTTPS
    # return 301 https://$host$request_uri;

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

    # Static files
    location /static {
        alias /home/harauto/har-automation/app/static;
        expires 1d;
    }

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
}
```

**Step 6: Enable and Start Services**
```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/har-automation /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx

# Enable and start HAR automation service
sudo systemctl enable har-automation
sudo systemctl start har-automation
sudo systemctl status har-automation

# Check logs
sudo journalctl -u har-automation -f
```

**Step 7: Firewall Configuration**
```bash
# Allow only internal network
sudo ufw allow from 10.0.0.0/8 to any port 80
sudo ufw enable
```

### Monitoring & Maintenance

#### Health Checks

**Automated monitoring**:
```bash
# Check service status
systemctl status har-automation

# Check Nginx status
systemctl status nginx

# Check logs for errors
tail -f /home/harauto/har-automation/logs/error.log

# Monitor resource usage
htop
```

**Application health endpoint**:
```
GET /health
Response: {"status": "ok", "version": "1.0", "schema_loaded": true}
```

#### Log Rotation

**Configure logrotate**:
```bash
sudo nano /etc/logrotate.d/har-automation
```

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

#### Updates

**Deployment workflow**:
```bash
# As harauto user
cd /home/harauto/har-automation
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart har-automation

# Verify
curl http://localhost:8000/health
```

---

## MINIMAL WEB UI SPECIFICATION

### User Interface Requirements

#### Page 1: Login (if authentication enabled)
- Username field
- Password field
- "Login" button
- Error message display
- PHIVOLCS logo

#### Page 2: HAR Generator (Main Page)

**Layout**:
```
+----------------------------------------------------------+
| HAR Automation - PHIVOLCS                    [Logout]    |
+----------------------------------------------------------+
| Instructions:                                             |
| 1. Copy summary table from OHAS assessment page          |
| 2. Paste into the text area below                        |
| 3. Click "Generate HAR"                                  |
+----------------------------------------------------------+
| Summary Table Input:                                     |
| +------------------------------------------------------+ |
| | [Large text area for summary table]                  | |
| |                                                      | |
| |                                                      | |
| +------------------------------------------------------+ |
|                                                          |
| [Clear] [Generate HAR]                                   |
+----------------------------------------------------------+
| Generated HAR:                                           |
| +------------------------------------------------------+ |
| | [Display generated HAR with formatting]              | |
| |                                                      | |
| +------------------------------------------------------+ |
|                                                          |
| [Copy to Clipboard] [Download as .txt]                   |
+----------------------------------------------------------+
```

**Features**:
1. **Input validation**: Check if table format is valid before processing
2. **Loading indicator**: Show spinner while generating HAR
3. **Error handling**: Display clear error messages if generation fails
4. **Success feedback**: Highlight generated HAR and show success message
5. **Copy button**: One-click copy to clipboard
6. **Download button**: Save as .txt file
7. **Clear button**: Reset form
8. **Responsive design**: Works on desktop and tablet

### Frontend Technology

**Option B (Local) - Recommendation**:
- **HTML5**: Semantic markup
- **Bootstrap 5**: Responsive layout and components
- **Vanilla JavaScript**: No heavy frameworks needed
- **Fetch API**: AJAX requests to backend

**Total code**: ~300 lines (HTML + CSS + JS)

### User Experience Flow

1. User logs in (if auth enabled)
2. User copies summary table from OHAS
3. User pastes into text area
4. User clicks "Generate HAR"
5. Loading spinner appears
6. HAR appears in output area (2-3 seconds)
7. User copies HAR to clipboard
8. User pastes into OHAS or Word document
9. (Optional) User downloads as .txt file

**Average time**: 30 seconds per HAR

---

## IMPLEMENTATION ROADMAP

### Phase 1: Planning & Coordination (Week 1)

**Tasks**:
1. Present deployment options to MIS/GEOMHAS
2. Decide on deployment option (A or B)
3. If Option B: Confirm server availability and specifications
4. Gather LDAP/AD authentication details (if available)
5. Define access control requirements

**Deliverables**:
- Deployment decision document
- Server requirements confirmed
- Authentication strategy agreed

### Phase 2: Development (Week 2-3)

**Option A (Vercel)**:
- Days 1-2: Set up Next.js project and API
- Days 3-4: Develop frontend UI
- Days 5-6: Integration testing
- Day 7: Deploy to Vercel

**Option B (Local)**:
- Days 1-3: Develop Flask application
- Days 4-5: Implement authentication
- Days 6-8: Develop UI and testing
- Days 9-10: Create deployment scripts and documentation

### Phase 3: Deployment (Week 4)

**Option A**:
- Day 1: Deploy to Vercel
- Day 2: Test and verify
- Day 3: Present to stakeholders

**Option B**:
- Days 1-2: MIS provisions server
- Day 3: Install system dependencies
- Day 4: Deploy application
- Day 5: Configure Nginx and SSL
- Days 6-7: Testing and verification
- Day 8: User acceptance testing
- Day 9: Training for assessors
- Day 10: Go live

### Phase 4: Documentation & Training (Week 5)

**Deliverables**:
1. User manual (for assessors)
2. Administrator guide (for MIS)
3. Deployment documentation
4. Troubleshooting guide
5. Video tutorial (optional)
6. Training session for assessors

---

## RISK ASSESSMENT

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Server downtime | Low | High | Systemd auto-restart, monitoring |
| LDAP integration issues | Medium | Medium | Fallback to local auth, test early |
| Performance issues | Low | Medium | Load testing, horizontal scaling |
| Schema updates breaking app | Low | High | Version control, rollback procedure |
| Nginx misconfiguration | Low | Medium | Configuration validation, testing |

### Security Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Unauthorized access (Option A) | High | High | DO NOT use for production data |
| Data leakage | Low | High | Internal network only, auth required |
| Session hijacking | Low | Medium | Secure cookies, HTTPS, timeouts |
| Input injection | Low | Medium | Input validation, sanitization |
| Denial of service | Low | Low | Rate limiting, Nginx limits |

### Organizational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MIS resource constraints | Medium | High | Provide complete documentation |
| User adoption resistance | Low | Medium | Training, user-friendly UI |
| Maintenance burden | Medium | Medium | Automate updates, clear docs |
| Scope creep | Medium | Low | Stick to minimal UI spec |

---

## COST ANALYSIS

### Option A (Vercel)

**Development**: 10 hours × ₱2,000/hour = ₱20,000
**Hosting**: $0/month (free tier)
**Maintenance**: 2 hours/month × ₱2,000/hour = ₱4,000/month

**Total Year 1**: ₱68,000

### Option B (Local Server)

**Development**: 17 hours × ₱2,000/hour = ₱34,000
**Server**: ₱0 (existing infrastructure assumed)
**Maintenance**: 4 hours/month × ₱2,000/hour = ₱8,000/month

**Total Year 1**: ₱130,000

**Note**: Costs are estimates and assume developer rates. Actual costs may vary.

---

## RECOMMENDATIONS

### Primary Recommendation: Option B (Local Deployment)

**Reasons**:
1. ✅ **Security**: Data never leaves PHIVOLCS network
2. ✅ **Control**: Full control over infrastructure and security
3. ✅ **Integration**: Can integrate with PHIVOLCS LDAP/systems
4. ✅ **Compliance**: Meets government data security requirements
5. ✅ **Audit**: Can implement comprehensive logging
6. ✅ **Reliability**: No dependency on external services

### Secondary Recommendation: Option A for Demos Only

**Use cases**:
- Demonstrations to stakeholders
- Training outside PHIVOLCS network
- Proof-of-concept only
- Use with SAMPLE DATA only (never real assessments)

### Implementation Approach

1. **Immediate**: Start with Option B development
2. **Week 1**: Coordinate with MIS/GEOMHAS on server provisioning
3. **Week 2-3**: Develop Flask application
4. **Week 4**: Deploy to test server
5. **Week 5**: User acceptance testing
6. **Week 6**: Production deployment

7. **Optional**: Create Option A as demo/backup (separate timeline)

---

## SUCCESS METRICS

### Technical Metrics
- ✅ HAR generation success rate: >99%
- ✅ Average response time: <3 seconds
- ✅ System uptime: >99.5%
- ✅ Zero security incidents
- ✅ Concurrent users supported: 50+

### User Metrics
- ✅ User satisfaction: >80% (survey)
- ✅ Time to generate HAR: <1 minute
- ✅ Training completion: 100% of assessors
- ✅ Adoption rate: >50% within 3 months

### Business Metrics
- ✅ Reduction in HAR generation time: >70%
- ✅ Reduction in errors: >80%
- ✅ Increased assessor productivity: +30%

---

## APPENDIX A: SAMPLE CODE STRUCTURE

### Flask Application (app/__init__.py)

```python
from flask import Flask
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
```

### API Endpoint (app/routes/api.py)

```python
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import sys
from pathlib import Path

# Import decision engine
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'decision_engine'))
from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine

api_bp = Blueprint('api', __name__)

# Load schema once at startup
schema_loader = SchemaLoader()
schema = schema_loader.load()
engine = DecisionEngine(schema)

@api_bp.route('/generate', methods=['POST'])
@login_required
def generate_har():
    """Generate HAR from summary table."""
    try:
        # Get input
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

        # Log generation (optional)
        # log_har_generation(current_user.id, assessment_ids)

        return jsonify({'success': True, 'hars': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## APPENDIX B: SECURITY CHECKLIST

### Pre-Deployment Security Review

- [ ] All dependencies up to date
- [ ] No hardcoded credentials
- [ ] Environment variables for sensitive config
- [ ] Input validation on all endpoints
- [ ] Output encoding for XSS prevention
- [ ] CSRF protection enabled
- [ ] Secure session configuration
- [ ] HTTPS enforced (if applicable)
- [ ] Rate limiting implemented
- [ ] Audit logging enabled
- [ ] Error messages don't leak info
- [ ] File permissions correct (644 for files, 755 for dirs)
- [ ] Service runs as non-root user
- [ ] Firewall rules configured
- [ ] Backup procedure documented

---

## APPENDIX C: MAINTENANCE PROCEDURES

### Weekly Tasks
- [ ] Check application logs for errors
- [ ] Review access logs for anomalies
- [ ] Verify service status
- [ ] Check disk space

### Monthly Tasks
- [ ] Update Python dependencies
- [ ] Review security advisories
- [ ] Backup audit logs (if implemented)
- [ ] Performance review

### Quarterly Tasks
- [ ] Security audit
- [ ] User feedback review
- [ ] Schema updates (if new hazard rules)
- [ ] System updates

---

**END OF DEPLOYMENT PLAN**

**Contact for Questions**:
- Technical: [Developer contact]
- Infrastructure: MIS/GEOMHAS
- User Support: PHIVOLCS Hazard Assessment Team
