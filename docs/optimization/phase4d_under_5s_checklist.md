# Phase 4D: Get Cold Loads Under 5 Seconds

**Goal:** Reduce player detail page cold loads from 60-100s to <5s
**Started:** 2025-10-23 Session 2
**Status:** 🟡 In Progress

---

## Current Baseline

| Page Type | Current Cold Load | Target |
|-----------|------------------|--------|
| Player Detail | 60-100s | <5s |
| Front Page | 86s | <10s |
| Team Detail | 21s | <5s |
| Leaderboards | 42s | <5s |

---

## Phase 4D Tasks

### ✅ Completed
- [x] Phase 4A: Connection pool improvements (v1.0.1-phase4a)
- [x] Phase 4B: Comprehensive route caching (v1.0.2-phase4b)
- [x] Phase 4B Fix 1: Cache key generation fix (v1.0.3-phase4b-fix)
- [x] Phase 4B Fix 2: DetachedInstanceError fix (v1.0.4-phase4b-fix2)
- [x] Analysis: Root cause identification
- [x] Verified: 99.9% cache hit performance

### 🔄 In Progress
- [ ] **Task 1: Add recursion_depth limit** (5 minutes)
  - File: `web/app/config.py`
  - Add to `SQLALCHEMY_ENGINE_OPTIONS`
  - Expected: 60s → 40s (33% improvement)
  - Tag: `v1.0.5-phase4d-recursion`

### ⏳ Pending
- [ ] **Task 2: Consolidate service calls** (2 hours)
  - Files: `web/app/services/player_service.py`, `web/app/routes/players.py`
  - Combine 4 stats calls into 1-2 queries
  - Expected: 40s → 15s (62% improvement from baseline)
  - Tag: `v1.0.6-phase4d-consolidation`

- [ ] **Task 3: Raw SQL for complex queries** (1-2 hours)
  - Target: Slowest remaining query (identify via profiling)
  - Use CTEs and optimized joins
  - Expected: 15s → <5s (92% improvement from baseline)
  - Tag: `v1.0.7-phase4d-rawsql`

- [ ] **Task 4 (Optional): Database trimming** (1 hour)
  - Script: `scripts/trim_inactive_players.py`
  - Remove retired non-majors players
  - Expected: Additional 20-30% improvement
  - Only if Tasks 1-3 don't achieve <5s
  - Tag: `v1.0.8-phase4d-trim`

---

## Success Criteria

- ✅ **Primary:** Player detail cold loads <5 seconds
- ✅ **Secondary:** Front page cold loads <10 seconds
- ✅ **Maintained:** Warm loads remain <100ms (99.9%+ cache hit)
- ✅ **No Regressions:** All existing functionality works

---

## Known Issues to Monitor

- ⚠️ **Player 1:** Has unique data issue causing 500 error (non-blocking)
- ⚠️ **SQLAlchemy Warnings:** "Loader depth excessive" at multiple locations
  - `web/app/routes/main.py:29` (front page)
  - `web/app/routes/main.py:89` (division query)
  - `web/app/services/player_service.py:619` (get notable rookies)
  - `web/app/context_processors.py:24` (game date injection)

---

## Testing Protocol

After each task, run on staging:

```bash
# Clear cache
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 FLUSHDB

# Test player detail pages (sample)
for player_id in 2 3 5 10 20; do
  echo "=== Player $player_id ==="
  echo "Cold:"
  time curl -o /dev/null -s http://localhost:5002/players/$player_id
  echo "Warm:"
  time curl -o /dev/null -s http://localhost:5002/players/$player_id
done

# Test front page
echo "=== Front Page ==="
time curl -o /dev/null -s http://localhost:5002/
time curl -o /dev/null -s http://localhost:5002/

# Verify cache keys
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 DBSIZE
```

**Expected progression:**
- After Task 1: ~40s cold, <100ms warm
- After Task 2: ~15s cold, <100ms warm
- After Task 3: **<5s cold, <100ms warm** ✅

---

## Rollback Plan

Each task is tagged separately. To rollback:

```bash
git checkout <previous-tag>
sudo systemctl restart rb2-staging
```

---

## Notes

### Why 60-100s is so slow:
1. **SQLAlchemy lazy-loading cascades** - Hundreds of extra queries
2. **Multiple redundant service calls** - 4 stats queries when 1-2 would suffice
3. **No recursion depth limit** - Allows infinite eager loading depth
4. **NOT hardware** - 500MB database is tiny, should be instant

### Why caching works so well (99.9%):
- Cache stores fully-rendered HTML
- No database queries on cache hit
- Redis is extremely fast (sub-millisecond)

### Phase 4D Strategy:
- Quick wins first (recursion depth)
- Query consolidation for major gains
- Raw SQL only if needed to hit target
- Database trimming as last resort (probably not needed)

---

**Document Status:** 🟡 Active - Phase 4D In Progress
**Last Updated:** 2025-10-23 Session 2
**Next Update:** After Task 1 completion
