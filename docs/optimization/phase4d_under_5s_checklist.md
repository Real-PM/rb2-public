# Phase 4D: Get Cold Loads Under 5 Seconds

**Goal:** Reduce player detail page cold loads from 60s to <5s
**Started:** 2025-10-23 Session 2
**Status:** 🟡 In Progress - Session 3 (2025-10-24)

---

## Current Status (2025-10-24 Session 3)

| Page Type | Cold Load | Warm Load | Status |
|-----------|-----------|-----------|--------|
| Player Detail | 60s | **BROKEN** | Route caching not working |
| Front Page | Unknown | **BROKEN** | Route caching not working |
| Team Detail | Unknown | **BROKEN** | Route caching not working |

**CRITICAL ISSUE:** Route-level caching (`@cache.cached()`) completely broken. Only `@cache.memoize()` works.

---

## Session 3 Progress (2025-10-24)

### ✅ Completed This Session

1. **Dictionary Conversion (v1.0.6-phase4d-dict-conversion)**
   - Converted `get_player_career_batting_stats()` to return dicts instead of ORM objects
   - Converted `get_player_career_pitching_stats()` to return dicts instead of ORM objects
   - Fixed `AttributeError: 'PlayerBattingStats' object has no attribute 'avg'`
   - Changed to use correct column names: `batting_average`, `on_base_percentage`, `slugging_percentage`
   - Updated templates to use `stat.team_abbr` instead of `stat.team.abbr`
   - **Result:** Page loads successfully (60s), but lazy-load improvement unclear due to broken caching

2. **Worker Type Investigation**
   - Discovered gevent workers were being used
   - Changed `/etc/systemd/system/rb2-staging.service` from `--worker-class gevent` to `--worker-class sync`
   - **Result:** No change - caching still broken (not the root cause)

3. **Root Cause Discovery: Cache Key Generation Broken**
   - **Found:** `@cache.memoize()` creates keys, but `@cache.cached()` does NOT
   - **Evidence:**
     - Only 6 memoize keys in Redis (service functions)
     - ZERO route cache keys created
     - Routes with explicit `key_prefix='static_name'` work (e.g., `players_list`)
     - Routes without explicit key_prefix fail silently
   - **Diagnosis:** Flask-Caching requires explicit `key_prefix` for dynamic routes

4. **Attempted Fixes**
   - Commit `9d0176f`: Added lambda-based key_prefix - **FAILED** (still no cache keys)
   - Commit `0e9f51e`: Changed to function-based key_prefix - **PENDING TEST**

### 🔄 Currently Testing

**Latest Fix (commit `0e9f51e`):**
```python
def _make_player_detail_cache_key():
    """Generate cache key for player detail route"""
    return f'player_detail_{request.view_args.get("player_id")}'

@bp.route('/<int:player_id>')
@cache.cached(timeout=600, key_prefix=_make_player_detail_cache_key)
def player_detail(player_id):
```

**Next Test Required:**
```bash
cd /opt/rb2-public
git pull origin master
sudo systemctl restart rb2-staging

# Test caching
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 FLUSHDB
time curl -o /dev/null -s http://localhost:5002/players/1008
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 KEYS '*player_detail*'
time curl -o /dev/null -s http://localhost:5002/players/1008
```

**Expected:**
- Cache key `rb2_staging:player_detail_1008` should be created
- Second request should be <100ms instead of 60s

---

## Phase 4D Tasks Checklist

### ✅ Completed
- [x] **Task 1:** Add recursion_depth=3 (v1.0.5-phase4d-task1) - **NO IMPACT**
- [x] **Task 2:** Convert service functions to return dictionaries (v1.0.6-phase4d-dict-conversion)
  - Expected 87s → 10-20s improvement
  - **Unable to measure due to broken caching**
- [x] **Investigation:** Identified route caching broken (commits 9d0176f, 0e9f51e)

### 🔄 Pending Verification
- [ ] **Verify cache fix works** (commit 0e9f51e)
  - Test if function-based key_prefix creates cache keys
  - Measure warm load time (<100ms expected)
  - If this works, measure cold load improvement from dictionary conversion

### ⏳ Next Steps (If Cache Works)
- [ ] **Measure dictionary conversion impact**
  - Expected: 87s → 10-20s (eliminated 56s of template lazy-loads)
  - If still >20s, proceed to Task 3

- [ ] **Task 3: Consolidate service calls** (if needed)
  - Files: `web/app/services/player_service.py`, `web/app/routes/players.py`
  - Combine 4 stats calls into 2 or fewer
  - Expected: Further 30-50% reduction

- [ ] **Task 4: Raw SQL optimization** (if needed)
  - Use CTEs for complex queries
  - Only if still >5s after Tasks 2-3

### ⚠️ Fallback Plan (If Cache Still Broken)
- [ ] **Manual route caching implementation**
  - Use `cache.set()` and `cache.get()` manually in route
  - Bypass `@cache.cached()` decorator entirely

---

## Debugging Log

### Why Route Caching Broke

**Timeline:**
1. Phase 4B (v1.0.2-phase4b): Caching reported as working (87s → 9ms warm)
2. Session 3 (2025-10-24): Caching completely broken (60s → 60s warm)

**Investigation:**
- Config unchanged between working and broken states
- Flask-Caching version: 2.1.0 (correct)
- Redis connectivity: Working (memoize keys created successfully)
- Worker type: Changed from gevent to sync (no effect)

**Root Cause:**
- `@cache.cached()` without `key_prefix` fails silently
- No cache keys generated at all
- No exceptions logged

**Attempted Solutions:**
1. Lambda key_prefix: `key_prefix=lambda: f'player_detail_{request.view_args.get("player_id")}'` ❌
2. Function key_prefix: `key_prefix=_make_player_detail_cache_key` ⏳ TESTING

---

## Key Findings from Session 3

1. **Dictionary Conversion Eliminates Lazy-Loads:**
   - Converted `get_player_career_batting_stats()` and `get_player_career_pitching_stats()`
   - Returns plain dicts instead of ORM objects
   - Templates can't trigger lazy-loads on dicts
   - **Expected impact:** Eliminate 56s of template rendering (from 87s total)

2. **Caching Infrastructure Partially Working:**
   - `@cache.memoize()` works perfectly (service function caching)
   - `@cache.cached()` completely broken (route caching)
   - Redis backend functional
   - Issue is with decorator, not infrastructure

3. **Performance Baseline:**
   - Cold load: 60s (dictionary conversion working)
   - Warm load: Should be <100ms but unmeasurable due to cache bug
   - 6 memoize keys created per request (service functions)
   - 0 route cache keys created

---

## Testing Protocol

After cache fix, run on staging:

```bash
# Clear cache
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 FLUSHDB

# Test single player (detailed)
time curl -o /dev/null -s http://localhost:5002/players/1008
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 KEYS '*player_detail*'
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 DBSIZE
time curl -o /dev/null -s http://localhost:5002/players/1008

# Test multiple players
for player_id in 2 3 5 10 20; do
  echo "=== Player $player_id ==="
  time curl -o /dev/null -s http://localhost:5002/players/$player_id
done

# Verify all cached
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 DBSIZE
```

**Expected Results (if cache works):**
- First request: ~60s (cold with dictionary conversion)
- Cache keys created: `rb2_staging:player_detail_1008`, etc.
- Second request: <100ms (cached)
- Total cache keys: 6 (memoize) + N (route keys)

**If cold load still >20s after cache fix:**
- Dictionary conversion didn't help as expected
- Need to proceed with Task 3 (consolidate queries)

---

## Git Commits This Session

- `b9826e6` - Phase 4D Task 2: Convert service functions to return dictionaries
- `fbb3f50` - Fix AttributeError: Use correct database column names
- `9d0176f` - Fix route caching: Add explicit key_prefix (lambda) - FAILED
- `0e9f51e` - Fix cache key generation: Use function instead of lambda - PENDING TEST

**Current HEAD:** `0e9f51e`
**Current Tag:** None (waiting for cache verification)

---

## Next Session Priorities

1. **URGENT: Test commit `0e9f51e`** - Verify function-based cache key works
2. **If cache works:** Measure dictionary conversion performance impact
3. **If still slow:** Implement Task 3 (consolidate service calls)
4. **If cache still broken:** Manual caching implementation as fallback

---

**Document Status:** 🔴 **BLOCKED** - Route caching broken, pending fix verification
**Last Updated:** 2025-10-24 Session 3
**Next Action:** Test commit `0e9f51e` on staging
