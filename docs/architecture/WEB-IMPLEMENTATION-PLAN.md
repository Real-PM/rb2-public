# RB2 Web Application Implementation Plan

## Overview

### Framework Recommendation: Flask + Jinja2 + HTMX + Tailwind CSS

Based on project requirements and technical constraints, this stack is ideal:

- **Flask**: Familiar framework, flexible architecture, perfect for low-traffic application (~200 concurrent users)
- **Jinja2**: Preferred templating engine, Flask's default
- **HTMX**: Server-side rendering focus with progressive enhancement for dynamic features
- **Tailwind CSS**: Modern utility-first CSS framework for rapid UI development

**Why Flask over Django:**
- Existing Flask comfort level reduces ramp-up time
- Jinja2 templating preference aligns with Flask default
- Low traffic doesn't require Django's heavier infrastructure
- Incremental complexity through Flask extensions as needed
- Provides learning opportunity without overwhelming new patterns

### Project Requirements Summary

**Reference Website (Baseball-Reference.com clone):**
- Player pages with stats, images, biographical data, and similarity scores
- Team pages (franchise home and year-specific)
- League/Season pages with standings and statistics
- Comprehensive leaderboards (career, single-season, progressive, year-by-year top tens)
  - All leaderboards mix active and retired players
  - Active players indicated with asterisk (*) after name
  - Optional filters to show only active or retired players
- Front page with player images, rookie highlights, standings, and "born this week" features
- Heavy data tables with hyperlinked navigation throughout

**Newspaper Section:**
- AI-generated news stories from game logs, box scores, and transaction data
- User-written stories about the Branch family
- Template-based content system with web editor
- Full integration with links to the Reference section

**Technical Constraints:**
- Single content producer + AI-generated content
- Max ~200 concurrent visitors (low traffic)
- Updates every game-day or game-week (game-days ≠ calendar days)
- Full-text search functionality required
- Server-side rendering preferred, JavaScript where appropriate
- Player images already in ETL; team/league logos TBD
- Review workflow needed during dev, not in prod
- Leaderboard queries may need optimization
- Caching strategy required

---

## Critical Database Gaps Identified

### Missing Database Components

1. **No search/autocomplete support**
   - Need: Full-text search indexes on `players_core` (name fields)
   - Need: Full-text search on `teams` (name, nickname, abbr)
   - Action: Add PostgreSQL GIN indexes for `tsvector` columns

2. **No aggregated leaderboard tables**
   - Current: Stats are normalized by year/team/stint
   - Need: Pre-aggregated career totals table for performance
   - Need: Single-season records table for quick lookups
   - Note: All leaderboards mix active and retired players with active player indicator (e.g., asterisk)

3. **No team/league logo associations**
   - Tables have `logo_file_name` columns but no file path management
   - Need: `team_logos` and `league_logos` tables similar to `person_images`

4. **No newspaper/content tables**
   - Need: `newspaper_articles` table
   - Need: `article_categories` (game recap, feature story, Branch family journal, etc.)
   - Need: `article_tags` for linking articles to players/teams/games

5. **No player similarity scores**
   - Need: `player_similarity_scores` table
   - Need: Calculation function (can be ETL job or on-demand)

6. **Missing current game date tracking**
   - Need: `game_state` table to track current in-game date
   - Important for "Born this week" and time-based features

### Required SQL Scripts (NEW FILES)

- `etl/sql/tables/06_web_support.sql` - Web support tables (team/league logos)
- `etl/sql/tables/07_newspaper.sql` - Newspaper tables (articles, categories, tags)
- `etl/sql/tables/08_search_indexes.sql` - Full-text search indexes (GIN/tsvector)
- `etl/sql/tables/09_leaderboard_views.sql` - Materialized views for leaderboards

**Note:** Current game date is now stored in `leagues.game_date` (added via ETL changes)

---

## Phase 1: Database & Backend Foundation (2-3 weeks)

### 1.1 Database Schema Extensions

**✅ Task 1.1.1: Web Support Tables** (COMPLETE)
- ✅ Created `etl/sql/tables/06_web_support.sql`
- ✅ Create `team_logos` table for logo file management
- ✅ Create `league_logos` table for logo file management
- ✅ Note: Current game date tracked via `leagues.game_date` (added in ETL changes)

**✅ Task 1.1.2: Newspaper Tables** (COMPLETE)
- ✅ Created `etl/sql/tables/07_newspaper.sql`
- ✅ Create `newspaper_articles` table with rich metadata
- ✅ Create `article_categories` table with pre-populated categories (8 categories)
- ✅ Create `article_player_tags` junction table
- ✅ Create `article_team_tags` junction table
- ✅ Create `article_game_tags` junction table
- ✅ Documented article tagging strategy (Task 3.2.4)

**✅ Task 1.1.3: Search Indexes** (COMPLETE)
- ✅ Created `etl/sql/tables/08_search_indexes.sql`
- ✅ Add PostgreSQL GIN indexes for full-text search on players (tsvector)
- ✅ Add PostgreSQL GIN indexes for full-text search on teams
- ✅ Add text_pattern_ops indexes for autocomplete
- ✅ Create composite indexes for common query patterns ("born this week", etc.)

**✅ Task 1.1.4: Leaderboard Optimization** (COMPLETE)
- ✅ Created `etl/sql/tables/09_leaderboard_views.sql`
- ✅ Create materialized views for career leaderboards (batting & pitching)
- ✅ Create materialized views for single-season records (batting & pitching)
- ✅ Create materialized views for yearly league leaders (batting & pitching)
- ⏳ Add refresh mechanism to ETL pipeline (PENDING)
- ✅ Note: All leaderboard views include active status indicator for display (asterisk)

### 1.2 Flask Project Structure

```
/mnt/hdd/PycharmProjects/rb2/web/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration classes
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── team.py
│   │   ├── stats.py
│   │   └── newspaper.py
│   ├── routes/              # Route blueprints
│   │   ├── __init__.py
│   │   ├── main.py          # Home page
│   │   ├── players.py
│   │   ├── teams.py-- =====================================================
  -- Leaderboard Materialized Views
  -- =====================================================
  -- Pre-aggregated views for high-performance leaderboard queries.
  -- These views are refreshed after each ETL run.
  --
  -- All views include is_active flag to support mixed 
  -- active/retired player leaderboards with visual indicators.
  -- =====================================================

  -- Drop existing views (for clean re-creation)
  DROP MATERIALIZED VIEW IF EXISTS leaderboard_career_batting CASCADE;
  DROP MATERIALIZED VIEW IF EXISTS leaderboard_career_pitching CASCADE;
  DROP MATERIALIZED VIEW IF EXISTS leaderboard_single_season_batting CASCADE;
  DROP MATERIALIZED VIEW IF EXISTS leaderboard_single_season_pitching CASCADE;
  DROP MATERIALIZED VIEW IF EXISTS leaderboard_yearly_batting CASCADE;
  DROP MATERIALIZED VIEW IF EXISTS leaderboard_yearly_pitching CASCADE;

  -- =====================================================
  -- Career Leaderboards
  -- =====================================================

  -- Career Batting Leaders (all players, with active status)
  CREATE MATERIALIZED VIEW leaderboard_career_batting AS
  SELECT
      s.player_id,
      p.first_name,
      p.last_name,
      COUNT(DISTINCT s.year) as seasons,
      SUM(s.g) as g,
      SUM(s.pa) as pa,
      SUM(s.ab) as ab,
      SUM(s.r) as r,
      SUM(s.h) as h,
      SUM(s.d) as doubles,
      SUM(s.t) as triples,
      SUM(s.hr) as hr,
      SUM(s.rbi) as rbi,
      SUM(s.sb) as sb,
      SUM(s.cs) as cs,
      SUM(s.bb) as bb,
      SUM(s.so) as so,
      SUM(s.ibb) as ibb,
      SUM(s.hbp) as hbp,
      SUM(s.sh) as sh,
      SUM(s.sf) as sf,
      SUM(s.gdp) as gdp,
      -- Calculated rate stats (weighted by PA)
      CASE WHEN SUM(s.ab) > 0
           THEN ROUND(SUM(s.h)::NUMERIC / SUM(s.ab)::NUMERIC, 3)
           ELSE 0 END as avg,
      CASE WHEN SUM(s.ab) > 0
           THEN ROUND((SUM(s.h) + SUM(s.bb) + SUM(s.hbp))::NUMERIC /
                      (SUM(s.ab) + SUM(s.bb) + SUM(s.hbp) + SUM(s.sf))::NUMERIC, 3)
           ELSE 0 END as obp,
      CASE WHEN SUM(s.ab) > 0
           THEN ROUND((SUM(s.h) + SUM(s.d) + SUM(s.t)*2 + SUM(s.hr)*3)::NUMERIC /
                      SUM(s.ab)::NUMERIC, 3)
           ELSE 0 END as slg,
      SUM(s.war) as war,
      -- Active status flag
      COALESCE(ps.retired, 1) = 0 as is_active,
      ps.retired
  FROM players_career_batting_stats s
  INNER JOIN players_core p ON s.player_id = p.player_id
  LEFT JOIN players_current_status ps ON s.player_id = ps.player_id
  WHERE s.split_id = 1  -- Only regular season stats
  GROUP BY s.player_id, p.first_name, p.last_name, ps.retired;

  -- Indexes for fast lookups
  CREATE INDEX idx_lb_career_bat_hr ON leaderboard_career_batting(hr DESC);
  CREATE INDEX idx_lb_career_bat_avg ON leaderboard_career_batting(avg DESC);
  CREATE INDEX idx_lb_career_bat_rbi ON leaderboard_career_batting(rbi DESC);
  CREATE INDEX idx_lb_career_bat_sb ON leaderboard_career_batting(sb DESC);
  CREATE INDEX idx_lb_career_bat_war ON leaderboard_career_batting(war DESC);
  CREATE INDEX idx_lb_career_bat_active ON leaderboard_career_batting(is_active);

  COMMENT ON MATERIALIZED VIEW leaderboard_career_batting IS 'Career batting statistics for all players with active status indicator';

  -- Career Pitching Leaders (all players, with active status)
  CREATE MATERIALIZED VIEW leaderboard_career_pitching AS
  SELECT
      s.player_id,
      p.first_name,
      p.last_name,
      COUNT(DISTINCT s.year) as seasons,
      SUM(s.w) as w,
      SUM(s.l) as l,
      SUM(s.g) as g,
      SUM(s.gs) as gs,
      SUM(s.cg) as cg,
      SUM(s.sho) as sho,
      SUM(s.sv) as sv,
      SUM(s.ip) as ip,
      SUM(s.h) as h,
      SUM(s.r) as r,
      SUM(s.er) as er,
      SUM(s.hr) as hr,
      SUM(s.bb) as bb,
      SUM(s.so) as so,
      SUM(s.hbp) as hbp,
      SUM(s.wp) as wp,
      SUM(s.bk) as bk,
      -- Calculated rate stats
      CASE WHEN SUM(s.ip) > 0
           THEN ROUND((SUM(s.er) * 9.0) / SUM(s.ip), 2)
           ELSE 0 END as era,
      CASE WHEN SUM(s.ip) > 0
           THEN ROUND((SUM(s.bb) + SUM(s.h)) / SUM(s.ip), 2)
           ELSE 0 END as whip,
      CASE WHEN SUM(s.ip) > 0
           THEN ROUND((SUM(s.so) * 9.0) / SUM(s.ip), 2)
           ELSE 0 END as k_per_9,
      CASE WHEN SUM(s.bb) > 0
           THEN ROUND(SUM(s.so)::NUMERIC / SUM(s.bb)::NUMERIC, 2)
           ELSE 0 END as k_bb_ratio,
      SUM(s.war) as war,
      -- Active status flag
      COALESCE(ps.retired, 1) = 0 as is_active,
      ps.retired
  FROM players_career_pitching_stats s
  INNER JOIN players_core p ON s.player_id = p.player_id
  LEFT JOIN players_current_status ps ON s.player_id = ps.player_id
  WHERE s.split_id = 1  -- Only regular season stats
  GROUP BY s.player_id, p.first_name, p.last_name, ps.retired;

  -- Indexes for fast lookups
  CREATE INDEX idx_lb_career_pit_w ON leaderboard_career_pitching(w DESC);
  CREATE INDEX idx_lb_career_pit_sv ON leaderboard_career_pitching(sv DESC);
  CREATE INDEX idx_lb_career_pit_so ON leaderboard_career_pitching(so DESC);
  CREATE INDEX idx_lb_career_pit_era ON leaderboard_career_pitching(era ASC) WHERE ip >= 500;
  CREATE INDEX idx_lb_career_pit_whip ON leaderboard_career_pitching(whip ASC) WHERE ip >= 500;
  CREATE INDEX idx_lb_career_pit_war ON leaderboard_career_pitching(war DESC);
  CREATE INDEX idx_lb_career_pit_active ON leaderboard_career_pitching(is_active);

  COMMENT ON MATERIALIZED VIEW leaderboard_career_pitching IS 'Career pitching statistics for all players with active status indicator';

  -- =====================================================
  -- Single-Season Leaderboards
  -- =====================================================

  -- Single-Season Batting Records (all players, with active status)
  CREATE MATERIALIZED VIEW leaderboard_single_season_batting AS
  SELECT
      s.player_id,
      p.first_name,
      p.last_name,
      s.year,
      s.league_id,
      l.abbr as league_abbr,
      s.team_id,
      t.abbr as team_abbr,
      s.g,
      s.pa,
      s.ab,
      s.r,
      s.h,
      s.d as doubles,
      s.t as triples,
      s.hr,
      s.rbi,
      s.sb,
      s.bb,
      s.so,
      -- Calculated stats
      CASE WHEN s.ab > 0 THEN ROUND(s.h::NUMERIC / s.ab::NUMERIC, 3) ELSE 0 END as avg,
      CASE WHEN s.ab > 0
           THEN ROUND((s.h + s.bb + s.hbp)::NUMERIC /
                      (s.ab + s.bb + s.hbp + s.sf)::NUMERIC, 3)
           ELSE 0 END as obp,
      CASE WHEN s.ab > 0
           THEN ROUND((s.h + s.d + s.t*2 + s.hr*3)::NUMERIC / s.ab::NUMERIC, 3)
           ELSE 0 END as slg,
      s.war,
      -- Active status flag
      COALESCE(ps.retired, 1) = 0 as is_active
  FROM players_career_batting_stats s
  INNER JOIN players_core p ON s.player_id = p.player_id
  LEFT JOIN players_current_status ps ON s.player_id = ps.player_id
  LEFT JOIN leagues l ON s.league_id = l.league_id
  LEFT JOIN teams t ON s.team_id = t.team_id
  WHERE s.split_id = 1  -- Only regular season stats
    AND s.pa >= 100;    -- Minimum PA threshold for meaningful stats

  -- Indexes for fast lookups
  CREATE INDEX idx_lb_ss_bat_year ON leaderboard_single_season_batting(year DESC);
  CREATE INDEX idx_lb_ss_bat_hr ON leaderboard_single_season_batting(hr DESC);
  CREATE INDEX idx_lb_ss_bat_avg ON leaderboard_single_season_batting(avg DESC);
  CREATE INDEX idx_lb_ss_bat_war ON leaderboard_single_season_batting(war DESC);
  CREATE INDEX idx_lb_ss_bat_league ON leaderboard_single_season_batting(league_id, year);

  COMMENT ON MATERIALIZED VIEW leaderboard_single_season_batting IS 'Single-season batting records with active status indicator';

  -- Single-Season Pitching Records (all players, with active status)
  CREATE MATERIALIZED VIEW leaderboard_single_season_pitching AS
  SELECT
      s.player_id,
      p.first_name,
      p.last_name,
      s.year,
      s.league_id,
      l.abbr as league_abbr,
      s.team_id,
      t.abbr as team_abbr,
      s.w,
      s.l,
      s.g,
      s.gs,
      s.cg,
      s.sho,
      s.sv,
      s.ip,
      s.h,
      s.er,
      s.bb,
      s.so,
      -- Calculated stats
      CASE WHEN s.ip > 0 THEN ROUND((s.er * 9.0) / s.ip, 2) ELSE 0 END as era,
      CASE WHEN s.ip > 0 THEN ROUND((s.bb + s.h) / s.ip, 2) ELSE 0 END as whip,
      CASE WHEN s.ip > 0 THEN ROUND((s.so * 9.0) / s.ip, 2) ELSE 0 END as k_per_9,
      s.war,
      -- Active status flag
      COALESCE(ps.retired, 1) = 0 as is_active
  FROM players_career_pitching_stats s
  INNER JOIN players_core p ON s.player_id = p.player_id
  LEFT JOIN players_current_status ps ON s.player_id = ps.player_id
  LEFT JOIN leagues l ON s.league_id = l.league_id
  LEFT JOIN teams t ON s.team_id = t.team_id
  WHERE s.split_id = 1  -- Only regular season stats
    AND s.ip >= 50;     -- Minimum IP threshold for meaningful stats

  -- Indexes for fast lookups
  CREATE INDEX idx_lb_ss_pit_year ON leaderboard_single_season_pitching(year DESC);
  CREATE INDEX idx_lb_ss_pit_w ON leaderboard_single_season_pitching(w DESC);
  CREATE INDEX idx_lb_ss_pit_so ON leaderboard_single_season_pitching(so DESC);
  CREATE INDEX idx_lb_ss_pit_era ON leaderboard_single_season_pitching(era ASC);
  CREATE INDEX idx_lb_ss_pit_war ON leaderboard_single_season_pitching(war DESC);
  CREATE INDEX idx_lb_ss_pit_league ON leaderboard_single_season_pitching(league_id, year);

  COMMENT ON MATERIALIZED VIEW leaderboard_single_season_pitching IS 'Single-season pitching records with active status indicator';

  -- =====================================================
  -- Yearly League Leaders (Top 10 per year/league)
  -- =====================================================

  -- Yearly Batting Leaders by League
  CREATE MATERIALIZED VIEW leaderboard_yearly_batting AS
  WITH ranked_stats AS (
      SELECT
          s.player_id,
          p.first_name,
          p.last_name,
          s.year,
          s.league_id,
          l.abbr as league_abbr,
          s.hr,
          s.rbi,
          s.sb,
          s.h,
          CASE WHEN s.ab >= 300 AND s.ab > 0
               THEN ROUND(s.h::NUMERIC / s.ab::NUMERIC, 3)
               ELSE NULL END as avg,
          s.war,
          COALESCE(ps.retired, 1) = 0 as is_active,
          -- Rank by each stat
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id ORDER BY s.hr DESC) as hr_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id ORDER BY s.rbi DESC) as rbi_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id ORDER BY s.sb DESC) as sb_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id ORDER BY s.h DESC) as h_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id
                            ORDER BY CASE WHEN s.ab >= 300 AND s.ab > 0
                                          THEN s.h::NUMERIC / s.ab::NUMERIC
                                          ELSE 0 END DESC) as avg_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id ORDER BY s.war DESC) as war_rank
      FROM players_career_batting_stats s
      INNER JOIN players_core p ON s.player_id = p.player_id
      LEFT JOIN players_current_status ps ON s.player_id = ps.player_id
      LEFT JOIN leagues l ON s.league_id = l.league_id
      WHERE s.split_id = 1
        AND s.pa >= 100
  )
  SELECT * FROM ranked_stats
  WHERE hr_rank <= 10
     OR rbi_rank <= 10
     OR sb_rank <= 10
     OR h_rank <= 10
     OR avg_rank <= 10
     OR war_rank <= 10;

  CREATE INDEX idx_lb_yearly_bat_year_league ON leaderboard_yearly_batting(year, league_id);
  CREATE INDEX idx_lb_yearly_bat_hr_rank ON leaderboard_yearly_batting(year, league_id, hr_rank);
  CREATE INDEX idx_lb_yearly_bat_avg_rank ON leaderboard_yearly_batting(year, league_id, avg_rank);

  COMMENT ON MATERIALIZED VIEW leaderboard_yearly_batting IS 'Top 10 batting leaders per year/league for key statistics';

  -- Yearly Pitching Leaders by League
  CREATE MATERIALIZED VIEW leaderboard_yearly_pitching AS
  WITH ranked_stats AS (
      SELECT
          s.player_id,
          p.first_name,
          p.last_name,
          s.year,
          s.league_id,
          l.abbr as league_abbr,
          s.w,
          s.sv,
          s.so,
          CASE WHEN s.ip >= 100 THEN ROUND((s.er * 9.0) / s.ip, 2) ELSE NULL END as era,
          CASE WHEN s.ip >= 100 THEN ROUND((s.bb + s.h) / s.ip, 2) ELSE NULL END as whip,
          s.war,
          COALESCE(ps.retired, 1) = 0 as is_active,
          -- Rank by each stat
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id ORDER BY s.w DESC) as w_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id ORDER BY s.sv DESC) as sv_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id ORDER BY s.so DESC) as so_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id
                            ORDER BY CASE WHEN s.ip >= 100
                                          THEN (s.er * 9.0) / s.ip
                                          ELSE 999 END ASC) as era_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id
                            ORDER BY CASE WHEN s.ip >= 100
                                          THEN (s.bb + s.h) / s.ip
                                          ELSE 999 END ASC) as whip_rank,
          ROW_NUMBER() OVER (PARTITION BY s.year, s.league_id ORDER BY s.war DESC) as war_rank
      FROM players_career_pitching_stats s
      INNER JOIN players_core p ON s.player_id = p.player_id
      LEFT JOIN players_current_status ps ON s.player_id = ps.player_id
      LEFT JOIN leagues l ON s.league_id = l.league_id
      WHERE s.split_id = 1
        AND s.ip >= 50
  )
  SELECT * FROM ranked_stats
  WHERE w_rank <= 10
     OR sv_rank <= 10
     OR so_rank <= 10
     OR era_rank <= 10
     OR whip_rank <= 10
     OR war_rank <= 10;

  CREATE INDEX idx_lb_yearly_pit_year_league ON leaderboard_yearly_pitching(year, league_id);
  CREATE INDEX idx_lb_yearly_pit_w_rank ON leaderboard_yearly_pitching(year, league_id, w_rank);
  CREATE INDEX idx_lb_yearly_pit_era_rank ON leaderboard_yearly_pitching(year, league_id, era_rank);

  COMMENT ON MATERIALIZED VIEW leaderboard_yearly_pitching IS 'Top 10 pitching leaders per year/league for key statistics';

  -- Analyze all views for query optimization
  ANALYZE leaderboard_career_batting;
  ANALYZE leaderboard_career_pitching;
  ANALYZE leaderboard_single_season_batting;
  ANALYZE leaderboard_single_season_pitching;
  ANALYZE leaderboard_yearly_batting;
  ANALYZE leaderboard_yearly_pitching;

│   │   ├── leaderboards.py
│   │   ├── newspaper.py
│   │   └── search.py
│   ├── services/            # Business logic layer
│   │   ├── __init__.py
│   │   ├── player_service.py
│   │   ├── team_service.py
│   │   ├── stats_service.py
│   │   ├── leaderboard_service.py
│   │   └── search_service.py
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   ├── components/      # Reusable template partials
│   │   ├── players/
│   │   ├── teams/
│   │   ├── leaderboards/
│   │   └── newspaper/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── images/          # Static assets
│   │   ├── player_images/   # Symlink to ETL images
│   │   ├── team_logos/
│   │   └── league_logos/
│   └── utils/
│       ├── __init__.py
│       ├── cache.py         # Flask-Caching utilities
│       └── formatters.py    # Template filters
├── migrations/              # Alembic migrations
├── tests/
├── run.py                   # Application entry point
└── requirements.txt
```

**✅ Task 1.2.1: Core Flask Setup** (COMPLETE)
- ✅ Created `web/requirements.txt` with all dependencies
- ✅ Created `web/app/__init__.py` with app factory pattern
- ✅ Created `web/app/config.py` with environment-based configs
- ✅ Created `web/app/extensions.py` for Flask extensions
- ✅ Created `web/run.py` as application entry point
- ✅ Configured database connection (reuses ETL connection settings)
- ✅ Set up Flask-Caching (SimpleCache for dev, Redis for prod)
- ✅ Configured loguru logging (consistent with ETL)
- ⏳ Decision: Separate requirements files for ETL and web (not consolidated)
- ⏳ Decision: Using relative imports in app package

**⏳ Task 1.2.2: SQLAlchemy Models** (IN PROGRESS - 60% complete)
- ✅ Created `web/app/models/base.py` with BaseModel class
- ✅ Created `web/app/models/player.py` (PlayerCore, PlayerCurrentStatus, PersonImage)
- ✅ Created `web/app/models/stats.py` (PlayerCareerBattingStats, PlayerCareerPitchingStats)
- ✅ Created `web/app/models/__init__.py` to export models
- ⏳ Need: `web/app/models/team.py` (Team, League, City models) - PENDING
- ⏳ Need: `web/app/models/newspaper.py` (Article, Category models) - PENDING
- ✅ Established relationships between models
- ✅ Added computed properties (full_name, age, height_display, avg, obp, slg, era, whip)

---

## Phase 2: Reference Website - Core Features (3-4 weeks)

### 2.1 Layout & Navigation

**Task 2.1.1: Base Template**
- Create responsive base template with Tailwind CSS
- Header with navigation: Players | Teams | Seasons | Leaderboards | Newspaper
- Search bar in header (HTMX-powered autocomplete)
- Footer with basic info
- Responsive breakpoints: mobile (640px), tablet (768px), desktop (1024px+)

**Task 2.1.2: Search Functionality**
- HTMX endpoint: `/api/search/autocomplete`
- Searches players (name), teams (name/nickname/abbr)
- Returns JSON with category separators
- Keyboard navigation support (up/down arrows, enter)
- Debounced input (300ms delay)

### 2.2 Home Page

**Task 2.2.1: Left Column**
- 3x6 grid of random player images (cached for 5 minutes)
- Service layer: `get_random_players(count=18)`
- Notable rookies widget (top 10 WAR for first-year players at highest level)
- "Born this week" widget (±7 days from current game date)

**Task 2.2.2: Right Column**
- Current standings by league/division
- Service: `get_current_standings(league_id=None)` - returns all if None
- Links to league summary pages
- Links to leaderboards by league

**Caching Strategy:**
- Home page: Cache for 1 hour (updates once per game day)
- Random players: Cache for 5 minutes (different each visit but not each load)
- Standings: Cache for 1 hour
- Cache key includes current game date

### 2.3 Player Pages

**Task 2.3.1: Player Home Page**
- A-Z alphabet navigation
- Each letter shows 10 notable players (by career WAR)
- Click letter → full list page with all players starting with that letter
- Service: `get_players_by_letter(letter, notable_only=True, limit=10)`

**Task 2.3.2: Individual Player Page**
- URL pattern: `/players/<player_id>` or `/players/<slug>` (e.g., `/players/john-smith-1234`)
- Layout:
  - Top left: Player image
  - Top right: Bio data (name, position, bats/throws, height/weight, birth date/place, school)
  - Career stats table (yearly breakdown) - batting, pitching, fielding
  - Leaderboard appearances section
  - Similarity scores (if calculated)
- Performance considerations:
  - Player page cache: 24 hours
  - Lazy-load historical stats (HTMX accordion)

**Task 2.3.3: Player Stats Display**
- Separate tables for batting/pitching/fielding
- Highlight career-best seasons
- Team abbreviations linked to team pages
- Year linked to team-year pages
- Advanced stats in collapsible section (HTMX toggle)

### 2.4 Team Pages

**Task 2.4.1: Team Home Page**
- URL: `/teams/<team_id>`
- Team logo (top left)
- Franchise history: names, W-L record, playoff count, championships
- 2x12 grid of top players by WAR
- Franchise stats by year table
- Links to organizational leaderboards

**Task 2.4.2: Team-Year Page**
- URL: `/teams/<team_id>/<year>`
- Team logo, year navigation (prev/next)
- 12 top players for that season (images)
- Roster batting stats table
- Roster pitching stats table
- Cache: 24 hours (historical years never change)

### 2.5 Leaderboards (CRITICAL - PERFORMANCE FOCUS)

**Task 2.5.1: Database Optimization**

Create materialized views for common leaderboard queries:

```sql
-- Career leaderboards (all players with active status indicator)
CREATE MATERIALIZED VIEW leaderboard_career_batting AS
SELECT
    s.player_id,
    SUM(s.hr) as hr,
    SUM(s.rbi) as rbi,
    -- Include other aggregated stats...
    COALESCE(p.retired, 1) = 0 as is_active  -- Flag for active players
FROM players_career_batting_stats s
LEFT JOIN players_current_status p ON s.player_id = p.player_id
GROUP BY s.player_id, p.retired;

-- Single-season records (all players with active status indicator)
CREATE MATERIALIZED VIEW leaderboard_single_season_batting AS
SELECT
    s.player_id,
    s.year,
    s.hr,
    -- Include other stats...
    COALESCE(p.retired, 1) = 0 as is_active
FROM players_career_batting_stats s
LEFT JOIN players_current_status p ON s.player_id = p.player_id
ORDER BY s.hr DESC
LIMIT 500;

-- Yearly league leaders
CREATE MATERIALIZED VIEW leaderboard_yearly_league_batting AS
SELECT year, league_id, stat_type, player_id, stat_value, is_active
FROM (
  SELECT
    s.*,
    COALESCE(p.retired, 1) = 0 as is_active,
    ROW_NUMBER() OVER (PARTITION BY year, league_id, stat_type ORDER BY stat_value DESC) as rn
  FROM batting_stats_pivot s
  LEFT JOIN players_current_status p ON s.player_id = p.player_id
) sub WHERE rn <= 10;
```

**Refresh Strategy:**
- Materialized views refresh: After each ETL run
- Add refresh function to ETL pipeline
- Manual refresh endpoint: `/admin/refresh-leaderboards` (for development)

**Task 2.5.2: Leaderboard Home Page**
- URL: `/leaderboards`
- Current year leaders (all leagues, key stats)
- Links to detailed leaderboards by type
- Links to historical leaderboards (past 10 years)

**Task 2.5.3: Leaderboard Detail Pages**
- URL patterns:
  - `/leaderboards/batting/career`
  - `/leaderboards/batting/single-season`
  - `/leaderboards/batting/progressive`
  - `/leaderboards/batting/yearly/<year>`
  - `/leaderboards/batting/top-tens`
- Filter controls (HTMX):
  - Active/Retired/All filter (shows all by default with asterisk for active players)
  - League filter
  - Year range filter (for applicable views)
  - Stat selector
- Display: Active players marked with asterisk (*) after name
- Pagination: 50 results per page
- Cache: 6 hours (leaderboards don't change frequently)

**Task 2.5.4: Year-by-Year Top Tens**
- Grid layout: 4 columns (years)
- Each cell: Top player + value
- "Show #2-10" link (HTMX toggle to expand)
- Expanded view shows players 2-10 inline

**Task 2.5.5: Progressive Leaderboards**
- Table with columns: Year | Career Leader | Value | Single-Season Leader | Value | Active Leader | Value | Yearly Leader | Value
- Shows progression over time (e.g., who held the all-time record in each year)
- Active players in current year marked with asterisk (*)
- "Active Leader" column shows the career leader among only active players at that time
- Complex query - cache aggressively (24 hours)

---

## Phase 3: Newspaper & Content Management (2-3 weeks)

### 3.1 Newspaper Article Database

**Task 3.1.1: Article Schema**

```sql
CREATE TABLE newspaper_articles (
    article_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    category_id INTEGER REFERENCES article_categories(category_id),
    author_type VARCHAR(20) DEFAULT 'user', -- 'user' or 'ai'
    game_date DATE,  -- In-game date of article
    publish_date TIMESTAMP DEFAULT NOW(),
    is_published BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE article_categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE article_player_tags (
    article_id INTEGER REFERENCES newspaper_articles(article_id),
    player_id INTEGER REFERENCES players_core(player_id),
    PRIMARY KEY (article_id, player_id)
);

CREATE TABLE article_team_tags (
    article_id INTEGER REFERENCES newspaper_articles(article_id),
    team_id INTEGER REFERENCES teams(team_id),
    PRIMARY KEY (article_id, team_id)
);

CREATE TABLE article_game_tags (
    article_id INTEGER REFERENCES newspaper_articles(article_id),
    game_id INTEGER,
    PRIMARY KEY (article_id, game_id)
);
```

### 3.2 Rich Text Editor

**Task 3.2.1: Editor Integration**
- Use **TinyMCE** (CDN version to start, self-hosted later)
- Configure toolbar: heading styles, bold, italic, link, image, lists
- Custom plugin: "Insert Reference Link"
  - Modal search for players/teams
  - Inserts properly formatted link: `<a href="/players/123">John Smith</a>`
- Auto-save drafts to localStorage every 30 seconds

**Task 3.2.2: Article Editor Page**
- URL: `/newspaper/editor/new` or `/newspaper/editor/<article_id>`
- Form fields:
  - Title (required)
  - Category dropdown (required)
  - Game date picker (defaults to current game date)
  - Content (TinyMCE editor)
  - Auto-generated excerpt (first 200 chars, editable)
  - Tag selectors (HTMX autocomplete for players/teams/games)
  - Featured checkbox
  - Publish checkbox
- Preview mode (HTMX): Render article in newspaper template
- Save draft vs Publish actions

**Task 3.2.3: Article List & Management**
- URL: `/newspaper/admin`
- Table of all articles: title, category, author type, game date, publish status
- Filter by category, publish status, date range
- Quick actions: Edit, Delete, Toggle publish, Toggle feature
- HTMX-powered for quick updates

**Task 3.2.4: Article Tagging Strategy**

**Phased Approach to Auto-Tagging:**

*Phase 1: Manual + Auto-Suggest (Initial Implementation)*
- Article editor includes autocomplete search for player/team tags
- Python `ArticleTaggerService` analyzes content and suggests entity tags:
  - Scans for player names using regex + database lookup
  - Scans for team names/nicknames from teams table
  - Returns suggestions with confidence scores
- Web editor displays tag suggestions as removable chips
- User accepts/rejects suggestions before publishing
- Manual tagging remains primary method for user control

*Phase 2: AI Auto-Tagging (Future Enhancement)*
- Differentiate behavior by `author_type`:
  - **AI-generated articles**: Auto-apply tags with confidence > 0.8
  - **User-written articles**: Suggest only, user confirms
- Add optional columns to tag tables for future use:
  - `confidence DECIMAL(3,2) DEFAULT 1.00`
  - `auto_tagged BOOLEAN DEFAULT FALSE`
  - `reviewed BOOLEAN DEFAULT FALSE`

*Phase 3: Background Enhancement (Long-term)*
- Cron job or post-ETL process to re-analyze existing articles
- Suggest additional tags for user review
- Consider LLM API integration for improved entity extraction

**Implementation Notes:**
- **Name Ambiguity**: Common names (e.g., "John Smith") may match multiple players - require manual selection
- **False Positives**: Team names in non-baseball context filtered by checking surrounding keywords
- **Performance**: Suggestion service called via debounced HTMX request (300ms delay)
- **Service Location**: `app/services/article_tagger_service.py`

**Service Methods:**
```python
ArticleTaggerService.suggest_tags(content: str) -> List[TagSuggestion]
ArticleTaggerService.auto_tag_article(article_id: int, threshold: float = 0.8)
ArticleTaggerService.find_player_mentions(content: str) -> List[PlayerMatch]
ArticleTaggerService.find_team_mentions(content: str) -> List[TeamMatch]
```

### 3.3 Newspaper Front-End

**Task 3.3.1: Newspaper Home**
- URL: `/newspaper`
- Featured article (large card with image if available)
- Recent articles (reverse chronological)
- Category navigation sidebar
- Filter by Branch family articles
- Pagination: 20 articles per page

**Task 3.3.2: Article Display Page**
- URL: `/newspaper/<slug>`
- Full article with proper typography
- Metadata: category, game date, author type
- Related articles (same category or tagged players/teams)
- Tagged players/teams displayed as chips with links
- Next/Previous article navigation

**Task 3.3.3: Category Pages**
- URL: `/newspaper/category/<slug>`
- Filtered list of articles by category
- Same layout as newspaper home

---

## Phase 4: Image Management & Assets (1 week)

### 4.1 Player Images

**Current State:** ETL already handling player images in `person_images` table

**Task 4.1.1: Symlink or Copy**
- Decision: Create symlink from `/web/app/static/player_images/` to ETL output directory
- Fallback image for players without photos
- Lazy loading images (native `loading="lazy"`)

**Task 4.1.2: Image Service**
- Route: `/images/player/<player_id>`
- Checks `person_images` table
- Returns image or fallback
- Add caching headers (1 year for player images)

### 4.2 Team & League Logos

**Task 4.2.1: Logo Management Table**

```sql
CREATE TABLE team_logos (
    team_id INTEGER PRIMARY KEY REFERENCES teams(team_id),
    logo_filename VARCHAR(255) NOT NULL,
    logo_path VARCHAR(500),
    upload_date TIMESTAMP DEFAULT NOW()
);

CREATE TABLE league_logos (
    league_id INTEGER PRIMARY KEY REFERENCES leagues(league_id),
    logo_filename VARCHAR(255) NOT NULL,
    logo_path VARCHAR(500),
    upload_date TIMESTAMP DEFAULT NOW()
);
```

**Task 4.2.2: Logo Upload Interface**
- Simple admin page: `/admin/logos`
- Upload form for team/league logos
- Stores in `/web/app/static/team_logos/` and `/web/app/static/league_logos/`
- Updates database with filename and path

**Task 4.2.3: Logo Display**
- Template helper: `{{ team_logo(team_id) }}`
- Returns `<img>` tag with proper path or fallback
- CSS: consistent sizing (e.g., 50x50px for thumbnails, 150x150px for headers)

---

## Phase 5: Performance Optimization (1 week)

### 5.1 Caching Strategy

**Multi-Level Caching:**

1. **Flask-Caching (Redis or Simple)**
   - Page caching: Home, player pages, team pages
   - Fragment caching: Leaderboards, standings widgets
   - Query caching: Expensive database queries

2. **Database-Level:**
   - Materialized views for leaderboards
   - Indexed columns for search
   - Query optimization (EXPLAIN ANALYZE)

3. **HTTP Caching:**
   - Static assets: 1 year cache
   - Player images: 1 year cache
   - API responses: ETags for conditional requests

**Task 5.1.1: Implement Redis Caching**
- Install Redis (Docker container on Minotaur)
- Configure Flask-Caching with Redis backend
- Add cache decorators to expensive routes
- Cache key strategy includes current game date

**Task 5.1.2: Cache Invalidation**
- After ETL runs: Invalidate leaderboard caches
- When article published: Invalidate newspaper home cache
- Admin endpoint: `/admin/clear-cache/<cache_type>`

### 5.2 Database Indexes

**Task 5.2.1: Add Missing Indexes**

```sql
-- Full-text search
CREATE INDEX idx_player_search ON players_core USING GIN(
    to_tsvector('english', first_name || ' ' || last_name)
);

CREATE INDEX idx_team_search ON teams USING GIN(
    to_tsvector('english', name || ' ' || nickname || ' ' || abbr)
);

-- Leaderboard queries
CREATE INDEX idx_batting_stats_year_league ON players_career_batting_stats(year, league_id, split_id);
CREATE INDEX idx_batting_stats_war ON players_career_batting_stats(war DESC) WHERE war IS NOT NULL;
CREATE INDEX idx_batting_stats_hr ON players_career_batting_stats(hr DESC);

-- Similar for pitching stats
```

**Task 5.2.2: Query Optimization**
- Run EXPLAIN ANALYZE on slow queries
- Add composite indexes where needed
- Use LIMIT on leaderboard queries
- Optimize JOIN operations

### 5.3 HTMX Optimization

**Task 5.3.1: Strategic HTMX Usage**
- Search autocomplete: `hx-get="/api/search?q={value}"` with debounce
- Leaderboard filters: `hx-get` with query params, swap table body
- Expandable sections: `hx-get` on click, swap content
- Infinite scroll: `hx-get` next page, append to list

**Task 5.3.2: Loading States**
- Add `hx-indicator` for loading spinners
- Skeleton screens for slow-loading content
- Optimistic UI updates where appropriate

---

## Phase 6: Deployment & DevOps (1 week)

### 6.1 Containerization

**Task 6.1.1: Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web/ .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

**Task 6.1.2: Docker Compose**

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@192.168.10.94:5432/ootp
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - /path/to/player_images:/app/static/player_images:ro
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### 6.2 Caddy Integration

**Task 6.2.1: Caddy Configuration**

Add to existing Caddy container on Minotaur:

```
rb2.local {
    reverse_proxy web:5000
    encode gzip

    # Cache static assets
    @static {
        path /static/*
    }
    header @static Cache-Control "public, max-age=31536000"
}
```

### 6.3 ETL Integration

**Task 6.3.1: Post-ETL Hook**
- Add webhook to ETL completion
- Triggers cache invalidation in web app
- Refreshes materialized views
- Updates game state table

---

## Technology Stack Summary

### Core Dependencies

```python
# Web Framework
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Caching==2.1.0
Flask-HTMX==0.3.2

# Database
psycopg2-binary==2.9.9
alembic==1.13.0

# Server
gunicorn==21.2.0

# Caching
redis==5.0.1

# Utilities
python-slugify==8.0.1
```

### Frontend Stack

- **CSS Framework**: Tailwind CSS
- **JavaScript**: Vanilla JS + HTMX for interactivity
- **Rich Text Editor**: TinyMCE (for newspaper articles)
- **Icons**: Optional - Font Awesome or Heroicons

---

## Gaps & Missing Components Summary

### Database Gaps

1. **Search Infrastructure**: Full-text indexes, search optimization
2. **Leaderboard Performance**: Materialized views, pre-aggregated stats
3. **Image Management**: Logo tables and file path tracking
4. **Newspaper Schema**: Article tables, categories, tags
5. **Game State**: Current game date tracking table
6. **Player Similarity**: Calculation and storage

### ETL Gaps

1. **Logo Import**: No current process for team/league logos
2. **Materialized View Refresh**: Need post-ETL job to refresh views
3. **Game Date Tracking**: Update game state table after each ETL run

### Application Gaps

1. **No web framework**: Entire Flask app needs to be built
2. **No caching layer**: Redis setup and Flask-Caching integration
3. **No search service**: Full-text search implementation
4. **No admin interface**: Article editor, logo uploader, cache management

---

## Priority Order

### High Priority (Core Functionality)
- Database extensions (search, leaderboards)
- Flask setup and basic routing
- Player/Team pages (most visited)
- Search functionality

### Medium Priority (Enhanced Features)
- Leaderboards (complex but essential)
- Home page widgets
- Newspaper article display

### Lower Priority (Can be phased in)
- Newspaper editor
- Logo management admin
- Player similarity scores
- Progressive leaderboards

---

## Next Steps

### Immediate Actions (Week 1)

1. **Create database extensions:**
   - Write SQL for web support tables
   - Write SQL for newspaper tables
   - Add search indexes
   - Create initial materialized views

2. **Set up Flask project structure:**
   - Initialize Flask app
   - Configure SQLAlchemy
   - Set up project structure
   - Install dependencies

3. **Establish Redis caching:**
   - Deploy Redis container on Minotaur
   - Configure Flask-Caching
   - Test basic caching
