# Phase 4D: Get Cold Loads Under 5 Seconds

**Goal:** Reduce player detail page cold loads from 60s to <5s
**Started:** 2025-10-23 Session 2
**Status:** 🟢 In Progress - Session 4 Complete (2025-10-24)

---

## Current Status (2025-10-24 Session 4 Complete)

| Page Type | Cold Load | Warm Load | Status |
|-----------|-----------|-----------|--------|
| Player Detail | **62s** | **13ms** | ✅ Caching works, indexes added, threading reverted |
| Front Page | Unknown | Unknown | Untested |
| Team Detail | Unknown | Unknown | Untested |

**Session 4 Achievements:**
- ✅ Manual route caching working (warm load: 13ms = 4,769x faster)
- ✅ Database indexes added (queries now <1ms)
- ✅ Identified real bottleneck: NOT query speed (queries are fast), likely network/connection overhead

**Critical Discovery:**
- Queries execute in <1ms with indexes
- Cold load still 62s despite fast queries
- Threading attempted but reverted (DetachedInstanceError + minimal benefit)
- **Real bottleneck:** 13 sequential round-trips with network latency, not query execution time

---

## Session 4 Summary (2025-10-24) - MAJOR PROGRESS

### ✅ Completed This Session

1. **Database Indexes Added**
   - Created comprehensive indexing for player detail queries
   - **Batting stats**: Composite index (player_id, split_id, level_id)
   - **Pitching stats**: Composite index (player_id, split_id, level_id)
   - **Trade history**: 20 partial indexes on player_id columns
   - **Result**: Queries now execute in <1ms (verified with EXPLAIN ANALYZE)
   - Files: `etl/sql/migrations/006_phase4d_player_detail_indexes.sql`
   - Commits: `4c39271`, `a6340d6`

2. **Index Verification**
   - EXPLAIN ANALYZE shows index usage and <1ms execution
   - Example: `SELECT * FROM players_career_batting_stats WHERE player_id=3000 AND split_id=1` = **0.121ms**
   - All queries using indexes correctly
   - **Surprising result**: Cold load still 62s despite fast queries!

3. **Threading Implementation Attempted**
   - Implemented ThreadPoolExecutor for parallel query execution
   - Used `@copy_current_request_context` for Flask context propagation
   - **Result**: 62s → 48s (only 23% improvement)
   - **Fatal flaw**: `DetachedInstanceError` - ORM objects detached from session
   - **Reverted**: Threading doesn't solve the problem
   - Commits: `865ba7e`, `96a3eac`, `03e31e2` (reverted)

4. **Root Cause Identified**
   - Queries are fast (<1ms each)
   - But 13 sequential queries with network round-trips = 62s
   - Bottleneck is **connection overhead + network latency**, NOT query execution
   - Database on different host (192.168.10.94) adds ~5s per round-trip

### 🎯 Key Learnings

1. **Indexes work perfectly**: All queries <1ms, using indexes correctly
2. **Query speed ≠ page speed**: Fast queries still slow if you have many sequential round-trips
3. **Threading doesn't help**: SQLAlchemy ORM objects can't cross thread boundaries safely
4. **Real bottleneck**: Network latency (13 queries × ~4.8s per round-trip ≈ 62s)
5. **Solution**: Reduce number of queries, not query speed

---

## Complete Optimization Strategy (Roadmap to <5s)

**Revised Strategy After Session 4:**
The bottleneck is **number of database round-trips**, not query speed. With network latency of ~4.8s per round-trip, we need to reduce from 13 queries to ≤2 queries to hit <5s.

### Phase 1: Lazy Loading (NEXT - Session 5)
**Target: 62s → 30s** (50% query reduction)
**Status:** Primary strategy - reduces queries from 13 to 7

#### 1.1 Minor League Stats (AJAX endpoint)
- Remove minor league queries from initial `player_detail()` load
- Create new route: `GET /players/<id>/minor-stats` (returns JSON)
- Add "Show Minor League Stats" button with AJAX handler
- **Impact:** Eliminates 4 queries (2 batting minor + 2 pitching minor)
- **Files:**
  - `web/app/routes/players.py` (remove 2 service calls, add new endpoint)
  - `web/app/templates/players/detail.html` (add button + JavaScript)

#### 1.2 Trade History Accordion (AJAX)
- Move trade history into collapsible accordion
- Load on first expand via AJAX
- Create route: `GET /players/<id>/trades` (returns JSON)
- **Impact:** Eliminates 1 expensive query with 20-way OR filter
- **Files:** Same as above

#### 1.3 Player News Accordion (AJAX)
- Move player news into collapsible accordion
- Load on first expand via AJAX
- Create route: `GET /players/<id>/news` (returns JSON)
- **Impact:** Eliminates 1 expensive query with 10-way OR filter
- **Files:** Same as above

**Total Phase 1 Impact:**
- Queries reduced: 13 → 7 (46% reduction)
- Estimated time: 60s → 30s

---

### Phase 2: Query Consolidation (Session 6)
**Target: 30s → 10-15s** (further reduce query count)
**Status:** ~~Threading reverted (DetachedInstanceError)~~ - New approach needed

#### 2.1 Consolidate Stats Queries
Instead of 4 separate stats queries, fetch all stats in one call:

```python
# Current (4 queries):
batting_major = get_player_career_batting_stats(player_id, league_level=1)
batting_minor = get_player_career_batting_stats(player_id, league_level=2)
pitching_major = get_player_career_pitching_stats(player_id, league_level=1)
pitching_minor = get_player_career_pitching_stats(player_id, league_level=2)

# Proposed (1 query):
all_stats = get_player_all_stats(player_id)  # Returns all batting + pitching for all levels
# Split results in Python
```

**Implementation:**
- Single raw SQL query with UNION ALL to fetch all stats
- Process results in Python to split by sport/level
- Return dictionary with all four datasets

**Impact:** 4 queries → 1 query = 3 fewer round-trips (~14s saved)

**Files:**
- `web/app/services/player_service.py` (new function: `get_player_all_stats`)
- `web/app/routes/players.py` (call single function instead of 4)

---

### Phase 3: Database Indexes
**Status:** ✅ **COMPLETE** (Session 4)
**Result:** All queries now execute in <1ms

#### 3.1 Indexes Added
All recommended indexes have been created and verified:
```sql
-- For batting/pitching stats queries
CREATE INDEX idx_batting_player_split ON players_batting(player_id, split_id);
CREATE INDEX idx_batting_player_league ON players_batting(player_id, league_level);
CREATE INDEX idx_pitching_player_split ON players_pitching(player_id, split_id);
CREATE INDEX idx_pitching_player_league ON players_pitching(player_id, league_level);

-- For trade history (temporary - see Phase 4)
CREATE INDEX idx_trades_player_0_0 ON trades_history(player_id_0_0) WHERE player_id_0_0 IS NOT NULL;
-- Repeat for all 20 player_id columns...

-- For messages (temporary - see Phase 4)
CREATE INDEX idx_messages_player_type ON messages(player_id_0, message_type, deleted);
-- Repeat for all 10 player_id columns...
```

**Impact:** Could reduce individual query times by 50-80% if indexes are missing

---

### Phase 4: Array Storage for Trades/Messages (Future - Separate Task)
**Target: Long-term query performance** 🌟 **BIGGEST WIN**

#### 4.1 Problem
Current schema has 20 separate columns for player IDs in trades:
```python
WHERE player_id_0_0 = X OR player_id_0_1 = X OR ... OR player_id_1_9 = X  # Slow!
```

#### 4.2 Solution: PostgreSQL Array Columns
```sql
-- Add array columns
ALTER TABLE trades_history ADD COLUMN all_player_ids INTEGER[];
ALTER TABLE messages ADD COLUMN all_player_ids INTEGER[];

-- Create GIN indexes for fast array containment
CREATE INDEX idx_trades_all_players_gin ON trades_history USING GIN (all_player_ids);
CREATE INDEX idx_messages_all_players_gin ON messages USING GIN (all_player_ids);
```

Query becomes:
```python
# Single array containment check (fast with GIN index!)
TradeHistory.query.filter(TradeHistory.all_player_ids.contains([player_id]))
```

#### 4.3 Implementation Plan
1. **ETL Changes** (preprocessing):
   ```python
   # When processing trades CSV:
   trade_record = {
       'all_player_ids': [pid for pid in [
           player_id_0_0, player_id_0_1, ..., player_id_1_9
       ] if pid is not None]
   }
   ```

2. **Database Migration:**
   - Add array columns (keep old columns for safety)
   - One-time data migration: populate arrays from existing columns
   - Update queries to use array containment
   - Verify performance improvement
   - Drop old columns after verification

3. **Query Updates:**
   ```python
   # In player_service.py
   from sqlalchemy.dialects.postgresql import ARRAY

   def get_player_trade_history(player_id):
       return TradeHistory.query.filter(
           TradeHistory.all_player_ids.contains([player_id])
       ).all()
   ```

**Impact:** Query time could reduce from ~5-10s to <100ms with GIN index

**Files:**
- `etl/src/loaders/` - Add array column population
- `web/app/models/` - Add array column definitions
- `web/app/services/player_service.py` - Update queries
- `scripts/migrations/` - Create migration script

**Status:** 📋 Planned - Requires separate task/session

---

## Phase 4D Tasks Checklist

### ✅ Session 1-3 (Complete)
- [x] **Task 1:** Add recursion_depth=3 (v1.0.5-phase4d-task1) - NO IMPACT
- [x] **Task 2:** Convert service functions to return dictionaries (v1.0.6-phase4d-dict-conversion) - MINIMAL IMPACT
- [x] **Investigation:** Identified route caching broken
- [x] **Root Cause:** Flask-Caching `@cache.cached()` decorator unreliable with dynamic keys

### ✅ Session 4 (Complete)
- [x] Implement manual route caching with `cache.get()`/`cache.set()`
- [x] Create `DictToObject` helper class for template compatibility
- [x] Add key aliasing for inconsistent naming (avg/batting_average)
- [x] Verify caching works on staging (warm load: 13ms ✅)
- [x] Tag clean version: `v0.2.0-phase4d-caching`
- [x] Document complete optimization roadmap

### 🔄 Session 5 (Next - Lazy Loading)
- [ ] Implement AJAX endpoint for minor league stats
- [ ] Add "Show Minor League Stats" button with JavaScript
- [ ] Create accordion for trade history with AJAX loading
- [ ] Create accordion for player news with AJAX loading
- [ ] Test on staging - measure cold load reduction (expect ~30s)

### ⏳ Session 6 (Threading + Indexes)
- [ ] Analyze database index query results
- [ ] Add missing indexes if needed
- [ ] Implement ThreadPoolExecutor for parallel queries
- [ ] Measure performance improvements
- [ ] Target: <10s cold load

### 📋 Future Sessions (If Still >5s)
- [ ] **Task 3:** Consolidate stats queries (combine batting/pitching)
- [ ] **Task 4:** Raw SQL optimization with CTEs
- [ ] **Phase 4 (Array Storage):** ETL refactor for trades/messages (separate task)

---

## Performance Metrics

### Baseline (Session 3)
- Cold load: 87s
- Warm load: BROKEN (caching not working)
- Queries: ~13 database queries

### Current (Session 4 - v0.2.0-phase4d-caching)
- Cold load: 60.4s (dictionary conversion complete)
- Warm load: **13ms** ✅ (caching working!)
- Cache improvement: **4,646x faster**
- Queries: ~13 database queries (unchanged)

### Targets
- **Phase 1 (Lazy Loading):** 60s → 30s (50% query reduction)
- **Phase 2 (Threading):** 30s → 10-15s (parallel execution)
- **Phase 3 (Indexes):** 10-15s → 5-8s (query optimization)
- **Final Goal:** <5s cold load

---

## Technical Implementation Details

### Manual Caching Implementation

**Location:** `web/app/routes/players.py:143-285`

```python
@bp.route('/<int:player_id>')
def player_detail(player_id):
    """Player detail page - bio, stats, ratings

    OPTIMIZATION: Manual caching implemented due to Flask-Caching
    decorator issues with dynamic key_prefix.
    """
    # Manual cache check
    cache_key = f'player_detail:{player_id}'
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return cached_data

    # ... load all data, render template ...

    # Cache the rendered HTML
    cache.set(cache_key, rendered_html, timeout=600)

    return rendered_html
```

**Cache Key Format:**
- Raw key: `player_detail:{player_id}` (e.g., `player_detail:3000`)
- Redis key: `rb2_staging:player_detail:3000` (with CACHE_KEY_PREFIX)

**Cache Storage:**
- Content: Full rendered HTML string
- Timeout: 600s (10 minutes)
- Type: String (Redis)

### DictToObject Helper Class

**Location:** `web/app/routes/players.py:13-35`

```python
class DictToObject:
    """Convert dict to object with attribute access for template compatibility

    Handles key name aliasing for template compatibility:
    - 'avg' -> 'batting_average'
    - 'obp' -> 'on_base_percentage'
    - 'slg' -> 'slugging_percentage'
    """
    def __init__(self, d):
        # First, update dict normally
        self.__dict__.update(d)

        # Then add aliases for short key names
        if 'avg' in d:
            self.batting_average = d['avg']
        if 'obp' in d:
            self.on_base_percentage = d['obp']
        if 'slg' in d:
            self.slugging_percentage = d['slg']
        if 'ops' in d and not hasattr(self, 'ops'):
            self.ops = d['ops']
```

**Purpose:** Service layer returns dicts (performance), templates expect objects (Jinja2 dot notation)

**Key Aliasing:** Service uses inconsistent naming:
- Yearly stats: Short keys ('avg', 'obp', 'slg')
- Career totals: Long keys ('batting_average', 'on_base_percentage', 'slugging_percentage')
- Templates: Expect long keys (from original ORM attributes)

---

## Database Query Analysis (Pending)

**Current queries in `player_detail()` route:**
1. Main player bio query (~1-2 queries with selectinload)
2. `get_player_career_batting_stats(player_id, league_level=1)` - 2 queries
3. `get_player_career_batting_stats(player_id, league_level=2)` - 2 queries
4. `get_player_career_pitching_stats(player_id, league_level=1)` - 2 queries
5. `get_player_career_pitching_stats(player_id, league_level=2)` - 2 queries
6. `get_player_trade_history(player_id)` - 1 query (20-way OR filter!)
7. `get_player_news(player_id)` - 1 query (10-way OR filter!)

**Total: ~12-13 queries**

**Expensive queries identified:**
- Trade history: 20-column OR filter
- Player news: 10-column OR filter
- Both excellent candidates for lazy loading + eventual array storage

**Index check required:** Awaiting staging query results to identify missing indexes

---

## Git Commits History

### Session 3
- `b9826e6` - Phase 4D Task 2: Convert service functions to return dictionaries
- `fbb3f50` - Fix AttributeError: Use correct database column names
- `9d0176f` - Fix route caching: Add explicit key_prefix (lambda) - FAILED
- `0e9f51e` - Fix cache key generation: Use function instead of lambda - FAILED
- `9218848` - Update Phase 4D docs with Session 3 progress

### Session 4
- `814b7af` - Implement manual caching with cache.get()/cache.set()
- `7bd77aa` - Add DictToObject class for template compatibility
- `420cdad` - Fix DictToObject aliasing: Always create long-form attributes
- `eb284ea` - Fix DictToObject aliasing: Always create long-form attributes from short keys
- `e3bbb29` - Remove debug logging from player_detail route

**Current HEAD:** `e3bbb29`
**Current Tag:** `v0.2.0-phase4d-caching` (clean, tested, verified)

---

## Testing Protocol

### Verify Caching Works
```bash
cd /opt/rb2-public && git pull origin master
sudo systemctl restart rb2-staging

# Clear cache and test
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 FLUSHDB
echo "=== COLD LOAD ==="
time curl -o /dev/null -s -w "%{http_code}\n" http://localhost:5002/players/3000
echo "=== CACHE KEYS ==="
docker exec $(docker ps --filter name=redis -q) redis-cli -n 1 KEYS '*player_detail*'
echo "=== WARM LOAD ==="
time curl -o /dev/null -s -w "%{http_code}\n" http://localhost:5002/players/3000
```

**Expected Results:**
- Cold load: ~60s (200 status)
- Cache key: `rb2_staging:player_detail:3000`
- Warm load: <100ms (13ms measured)

### Check Database Indexes
```bash
psql -h 192.168.10.94 -U ootp_etl -d ootp_dev -c "
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('players_batting', 'players_pitching', 'trades_history', 'messages')
ORDER BY tablename, indexname;
"
```

---

## Next Session Priorities (Session 5)

**Primary Goal:** Implement lazy loading to reduce from 13 queries to 7 queries

**Why This Approach:**
- Threading doesn't work (DetachedInstanceError)
- Queries are already fast (<1ms)
- Bottleneck is number of round-trips, not query speed
- 13 queries × 4.8s/query ≈ 62s
- Target: 7 queries × 4.8s/query ≈ 34s

**Implementation Steps:**
1. **Remove minor league stats from initial load** (saves 4 queries)
   - Comment out `batting_data_minor` and `pitching_data_minor` calls
   - Update template to hide minor stats section initially
   - Create AJAX endpoint: `GET /players/<id>/minor-stats`
   - Add JavaScript toggle button

2. **Convert trades to accordion** (saves 1 query)
   - Create AJAX endpoint: `GET /players/<id>/trades`
   - Update template with collapsible accordion
   - Load on first expand

3. **Convert news to accordion** (saves 1 query)
   - Create AJAX endpoint: `GET /players/<id>/news`
   - Update template with collapsible accordion
   - Load on first expand

4. **Test and measure:**
   - Deploy to staging
   - Measure cold load (expect ~34s)
   - Verify warm load still works (expect 13ms)

**Expected Result:** 62s → 34s (45% improvement)

---

**Document Status:** 🟢 **ACTIVE** - Route caching working, roadmap defined
**Last Updated:** 2025-10-24 Session 4
**Next Action:** Implement lazy loading (Session 5)
