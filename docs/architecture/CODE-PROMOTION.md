# RB2 Baseball - Code Promotion & Release Management

**Date:** 2025-10-15
**Version:** 1.0
**Strategy:** Tag-Based Deployment with Semantic Versioning

---

## Overview

This document defines the code promotion process for the RB2 Baseball reference website, from development through staging to production deployment.

**Key Principles:**
- Single source of truth: `master` branch
- Tag-based releases for traceability
- Same code deployed to staging and production
- Simple workflow optimized for solo development
- Clear rollback path via git tags

---

## Git Workflow Strategy

### Branch Structure

**Primary Branch:**
- `master` (or `main`) - Production-ready code, always deployable

**Optional Branches:**
- `develop` - Experimental features, major refactors (optional)
- `feature/*` - Feature branches (e.g., `feature/add-awards-page`)
- `hotfix/*` - Critical bug fixes (e.g., `hotfix/image-links`)

**Tag Strategy:**
- Semantic versioning: `vMAJOR.MINOR.PATCH`
- Tags represent deployable releases
- Example: `v1.0.0`, `v1.1.0`, `v1.0.1`

### Semantic Versioning

**MAJOR.MINOR.PATCH (e.g., v1.2.3)**

- **MAJOR** (1.x.x) - Breaking changes, major new features, database schema changes
- **MINOR** (x.1.x) - New features, enhancements (backward compatible)
- **PATCH** (x.x.1) - Bug fixes, small improvements (backward compatible)

**Examples:**
- `v1.0.0` - Initial production release
- `v1.1.0` - Add awards page feature
- `v1.0.1` - Fix broken image links (hotfix)
- `v2.0.0` - Major redesign with new database schema

---

## Development Workflow

### 1. Local Development

**For small changes (direct to master):**
```bash
cd /mnt/hdd/PycharmProjects/rb2

# Ensure you're on master and up to date
git checkout master
git pull origin master

# Make changes
vim web/app/routes/players.py

# Test locally
cd web
FLASK_RUN_PORT=5000 python run.py
# Test in browser: http://localhost:5000

# Commit changes
git add .
git commit -m "Fix: Correct player image path resolution"
git push origin master
```

**For larger features (use feature branch):**
```bash
# Create feature branch
git checkout -b feature/add-awards-page

# Make changes and test
# ... development work ...

# Commit frequently
git add .
git commit -m "Add awards data models"
git commit -m "Create awards page template"
git commit -m "Wire up awards routes"

# Merge back to master when complete
git checkout master
git merge feature/add-awards-page

# Push to remote
git push origin master

# Optional: Delete feature branch
git branch -d feature/add-awards-page
```

### 2. Testing Before Release

**Pre-release checklist:**
- [ ] All features work locally
- [ ] No console errors in browser
- [ ] Database queries optimized (no N+1)
- [ ] New dependencies added to `web/requirements.txt`
- [ ] No hardcoded credentials or secrets
- [ ] Code reviewed (even if self-review)
- [ ] Documentation updated if needed

---

## Release Process

### Creating a Release

**1. Decide on version number:**
```bash
# Check current version
git tag -l | tail -5

# Determine next version based on changes
# - Bug fixes only? → Increment PATCH (v1.0.1)
# - New features? → Increment MINOR (v1.1.0)
# - Breaking changes? → Increment MAJOR (v2.0.0)
```

**2. Create and push tag:**
```bash
# Ensure master is clean and up to date
git checkout master
git pull origin master

# Create annotated tag with message
git tag -a v1.1.0 -m "Release v1.1.0 - Add awards page and fix league standings"

# Push tag to remote
git push origin v1.1.0

# View tag details
git show v1.1.0
```

**3. Document the release:**
```bash
# Optional: Create CHANGELOG.md entry
cat >> docs/CHANGELOG.md << 'EOF'

## [1.1.0] - 2025-10-15

### Added
- Awards page with career and season awards
- League standings sorting improvements

### Fixed
- League standings display for division_id=0
- Player image path resolution

### Changed
- Improved Redis cache key structure
EOF
```

---

## Staging Deployment

### Environment Setup

**Staging environment:**
- **Server:** Minotaur (192.168.10.94)
- **Directory:** `/opt/rb2-staging/`
- **Port:** 5002
- **Redis DB:** 1
- **Systemd service:** `rb2-staging.service`
- **URL:** http://192.168.10.94:8080 (or staging domain)

### Initial Staging Setup (One-Time)

```bash
# SSH to Minotaur
ssh jayco@192.168.10.94

# Create staging directory
sudo mkdir -p /opt/rb2-staging
sudo chown jayco:jayco /opt/rb2-staging

# Clone repository
cd /opt/rb2-staging
git clone /mnt/hdd/PycharmProjects/rb2 .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r web/requirements.txt

# Create staging .env file
cat > web/.env << 'EOF'
FLASK_ENV=staging
FLASK_CONFIG=staging
FLASK_RUN_PORT=5002
DATABASE_URL=postgresql://ootp_etl:d0ghouse@localhost:5432/ootp_dev
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=staging-secret-key-change-this
EOF
chmod 600 web/.env

# Create systemd service (see staging-deployment-plan.md)
# Configure Caddy reverse proxy (see staging-deployment-plan.md)
```

### Deploying to Staging

**Step-by-step deployment:**

```bash
# 1. SSH to Minotaur
ssh jayco@192.168.10.94

# 2. Navigate to staging directory
cd /opt/rb2-staging

# 3. Fetch latest tags
git fetch --tags

# 4. Check current version
git describe --tags

# 5. Checkout new version tag
git checkout v1.1.0

# 6. Update dependencies (if requirements.txt changed)
source venv/bin/activate
pip install -r web/requirements.txt

# 7. Restart service
sudo systemctl restart rb2-staging

# 8. Verify service started successfully
sudo systemctl status rb2-staging
sudo journalctl -u rb2-staging -n 50

# 9. Test application
curl http://localhost:5002/
```

**Quick deployment script:**
```bash
# Save as: /opt/rb2-staging/deploy.sh
#!/bin/bash
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh v1.1.0"
    exit 1
fi

echo "Deploying $VERSION to staging..."
git fetch --tags
git checkout $VERSION
source venv/bin/activate
pip install -r web/requirements.txt
sudo systemctl restart rb2-staging
echo "Deployment complete. Checking status..."
sudo systemctl status rb2-staging --no-pager
```

### Staging Testing Checklist

After deployment to staging, perform these tests:

- [ ] **Smoke Tests**
  - [ ] Application starts without errors
  - [ ] Front page loads
  - [ ] Database connection works
  - [ ] Redis caching works
  - [ ] No errors in logs: `sudo journalctl -u rb2-staging -n 100`

- [ ] **Functional Tests** (see staging-deployment-plan.md for full list)
  - [ ] Players pages work
  - [ ] Teams pages work
  - [ ] Leagues pages work
  - [ ] Leaderboards work
  - [ ] Search functionality works
  - [ ] Images display correctly
  - [ ] Mobile responsive design

- [ ] **Performance Tests**
  - [ ] Front page (cached) < 100ms
  - [ ] Player detail < 3s
  - [ ] Check Redis cache hit rate: `redis-cli -n 1 INFO stats`

- [ ] **Regression Tests**
  - [ ] Test previously working features
  - [ ] Verify no broken links
  - [ ] Check for console errors (browser dev tools)

**Testing period:** 1-3 days minimum for staging validation

---

## Production Deployment

### Environment Setup

**Production environment:**
- **Server:** Minotaur (192.168.10.94)
- **Directory:** `/opt/rb2-production/`
- **Port:** 5003
- **Redis DB:** 2
- **Systemd service:** `rb2-production.service`
- **URL:** http://rb2.yourdomain.com (with SSL via Caddy)

### Initial Production Setup (One-Time)

```bash
# SSH to Minotaur
ssh jayco@192.168.10.94

# Create production directory
sudo mkdir -p /opt/rb2-production
sudo chown jayco:jayco /opt/rb2-production

# Clone repository (or copy from staging)
cd /opt/rb2-production
git clone /mnt/hdd/PycharmProjects/rb2 .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r web/requirements.txt

# Create production .env file
cat > web/.env << 'EOF'
FLASK_ENV=production
FLASK_CONFIG=production
FLASK_RUN_PORT=5003
DATABASE_URL=postgresql://ootp_etl:d0ghouse@localhost:5432/ootp_dev
REDIS_URL=redis://localhost:6379/2
SECRET_KEY=$(openssl rand -base64 32)
EOF
chmod 600 web/.env

# Create systemd service
sudo nano /etc/systemd/system/rb2-production.service
```

**Production systemd service:**
```ini
[Unit]
Description=RB2 Baseball Reference Website (Production)
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=jayco
Group=jayco
WorkingDirectory=/opt/rb2-production/web
Environment="PATH=/opt/rb2-production/venv/bin"
Environment="FLASK_ENV=production"
Environment="FLASK_CONFIG=production"
Environment="FLASK_RUN_PORT=5003"
ExecStart=/opt/rb2-production/venv/bin/python /opt/rb2-production/web/run.py

Restart=on-failure
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=rb2-production

[Install]
WantedBy=multi-user.target
```

**Production Caddyfile entry:**
```caddy
# Add to /home/jayco/hosting/caddy/Caddyfile

rb2.yourdomain.com {
    reverse_proxy 127.0.0.1:5003

    encode gzip

    header {
        X-Content-Type-Options nosniff
        X-Frame-Options SAMEORIGIN
        X-XSS-Protection "1; mode=block"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }

    # Longer timeouts for slow queries
    @slow_queries {
        path /leaderboards/* /players/*/detailed
    }
    reverse_proxy @slow_queries 127.0.0.1:5003 {
        transport http {
            read_timeout 90s
        }
    }
}
```

### Deploying to Production

**Production deployment checklist:**

- [ ] **Pre-Deployment**
  - [ ] Staging validation complete (all tests passed)
  - [ ] Tag deployed to staging and tested for 1-3 days
  - [ ] Database backup created (if schema changes)
  - [ ] Redis production cache cleared (if cache structure changed)
  - [ ] Announcement/maintenance window scheduled (if needed)

- [ ] **Deployment Steps**
  ```bash
  # 1. SSH to Minotaur
  ssh jayco@192.168.10.94

  # 2. Navigate to production directory
  cd /opt/rb2-production

  # 3. Record current version (for rollback)
  git describe --tags > /tmp/rb2-previous-version.txt
  echo "Previous version: $(cat /tmp/rb2-previous-version.txt)"

  # 4. Fetch latest tags
  git fetch --tags

  # 5. Checkout new version (SAME tag as staging)
  git checkout v1.1.0

  # 6. Update dependencies
  source venv/bin/activate
  pip install -r web/requirements.txt

  # 7. Clear production Redis cache (if needed)
  redis-cli -n 2 FLUSHDB

  # 8. Restart production service
  sudo systemctl restart rb2-production

  # 9. Verify service started
  sudo systemctl status rb2-production
  sudo journalctl -u rb2-production -n 50

  # 10. Test application
  curl http://localhost:5003/
  curl https://rb2.yourdomain.com/
  ```

- [ ] **Post-Deployment Verification**
  - [ ] Application responds on production URL
  - [ ] SSL certificate valid
  - [ ] Front page loads correctly
  - [ ] No errors in logs
  - [ ] Test critical user paths
  - [ ] Monitor for 15-30 minutes

**Production deployment script:**
```bash
#!/bin/bash
# Save as: /opt/rb2-production/deploy.sh
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh v1.1.0"
    exit 1
fi

echo "=== PRODUCTION DEPLOYMENT ==="
echo "Version: $VERSION"
echo "Current version: $(git describe --tags)"
echo ""
read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo "Recording current version for rollback..."
git describe --tags > /tmp/rb2-previous-version.txt

echo "Fetching tags..."
git fetch --tags

echo "Checking out $VERSION..."
git checkout $VERSION

echo "Updating dependencies..."
source venv/bin/activate
pip install -r web/requirements.txt

echo "Restarting production service..."
sudo systemctl restart rb2-production

echo "Waiting 5 seconds..."
sleep 5

echo "Checking service status..."
sudo systemctl status rb2-production --no-pager

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo "Version deployed: $VERSION"
echo "Previous version: $(cat /tmp/rb2-previous-version.txt)"
echo "Monitor logs: sudo journalctl -u rb2-production -f"
```

---

## Rollback Procedures

### When to Rollback

Rollback immediately if:
- Application won't start after deployment
- Critical functionality broken
- Severe performance degradation
- Security vulnerability introduced
- Database errors preventing access

### Staging Rollback

```bash
# SSH to Minotaur
ssh jayco@192.168.10.94
cd /opt/rb2-staging

# Check available versions
git tag -l

# Rollback to previous version
git checkout v1.0.0

# Restart service
sudo systemctl restart rb2-staging

# Verify
sudo systemctl status rb2-staging
curl http://localhost:5002/
```

### Production Rollback

**Emergency rollback (< 5 minutes):**
```bash
# SSH to Minotaur
ssh jayco@192.168.10.94
cd /opt/rb2-production

# Use recorded previous version
PREVIOUS_VERSION=$(cat /tmp/rb2-previous-version.txt)
echo "Rolling back to: $PREVIOUS_VERSION"

# Checkout previous version
git checkout $PREVIOUS_VERSION

# Restart service
sudo systemctl restart rb2-production

# Verify immediately
sudo systemctl status rb2-production
curl http://localhost:5003/
curl https://rb2.yourdomain.com/

# Monitor logs
sudo journalctl -u rb2-production -f
```

**Post-rollback actions:**
1. Announce rollback to users (if public-facing)
2. Document the issue that caused rollback
3. Clear production Redis cache if data structure changed
4. Test thoroughly on staging before attempting re-deployment
5. Create hotfix if needed

---

## Hotfix Process

### When to Use Hotfix

Use hotfix process for:
- Critical bugs in production
- Security vulnerabilities
- Data corruption issues
- Urgent performance problems

**DO NOT use hotfix for:**
- New features
- Non-critical bugs (wait for next release)
- Cosmetic changes

### Hotfix Workflow

```bash
# 1. Identify the production version with the bug
cd /mnt/hdd/PycharmProjects/rb2
git checkout v1.0.0  # Current production version

# 2. Create hotfix branch
git checkout -b hotfix/fix-image-links

# 3. Make minimal fix
vim web/app/routes/players.py
# Fix only the critical issue - no other changes!

# 4. Test locally
cd web
FLASK_RUN_PORT=5000 python run.py

# 5. Commit fix
git add .
git commit -m "Hotfix: Fix broken player image links"

# 6. Merge to master
git checkout master
git merge hotfix/fix-image-links

# 7. Create hotfix tag (increment PATCH version)
git tag -a v1.0.1 -m "Hotfix v1.0.1 - Fix broken player image links"
git push origin v1.0.1

# 8. Deploy to staging for quick validation
ssh jayco@192.168.10.94
cd /opt/rb2-staging
git fetch --tags
git checkout v1.0.1
sudo systemctl restart rb2-staging

# 9. Quick smoke test on staging (15-30 minutes)

# 10. Deploy to production
cd /opt/rb2-production
git fetch --tags
git checkout v1.0.1
sudo systemctl restart rb2-production

# 11. Verify fix in production

# 12. Clean up hotfix branch
git branch -d hotfix/fix-image-links
```

### Hotfix Best Practices

- **Keep it minimal** - Only fix the critical issue
- **Test quickly** - Don't wait days, but don't skip staging
- **Document** - Update CHANGELOG.md with hotfix
- **Communicate** - Announce fix to users if needed
- **Follow up** - Ensure fix is in next regular release

---

## Environment Comparison

| Aspect | Development | Staging | Production |
|--------|-------------|---------|------------|
| **Location** | Local machine | Minotaur | Minotaur |
| **Directory** | `/mnt/hdd/PycharmProjects/rb2` | `/opt/rb2-staging` | `/opt/rb2-production` |
| **Branch/Tag** | `master` (latest) | Tagged release | Same tag as staging |
| **Port** | 5000 | 5002 | 5003 |
| **Redis DB** | 0 (or 1) | 1 | 2 |
| **Database** | `ootp_dev` | `ootp_dev` | `ootp_dev` (consider read replica) |
| **URL** | `localhost:5000` | `192.168.10.94:8080` | `rb2.yourdomain.com` |
| **SSL** | No | Optional | Yes (Caddy auto) |
| **Debug Mode** | Yes | No | No |
| **Cache TTL** | Short (60s) | Normal (300s) | Long (600s) |
| **Logging** | Console | journalctl | journalctl + monitoring |
| **Git State** | Working changes | Clean tag | Clean tag |

---

## Version History

### Tracking Versions

**View all releases:**
```bash
git tag -l
```

**View release details:**
```bash
git show v1.0.0
```

**View changes between versions:**
```bash
# See what changed between v1.0.0 and v1.1.0
git log v1.0.0..v1.1.0 --oneline

# See file diffs
git diff v1.0.0..v1.1.0
```

**Current deployed versions:**
```bash
# Staging
ssh jayco@192.168.10.94 "cd /opt/rb2-staging && git describe --tags"

# Production
ssh jayco@192.168.10.94 "cd /opt/rb2-production && git describe --tags"
```

### CHANGELOG.md

Maintain a changelog for user-facing changes:

```markdown
# Changelog

All notable changes to RB2 Baseball Reference website will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Features in development

## [1.1.0] - 2025-10-20
### Added
- Awards page with career and season awards
- League standings sorting improvements

### Fixed
- League standings display for division_id=0
- Player image path resolution

### Changed
- Improved Redis cache key structure

## [1.0.1] - 2025-10-16
### Fixed
- Broken player image links on detail pages

## [1.0.0] - 2025-10-15
### Added
- Initial production release
- Players pages (list, detail)
- Teams pages (list, detail, roster)
- Leagues pages (index, home, year summary)
- Leaderboards (career, season, yearly)
- Search functionality
- Redis caching (99.8% performance improvement)
- Mobile responsive design

[Unreleased]: https://github.com/yourrepo/rb2/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/yourrepo/rb2/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/yourrepo/rb2/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/yourrepo/rb2/releases/tag/v1.0.0
```

---

## Quick Reference Commands

### Deployment Commands

```bash
# Deploy to staging
ssh jayco@192.168.10.94 "cd /opt/rb2-staging && git fetch --tags && git checkout v1.1.0 && source venv/bin/activate && pip install -r web/requirements.txt && sudo systemctl restart rb2-staging"

# Deploy to production
ssh jayco@192.168.10.94 "cd /opt/rb2-production && git fetch --tags && git checkout v1.1.0 && source venv/bin/activate && pip install -r web/requirements.txt && sudo systemctl restart rb2-production"

# Check deployed versions
ssh jayco@192.168.10.94 "echo 'Staging:' && cd /opt/rb2-staging && git describe --tags && echo 'Production:' && cd /opt/rb2-production && git describe --tags"
```

### Service Management

```bash
# Restart services
sudo systemctl restart rb2-staging
sudo systemctl restart rb2-production

# View logs
sudo journalctl -u rb2-staging -f
sudo journalctl -u rb2-production -f

# Check status
sudo systemctl status rb2-staging
sudo systemctl status rb2-production
```

### Cache Management

```bash
# Clear staging cache
redis-cli -n 1 FLUSHDB

# Clear production cache
redis-cli -n 2 FLUSHDB

# Check cache stats
redis-cli -n 1 INFO stats | grep keyspace
redis-cli -n 2 INFO stats | grep keyspace
```

---

## Troubleshooting Common Issues

### Issue: Tag already exists

**Error:** `fatal: tag 'v1.0.0' already exists`

**Solution:**
```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag (be careful!)
git push --delete origin v1.0.0

# Recreate tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Issue: Deployment shows old version

**Problem:** Deployed new tag but application shows old code

**Solution:**
```bash
# Force refresh git state
cd /opt/rb2-staging
git fetch --tags --force
git checkout v1.1.0 --force

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Restart service
sudo systemctl restart rb2-staging
```

### Issue: Service won't start after deployment

**Problem:** `sudo systemctl status rb2-staging` shows failed

**Solution:**
```bash
# Check logs for error
sudo journalctl -u rb2-staging -n 100

# Common issues:
# 1. Missing dependencies
source venv/bin/activate
pip install -r web/requirements.txt

# 2. Database connection
psql -h localhost -U ootp_etl -d ootp_dev -c "SELECT 1;"

# 3. Redis connection
redis-cli -n 1 PING

# 4. Port conflict
sudo netstat -tlnp | grep 5002

# 5. Permissions
ls -la web/
```

---

## Best Practices

### Do's ✅

- ✅ Always test on staging before production
- ✅ Use semantic versioning for tags
- ✅ Document changes in commits and CHANGELOG
- ✅ Deploy same tag to staging and production
- ✅ Keep deployment scripts simple
- ✅ Monitor logs after deployment
- ✅ Record previous version before production deployment
- ✅ Clear cache when data structures change

### Don'ts ❌

- ❌ Never skip staging validation
- ❌ Don't deploy untagged commits to production
- ❌ Don't make changes directly on server
- ❌ Don't deploy during peak usage hours (if avoidable)
- ❌ Don't skip the pre-deployment checklist
- ❌ Don't forget to update requirements.txt
- ❌ Don't commit secrets or credentials
- ❌ Don't deploy on Friday afternoon (Murphy's Law!)

---

## Appendix: Complete Deployment Example

### Scenario: Deploy v1.1.0 with new awards feature

**Step 1: Complete development**
```bash
cd /mnt/hdd/PycharmProjects/rb2
git checkout master
# ... development work completed ...
git add .
git commit -m "Add awards page and fix league standings"
git push origin master
```

**Step 2: Create release**
```bash
git tag -a v1.1.0 -m "Release v1.1.0 - Awards page and league fixes"
git push origin v1.1.0

# Update changelog
vim docs/CHANGELOG.md
git add docs/CHANGELOG.md
git commit -m "Update CHANGELOG for v1.1.0"
git push origin master
```

**Step 3: Deploy to staging**
```bash
ssh jayco@192.168.10.94
cd /opt/rb2-staging
git fetch --tags
git checkout v1.1.0
source venv/bin/activate
pip install -r web/requirements.txt
sudo systemctl restart rb2-staging
sudo journalctl -u rb2-staging -n 50
```

**Step 4: Test staging**
```bash
# Smoke tests
curl http://localhost:5002/
curl http://localhost:5002/awards/

# Full testing (1-3 days)
# - Functional tests
# - Performance tests
# - Regression tests
```

**Step 5: Deploy to production**
```bash
ssh jayco@192.168.10.94
cd /opt/rb2-production

# Record current version
git describe --tags > /tmp/rb2-previous-version.txt

# Deploy new version
git fetch --tags
git checkout v1.1.0
source venv/bin/activate
pip install -r web/requirements.txt
sudo systemctl restart rb2-production

# Verify
sudo systemctl status rb2-production
curl http://localhost:5003/
curl https://rb2.yourdomain.com/

# Monitor
sudo journalctl -u rb2-production -f
```

**Step 6: Post-deployment**
```bash
# Monitor for 15-30 minutes
# Check logs for errors
# Test critical user paths
# Monitor performance metrics

# If issues arise, rollback:
PREVIOUS=$(cat /tmp/rb2-previous-version.txt)
git checkout $PREVIOUS
sudo systemctl restart rb2-production
```

---

## Summary

**RB2 Code Promotion Process:**

1. **Develop** on `master` branch locally
2. **Tag** releases with semantic versioning (v1.0.0)
3. **Deploy** tag to staging (`/opt/rb2-staging`)
4. **Test** thoroughly on staging (1-3 days)
5. **Deploy** same tag to production (`/opt/rb2-production`)
6. **Monitor** and be ready to rollback if needed

**Key Principle:** Simple, repeatable process optimized for solo development with clear traceability and easy rollback.

---

**Document Version:** 1.0
**Last Updated:** 2025-10-15
**Related Documents:**
- `staging-deployment-plan.md` - Detailed deployment procedures
- `optimization-strategy.md` - Performance guidelines
- `CHANGELOG.md` - Version history
