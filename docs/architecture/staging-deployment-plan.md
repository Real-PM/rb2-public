# RB2 Baseball - Staging Deployment Plan v2.0

**Date:** 2025-10-15
**Version:** 2.0 (Updated for Caddy)
**Target:** Staging Environment (192.168.10.94 - Minotaur)
**Reverse Proxy:** Caddy (Docker container)

---

## Overview

This document outlines the steps to deploy the RB2 Baseball reference website to the staging environment on Minotaur (192.168.10.94) for pre-production testing and validation. The server is already running Caddy in a Docker container hosting other websites.

---

## Prerequisites

### Infrastructure Requirements

**Server: Minotaur (192.168.10.94)**
- Linux server (Ubuntu 20.04+ or similar)
- Minimum: 2GB RAM, 2 CPU cores, 20GB disk
- Already has PostgreSQL, Redis, and Caddy running
- Docker and docker-compose installed

**Software:**
- Python 3.9+ with pip ✓
- systemd (for service management) ✓
- Docker with Caddy container (hosting-caddy-1) ✓
- Git ✓

**Database:**
- PostgreSQL 13+ server at 192.168.10.94:5432 ✓
- Database: `ootp_stage` (dedicated staging database)
- User: `ootp_etl` with full privileges ✓
- ETL should have populated all required tables ✓

**Redis:**
- Redis 6+ server at 192.168.10.94:6379 ✓
- Database: `/1` (staging namespace)
- No authentication required (internal network) ✓

---

## Existing Infrastructure

### Caddy Container Setup

**Container:** `hosting-caddy-1`
- **Image:** caddy:latest
- **Ports:** 80:80, 443:443
- **Docker Compose:** `/home/jayco/hosting/docker-compose.yml`
- **Caddyfile:** `/home/jayco/hosting/caddy/Caddyfile`

**Volume Mounts:**
- `/home/jayco/hosting/caddy/Caddyfile` → `/etc/caddy/Caddyfile`
- `/home/jayco/hosting/caddy/data` → `/data` (certificates)
- `/home/jayco/hosting/caddy/config` → `/config`
- `/home/jayco/hosting/static-site` → `/srv/static`

**Currently Hosted Sites:**
1. `realpm.net` - Static site + Flask API reverse proxy (172.17.0.1:5000)
2. `mail-rulez.com` - Static site
3. `docs.mail-rulez.com` - Documentation site

---

## Deployment Architecture

### Host-Based Flask App (Recommended)

```
┌─────────────────────────────────────────────────┐
│  Server: 192.168.10.94 (Minotaur)               │
│  ┌────────────────────────────────────────┐    │
│  │  PostgreSQL (port 5432)                │    │
│  │  - ootp_stage database                 │    │
│  └────────────────────────────────────────┘    │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │  Redis (port 6379)                     │    │
│  │  - DB 0: Dev                           │    │
│  │  - DB 1: Staging (RB2)                 │    │
│  │  - DB 2: Production                    │    │
│  └────────────────────────────────────────┘    │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │  RB2 Flask App (port 5002)             │    │
│  │  - Virtual env: /opt/rb2-public-public/venv   │    │
│  │  - systemd service: rb2-staging        │    │
│  │  - Working dir: /opt/rb2-public-public/web    │    │
│  │  - WSGI server: gunicorn               │    │
│  └────────────────────────────────────────┘    │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │  Docker: hosting-caddy-1               │    │
│  │  - Reverse proxy to 127.0.0.1:5002     │    │
│  │  - Handles SSL/TLS                     │    │
│  │  - Ports 80/443                        │    │
│  └────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

**Design Decision:** Run Flask app on host (not in Docker) because:
1. Matches existing pattern (realpm.net contact handler runs on host)
2. Simpler debugging and log access via journalctl
3. Easier systemd management
4. Direct filesystem access for images
5. Can containerize later if needed

---

## Deployment Steps

### 0. Configure Cloudflare DNS

**Goal:** Point `stage.rickybranch.com` to Minotaur server (192.168.10.94)

#### Option A: Public IP with Port Forwarding (Recommended for External Access)

If you want staging accessible from outside your network:

1. **Configure UniFi Port Forwarding:**
   - Log into UniFi Network Controller
   - Navigate to **Settings** → **Routing & Firewall** → **Port Forwarding**
   - Create new port forward rule:
     - **Name:** RB2 Staging HTTP/HTTPS
     - **Enabled:** ✓
     - **From:** Any / WAN
     - **Port:** 80,443
     - **Forward IP:** 192.168.10.94
     - **Forward Port:** 80,443
     - **Protocol:** TCP
   - Click **Apply Changes**

   **Note:** If you're already forwarding ports 80 and 443 to Minotaur for other sites (realpm.net, mail-rulez.com), this rule should already exist. Verify it's configured correctly.

2. **Verify/Configure UniFi Dynamic DNS (DDNS) for Cloudflare:**

   Since you're already using Cloudflare DDNS through UniFi for other domains:

   - Navigate to **Settings** → **Internet** → **WAN Networks**
   - Select your WAN connection
   - Scroll to **Dynamic DNS** section
   - Your existing Cloudflare DDNS should be configured with:
     - **Service:** cloudflare
     - **Hostname:** (your existing domain, e.g., realpm.net)
     - **API Token/Key:** [Your Cloudflare API credentials]

   **Important:** This DDNS configuration keeps Cloudflare updated with your current public IP. All subdomains under `rickybranch.com` will automatically point to the same IP.

3. **Add DNS A Record in Cloudflare:**
   - Log into Cloudflare dashboard
   - Select domain: `rickybranch.com`
   - Go to DNS → Records
   - Add new record:
     - **Type:** A
     - **Name:** stage
     - **IPv4 address:** @rickybranch.com (or your current public IP shown in UniFi)
     - **Proxy status:** OFF (orange cloud disabled) *Critical: Must be DNS-only for now*
     - **TTL:** Auto
   - Click **Save**

   **Note:** Since you already have Cloudflare DDNS configured in UniFi, the IP will be kept up-to-date automatically if it changes.

4. **Why Proxy OFF?**
   - Cloudflare proxy would terminate SSL at their edge
   - Let's Encrypt ACME challenges need direct access to your Caddy server
   - After SSL is working, you can optionally enable proxy for DDoS protection

5. **Verify Port Forwarding:**
   ```bash
   # From outside your network (use phone data or external server)
   curl -I http://[your-public-ip]

   # Should connect to Caddy on Minotaur
   # Or test with existing domain if already working:
   curl -I http://realpm.net
   ```

#### Option B: Internal DNS Only (For Testing/Development)

If you only need access from your local network:

1. **Skip Cloudflare DNS entirely** - use internal DNS or hosts file

2. **Add to /etc/hosts on your workstation:**
   ```bash
   sudo nano /etc/hosts
   # Add line:
   192.168.10.94  stage.rickybranch.com
   ```

3. **Note:** SSL/TLS won't work with this approach (Let's Encrypt requires public DNS)

#### Option C: Cloudflare Tunnel (Advanced, Zero Trust)

For secure external access without port forwarding:

1. **Install Cloudflare Tunnel on Minotaur:**
   ```bash
   # On Minotaur (192.168.10.94)
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
   sudo dpkg -i cloudflared.deb

   # Authenticate
   cloudflared tunnel login

   # Create tunnel
   cloudflared tunnel create rb2-staging

   # Configure tunnel
   nano ~/.cloudflared/config.yml
   ```

   **config.yml:**
   ```yaml
   tunnel: [tunnel-id-from-creation]
   credentials-file: /home/jayco/.cloudflared/[tunnel-id].json

   ingress:
     - hostname: stage.rickybranch.com
       service: http://localhost:5002
     - service: http_status:404
   ```

   ```bash
   # Route DNS
   cloudflared tunnel route dns rb2-staging stage.rickybranch.com

   # Run tunnel
   cloudflared tunnel run rb2-staging
   ```

2. **DNS is automatic** - Cloudflare Tunnel sets up CNAME automatically
3. **No Caddy needed** for SSL - Cloudflare handles it
4. **Alternative to port forwarding** - More secure

#### Recommended Approach for Staging: Option A

**Rationale:**
- Option A gives you real-world production-like setup
- Tests SSL/TLS certificate acquisition
- Caddy handles everything automatically
- Easy to transition to production VPS later
- Can enable Cloudflare proxy after SSL is working

**Verification After DNS Configuration:**

```bash
# Check DNS propagation (may take 5-10 minutes)
dig stage.rickybranch.com +short
nslookup stage.rickybranch.com

# Should return your public IP
# Or 192.168.10.94 if using hosts file

# Test connectivity
ping stage.rickybranch.com
curl http://stage.rickybranch.com
```

**Important:** Wait for DNS propagation (5-10 min) before proceeding to Caddy configuration.

---

### 1. Prepare Server Environment

```bash
# SSH to staging server
ssh jayco@192.168.10.94

# Create application directory
sudo mkdir -p /opt/rb2-public
sudo chown jayco:jayco /opt/rb2-public

# Optional: Create dedicated user for running app
# sudo useradd -r -s /bin/bash -d /opt/rb2-public rb2app
# sudo chown rb2app:rb2app /opt/rb2-public
# For now, we'll use jayco user for simplicity
```

### 2. Clone Repository

```bash
cd /opt/rb2-public

# Clone from development machine
git clone /mnt/hdd/PycharmProjects/rb2 .

# OR: Create clean deployment repository (recommended)
# See "Repository Cleanup" section below

# Checkout v1.0 tag (once created)
git checkout v1.0
```

### 3. Create Python Virtual Environment

```bash
cd /opt/rb2-public

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r web/web_requirements.txt

# Verify critical packages
pip list | grep -E "(Flask|SQLAlchemy|redis|psycopg2)"
```

**Expected packages:**
- Flask
- Flask-SQLAlchemy
- Flask-Caching
- redis
- psycopg2-binary

### 4. Configure Application

```bash
cd /opt/rb2-public/web

# Create .env file for staging
cat > .env << 'EOF'
FLASK_ENV=staging
FLASK_CONFIG=staging
DATABASE_URL=postgresql://ootp_etl:d0ghouse@localhost:5432/ootp_stage
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=your-staging-secret-key-change-this-to-random-string
EOF

chmod 600 .env
```

**Important:** The application uses `StagingConfig` from `web/app/config.py` which has:
- `CACHE_REDIS_URL = 'redis://192.168.10.94:6379/1'`
- `CACHE_KEY_PREFIX = 'rb2_staging:'`
- `CACHE_DEFAULT_TIMEOUT = 300`

Since we're on the same server, we can use `localhost` for connections.

### 5. Test Application Manually

```bash
cd /opt/rb2-public/web
source ../venv/bin/activate

# Test run (dev mode on port 5002)
FLASK_RUN_PORT=5002 python run.py

# Application should start on http://localhost:5002
# Check logs for errors
```

**Verify:**
- Application starts without errors
- Can connect to database
- Can connect to Redis
- Images serve correctly from `/opt/rb2-public/etl/data/images/`
- Front page loads
- Check URLs like:
  - http://localhost:5002/
  - http://localhost:5002/players/
  - http://localhost:5002/leagues/

Press `Ctrl+C` to stop.

### 6. Create systemd Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/rb2-staging.service
```

**Service file content:**

```ini
[Unit]
Description=RB2 Baseball Reference Website (Staging)
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=jayco
Group=jayco
WorkingDirectory=/opt/rb2-public-public/web
Environment="PATH=/opt/rb2-public-public/venv/bin"
Environment="FLASK_ENV=staging"
Environment="FLASK_CONFIG=staging"

# Gunicorn configuration
# --bind: Listen on localhost:5002
# --workers: Number of worker processes (2-4 x CPU cores recommended)
# --worker-class: Use sync workers (default, good for Flask)
# --timeout: Request timeout in seconds
# --access-logfile: Access log location (- for stdout/journald)
# --error-logfile: Error log location (- for stderr/journald)
# --log-level: Logging level
ExecStart=/opt/rb2-public-public/venv/bin/gunicorn \
    --bind 127.0.0.1:5002 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --access-logformat '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s' \
    'run:app'

# Restart policy
Restart=on-failure
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rb2-staging

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable rb2-staging

# Start service
sudo systemctl start rb2-staging

# Check status
sudo systemctl status rb2-staging

# View logs
sudo journalctl -u rb2-staging -f
```

### 7. Configure Caddy Reverse Proxy

**Edit Caddyfile on host:**

```bash
nano /home/jayco/hosting/caddy/Caddyfile
```

**Add RB2 configuration:**

```caddy
# Existing sites (realpm.net, mail-rulez.com, etc.)
# ... keep existing configurations ...

# RB2 Baseball Reference - Staging
stage.rickybranch.com {
    reverse_proxy 127.0.0.1:5002

    encode gzip

    header {
        X-Content-Type-Options nosniff
        X-Frame-Options SAMEORIGIN
        X-XSS-Protection "1; mode=block"
    }

    # Optional: Longer timeouts for slow queries
    @slow_queries {
        path /leaderboards/* /players/*/detailed
    }
    reverse_proxy @slow_queries 127.0.0.1:5002 {
        transport http {
            read_timeout 90s
        }
    }
}

# Optional: IP-based access for testing (before DNS setup)
192.168.10.94:8080 {
    reverse_proxy 127.0.0.1:5002
    encode gzip
}
```

**Reload Caddy:**

```bash
# Reload Caddy configuration
docker exec hosting-caddy-1 caddy reload --config /etc/caddy/Caddyfile

# OR restart the container
docker restart hosting-caddy-1

# Verify container is running
docker ps | grep caddy
```

**Notes:**
- Use `127.0.0.1` (not `localhost`) in Caddy config for Docker → host communication
- Docker container can reach host services via `127.0.0.1` on Linux
- Caddy automatically handles SSL/TLS with Let's Encrypt for domain names
- For IP-based access, SSL is not used (port 8080 in example)

### 8. Verify Deployment

**Check Services:**

```bash
# PostgreSQL
psql -h localhost -U ootp_etl -d ootp_stage -c "SELECT COUNT(*) FROM players_core;"

# Redis
redis-cli -n 1 PING

# Flask app
sudo systemctl status rb2-staging
sudo journalctl -u rb2-staging -n 20

# Caddy container
docker ps | grep caddy
docker logs hosting-caddy-1 --tail 20
```

**Test Website:**

```bash
# From server (direct to Flask)
curl http://localhost:5002/

# From server (through Caddy, if using IP-based config)
curl http://192.168.10.94:8080/

# From your workstation (if DNS configured)
curl http://rb2-staging.yourdomain.com/

# Check that reverse proxy headers are set
curl -I http://localhost:5002/ | grep -E "(Content-Encoding|X-Content-Type)"
```

**Browser Test:**
1. Navigate to staging URL
2. Verify front page loads with standings
3. Check Redis caching: refresh page multiple times, check journalctl for cache hits
4. Test navigation: players, teams, leaderboards, leagues
5. Test search functionality
6. Verify player images load
7. Check mobile responsive design

---

## Post-Deployment Validation

### Functional Testing Checklist

- [ ] **Front Page**
  - [ ] Standings display correctly
  - [ ] Featured players show images
  - [ ] Notable rookies listed
  - [ ] Born this week populated
  - [ ] Quick links work
  - [ ] League logos display

- [ ] **Player Pages**
  - [ ] Player list paginated
  - [ ] Player search works
  - [ ] Player detail shows stats
  - [ ] Player images display
  - [ ] Career batting/pitching tables render
  - [ ] League links functional

- [ ] **Team Pages**
  - [ ] Team list displays
  - [ ] Team detail page works
  - [ ] Franchise top players shown
  - [ ] Team roster loads

- [ ] **League Pages**
  - [ ] Leagues index lists all leagues
  - [ ] League home page shows standings
  - [ ] League logos display
  - [ ] Year summary pages work
  - [ ] Team stats tables display

- [ ] **Leaderboards**
  - [ ] Career leaders load
  - [ ] Active players filter works
  - [ ] Single-season records display
  - [ ] Yearly leaders by stat

- [ ] **Search & Navigation**
  - [ ] Search autocomplete works
  - [ ] Full search results page
  - [ ] Breadcrumbs on all pages
  - [ ] Mobile menu functional
  - [ ] All navigation links work

### Performance Testing

```bash
# Test page load times (from server)
time curl -s http://localhost:5002/ > /dev/null
time curl -s http://localhost:5002/players/12345 > /dev/null

# Check Redis cache hit rate
redis-cli -n 1 INFO stats | grep keyspace

# Monitor cache keys
redis-cli -n 1 KEYS "rb2_staging:*" | wc -l

# Check memory usage
redis-cli -n 1 INFO memory | grep used_memory_human
```

**Expected Performance (Phase 3 optimizations):**
- Front page (cached): <100ms (99.8% improvement vs baseline)
- Front page (uncached): <3s
- Player detail: <2-3s
- Team pages: <2s
- Leaderboards: <1s

### Monitoring

```bash
# Application logs (follow)
sudo journalctl -u rb2-staging -f

# Application logs (last 100 lines)
sudo journalctl -u rb2-staging -n 100

# Caddy logs
docker logs hosting-caddy-1 -f

# System resources
htop

# Check disk usage (especially /etl/data/images)
du -sh /opt/rb2-public/etl/data/images/

# Check Redis memory
redis-cli -n 1 INFO memory
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u rb2-staging -n 50

# Common issues:
# 1. Database connection
psql -h localhost -U ootp_etl -d ootp_stage -c "SELECT 1;"

# 2. Redis connection
redis-cli -n 1 PING

# 3. Virtual environment
/opt/rb2-public/venv/bin/python --version
/opt/rb2-public/venv/bin/pip list | grep Flask

# 4. Permissions
ls -la /opt/rb2-public/web/
ls -la /opt/rb2-public/etl/data/images/

# 5. Port conflict
sudo netstat -tlnp | grep 5002
```

### Caddy Not Proxying

```bash
# Check Caddy config syntax
docker exec hosting-caddy-1 caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy
docker exec hosting-caddy-1 caddy reload --config /etc/caddy/Caddyfile

# Check Caddy logs for errors
docker logs hosting-caddy-1 --tail 50 | grep -i error

# Test direct connection to Flask
curl http://127.0.0.1:5002/

# Check from inside Caddy container
docker exec hosting-caddy-1 wget -O- http://127.0.0.1:5002/
```

### Slow Page Loads

```bash
# Check Redis connection
redis-cli -n 1 KEYS "rb2_staging:*"

# Clear Redis cache (staging namespace only)
redis-cli -n 1 FLUSHDB

# Check database query performance
# Enable SQLAlchemy echo in staging config temporarily

# Monitor application logs during page load
sudo journalctl -u rb2-staging -f
```

### Images Not Loading

```bash
# Verify image directory exists
ls -la /opt/rb2-public/etl/data/images/players/ | head

# Check Flask routes
curl -I http://localhost:5002/players/image/12345

# Check permissions
sudo chmod -R 755 /opt/rb2-public/etl/data/images/

# Verify image path in config
grep -r "image" /opt/rb2-public/web/app/config.py
```

### SSL/TLS Issues (Domain-Based Access)

```bash
# Check Caddy certificate status
docker exec hosting-caddy-1 caddy list-certificates

# Force certificate renewal (if needed)
# Remove and restart Caddy - it will auto-renew
docker restart hosting-caddy-1

# Check Caddy logs for ACME/Let's Encrypt errors
docker logs hosting-caddy-1 | grep -i acme
```

---

## Rollback Procedure

If deployment fails:

```bash
# Stop service
sudo systemctl stop rb2-staging

# Rollback code
cd /opt/rb2-public
git checkout previous-version  # Or specific commit/tag

# Reinstall dependencies (if needed)
source venv/bin/activate
pip install -r web/web_requirements.txt

# Restart service
sudo systemctl start rb2-staging

# Verify
sudo systemctl status rb2-staging
sudo journalctl -u rb2-staging -n 20
```

---

## Repository Cleanup (Recommended)

### Create Clean Deployment Repository

Before deploying, consider creating a clean repository without development cruft:

**Files/Directories to EXCLUDE:**
```
# Development artifacts
/profile_*.py
/test_*.py
/CASCADE_EXPLOSION_DIAGRAM.txt
/continuity.txt
/PERFORMANCE_INVESTIGATION_REPORT.md
/tree_output.txt

# Legacy code
/false_start/
/scripts/

# Development configs
/.idea/
/.claude/

# Documentation sprawl
/docs/*.backup
/docs/newspaper-brainstorm.md
/docs/sqlalchemy-architecture-recommendation.md
/docs/WEB-IMPLEMENTATION-PLAN.md
/docs/WEBSITE-SPECS.MD
/docs/ETL-CHANGE-DETECTION.MD
/docs/phase*.md
/docs/baseline_*.py
/docs/collect_*.py
/docs/automated_baseline.sh
/docs/performance_baseline.csv
```

**Files to INCLUDE (production-relevant):**
```
/web/                           # Complete Flask application
/etl/                           # ETL scripts (data/ dir excluded by .gitignore)
/docs/
  - staging-deployment-plan.md  # This file
  - DATA-MODEL.MD               # Database schema reference
  - OVERVIEW.MD                 # Project overview
  - CLAUDE.MD                   # Project quick reference
  - optimization-strategy.md    # Performance documentation
  - backlog-active.md           # Current status
/.gitignore
/requirements.txt
/README.md
```

**Create clean repository:**
```bash
# On development machine
cd /mnt/hdd/PycharmProjects
git clone rb2 rb2-deploy
cd rb2-deploy

# Remove development artifacts
rm -rf false_start/ scripts/ .idea/ .claude/
rm profile_*.py test_*.py CASCADE_EXPLOSION_DIAGRAM.txt continuity.txt
rm PERFORMANCE_INVESTIGATION_REPORT.md tree_output.txt

# Clean docs directory
cd docs
rm *.backup newspaper-brainstorm.md sqlalchemy-architecture-recommendation.md
rm WEB-IMPLEMENTATION-PLAN.md WEBSITE-SPECS.MD ETL-CHANGE-DETECTION.MD
rm phase*.md baseline_*.py collect_*.py automated_baseline.sh performance_baseline.csv

# Commit cleanup
git add -A
git commit -m "Clean repository for v1.0 deployment"
git tag v1.0

# Push to remote (if using git remote)
git push origin v1.0
```

---

## Production Deployment Prep

After successful staging validation:

1. **Domain Configuration**
   - Register domain or subdomain for RB2
   - Point DNS to 192.168.10.94
   - Update Caddyfile with production domain
   - Caddy will automatically handle SSL/TLS

2. **Production Service**
   - Create `/etc/systemd/system/rb2-production.service`
   - Use port 5003 (different from staging)
   - Set `FLASK_CONFIG=production`
   - Use Redis DB 2 (`redis://localhost:6379/2`)

3. **Production Caddyfile Entry**
   ```caddy
   rb2.yourdomain.com {
       reverse_proxy 127.0.0.1:5003
       encode gzip
       header {
           X-Content-Type-Options nosniff
           X-Frame-Options SAMEORIGIN
           X-XSS-Protection "1; mode=block"
           Strict-Transport-Security "max-age=31536000; includeSubDomains"
       }
   }
   ```

4. **Production Checklist**
   - [ ] Use production database (or dedicated read replica)
   - [ ] Configure log rotation for journalctl
   - [ ] Set up automated backups (database)
   - [ ] Configure monitoring (optional: Uptime Kuma, etc.)
   - [ ] Document production URLs and credentials
   - [ ] Create production .env with strong SECRET_KEY
   - [ ] Test SSL/TLS certificate

---

## Maintenance

### Update Application

```bash
cd /opt/rb2-public
git pull
source venv/bin/activate
pip install -r web/web_requirements.txt
sudo systemctl restart rb2-staging
sudo journalctl -u rb2-staging -f
```

### Clear Cache

```bash
# Clear staging cache only (doesn't affect other Redis DBs)
redis-cli -n 1 FLUSHDB

# Or programmatically via Flask shell
cd /opt/rb2-public/web
source ../venv/bin/activate
python -c "from app import create_app; app = create_app('staging'); with app.app_context(): app.extensions['cache'].clear()"
```

### View Logs

```bash
# Flask application logs
sudo journalctl -u rb2-staging -n 100        # Last 100 lines
sudo journalctl -u rb2-staging -f            # Follow live
sudo journalctl -u rb2-staging --since "2025-10-15 10:00:00"

# Caddy logs
docker logs hosting-caddy-1 -f
docker logs hosting-caddy-1 --tail 100

# Combined view (application + caddy)
sudo journalctl -u rb2-staging -f & docker logs hosting-caddy-1 -f
```

### Restart Services

```bash
# Restart Flask app
sudo systemctl restart rb2-staging

# Reload Caddy config (no downtime)
docker exec hosting-caddy-1 caddy reload --config /etc/caddy/Caddyfile

# Restart Caddy container (brief downtime for all sites)
docker restart hosting-caddy-1
```

---

## Success Criteria

Staging deployment is successful when:

- ✅ Application starts and runs without errors
- ✅ Database connectivity verified (localhost:5432)
- ✅ Redis caching functional (cache hit rate >80%)
- ✅ All pages load successfully
- ✅ Search functionality works
- ✅ Images display correctly
- ✅ Performance meets targets (<3s uncached, <100ms cached)
- ✅ No errors in application logs
- ✅ Mobile responsive design works
- ✅ Caddy reverse proxy working
- ✅ SSL/TLS configured (if using domain)

---

## Next Steps After Staging

1. **User Acceptance Testing** - Test all features thoroughly
2. **Performance Monitoring** - Track metrics for 24-48 hours
3. **Bug Fixes** - Address any issues found in staging
4. **Production Planning** - Prepare production deployment
5. **Go-Live Date** - Schedule production deployment

**Estimated Staging Testing Period:** 1-3 days

---

## Additional Notes

### Port Assignments
- **5000**: realpm.net Flask contact handler
- **5001**: mail-rulez.com Docker container
- **5002**: RB2 staging
- **5003**: (reserved for RB2 production)

### Redis Database Assignments
- **DB 0**: Development/shared
- **DB 1**: RB2 Staging
- **DB 2**: RB2 Production

### Caddy Volume Mounts
- Caddyfile changes persist to `/home/jayco/hosting/caddy/Caddyfile`
- Certificates stored in `/home/jayco/hosting/caddy/data`
- Config stored in `/home/jayco/hosting/caddy/config`

### Security Notes
- Staging environment is on internal network (192.168.10.x)
- Consider firewall rules if exposing to internet
- Use strong SECRET_KEY in production
- Keep Flask in production mode (never debug=True in production)
