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

## Session 2025-10-24: Phase 4D Bottleneck Analysis

**Status:** ✅ Bottleneck identified - Dictionary conversion needed

### Current Performance (After Phase 4B Caching)

| Route         | Cold Load | Warm Load | Cache Hit Improvement |
|---------------|-----------|-----------|-----------------------|
| Front Page    | 86s       | 24ms      | 99.97% ✅              |
| Player List   | 20s       | 9ms       | 99.96% ✅              |
| Player Detail | 87s       | 9ms       | 99.99% ✅              |
| Team Detail   | 21s       | 17ms      | 99.92% ✅              |
| Leaderboards  | 42s       | 10ms      | 99.98% ✅              |

**Caching WORKS!** 99.9%+ improvement on warm loads.

**Problem:** Cold loads still 60-100 seconds (unacceptable).

### 87-Second Player Detail Breakdown

From timestamp analysis in journalctl logs:
- **31 seconds:** Database queries (8 queries total)
- **56 seconds:** Template rendering (lazy-load cascades)

### Query Analysis: Player Detail Route

**File:** `web/app/routes/players.py:110`

**Current Pattern (4 Service Calls):**
```python
# Lines 195-200 - Four separate service calls
batting_data_major = player_service.get_player_career_batting_stats(player_id, league_level_filter=1)
batting_data_minor = player_service.get_player_career_batting_stats(player_id, league_level_filter=2)
pitching_data_major = player_service.get_player_career_pitching_stats(player_id, league_level_filter=1)
pitching_data_minor = player_service.get_player_career_pitching_stats(player_id, league_level_filter=2)
```

Each call executes **2 SQL queries**:
1. Yearly stats query (with league level join)
2. Career totals aggregation (with league level join)

**Total:** 4 calls × 2 queries = **8 SQL queries** (31 seconds)

### The Real Bottleneck: 56 Seconds of Template Rendering

**Root Cause:** Service functions return **ORM objects** to templates.

**File:** `web/app/services/player_service.py:46` (`get_player_career_batting_stats()`)

Current return pattern:
```python
# Line 95: Returns ORM objects
yearly_stats = query.order_by(PlayerBattingStats.year.asc()).all()  # ← ORM objects

# Line 64: Returns dict with ORM objects inside
return {'yearly_stats': yearly_stats, 'career_totals': career_totals}
```

**Problem:** When templates access ORM object attributes, SQLAlchemy can trigger lazy loads:

```jinja2
{# Template accessing stat.team.abbr #}
{% for stat in batting_data_major.yearly_stats %}
  {{ stat.team.abbr }}  {# ← Can trigger lazy load #}
{% endfor %}
```

Even with `selectinload(PlayerBattingStats.team)` in the service function (line 82), **memoization caches detached ORM objects** that trigger lazy loads in different contexts.

**Result:** Hundreds of lazy-load queries during template rendering = **56 seconds**

### Why recursion_depth=3 Had No Impact

The `recursion_depth` setting (added in v1.0.5-phase4d-task1) only limits eager-loading depth in the initial query. It does **not prevent** lazy-loads triggered during template rendering.

---

## Solution: Return Dictionaries Instead of ORM Objects

### Current Implementation (SLOW)

**File:** `web/app/services/player_service.py:95`

```python
# Returns ORM objects (can lazy-load in templates)
yearly_stats = query.order_by(PlayerBattingStats.year.asc()).all()
for stat in yearly_stats:
    stat.age = calculate_age_for_season(player.date_of_birth, stat.year)
return {'yearly_stats': yearly_stats, 'career_totals': career_totals}
```

### Proposed Implementation (FAST)

```python
# Query ORM objects with all needed relationships eager-loaded
yearly_stats = query.order_by(PlayerBattingStats.year.asc()).all()

# Convert to dictionaries BEFORE returning (prevents lazy-loading)
yearly_stats_dicts = [
    {
        'year': stat.year,
        'age': calculate_age_for_season(player.date_of_birth, stat.year),
        'team_id': stat.team.team_id if stat.team else None,
        'team_abbr': stat.team.abbr if stat.team else None,
        'team_name': stat.team.name if stat.team else None,
        'league_id': stat.league_id,
        'g': stat.g,
        'pa': stat.pa,
        'ab': stat.ab,
        'r': stat.r,
        'h': stat.h,
        'd': stat.d,
        't': stat.t,
        'hr': stat.hr,
        'rbi': stat.rbi,
        'sb': stat.sb,
        'cs': stat.cs,
        'bb': stat.bb,
        'ibb': stat.ibb,
        'k': stat.k,
        'hp': stat.hp,
        'sh': stat.sh,
        'sf': stat.sf,
        'gdp': stat.gdp,
        'avg': stat.avg,
        'obp': stat.obp,
        'slg': stat.slg,
        'ops': stat.ops,
        'iso': stat.iso,
        'babip': stat.babip,
        'woba': stat.woba,
        'wrc_plus': stat.wrc_plus,
        'war': stat.war,
        'wrc': stat.wrc,
        'wraa': stat.wraa,
        'wpa': stat.wpa,
        'ubr': stat.ubr
    }
    for stat in yearly_stats
]

return {'yearly_stats': yearly_stats_dicts, 'career_totals': career_totals}
```

**Benefit:** Dictionaries can't lazy-load. Templates access dict keys, not ORM attributes.

### Template Changes (Minimal)

Templates already use attribute access, which works with dicts:

```jinja2
{# BEFORE (ORM object) #}
{{ stat.team.abbr }}

{# AFTER (dictionary) #}
{{ stat.team_abbr }}
{# OR {{ stat['team_abbr'] }} #}
```

---

## Implementation Plan - Phase 4D Task 2

### Files to Modify

1. **`web/app/services/player_service.py`**
   - **Function:** `get_player_career_batting_stats()` (line 46-211)
     - Convert `yearly_stats` ORM objects to dictionaries before returning
     - Keep `career_totals` as dict (already is)

   - **Function:** `get_player_career_pitching_stats()` (line 212-378)
     - Same conversion for pitching stats
     - Include all pitching stat fields

2. **Templates** (verify compatibility):
   - `web/app/templates/players/detail.html`
   - `web/app/templates/players/_batting_stats_table.html`
   - `web/app/templates/players/_pitching_stats_table.html`
   - Change `stat.team.abbr` → `stat.team_abbr` (if needed)
   - Change `stat.team.name` → `stat.team_name` (if needed)

3. **Other Service Functions** (check for ORM returns):
   - `get_player_trade_history()` - Check if returns ORM objects
   - `get_player_news()` - Check if returns ORM objects

### Testing Protocol

After modification:
```bash
# On staging (Minotaur)
# Clear cache
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 FLUSHDB

# Test player detail cold load
time curl -o /dev/null -s http://localhost:5002/players/10

# Expected: 87s → <20s (77% improvement from 56s template rendering eliminated)

# Test warm load (should still be cached)
time curl -o /dev/null -s http://localhost:5002/players/10

# Expected: <100ms (caching still works)

# Verify cache keys
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 DBSIZE
```

**Expected Results:**
- **Cold load:** 87s → 10-20s (65-88% improvement)
  - Eliminates 56s of template rendering lazy-loads
  - 31s of queries remains (will optimize in Task 3 if needed)
- **Warm load:** <100ms (no change - caching still works)

---

## Phase 4D Tasks Checklist

- [x] **Task 1:** Add `recursion_depth=3` to SQLAlchemy config (v1.0.5-phase4d-task1)
  - **Result:** No impact (87s → 87s)
  - **Reason:** Doesn't prevent template lazy-loads

- [ ] **Task 2:** Convert service functions to return dictionaries
  - **Expected:** 87s → 10-20s (eliminate 56s template rendering)
  - **Tag:** `v1.0.6-phase4d-dict-conversion`
  - **Status:** Ready to implement

- [ ] **Task 3:** Consolidate 4 service calls into 2 (if still needed)
  - **Expected:** 31s queries → 15s queries
  - **Only if:** Task 2 doesn't achieve <5s target

- [ ] **Task 4:** Raw SQL with CTEs (if still needed)
  - **Expected:** 15s → <5s
  - **Only if:** Tasks 2-3 don't achieve <5s target

- [ ] **Task 5:** Database trimming (last resort - optional)
  - **Only if:** All other optimizations fail

---

## Success Criteria

- ✅ **Primary:** Player detail cold loads <5 seconds
- ✅ **Secondary:** Front page cold loads <10 seconds
- ✅ **Maintained:** Warm loads remain <100ms (99.9%+ cache hit)
- ✅ **No Regressions:** All existing functionality works

---

## Related Documentation

- `docs/optimization/phase4d_under_5s_checklist.md` - Persistent task checklist
- `docs/optimization/optimization-strategy.md` - Overall optimization strategy
- `docs/optimization/phase3_results.md` - Redis caching implementation
- `docs/optimization/phase2_results.md` - Application-level optimizations
- `docs/optimization/phase1b_results.md` - N+1 query fixes

---

**Document Status:** 🟡 Phase 4D In Progress - Dictionary conversion ready
**Last Updated:** 2025-10-24 (Session 3)
**Next Review:** After Task 2 implementation and testing
