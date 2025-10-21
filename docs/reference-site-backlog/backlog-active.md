# RB2 Website Development Backlog - Active Epics

**Last Updated:** 2025-10-13 (Session 16)
**Current Sprint Focus:** Front Page & Infrastructure
**Database State:** 18 seasons of history (1980-1997), Currently in June 1997 season

**Note:** This file contains incomplete epics only (Epics 4, 7, 8, 9). For completed epics (1-3, 5-6), see `backlog-completed.md`

---

## Priority Legend
- **CRITICAL:** Blocking core functionality, must be done immediately
- **HIGH:** Essential features for launch, high user value
- **MEDIUM:** Important but not blocking, enhances user experience
- **LOW:** Nice-to-have, future enhancements
- **DEFERRED:** Not planned for initial release



## Status Legend
- **NOT STARTED:** Work not yet begun
- **IN PROGRESS:** Currently being worked on
- **BLOCKED:** Waiting on dependency or decision
- **DONE:** Complete and tested

---

## Epic 4: Front Page Enhancements

### US-F001: Two-Column Responsive Layout [DONE]
**Priority:** HIGH
**Effort:** 3-4 hours (Actual: ~1 hour)
**Status:** DONE (Session 12: 2025-10-11)
**Spec Reference:** Lines 52-65, 68-83

**Description:**
Restructure front page into two-column layout (desktop) that collapses on mobile.

**Acceptance Criteria:**
- [x] Desktop: Left column (40%) and Right column (60%) - Using `lg:col-span-2` and `lg:col-span-3` (2:3 ratio ≈ 40:60)
- [x] Mobile: Single column, left content first - `grid-cols-1` on mobile, left column renders first in DOM
- [x] Right column: Current standings (already done) - Preserved with minor formatting improvements
- [x] Left column: Placeholder sections for upcoming features - 3 cards: Featured Players, Notable Rookies, Born This Week
- [x] Responsive breakpoints at md: and lg: - Using `lg:` for main 2-column split, `xl:` for standings grid

**Implementation Notes:**
- **File Modified:** `/web/app/templates/index.html` (complete rewrite, 167 lines)
- **Layout:** Tailwind `grid grid-cols-1 lg:grid-cols-5` with `lg:col-span-2` (left) and `lg:col-span-3` (right)
- **Left Column Placeholders:**
  - Featured Players (US-F004 placeholder)
  - Notable Rookies (US-F002 placeholder)
  - Born This Week (US-F003 placeholder)
- **Right Column Enhancements:**
  - Standings preserved with improved spacing
  - Added "Quick Links" section with buttons to: Batting Leaders, Pitching Leaders, All Teams, All Players
  - Changed team display from full name to abbreviation for better fit
  - Adjusted padding to maximize space efficiency
- **Responsive Behavior:**
  - Mobile (<1024px): Single column, left content stacked above standings
  - Desktop (≥1024px): Two columns side-by-side, 40/60 split
  - Extra-wide (≥1280px): Standings split into 2 columns within right column

**Testing:**
- Page loads without errors
- Layout structure verified in HTML output
- Performance maintained (<100ms, 17 queries from Session 12 optimization)

**Dependencies:** None

---

### US-F002: Notable Rookies Widget [DONE]
**Priority:** HIGH
**Effort:** 6-8 hours (Actual: 1.5 hours)
**Status:** DONE (Session 13: 2025-10-11)
**Spec Reference:** Lines 57-58, 86-87

**Description:**
Display top 10 rookies (by WAR) in their first season at highest league level.

**Acceptance Criteria:**
- [x] Shows 10 players
- [x] Definition: First season at league_level=1 (experience <= 1)
- [x] Ranked by WAR
- [x] Display: Player name, team, position, WAR
- [x] Links to player pages
- [x] Card/list format with player images

**Implementation:**
- **Service Function:** `/web/app/services/player_service.py` - Added `get_notable_rookies()` (lines 546-700)
  - Queries both batting and pitching stats for current season (1997)
  - Combines WAR from both sources for dual-role players
  - Filters: league_level=1, experience<=1, retired=0, team_id!=0
  - Returns top 10 by combined WAR with team and position info
  - Optimized with load_only() and raiseload() to prevent cascading loads
- **Route Update:** `/web/app/routes/main.py` - Added rookies to index route (line 127)
- **Template Update:** `/web/app/templates/index.html` - Implemented widget with images (lines 63-103)
  - Player thumbnail images (45x68px, half size of full images)
  - Shows name (linked to player page), team abbreviation, position, WAR value
  - Hover effect on each row for better UX
  - Fallback for missing images ("No Photo" placeholder)

**Testing:**
- 10 rookies displayed (Antonio Reyes 1.1 WAR leads)
- All images loading correctly with proper sizing
- Links functional to player detail pages
- Data refreshes on each page load

**Dependencies:** US-F001 (left column layout)

---

### US-F003: Born This Week Widget [DONE]
**Priority:** MEDIUM
**Effort:** 3-4 hours (Actual: 1 hour)
**Status:** DONE (Session 13: 2025-10-12)
**Spec Reference:** Lines 59, 88, 96

**Description:**
Show players whose birthday is within 7 days of current game date.

**Acceptance Criteria:**
- [x] List of players with birthdays within +/- 7 days
- [x] Show: Player name, DOB, age, team
- [x] Links to player pages
- [x] Use game_date from league (not real-world date)

**Implementation:**
- **Service Function:** `/web/app/services/player_service.py` - Added `get_players_born_this_week()` (lines 826-953)
  - Fetches current game_date from leagues table (1997-06-01)
  - Calculates date range ±7 days (May 25 - June 8)
  - Extracts month/day from date_of_birth for comparison
  - Handles year wraparound (Dec 28 - Jan 4) with conditional SQL logic
  - **Updated 2025-10-21:** Reduced from 50 to 12 players, ordered by total career WAR
  - Joins `players_career_batting_stats` and `players_career_pitching_stats` for WAR ordering
  - ORDER BY: `(COALESCE(pcbs.war, 0) + COALESCE(pcps.war, 0)) DESC` (highest WAR first)
  - Calculates age as of game_date (not current year)
  - Includes retired flag for display
  - Position mapping for display
- **Route Update:** `/web/app/routes/main.py` - Added birthdays to index route (line 128)
- **Template Update:** `/web/app/templates/index.html` - Implemented widget (lines 106-137)
  - Shows player name (linked to detail page), team, position
  - Displays birthday as "Mon DD" format
  - Shows current age
  - Marks retired players with red "(Retired)" text
  - Hover effect on each row
  - Empty state: "No birthdays this week"

**Testing:**
- Widget displaying players with May 25 - June 8 birthdays (±7 days from June 1)
- Example: Wes Yeo (May 25, Age 42)
- Links to player detail pages functional
- Retired player indicators working
- Performance: No measurable impact on page load time

**Technical Notes:**
- Date comparison uses EXTRACT(MONTH) and EXTRACT(DAY) for year-agnostic matching
- Two query variants: one for normal ranges, one for year wraparound
- Uses raw SQL for optimal performance
- Age calculation: `age = game_date.year - birth_date.year` with adjustment if birthday hasn't occurred yet

**Dependencies:** US-F001

---

### US-F004: Random Player Image Grid [DONE]
**Priority:** MEDIUM
**Effort:** 4-6 hours (Actual: 1.5 hours)
**Status:** DONE (Session 13: 2025-10-11)
**Spec Reference:** Lines 56-57, 70-71, 87

**Description:**
Grid of random player images that changes on each page load, displayed as featured players.

**Acceptance Criteria:**
- [x] 18 random players with images
- [x] 6 columns x 3 rows on desktop (changed from 3x6 for better layout)
- [x] Responsive grid layout
- [x] Images link to player pages
- [x] Only select players with images available (filesystem check)
- [x] Hover effect shows player name, team, and position
- [x] Filter for league_level=1 (major league players only)

**Implementation:**
- **Service Function:** `/web/app/services/player_service.py` - Added `get_featured_players()` (lines 703-790)
  - Scans `/etl/data/images/players/` directory for `player_*.png` files
  - Extracts player IDs from filenames
  - Queries database for random active players from filtered list
  - Filters: has_image=true, league_level=1, retired=0, team_id!=0
  - Uses `ORDER BY RANDOM()` for randomization on each page load
  - Returns 18 players with name, team, position
- **Route Update:** `/web/app/routes/main.py` - Added featured_players to index route (line 126)
- **Template Update:** `/web/app/templates/index.html` - Implemented grid widget (lines 31-61)
  - 6-column grid layout (`grid-cols-6`)
  - Full player images with `object-contain` (no cropping)
  - Hover overlay with semi-transparent black background
  - Shows player name, team abbreviation, position on hover
  - Links to player detail page
  - Fallback for missing images

**Testing:**
- 18 featured players displaying in 6x3 grid
- Images load correctly at half size (no cropping)
- Hover overlay shows player info
- Links to player pages functional
- Randomization works on each page refresh
- Only major league players (league_level=1) displayed

**Dependencies:** US-F001 (left column layout), US-P004 (player images)

---

### US-F005: Magic Number in Standings [DEFERRED]
**Priority:** LOW
**Effort:** 4-6 hours
**Status:** DEFERRED (Session 14: 2025-10-13)
**Spec Reference:** Lines 62, 75-76

**Description:**
Calculate and display playoff magic numbers in standings tables.

**Acceptance Criteria:**
- [ ] Magic number column in standings tables
- [ ] Only show during relevant part of season
- [ ] Formula: (Games Remaining for Leader + 1) - (Leader Wins - Team Wins)
- [ ] Show "-" if team eliminated or already clinched

**Technical Notes:**
- `magic_number` field already exists in `TeamRecord` model (line 189)
- Unknown if ETL populates this field
- Requires conditional logic for when to display (in-season only)
- Needs elimination/clinched status determination
- Deferred until core navigation complete

**Deferral Reason:**
- Field exists but population status unclear
- Requires seasonal logic that's complex to verify
- LOW priority - better to complete navigation first

**Dependencies:** ETL magic_number population, games/schedule data understanding

---

### US-F006: League Summary Links [DONE]
**Priority:** MEDIUM
**Effort:** 2-3 hours (Actual: 15 minutes)
**Status:** DONE (Session 13: 2025-10-12)
**Spec Reference:** Lines 63-64, 89

**Description:**
Add links below each league's standings to league summary pages.

**Acceptance Criteria:**
- [x] Links: "League Leaders", "Team Stats", "Schedule"
- [x] Links go to appropriate league pages

**Implementation:**
- **Template Update:** `/web/app/templates/index.html` (lines 217-233)
  - Added centered inline link group below each league's standings
  - Three links separated by pipe dividers
  - "League Leaders" - Links to `/leaderboards/batting?league={league_id}` (working)
  - "Team Stats" - Placeholder link (#) for future implementation (US-LY001)
  - "Schedule" - Placeholder link (#) for future implementation
  - Clean, minimal styling with hover effects
  - Responsive design

**Testing:**
- All 4 leagues display links correctly (leagues 200, 201, 202, 203)
- League Leaders link works and filters to specific league
- Team Stats and Schedule links render as placeholders (will work when pages exist)
- Layout is clean and centered below standings

**Technical Notes:**
- Replaced previous "Quick Links" card with simpler inline link pattern
- League Leaders link already functional (leaderboard pages exist)
- Team Stats and Schedule will work once US-LY001 (League Home Pages) is implemented

**Dependencies:** None (placeholder links acceptable per requirements)

---

## Epic 7: Infrastructure & Performance

### US-I001: Redis Caching Infrastructure [DONE]
**Priority:** HIGH
**Effort:** 4-6 hours (Actual: ~3 hours)
**Status:** DONE (Session 17: 2025-10-15)
**Completed:** 2025-10-15
**Spec Reference:** Lines 667-682, Phase 3 optimization

**Description:**
Set up Redis for caching query results and computed values.

**Acceptance Criteria:**
- [x] Redis server deployed (multi-environment: dev/staging/prod)
- [x] Flask-Caching configured for Redis backend
- [x] Cache keys strategy defined (environment prefixes)
- [x] TTL strategy: 5 min (route cache), 10 min-24 hr (function cache)
- [x] Cache invalidation strategy planned
- [x] Fallback to SimpleCache if Redis unavailable

**Implementation Details:**
- **Configuration:** `web/app/config.py`
  - Development: Local Redis `localhost:6379/0` (shared with Ollama)
  - Staging: Centralized Redis `192.168.10.94:6379/1`
  - Production: Centralized Redis `192.168.10.94:6379/2`
  - Key prefixes: `rb2_dev:*`, `rb2_staging:*`, `rb2_prod:*`
- **Route-Level Caching:** `@cache.cached()` on front page (300s TTL)
- **Function-Level Caching:** `@cache.memoize()` on 5 player service functions
  - `get_player_career_batting_stats()` - 600s TTL
  - `get_player_career_pitching_stats()` - 600s TTL
  - `get_featured_players()` - 86400s TTL
  - `get_notable_rookies()` - 600s TTL
  - `get_players_born_this_week()` - 600s TTL

**Performance Impact:**
- Front page: 3,149ms → 5ms (cache hit) = **99.8% improvement**
- Player detail: 4,134ms → 2,658ms = **35.7% improvement**

**Technical Notes:**
- Flask-Caching 2.x with Redis backend
- Automatic serialization/deserialization
- Zero infrastructure overhead (shared Redis instance)

**Dependencies:** None

**See:** `docs/phase3_results.md` for complete implementation details

---

### US-I002: Database Indexes [DONE]
**Priority:** HIGH
**Effort:** 2-4 hours (actual: ~2 hours)
**Status:** DONE
**Spec Reference:** Lines 741-752
**Completed:** 2025-10-09

**Description:**
Add critical database indexes for query performance on player detail page queries.

**Acceptance Criteria:**
- [x] Analyzed current queries to identify missing indexes
- [x] Discovered most indexes already exist from ETL (batting_player_year, pitching_player_year, player names, etc.)
- [x] Added 20 indexes on trade_history player_id columns (player_id_0_0 through player_id_1_9)
- [x] Added 10 indexes on messages player_id columns (player_id_0 through player_id_9)
- [x] Used partial indexes with WHERE IS NOT NULL to optimize index size
- [x] Tested query performance before/after with EXPLAIN ANALYZE
- [x] Documented all indexes in DDL (etl/sql/tables/07_newspaper.sql)
- [x] Created migration script for existing databases (scripts/apply_performance_indexes.sql)

**Performance Improvements (EXPLAIN ANALYZE):**
- **Trade History Query** (player 16747, 4 trades):
  - BEFORE: 1.148ms (Sequential Scan of 2,097 rows)
  - AFTER: 0.667ms (Bitmap Index Scan using all 20 indexes)
  - **Improvement: 1.7x faster (42% reduction)**

- **Player News Query** (player 53425, 12 news stories):
  - BEFORE: 1.161ms (Bitmap Heap Scan filtering 1,819 rows)
  - AFTER: Expected similar improvement with BitmapOr on player indexes
  - Query now uses indexed lookups instead of filtering full result set

**Technical Implementation:**
- **Total Indexes Added: 30**
  - 20 on trade_history (all player_id slots)
  - 10 on messages (all player_id slots)
- Partial indexes with `WHERE column IS NOT NULL` to reduce index size
- PostgreSQL uses BitmapOr to combine multiple index scans efficiently
- ANALYZE run on both tables to update query planner statistics

**Files Modified:**
- `/etl/sql/tables/07_newspaper.sql` - Added index definitions to DDL
- `/scripts/apply_performance_indexes.sql` - Migration script for existing databases

**Scaling Notes:**
- Current improvements modest due to small table sizes (2,097 trades, 3,271 messages)
- Will scale much better as database grows (eliminates sequential scans)
- Bitmap index scans are O(log n) vs O(n) for sequential scans
- Future: Consider composite indexes for multi-column queries

**Dependencies:** None

---

### US-I003: Image Serving Infrastructure [DONE]
**Priority:** HIGH
**Effort:** 3-4 hours (Actual: ~2 hours)
**Status:** DONE (Multiple sessions)
**Completed:** 2025-10-12
**Spec Reference:** Player/team image requirements throughout

**Description:**
Set up efficient serving of player images and team logos.

**Acceptance Criteria:**
- [x] Flask routes to serve images directly from filesystem
- [x] Player images served from `/players/image/<player_id>`
- [x] Coach images served from `/coaches/image/<coach_id>`
- [x] League logos served from `/leagues/logo/<league_id>`
- [x] Lazy loading in templates
- [x] Fallback to initials for missing images

**Implementation Details:**
- **Routes:**
  - `web/app/routes/players.py`: `player_image()` route
  - `web/app/routes/coaches.py`: `coach_image()` route
  - `web/app/routes/leagues.py`: `league_logo()` route
- **Image Paths:**
  - Players: `etl/data/images/players/player_<player_id>.png`
  - Coaches: `etl/data/images/coaches/coach_<coach_id>.png`
  - Leagues: `etl/data/images/league_logos/<filename>.png`
- **Features:**
  - Direct filesystem serving via Flask `send_file()`
  - Predictable naming convention
  - Error handling with 404 responses
  - Template fallback with CSS initials

**Technical Notes:**
- No database overhead - predictable file paths
- Simple and performant approach
- CDN can be added later if needed

**Dependencies:** None

---

### US-I004: Query Optimization - Service Layer [DONE]
**Priority:** HIGH
**Effort:** 6-8 hours (Actual: ~10 hours across multiple sessions)
**Status:** DONE (Phases 1B, 2, 3)
**Completed:** 2025-10-15
**Spec Reference:** Lines 760-780, 827-834, Phase 1B/2/3

**Description:**
Refactor existing routes to use service layer for better performance and caching.

**Acceptance Criteria:**
- [x] Service layer architecture implemented
- [x] Player routes use `player_service.py`
- [x] Team routes use `team_service.py`
- [x] League routes use `league_service.py`
- [x] Leaderboard routes use `leaderboard_service.py`
- [x] Search routes use `search_service.py`
- [x] Caching decorators applied to service functions
- [x] Eager loading eliminates N+1 queries

**Implementation Details:**
- **Phase 1B:** Fixed N+1 queries in coach routes (75% improvement)
  - Added `selectinload(Coach.team)` with `load_only()`
  - Reduced from hundreds of queries to 2 queries
- **Phase 2:** Audited all routes, found already optimized
  - Proper use of `selectinload()`, `joinedload()`, `load_only()`, `raiseload()`
  - Service layer consistently uses optimized query patterns
  - Raw SQL where appropriate (e.g., standings queries)
- **Phase 3:** Added caching to service functions
  - 5 player service functions with `@cache.memoize()`
  - Front page with `@cache.cached()`

**Performance Impact:**
- Coach pages: 8,295ms → 2,102ms (75% faster)
- Player detail: Stable at ~4s with 15 optimized queries
- Front page: 3,149ms → 5ms cached (99.8% improvement)

**Technical Notes:**
- Service layer complete and optimized
- No remaining N+1 patterns identified
- Query optimization is production-ready

**Dependencies:** Complete

**See:** `docs/phase1b_results.md`, `docs/phase2_results.md` for details

---

### US-I005: Materialized Views for Leaderboards [NOT STARTED]
**Priority:** MEDIUM
**Effort:** 6-8 hours
**Status:** DEFERRED (until leaderboards cause performance issues)
**Spec Reference:** Lines 663-666

**Description:**
Create materialized views for expensive leaderboard aggregations.

**Acceptance Criteria:**
- [ ] MV: career_batting_leaders_mv
- [ ] MV: single_season_records_mv
- [ ] MV: active_player_stats_mv
- [ ] Refresh strategy defined (nightly? on-demand?)
- [ ] Service layer uses MVs when available

**Technical Notes:**
- PostgreSQL CREATE MATERIALIZED VIEW
- Refresh with ETL or cron job
- Massive performance gain for leaderboards

**Dependencies:** Leaderboard queries must exist first

---

### US-I006: Logging & Monitoring [NOT STARTED]
**Priority:** MEDIUM
**Effort:** 4-6 hours
**Status:** NOT STARTED
**Spec Reference:** Production requirements

**Description:**
Add application logging and basic monitoring.

**Acceptance Criteria:**
- [ ] Python logging configured (file + console)
- [ ] Log levels: DEBUG for dev, INFO for prod
- [ ] Log slow queries (>1s)
- [ ] Error tracking (Sentry or similar)
- [ ] Basic metrics endpoint (/metrics)

**Technical Notes:**
- Use Python logging module
- Structured logging (JSON format)
- Log rotation for production

**Dependencies:** None

---

## Epic 8: Testing & Quality

### US-Q001: Pytest Setup & Configuration [NOT STARTED]
**Priority:** HIGH
**Effort:** 4-6 hours
**Status:** NOT STARTED
**Spec Reference:** QA requirements, test-as-you-go

**Description:**
Set up pytest framework with fixtures and test database.

**Acceptance Criteria:**
- [ ] pytest.ini configured
- [ ] Fixtures for test database
- [ ] Fixtures for test client (Flask test client)
- [ ] Fixtures for sample data (players, teams, stats)
- [ ] Test coverage reporting (pytest-cov)
- [ ] CI/CD integration ready

**Technical Notes:**
- Use test database (ootp_test)
- Factory pattern for test data
- Arrange-Act-Assert pattern

**Dependencies:** None

---

### US-Q002: Unit Tests - Models [NOT STARTED]
**Priority:** HIGH
**Effort:** 6-8 hours
**Status:** NOT STARTED

**Description:**
Write unit tests for all model hybrid properties and methods.

**Acceptance Criteria:**
- [ ] Test Player model properties (age, full_name, etc.)
- [ ] Test Team model properties
- [ ] Test Stats model calculations (total_bases, innings_pitched_display, etc.)
- [ ] Test edge cases (missing data, nulls)
- [ ] 90%+ coverage on models

**Dependencies:** US-Q001

---

### US-Q003: Integration Tests - Routes [NOT STARTED]
**Priority:** HIGH
**Effort:** 8-10 hours
**Status:** NOT STARTED

**Description:**
Write integration tests for all routes.

**Acceptance Criteria:**
- [ ] Test all player routes (list, detail, by_letter)
- [ ] Test all team routes
- [ ] Test main routes (index, health)
- [ ] Test 404 handling
- [ ] Test with real-ish data
- [ ] No mocks unless absolutely necessary

**Dependencies:** US-Q001

---

### US-Q004: Performance Tests [NOT STARTED]
**Priority:** MEDIUM
**Effort:** 4-6 hours
**Status:** NOT STARTED

**Description:**
Test query performance and page load times.

**Acceptance Criteria:**
- [ ] Benchmark critical queries
- [ ] Test with full dataset (18 seasons)
- [ ] Page load times < 1s for detail pages
- [ ] Leaderboard queries < 2s
- [ ] Identify slow queries for optimization

**Dependencies:** US-I002 (indexes)

---

## Epic 9: Newspaper/Journal (Phase 2)

### US-NEWS-001: Content Strategy & Data Model [NOT STARTED]
**Priority:** LOW
**Effort:** 6-8 hours
**Status:** DEFERRED
**Spec Reference:** Lines 400-442

**Description:**
Define newspaper content strategy and data model.

**Acceptance Criteria:**
- [ ] Decide on user-written vs. auto-generated content mix
- [ ] Define article schema (title, author, date, body, category, tags)
- [ ] Create database tables/models
- [ ] Define article generation triggers (game events, milestones)

**Technical Notes:**
- Article generation is complex (NLP/templates)
- User-written needs editor interface
- Timeline view vs. traditional blog layout

**Dependencies:** None (standalone epic for Phase 2)

---

## Database & ETL Enhancements (Supporting Work)

### DB-001: Create Missing Models [NOT STARTED]
**Priority:** MEDIUM
**Effort:** 4-6 hours
**Status:** NOT STARTED

**Description:**
Create SQLAlchemy models for tables that exist but aren't modeled yet.

**Tables to Model:**
- [ ] trade_history
- [ ] team_history (currently only team_history_record?)
- [ ] league_history
- [ ] games
- [ ] person_images
- [ ] team_logos
- [ ] league_logos

**Dependencies:** None

---

### DB-002: Populate Image Reference Tables [NOT STARTED]
**Priority:** MEDIUM
**Effort:** 2-3 hours
**Status:** NOT STARTED

**Description:**
Populate person_images, team_logos, league_logos tables with file paths.

**Acceptance Criteria:**
- [ ] Scan etl/data/images/players/ directory
- [ ] Insert records into person_images for each file
- [ ] Define team logo strategy and populate team_logos
- [ ] Define league logo strategy and populate league_logos

**Technical Notes:**
- ETL script or one-time migration
- File naming convention already established

**Dependencies:** None

---

## Performance Optimization Work (Session 12: 2025-10-11)

### Overview
Major performance optimization sprint focused on eliminating cascading eager loads from SQLAlchemy queries.

### Work Completed

#### Player Detail Page Optimization
**Problem:** 124 queries taking 4.4 seconds per page load due to cascading `lazy='joined'` relationships.

**Solution:** Implemented comprehensive query optimization:
- Route layer (`/web/app/routes/players.py`): Used `load_only()` with `selectinload()` for minimal field loading
- Service layer (`/web/app/services/player_service.py`): Added `lazyload()` + `raiseload('*')` to batting/pitching stats queries
- Trade history: Blocked team relationship cascades

**Results:**
- **Before:** 124 queries, 4,402ms
- **After:** 12 queries, 171ms
- **Improvement:** 90% fewer queries, 96% faster (25.8x speedup)

**Files Modified:**
- `/web/app/routes/players.py` (lines 108-168)
- `/web/app/services/player_service.py` (lines 68-80, 210-222, 448-486)

#### Home Page Optimization
**Problem:** 81 queries with slowest taking 1.6 seconds, caused by Team model cascading loads.

**Solution:** Applied `load_only()` + relationship controls to Team queries in home page route.

**Results:**
- **Before:** 81 queries, slowest 1,644ms, average 133ms
- **After:** 17 queries, slowest 17ms, average 5ms
- **Improvement:** 79% fewer queries, 99% faster on slowest query, 96% faster on average

**Files Modified:**
- `/web/app/routes/main.py` (lines 84-106)

### Technical Pattern Established
**Mandatory SQLAlchemy Optimization Pattern** (added to continuity.txt):

```python
# For routes fetching single records with relationships
Player.query.options(
    load_only(Player.field1, Player.field2, ...),  # Only load needed columns
    selectinload(Player.relationship).load_only(...).raiseload('*'),  # Controlled load
    lazyload(Player.unwanted_rel),  # Override lazy='joined'
    raiseload('*')  # Block all others
)

# For service layer fetching collections
Stats.query.options(
    lazyload(Stats.player),
    lazyload(Stats.team),
    lazyload(Stats.league),
    raiseload('*')  # Block cascades
)
```

### Impact
These optimizations bring player and home pages to production-ready performance standards:
- Player pages: Now < 200ms (target: < 1s)
- Home page: Now < 100ms (target: < 500ms)

**Hours Invested:** ~2 hours

---

## Summary Statistics

### Overall Progress
- **Total User Stories:** 77 (added 6 coach stories, 1 team coaching story, 1 roster cleanup story, 3 UX enhancement stories, 1 league level separation story)
- **Completed:** 40 (Player list, Team list, Standings, Player detail, US-P001, US-P002, US-P004, US-P006, US-P007, US-P007B, US-I002, US-P010 through US-P015, US-T001, US-T002, US-T002B, US-T003, US-T005, US-L001 through US-L007, US-L009, US-F001 through US-F004, US-F006, US-N001 through US-N004)
- **In Progress:** 0
- **Deferred:** 7 (US-P003, US-P005, US-P009, US-I005, US-L008, US-NEWS-001, others)
- **Not Started:** 30 (including US-P016, US-P017, US-P018, US-F005, Epic 5, Epic 7 remaining, Epic 8)
- **Completion:** ~52% (40/77 complete)

### By Priority
- **CRITICAL:** 0 items remaining (batting and pitching tables DONE!)
- **HIGH:** 22 items (17 done, 0 in progress, 5 not started)
  - Done: US-P001, US-P002, US-P010, US-P011, US-P012, US-P013, US-T002, US-T002B, US-T003, US-I002, US-I003, US-I004, US-L001, US-L003, US-L004, US-F001, US-F002
- **MEDIUM:** 29 items (12 done, 1 deferred)
  - Done: US-P004, US-P014, US-P015, US-T001, US-T005, US-L002, US-L005, US-L006, US-F003, US-F004, US-F006, plus partial US-N002/US-N003
  - New: US-P018
- **LOW:** 13 items (2 done - US-P006, US-P007; 3 new - US-P016, US-P017, US-N004)
- **DEFERRED:** 7 items

### By Epic (Effort in Hours)
1. **Player Pages (including Coaches):** 98-130 hours (**100% done** - All stories complete, optional enhancements deferred)
2. **Team Pages:** 29-41 hours (**100% done** - US-T001, US-T002, US-T002B, US-T003, US-T005 complete; US-T004 deferred)
3. **Leaderboards:** 65-85 hours (**100% done** - US-L001 through US-L007, US-L009 complete; US-L008 deferred; US-L010 not started but not needed)
4. **Front Page:** 25-35 hours (**100% done** - US-F001, US-F002, US-F003, US-F004, US-F006 complete; US-F005 deferred LOW priority)
5. **League/Year Pages:** 15-20 hours (**100% done** - Moved to backlog-completed.md, all functionality complete)
6. **Search/Nav:** 16-22 hours (**100% done** - US-N001 through US-N004 complete!)
7. **Infrastructure:** 30-40 hours (**83% done** - US-I001 through US-I004 complete; US-I005 deferred; US-I006 optional 4-6 hrs)
8. **Testing:** 25-35 hours (**0% done** - Deferred to post-v1.0, optional for launch)
9. **Newspaper:** TBD (**Deferred to Phase 2**)

**Total Estimated Effort:** 297-400 hours
**Hours Completed Session 1:** ~16 hours (US-P001, US-P002, US-P004, US-P006, US-P007, US-P007B, US-I002)
**Hours Completed Session 2:** ~14 hours (Coach pages: US-P010 through US-P015, US-T001, US-T005, partial US-T002)
**Hours Completed Session 4:** ~10 hours (US-T003 + performance optimization)
**Hours Completed Session 5:** ~1 hour (US-T002B)
**Hours Completed Session 6:** ~1 hour (US-T002 completion review)
**Hours Completed Session 7:** ~4 hours (US-L001 leaderboard infrastructure)
**Hours Completed Session 8:** ~2 hours (US-L002 leaderboard home page)
**Hours Completed Session 9:** ~2 hours (US-L003, US-L004, US-L005 - unified leaderboard pages)
**Hours Completed Session 11:** ~1.5 hours (US-L006 - yearly league leaders page)
**Hours Completed Session 12:** ~3 hours (Performance optimization - player and home pages; US-F001 - 2-column layout)
**Hours Completed Session 13:** ~4.5 hours (US-F002 - Notable Rookies widget; US-F003 - Born This Week widget; US-F004 - Featured Players grid with caching optimization; US-P018 - League level separation story created)
**Hours Completed Session 14:** ~8 hours (ETL: incremental loading; US-N002, US-N003, US-N004 - Navigation & UX enhancements)
**Hours Completed Session 15:** ~4 hours (US-L007 - Year-by-Year Top Tens; US-L009 - Mega Dropdown Navigation; Epic 3 complete!)
**Total Hours Completed:** ~71 hours

---

## Current Sprint Focus

### Sprint Goal
Complete core player page functionality with yearly statistics tables.

### Sprint Backlog (Completed 2025-10-09)
1. ✅ Create BACKLOG.MD
2. ✅ US-P001: Player Yearly Batting Statistics Table (DONE - 10 bugs fixed)
3. ✅ US-P002: Player Yearly Pitching Statistics Table (DONE)
4. ✅ US-P004: Player Image Display (DONE)
5. ✅ US-P006: Sortable Statistics Tables (DONE)
6. ✅ US-P007: Player History Timeline (DONE - Trade history)
7. ✅ US-P007B: Player News & Highlights (DONE - Bonus feature!)
8. ⏸️ US-P003: Player Yearly Fielding Statistics Table (DEFERRED - no ETL data)
9. ⏸️ US-P005: Player Bio - School Field (DEFERRED - no reference data)
10. ⏭️ US-I002: Database Indexes (blocks performance)
11. ⏭️ US-Q001: Pytest Setup
12. ⏭️ US-Q003: Integration Tests for Player Routes

### Next Sprint Options
- **Team Pages** (US-T002, US-T003, US-T004)
- **Front Page Enhancements** (US-F001, US-F002, US-F003, US-F004)
- **Infrastructure** (US-I001 Redis, US-I002 Indexes, US-I003 Images)

---

## Notes & Decisions Log

### 2025-10-09 - Session 1: Epic 1 - Player Pages Nearly Complete!
**Completed:**
- ✅ US-P001: Player Yearly Batting Statistics Table (with 10 bug fixes)
- ✅ US-P002: Player Yearly Pitching Statistics Table
- ✅ US-P004: Player Image Display
- ✅ US-P006: Sortable Statistics Tables
- ✅ US-P007: Player History Timeline (Trade history)
- ✅ US-P007B: Player News & Highlights (Bonus feature!)

**Key Accomplishments:**
- **Stats Tables**: Comprehensive batting/pitching tables with career totals, sortable columns
- **Bug Fixes**: Fixed 10 critical bugs (template rendering, age calculation, sort order, stat formatting, image paths, cropping, height conversion)
- **Player Images**: Natural 90x135 size with JavaScript fallback to initials
- **Trade History**: Beautiful timeline UI with 2,097 trades, clickable team/player links
- **Player News**: Parsed 1,831 messages from messages table, grouped by category (Awards, Highlights, Injuries, Contracts, Career)
- **Data Formatting**: Proper stat formatting (.262 not 0.262), stripped literal `\n` characters from messages
- **Performance**: Service layer with SQL aggregation, optimized queries
- **Age Calculation**: Uses game year (1997) not real-world date

**Deferred:**
- US-P003: Fielding stats (no ETL data yet)
- US-P005: School field (no reference data)

**Technical Decisions:**
- Created comprehensive backlog from WEBSITE-SPECS.MD (61+ user stories)
- Analyzed messages table to identify relevant player news types (2,3,4,7,8)
- Enhanced clean_trade_summary filter to handle both trade summaries and message bodies
- Database has 18 seasons of history (1980-1997), currently in June 1997
- Non-traditional league structure: 4 top-level leagues, no traditional AL/NL
- Player images at etl/data/images/players/ (90x135px portrait)
- Team/league logos need strategy defined
- Redis not yet available, add to infrastructure backlog
- Performance is already a concern, prioritize optimization work
- Public-facing site, read-only except search
- Testing will happen as we go (not separate phase)
- Use SQL aggregation for performance (not Python calculations)

---

### 2025-10-10 - Session 2: Coaches & Staff Implementation
**Context:**
Implemented complete coach pages and began team year pages work.

**Completed:**
- ✅ **US-P010:** Coach Model and Data Layer (3 hours actual)
- ✅ **US-P011:** Coach List and Detail Pages (4 hours actual)
- ✅ **US-P012:** Coach Ratings Bar Charts (2 hours actual)
- ✅ **US-P013:** Coach Preferences Display (2 hours actual)
- ✅ **US-P014:** Coach Image Serving (1 hour actual)
- ✅ **US-P015:** Coach-Player Linkage Display (1 hour actual)
- ✅ **US-T005:** Team Coaching Staff Display (1 hour actual)
- ✅ **US-T001:** Team Logo Display (1 hour actual - placeholder system)
- 🔧 **US-T002:** Team Year Pages (8 hours actual - core complete, roster/players pending)

**Implementation Details:**

**Coach Pages (Epic 1):**
1. **Coach Model** - Created with all 80+ fields, relationships, hybrid properties
   - Added occupation_display, occupation_sort_order properties
   - Labels: 7/8 = Base Coach (not generic "Staff")
   - Weight in lbs (not kg like originally thought)
2. **Coach Routes** - List grouped by occupation, detail with all sections
3. **Rating Bars** - Reusable macro, 0-200 scale, color-coded progression
4. **Preference Bars** - Reusable macro, -5 to +5 scale with marker positioning
5. **Images** - Served from `/etl/data/images/players/coach_{id}.png` (same directory as players!)
6. **Former Player Link** - Top-right corner shows player image with link when applicable

**Team Pages (Epic 2):**
1. **Team Logo Display** - Placeholder system (blue box with abbreviation) until logos available
2. **Team Coaching Staff** - Added to current team page with proper ordering:
   - Order: Owner → GM → Manager → Bench Coach → Pitching Coach → Hitting Coach → Base Coach → Scout → Trainer
   - Python sorting via occupation_sort_order property
3. **Team Year Pages** - Created infrastructure:
   - Models: TeamHistoryRecord, TeamHistoryBattingStats, TeamHistoryPitchingStats, TeamBattingStats, TeamPitchingStats
   - Service layer handles both historical (1980-1996) and current year (1997)
   - Route `/teams/<team_id>/<year>` with prev/next navigation
   - Template shows team batting/pitching stats, record, season info
   - TODO: Individual player roster, top 12 by WAR

**Bug Fixes:**
1. **OPS+ removed** - Not in database (no ETL calculation), removed from advanced batting table
2. **Coach weight** - Source data already in lbs, removed kg→lbs conversion
3. **Coach occupation ordering** - Created occupation_sort_order property, sorted in Python
4. **Coach images path** - Same directory as players: `/etl/data/images/players/coach_{id}.png`
5. **Nation abbreviation** - Used `nation.abbreviation` not `nation.abbr`

**Files Created:**
- `/web/app/models/coach.py` (200+ lines)
- `/web/app/models/team_history.py` (400+ lines, 5 models)
- `/web/app/services/team_service.py` (get_team_year_data, get_available_years_for_team)
- `/web/app/routes/coaches.py` (coach list, detail, image routes)
- `/web/app/templates/coaches/` (list, detail, _rating_bar, _preference_bar)
- `/web/app/templates/teams/_coaching_staff.html`
- `/web/app/templates/teams/_team_logo.html`
- `/web/app/templates/teams/year.html`

**Updated Backlog Statistics:**
- Total user stories: 72
- Completed this session: 9 (US-P010 through US-P015, US-T001, US-T005, partial US-T002)
- Total completed: 18 (including prior sessions)
- Overall completion: ~25%
- Time spent this session: ~23 hours actual (vs 32-48 estimated)

---

### 2025-10-10 - Session 4: Team Home Page Performance Optimization (COMPLETE)
**Context:**
Continued from Session 2, focused on completing US-T003 (Team Home - Historical Summary) which was implemented but had severe performance issues.

**Problem:**
- Team home page taking 28+ seconds to load with 1,861 SQL queries
- Page completely unusable in production
- Initial implementation complete but performance unacceptable

**Root Cause Analysis:**
1. SQLAlchemy's `lazy='joined'` on models causing cascading eager loads
2. Roster query alone generated 1,849 queries (Player → City → Nation → Continent → State cascade)
3. Critical discovery: `raiseload('*')` only blocks **accessing** relationships, not **loading** them
4. When models have `lazy='joined'`, SQLAlchemy loads relationships during query construction time

**Solution Implemented:**
1. **Raw SQL for Roster Query** - Switched from ORM to `text()` SQL to completely bypass relationship machinery
2. **Optimized Team Query** - Used `load_only()`, `selectinload()`, and nested `raiseload('*')`
3. **Service Layer Optimization** - Added `raiseload('*')` to all franchise service functions
4. **Helper Function** - Created `get_position_display()` for position code mapping

**Performance Results:**
```
BEFORE: 28,000ms with 1,861 queries
AFTER:    120ms with 12 queries

Improvement: 99.6% reduction (232x faster)
Query reduction: 99.4% fewer queries

Query breakdown:
- Get team: 80.2ms (5 queries)
- Get roster: 12.1ms (1 raw SQL query, 97 players) ← KEY FIX
- Get coaches: 9.5ms (1 query)
- Get franchise history: 5.7ms (2 queries)
- Get franchise top players: 7.6ms (1 CTE query)
- Get franchise year by year: 5.4ms (2 queries)
```

**Completed:**
- ✅ **US-T003:** Team Home - Historical Summary (with extensive performance optimization)
- ✅ Fixed critical performance bottleneck in team pages
- ✅ Documented optimization journey in continuity.txt
- ✅ Created reusable optimization patterns for future pages

**Key Learnings:**
- `lazy='joined'` in models loads relationships at query time, not access time
- Raw SQL with `text()` is sometimes the only viable solution for complex relationship graphs
- Measuring query count is as important as measuring execution time
- Always profile with real data before declaring optimization complete

**Files Modified:**
- `/web/app/routes/teams.py` - Added db import, helper function, raw SQL roster query
- `/web/app/services/team_service.py` - Added raiseload() to service functions
- `/continuity.txt` - Documented Session 4 journey
- `/docs/backlog.md` - Updated US-T003 with performance details

**Time Spent:** ~10 hours actual (investigation, implementation, testing, documentation)

**Follow-up Work Identified:**
- Created **US-T002B** to remove simplified roster from team home page
- Roster query optimization sacrificed detail for performance
- Better UX: Link to current year team-year page for full roster details
- Will further improve performance by removing roster query entirely (11 queries instead of 12)

**Status:**
✅ Session 4 complete - Team home pages now production-ready with sub-second load times
📋 New user story US-T002B added to backlog for roster cleanup

---

### 2025-10-10 - Session 6: US-T002 Team Year Pages - Completion Review
**Context:**
Reviewed and verified completion of US-T002 (Team Year Pages) which was partially implemented in Session 2.

**Completion Verified:**
- ✅ **US-T002:** Team Year Pages (100% complete)

**Key Verification:**
All acceptance criteria met:
- ✅ URL `/teams/<team_id>/<year>` route implemented
- ✅ Team logo and header with year navigation
- ✅ Previous/next year navigation with disabled states
- ✅ Team batting stats table (aggregate)
- ✅ Team pitching stats table (aggregate)
- ✅ Individual player batting stats table with position column
- ✅ Individual player pitching stats table
- ✅ Top 12 players by WAR with images
- ✅ Season record, place in standings

**Templates Implemented:**
1. `/web/app/templates/teams/year.html` - Main team year page (206 lines)
2. `/web/app/templates/teams/_roster_batting_table.html` - Individual player batting stats (72 lines)
3. `/web/app/templates/teams/_roster_pitching_table.html` - Individual player pitching stats (74 lines)
4. `/web/app/templates/teams/_top_players_grid.html` - Top 12 players grid (44 lines)

**Service Layer Complete:**
- `get_team_year_data()` - Team, record, aggregate stats
- `get_team_player_batting_stats()` - Individual player batting with position
- `get_team_player_pitching_stats()` - Individual player pitching
- `get_team_top_players_by_war()` - Top players by WAR
- `get_available_years_for_team()` - Years for navigation

**Features Implemented:**
- Handles both current year (1997) and historical years (1980-1996)
- Aggregate team stats displayed prominently
- Individual player stats with 20 batting columns, 17 pitching columns
- Top 12 players grid with images and WAR values
- Responsive design with horizontal scroll and sticky first column
- Optimized performance: 0.3-0.5 second page load times

**Updated Backlog Statistics:**
- Total user stories: 76
- Completed this session: 1 (US-T002 - verification/documentation)
- Total completed: 21 (28% overall completion)
- Epic 2 (Team Pages): **100% complete**
- Time spent this session: ~1 hour (verification and documentation)

**Session 6 Summary:**
US-T002 was the last remaining user story for Epic 2 (Team Pages). With its completion, Epic 2 is now 100% done, achieving all core team page functionality with excellent performance characteristics.

---

### 2025-10-10 - Session 7: US-L001 Leaderboard Infrastructure
**Context:**
Began Epic 3 (Leaderboards) by implementing the foundational service layer and models for leaderboard queries.

**Completion:**
- ✅ **US-L001:** Leaderboard Infrastructure & Service Layer (100% complete)

**Key Accomplishments:**
1. **Materialized Views Analysis:**
   - Reviewed existing 6 materialized views from ETL (already created in database)
   - Career batting/pitching, single-season batting/pitching, yearly batting/pitching
   - All views include pre-aggregated stats, active status flags, and proper indexes

2. **Architecture Decisions:**
   - League filtering at top-level leagues only (league_level = 1)
   - "All Leagues" universe includes all top-level leagues (not minors)
   - Keep materialized views as-is, filter in application layer
   - Keep existing qualification thresholds (100 PA, 50 IP single-season; 1000 PA, 500 IP career)

3. **Models Created** (`/web/app/models/leaderboard.py` - 305 lines):
   - `LeaderboardCareerBatting` - Career batting totals with active flag
   - `LeaderboardCareerPitching` - Career pitching totals with active flag
   - `LeaderboardSingleSeasonBatting` - Single-season batting records
   - `LeaderboardSingleSeasonPitching` - Single-season pitching records
   - `LeaderboardYearlyBatting` - Yearly leaders with pre-calculated ranks
   - `LeaderboardYearlyPitching` - Yearly leaders with pre-calculated ranks
   - All models use ReadOnlyMixin to prevent accidental writes

4. **Service Layer Created** (`/web/app/services/leaderboard_service.py` - 600+ lines):
   - **Career Leaders Functions:**
     - `get_career_batting_leaders()` - Career batting with league/active filtering
     - `get_career_pitching_leaders()` - Career pitching with league/active filtering
   - **Single-Season Functions:**
     - `get_single_season_batting_leaders()` - Single-season batting with year/league filtering
     - `get_single_season_pitching_leaders()` - Single-season pitching with year/league filtering
   - **Yearly Leaders Functions:**
     - `get_yearly_batting_leaders()` - Pre-ranked yearly leaders by league
     - `get_yearly_pitching_leaders()` - Pre-ranked yearly leaders by league
   - **Helper Functions:**
     - `get_top_level_leagues()` - Fetch top-level leagues (league_level = 1)
     - `get_league_options()` - Format league options for filters
     - `get_available_years()` - Get all years with data
     - `get_stat_metadata()` - Stat display names, categories, formatting
     - `clear_cache()` - Manual cache invalidation

5. **Caching Implementation:**
   - In-memory cache with 15-minute TTL
   - Cache key generation from function name + parameters
   - 537x speedup (6.8ms → 0.01ms)
   - Ready for Redis integration (same interface)

6. **Performance Results** (from comprehensive test suite):
   - Career batting leaders: 15-23ms
   - Career pitching leaders: 9-16ms
   - Single-season leaders: 15-18ms
   - Yearly league leaders: 5-7ms
   - All queries well under 30ms benchmark

7. **Test Suite Created** (`/test_leaderboards.py` - 279 lines):
   - Test league options and filtering
   - Test career batting/pitching leaders with various filters
   - Test single-season leaders (all-time and year-specific)
   - Test yearly league leaders
   - Test caching functionality and performance
   - Test stat metadata retrieval
   - All tests passing

**Files Created:**
- `/web/app/models/leaderboard.py` - 6 read-only models (305 lines)
- `/web/app/services/leaderboard_service.py` - Complete service layer (600+ lines)
- `/test_leaderboards.py` - Comprehensive test suite (279 lines)

**Files Modified:**
- `/web/app/models/__init__.py` - Added leaderboard model exports

**Updated Backlog Statistics:**
- Total user stories: 76
- Completed this session: 1 (US-L001)
- Total completed: 22 (29% overall completion)
- Epic 3 (Leaderboards): 9% complete (1/11 user stories)
- Time spent this session: ~4 hours

**Session 7 Summary:**
US-L001 establishes a robust, high-performance foundation for all leaderboard functionality. The service layer provides comprehensive filtering, caching, and query optimization, with all queries meeting performance benchmarks.

---

### 2025-10-10 - Session 8: US-L002 Leaderboard Home Page
**Context:**
Continued Epic 3 (Leaderboards) by creating the main leaderboard landing page.

**Completion:**
- ✅ **US-L002:** Leaderboard Home Page (100% complete)

**Key Accomplishments:**
1. **Route Created** (`/web/app/routes/leaderboards.py`):
   - Added `/` and `/home` routes for leaderboard home page
   - Fetches current year (1997) leaders for 10 key stats:
     - Batting: HR, AVG, RBI, SB, H
     - Pitching: W, SV, SO, ERA, WHIP
   - Uses `get_single_season_batting_leaders()` and `get_single_season_pitching_leaders()`
   - Passes leagues, current_leaders dict, and stat_metadata to template

2. **Template Created** (`/web/app/templates/leaderboards/home.html` - 182 lines):
   - **Header:** "Overall Baseball Leaders & Baseball Records"
   - **Current Year Leaders Section:**
     - "1997 Leaders" heading with league cards
     - League cards show league name with links to batting/pitching leaderboards
     - 3-column responsive grid showing current top leaders
     - Each stat displays: stat name, player name (linked), team abbr, formatted value
     - Proper formatting for rate stats (AVG, ERA, WHIP)
   - **All-Time Records Section:**
     - "All-Time Career and Single-Season Records" heading
     - Separate tables for batting and pitching
     - 4-column link matrix:
       - Statistic | Single-Season | Career | Active | Yearly
     - All links use query param pattern: `/leaderboards/batting?type=career&stat=hr`
     - Batting stats: HR, AVG, RBI, SB, H, OBP, SLG
     - Pitching stats: W, SV, SO, ERA, WHIP, K/9
   - **Responsive Design:**
     - 3-column grid for current leaders (1-col mobile, 2-col tablet, 3-col desktop)
     - Horizontal scroll for tables on mobile
     - Hover states on all links

3. **Navigation Updated** (`/web/app/templates/base.html`):
   - Changed "Leaderboards" link from `/leaderboards/batting` to `/leaderboards/home`
   - Now points to new home page as main entry point

4. **Testing:**
   - Page renders correctly at http://localhost:5000/leaderboards/
   - All 10 current year leaders display properly
   - League cards show correct league names
   - All links formatted correctly (will 404 until future stories implemented)
   - Responsive layout works across all viewport sizes

**Files Created:**
- `/web/app/templates/leaderboards/home.html` - Main landing page (182 lines)

**Files Modified:**
- `/web/app/routes/leaderboards.py` - Added home route
- `/web/app/templates/base.html` - Updated navigation link

**Updated Backlog Statistics:**
- Total user stories: 76
- Completed this session: 1 (US-L002)
- Total completed: 23 (30% overall completion)
- Epic 3 (Leaderboards): 18% complete (2/11 user stories)
- Time spent this session: ~2 hours

**Session 8 Summary:**
US-L002 creates a clean, well-organized landing page for all leaderboard functionality. The page provides quick access to current year leaders and a comprehensive link matrix to all leaderboard types, setting up the navigation structure for the remaining Epic 3 user stories.

---

### 2025-10-10 - Session 9: US-L002 Data Quality Fix (team_id=0)
**Context:**
Discovered critical data quality issue where college/HS players (team_id=0) were appearing in leaderboards.

**Problem Identified:**
- 11,685 stat records with team_id=0 and league_id=0 (college/HS players)
- 11,681 of these made it into leaderboard_single_season_batting view (26% of all records!)
- These players have stats but shouldn't count toward professional leaderboards
- Would appear in "All Leagues" queries where league_id filter is None

**Solution Implemented:**
1. **Service Layer Fix** (`/web/app/services/leaderboard_service.py`):
   - Added `team_id != 0` filter to `get_single_season_batting_leaders()`
   - Added `team_id != 0` filter to `get_single_season_pitching_leaders()`
   - Filters applied before all other query logic

2. **Database Layer Fix** (`/etl/sql/tables/09_leaderboard_views.sql`):
   - Added `AND s.team_id != 0` to leaderboard_single_season_batting view
   - Added `AND s.team_id != 0` to leaderboard_single_season_pitching view
   - Added `AND s.team_id != 0` to leaderboard_yearly_batting view
   - Added `AND s.team_id != 0` to leaderboard_yearly_pitching view
   - This ensures future ETL runs automatically exclude college/HS players

3. **Migration Script Created** (`/scripts/refresh_leaderboard_views.sql`):
   - Refreshes all 6 materialized views with new filters
   - Includes verification query to confirm team_id=0 records removed

4. **Documentation Updated** (`/continuity.txt`):
   - Added "Critical Data Quality Rules" section
   - Documented that team_id=0 must ALWAYS be filtered from leaderboards
   - Notes dual-layer protection (database + application)

**Files Modified:**
- `/web/app/services/leaderboard_service.py` - Added team_id filters to single-season functions
- `/etl/sql/tables/09_leaderboard_views.sql` - Added team_id filters to 4 view definitions
- `/continuity.txt` - Documented data quality rule

**Files Created:**
- `/scripts/refresh_leaderboard_views.sql` - Migration script to refresh views

**Impact:**
- Fixes current data: Service layer filters prevent bad data from reaching UI immediately
- Fixes future data: View definitions ensure ETL won't populate bad data
- Expected reduction: ~11,681 records removed from single-season batting view
- Performance benefit: Smaller views = faster queries

**Next Steps:**
- Run `/scripts/refresh_leaderboard_views.sql` to apply view changes to database
- Clear leaderboard cache: `leaderboard_service.clear_cache()`
- Verify home page no longer shows college/HS players in current year leaders

**Status:**
✅ Code fixed and deployed
✅ Database views recreated with filters
✅ Verified: All team_id=0 records removed from views
✅ Tested: Leaderboard home page showing correct data

**Results:**
- Single-season batting: 44,178 → 32,497 records (11,681 removed, 26% reduction)
- Single-season pitching: Similar reduction
- Both views now have 0 team_id=0 records
- Home page confirmed showing only professional team players

**Session 9 Complete:** Data quality issue resolved

---

### 2025-10-11 - Session 10: US-L003, US-L004, US-L005 Complete + Bug Fixes
**Context:**
Implemented unified leaderboard pages for Career, Active, Single-Season, and Yearly types, completing 3 user stories simultaneously. Fixed multiple bugs discovered during testing.

**Completed:**
- ✅ **US-L003:** Career Leaderboards
- ✅ **US-L004:** Single-Season Leaderboards  
- ✅ **US-L005:** Active Player Leaderboards

**Key Implementation:**
1. **Unified Leaderboard System:**
   - Single template (`leaderboard.html`) handles all 4 leaderboard types
   - Routes: `/leaderboards/batting` and `/leaderboards/pitching`
   - Query params: `?type=career&stat=hr&league=X&year=Y`
   - Dynamic table columns based on type (Career shows Seasons, Single-Season shows Year/Team, Yearly shows League)

2. **Features Delivered:**
   - Filter dropdowns: Type, Stat, League, Year (shown dynamically)
   - Active player indicators: Asterisk (*) next to active players on career/single-season types
   - Legend: "* Denotes active player" at bottom of table
   - Top 100 leaders with proper stat formatting
   - Breadcrumb navigation
   - Responsive design with sticky columns

3. **Bug Fixes:**
   - **Form Dropdown Bug:** Removed hidden `type` input that was overriding dropdown selections, preventing filter changes from working
   - **Yearly Return Type Bug:** Fixed `get_yearly_batting_leaders()` and `get_yearly_pitching_leaders()` to return dict format `{'leaders': [...], 'total': count}` instead of raw list
   - **Yearly Template Bug:** Fixed template to show `league_abbr` for yearly type instead of non-existent `team_id`/`team_abbr` fields
   - **Active Player Indicators:** Added after user request for visual distinction of active vs retired players

**Testing Verified:**
- ✓ Career HR leaders: Elton Scott* (530 HR, 17 seasons)
- ✓ Single-season HR leaders: Chris Johnson* (65 HR, 1996, MON)
- ✓ Yearly RBI leaders: Carlos Gonzalez (118 RBI, 1990, PL League)
- ✓ Yearly pitching leaders: Ubbe de Witte (1985, PL League)
- ✓ Active player filter working
- ✓ All dropdown filters working correctly (after bug fix)
- ✓ Year filter 1984 vs 1994 showing different results (Sal Roman vs Rupert Pouw)

**Files Created:**
- `/web/app/templates/leaderboards/leaderboard.html` - Unified leaderboard template (260 lines)

**Files Modified:**
- `/web/app/routes/leaderboards.py` - Enhanced batting/pitching routes (220 lines)
- `/web/app/services/leaderboard_service.py` - Fixed yearly functions return type

**Performance:**
- All queries <200ms using cached materialized views
- Meeting all performance benchmarks

**Architecture Decisions:**
- Unified template approach eliminated code duplication
- Query param-based filtering provides RESTful, bookmarkable URLs
- JavaScript used minimally (only for year filter visibility toggle)
- All business logic remains in service layer

**Updated Backlog Statistics:**
- Total user stories: 76
- Completed this session: 3 (US-L003, US-L004, US-L005)
- Total completed: 26 (34% overall completion)
- Epic 3 (Leaderboards): 55% complete (5/11 user stories)
- Time spent this session: ~3 hours (including bug fixes)

**Session 10 Summary:**
Three user stories completed with a single elegant solution. The unified template approach proved highly effective, allowing all leaderboard types to share common infrastructure while maintaining distinct displays. Post-implementation bugs were quickly identified and resolved through user testing.

