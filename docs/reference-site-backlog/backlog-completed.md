# RB2 Website Development Backlog - Completed Epics

**Last Updated:** 2025-10-13 (Session 16)
**Completed Epics:** 1 (Player Pages), 2 (Team Pages), 3 (Leaderboards), 5 (League/Year Pages), 6 (Search & Navigation)
**Database State:** 18 seasons of history (1980-1997), Currently in June 1997 season

**Note:** This file contains completed epics for reference. For active work, see `backlog-active.md`

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

## Epic 1: Player Pages

### US-P001: Player Yearly Batting Statistics Table [DONE]
**Priority:** CRITICAL
**Effort:** 4-6 hours (actual: ~6 hours)
**Status:** DONE
**Spec Reference:** Lines 220-228, 306-328
**Completed:** 2025-10-09

**Description:**
Display comprehensive yearly batting statistics for position players in tabular format with career totals.

**Acceptance Criteria:**
- [x] Standard batting table displays all specified columns: Year, Age, Team, League, G, PA, AB, R, H, 2B, 3B, HR, RBI, SB, CS, BB, SO, BA, OBP, SLG, OPS, OPS+, TB, GDP, HBP, SH, SF, IBB
- [x] Advanced batting table displays: Year, Age, Team, League, ISO, BABIP, wOBA, wRC, wRC+, wRAA, WPA, UBR, WAR
- [x] Career totals row at bottom (sum of counting stats, calculate rate stats from totals)
- [x] Year column links to Team-Year page (404 for now)
- [x] Team column links to Team detail page
- [x] League column links to League page (404 for now)
- [x] Age calculated correctly for each season
- [x] Numbers formatted correctly (.XXX for AVG, integers for counts)
- [x] Missing values show as '-'
- [x] Table responsive with horizontal scroll on mobile
- [x] First column (Year) is sticky during horizontal scroll
- [x] Retired status displays in player bio when retired=1
- [ ] One row per season (handle mid-season trades by showing combined stats) - DEFERRED

**Bugs Fixed (2025-10-09):**
1. **FIXED: Tables not rendering** - Variables were set AFTER {% include %} instead of before. Moved {% set %} statements before the include in detail.html lines 145-146, 154-155.
2. **FIXED: Missing statistics** - Same root cause as Bug #1. All stats now display correctly.
3. **FIXED: Retired status** - Added conditional check for `player.current_status.retired` in detail.html lines 14-16 with red "Retired" label.
4. **FIXED: SQLAlchemy Row.t conflict** - Used bracket notation `totals_query[6]` instead of `.t` property in player_service.py line 118.
5. **FIXED: Age calculation** - Changed from real-world date (2025) to game year (1997). Updated Player.age property in player.py lines 155-179.
6. **FIXED: Stats sort order** - Changed from descending to ascending (oldest to newest) in player_service.py lines 70, 185.
7. **FIXED: Batting average formatting** - Applied format_stat('avg') filter to show .262 instead of 0.262 in _batting_stats_table.html.
8. **FIXED: Player images not rendering** - Corrected relative path from 4 levels up to 3 levels in players.py line 128.
9. **FIXED: Image cropping** - Changed from 128x128 square to natural 90x135 portrait dimensions in detail.html lines 15, 18.
10. **FIXED: Height display** - Added height_display property to convert cm to feet/inches in player.py lines 193-208.

**Enhancement Added (2025-10-09):**
11. **ADDED: Advanced Batting Statistics Table** - Added separate table below standard stats showing ISO, BABIP, wOBA, wRC, wRC+, wRAA, WPA, UBR, WAR. Moved WAR from standard table to advanced table. All yearly advanced stats pulled directly from database (already calculated in ETL). Career rate stats (ISO, BABIP, wOBA) calculated from totals. Career counting stats (wRC, wRAA, WPA, UBR, WAR) summed via SQL. Values centered in columns.

**Technical Notes:**
- Use SQL aggregation for career totals (performance requirement) ✓ DONE
- Create reusable service layer function: `get_player_career_batting_stats(player_id)` ✓ DONE
- Create Jinja macro/include for reusability: `_batting_stats_table.html` ✓ DONE
- Pitching stats service and template already created during initial implementation

**Files Modified:**
- `/web/app/services/player_service.py` - Created with batting/pitching stats functions, fixed sort order
- `/web/app/templates/players/_batting_stats_table.html` - Created reusable component with proper formatting
- `/web/app/templates/players/_pitching_stats_table.html` - Created reusable component
- `/web/app/templates/players/detail.html` - Fixed variable passing, added retired indicator, player image, corrected dimensions
- `/web/app/routes/players.py` - Updated to use service layer, added image serving route
- `/web/app/models/player.py` - Fixed age calculation, added height_display property
- `/web/app/utils/formatters.py` - Enhanced format_stat filter documentation

**Dependencies:** None

**Test Coverage:**
- [x] Test with player who has batting stats (player ID 2: 3 seasons, 35G, 16H, BA=0.262)
- [ ] Test with position player (10+ seasons) - NEEDS QA
- [ ] Test with player traded mid-season - NEEDS QA
- [ ] Test with rookie (1 season) - NEEDS QA
- [ ] Test with missing advanced stats (OPS+, WAR) - NEEDS QA
- [ ] Test with retired player - NEEDS QA

**QA Notes:**
Ready for QA testing. Service layer confirmed working. Need to start Flask dev server and verify:
1. Tables render for players with stats
2. All stat columns display correctly
3. Career totals calculate properly
4. Retired status shows for retired players
5. No errors for players without stats

---

### US-P002: Player Yearly Pitching Statistics Table [DONE]
**Priority:** CRITICAL
**Effort:** 4-6 hours (actual: ~0.5 hours - implemented alongside US-P001)
**Status:** DONE
**Spec Reference:** Lines 229-233, 306-328
**Completed:** 2025-10-09

**Description:**
Display comprehensive yearly pitching statistics for pitchers in tabular format with career totals.

**Acceptance Criteria:**
- [x] Table displays all specified columns: Year, Age, Team, League, W, L, ERA, G, GS, GF, CG, SHO, SV, IP, H, R, ER, HR, BB, IBB, SO, HBP, BK, WP, BF, ERA+, FIP, WHIP, H9, HR9, BB9, SO9, SO/W, WAR
- [x] Career totals row at bottom
- [x] IP formatted correctly (200.1 for 200 and 1/3 innings)
- [x] Year/Team/League columns linked appropriately
- [x] Same responsive behavior as batting table
- [x] Shows for pitchers AND position players with pitching appearances
- [x] Stats sorted chronologically (ascending by year)
- [x] Age calculated using game year

**Implementation Notes:**
- Service function `get_player_career_pitching_stats()` created in player_service.py (lines 159-276)
- Template `_pitching_stats_table.html` created with 33+ columns
- IP formatting handled with separate `ip` and `ipf` fields (XXX.Y format)
- All fixes from US-P001 automatically applied (age, sort order, formatting, images)

**Files Created/Modified:**
- `/web/app/services/player_service.py` - Contains pitching stats service function
- `/web/app/templates/players/_pitching_stats_table.html` - Reusable pitching table component
- `/web/app/templates/players/detail.html` - Includes pitching stats table
- `/web/app/routes/players.py` - Passes pitching_data to template

**Dependencies:** US-P001 (pattern followed)

**Test Coverage:**
- [x] Tested with pitcher (player ID 37284) - confirmed working

---

### US-P003: Player Yearly Fielding Statistics Table [DEFERRED]
**Priority:** HIGH
**Effort:** 3-4 hours
**Status:** DEFERRED
**Spec Reference:** Lines 235-238, 306-328

**Description:**
Display yearly fielding statistics by position with career totals.

**Acceptance Criteria:**
- [ ] Table displays: Year, Age, Team, League, Pos, G, GS, Inn, PO, A, E, DP, Fld%, RF/9, RF/G
- [ ] Career totals by position (separate totals for each position played)
- [ ] Year/Team/League columns linked
- [ ] Only show if player has fielding stats

**Technical Notes:**
- Create service function: `get_player_career_fielding_stats(player_id)`
- Create Jinja include: `_fielding_stats_table.html`
- Group by position for career totals
- BLOCKED: players_career_fielding_stats table exists but has no data

**Dependencies:** Fielding stats ETL implementation (not done yet)

**Future Enhancement:**
- Implement fielding stats ETL to populate players_career_fielding_stats table
- Then implement service layer and template components

---

### US-P004: Player Image Display [DONE]
**Priority:** HIGH
**Effort:** 2-3 hours (actual: ~1 hour - implemented alongside US-P001)
**Status:** DONE
**Spec Reference:** Lines 43, 216, 259
**Completed:** 2025-10-09

**Description:**
Display player images on player detail pages, with fallback for missing images.

**Acceptance Criteria:**
- [x] Image displayed top-left of bio section
- [x] Load from `etl/data/images/players/player_$player_id.png`
- [x] Fallback placeholder if image missing (shows player initials)
- [x] Images served efficiently via Flask route
- [x] Proper aspect ratio maintained (90x135px, no cropping)

**Implementation Notes:**
- Created `/players/image/<player_id>` route in players.py to serve images
- Images displayed at natural size (90×135 portrait) without cropping
- JavaScript fallback shows player initials if image load fails
- All player images follow naming convention: `player_{player_id}.png`

**Files Modified:**
- `/web/app/routes/players.py` - Added player_image() route (lines 118-137)
- `/web/app/templates/players/detail.html` - Added image display with fallback (lines 10-21)

**Dependencies:** None

---

### US-P005: Player Bio - School Field [DEFERRED]
**Priority:** MEDIUM
**Effort:** 1 hour
**Status:** DEFERRED
**Spec Reference:** Lines 217-218, 262

**Description:**
Add school/college information to player bio section.

**Acceptance Criteria:**
- [ ] Display school field from players_core table
- [ ] Show only if present (many players won't have this)
- [ ] Formatting matches other bio data

**Technical Notes:**
- School field contains numeric IDs (e.g., "19962", "877")
- Requires schools reference table/CSV that doesn't exist yet
- BLOCKED: Need schools.csv with ID→Name mapping

**Dependencies:** Schools reference data (not available)

**Future Enhancement:**
- Create schools table/model when reference data becomes available
- Add relationship to Player model
- Display school name instead of ID

---

### US-P006: Sortable Statistics Tables [DONE]
**Priority:** MEDIUM
**Effort:** 3-4 hours (actual: ~1 hour)
**Status:** DONE
**Spec Reference:** Lines 226, 232, 237, 289
**Completed:** 2025-10-09

**Description:**
Add client-side sorting to player statistics tables.

**Acceptance Criteria:**
- [x] Click column headers to sort
- [x] Sort indicator (arrow up/down) shows current sort
- [x] Number columns sort numerically, not alphabetically
- [x] Year column default sort (ascending - oldest to newest)
- [x] Sorting works on all stat tables (standard batting, advanced batting, pitching)

**Technical Implementation:**
- Created reusable vanilla JavaScript `TableSorter` class
- No external dependencies (keeps page lightweight)
- Client-side sorting (no page reload)
- Career totals row stays pinned at bottom
- Handles numeric values including decimals (.262 format)
- Handles missing values ('-') by sorting to end
- Preserves sticky column functionality
- Column headers get hover effect and cursor pointer
- Sort direction toggles on repeated clicks
- Default sort: Year ascending (matches data order)

**Files Created:**
- `/web/app/static/js/table-sort.js` - Reusable TableSorter class with numeric/alphabetic detection

**Files Modified:**
- `/web/app/templates/players/_batting_stats_table.html` - Added IDs to both tables (batting-stats-table, advanced-batting-stats-table)
- `/web/app/templates/players/_pitching_stats_table.html` - Added ID (pitching-stats-table)
- `/web/app/templates/players/detail.html` - Added script tag and initialization code in extra_js block

**Dependencies:** US-P001, US-P002

---

### US-P007: Player History Timeline [DONE]
**Priority:** LOW
**Effort:** 4-6 hours (actual: ~2 hours)
**Status:** DONE
**Spec Reference:** Lines 240-241
**Completed:** 2025-10-09

**Description:**
Display player's transaction history (trade history) below statistics in chronological timeline format.

**Acceptance Criteria:**
- [x] Show trade history from trade_history table
- [x] Chronological timeline format (oldest to newest)
- [x] Only show if player has trades
- [x] Clickable links to teams and players in trade summaries
- [ ] Show awards/achievements - DEFERRED (complex award_id mapping)
- [ ] Show injury history - DEFERRED (not requested)
- [ ] Show salary/contract history - DEFERRED (complex multi-table joins)

**Technical Implementation:**
- Created TradeHistory model mapping to trade_history table (50 columns)
- Service layer function `get_player_trade_history()` queries all 20 player slots
- Beautiful timeline UI with vertical line, dots, and date badges
- Custom Jinja filter `clean_trade_summary` converts OOTP tags to HTML links
- Regex parsing: `<Team Name:team#ID>` → clickable team link
- Regex parsing: `<Player Name:player#ID>` → clickable player link
- Gracefully handles players with no trade history (component doesn't render)

**Files Created:**
- `/web/app/models/history.py` - TradeHistory model (180 lines)
- `/web/app/templates/players/_trade_history.html` - Timeline component (80 lines)

**Files Modified:**
- `/web/app/models/__init__.py` - Export TradeHistory
- `/web/app/services/player_service.py` - Added get_player_trade_history() function
- `/web/app/routes/players.py` - Added trade_history to player_detail route
- `/web/app/templates/players/detail.html` - Integrated timeline below stats
- `/web/app/utils/formatters.py` - Added clean_trade_summary filter with regex parsing

**Testing:**
- Player 16747: 4 trades (most-traded player)
- Player 2: No trades (timeline doesn't display - correct behavior)
- Total trades in database: 2,097

**Dependencies:** None

---

### US-P007B: Player News & Highlights [DONE]
**Priority:** MEDIUM (Enhancement beyond spec)
**Effort:** 3-4 hours (actual: ~3 hours)
**Status:** DONE
**Spec Reference:** Not in original spec - enhancement based on messages table analysis
**Completed:** 2025-10-09

**Description:**
Display player-related news stories parsed from the messages table, grouped by category. Shows contracts, injuries, awards, performance highlights, and career milestones.

**Acceptance Criteria:**
- [x] Query messages table for player-specific news (types 2, 3, 4, 7, 8)
- [x] Exclude redundant/irrelevant message types (trades, rumors, general announcements)
- [x] Group messages by category (Awards, Highlights, Injuries, Contracts, Career)
- [x] Display with category headers showing count
- [x] Parse OOTP tags for clickable player/team links
- [x] Strip literal `\n` characters from message bodies
- [x] Color-coded left borders by category
- [x] Show date badges and headlines
- [x] Only display if player has news stories

**Message Types Included:**
- Type 2: Contract signings (592 messages)
- Type 3: Retirements & suspensions (15 messages)
- Type 4: Performance highlights - shutouts, cycles, multi-hit games (175 messages)
- Type 7: Awards - Player of the Week, etc. (381 messages)
- Type 8: Injuries (668 messages)
- **Total: 1,831 relevant player news stories**

**Message Types Excluded:**
- Type 0: General announcements (not player-specific)
- Type 1: Trades (already shown via trade_history table)
- Type 6: General
- Type 11: Trade rumors (speculation, not news)

**Technical Implementation:**
- Created Message model mapping to messages table (32 columns, 10 player_id slots)
- Service layer function `get_player_news()` with filtered query on message_type
- Template component with Jinja grouping logic (dictionary by category)
- Enhanced `clean_trade_summary` filter to handle literal `\n` strings
- Category-specific styling: 🏆 Awards (blue), ⭐ Highlights (yellow), 🏥 Injuries (red), ✍️ Contracts (green), 👋 Career (purple)

**Files Created:**
- `/web/app/models/message.py` - Message model with category/icon/color properties
- `/web/app/templates/players/_player_news.html` - Grouped news display component

**Files Modified:**
- `/web/app/models/__init__.py` - Export Message model
- `/web/app/services/player_service.py` - Added get_player_news() function
- `/web/app/routes/players.py` - Added player_news to player_detail route
- `/web/app/templates/players/detail.html` - Integrated news section below trade history
- `/web/app/utils/formatters.py` - Enhanced clean_trade_summary to strip `\n` literals and newlines

**Testing:**
- Player 53425 (Bráulio Brandling): 12 stories (Contract, Highlight, Injury)
- Player 14285 (Graham Leonard): 8 stories (Award, Contract)
- Player 17381 (Terry McNeely): 5 stories (Award, Contract, Highlight)

**Dependencies:** None

---

### US-P008: Leaderboard Appearances [NOT STARTED]
**Priority:** LOW
**Effort:** 6-8 hours
**Status:** NOT STARTED
**Spec Reference:** Lines 241, 289

**Description:**
Show which leaderboards this player appears on (Top 10 HR, Top 10 Wins, etc.)

**Acceptance Criteria:**
- [ ] List all leaderboards where player ranks in top 10
- [ ] Show rank, stat value, and leaderboard type
- [ ] Link to full leaderboard
- [ ] Grouped by stat category

**Technical Notes:**
- Complex queries across multiple leaderboard types
- May need materialized views for performance
- Depends on leaderboard infrastructure

**Dependencies:** Epic 3 (Leaderboards)

---

### US-P009: Similarity Scores [NOT STARTED]
**Priority:** LOW
**Effort:** 12-16 hours
**Status:** DEFERRED
**Spec Reference:** Lines 243-246, 279

**Description:**
Calculate and display similar players using Bill James similarity score algorithm.

**Acceptance Criteria:**
- [ ] Implement Bill James similarity score formula
- [ ] Show top 10 similar players (career)
- [ ] Show top 10 similar by age
- [ ] Side-by-side comparison cards

**Technical Notes:**
- Complex algorithm, needs research
- Computationally expensive - run as background job
- Store results in cache or separate table

**Dependencies:** Background job infrastructure (Celery/RQ)

---

### US-P010: Coach Model and Data Layer [DONE]
**Priority:** HIGH
**Effort:** 3-4 hours (actual: 3 hours)
**Status:** DONE
**Completed:** 2025-10-10
**Spec Reference:** Lines 336-389

**Description:**
Create Coach model and supporting infrastructure to map coaches table to SQLAlchemy ORM.

**Acceptance Criteria:**
- [ ] Create Coach model in models/coach.py
- [ ] Map all coach fields from coaches table (80+ columns)
- [ ] Create hybrid properties: full_name, occupation_display, age_display
- [ ] Add relationship to Team model (coach.team)
- [ ] Add relationship to Player model (coach.former_player)
- [ ] Export Coach model from models/__init__.py

**Technical Notes:**
- Table has 80+ columns (ratings, preferences, contract info, etc.)
- Occupation codes: 1=GM, 2=Manager, 3=Bench Coach, 4=Pitching Coach, 5=Hitting Coach, 6=Scout, 12=Trainer, 13=Owner
- Former_player_id links to players_core.player_id
- Coach images should be in etl/data/images/coaches/ (similar to players)
- Position field exists but likely not used for coaches

**Files to Create:**
- `/web/app/models/coach.py` - Coach model with all fields and properties

**Files to Modify:**
- `/web/app/models/__init__.py` - Export Coach model

**Dependencies:** None

**Test Data:**
- Query database to understand data distribution: occupation types, former players vs non-players, team assignments

---

### US-P011: Coach List and Detail Pages [DONE]
**Priority:** HIGH
**Effort:** 4-6 hours (actual: 4 hours)
**Status:** DONE
**Completed:** 2025-10-10
**Spec Reference:** Lines 336-389

**Description:**
Create coach list and detail pages with basic header information.

**Acceptance Criteria:**
- [ ] Create `/coaches/` list page showing all coaches grouped by occupation
- [ ] Display: Name, Team, Occupation, Experience
- [ ] Link each coach to detail page
- [ ] Create `/coaches/<coach_id>` detail page
- [ ] Header section matches player page look/feel
- [ ] Display: Coach image (top left), Name, Occupation, Team, Experience
- [ ] Display: Age, DOB, Height, Weight, Birth City/Nation
- [ ] If former_player_id exists, show player image (top right) with link to player page
- [ ] Link current team to team page

**Technical Notes:**
- Reuse player page header structure and styling
- Coach images: `etl/data/images/coaches/coach_<coach_id>.png`
- Fallback to initials if no image (like player pages)
- Occupation display names: {"1": "General Manager", "2": "Manager", "3": "Bench Coach", etc.}

**Files to Create:**
- `/web/app/routes/coaches.py` - Route handlers
- `/web/app/templates/coaches/list.html` - Coach list page
- `/web/app/templates/coaches/detail.html` - Coach detail page

**Files to Modify:**
- `/web/app/routes/__init__.py` - Register coaches blueprint
- `/web/app/templates/base.html` - Add "Coaches" nav link (if not present)

**Dependencies:** US-P010 (Coach model)

---

### US-P012: Coach Ratings Bar Charts [DONE]
**Priority:** HIGH
**Effort:** 6-8 hours (actual: 2 hours)
**Status:** DONE
**Completed:** 2025-10-10
**Spec Reference:** Lines 344-350

**Description:**
Display coach ratings as color-coded horizontal bar charts showing values out of 200.

**Acceptance Criteria:**
- [ ] Section header: "Staff Ratings"
- [ ] Display 7 ratings as horizontal bar charts:
  - Manager Value (manager_value)
  - Pitching Coach Value (pitching_coach_value)
  - Hitting Coach Value (hitting_coach_value)
  - Scout Value (scout_value)
  - Teach Running (teach_running)
  - Teach Hitting (teach_hitting)
  - Doctor Value (doctor_value)
- [ ] Each bar shows value out of 200 (e.g., "145/200")
- [ ] Color coding: Red (0-40) → Orange (41-80) → Yellow (81-120) → Green (121-160) → Blue (161-200)
- [ ] Bars scale proportionally to value
- [ ] Include rating name label on left, value on right

**Technical Notes:**
- Use Tailwind CSS for bar charts (relative widths, background colors)
- Color thresholds:
  - Red: bg-red-500 (0-40)
  - Orange: bg-orange-500 (41-80)
  - Yellow: bg-yellow-500 (81-120)
  - Green: bg-green-500 (121-160)
  - Blue: bg-blue-500 (161-200)
- Calculate percentage: (value / 200) * 100
- Create reusable Jinja macro for bar chart component
- Responsive: Stack on mobile, 2-column on desktop

**Files to Create:**
- `/web/app/templates/coaches/_rating_bar.html` - Reusable bar chart macro

**Files to Modify:**
- `/web/app/templates/coaches/detail.html` - Add ratings section

**Dependencies:** US-P011 (Coach detail page)

---

### US-P013: Coach Preferences Display [DONE]
**Priority:** HIGH
**Effort:** 6-8 hours (actual: 2 hours)
**Status:** DONE
**Completed:** 2025-10-10
**Spec Reference:** Lines 351-389

**Description:**
Display coach preferences as markers on horizontal bars with color coding based on distance from 0.

**Acceptance Criteria:**
- [ ] Section header: "Coach Preferences"
- [ ] Display 24 preference fields as horizontal bars with center markers
- [ ] Scale: -5 (left) to +5 (right), with 0 in center
- [ ] Marker positioned at coach's value on the scale
- [ ] Color coding by absolute distance from 0:
  - Blue: 0-2 (bg-blue-500)
  - Green: 3-4 (bg-green-500)
  - Red: 5 (bg-red-500)
- [ ] Display all 24 preferences from spec:
  - Stealing, Running Aggressiveness, Use Pinch Runners, Use Pinch Hitters
  - Pull Starters, Pull Relievers, Use Closer, Favor L/R Matchups
  - Bunt For Hit, Bunt, Hit and Run, Run and Hit, Squeeze
  - Pitch Around Hitters, Intentional Walk, Hold Runner
  - Guard Lines, Infield In, Outfield In, Corners In
  - Shift Infield, Shift Outfield, Use Opener
  - Favor Speed to Power, Favor Offense to Defense, Favor Pitching to Hitting
  - Favor Veterans to Prospects, Trade Aggressiveness, Player Loyalty, Trade Frequency

**Technical Notes:**
- Map preference names to database fields:
  - "Stealing" → stealing
  - "Running Aggressiveness" → running
  - "Use Pinch Runners" → pinchrun
  - "Use Pinch Hitters" → pinchhit_pos (or pinchhit_pitch?)
  - "Pull Starters" → hook_start
  - "Pull Relievers" → hook_relief
  - "Use Closer" → closer
  - "Favor L/R Matchups" → lr_matchup
  - "Bunt For Hit" → bunt_hit
  - "Bunt" → bunt
  - "Hit and Run" → hit_run
  - "Run and Hit" → run_hit
  - "Squeeze" → squeeze
  - "Pitch Around Hitters" → pitch_around
  - "Intentional Walk" → intentional_walk
  - "Hold Runner" → hold_runner
  - "Guard Lines" → guard_lines
  - "Infield In" → infield_in
  - "Outfield In" → outfield_in
  - "Corners In" → corners_in
  - "Shift Infield" → shift_if
  - "Shift Outfield" → shift_of
  - "Use Opener" → opener
  - "Favor Speed to Power" → favor_speed_to_power
  - "Favor Offense to Defense" → favor_defense_to_offense (INVERSE)
  - "Favor Pitching to Hitting" → favor_pitching_to_hitting
  - "Favor Veterans to Prospects" → favor_veterans_to_prospects
  - "Trade Aggressiveness" → trade_aggressiveness
  - "Player Loyalty" → player_loyalty
  - "Trade Frequency" → trade_frequency
- Calculate marker position: ((value + 5) / 10) * 100 = percentage from left
- Create reusable Jinja macro for preference bar component
- Responsive: Stack on mobile, 2-column on desktop

**Files to Create:**
- `/web/app/templates/coaches/_preference_bar.html` - Reusable preference bar macro

**Files to Modify:**
- `/web/app/templates/coaches/detail.html` - Add preferences section

**Dependencies:** US-P011 (Coach detail page)

**Research Needed:**
- Verify field names match spec descriptions (some may need clarification)
- Confirm pinchhit_pos vs pinchhit_pitch usage
- Verify if favor_defense_to_offense should be inverted for "Favor Offense to Defense"

---

### US-P014: Coach Image Serving [DONE]
**Priority:** MEDIUM
**Effort:** 1-2 hours (actual: 1 hour)
**Status:** DONE
**Completed:** 2025-10-10
**Spec Reference:** Lines 339, 341-342

**Description:**
Serve coach images from filesystem with fallback to initials.

**Acceptance Criteria:**
- [ ] Create route `/coaches/image/<coach_id>` to serve coach images
- [ ] Load from `etl/data/images/coaches/coach_<coach_id>.png`
- [ ] Return 404 if image doesn't exist (client-side fallback handles it)
- [ ] Display coach image in header (90x135px like players)
- [ ] JavaScript fallback shows coach initials if image fails to load

**Technical Notes:**
- Reuse player image serving pattern from US-P004
- Same dimensions and fallback logic as player images
- Coach images directory: `etl/data/images/coaches/`

**Files to Modify:**
- `/web/app/routes/coaches.py` - Add coach_image() route
- `/web/app/templates/coaches/detail.html` - Add image display with fallback

**Dependencies:** US-P011 (Coach detail page)

---

### US-P015: Coach-Player Linkage Display [DONE]
**Priority:** MEDIUM
**Effort:** 2-3 hours (actual: 1 hour)
**Status:** DONE
**Completed:** 2025-10-10
**Spec Reference:** Lines 341-342

**Description:**
When a coach was formerly a player, display the player's image and link to their player page.

**Acceptance Criteria:**
- [ ] Check if coach.former_player_id is not null
- [ ] If former player exists, display in top-right corner of header
- [ ] Show most recent player image (90x135px)
- [ ] Link image to player detail page (`/players/<player_id>`)
- [ ] Add label: "Former Player" above/below image
- [ ] Gracefully handle if player record doesn't exist

**Technical Notes:**
- Query player record by former_player_id
- Reuse player image serving route
- Consider showing "View Player Career" link/button
- May want to show player's career stats summary (optional enhancement)

**Files to Modify:**
- `/web/app/routes/coaches.py` - Query former_player record
- `/web/app/templates/coaches/detail.html` - Add former player section

**Dependencies:** US-P011 (Coach detail page), US-P004 (Player images)

---

### US-P016: Enhanced Birthplace Display with State/Province [DONE]
**Priority:** LOW
**Effort:** 2-3 hours (actual: 1.5 hours)
**Status:** DONE
**Completed:** 2025-10-12
**Spec Reference:** UX enhancement request

**Description:**
Enhance the birthplace display on player and coach detail pages to include State/Province when the person was born in the United States or Canada.

**Acceptance Criteria:**
- [x] For players born in USA, display format: "City, State, USA" (e.g., "New York, NY, USA")
- [x] For players born in Canada, display format: "City, Province, Canada" (e.g., "Toronto, ON, Canada")
- [x] For all other countries, keep current format: "City, Country"
- [x] Apply same logic to coach detail pages
- [x] State/Province data sourced from cities.state_id field
- [x] Only display state/province if data exists in database

**Implementation Details:**
- Added `birthplace_display` hybrid property to both Player and Coach models
- Property handles state/province formatting logic internally
- Updated player and coach detail routes to eager-load state relationships using selectinload
- Updated templates to use simple `{{ player.birthplace_display }}` / `{{ coach.birthplace_display }}`
- Returns "Unknown" if no location data available

**Files Modified:**
- `/web/app/models/player.py` - Added birthplace_display property (lines 210-236)
- `/web/app/models/coach.py` - Added birthplace_display property (lines 228-254)
- `/web/app/routes/players.py` - Updated city_of_birth loading to include state (lines 138-151)
- `/web/app/routes/coaches.py` - Updated imports and city_of_birth loading (lines 1-66)
- `/web/app/templates/players/detail.html` - Simplified birthplace display (line 70)
- `/web/app/templates/coaches/detail.html` - Simplified birthplace display (lines 60-63)

**Technical Notes:**
- Cities table has state_id field linking to states table
- States table has state_id, nation_id, name, abbreviation columns
- Need to check if cities.state_id is populated for US/Canada cities
- May need to join: City → State → Nation to verify nation is USA/Canada
- Update player detail template (players/detail.html)
- Update coach detail template (coaches/detail.html)
- Consider adding state relationship to City model if not present

**Implementation Approach:**
1. Check if City model has state relationship defined
2. In player/coach detail routes, eager load city.state.nation
3. In templates, conditionally display state abbreviation for USA/Canada
4. Template logic: `{% if city.state and nation.name in ['United States', 'Canada'] %}{{ city.name }}, {{ state.abbreviation }}, {{ nation.abbreviation }}{% else %}{{ city.name }}, {{ nation.abbreviation }}{% endif %}`

**Data Validation Required:**
- Verify cities table has state_id populated for US/Canada cities
- Check states table for completeness (all 50 US states + Canadian provinces)
- Test with players from various countries to ensure proper display

**Dependencies:** None

---

### US-P017: Enhanced Draft Information Display [NOT STARTED]
**Priority:** LOW
**Effort:** 2-3 hours
**Status:** NOT STARTED
**Spec Reference:** UX enhancement request

**Description:**
Enhance the draft information display on player detail pages to include the name of the team that drafted the player, providing better historical context.

**Acceptance Criteria:**
- [ ] Draft field displays team name along with existing draft information
- [ ] Format: "YYYY - Round R, Pick P by Team Name" (e.g., "1984 - Round 2, Pick 188 by Detroit Tigers")
- [ ] Team name should be clickable link to team detail page
- [ ] Only display if player has draft information (many players are not drafted)
- [ ] Handle edge cases: undrafted players, international signees, etc.
- [ ] Apply to player detail page bio section

**Technical Notes:**
- Current draft data location needs investigation (likely players_core table or separate draft table)
- Fields likely include: draft_year, draft_round, draft_pick, draft_team_id
- Need to join with teams table to get team name
- Team relationship may need to be added to Player model
- Template location: `/web/app/templates/players/detail.html`

**Implementation Approach:**
1. Investigate draft data schema:
   - Check players_core table for draft-related columns
   - Check if separate draft_picks or draft_history table exists
   - Identify draft_team_id field (foreign key to teams table)

2. Update Player model (if needed):
   - Add draft_team relationship if not present
   - May need hybrid property for formatted draft display

3. Update player detail route:
   - Eager load draft_team relationship: `joinedload(Player.draft_team)`
   - Ensure draft_team is included in query options

4. Update player detail template:
   - Add team name to draft display
   - Make team name clickable: `<a href="{{ url_for('teams.team_detail', team_id=player.draft_team.team_id) }}">{{ player.draft_team.name }}</a>`
   - Example: `{{ player.draft_year }} - Round {{ player.draft_round }}, Pick {{ player.draft_pick }} by <a>{{ player.draft_team.name }}</a>`

**Data Validation Required:**
- Verify draft_team_id is populated in database
- Check for NULL values (undrafted players)
- Test with players from different draft eras
- Verify team_id references are valid (no broken foreign keys)

**Edge Cases to Handle:**
- Undrafted players: Display "Undrafted" or hide draft field entirely
- International signees: May have different acquisition method
- Players signed before draft era: Handle gracefully
- Team no longer exists (relocated/renamed): Still show historical team name

**Example Display Variations:**
- Drafted: "1984 - Round 2, Pick 188 by Detroit Tigers"
- Undrafted: "Undrafted Free Agent" or hide field
- First round: "1990 - Round 1, Pick 5 by New York Yankees"
- Supplemental round: "1988 - Supplemental Round, Pick 32 by Boston Red Sox" (if applicable)

**Testing Requirements:**
- Test with high draft picks (Round 1)
- Test with late-round picks (Round 20+)
- Test with undrafted players
- Test with players on multiple teams (verify correct draft team shown)
- Test link to team detail page works

**Dependencies:** None

---

### US-P018: Separate Stats Tables by League Level [DONE]
**Priority:** MEDIUM
**Effort:** 4-6 hours (actual: 2 hours)
**Status:** DONE
**Completed:** 2025-10-12
**Spec Reference:** Enhancement request - Session 13

**Description:**
Separate player statistics tables by league level on player detail pages. Major league (league_level=1) stats should display in separate tables from minor league (league_level>1) stats. A player with experience in both major and minor leagues should have up to 6 stats tables: All Levels (Batting/Pitching), Major League (Batting/Pitching), Minor League (Batting/Pitching).

**Acceptance Criteria:**
- [x] Stats tables are grouped by league level (All/Major/Minor)
- [x] All levels stats display first, followed by major, then minor
- [x] Each section has clear heading: "Career Batting Stats - All Levels", "Major League Batting Stats", "Minor League Batting Stats"
- [x] Career totals calculated separately for each league level
- [x] Batting and pitching tables maintain current functionality (sortable, formatted)
- [x] Only display tables that have data (e.g., hide Minor League Batting if player never played in minors)
- [x] League column in tables still shows specific league name (e.g., "MLB", "AAA", "AA")

**Implementation Details:**
- Modified service layer functions to accept optional `league_level_filter` parameter
- `get_player_career_batting_stats(player_id, league_level_filter=None)` - Filter: 1=major, 2+=minor, None=all
- `get_player_career_pitching_stats(player_id, league_level_filter=None)` - Same filter logic
- Conditional League JOIN only when filter is specified (backward compatible)
- Route calls each function 3 times: once for all levels, once for majors, once for minors
- Template displays up to 6 separate stat tables with conditional rendering
- Each table only displays if player has stats at that level

**Files Modified:**
- `/web/app/services/player_service.py` - Modified batting/pitching functions (lines 45-362)
- `/web/app/routes/players.py` - Updated to call functions 3x each with filters (lines 186-211)
- `/web/app/templates/players/detail.html` - Added 6 separate stat sections (lines 158-216)

**Technical Notes:**
- Current implementation: `/web/app/services/player_service.py` functions `get_player_career_batting_stats()` and `get_player_career_pitching_stats()`
- Currently queries ALL stats regardless of league level
- Need to split queries or add league_level filtering
- Tables currently join with leagues table but don't filter on league_level

**Implementation Approach:**

1. **Update Service Layer:**
   - Modify `get_player_career_batting_stats()` to accept optional `league_level_filter` parameter
   - Modify `get_player_career_pitching_stats()` to accept optional `league_level_filter` parameter
   - Add filter: `JOIN leagues l ON stats.league_id = l.league_id WHERE l.league_level = :level`
   - Calculate career totals separately for each league level
   - OR: Create new functions `get_player_major_league_stats()` and `get_player_minor_league_stats()`

2. **Update Route Layer:**
   - In `/web/app/routes/players.py` player_detail route:
   - Call service functions twice: once for league_level=1, once for league_level>1
   - Pass both datasets to template as separate variables
   - Example: `major_batting`, `minor_batting`, `major_pitching`, `minor_pitching`

3. **Update Template:**
   - In `/web/app/templates/players/detail.html`:
   - Create section: "Major League Statistics" (if data exists)
   - Display major batting table (if data)
   - Display major pitching table (if data)
   - Create section: "Minor League Statistics" (if data exists)
   - Display minor batting table (if data)
   - Display minor pitching table (if data)
   - Reuse existing table partials/components

**Data Considerations:**
- A player may have stats in major leagues only (league_level=1)
- A player may have stats in minor leagues only (league_level>1)
- A player may have stats in both major and minor leagues
- League level values: 1=Major, 2=AAA, 3=AA, 4=A, 5=Rookie, etc.
- Each table should maintain sortable columns functionality

**Example Player Scenarios:**
1. **Major League Only Player:** Shows 2 tables (Major Batting, Major Pitching)
2. **Minor League Only Player:** Shows 2 tables (Minor Batting, Minor Pitching)
3. **Career Player (Both Levels):** Shows 4 tables (Major Batting, Major Pitching, Minor Batting, Minor Pitching)
4. **Position Player (Batting Only):** Shows 1-2 tables depending on league history

**UI/UX Considerations:**
- Major league stats are more important, display first
- Clear visual separation between sections (headings, spacing)
- Consistent styling with current tables
- Mobile responsiveness maintained
- Career totals at bottom of each table group

**Testing Requirements:**
- Test with player who only played in majors
- Test with player who only played in minors
- Test with player who played in both majors and minors
- Test with player who has batting stats only
- Test with player who has pitching stats only
- Test with player who has both batting and pitching stats
- Verify career totals calculate correctly for each level
- Verify sortable columns work in all tables

**Performance Considerations:**
- Currently stats queries are already optimized with `lazyload()` and `raiseload()`
- Running 4 separate queries should have minimal impact (queries are fast ~20-50ms each)
- Could batch queries in future if performance becomes issue
- Maintain existing optimization patterns

**Alternative Approach (Future Enhancement):**
- Add tabbed interface to switch between Major/Minor stats
- Single-page app style with JavaScript toggle
- Would require US-I006 (JavaScript framework) - defer to later

**Dependencies:** US-P001 (Batting stats table), US-P002 (Pitching stats table)

---

## Epic 2: Team Pages

### US-T001: Team Logo Display [DONE]
**Priority:** MEDIUM
**Effort:** 2-3 hours (actual: 1 hour)
**Status:** DONE
**Completed:** 2025-10-10
**Spec Reference:** Lines 43, 339

**Description:**
Display team logos on team pages with placeholder fallback.

**Acceptance Criteria:**
- [ ] Logo displayed on team home and team year pages
- [ ] Use team_logos table for logo paths
- [ ] Fallback placeholder for missing logos
- [ ] Consistent sizing and positioning

**Technical Notes:**
- Similar to player images
- Need to populate team_logos table or create strategy
- Placeholder: generic team icon or text abbreviation

**Dependencies:** None (can use placeholders)

---

### US-T002: Team Year Pages [DONE]
**Priority:** HIGH
**Effort:** 8-10 hours (actual: ~10 hours)
**Status:** DONE
**Spec Reference:** Lines 347-353, 375-387
**Completed:** 2025-10-10

**Description:**
Create team-year detail pages showing roster, stats, and results for a specific season.

**Acceptance Criteria:**
- [x] URL: `/teams/<team_id>/<year>`
- [x] Team logo and header
- [x] Previous/next year navigation
- [x] Team batting stats table (aggregate team stats)
- [x] Team pitching stats table (aggregate team stats)
- [x] Individual player batting stats table (all players with position column)
- [x] Individual player pitching stats table (all pitchers)
- [x] Top 12 players by WAR (with images)
- [x] Season record, place in standings

**Implementation Details:**

**Templates Created:**
- `/web/app/templates/teams/year.html` - Main team year page (206 lines)
- `/web/app/templates/teams/_roster_batting_table.html` - Individual player batting stats component (72 lines)
- `/web/app/templates/teams/_roster_pitching_table.html` - Individual player pitching stats component (74 lines)
- `/web/app/templates/teams/_top_players_grid.html` - Top 12 players grid with images (44 lines)

**Service Layer Functions:**
- `get_team_year_data(team_id, year)` - Retrieves team, record, batting/pitching aggregate stats
- `get_team_player_batting_stats(team_id, year)` - Individual player batting stats with position data
- `get_team_player_pitching_stats(team_id, year)` - Individual player pitching stats
- `get_team_top_players_by_war(team_id, year, limit)` - Top players by WAR (batting + pitching)
- `get_available_years_for_team(team_id)` - Years for prev/next navigation

**Features:**
- Handles both current year (1997) and historical years (1980-1996)
- Aggregate team batting/pitching stats displayed prominently
- Individual player stats tables with sortable columns (20 batting columns, 17 pitching columns)
- Top 12 players grid with player images and WAR values
- Previous/next year navigation with disabled states for missing years
- Responsive design with horizontal scroll for wide stat tables
- Sticky first column (player name) in roster tables

**Performance:**
- Query optimization implemented using SQLAlchemy `load_only()` and `raiseload()`
- Page load times: 0.3-0.5 seconds
- Minimal database queries (optimized service layer)

**Known Limitations:**
- **Position Data Workaround:** Currently sourcing player positions from `players_current_status` table (current position) instead of historical position data. This works for current/recent seasons but may be inaccurate for older historical data.
  - **Future Enhancement:** Once `players_career_fielding_stats` table is implemented, update `get_team_player_batting_stats()` in `team_service.py` to join with fielding stats instead of current status for accurate historical position data.
  - **Affected Files:** `/web/app/services/team_service.py` (lines 111-146)

**Dependencies:** US-T001 (Team logos - placeholder system in place)

**Files Created/Modified:**
- `/web/app/templates/teams/year.html` - Created
- `/web/app/templates/teams/_roster_batting_table.html` - Created
- `/web/app/templates/teams/_roster_pitching_table.html` - Created
- `/web/app/templates/teams/_top_players_grid.html` - Created
- `/web/app/routes/teams.py` - Added team_year() route (lines 123-160)
- `/web/app/services/team_service.py` - Added 4 service functions
- `/web/app/models/team_history.py` - Created with 5 models (TeamHistoryRecord, TeamHistoryBattingStats, TeamHistoryPitchingStats, TeamBattingStats, TeamPitchingStats)

---

### US-T002B: Remove Current Roster from Team Home & Add Current Year Link [DONE]
**Priority:** HIGH
**Effort:** 2-3 hours (actual: ~1 hour)
**Status:** DONE
**Completed:** 2025-10-10
**Spec Reference:** Follow-up to Session 4 performance optimization

**Description:**
Remove the simplified current roster table from the team home page and replace it with a prominent link to the current season's team-year page, which will show the full detailed roster.

**Context:**
During Session 4 performance optimization (US-T003), we switched the roster query to raw SQL to eliminate 1,849 cascading queries. This simplified roster now only shows: player name, position, bats, throws, birth city/nation. It lacks the rich detail that a proper roster should have (stats, jersey numbers, etc.).

Instead of maintaining two roster displays, we should:
1. Remove the simplified roster from team home page
2. Add a clear, prominent link to the current season team-year page
3. Ensure the current year team-year page has full roster details

**Acceptance Criteria:**
- [x] Remove roster section from `/web/app/templates/teams/detail.html`
- [x] Remove roster query from `/web/app/routes/teams.py` team_detail() route (lines ~90-135)
- [x] Remove `get_position_display()` helper function (no longer needed)
- [x] Add prominent "Current Season" or "1997 Season" button/card near top of team home page
- [x] Button links to `/teams/<team_id>/1997` (current year team-year page)
- [x] Ensure current year team-year page exists and displays full roster with stats
- [x] Update coaching staff section to remain on home page (coaches are current, not seasonal)
- [x] Test that navigation flow makes sense: Team Home → Current Year → Player details

**UI/UX Considerations:**
- Button should be visually prominent (large, colored, clear call-to-action)
- Consider card/panel with current season stats preview: "1997 Season: 45-32, 2nd place"
- Position near top after franchise header, before franchise history sections
- Could include current W-L record, place in standings as teaser
- Mobile-friendly (works on small screens)

**Technical Notes:**
- This simplifies team home page and improves performance further (removes roster query entirely)
- Team-year pages already have infrastructure for detailed rosters (US-T002)
- Current year = 1997 (stored in CURRENT_GAME_YEAR constant in team_service.py)
- Team-year page should handle both historical years and current year seamlessly

**Implementation Details:**
1. **Removed from teams.py:**
   - Lines 20-26: `get_position_display()` helper function
   - Lines 93-145: Entire roster query (raw SQL + object conversion)
   - Removed `roster` from render_template context
   - Added `current_year=1997` to template context
   - Updated profiling step numbers (2→2, 3→3, etc.)

2. **Created Current Season Card (teams/detail.html lines 51-77):**
   - Large gradient blue card (from-blue-600 to-blue-800)
   - Left side: "1997 Season" heading with arrow CTA
   - Right side: Current W-L record, winning percentage, standings position
   - Full card is clickable link to `/teams/<team_id>/1997`
   - Hover effect (shadow-xl) for better UX
   - Positioned after team header, before coaching staff

3. **Removed from teams/detail.html:**
   - Lines 174-235: Entire "Active Roster" section with player table
   - Player images, names, positions, age, bats/throws, birthplace columns

**Performance Impact:**
- **ACTUAL:** Reduced team home page from 12 queries to 11 (removes roster query)
- **ACTUAL:** Reduced route execution time by ~12-15ms
- Simplified page complexity and maintenance burden

**Files Modified:**
- `/web/app/routes/teams.py` - Removed roster query, helper function, updated profiling
- `/web/app/templates/teams/detail.html` - Removed roster section, added current season card

**Testing:**
- ✅ Team home page loads: HTTP 200
- ✅ Current season card displays with correct link
- ✅ Roster section successfully removed (no "Active Roster" in HTML)
- ✅ Link to team-year page works: `/teams/1/1997` returns HTTP 200
- ✅ Coaching staff section remains on home page

**Dependencies:**
- US-T002 (Team Year Pages) - Complete and functional ✅
- US-T003 (Team Home Historical Summary) - Complete ✅

**Follow-up Tasks:**
- Consider adding "View Full Roster" links to other years in year-by-year table
- May want to add navigation breadcrumbs: Home > Teams > [Team Name] > [Year]

**Session 5 Completion Time:** ~1 hour (estimated 2-3 hours)

---

### US-T003: Team Home - Historical Summary [DONE]
**Priority:** HIGH
**Effort:** 6-8 hours (actual: ~10 hours including performance optimization)
**Status:** DONE
**Spec Reference:** Lines 339-345, 357-368
**Completed:** 2025-10-10 (Session 4)

**Description:**
Enhance team home page with franchise history, top players, year-by-year records.

**Acceptance Criteria:**
- [x] Team logo top-left
- [x] H2: "$Team_nickname Team History & Encyclopedia"
- [x] Former team names (from team_history) - Deferred, data not available
- [x] Count of seasons
- [x] All-time W-L record
- [x] Playoff appearances count - Deferred, data not available
- [x] Championships count - Deferred, data not available
- [x] Top 24 franchise players by WAR (2x12 grid with images)
- [x] Year-by-year franchise table (all seasons)
- [ ] Organizational leaderboards links - Deferred until leaderboards exist

**Implementation Details:**
- Created comprehensive service layer in team_service.py:
  - `get_franchise_history()` - Aggregates all-time W-L from team_history tables
  - `get_franchise_top_players()` - CTE query for top 24 players by total WAR
  - `get_franchise_year_by_year()` - Year-by-year records with current season
- Template includes all franchise data sections
- Player grid component displays player cards with images

**Performance Optimization (Critical):**
This user story required extensive performance optimization work that became the focus of Session 4:

**Problem Discovered:**
- Initial implementation took 28+ seconds to load with 1,861 SQL queries
- Root cause: SQLAlchemy's `lazy='joined'` on models causing cascading eager loads
- Roster query alone generated 1,849 queries (Player → City → Nation → Continent cascade)
- `raiseload('*')` only blocks accessing relationships, not loading them

**Solution Implemented:**
1. **Raw SQL for Roster Query** - Eliminated 1,849 cascading queries by bypassing ORM entirely
2. **Optimized Team Query** - Used load_only(), selectinload(), and nested raiseload('*')
3. **Service Layer Optimization** - Added raiseload('*') to all franchise service functions
4. **Helper Function** - Created get_position_display() for position code mapping

**Performance Results:**
- BEFORE: 28,000ms with 1,861 queries
- AFTER: 120ms with 12 queries
- **Improvement: 99.6% reduction in page load time (232x faster)**
- **Query reduction: 99.4% fewer queries**

**Files Created/Modified:**
- `/web/app/services/team_service.py` - Added franchise service functions with optimization
- `/web/app/routes/teams.py` - Added raw SQL roster query, helper function, db import
- `/web/app/templates/teams/detail.html` - Integrated franchise history sections
- `/continuity.txt` - Documented Session 4 performance optimization journey

**Technical Highlights:**
- PostgreSQL CTE (WITH clause) for top players aggregation
- Partial indexes on stats tables (team_id, player_id WHERE split_id=1 AND war IS NOT NULL)
- Raw SQL with text() to completely bypass ORM relationship machinery
- Simple objects from dictionaries for template compatibility
- Nested raiseload('*') to prevent cascading through related models

**Key Learnings:**
- When models have `lazy='joined'`, SQLAlchemy loads relationships during query construction
- Only way to prevent cascading eager loads is to NOT use the ORM for these queries
- Raw SQL with text() is sometimes the only viable solution for complex relationship graphs
- Measuring query count is as important as measuring execution time

**Dependencies:** US-T001 (Team logos - done with placeholder system)

---

### US-T004: Team Roster Display Enhancement [NOT STARTED]
**Priority:** MEDIUM
**Effort:** 2-3 hours
**Status:** NOT STARTED
**Spec Reference:** Current implementation basic

**Description:**
Improve current team roster display with better formatting and stats.

**Acceptance Criteria:**
- [ ] Group by position (Pitchers, Catchers, Infielders, Outfielders)
- [ ] Show key stats (AVG/HR/RBI for batters, ERA/W-L for pitchers)
- [ ] Jersey numbers
- [ ] Bats/Throws
- [ ] Link to player pages (already done)

**Technical Notes:**
- Enhance existing teams/detail.html
- Query current year stats for each player

**Dependencies:** None

---

### US-T005: Team Coaching Staff Display [DONE]
**Priority:** MEDIUM
**Effort:** 2-3 hours (actual: 1 hour)
**Status:** DONE
**Completed:** 2025-10-10
**Spec Reference:** Lines 404 (manager in year-by-year stats), 336-389 (coaches section)

**Description:**
Display coaching staff on team pages with links to coach detail pages.

**Acceptance Criteria:**
- [ ] Add "Coaching Staff" section to team detail page
- [ ] Display all coaches for current team (WHERE team_id = X)
- [ ] Group by occupation: Manager, Coaches, Scouts, Front Office
- [ ] Display: Coach Name, Occupation, Experience
- [ ] Link each coach to coach detail page
- [ ] Show coach images (thumbnail size)
- [ ] Display in team year pages as well (manager in year-by-year table)

**Technical Notes:**
- Query coaches table: `Coach.query.filter_by(team_id=team_id).all()`
- Sort by occupation priority: Manager (2) first, then Bench/Pitching/Hitting coaches (3,4,5), then others
- Occupation display names: {"1": "GM", "2": "Manager", "3": "Bench Coach", "4": "Pitching Coach", "5": "Hitting Coach", "6": "Scout", "12": "Trainer", "13": "Owner"}
- For team year pages, only show manager (occupation=2)

**Files to Modify:**
- `/web/app/routes/teams.py` - Query coaches for team
- `/web/app/templates/teams/detail.html` - Add coaching staff section
- `/web/app/templates/teams/year.html` (when created) - Add manager to year header

**Dependencies:** US-P010 (Coach model), US-P011 (Coach pages)

---

## Epic 3: Leaderboards

### US-L001: Leaderboard Infrastructure & Service Layer [DONE]
**Priority:** HIGH
**Effort:** 8-10 hours (actual: ~4 hours)
**Status:** DONE
**Spec Reference:** Lines 100-163, 643-686
**Completed:** 2025-10-10

**Description:**
Build core leaderboard query infrastructure with caching and optimization.

**Acceptance Criteria:**
- [x] Create leaderboard_service.py with reusable query functions
- [x] Implement materialized views for expensive aggregations
- [x] Set up caching strategy (Redis when available, in-memory for now)
- [x] Generic leaderboard query function with filters (stat, type, year, league)
- [x] Support for Career, Single-Season, Active leaderboards

**Technical Notes:**
- Critical for performance with 18+ seasons of data
- Use database indexes aggressively
- Consider pre-calculating common leaderboards in ETL

**Dependencies:** None (but Redis preferred)

**Implementation Notes (2025-10-10):**
1. **Materialized Views:** Leveraged existing 6 materialized views from ETL:
   - `leaderboard_career_batting` - Pre-aggregated career totals for all players
   - `leaderboard_career_pitching` - Pre-aggregated career pitching stats
   - `leaderboard_single_season_batting` - Best seasons (min 100 PA)
   - `leaderboard_single_season_pitching` - Best seasons (min 50 IP)
   - `leaderboard_yearly_batting` - Top 10 per year/league for key stats
   - `leaderboard_yearly_pitching` - Top 10 per year/league for key stats

2. **Created Leaderboard Models** (`/web/app/models/leaderboard.py`):
   - 6 read-only SQLAlchemy models mapping to materialized views
   - All include `is_active` flag for filtering active/retired players
   - Models use ReadOnlyMixin to prevent accidental writes

3. **Created Leaderboard Service** (`/web/app/services/leaderboard_service.py`):
   - **Career Leaders:** `get_career_batting_leaders()`, `get_career_pitching_leaders()`
   - **Single-Season Leaders:** `get_single_season_batting_leaders()`, `get_single_season_pitching_leaders()`
   - **Yearly League Leaders:** `get_yearly_batting_leaders()`, `get_yearly_pitching_leaders()`
   - **Helper Functions:** `get_top_level_leagues()`, `get_league_options()`, `get_available_years()`, `get_stat_metadata()`

4. **Filtering Capabilities:**
   - League filtering (top-level leagues only, as agreed)
   - Year filtering (single-season and yearly views)
   - Active/retired filtering (all views)
   - Stat-specific sorting (asc for ERA/WHIP, desc for all others)
   - Minimum qualification thresholds applied (1000 PA career, 500 IP career, 100 PA season, 50 IP season)

5. **Caching Strategy:**
   - In-memory cache with 15-minute TTL
   - Cache key generated from function name + parameters
   - `clear_cache()` function for manual cache invalidation
   - Ready for Redis integration (same interface)

6. **Performance Results (from test suite):**
   - Career batting leaders: 15-23ms
   - Career pitching leaders: 9-16ms
   - Single-season leaders: 15-18ms
   - Yearly league leaders: 5-7ms
   - Cache speedup: 537x faster (6.8ms → 0.01ms)
   - All queries well under target benchmark (<30ms, <2s for leaderboards)

**Files Created:**
- `/web/app/models/leaderboard.py` - 6 read-only models for materialized views
- `/web/app/services/leaderboard_service.py` - Complete service layer with caching
- `/test_leaderboards.py` - Comprehensive test suite (all tests passing)

**Files Modified:**
- `/web/app/models/__init__.py` - Added leaderboard model exports

**Test Coverage:**
- ✓ League options and filtering
- ✓ Career batting leaders (HR, AVG with PA threshold)
- ✓ Career pitching leaders (W, ERA with IP threshold)
- ✓ Single-season leaders (all-time and year-specific)
- ✓ Yearly league leaders (batting and pitching)
- ✓ Caching functionality and performance
- ✓ Stat metadata retrieval

**Architecture Decisions:**
- **League Filtering:** Top-level leagues only (league_level = 1). For career stats, uses subquery to find players with stats in target league
- **Universe Definition:** "All Leagues" includes all top-level leagues (not minors)
- **Qualification Thresholds:** Kept existing thresholds (100 PA, 50 IP single-season; 1000 PA, 500 IP career for rate stats)
- **View Enhancement:** Kept materialized views as-is, filter in application layer for league-specific career stats

---

### US-L002: Leaderboard Home Page [DONE]
**Priority:** HIGH
**Effort:** 4-6 hours (actual: ~2 hours)
**Status:** DONE
**Spec Reference:** Lines 127-142
**Completed:** 2025-10-10

**Description:**
Create main leaderboard landing page with current year leaders and links to all leaderboards.

**Acceptance Criteria:**
- [x] H1: "Overall Baseball Leaders & Baseball Records"
- [x] "$Year Leaders" section with links to batting/pitching by league
- [x] 3-column current leaders table (top player for each stat across all leagues)
- [x] "All-Time Career and Single-Season Records" section
- [x] Links to all leaderboard types for each stat

**Technical Notes:**
- Template-heavy, queries from leaderboard service
- Grid layout for leaderboard type matrix

**Dependencies:** US-L001

**Implementation Notes (2025-10-10):**
1. **Route Created** (`/web/app/routes/leaderboards.py`):
   - Added `/` and `/home` routes for leaderboard home page
   - Fetches current year leaders for top 10 key stats (5 batting, 5 pitching)
   - Uses leaderboard service to get single-season leaders for current year (1997)
   - Passes leagues, current_leaders, and stat_metadata to template

2. **Template Created** (`/web/app/templates/leaderboards/home.html`):
   - **Header:** "Overall Baseball Leaders & Baseball Records"
   - **Current Year Leaders Section:**
     - Displays "1997 Leaders" heading
     - League cards with links to batting/pitching leaderboards per league
     - 3-column responsive grid showing current leaders
     - Each stat shows: stat name, player link, team abbr, value
     - Proper formatting for AVG (.XXX), ERA, WHIP
   - **All-Time Records Section:**
     - Separate batting and pitching tables
     - 4-column matrix: Statistic | Single-Season | Career | Active | Yearly
     - Each cell links to appropriate leaderboard page with query params
     - Batting stats: HR, AVG, RBI, SB, H, OBP, SLG
     - Pitching stats: W, SV, SO, ERA, WHIP, K/9
   - Tailwind styling with hover states and responsive layout

3. **Navigation Updated:**
   - Changed base.html nav link from `/leaderboards/batting` to `/leaderboards/home`

4. **Current Year Leaders Displayed:**
   - HR, AVG, RBI, SB, H (batting)
   - W, SV, SO, ERA, WHIP (pitching)
   - Each shows top player across all leagues for 1997 season

**Files Created:**
- `/web/app/templates/leaderboards/home.html` - Complete home page template

**Files Modified:**
- `/web/app/routes/leaderboards.py` - Added home route with data fetching
- `/web/app/templates/base.html` - Updated navigation link

**Performance:**
- Page loads quickly (all data cached from previous queries)
- Queries 10 single-season leaderboards (5 batting + 5 pitching)
- Each query <20ms due to materialized view performance

**Next Steps:**
- Individual leaderboard pages (US-L003, US-L004, etc.) will use query params from these links
- Example URLs: `/leaderboards/batting?type=career&stat=hr`

---

### US-L003: Career Leaderboards [DONE]
**Priority:** HIGH
**Effort:** 4-6 hours (actual: ~2 hours)
**Status:** DONE
**Spec Reference:** Lines 108-126, 188-191
**Completed:** 2025-10-11

**Description:**
Career leaders for all major batting and pitching stats.

**Acceptance Criteria:**
- [x] Separate pages for each stat (HR, AVG, RBI, W, K, ERA, etc.)
- [x] Top 100 leaders (paginated or scrollable)
- [x] Filters: All-time, By League, Active/Retired, Type (Career/Active/Single-Season/Yearly)
- [x] Display: Rank, Player Name, Value, Years Played (career), Year/Team (single-season)
- [x] Links to player pages

**Technical Notes:**
- URL pattern: `/leaderboards/batting` and `/leaderboards/pitching`
- Query params: `?type=career&stat=hr&league=X&year=Y`
- Use leaderboard service with filters

**Dependencies:** US-L001

**Test Coverage:**
- Test with qualifying stats (min PA/IP thresholds)

**Implementation Notes (2025-10-11):**
1. **Routes Created** (`/web/app/routes/leaderboards.py`):
   - Enhanced `/batting` and `/pitching` routes to handle all leaderboard types
   - Query params: `type` (career/active/single-season/yearly), `stat`, `league`, `year`
   - Validates stat is appropriate for category (batting/pitching)
   - Calls appropriate service functions based on type
   - Passes all filter options to template

2. **Unified Template** (`/web/app/templates/leaderboards/leaderboard.html`):
   - Single template handles all leaderboard types (career, active, single-season, yearly)
   - **Filter Section:**
     - Type dropdown (Career, Active, Single-Season, Yearly)
     - Stat dropdown (8 batting stats, 7 pitching stats)
     - League dropdown (All Leagues + 4 top-level leagues)
     - Year dropdown (shown only for single-season and yearly types)
     - JavaScript to show/hide year filter dynamically
   - **Dynamic Table Columns:**
     - Career/Active: Rank, Player, Seasons, Stat Value, G, PA/IP, AB, H
     - Single-Season: Rank, Player, Year, Team, Stat Value
     - Yearly: Rank, Player, League, Stat Value
   - **Breadcrumb Navigation:** Home > Leaderboards > Batting/Pitching
   - **Responsive Design:** Sticky rank and player columns, horizontal scroll for stats
   - **Proper Stat Formatting:**
     - AVG/OBP/SLG: .XXX format
     - ERA/WHIP: X.XX format
     - K/9: X.XX format
     - WAR: X.X format
     - IP: XXX.X format
     - Counting stats: Integer format

3. **Features Implemented:**
   - All 4 leaderboard types work from single template
   - League filtering works for career and active types (subquery approach)
   - Year filtering works for single-season and yearly types
   - Active status filtering works (is_active flag)
   - **Active player indicators:** Asterisk (*) shown next to active players on career/single-season types
   - Legend: "* Denotes active player" at bottom of table
   - Links to player detail pages
   - Links to team-year pages (single-season only; yearly shows league abbr)
   - Top 100 results displayed (scrollable)
   - Proper sort order (desc for counting stats, asc for ERA/WHIP)

4. **Testing Results:**
   - ✓ Career HR leaders: Elton Scott* (530 HR, 17 seasons) - active player indicator working
   - ✓ Active players filter works
   - ✓ Career pitching leaders: Andrew McKay (18 seasons)
   - ✓ Career batting average leaders (rate stat)
   - ✓ Career ERA leaders (lower is better)
   - ✓ Single-season HR leaders: Chris Johnson* (65 HR, 1996, MON)
   - ✓ Year and team columns display correctly
   - ✓ 1997 single-season filter works
   - ✓ Yearly RBI leaders: Carlos Gonzalez (118 RBI, 1990, PL League)
   - ✓ Yearly pitching leaders: Ubbe de Witte (1985, PL League)
   - ✓ All filter combinations tested and working

5. **Bonus Achievement:**
   - **US-L004 (Single-Season) and US-L005 (Active) also completed!**
   - Single template approach means all leaderboard types are done
   - US-L004 and US-L005 acceptance criteria fully met
   - Yearly leaderboards working (US-L006 partially complete - display works, needs dedicated page)

**Files Created:**
- `/web/app/templates/leaderboards/leaderboard.html` - Unified leaderboard template (260 lines)

**Files Modified:**
- `/web/app/routes/leaderboards.py` - Enhanced batting/pitching routes with full filtering (220 lines)
- `/web/app/services/leaderboard_service.py` - Fixed yearly functions to return dict format

6. **Bug Fixes (Post-Implementation):**
   - **Form Dropdown Bug:** Removed hidden `type` input that was overriding dropdown selections
   - **Yearly Return Type:** Fixed `get_yearly_batting_leaders()` and `get_yearly_pitching_leaders()` to return `{'leaders': [...], 'total': count}` instead of list
   - **Yearly Template Fields:** Changed yearly table to show `league_abbr` instead of non-existent `team_id`/`team_abbr`
   - **Active Player Indicators:** Added asterisk (*) for active players on career and single-season leaderboards

**Performance:**
- All queries use cached service layer
- Page loads <200ms (materialized view queries)
- Filter changes require form submit (no AJAX needed)

**Architecture Decisions:**
- Single template approach reduces code duplication
- Query param-based filtering (RESTful, bookmarkable URLs)
- JavaScript only for UI enhancement (year filter visibility)
- All business logic in service layer, routes just coordinate

---

### US-L004: Single-Season Leaderboards [DONE]
**Priority:** HIGH
**Effort:** 4-6 hours (actual: ~0 hours, completed with US-L003)
**Status:** DONE
**Spec Reference:** Lines 108-126, 188-191
**Completed:** 2025-10-11

**Description:**
Single-season leaders for all major stats.

**Acceptance Criteria:**
- [x] Separate pages for each stat
- [x] Top 100 seasons
- [x] Filters: All-time, By Year, By League
- [x] Display: Rank, Player Name, Year, Team, Value
- [x] Links to player and team-year pages

**Technical Notes:**
- URL pattern: `/leaderboards/batting?type=single-season&stat=hr`
- Query params: `?year=X&league=Y`

**Dependencies:** US-L001

**Implementation Notes (2025-10-11):**
- **Completed as part of US-L003 implementation**
- Uses same unified template and routes
- Access via: `/leaderboards/batting?type=single-season&stat=hr`
- Year dropdown shows all available years (1980-1997)
- "All-Time" option shows best single-season performances ever
- Table displays: Rank, Player Name, Year, Team Abbr (linked to team-year), Stat Value
- Example: Chris Johnson, 1996, MON, 65 HR
- All acceptance criteria met and tested

---

### US-L005: Active Player Leaderboards [DONE]
**Priority:** MEDIUM
**Effort:** 3-4 hours (actual: ~0 hours, completed with US-L003)
**Status:** DONE
**Spec Reference:** Lines 109, 138, 193
**Completed:** 2025-10-11

**Description:**
Career leaders among active (non-retired) players only.

**Acceptance Criteria:**
- [x] Same format as career leaderboards
- [x] Filter to players where retired = 0
- [x] Clear indication these are active players only

**Technical Notes:**
- URL pattern: `/leaderboards/batting?type=active&stat=hr`
- Join with players_current_status WHERE retired = 0

**Dependencies:** US-L001

**Implementation Notes (2025-10-11):**
- **Completed as part of US-L003 implementation**
- Uses same unified template and routes
- Access via: `/leaderboards/batting?type=active&stat=hr`
- Page header clearly shows "Active Player Career Leaders"
- Service layer filters with `active_only=True` parameter
- Uses `is_active` flag from materialized view
- Same display format as career leaderboards (Rank, Player, Seasons, Stat, G, PA/IP)
- All acceptance criteria met and tested

---

### US-L006: Yearly League Leaders [DONE]
**Priority:** MEDIUM
**Effort:** 4-6 hours (actual: ~1.5 hours)
**Status:** DONE
**Spec Reference:** Lines 105-106, 114, 140, 194
**Completed:** 2025-10-11

**Description:**
League leaders for each stat, by year and league.

**Acceptance Criteria:**
- [x] Dropdown to select year and league
- [x] Show top 10 for each stat in that league/year
- [x] Grouped by batting and pitching
- [x] Links to full leaderboards

**Technical Notes:**
- URL: `/leaderboards/yearly` (query params: `?year=X&league=Y`)
- Card/grid layout with 6 stats per category
- Responsive: 3 columns on desktop, 2 on tablet, 1 on mobile

**Dependencies:** US-L001

**Implementation Notes (2025-10-11):**
1. **Route Created** (`/web/app/routes/leaderboards.py` - lines 222-291):
   - Added `/leaderboards/yearly` route with year and league query params
   - Defaults to current year (1997) and "All Leagues"
   - Fetches top 10 leaders for 12 stats (6 batting + 6 pitching)
   - Uses existing `get_yearly_batting_leaders()` and `get_yearly_pitching_leaders()` service functions

2. **Template Created** (`/web/app/templates/leaderboards/yearly.html` - 186 lines):
   - **Filter Section:** Year and league dropdowns with "Update Leaders" button
   - **Batting Leaders Section:** 6 stat cards (HR, AVG, RBI, SB, H, WAR)
   - **Pitching Leaders Section:** 6 stat cards (W, SV, SO, ERA, WHIP, WAR)
   - **Card Layout:**
     - Stat name header (blue for batting, green for pitching)
     - Compact table showing top 10 players with rank, name, league, and stat value
     - "View Full Leaderboard" link to detailed single-stat page
   - **Responsive Grid:** 3 columns (lg), 2 columns (md), 1 column (mobile)
   - **Null Handling:** Shows "-" for null stat values
   - **Stat Formatting:**
     - AVG: .XXX format
     - ERA/WHIP: X.XX format
     - WAR: X.X format
     - Counting stats: Integer

3. **Home Page Integration** (`/web/app/templates/leaderboards/home.html`):
   - Added prominent "View All 1997 League Leaders →" button after current leaders section
   - Links to yearly page with current year parameter

4. **Stats Displayed:**
   - **Batting:** Home Runs, Batting Average, RBI, Stolen Bases, Hits, WAR
   - **Pitching:** Wins, Saves, Strikeouts, ERA, WHIP, WAR

5. **Testing Results:**
   - ✓ Page loads successfully (HTTP 200)
   - ✓ Defaults to 1997, All Leagues
   - ✓ Year filter works (tested 1990)
   - ✓ League filter works
   - ✓ All 12 stat cards display correctly
   - ✓ Player links work (url_for 'players.player_detail')
   - ✓ "View Full Leaderboard" links work (proper query params)
   - ✓ Button on home page links correctly

6. **Performance:**
   - 12 service calls (cached materialized view queries)
   - Each query <10ms due to caching
   - Total page load <200ms
   - All data cached with 15-minute TTL

**Files Created:**
- `/web/app/templates/leaderboards/yearly.html` - Yearly leaders page template (186 lines)

**Files Modified:**
- `/web/app/routes/leaderboards.py` - Added yearly() route (70 lines)
- `/web/app/templates/leaderboards/home.html` - Added navigation button to yearly page
- `/web/app/services/leaderboard_service.py` - Added NULL filtering and proper ordering for All Leagues view

**Architecture Decisions:**
- Query params approach (`?year=X&league=Y`) instead of URL path (`/<year>/<league>`)
- Provides cleaner default behavior (current year) and easier filtering
- Card-based layout for better visual hierarchy and scannability
- Links to existing unified leaderboard pages for full details
- Color coding: blue for batting, green for pitching

**Bug Fixes (Post-Implementation):**
- **NULL stat filtering:** Added `stat_column.isnot(None)` filter to exclude records with NULL stat values (fixes 1997 AVG issue where rank exists but value is NULL)
- **All Leagues ordering:** Changed ordering logic - single league uses rank, All Leagues orders by actual stat value (DESC for most stats, ASC for ERA/WHIP)

---

### US-L007: Year-by-Year Top Tens [DONE]
**Priority:** LOW
**Effort:** 8-10 hours (actual: ~2.5 hours)
**Status:** DONE
**Spec Reference:** Lines 143-147, 195
**Completed:** 2025-10-13

**Description:**
Expandable grid showing #1 player for each year, with "Show #2-10" expansion.

**Acceptance Criteria:**
- [x] 4-column grid, each cell = one year
- [x] Shows #1 player and value
- [x] "Show #2-10" link expands to show ranks 2-10
- [x] Collapsible accordion behavior

**Implementation Notes (2025-10-13):**
1. **Service Layer Function** (`/web/app/services/leaderboard_service.py` - lines 708-779):
   - Added `get_year_by_year_leaders()` function
   - Queries single-season leaderboard views for all years
   - Returns dict with years as keys, each containing top 10 leaders
   - Supports filtering by stat, category (batting/pitching), and league
   - Uses caching with 15-minute TTL

2. **Route Created** (`/web/app/routes/leaderboards.py` - lines 294-351):
   - `/leaderboards/year-by-year` route
   - Query params: `stat`, `category`, `league`
   - Defaults to HR for batting
   - Validates stat belongs to selected category
   - Passes sorted years (descending) to template

3. **Template Created** (`/web/app/templates/leaderboards/year_by_year.html` - 197 lines):
   - Responsive grid layout: 1 col (mobile), 2 cols (md), 3 cols (lg), 4 cols (xl)
   - Filter dropdowns for category, stat, and league
   - Each year card shows:
     - Year header with gradient background
     - #1 leader (always visible) with yellow highlight
     - Player name, team abbreviation, stat value
     - "Show #2-10" toggle button
     - Hidden #2-10 section (expandable via JavaScript)
   - Proper stat formatting (AVG, ERA, WHIP, decimals, integers)
   - Active player indicators (asterisk)
   - Breadcrumb navigation
   - Vanilla JavaScript toggle function (no framework needed)

4. **Features Implemented:**
   - 18 years of data displayed (1980-1997)
   - Toggle behavior: "Show #2-10 ▼" changes to "Hide #2-10 ▲"
   - No AJAX needed - all data pre-loaded and hidden with CSS
   - Performant: One service call fetches all years at once
   - Links to player detail and team-year pages

5. **Testing Results:**
   - ✓ Page loads (HTTP 200)
   - ✓ 37 "Show #2-10" buttons (18 years with data)
   - ✓ Batting stats working (HR, AVG, RBI, etc.)
   - ✓ Pitching stats working (W, SV, SO, ERA, etc.)
   - ✓ League filtering working
   - ✓ Toggle accordion working
   - ✓ All links functional

**Files Created:**
- `/web/app/templates/leaderboards/year_by_year.html` (197 lines)

**Files Modified:**
- `/web/app/services/leaderboard_service.py` - Added get_year_by_year_leaders() function
- `/web/app/routes/leaderboards.py` - Added year_by_year() route

**Technical Decisions:**
- Pre-load all #2-10 data instead of AJAX (simpler, faster with caching)
- Vanilla JavaScript for toggle (no need for Alpine.js or framework)
- 4-column responsive grid (adapts to screen size)
- Query param-based filtering (RESTful, bookmarkable URLs)

**Dependencies:** US-L001

---

### US-L008: Progressive Leaderboards [NOT STARTED]
**Priority:** LOW
**Effort:** 12-16 hours
**Status:** DEFERRED
**Spec Reference:** Lines 149-162, 194

**Description:**
Show leader at each year for Career, Single-Season, Active, and Yearly categories.

**Acceptance Criteria:**
- [ ] Table with columns: Year, Career Leader, Career Value, Single-Season Leader, SS Value, Active Leader, Active Value, Yearly Leader, Yearly Value
- [ ] One row per year
- [ ] Computationally expensive - needs pre-calculation

**Technical Notes:**
- Extremely complex queries (point-in-time calculations)
- MUST be pre-calculated in ETL or background job
- Store in materialized view or separate table

**Dependencies:** ETL enhancement, background jobs

---

### US-L009: Mega Dropdown Navigation [DONE]
**Priority:** MEDIUM
**Effort:** 4-6 hours (actual: ~1.5 hours)
**Status:** DONE
**Spec Reference:** Lines 104-106, 167-168, 187
**Completed:** 2025-10-13

**Description:**
Multi-level dropdown menu for leaderboard navigation in header.

**Acceptance Criteria:**
- [x] Hover over "Leaderboards" shows dropdown
- [x] Categories: Batting Leaders (by league), Pitching Leaders (by league), Career/Single-Season/Active/etc.
- [x] Links to all leaderboard types
- [x] Mobile-friendly (click instead of hover)

**Implementation Notes (2025-10-13):**
1. **Desktop Mega Dropdown** (`/web/app/templates/base.html` - lines 27-85):
   - Replaced simple "Leaderboards" link with dropdown button
   - 3-column mega menu layout (Batting, Pitching, Quick Links)
   - **Batting Leaders column** (8 stats):
     - Home Runs, Batting Average, RBI, Stolen Bases, Hits, OBP, SLG, WAR
     - All link to career leaderboards with proper query params
     - Blue color theme with hover states
   - **Pitching Leaders column** (7 stats):
     - Wins, Saves, Strikeouts, ERA, WHIP, K/9, WAR
     - All link to career leaderboards with proper query params
     - Green color theme with hover states
   - **Quick Links column**:
     - Leaderboards Home, Current Year Leaders
     - Leaderboard Types: Career, Active, Single-Season, Yearly
   - Hover behavior: Shows menu on mouseenter with 200ms delay on leave
   - Click behavior: Toggle menu on button click (for touch devices)
   - Click-outside-to-close functionality
   - Auto-closes when link clicked

2. **Mobile Accordion Menu** (`/web/app/templates/base.html` - lines 130-145):
   - Collapsible "Leaderboards" section in mobile menu
   - Toggle button with chevron icon (rotates on expand)
   - Simplified links: Home, Current Year, Career, Active, Single-Season
   - Vertical stacking for mobile UX

3. **JavaScript Implementation** (`/web/app/templates/base.html` - lines 362-420):
   - **Desktop dropdown script**:
     - Mouseenter/mouseleave with timeout for smooth UX
     - Click toggle for touch devices
     - Click-outside detection to close menu
     - Auto-close on link click
   - **Mobile accordion script**:
     - Toggle visibility with CSS classes
     - Chevron rotation animation (180deg)
   - Both use vanilla JavaScript (no framework needed)

4. **Testing Results:**
   - ✓ All links tested and working (HTTP 200)
   - ✓ Career HR leaders: working
   - ✓ Career wins leaders: working
   - ✓ Yearly leaderboards: working
   - ✓ Mega menu HTML present in page
   - ✓ Mobile accordion present

5. **Features Delivered:**
   - 15 direct stat links (8 batting + 7 pitching)
   - 6 navigation links (home, yearly, 4 leaderboard types)
   - Responsive design (desktop hover, mobile click)
   - Smooth animations and transitions
   - Consistent with existing nav styling
   - All links use proper url_for() with query params

**Files Modified:**
- `/web/app/templates/base.html` - Added mega dropdown HTML, mobile accordion, JavaScript

**Technical Decisions:**
- Static HTML approach (no dynamic league generation) for simplicity
- Vanilla JavaScript instead of Alpine.js (lighter weight)
- 3-column layout optimized for desktop screens (max-width: 4xl)
- Separate mobile UX (accordion vs mega menu)
- Color coding: Blue for batting, Green for pitching, Gray for links

**Dependencies:** Leaderboard pages exist to link to

---

## Epic 5: League & Year Pages

### US-LY001: League Home Pages [DONE]
**Priority:** MEDIUM
**Effort:** 6-8 hours (Actual: ~3 hours)
**Status:** DONE (Session 16: 2025-10-13)
**Completed:** 2025-10-13
**Spec Reference:** Lines 34, 63-64

**Description:**
Create league detail pages showing current standings, stats, leaders.

**Acceptance Criteria:**
- [x] URL: `/leagues/<league_id>`
- [x] League logo and header
- [x] Current standings (by division)
- [x] Top 10 batting leaders (this league only)
- [x] Top 10 pitching leaders (this league only)
- [x] Team batting and pitching aggregate stats
- [x] Link to full league leaderboards

**Technical Notes:**
- Similar to front page, but filtered to one league
- Reuse standings component

**Dependencies:** Leaderboard infrastructure

**Implementation Details:**
- **Service Layer Created:** `/web/app/services/league_service.py`
  - `get_league_standings()` - Returns current standings grouped by sub-league/division
  - `get_league_team_stats()` - Returns aggregate batting/pitching stats for all teams in league
  - Reused standings logic from main.py front page route
  - Optimized queries with explicit relationship loading controls

- **Routes Created:** `/web/app/routes/leagues.py`
  - `league_home()` route at `/leagues/<league_id>`
  - Fetches standings, team stats, and top 10 leaders per stat (5 batting + 5 pitching stats)
  - Uses `leaderboard_service.get_yearly_batting_leaders()` and `get_yearly_pitching_leaders()`
  - Current year hardcoded to 1997 (TODO: Make dynamic based on league.season_year)

- **Template Created:** `/web/app/templates/leagues/home.html`
  - League header with season year and current game date
  - Standings section (reused component from index.html)
  - Two-column leaders section (batting left, pitching right)
  - Top 5 leaders shown per stat with "View All" link to filtered leaderboards
  - Team stats tables for batting and pitching
  - Uses `leader.first_name`, `leader.last_name`, `leader.league_abbr` from LeaderboardYearlyBatting/Pitching models
  - Dynamic stat value access via `leader[stat]` dictionary-style attribute access

- **Blueprint Registration:** Updated `/web/app/__init__.py` to register leagues blueprint

**Known Issues/Limitations:**
- League logo not yet implemented (logo_file_name field exists but not displayed)
- Current year is hardcoded to 1997 - should use league.season_year dynamically
- Team stats sorted alphabetically, not by standings position
- Awards section not included (awards data structure TBD)

**Files Created:**
- `/web/app/services/league_service.py` (329 lines)
- `/web/app/routes/leagues.py` (147 lines - includes both US-LY001 and US-LY002)
- `/web/app/templates/leagues/home.html` (280 lines)

**Files Modified:**
- `/web/app/__init__.py` - Added leagues blueprint registration

---

### US-LY002: Year Summary Pages [DONE]
**Priority:** MEDIUM
**Effort:** 6-8 hours (Actual: ~3 hours)
**Status:** DONE (Session 16: 2025-10-13)
**Completed:** 2025-10-13
**Spec Reference:** Lines 36, 46, 551

**Description:**
Create year detail pages showing results, leaders, and awards for a specific season.

**Acceptance Criteria:**
- [x] URL: `/leagues/years/<year>` (chose /leagues prefix for consistency)
- [x] Show all leagues for that year
- [x] Final standings (or current if ongoing)
- [x] Top 10 batting/pitching leaders
- [ ] Awards (MVP, Cy Young, etc.) if available (deferred - data structure TBD)
- [x] Links to team-year pages

**Technical Notes:**
- Query historical data from team_history and league_history tables
- Awards data structure needs investigation

**Dependencies:** Team-year pages, historical data models

**Implementation Details:**
- **Service Layer Updated:** `/web/app/services/league_service.py`
  - `get_year_standings()` - Returns standings for all leagues for a specific year
  - `get_available_years()` - Returns list of all years with historical data
  - Handles both current year (1997, uses TeamRecord) and historical years (uses TeamHistoryRecord)
  - Key insight: Cannot assign TeamHistoryRecord to Team.record relationship (SQLAlchemy type mismatch)
  - Solution: Attached historical records as `team.history_record` attribute instead

- **Routes Updated:** `/web/app/routes/leagues.py`
  - `year_summary()` route at `/leagues/years/<year>`
  - Year validation against available years (404 if invalid)
  - Year navigation (prev/next year links)
  - Fetches standings for all leagues
  - Top 10 batting/pitching leaders (6 stats each)
  - Uses yearly leaders for current year, single-season leaders for historical years

- **Template Created:** `/web/app/templates/leagues/year.html`
  - Year header with current/historical indicator
  - Year dropdown for quick navigation
  - Prev/Next year navigation buttons
  - Standings for all leagues (grouped by sub-league/division)
  - Team links go to team-year pages (`/teams/<team_id>/<year>`)
  - Two-column leaders section (batting left, pitching right)
  - Top 5 leaders shown per stat
  - Conditional rendering based on `is_current_year` flag
  - Uses `team.record` for current year, `team.history_record` for historical years

**Key Technical Challenges:**
1. **SQLAlchemy Relationship Type Mismatch:**
   - Problem: Tried to assign TeamHistoryRecord to Team.record (expects TeamRecord)
   - Solution: Used separate attribute `team.history_record` for historical data
   - Template uses conditional `{% if is_current_year %}` to access correct attribute

2. **Lazy Load Errors with raiseload('*'):**
   - Problem: Template trying to check `team.record is defined` triggered lazy load attempt
   - Solution: Used explicit `is_current_year` flag instead of attribute existence check

3. **Template Syntax Error:**
   - Initial implementation had typo: missing `}` in Jinja2 expression
   - Fixed with proper closing braces in format filters

**Files Created:**
- `/web/app/templates/leagues/year.html` (239 lines)

**Files Modified:**
- `/web/app/services/league_service.py` - Added year-related functions
- `/web/app/routes/leagues.py` - Added year_summary() route

**Known Issues/Limitations:**
- Awards not implemented (data structure unknown)
- Year dropdown shows all historical years (could be large list for long-running saves)
- Current year detection is hardcoded (year == 1997) - should be dynamic
- Single-season vs yearly leaders logic is duplicated - could be refactored

---

## Epic 6: Search & Navigation

### US-N001: Global Search Functionality [DONE]
**Priority:** HIGH
**Effort:** 8-10 hours (actual: 3 hours)
**Status:** DONE
**Completed:** 2025-10-12
**Spec Reference:** base.html line 29 (placeholder exists)

**Description:**
Implement search for players, teams with autocomplete and full results page.

**Acceptance Criteria:**
- [x] Search box in header (functional form)
- [x] Autocomplete as user types (300ms debounce)
- [x] Search players by name (first, last, or full name)
- [x] Search teams by name or abbreviation
- [x] Results page shows grouped results (players and teams separate)
- [x] Keyboard navigation support (arrow keys, Enter, Escape)

**Implementation Details:**
- Created search service with `search_players()`, `search_teams()`, and `search_all()` functions
- Uses PostgreSQL ILIKE for case-insensitive partial matching
- Autocomplete endpoint returns up to 5 results per type (players/teams)
- Full search results page shows up to 50 results per type
- JavaScript autocomplete with debouncing, keyboard navigation, click-outside-to-close
- Responsive dropdown with player/team icons, subtitles showing team/position or league
- Minimum 2 characters required for search

**Files Created:**
- `/web/app/services/search_service.py` - Search service layer
- `/web/app/templates/search/results.html` - Search results page
- `/web/app/routes/search.py` - Search routes (updated from placeholder)

**Files Modified:**
- `/web/app/templates/base.html` - Added search form and autocomplete JavaScript (lines 27-200)
- `/web/app/__init__.py` - Fixed search blueprint registration (line 30)

**Technical Notes:**
- Uses PostgreSQL ILIKE for case-insensitive search (not full-text search)
- Excludes team_id=0 (college/high school players) from player results
- Future enhancement: Add Elasticsearch for better search performance and fuzzy matching

**Dependencies:** None

**Testing:**
- Autocomplete API tested with curl: Returns 5 results for "smith" query
- Server restart required to load new search routes

---

### US-N002: Breadcrumb Navigation [DONE]
**Priority:** MEDIUM
**Effort:** 2-3 hours (Actual: 1.5 hours)
**Status:** DONE (Session 14: 2025-10-13)
**Spec Reference:** Lines 377, 394

**Description:**
Add breadcrumb navigation to all detail pages.

**Acceptance Criteria:**
- [x] Show path: Home > Category > Item
- [x] Examples: "Home > Teams > Giants", "Home > Players > M > Mike Smith"
- [x] Links to each level
- [x] Styled with separators (chevrons or slashes)

**Implementation:**
- **Macro Created:** `/web/app/templates/_macros/breadcrumbs.html`
  - Reusable breadcrumb component
  - Home icon for first item
  - Chevron separators between items
  - Last item (current page) not linked
  - Responsive design
- **Pages Updated:**
  - Player detail: Home > Players > [Letter] > Player Name
  - Coach detail: Home > Coaches > Coach Name
  - Team detail: Home > Teams > Team Name
  - Team year: Home > Teams > Team Name > Year
  - Leaderboards: Home > Leaderboards > Batting/Pitching
- Replaced custom breadcrumb in leaderboard template with macro for consistency

**Technical Notes:**
- Used Jinja2 macro pattern for reusability
- SVG icons from Heroicons (home, chevron)
- Tailwind CSS styling
- Accessible markup with aria-label and aria-current

**Files Created:**
- `/web/app/templates/_macros/breadcrumbs.html` (46 lines)

**Files Modified:**
- `/web/app/templates/players/detail.html` - Added breadcrumb import and display
- `/web/app/templates/coaches/detail.html` - Added breadcrumb import and display
- `/web/app/templates/teams/detail.html` - Added breadcrumb import and display
- `/web/app/templates/teams/year.html` - Added breadcrumb import and display
- `/web/app/templates/leaderboards/leaderboard.html` - Replaced custom breadcrumb with macro

**Dependencies:** None

---

### US-N003: Site Navigation Enhancements [DONE]
**Priority:** MEDIUM
**Effort:** 3-4 hours (Actual: 2 hours)
**Status:** DONE (Session 14: 2025-10-13)
**Spec Reference:** Lines 46

**Description:**
Update navigation to match specs (add Seasons, Newspaper links) and add mobile menu.

**Acceptance Criteria:**
- [x] Nav links: Home, Players, Teams, Coaches, Leaderboards
- [x] Mobile hamburger menu implemented
- [x] Mobile search form
- [x] Responsive design (desktop/mobile)

**Implementation:**
- **Desktop Navigation:**
  - Enhanced with Coaches link
  - Search bar remains in top navigation
  - Horizontal menu for larger screens
- **Mobile Navigation:**
  - Hamburger menu button (toggle between hamburger/X icon)
  - Slide-down mobile menu with vertical nav links
  - Mobile search form in dropdown
  - Auto-close menu when link clicked
  - Responsive breakpoint: md (768px)
- **JavaScript:**
  - Mobile menu toggle functionality
  - Icon switching (hamburger ↔ close)
  - Link click auto-close

**Technical Notes:**
- Tailwind CSS responsive utilities (hidden md:flex, md:hidden)
- SVG icons for hamburger and close (Heroicons)
- Vanilla JavaScript (no framework needed)
- Accessible (screen reader labels with sr-only)

**Files Modified:**
- `/web/app/templates/base.html`:
  - Restructured nav (lines 14-84)
  - Added mobile menu HTML
  - Added mobile menu toggle script (lines 256-285)

**Future Enhancements:**
- Seasons/Newspaper links when those sections are ready
- Active page highlighting in navigation
- Dropdown menus for subnavigation

**Dependencies:** None

---

### US-N004: Game Date Display in Header [DONE]
**Priority:** LOW
**Effort:** 1-2 hours (Actual: 45 minutes)
**Status:** DONE (Session 14: 2025-10-13)
**Spec Reference:** UX enhancement request

**Description:**
Display the current game date prominently in the page header between the top navigation and search bar, giving users immediate context about the current in-game date.

**Acceptance Criteria:**
- [x] Game date displayed on every page in the header
- [x] Positioned between top navigation bar and game content
- [x] Format: "Current Date: June 01, 1997" (Month DD, YYYY)
- [x] Sourced from league table's game_date field
- [x] Centered for visibility
- [x] Responsive design (works on mobile)
- [x] No performance impact (context processor runs once per request)

**Implementation:**
- **Context Processor:** `/web/app/context_processors.py` (NEW - 41 lines)
  - `inject_game_date()` function queries first top-level league (league_level=1)
  - Returns `current_game_date` and `current_game_year` to all templates
  - Error handling with fallback to None
- **App Factory:** `/web/app/__init__.py` (lines 36-38)
  - Registered context processor
- **Template:** `/web/app/templates/base.html` (lines 86-98)
  - Game date banner between nav and main content
  - Gradient background (gray-100 to gray-200) with calendar icon
  - Centered text: "Current Date: June 01, 1997"
  - Conditional display (only if current_game_date exists)

**Technical Notes:**
- Uses first league with league_level=1 (all leagues share same game_date)
- Context processor runs once per request (minimal overhead)
- Error handling prevents crashes if no leagues exist
- Responsive design (works on all screen sizes)

**Files Created:**
- `/web/app/context_processors.py`

**Files Modified:**
- `/web/app/__init__.py` - Registered context processor
- `/web/app/templates/base.html` - Added game date banner

**Future Enhancements:**
- Link to "Today's Games" or schedule page
- Season progress indicator (e.g., "Day 45 of 162")
- Cache with Redis (TTL: 1 hour) for higher traffic

**Dependencies:** None

---

