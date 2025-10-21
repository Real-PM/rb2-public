# Phase 1B Results: N+1 Query Fix

**Date:** 2025-10-14
**Objective:** Fix application-level performance issues through query profiling
**Result:** 75.5% improvement on Coach Main page with single-line fix

---

## The Problem

### Coach Main Page Analysis
- **Original Performance:** 8572ms average
- **Issue:** Classic N+1 query pattern in `/coaches/` route

### Root Cause (coaches.py:16-20)
```python
# BEFORE: No eager loading
coaches = Coach.query.filter(Coach.team_id > 0).order_by(
    Coach.occupation,
    Coach.team_id,
    Coach.last_name
).all()
```

**What was happening:**
1. Query fetches all coaches (~hundreds of records)
2. Template loops through coaches
3. For EACH coach, template accesses `coach.team.name` (list.html:44)
4. Each access triggers a separate SQL query to fetch the team
5. Result: 1 query to get coaches + N queries to get teams = N+1 pattern

---

## The Fix

### Added Eager Loading (coaches.py:17-21)
```python
# AFTER: Eager load team relationship
coaches = Coach.query.filter(Coach.team_id > 0).options(
    selectinload(Coach.team).load_only(
        Team.team_id,
        Team.name
    )
).order_by(
    Coach.occupation,
    Coach.team_id,
    Coach.last_name
).all()
```

**What changed:**
1. `selectinload(Coach.team)` - Fetch all teams in a single separate query
2. `load_only(Team.team_id, Team.name)` - Only fetch needed columns
3. Result: 2 queries total (coaches + teams) instead of N+1

---

## Performance Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Run 1 | 8476ms | 2311ms | 72.7% faster |
| Run 2 | 8433ms | 1952ms | 76.9% faster |
| Run 3 | 8808ms | 2043ms | 76.8% faster |
| **Average** | **8572ms** | **2102ms** | **75.5% faster** |

### Comparison to Baseline
- **Original Baseline** (before Phase 1 indexes): 8295ms
- **After Phase 1 indexes** (degraded): 8572ms (+3.3%)
- **After N+1 fix**: 2102ms (**74.7% faster than original baseline**)

---

## Technical Details

### SQL Queries Generated

**Before (N+1 pattern):**
```sql
-- Query 1: Get all coaches
SELECT * FROM coaches WHERE team_id > 0 ORDER BY occupation, team_id, last_name;

-- Query 2-N: For EACH coach in template
SELECT * FROM teams WHERE team_id = ?;  -- Repeated hundreds of times!
```

**After (Optimized):**
```sql
-- Query 1: Get all coaches
SELECT coach_id, team_id, first_name, last_name, ...
FROM coaches
WHERE team_id > 0
ORDER BY occupation, team_id, last_name;

-- Query 2: Get all teams for those coaches (single query)
SELECT team_id, name
FROM teams
WHERE team_id IN (1, 2, 3, ...);  -- All team IDs in one query
```

### SQLAlchemy Strategy
- **`selectinload()`** - Loads related objects in separate query using IN clause
- **`load_only()`** - Limits columns fetched (reduces data transfer)
- **Alternative:** `joinedload()` would use LEFT JOIN (single query, but more data)

---

## Key Learnings

### ✅ What Worked
1. **Profile before optimize** - Found the exact problem by reading code
2. **N+1 is the killer** - Single relationship access = hundreds of queries
3. **Eager loading is essential** - Small code change, massive impact
4. **Measurement validates** - 75% improvement proves the fix

### 💡 Insights
1. **Indexes can't fix N+1** - Phase 1 actually made it worse (+3.3%)
2. **Application layer > Database layer** - Query patterns matter more than indexes
3. **Template analysis critical** - Must trace what templates access
4. **One line can save 6+ seconds** - Simple fixes have huge impact

### 🎯 Pattern to Replicate
**For any list page:**
1. Check template for relationship access (e.g., `object.related.field`)
2. Add `selectinload()` in query with `load_only()` for needed fields
3. Test and measure impact
4. Repeat for other slow pages

---

## Next Steps

### Immediate Priorities
1. ✅ Coach Main - **FIXED** (75.5% improvement)
2. 🔄 Front Page - Investigate (worst degradation +24.8%)
3. 🔄 Player Detail - Check for similar N+1 patterns
4. 🔄 Team Main - Verify query patterns

### Investigation Areas
- Check if Front page has similar issues in featured players/rookies/birthdays
- Profile Player Detail page for stats loading
- Look for other list pages with relationship access in templates

### Documentation
- ✅ Updated performance_baseline.csv with Phase 1B results
- ✅ Created phase1b_results.md
- 🔄 Need to update optimization-strategy.md with success

---

## Code Changes

### Modified Files
- `/web/app/routes/coaches.py` (lines 17-21)
  - Added `selectinload(Coach.team).load_only(...)`
  - Single modification, massive impact

### No Schema Changes
- No database changes required
- No migrations needed
- Pure application-level optimization

---

## Conclusion

**Phase 1B validated the revised strategy:** Application-level optimization (fixing N+1 queries) delivers far better results than database indexing alone.

**Single Finding:** One N+1 query pattern cost 6.4 seconds (75% of page load time)

**The Fix:** 4 lines of code using SQLAlchemy's `selectinload()`

**The Result:** Page loads in 2.1 seconds instead of 8.6 seconds

**Next Goal:** Find and fix similar patterns in Front page and Player Detail to achieve overall 50%+ improvement across all pages.
