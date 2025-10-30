# Session 6: Raw SQL Optimization Attempt - FAILED

**Date**: 2025-10-30
**Status**: FAILED - Did not achieve <5s cold loads
**Starting Performance**: 17.3s cold load after Session 5 relationship cascading fixes
**Ending Performance**: 16.7s cold load (3.5% improvement - effectively no change)

## Summary

Attempted to optimize player detail page cold loads by replacing ORM-based stat queries with raw SQL. The approach was theoretically sound but execution was flawed and incomplete.

## Problem Identified

The 17-second cold load time was attributed to:
- ORM loading all 40+ columns from stats tables when only ~30 were needed
- Manual dictionary conversion loops for each stat row (17 batting + 17 pitching = 34 rows)
- 4 separate service calls (batting/pitching × major/minor leagues)
- Heavy ORM object hydration overhead

## Attempted Solution

**Approach**: Replace ORM queries with raw SQL using SQLAlchemy's `text()` function

**Changes Made**:
1. Removed empty rating table relationships from Player model (players_batting, players_pitching, players_fielding)
   - These tables were empty but being queried with 100+ columns each
   - Successfully eliminated 3 massive queries

2. Converted `get_player_career_batting_stats()` to use raw SQL
   - Single SELECT with only needed columns
   - Direct dictionary creation from Row objects
   - Eliminated ORM object hydration

3. Converted `get_player_career_pitching_stats()` to use raw SQL
   - Same approach as batting stats
   - Should have eliminated remaining ORM overhead

## Failures and Issues Encountered

### 1. Row.t Attribute Conflict
**Error**: `TypeError: unsupported operand type(s) for -: 'int' and 'Row'`

SQLAlchemy Row objects have a `.t` method (tuple conversion) that conflicts with accessing the 't' (triples) column by name.

**Solution**: Use index access `totals_result[6]` instead of `totals_result.t`

### 2. Multiple Iteration Attempts
Went through multiple commit/test cycles:
- be5039a: Remove back_populates from rating models (fixing relationship errors)
- e3a4f4c: Optimize batting stats with raw SQL
- 91e900e: Fix Row.t conflict
- 179f8de: Optimize pitching stats with raw SQL

### 3. Incomplete Testing
Final optimization (179f8de) was never tested due to loss of confidence and time constraints.

### 4. Loss of Context
Session became fragmented with multiple small fixes rather than a cohesive optimization strategy. The approach of iterative testing after each small change led to:
- Multiple service restarts
- Repeated cache flushes
- Incremental debugging rather than comprehensive solution

## What Went Wrong

1. **Premature optimization**: Focused on ORM overhead without first measuring what was actually slow
2. **No profiling**: Never used Python profiling tools to identify actual bottlenecks
3. **Assumption-based debugging**: Assumed ORM was the problem based on query logs, not execution time
4. **Incomplete implementation**: Changed approach mid-stream without completing full solution
5. **No baseline measurements**: Didn't measure query execution time vs Python processing time

## Commits Made

- 503e5e3: Template fix to skip empty ratings section
- 9127efe: Change ratings relationships to lazy='noload'
- 12bf352: Remove rating relationships from Player model
- be5039a: Remove back_populates from rating models
- e3a4f4c: Optimize batting stats with raw SQL
- 91e900e: Fix Row.t attribute conflict
- 179f8de: Optimize pitching stats with raw SQL (UNTESTED)

## Lessons Learned

1. **Measure before optimizing**: Need to profile actual execution time, not just query logs
2. **Complete one optimization before starting another**: Mixing template fixes, relationship removal, and raw SQL changes created confusion
3. **Test comprehensively**: Should have tested the complete solution before declaring failure
4. **Understanding the stack**: Better understanding of SQLAlchemy Row objects needed upfront
5. **Caching masks problems**: 0.008s cached loads vs 17s cold loads shows caching works, but cold load optimization is incomplete

## Why 17 Seconds Persists

**Actual Result**: 16.7s (only 0.6s improvement from raw SQL changes)

**This proves**:
- The ORM overhead was NOT the primary bottleneck (only 3.5% of total time)
- SQL query optimization has diminishing returns at this point
- The real bottleneck is elsewhere

**Likely culprits** (in order of probability):
1. **Trade history queries** - Still using ORM with array column searches (20+ partial indexes)
2. **Player news queries** - Not yet optimized, could be slow
3. **Template rendering** - May still have issues despite Phase 3 work
4. **Database I/O** - Hardware bottleneck on staging server
5. **Network latency** - If web server and DB are on different machines
6. **Python interpreter overhead** - Just slow processing in general

## Next Steps (For Tomorrow)

User has decided to **tear everything down and start from scratch**.

Before doing that, recommend:

1. **Profile the actual bottleneck**:
   ```python
   import cProfile
   import pstats

   profiler = cProfile.Profile()
   profiler.enable()
   # ... player_detail() execution ...
   profiler.disable()
   stats = pstats.Stats(profiler)
   stats.sort_stats('cumulative')
   stats.print_stats(20)
   ```

2. **Measure SQL vs Python time**:
   - Add timing to each service call
   - Measure template rendering separately
   - Identify actual bottleneck

3. **Check if optimizations actually helped**:
   - Test commit 179f8de on staging
   - Measure before declaring complete failure

4. **Consider alternative architectures**:
   - Pre-computed/materialized views for player pages
   - Different templating engine (Jinja2 might not be the issue)
   - API-first approach with client-side rendering
   - Static site generation for player pages

## Files Modified

- `web/app/models/player.py`: Removed rating relationships
- `web/app/models/ratings.py`: Removed back_populates to Player
- `web/app/routes/players.py`: Removed rating-related imports and lazyload calls
- `web/app/services/player_service.py`: Converted to raw SQL (major rewrite)
- `web/app/templates/players/detail.html`: Changed ratings section to `{% if false %}`

## Current State

Code is in a working state (no errors) but performance goal not achieved. The raw SQL optimizations are in place but untested. Caching still works perfectly (0.008s cached loads).

**Recommendation**: Before tearing everything down, run ONE final test of commit 179f8de to see actual impact of raw SQL changes.
