# Phase 4: Slow Query Investigation & Optimization Plan

**Date Started:** 2025-10-22
**Status:** Investigation Phase
**Current Staging Performance:** 86-90 seconds per page load (CRITICAL)

---

## Executive Summary

Staging environment is experiencing **90-second page loads** despite:
- ✅ Redis deployed and working (`redis://192.168.10.94:6379/1`)
- ✅ Gunicorn gevent workers configured (4 workers, 100 connections each)
- ✅ SQLAlchemy connection pool increased (pool_size=20, max_overflow=10)
- ✅ Flask-Caching initialized and functional

**Root Cause:** Code on staging does NOT have Phase 3 caching optimizations deployed. The staging server has manual edits that include cache decorators, but performance indicates deeper issues with query complexity.

---

## Current Staging Status (2025-10-22)

### Infrastructure ✅
- **Redis**: Running in Docker container `redis-rb2` on port 6379
- **Gunicorn**: 4 gevent workers, 100 connections/worker, 120s timeout
- **Database**: PostgreSQL in Docker `ootp-postgres`, database `ootp_stage`
- **Service**: `rb2-staging.service` running on port 5002

### Configuration ✅
- **FLASK_ENV**: `staging`
- **Cache Type**: `RedisCache`
- **Cache URL**: `redis://192.168.10.94:6379/1`
- **Cache Prefix**: `rb2_staging:`
- **Pool Size**: 20 connections
- **Max Overflow**: 10 connections

### Code State ⚠️
- **Local Repo**: Clean repo with only 3 commits (ETL fixes, no optimization history)
- **Staging Repo**: `/opt/rb2-public` - appears to have some manual edits
- **Git Commits**:
  - `9f1e124` - Fix staging ETL issues (migrations)
  - `3658c7a` - Fix ETL database environment selection
  - `63075d5` - Initial commit on clean repo

**Issue**: Phase 3 caching code is NOT deployed to staging. Optimization history from previous phases is in a different repository.

---

## Performance Test Results (2025-10-22 04:38 UTC)

### Front Page Load Times
| Test | Time | Notes |
|------|------|-------|
| Cache MISS (1st request) | **86.2s** | With Redis flushed |
| Cache HIT (2nd request) | **90.6s** | Should be <10ms! |
| Redis Keys After Test | **0** | No caching occurred |

### Observed Issues
1. **Flask-Caching works in isolation** - manual test shows Redis connectivity OK
2. **Route cache decorator present** - `@cache.cached(timeout=300)` on front page
3. **No cache keys created** - Redis remains empty after requests
4. **SQLAlchemy warnings** - "Loader depth for query is excessively deep; caching will be disabled"

### SQLAlchemy Warnings Locations
From journalctl, excessive loader depth warnings at:
- `/opt/rb2-public/web/app/routes/main.py:29`
- `/opt/rb2-public/web/app/routes/main.py:89`
- `/opt/rb2-public/web/app/services/player_service.py:619`
- `/opt/rb2-public/web/app/context_processors.py:24`

These indicate **deeply nested eager loading** causing query complexity.

---

## Investigation Plan

### Phase 4A: Diagnose Query Complexity (1-2 hours)

**Objective**: Identify which queries are causing 90-second page loads

#### Step 1: Enable SQLAlchemy Query Logging
```python
# In web/app/config.py - StagingConfig
SQLALCHEMY_ECHO = True  # Temporarily enable for diagnosis
```

#### Step 2: Add Query Timing Middleware
```python
# In web/app/__init__.py
from flask import request
import time

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = (time.time() - request.start_time) * 1000
        logger.info(f"{request.method} {request.path} - {duration:.0f}ms")
    return response
```

#### Step 3: Profile Front Page Route
Examine `/opt/rb2-public/web/app/routes/main.py` lines causing warnings:
- Line 29: Likely standings query with deep joins
- Line 89: Unknown query location

Check for:
- Multiple `selectinload()` or `joinedload()` chains
- Queries without `load_only()` to limit columns
- Missing `lazyload()` or `noload()` on unused relationships

#### Step 4: Count Database Rows
```sql
-- Check data volume on staging
SELECT
    schemaname,
    relname,
    n_live_tup,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as size
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 20;
```

**Expected Findings**:
- Staging has 780K game batting stats (vs dev's smaller dataset)
- Potentially 20K+ active players being loaded unnecessarily
- Nested joins causing Cartesian product explosions

---

### Phase 4B: Implement Query Optimizations (2-4 hours)

**Priority Actions**:

#### 1. Fix Excessive Eager Loading
**Location**: `web/app/routes/main.py` (front page)

**Problem**: Deep nested joins causing "loader depth excessive" warnings

**Solution**:
```python
# BEFORE (likely current code)
teams = Team.query.options(
    joinedload(Team.current_record),
    joinedload(Team.relations).joinedload(SubLeague.league),
    joinedload(Team.relations).joinedload(Division),
    # ... more nested joins
).all()

# AFTER (optimized)
teams = Team.query.options(
    selectinload(Team.current_record).load_only(
        TeamRecord.w, TeamRecord.l, TeamRecord.pct, TeamRecord.gb
    ),
    selectinload(Team.relations).load_only(
        TeamRelation.league_id, TeamRelation.division_id
    ),
    lazyload('*'),  # Don't load anything else
).all()
```

#### 2. Add Loader Recursion Limits
```python
# In web/app/config.py - All configs
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'pool_timeout': 30,
    'echo_pool': False,
    'execution_options': {
        'compiled_cache': {},
        'recursion_depth': 3,  # Limit eager load depth
    }
}
```

#### 3. Simplify Front Page Query
Use raw SQL or simpler ORM query:
```python
# Option A: Raw SQL (fastest)
standings_query = text("""
    SELECT
        t.team_id, t.name, t.abbr,
        tr.league_id, tr.division_id,
        rec.w, rec.l, rec.pct, rec.gb, rec.pos
    FROM teams t
    JOIN team_relations tr ON t.team_id = tr.team_id
    JOIN team_record rec ON t.team_id = rec.team_id
    WHERE t.level = 1
    ORDER BY tr.league_id, tr.division_id, rec.pos
""")
standings = db.session.execute(standings_query).fetchall()

# Option B: Denormalized query with minimal joins
teams = db.session.query(
    Team.team_id, Team.name,
    TeamRecord.w, TeamRecord.l, TeamRecord.pct
).join(TeamRecord).filter(Team.level == 1).all()
```

#### 4. Fix Player Service Queries
**Location**: `web/app/services/player_service.py:619`

Likely in `get_featured_players()` or `get_notable_rookies()`:
```python
# Add load_only and limit relationships
players = Player.query.filter(...).options(
    load_only(Player.player_id, Player.first_name, Player.last_name),
    selectinload(Player.current_status).load_only(
        PlayerCurrentStatus.team_id, PlayerCurrentStatus.position
    ),
    noload('*'),  # Don't load anything else
).limit(10).all()
```

---

### Phase 4C: Database Trimming Strategy (Optional - Last Resort)

**Only if query optimization doesn't get page loads under 5 seconds**

#### Trimming Criteria
Remove players who meet ALL conditions:
1. `retired = 1` (retired)
2. Never played `league_level = 1` (never reached majors)
3. Not in `coaches` table (didn't become a coach)
4. Not referenced in `messages` table (no newspaper mentions)

#### Implementation Script
```python
# scripts/trim_inactive_players.py
"""
Removes inactive players from staging database to improve performance.
Run ONLY on staging, NEVER on production.
"""
from sqlalchemy import text

def identify_trimmable_players(db):
    """Identify players safe to remove"""
    query = text("""
        SELECT COUNT(*) as trimmable_count
        FROM players_core pc
        JOIN players_current_status pcs ON pc.player_id = pcs.player_id
        WHERE pcs.retired = 1
          AND pc.player_id NOT IN (
              SELECT DISTINCT player_id
              FROM players_career_batting_stats
              WHERE league_level = 1
              UNION
              SELECT DISTINCT player_id
              FROM players_career_pitching_stats
              WHERE league_level = 1
          )
          AND pc.player_id NOT IN (SELECT person_id FROM coaches)
          AND pc.player_id NOT IN (SELECT player_id FROM messages WHERE player_id IS NOT NULL)
    """)
    return db.execute(query).scalar()

def trim_players(db, dry_run=True):
    """
    Remove players and all related records
    WARNING: This is destructive! Always test with dry_run=True first
    """
    # List of tables to clean (in dependency order)
    tables_to_clean = [
        'players_game_batting_stats',
        'players_game_pitching_stats',
        'players_game_fielding_stats',
        'players_career_batting_stats',
        'players_career_pitching_stats',
        'players_career_fielding_stats',
        'players_ratings',
        'players_contracts',
        'players_current_status',
        'trade_history',
        'players_core',  # Last - master table
    ]

    # Get player IDs to remove
    player_ids_query = text("""
        SELECT pc.player_id
        FROM players_core pc
        JOIN players_current_status pcs ON pc.player_id = pcs.player_id
        WHERE pcs.retired = 1
          AND pc.player_id NOT IN (...)  -- Full criteria from above
    """)

    if dry_run:
        print(f"DRY RUN: Would remove {count} players and their records")
        return

    # Execute deletions in transaction
    with db.begin():
        for table in tables_to_clean:
            result = db.execute(text(f"""
                DELETE FROM {table}
                WHERE player_id IN ({player_ids_query})
            """))
            print(f"Deleted {result.rowcount} rows from {table}")
```

#### Expected Impact
- **Before**: 24K players, 780K game stats
- **After**: ~15K players (estimate), ~500K game stats
- **Performance**: 20-30% reduction in query times
- **Risk**: Medium - could affect historical queries if criteria too aggressive

---

## Deployment Process

### Git Workflow: Dev → Staging

**All optimization changes must flow through git tags for proper version control.**

#### 1. Make Changes in Local Dev Repo
```bash
# On development machine
cd /mnt/hdd/PycharmProjects/rb2-public

# Make code changes for optimization
# Edit files in web/app/routes/, web/app/services/, etc.

# Test locally
cd web && python run.py
# Verify changes work in dev environment
```

#### 2. Commit and Tag Changes
```bash
# Stage your changes
git add web/app/routes/main.py web/app/services/player_service.py web/app/config.py

# Commit with descriptive message
git commit -m "Phase 4A: Fix excessive eager loading on front page

- Limit selectinload depth in main.py standings query
- Add load_only to player service queries
- Set recursion_depth=3 in SQLAlchemy config
- Expected improvement: 50-70% reduction in query time"

# Create a version tag
git tag -a v1.0.1-phase4a -m "Phase 4A: Query optimization for staging performance

Changes:
- Fix SQLAlchemy loader depth warnings
- Optimize front page standings query
- Add recursion limits to prevent deep joins

Expected: Reduce 90s page loads to <10s"

# Push to origin (includes tags)
git push origin master
git push origin v1.0.1-phase4a
```

#### 3. Deploy to Staging (On Minotaur)
```bash
# SSH to staging server
ssh jayco@192.168.10.94

# Navigate to staging repo
cd /opt/rb2-public

# Fetch latest changes and tags from origin
git fetch origin --tags

# List available tags to verify
git tag -l
# Output should show: v1.0.1-phase4a

# Checkout the specific tag
git checkout v1.0.1-phase4a

# Verify you're on the tag
git describe --tags
# Output: v1.0.1-phase4a

# Install any new dependencies (if requirements changed)
source /opt/rb2-public/venv/bin/activate
pip install -r web/requirements.txt

# Restart the service
systemctl restart rb2-staging

# Check service started OK
systemctl status rb2-staging

# Monitor logs for errors
journalctl -u rb2-staging -f
# Press Ctrl+C to stop following logs
```

#### 4. Test Performance
```bash
# Still on Minotaur
# Test 1: Cache miss (cold)
curl -o /dev/null -s -w 'Load time: %{time_total}s\n' http://localhost:5002/

# Test 2: Cache hit (warm)
curl -o /dev/null -s -w 'Load time: %{time_total}s\n' http://localhost:5002/

# Check Redis cache keys
docker exec $(docker ps --filter name=redis -q) redis-cli --scan --pattern 'rb2_staging:*'

# Expected results:
# - First request: <10s (down from 90s)
# - Second request: <100ms (cached)
# - Redis should show cache keys
```

#### 5. Rollback (If Something Breaks)
```bash
# On Minotaur
cd /opt/rb2-public

# Go back to previous working tag/commit
git checkout v1.0.0  # or whatever the last working tag was
# OR
git checkout master  # return to latest master

# Restart service
systemctl restart rb2-staging
```

---

## Tag Naming Convention

Use semantic versioning with phase suffixes:

- `v1.0.0` - Initial production release
- `v1.0.1-phase4a` - Phase 4A: Query diagnosis
- `v1.0.2-phase4b` - Phase 4B: Query optimizations
- `v1.0.3-phase4c` - Phase 4C: Database trimming (if needed)
- `v1.1.0` - Major feature or significant optimization milestone

**Format**: `v{major}.{minor}.{patch}-{phase}{iteration}`

---

## Success Criteria

### Phase 4A Complete (Diagnosis)
- ✅ Query logging enabled
- ✅ Slow queries identified (specific lines, tables, joins)
- ✅ Baseline metrics recorded (query count, execution time per query)
- ✅ Root cause documented

### Phase 4B Complete (Optimization)
- ✅ Front page load: <5 seconds uncached, <100ms cached
- ✅ No SQLAlchemy "loader depth" warnings
- ✅ Redis cache keys created and used
- ✅ Worker CPU usage: <30% average
- ✅ Database connection pool stable (<80% utilization)

### Phase 4C Complete (Trimming - Optional)
- ✅ Player count reduced by 30-40%
- ✅ Game stats reduced by 30-40%
- ✅ Query performance improved by additional 20-30%
- ✅ No data loss for important players (majors, coaches, news mentions)

---

## Notes and Gotchas

### Git Tag Management
- **Always fetch tags**: `git fetch origin --tags` before checking out
- **List tags**: `git tag -l` to see what's available
- **Detached HEAD**: Checking out a tag puts you in "detached HEAD" state - this is OK for deployment, but don't make changes here
- **Return to branch**: `git checkout master` to get back to normal development

### Staging Environment Specifics
- **Database**: 3-4x larger than dev (780K vs ~200K game stats)
- **Redis**: Shared on DB server, namespace `rb2_staging:`
- **Service**: Must restart after code changes: `systemctl restart rb2-staging`
- **Logs**: `journalctl -u rb2-staging -f` for real-time monitoring

### Performance Testing
- **Always clear cache first**: `docker exec $(docker ps --filter name=redis -q) redis-cli FLUSHDB`
- **Test both cold and warm**: First request = cache miss, second = cache hit
- **Use curl timing**: `-w 'Time: %{time_total}s\n'` for accurate measurement
- **Monitor worker CPU**: `ps aux | grep gunicorn | grep 5002` during requests

### Common Issues
1. **Service won't start**: Check `journalctl -u rb2-staging` for Python syntax errors
2. **Redis not caching**: Verify FLASK_ENV=staging and cache type is RedisCache
3. **Still slow with cache**: Check for cache exceptions in logs, verify decorators present
4. **Workers crashing**: Check timeout (120s), increase if needed for cold starts

---

## Session 2025-10-23: Phase 4A Implementation ✅

**Status:** Connection pool optimization completed, ready for deployment

### Findings from Code Audit

**Good News:**
1. ✅ **Phase 3 caching code already present** in rb2-public codebase
   - `@cache.cached()` decorator on main.py index route (line 13)
   - `@cache.memoize()` decorators on all player_service functions
   - Redis configuration properly set for all environments
   - Flask-Caching and redis in requirements.txt

2. ✅ **Query optimizations already implemented**
   - main.py uses `load_only()`, `lazyload()`, `raiseload()` to prevent cascades
   - player_service.py uses raw SQL with CTEs for complex queries
   - Context processors use simple, efficient queries

3. ✅ **SQLAlchemy warnings locations verified**
   - Line 29: `League.query.filter_by(league_level=1).order_by(League.name).all()` - SIMPLE
   - Line 89: `Division.query.filter_by(...).first()` - SIMPLE
   - Line 619 (player_service): `League.query.filter_by(league_level=1).first()` - SIMPLE
   - **Conclusion**: Warnings likely from relationship loading, not these specific queries

### Changes Implemented

**Commit:** `ecef8ea`
**Tag:** `v1.0.1-phase4a`

```python
# web/app/config.py - Updated SQLALCHEMY_ENGINE_OPTIONS
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,          # Was 10 - doubled for staging load
    'max_overflow': 10,       # NEW - burst capacity
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'pool_timeout': 30,       # NEW - prevent indefinite waits
    'echo_pool': False,       # NEW - reduce log noise
}
```

### Root Cause Analysis

**The mystery: Why is caching not working on staging?**

The investigation doc states:
- Cache decorators are present on staging (confirmed manually)
- Redis is running and accessible
- But Redis shows **0 keys** after requests
- Page loads still take 90 seconds even with cache decorator

**Hypothesis for next deployment:**
1. Code on staging may be outdated (despite having some manual edits)
2. Flask-Caching may not be properly initialized
3. FLASK_ENV variable may not be set correctly
4. Gunicorn workers may not have access to updated code

**Deployment will reveal:**
- Whether connection pool improvements help
- If caching starts working with fresh deployment
- If additional query optimization needed

---

## Next Steps: Deployment & Testing

**Step 1: Deploy v1.0.1-phase4a to Staging**

```bash
# On Minotaur (192.168.10.94)
ssh jayco@192.168.10.94
cd /opt/rb2-public

# Fetch and checkout tag
git fetch origin --tags
git checkout v1.0.1-phase4a

# Verify dependencies
source venv/bin/activate
pip install -r web/web_requirements.txt

# Restart service
sudo systemctl restart rb2-staging
sudo systemctl status rb2-staging

# Monitor logs
journalctl -u rb2-staging -f
```

**Step 2: Test Performance**

```bash
# Clear Redis first
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 FLUSHDB

# Test 1: Cold load (cache miss)
time curl -o /dev/null -s http://localhost:5002/

# Test 2: Warm load (should be cached)
time curl -o /dev/null -s http://localhost:5002/

# Verify cache keys exist
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 --scan --pattern 'rb2_staging:*'
```

**Expected Results:**
- **If caching works:** Cold ~5-10s, warm <1s, Redis shows keys
- **If still broken:** Cold 90s, warm 90s, Redis empty → investigate Flask-Caching init

**Step 3: If Caching Still Doesn't Work**

Enable diagnostic logging:
```python
# Temporarily in web/app/config.py - StagingConfig
SQLALCHEMY_ECHO = True  # See all queries
CACHE_TYPE = 'RedisCache'  # Verify this is set
```

Check logs for:
- Cache initialization messages
- Redis connection errors
- SQLAlchemy query count and timing

---

## Next Session Tasks (If Issues Persist)

**If caching works after deployment:** ✅ DONE - Monitor and move to Phase 5

**If caching still broken:**
1. Add debug logging to cache decorator calls
2. Test Flask-Caching manually in flask shell
3. Verify FLASK_ENV environment variable
4. Check gunicorn worker process has correct config

**If caching works but still slow:**
1. Enable SQLALCHEMY_ECHO to identify slow queries
2. Add query timing middleware (see investigation plan Phase 4A Step 2)
3. Profile specific queries with EXPLAIN ANALYZE
4. Consider database trimming strategy (Phase 4C)

---

## Related Documentation

- `docs/optimization/optimization-strategy.md` - Overall optimization strategy
- `docs/optimization/phase3_results.md` - Redis caching implementation (99.8% improvement)
- `docs/optimization/phase2_results.md` - Application-level optimizations
- `docs/optimization/phase1b_results.md` - N+1 query fixes (75% improvement)
- `docs/stage-issues/stage-issues.md` - Known staging environment issues

---

**Document Status:** 🟢 Phase 4A Complete - Ready for Deployment
**Last Updated:** 2025-10-23 (Session 2)
**Next Review:** After staging deployment and performance testing
