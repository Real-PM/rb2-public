
# Performance Profiling Guide

This guide explains how to use the comprehensive profiling system to identify performance bottlenecks in the RB2 application.

## Quick Start

### 1. Enable Profiling

Profiling is automatically enabled in `development` and `staging` environments via config:

```python
# web/app/config.py
class DevelopmentConfig(Config):
    ENABLE_PROFILING = True  # ✓ Enabled

class StagingConfig(Config):
    ENABLE_PROFILING = True  # ✓ Enabled
```

### 2. Run Profiling Tests

```bash
# Run on local development server
python scripts/run_profiling_tests.py --env development

# Run on staging server
python scripts/run_profiling_tests.py --env staging

# Custom iterations and output
python scripts/run_profiling_tests.py --env staging --iterations 5 --output my_results.json
```

### 3. Analyze Results

```bash
# Analyze single test run
python scripts/analyze_profiling_results.py profiling_results_staging_20251030_120000.json

# Compare two runs (before/after optimization)
python scripts/analyze_profiling_results.py \
    profiling_results_after.json \
    --compare profiling_results_before.json
```

## How It Works

### Profiling Infrastructure

The profiling system consists of three components:

#### 1. Profiling Decorator (`@profile_route`)

Wraps entire route execution with cProfile and custom timing:

```python
from app.utils.profiling import profile_route, timing_context

@bp.route('/players/<int:player_id>')
@profile_route('player_detail')  # ← Profiles entire route
def player_detail(player_id):
    # ... route code ...
```

#### 2. Timing Context Managers (`timing_context`)

Measure specific blocks of code:

```python
with timing_context('query_player_bio'):
    player = Player.query.filter_by(player_id=player_id).first_or_404()

with timing_context('query_batting_stats'):
    batting_stats = get_player_career_batting_stats(player_id)

with timing_context('render_template'):
    return render_template('players/detail.html', player=player)
```

#### 3. Logging Output

Profiling data is logged to application logs:

- **Development**: Flask console output
- **Staging**: systemd journal (`journalctl -u rb2-staging.service`)

## Understanding Profiling Output

### Timing Breakdown

```
================================================================================
PROFILE: player_detail
Total Time: 16734.56ms
--------------------------------------------------------------------------------
Timing Breakdown:
  query_batting_stats_major                     4521.34ms ( 27.0%)
  query_pitching_stats_major                    3842.12ms ( 23.0%)
  render_template                               3214.87ms ( 19.2%)
  query_batting_stats_minor                     2134.56ms ( 12.8%)
  query_player_bio                              1432.21ms (  8.6%)
  query_pitching_stats_minor                    1098.43ms (  6.6%)
  convert_dicts_to_objects                       287.91ms (  1.7%)
  query_trade_history                            145.23ms (  0.9%)
  cache_check                                      3.12ms (  0.0%)
  cache_store                                      1.89ms (  0.0%)
--------------------------------------------------------------------------------
```

This tells you:
- **Total time**: 16.7 seconds for the entire request
- **Biggest bottleneck**: Batting stats queries (27% of time)
- **Second bottleneck**: Pitching stats queries (23% of time)
- **Third bottleneck**: Template rendering (19% of time)
- **Caching is fast**: <5ms (good!)

### cProfile Output

```
Top Functions (by cumulative time):
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
      1    0.023    0.023   16.735   16.735 {built-in method builtins.exec}
      1    0.012    0.012   16.712   16.712 players.py:147(player_detail)
      8    0.001    0.000   12.596    1.575 {method 'execute' of 'psycopg2.extensions.cursor' objects}
      1    0.002    0.002    3.215    3.215 environment.py:1284(render)
     34    0.456    0.013    1.234    0.036 player_service.py:95(<listcomp>)
```

This shows:
- Database queries (`psycopg2.extensions.cursor`) taking 12.6 seconds
- Template rendering (`environment.py:1284`) taking 3.2 seconds
- Dictionary conversion taking 1.2 seconds

## Interpreting Results

### Cold Load vs Warm Load

- **Cold load**: First request with empty cache (real-world new user experience)
- **Warm load**: Subsequent requests with populated cache

Example output:
```
Player Detail          #1           17234.56ms      ✓  ← Cold load
Player Detail          #2             124.23ms      ✓  ← Warm load (cache hit)
Player Detail          #3             118.45ms      ✓  ← Warm load (cache hit)
```

**Cache improvement**: 17234ms → 120ms average = **99.3% faster!**

### Performance Thresholds

Based on analysis script output:

- **<100ms**: ✓ Excellent - no optimization needed
- **100-500ms**: ○ Good - acceptable for most pages
- **500-2000ms**: △ Acceptable - could be improved
- **2000-5000ms**: ⚠ Slow - optimization recommended
- **>5000ms**: ✗ CRITICAL - immediate action required

## Common Bottlenecks

### 1. Database Queries

**Symptoms**:
- High cumulative time in `psycopg2.extensions.cursor`
- Multiple query timing blocks with high percentages

**Solutions**:
- Add missing indexes
- Use `EXPLAIN ANALYZE` to check query plans
- Consolidate multiple queries into one
- Use raw SQL for complex queries (avoid ORM overhead)
- Implement eager loading with `selectinload()` to prevent N+1

### 2. Template Rendering

**Symptoms**:
- High time in `render_template` timing block
- High time in `jinja2.environment` functions

**Solutions**:
- Move logic from templates to Python
- Reduce number of loops in templates
- Pre-process data before passing to template
- Check for lazy-loaded relationships accessed in loops

### 3. Python Processing

**Symptoms**:
- High time in service layer functions
- High time in dictionary/list comprehensions

**Solutions**:
- Profile with cProfile to find slow functions
- Optimize data transformations
- Consider caching expensive calculations
- Use generators instead of lists where possible

### 4. Network/Database Latency

**Symptoms**:
- Many fast queries but slow overall time
- Query execute time < total time by large margin

**Solutions**:
- Reduce number of round-trips
- Batch queries together
- Use connection pooling effectively
- Consider database co-location

## Example Workflow

### Finding and Fixing a Bottleneck

1. **Run profiling tests**:
   ```bash
   python scripts/run_profiling_tests.py --env staging
   ```

2. **Analyze results**:
   ```bash
   python scripts/analyze_profiling_results.py profiling_results_staging_*.json
   ```

3. **Review output**:
   ```
   CRITICAL (>5s average):
      • Player Detail: 16734.56ms avg
        - Cold load: 17234.56ms
        - Warm loads: 121.34ms (99.3% faster)
        ⚠ Good cache effectiveness, focus on cold load optimization
   ```

4. **Check detailed profiling logs**:
   ```bash
   journalctl -u rb2-staging.service -n 200 | grep "PROFILE: player_detail" -A 30
   ```

5. **Identify bottleneck**:
   ```
   Timing Breakdown:
     query_batting_stats_major    4521.34ms (27.0%)  ← THIS!
     query_pitching_stats_major   3842.12ms (23.0%)  ← THIS!
     render_template              3214.87ms (19.2%)
   ```

6. **Drill down further**:
   - If query is slow: Add indexes, optimize query
   - If query is fast but called many times: Consolidate queries
   - If template is slow: Profile template rendering separately

7. **Implement fix and re-test**:
   ```bash
   # After making changes
   python scripts/run_profiling_tests.py --env staging --output after_fix.json

   # Compare before and after
   python scripts/analyze_profiling_results.py \
       after_fix.json \
       --compare profiling_results_staging_before.json
   ```

8. **Verify improvement**:
   ```
   PERFORMANCE COMPARISON
   Baseline:  2025-10-30T10:00:00
   Current:   2025-10-30T11:30:00

   Route                  Baseline        Current         Change          Status
   -------------------------------------------------------------------------------
   Player Detail          16734.56ms      4521.23ms       -73.0%          ✓ Improved
   ```

## Best Practices

1. **Always profile with cache cleared first** to measure cold load performance
2. **Run multiple iterations** (3-5) to account for variance
3. **Profile in staging** environment that matches production data/hardware
4. **Save baseline results** before making changes for comparison
5. **Profile individual operations** using `timing_context` for granular data
6. **Review cProfile output** for Python-level bottlenecks
7. **Check both cold and warm loads** to ensure caching works correctly

## Troubleshooting

### Profiling Not Working

**Check configuration**:
```python
# web/app/config.py
ENABLE_PROFILING = True  # Must be True
```

**Check logs are being generated**:
```bash
# Development
# Look for "PROFILE:" in Flask console

# Staging
journalctl -u rb2-staging.service -f | grep "PROFILE:"
```

### No Timing Breakdown

Ensure you're using `timing_context()` in your routes:
```python
with timing_context('operation_name'):
    # code to time
```

### Incomplete cProfile Output

Increase the number of functions shown:
```python
# In app/utils/profiling.py
stats.print_stats(30)  # Shows top 30 (default)
stats.print_stats(50)  # Shows top 50
```

## Files Reference

- **Profiling utility**: `web/app/utils/profiling.py`
- **Configuration**: `web/app/config.py`
- **Test runner**: `scripts/run_profiling_tests.py`
- **Analysis script**: `scripts/analyze_profiling_results.py`
- **Routes with profiling**:
  - `web/app/routes/players.py` - Player routes
  - `web/app/routes/main.py` - Home page
  - `web/app/routes/teams.py` - Team routes

## Next Steps

After identifying bottlenecks with profiling:

1. **Optimize queries**: Add indexes, use raw SQL, consolidate queries
2. **Optimize templates**: Move logic to Python, pre-process data
3. **Add caching**: Use `@cache.memoize()` for expensive operations
4. **Consider async**: Load secondary data via AJAX for faster initial render
5. **Monitor production**: Set up continuous performance monitoring

For optimization strategies, see:
- `docs/optimization/optimization-strategy.md`
- Previous session docs in `docs/optimization/`
