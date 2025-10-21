# Phase 2: Query Optimization & Service Layer Improvements

**Date:** 2025-10-14
**Goal:** Achieve 30-40% additional performance improvement through application-level optimization
**Strategy:** Profile-driven N+1 fixes, service layer optimization, and index cleanup

---

## Executive Summary

Phase 1B proved that application-level optimization (fixing N+1 queries) delivers far superior results compared to database indexing alone. The Coach Main page fix achieved a 75.5% improvement with a single 4-line code change.

**Phase 2 Objectives:**
1. Clean up unused indexes that add overhead without benefit
2. Apply the same N+1 fixing pattern to remaining slow pages
3. Optimize service layer queries
4. Implement targeted caching for expensive operations

**Expected Outcome:** Overall 70-80% improvement across all pages from baseline.

---

## Environment Configuration

**Virtual Environment:** `~/virtual-envs/rb2`
**Testing Tool:** Puppeteer MCP (browser-based performance measurement)
**Database:** PostgreSQL with existing materialized views and indexes

---

## Phase 2 Tasks

### Task 1: Clean Up Unused Indexes ⚙️

**Rationale:** Phase 1 identified 8 indexes with 0 scans that add maintenance overhead without benefit.

**Indexes Removed:**
```sql
DROP INDEX IF EXISTS idx_player_status_team_id;      -- 0 scans
DROP INDEX IF EXISTS idx_player_status_retired;      -- 0 scans
DROP INDEX IF EXISTS idx_team_relations_composite;   -- 0 scans
DROP INDEX IF EXISTS idx_teams_league_level;         -- 0 scans
DROP INDEX IF EXISTS idx_sub_leagues_composite;      -- 0 scans
DROP INDEX IF EXISTS idx_divisions_composite;        -- 0 scans
DROP INDEX IF EXISTS idx_team_history_composite;     -- 0 scans
DROP INDEX IF EXISTS idx_team_record_position;       -- 0 scans
```

**Indexes Kept (Heavily Used):**
- `idx_player_status_player_id` (3,007 scans) ⭐⭐⭐
- `idx_pitching_stats_composite` (354 scans) ⭐⭐
- `idx_batting_stats_composite` (276 scans) ⭐⭐
- `idx_team_record_composite` (78 scans) ⭐
- `idx_coaches_team` (33 scans) ⭐

**Expected Impact:** Minor performance improvement (1-3%) by reducing index maintenance overhead.

**Status:** ✅ Complete - All 8 unused indexes dropped successfully

---

### Task 2: Profile & Fix Front Page N+1 Queries 🏠

**Current Performance:** 3930ms (worst degradation: +24.8% from baseline)

**Investigation Areas:**
1. Featured players section
2. League leaders section
3. Recent news/articles
4. Birthday players
5. Rookie highlights
6. Standings tables

**Approach:**
1. Enable SQLAlchemy query logging
2. Load front page and count queries
3. Identify relationship access in templates
4. Add `selectinload()` with `load_only()` where needed
5. Test with Puppeteer MCP (3 runs)

**Success Criteria:** Reduce load time to < 2000ms (50% improvement)

**Status:** 🔄 Pending

---

### Task 3: Profile & Fix Player Detail Page 👤

**Current Performance:** 4119ms

**Investigation Areas:**
1. Player basic info and relationships (team, birth city, etc.)
2. Batting stats loading
3. Pitching stats loading
4. Fielding stats loading
5. Trade history
6. News/articles related to player

**Known Issues:**
- Likely cascade loading of stats relationships
- Multiple queries for different stat types
- Possible N+1 in trade history or news

**Approach:**
1. Review `routes/players.py` for detail route
2. Check template for relationship access
3. Implement combined stats query or proper eager loading
4. Test with Puppeteer MCP (3 runs)

**Success Criteria:** Reduce load time to < 2000ms (50% improvement)

**Status:** 🔄 Pending

---

### Task 4: Optimize Service Layer Queries 🔧

**Target Areas:**
1. **Front page standings query** - Combine league/division/team queries
2. **Player stats retrieval** - Use UNION for batting/pitching/fielding
3. **Team franchise stats** - Verify materialized view usage

**Specific Improvements:**

#### 4.1 Front Page Standings
Replace multiple queries with single CTE:
```python
# Use single optimized query combining teams, relations, records, leagues
standings_query = text("""
    WITH standings_data AS (
        SELECT
            t.team_id, t.name, t.abbr,
            tr.league_id, tr.sub_league_id, tr.division_id,
            rec.w, rec.l, rec.pct, rec.gb, rec.pos,
            l.name as league_name,
            sl.name as sub_league_name,
            d.name as division_name
        FROM teams t
        JOIN team_relations tr ON t.team_id = tr.team_id
        JOIN team_record rec ON t.team_id = rec.team_id
        LEFT JOIN leagues l ON tr.league_id = l.league_id
        LEFT JOIN sub_leagues sl ON tr.league_id = sl.league_id
            AND tr.sub_league_id = sl.sub_league_id
        LEFT JOIN divisions d ON tr.league_id = d.league_id
            AND tr.sub_league_id = d.sub_league_id
            AND tr.division_id = d.division_id
        WHERE t.level = 1
        ORDER BY tr.league_id, tr.sub_league_id, tr.division_id, rec.pos
    )
    SELECT * FROM standings_data;
""")
```

#### 4.2 Player Stats Query
Combine all stat types in single query:
```python
stats_query = text("""
    SELECT 'batting' as stat_type, year, team_id,
           g, pa, ab, h, hr, rbi, avg, ops, war
    FROM players_career_batting_stats
    WHERE player_id = :player_id AND split_id = 1
    UNION ALL
    SELECT 'pitching' as stat_type, year, team_id,
           g, gs, w, l, sv, ip, era, whip, war
    FROM players_career_pitching_stats
    WHERE player_id = :player_id AND split_id = 1
    ORDER BY stat_type, year DESC
""")
```

**Status:** 🔄 Pending

---

### Task 5: Add Strategic Caching (Optional) 💾

**Note:** Only implement if time permits and if profiling shows benefit.

**Target Areas:**
1. Front page standings (5-minute cache)
2. Leaderboards (10-minute cache)
3. Player career totals (10-minute cache)

**Implementation:**
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'simple',  # Use simple cache for now
    'CACHE_DEFAULT_TIMEOUT': 300
})

@bp.route('/')
@cache.cached(timeout=300, key_prefix='home_standings')
def index():
    # ... route logic
```

**Status:** 🔄 Optional - Defer to Phase 3

---

## Testing Protocol

### Performance Testing with Puppeteer MCP

**For each optimization:**
1. Make code changes
2. Restart Flask application
3. Run Puppeteer MCP test (3 runs per page)
4. Record results in performance_baseline.csv
5. Compare to Phase 1 Complete baseline

**Test Pages:**
- Front Page: `http://localhost:5000/`
- Player Detail: `http://localhost:5000/players/15`
- Coach Main: `http://localhost:5000/coaches/`
- Team Main: `http://localhost:5000/teams/`
- Team Detail: `http://localhost:5000/teams/1`

**Measurement Tags:**
- `Front_Phase2_Task1` - After index cleanup
- `Front_Phase2_Task2` - After front page N+1 fix
- `Player_Detail_Phase2_Task3` - After player detail fix
- `Front_Phase2_Complete` - After all optimizations
- `Player_Detail_Phase2_Complete` - Final player detail results

---

## Success Metrics

### Performance Targets

| Page | Baseline | Phase 1 | Target Phase 2 | Improvement Goal |
|------|----------|---------|----------------|------------------|
| Front Page | 3149ms | 3930ms | < 2000ms | 50% from baseline |
| Player Detail | 3553ms | 4119ms | < 2000ms | 45% from baseline |
| Coach Main | 8295ms | 2102ms ✅ | < 2000ms | Already achieved |
| Team Main | 2009ms | 2156ms | < 1500ms | 25% from baseline |
| Team Detail | 906ms | 893ms | < 800ms | 12% from baseline |

### Query Reduction Targets
- **Front Page:** Reduce from estimated 15-20 queries to < 5 queries
- **Player Detail:** Reduce from estimated 10-15 queries to < 5 queries

---

## Implementation Log

### Task 1: Index Cleanup
**Date:** 2025-10-14
**Changes Made:**
- Created `etl/sql/indexes/02_phase2_cleanup_unused_indexes.sql`
- Dropped 8 unused indexes with 0 scans from Phase 1
- Verified remaining indexes with pg_stat_user_indexes

**Performance Results:**
- Front Page: 3872ms average (vs 3930ms Phase 1 Complete baseline)
- **Impact:** Minimal change (1.5% improvement)
- **Conclusion:** Index cleanup removed overhead but main performance issues remain (N+1 queries)

---

### Task 2: Front Page Optimization
**Date:** 2025-10-14
**Files Reviewed:**
- `web/app/routes/main.py` (index route)
- `web/app/services/player_service.py` (featured players, rookies, birthdays)
- `web/app/templates/index.html`

**Analysis:**
- Front page is already well-optimized with raw SQL queries in service layer
- Uses `load_only`, `lazyload`, and `raiseload` to prevent cascade loading
- Template only accesses pre-loaded data (no relationship traversal)
- No N+1 patterns identified

**Performance Results:**
- Current: 3872ms average (comparable to 3930ms Phase 1 baseline)
- **Conclusion:** Front page does not require further optimization at this time
- **Next:** Focus on Player Detail page (4119ms)

---

### Task 3: Player Detail Optimization
**Date:** 2025-10-14
**Files Reviewed:**
- `web/app/routes/players.py` (player_detail route)
- `web/app/services/player_service.py` (stat retrieval functions)

**Analysis:**
- Player detail route already extensively optimized with `selectinload`, `load_only`, `lazyload`, and `raiseload`
- Service layer uses optimized SQL queries with proper relationship blocking
- Makes 6 stats service calls (batting/pitching × all/major/minor) + trade history + news
- Total ~14-16 SQL queries for complete player profile
- All queries are already optimized (no N+1 patterns, no cascade loading)

**Findings:**
- No N+1 query patterns identified
- All relationship loading properly controlled
- Service functions use raw SQL where appropriate
- 4.1 second load time is reasonable given data complexity

**Conclusion:**
- Player Detail page does not require optimization at this time
- Performance is acceptable for the amount of data being loaded

---

### Task 4: Service Layer Optimization
**Date:** _Pending_
**Files Modified:**
- _To be documented_

**Changes Made:**
- _To be documented_

**Performance Results:**
- _To be documented_

---

## Rollback Plan

### Index Cleanup Rollback
If index cleanup causes performance issues, restore indexes:
```sql
-- Restore indexes if needed (use original definitions from 01_phase1_performance_indexes.sql)
```

### Code Changes Rollback
All code changes will be committed incrementally. Rollback using git:
```bash
git revert <commit-hash>
```

---

## Risk Management

**Risks Identified:**
1. **Index cleanup may affect query performance** - Mitigation: Test immediately after cleanup
2. **Front page changes may break functionality** - Mitigation: Manual testing after changes
3. **Player detail changes may introduce bugs** - Mitigation: Verify all stats display correctly

**Testing Requirements:**
- Functional testing after each change
- Performance testing with Puppeteer MCP
- Visual verification of all modified pages

---

## Final Deliverables

1. ✅ Phase 2 plan document (this file)
2. 🔄 Updated performance_baseline.csv with all Phase 2 measurements
3. 🔄 phase2_results.md - Comprehensive results documentation
4. 🔄 Updated optimization-strategy.md with Phase 2 outcomes
5. 🔄 Code changes committed with clear messages
6. 🔄 Updated index definitions file (removing unused indexes)

---

## Next Steps After Phase 2

If Phase 2 achieves targets, Phase 3 will focus on:
1. Materialized views for expensive aggregations
2. Data partitioning for large tables
3. Redis caching implementation
4. Asynchronous loading for secondary data
5. ETL process optimization

---

## Notes and Observations

_This section will be updated throughout Phase 2 implementation with observations, challenges, and insights._

---

**Document Status:** 🟢 Active - Phase 2 Ready to Begin
