# RB2 Website Specifications
This document contains the specifications for the reference website portion of the RB2 project.

RB2 will have a single website with 2 distinct parts: A reference website and a newspaper/journal.

The two parts will be almost completely independent of each other. Users will visit the reference website to browse
current and historical statistics and leaderboards. The newspaper will contain narrative prose about league events in
general and about the Branch family in particular. Data for these events will come from game logs, box scores, and the
messages file, which are exported from the game.

## Technology Stack
This website will use data from a PostgreSQL database, and it will be served by Flask (Python framework). **[COMPLETED]**
The UI is built with Tailwind CSS via CDN for rapid development. **[COMPLETED]**

## Development Environment
### Development Computers
Coding will be done on either a MacBook Pro or a Pop-OS desktop, both using Pycharm Professional as an IDE.
### Database
The dev database is located in a Docker container on a small server on the local network.
Hostname: `Minotaur`
IP: 192.168.10.94
Container name: `ootp-postgres`
**Ask the user to run queries for you**
### Serving
Reverse Proxy: Minotaur hosts a few small websites in production. It uses Caddy in a docker container called "hosting-caddy-1".
### Virtual Environment for Dev
The virtual environment is located at ~/virtual-envs/rb2

---

## Reference website specifications

### Overview
The reference website will be similar to [baseball-reference.com](http://www.baseball-reference.com). It will serve
statistics at the League, Team, and Player levels. It will have a front page and templates for the following page types:
- Player **[COMPLETED]**
- Coaches/Staff [NOT STARTED]
- League **[NOT STARTED]**
- Team **[IN PROGRESS]** - Basic detail page exists, needs Team Year pages and historical data
- Year **[NOT STARTED]**

Each page will contain hyperlinks to relevant pages. For example, on a Player page, a players statistics will be listed
in table format that includes year, league, and team for each season. Each year, league, and team entry will be linked
to the Year, League, and Team page, respectively. **[IN PROGRESS]** - Player stats link to teams, but Year/League pages don't exist yet.

Player pages will include an image of the player. **[NOT STARTED]** - No image display implemented.
Team pages will include the team logo file. **[NOT STARTED]** - No logo display implemented.
League pages will contain the league logo. **[NOT STARTED]**

There will be a nav header with links for 'Players', 'Teams', 'Seasons', 'Newspaper' **[IN PROGRESS]** - Nav exists but links to 'Leaderboards' instead of 'Seasons', and Newspaper link is missing.

---

### Front Page

**Overall Status: [IN PROGRESS]** - Standings implemented, left column content missing

2-column layout (for desktop). **[NOT STARTED]** - Currently single column, needs 2-column responsive layout.

The left column will include the following:
- 3x6 grid of random player images with links to their player pages. The images will change on every load. **[NOT STARTED]**
- 'Notable rookies': A list of 10 players who 1) are in their first season at the highest league level and 2) are in the top 10 WAR for rookies. These will be linked to their player pages. **[NOT STARTED]**
- 'Born this week': A hyperlinked list of players whose date of birth is within 7 days in either direction of the current game-date. **[NOT STARTED]**

The right column will include the following:
- Current standings for every league. Will include Wins, Losses, Win Percentage, Games Back, and Magic Number. **[IN PROGRESS]** - W, L, PCT, GB implemented; Magic Number missing.
- Links to leaderboards by league **[NOT STARTED]**
- Links to League Summary pages that show: Current Standings (by division and/or sub-league if appropriate), Team Batting and Pitching stats. **[NOT STARTED]**

#### Implementation Status - Front Page

**Missing UI Components:**
- Two-column responsive layout component (mobile-first approach)
- Player image grid component (3x6 grid with random selection logic)
- Notable rookies list component
- "Born this week" player list component
- League leaderboard links section
- League summary cards/links
- Magic Number column in standings tables

**Approach:**
- Create reusable card components for different content sections (rookies, birthdays, etc.)
- Implement responsive grid system that collapses to single column on mobile
- Build image grid with proper loading states and fallback for missing images
- Design sidebar widget pattern for reusable content blocks (rookies, birthdays can share similar styling)
- Add interactive hover states and smooth transitions

**Implementation Priority:**
- **HIGH**: Two-column layout structure (foundation for all other work)
- **HIGH**: Notable rookies component (high user value, drives engagement)
- **MEDIUM**: Player image grid (visual appeal but requires image assets)
- **MEDIUM**: "Born this week" component (nice-to-have feature)
- **MEDIUM**: League leaderboard links
- **LOW**: Magic Number in standings (low season relevance depending on timing)

**Dependencies:**
- Need player image assets/URLs in database
- Reusable standings table component (already exists, can extend)
- Reusable player list component (can be used across multiple pages)
- Date utility functions for "born this week" calculations

---

### Leaderboards

**Overall Status: [NOT STARTED]** - Routes exist as placeholders, no templates or functionality

Hovering over the Leaderboard link in the header will expose links for the following: **[NOT STARTED]** - Dropdown navigation not implemented
- League Batting Leaders for each league, with links to the leaderboard pages for the most recent 10 years. **[NOT STARTED]**
- League Pitching Leaders for each league, with links to the leaderboard pages for the most recent 10 years. **[NOT STARTED]**
- Same as above for Sub-Leagues, if applicable. **[NOT STARTED]**
- Leaderboards for the following stats, each presented with links to: **[NOT STARTED]**
    - Active
    - Single-Season
    - Progressive
    - Year-by-year Top-Tens
    - Career
    - Yearly League
  - W
  - SB
  - SV
  - WAR
  - WHIP
  - HR
  - SO/W
  - SO
  - OPS+
  - BA
  - RBI

#### Leaderboard Home
Clicking on the Leaderboard header link will navigate to Leaderboard Home. **[NOT STARTED]**
There will be an H1 header: "Overall Baseball Leaders & Baseball Records" **[NOT STARTED]**
Beneath the header will be "$Year Leaders", followed by links to Batting and Pitching Leaders for each league. **[NOT STARTED]**
Beneath that will be a 3-column (6 columns if you count statistic and player as separate columns) table for the current leaders across all leagues
for important statistics across all leagues. The format will be: $Statistic    $Player_Name $team_abbr ($value) **[NOT STARTED]**

Beneath this will be "All-Time Career and Single-Season Records and Leaders". Each row will be for a different statistic.
Each column will be a link to a leaderboard. The columns are: **[NOT STARTED]**
- Single-Season
- Career
- Active
- Progressive
- Yearly League
- Year-by-Year Top Tens

#### Year-by-Year Top Tens
The format for this type of leaderboard will be a table 4-columns wide. Each cell shall represent one year. The top player
for that year for that statistic shall be displayed in the cell, alongside the value for that stat. A link titled
"Show #2-10" shall be displayed directly beneath the value. Clicking that link will expand that row to show the players
with the 2nd through 10th best values for that stat. **[NOT STARTED]**

#### Progressive
This may be difficult to implement with our data structure.
Progressive leaderboard is a table where each row represents a year. The columns are: **[NOT STARTED]**
- Year
- Career
- $Statistic
- Single-Season
- $Statistic
- Active
- $Statistic
- Yearly
- $Statistic

The intention is to show, as of every year, who career, single season, active, and leader for that season are.

#### Implementation Status - Leaderboards

**Missing UI Components:**
- Mega dropdown menu component for navigation (multi-level, responsive)
- Leaderboard home page template
- Current year leaders grid (3-column layout)
- All-time records table with stat category navigation
- Individual stat leaderboard templates (Career, Single-Season, Active, etc.)
- Year-by-Year Top Tens expandable grid component
- Progressive leaderboard table component
- Sortable table headers component
- Filter/year selector components
- League/sub-league filter tabs

**Approach:**
- Build a mega-menu dropdown component with hover behavior (desktop) and click behavior (mobile)
- Create a base leaderboard table component that can be configured for different stat types
- Implement expandable/collapsible rows for Year-by-Year Top Tens (JavaScript accordion pattern)
- Design tabbed interface for switching between leaderboard types (Career, Single-Season, etc.)
- Use sticky table headers for long leaderboards
- Implement client-side sorting for small datasets, server-side for large ones
- Create filter chips/tags UI for selected criteria

**Implementation Priority:**
- **HIGH**: Leaderboard Home page (main entry point, sets the tone)
- **HIGH**: Current year leaders grid (timely, engaging content)
- **HIGH**: Career and Single-Season leaderboards (most commonly used)
- **MEDIUM**: Mega dropdown navigation (improves discoverability but not critical for initial launch)
- **MEDIUM**: Active leaders (subset of career)
- **MEDIUM**: Yearly League leaders
- **LOW**: Progressive leaderboards (complex, lower user demand)
- **LOW**: Year-by-Year Top Tens (nice-to-have, requires interaction complexity)

**Dependencies:**
- Reusable sortable table component
- Dropdown menu component for navigation
- Tab component for switching between leaderboard types
- Accordion/expansion component for Top Tens
- Shared filter UI components
- Base leaderboard layout that all stat pages extend

---

### Players

#### Players Home Page
The Players Home Page shall feature a row for every letter of the alphabet. Immediately beneath the letter shall be links to
the player pages for 10 notable players (based on career WAR?) whose last names begin with that letter. **[COMPLETED]**
Clicking on the letter itself takes you to a page with a list of every player whose last name begins with that letter along with their
years of service in parentheses. Each player on a different row. **[COMPLETED]**

#### Players Pages
The player's image will be top left. **[NOT STARTED]** - No image display implemented.
Aligned roughly against the player image shall be the following data from players_core: name, position, bats and throws,
height and weight, birth date and place (city, state, country), school. **[IN PROGRESS]** - Most bio data displayed, missing school field.

**Yearly Statistics Tables:** **[NOT STARTED]**
Beneath the bio section will be the player's statistics by year. These will be presented in table format with one row per season:

**Batting Statistics Table** (for position players):
- Columns: Year (linked to Team Year page), Age, Team (linked to Team page), League (linked to League page), G, PA, AB, R, H, 2B, 3B, HR, RBI, SB, CS, BB, SO, BA, OBP, SLG, OPS, OPS+, TB, GDP, HBP, SH, SF, IBB, WAR
- Career totals row at the bottom
- Sortable by any column
- Highlight rows for playoff seasons or award-winning seasons

**Pitching Statistics Table** (for pitchers, or position players with pitching appearances):
- Columns: Year (linked to Team Year page), Age, Team (linked to Team page), League (linked to League page), W, L, ERA, G, GS, GF, CG, SHO, SV, IP, H, R, ER, HR, BB, IBB, SO, HBP, BK, WP, BF, ERA+, FIP, WHIP, H9, HR9, BB9, SO9, SO/W, WAR
- Career totals row at the bottom
- Sortable by any column
- Highlight rows for playoff seasons or award-winning seasons

**Fielding Statistics Table** (if fielding stats are available):
- Columns: Year, Age, Team, League, Pos, G, GS, Inn, PO, A, E, DP, Fld%, RF/9, RF/G
- Career totals by position
- Sortable by any column

If we are able to capture the player's history, we will include items from the player's general history beneath. **[NOT STARTED]**
We will include a section of appearances on leaderboards beneath the history. **[NOT STARTED]**
Finally, we will have a section for Similarity Scores. **[NOT STARTED]**

#### Similarity Scores
We will follow as closely as we can Bill James's Similarity Scores. We can look up the formula if we have to. We will
have one column of similar players for the entire career and one on similarity by age. **[NOT STARTED]**

#### Implementation Status - Players

**Missing UI Components:**
- **Yearly Statistics Tables** (CRITICAL - core functionality):
  - Batting stats table with all specified columns
  - Pitching stats table with all specified columns
  - Fielding stats table with all specified columns
  - Career totals row for each table
  - Sortable column headers
  - Row highlighting for special seasons (playoffs, awards)
  - Links from Year/Team/League columns to respective pages
- Player image display component (with fallback for missing images)
- Player history timeline/accordion component
- Leaderboard appearances section
- Similarity scores comparison table
- School field in bio section
- Player awards/honors section (if data available)
- Career highlights callout boxes

**Approach:**
- **Yearly Stats Tables**: Create comprehensive stat table component with:
  - Responsive design (horizontal scroll on mobile for wide tables)
  - Sticky first column (player name/year) for better UX
  - Sortable headers using JavaScript or Alpine.js
  - Conditional rendering (only show batting for position players, pitching for pitchers)
  - Career totals row with distinct styling (bold, background color)
  - Conditional highlighting (gold for championships, light blue for playoffs)
  - Link generation for Year, Team, League columns
  - Proper number formatting (batting average as .xxx, ERA as x.xx)
- Design image component with proper aspect ratio, lazy loading, and fallback placeholder
- Create timeline component for player history events
- Build comparison table for similarity scores (side-by-side player cards)
- Add badge/pill components for leaderboard appearances
- Implement tabbed stats view if tables get too long (batting/pitching/fielding separate tabs)
- Consider adding visual stat charts (career WAR progression, etc.)

**Implementation Priority:**
- **CRITICAL**: Yearly statistics tables (core content, essential feature)
- **HIGH**: Player image display (major visual improvement)
- **MEDIUM**: School field in bio (data completeness)
- **MEDIUM**: Sortable table functionality (usability enhancement)
- **MEDIUM**: Leaderboard appearances (cross-referencing, high user value)
- **LOW**: Player history timeline (depends on data availability)
- **LOW**: Similarity scores (complex calculation, niche feature)
- **LOW**: Visual charts (enhancement, not essential)

**Dependencies:**
- **Backend**: Route must fetch yearly batting/pitching/fielding stats from database
- **Backend**: Calculate player age for each season
- **Backend**: Determine which tables to show (batting/pitching/fielding) based on player position/stats
- Player image assets/URLs in database
- Reusable sortable table component or JavaScript library
- Reusable image component with fallback
- Timeline component (can reuse for other pages)
- Card component for similarity score players
- Badge/pill component for leaderboard references
- Year/Team/League pages must exist for links to work properly

**Backend Requirements for Yearly Stats:**
```python
# In player_detail route, need to query:
# 1. Batting stats by year (from players_career_batting_stats)
career_batting = (PlayerBattingStats.query
    .filter_by(player_id=player_id, split_id=1)  # split_id=1 for overall
    .order_by(PlayerBattingStats.year.desc())
    .all())

# 2. Pitching stats by year (from players_career_pitching_stats)
career_pitching = (PlayerPitchingStats.query
    .filter_by(player_id=player_id, split_id=1)
    .order_by(PlayerPitchingStats.year.desc())
    .all())

# 3. Fielding stats by year (from players_career_fielding_stats)
career_fielding = (PlayerFieldingStats.query
    .filter_by(player_id=player_id)
    .order_by(PlayerFieldingStats.year.desc())
    .all())

# 4. Calculate totals (sum stats, don't include rates like AVG, ERA)
```

---



### Coaches and Staff
All coaches and staff will have pages in the same manner as players have pages.  
-  Coach and staff pages shall have a header section with the coach image in the top left corner. The header section 
shall have the same elements and look and feel as the players header with the following additions:  
    - If `coaches.former_player_id` is not null, then the top right corner of the header shall display the most recent 
   picture of the player with a link to the player's player page.
    - The header shall display the coach's current occupation, team, and experience.
-  The detail section of the coach page shall display the following:
    - Staff Ratings  
        - A color coded bar chart showing the coach's ratings (out of 200) for the following fields. Red for low values
      changing to blue for the highest values. Intermediate colors yellow, orange, green:
            - Manager Value
            - Pitching Coach Value
            - Hitting Coach Value
            - Scout Value
            - Teach Running
            - Teach Hitting
            - Doctor Value
    -  Coach Preferences
       - The scale for preferences is from -5 to 5. Values should be displayed as a marker of some sort on a bar. The 
       color of the bar should correspond the value's distance from 0. Blue for 0-2, Green for 3-4, Red for 5.
       - Fields:  
           - Stealing
           - Running Aggressiveness
           - Use Pinch Runners
           - Use Pinch Hitters
           - Pull Starters
           - Pull Relievers
           - Use Closer
           - Favor L/R Matchups
           - Bunt For Hit
           - Bunt
           - Hit and Run
           - Run and Hit
           - Squeeze
           - Pitch Around Hitters
           - Intentional Walk
           - Hold Runner
           - Guard Lines
           - Infield In
           - Outfield In
           - Corners In
           - Shift Infield
           - Shift Outfield
           - Use Opener
           - Favor Speed to Power
           - Favor Offense to Defense
           - Favor Pitching to Hitting
           - Favor Veterans to Prospects
           - Trade Aggressiveness
           - Player Loyalty
           - Trade Frequency
           - 


### Teams

**Overall Status: [IN PROGRESS]** - Basic current team page exists, missing historical and year-specific pages

Every team will have a Home page and pages for each year. **[IN PROGRESS]** - Home page partially done, year pages missing.

#### Team Home Page
Upper left will be the current team logo. **[NOT STARTED]** - No logo display implemented.
Roughly aligned next to the logo will be the H2 text: $Team_nickname Team History & Encyclopedia. **[IN PROGRESS]** - Title exists but not in exact format specified.
Then, on succeeding lines, former team names, Count of seasons, complete historical w/l records, Count of playoff appearances,
championships. **[NOT STARTED]** - Historical data not displayed.
Beneath that, a 2x12 grid of the franchise's top players by WAR. **[NOT STARTED]**
Beneath that, team statistics for every year of the franchise: league, division, g, w, l, pct, pyth_pct, finish, gb, r, ra, top player, manager. **[NOT STARTED]**
Beneath that, links to organizational leaderboards. **[NOT STARTED]**

#### Team Year Pages
Top left will have the team's logo. **[NOT STARTED]** - Team year pages don't exist yet.
Roughly aligned with the logo: H2: $year $team_name $team_nickname Statistics. **[NOT STARTED]**
On the next line will be links to the previous and next years. **[NOT STARTED]**
Beneath that, images of the 12 top players for that year by WAR. **[NOT STARTED]**
Beneath that a table of batting statistics for every hitter who appeared for the team that season. Beneath that, one for
pitchers. **[NOT STARTED]**

#### Implementation Status - Teams

**Missing UI Components:**
- Team logo display component
- Team history header section (franchise stats, championships, etc.)
- Franchise top players grid (2x12 player cards)
- Year-by-year franchise stats table (scrollable, sortable)
- Organizational leaderboards links section
- Team year page template (complete new page)
- Year navigation component (previous/next year)
- Top players for year image grid (12 players)
- Team batting stats table (season-specific)
- Team pitching stats table (season-specific)

**Approach:**
- Create logo component with proper sizing and fallback
- Design franchise header component with key stats highlighted (championships in gold, etc.)
- Build player card grid component (reusable for top players sections)
- Create comprehensive year-by-year table with highlighting for playoff years
- Implement year navigation with arrow buttons and year dropdown
- Build team season stats tables with player links
- Add breadcrumb navigation (Team Home → Year)

**Implementation Priority:**
- **HIGH**: Team Year pages (major missing functionality)
- **HIGH**: Year navigation component (essential for Team Year pages)
- **HIGH**: Team season stats tables (core content for year pages)
- **MEDIUM**: Team logo display (visual identity)
- **MEDIUM**: Franchise history header (context and credibility)
- **MEDIUM**: Year-by-year franchise table (comprehensive view)
- **MEDIUM**: Top players grid (both for home and year pages)
- **LOW**: Organizational leaderboards (nice-to-have)

**Dependencies:**
- Team logo assets/URLs in database
- Reusable logo component
- Player card grid component (shared with front page)
- Historical team statistics data
- Year-by-year player performance data
- Breadcrumb component
- Year selector/navigation component
- Reusable stat table component (extend existing)

---

## Newspaper

**Overall Status: [NOT STARTED]** - Placeholder route exists, no templates or functionality

The structure and format of this section still needs definition but it will follow these conventions:
- Data will come from one of two sources: written directly by the user or from the database. **[NOT STARTED]**
- The user will occasionally write news stories or journal entries about or from the perspective of a Branch family
member. **[NOT STARTED]**
- The application will generate news stories from exported game data. These stories will have the look and feel of a
newspaper or sports magazine article. **[NOT STARTED]**

#### Implementation Status - Newspaper

**Missing UI Components:**
- Newspaper home page template
- Article listing page (chronological feed)
- Article detail page template
- Article authoring/editing interface (if user-generated)
- Newspaper-style typography and layout
- Article categories/tags navigation
- Search/filter for articles
- Article card component for listings

**Approach:**
- Design newspaper-style layout with classic typography (serif fonts, column layouts)
- Create article templates with different styles (news story, feature, journal entry)
- Build article listing with card-based or list-based layout
- Implement rich text display for article content
- Add metadata display (date, author, category)
- Consider timeline view for chronological browsing
- Design print-friendly styles for articles

**Implementation Priority:**
- **LOW**: All newspaper features (specs not finalized, dependent on content strategy)
- Recommend waiting for content strategy and data structure definition before building UI

**Dependencies:**
- Content management strategy (user-written vs. auto-generated)
- Article data model definition
- Rich text editor (if user-generated content)
- Article generation logic (if auto-generated)
- Typography styles for newspaper aesthetic

---

## Global UI Components & Patterns

### Reusable Components Identified

Based on the specifications, these shared components should be built first:

**High Priority (Foundation):**
1. **Base Layout Component** (extends base.html)
   - Responsive container
   - Consistent spacing/padding

2. **Navigation Components**
   - Mega dropdown menu
   - Breadcrumb navigation
   - Tab navigation

3. **Data Display Components**
   - Sortable table component (highly reusable)
   - Player list/card component
   - Team card component
   - Stat grid/card component

4. **Interactive Components**
   - Accordion/expansion panel
   - Modal/dialog
   - Tooltip

5. **Media Components**
   - Image component with fallback
   - Logo component

**Medium Priority (Enhancement):**
6. Filter/search components
7. Pagination component
8. Loading states/skeletons
9. Badge/pill components for tags/categories
10. Icon set (consistent visual language)

### Design System Considerations

**Typography:**
- Establish consistent heading hierarchy (H1-H6)
- Define body text styles
- Special styles for stats (monospace for numbers, bold for emphasis)

**Color Palette:**
- Primary: Blue (already using blue-700, blue-900)
- Secondary: Gray scale (already established)
- Accent: Define success/warning/error colors
- Team colors support (if needed)

**Spacing:**
- Already using Tailwind's spacing scale
- Maintain consistency in card padding, section margins

**Responsive Breakpoints:**
- Mobile-first approach
- Key breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Currently using md: and lg: prefixes appropriately

**Accessibility:**
- Semantic HTML (good foundation already)
- ARIA labels for interactive elements
- Keyboard navigation support
- Color contrast compliance (WCAG AA minimum)
- Focus states for all interactive elements

---

## Summary Statistics

### Completion Overview

**Templates Created:** 7 of ~20+ needed (35%)
- base.html (layout)
- index.html (front page - partial)
- players/list.html
- players/letter.html
- players/detail.html
- teams/list.html
- teams/detail.html (partial)

**Routes Implemented:** 7 of ~30+ needed (23%)
- Main: index, health
- Players: list, by_letter, detail
- Teams: list, detail
- Leaderboards: batting, pitching (placeholders)
- Newspaper: index (placeholder)

**Major Page Types:**
- Front Page: 30% complete
- Players: 70% complete
- Teams: 40% complete
- Leaderboards: 5% complete (structure only)
- League Pages: 0% complete
- Year Pages: 0% complete
- Newspaper: 0% complete

### Next Steps Recommendation

**Phase 1: Complete Core Functionality (Highest ROI)**
1. Build reusable component library (tables, cards, images)
2. Complete Front Page two-column layout
3. Add player images to player pages
4. Create Team Year pages
5. Implement League pages

**Phase 2: Leaderboards (High User Engagement)**
1. Build Leaderboard Home page
2. Implement Current Year Leaders
3. Create Career and Single-Season leaderboards
4. Add mega dropdown navigation

**Phase 3: Enhanced Features**
1. Year pages (league year summaries)
2. Player history and similarity scores
3. Team historical data and franchise leaders
4. Advanced leaderboard types (Progressive, Top Tens)

**Phase 4: Newspaper (Content-Dependent)**
1. Finalize content strategy
2. Build article templates
3. Implement article listing and navigation

---

## Technical Debt & Improvements

**Current Implementation Strengths:**
- Clean, semantic HTML structure
- Good use of Tailwind utility classes
- Proper template inheritance
- Accessible table markup
- Responsive grid layouts

**Areas for Improvement:**
1. **Navigation:** Missing dropdown menus, inconsistent with specs (Leaderboards vs Seasons)
2. **Images:** No image handling infrastructure (players, teams, logos)
3. **JavaScript:** No client-side interactivity (sorting, filtering, accordions)
4. **Component Extraction:** Repeated patterns (stat tables) should be Jinja macros or includes
5. **Loading States:** No feedback for data-heavy pages
6. **Error Handling:** Missing 404 pages, error states in templates
7. **SEO:** Missing meta descriptions, Open Graph tags
8. **Performance:** Consider moving from Tailwind CDN to build process for production

**Recommended Refactors:**
- Extract stat table into reusable Jinja macro
- Create template partials for player cards, team cards
- Implement base filter/search pattern for lists
- Add JavaScript build step for interactive components
- Consider Alpine.js or minimal vanilla JS for interactions

---

## Architectural Analysis - Backend & Data Perspective

### Data Model Assessment

**Existing Models (Strong Foundation):**
- **Player Models**: Comprehensive with `Player`, `PlayerCurrentStatus`, `PlayerBattingStats`, `PlayerPitchingStats`, `PlayerFieldingStats`
- **Team Models**: `Team`, `TeamRecord`, `TeamRoster` with proper hierarchical relationships
- **League Structure**: `League`, `SubLeague`, `Division` supporting flexible league configurations
- **Reference Data**: `City`, `Nation`, `State`, `Language`, `Park`, `Continent`
- **Ratings Models**: Separate batting/pitching/fielding ratings (though not referenced in routes yet)

**Critical Data Gaps:**
1. **Images**: Tables exist (`person_images`, `team_logos`, `league_logos`) but no retrieval/serving infrastructure
2. **Historical Data**: Tables exist (`team_history`, `league_history`, etc.) but not integrated into models
3. **Manager/Coach Data**: `coaches` table exists but no model or team relationships
4. **Game/Schedule Data**: `games` table exists but no model - needed for "Year" pages
5. **Transaction History**: `trade_history` table exists - needed for player histories
6. **Awards/Achievements**: Tables referenced but not modeled
7. **Similarity Scores**: No calculation or storage mechanism

### Backend Implementation Status by Feature

#### Front Page Backend Requirements
**Data Available:**
- ✅ Current standings (via `TeamRecord`)
- ✅ Player listings with WAR (via stats tables)
- ✅ Birth dates for "born this week" feature

**Missing Backend Components:**
- ❌ Rookie flagging system (needs experience tracking)
- ❌ Random player image selection query
- ❌ Game date synchronization service
- ❌ Magic number calculation algorithm

**Implementation Approach:**
```python
# Service layer needed for complex queries
class FrontPageService:
    def get_notable_rookies(self, limit=10)
    def get_players_born_this_week(self, game_date)
    def get_random_player_images(self, count=18)
    def calculate_magic_numbers(self, standings)
```

#### Leaderboards Backend Architecture
**Query Complexity Analysis:**
- **Career Leaders**: Simple aggregation, but needs indexing on `player_id`, `split_id`
- **Single-Season**: Straightforward with year filter
- **Active Players**: Requires join with `PlayerCurrentStatus.retired`
- **Progressive**: Complex - needs point-in-time calculations for each year
- **Year-by-Year Top Tens**: Requires window functions or multiple queries

**Performance Concerns:**
```sql
-- Example: Career home run leaders (will scan millions of rows)
SELECT player_id, SUM(hr) as total_hr
FROM players_career_batting_stats
WHERE split_id = 1
GROUP BY player_id
ORDER BY total_hr DESC
LIMIT 10;
```

**Recommended Architecture:**
1. **Materialized Views** for expensive aggregations:
   - `career_batting_leaders_mv`
   - `single_season_records_mv`
   - `active_player_stats_mv`

2. **Caching Strategy**:
   - Redis for frequently accessed leaderboards
   - 1-hour TTL for current season stats
   - 24-hour TTL for historical stats

3. **Service Layer Pattern**:
```python
class LeaderboardService:
    def __init__(self, cache_client):
        self.cache = cache_client

    def get_career_leaders(self, stat, limit=10):
        cache_key = f"career_{stat}_{limit}"
        # Check cache, fallback to DB, cache result

    def get_progressive_leaders(self, stat, year):
        # Complex calculation - definitely needs caching
```

#### Players Section Backend
**Available Queries:**
- ✅ Players by letter with career WAR (implemented but inefficient)
- ✅ Career stats by year
- ✅ Current team and status

**Missing Components:**
- ❌ Years of service calculation
- ❌ Leaderboard appearances tracking
- ❌ Similarity score algorithm
- ❌ Player transaction history

**Optimization Needed:**
Current implementation in `/players/` route loads ALL players then filters in Python. Should be:
```python
# Better approach - let database do the work
def get_top_players_by_letter(letter, limit=10):
    return db.session.query(
        Player,
        func.sum(PlayerBattingStats.war).label('career_war')
    ).outerjoin(
        PlayerBattingStats
    ).filter(
        Player.last_name.like(f'{letter}%')
    ).group_by(Player.player_id
    ).order_by(desc('career_war')
    ).limit(limit).all()
```

#### Teams Section Backend
**Critical Missing Queries:**
1. **Franchise History Aggregation**:
```python
def get_franchise_history(team_id):
    # Need to aggregate from team_history tables
    # Calculate all-time W-L record
    # Count championships, playoff appearances
```

2. **Top Franchise Players**:
```python
def get_franchise_top_players(team_id, limit=24):
    # Sum WAR for all players who played for this team
    # Complex join across player stats and rosters
```

3. **Year-by-Year Team Stats**:
- Requires `team_history_record` table integration
- Need manager data from missing model

### Database Performance Recommendations

**Critical Indexes Needed:**
```sql
-- For leaderboard queries
CREATE INDEX idx_batting_stats_split_year ON players_career_batting_stats(split_id, year);
CREATE INDEX idx_batting_stats_war ON players_career_batting_stats(war DESC) WHERE split_id = 1;
CREATE INDEX idx_player_lastname ON players_core(last_name);

-- For team queries
CREATE INDEX idx_team_roster_team_player ON team_roster(team_id, player_id);
CREATE INDEX idx_team_history_team_year ON team_history_record(team_id, year);

-- For date-based queries
CREATE INDEX idx_player_birth_date ON players_core(date_of_birth);
```

**Query Optimization Priorities:**
1. **HIGH**: Leaderboard queries (most expensive, most frequent)
2. **HIGH**: Player list pages (currently loading all players)
3. **MEDIUM**: Team franchise history (one-time load per team)
4. **LOW**: Similarity scores (can be pre-calculated in batch)

### Service Layer Architecture

**Recommended Service Structure:**
```
app/
├── services/
│   ├── __init__.py
│   ├── base.py (BaseService with caching)
│   ├── leaderboard_service.py
│   ├── player_service.py
│   ├── team_service.py
│   ├── stats_service.py
│   └── cache_service.py
├── repositories/  # Data access layer
│   ├── player_repository.py
│   ├── team_repository.py
│   └── stats_repository.py
└── utils/
    ├── calculations.py (WAR, magic number, etc.)
    └── date_utils.py (game date handling)
```

### API Design for Future Features

**RESTful Endpoints Needed:**
```
# For AJAX/dynamic content
GET /api/players/random-images?count=18
GET /api/players/rookies?limit=10
GET /api/players/birthdays?week_offset=0

GET /api/leaderboards/{stat}/{type}?year=2024&league=1
GET /api/leaderboards/progressive/{stat}?year=2024

GET /api/teams/{team_id}/history
GET /api/teams/{team_id}/top-players?limit=24

# For similarity scores (expensive, should be async)
GET /api/players/{player_id}/similar
```

### Data Pipeline Requirements

**ETL Enhancements Needed:**
1. **Image Processing Pipeline**: Ingest and store player/team images with proper URLs
2. **Rookie Flagging**: Mark first-year players at highest level
3. **Similarity Score Calculation**: Batch process using Bill James formula
4. **Leaderboard Materialization**: Pre-calculate expensive aggregations
5. **Historical Data Integration**: Import team_history, league_history tables

### Infrastructure Recommendations

**Caching Layer:**
- Redis for query results and calculated values
- Consider Redis Sorted Sets for leaderboards (natural fit)

**Background Jobs (Celery/RQ):**
- Similarity score calculations
- Leaderboard updates
- Image processing
- Game narrative generation (for newspaper)

**Search Infrastructure:**
- Elasticsearch for player/team search (future enhancement)
- Full-text search for newspaper articles

### Implementation Priority from Backend Perspective

**Phase 1: Foundation (Required for most features)**
1. Implement service layer architecture
2. Add critical database indexes
3. Set up Redis caching
4. Create image serving infrastructure

**Phase 2: Core Features**
1. Leaderboard query optimization and caching
2. Player service with efficient queries
3. Team history aggregation
4. Game date synchronization

**Phase 3: Advanced Features**
1. Similarity score calculation system
2. Progressive leaderboard calculations
3. Transaction history integration
4. Background job infrastructure

**Phase 4: Performance & Scale**
1. Materialized views for expensive queries
2. Read replicas for heavy read operations
3. CDN for static assets and images
4. Query result pagination

### Risk Mitigation

**Performance Risks:**
- Leaderboard queries on millions of rows → Mitigate with materialized views
- N+1 queries in templates → Use eager loading in SQLAlchemy
- Memory issues with large result sets → Implement pagination

**Data Integrity Risks:**
- Orphaned players without teams → Add data validation in ETL
- Missing statistical categories → Provide defaults/nulls handling
- Inconsistent year/season data → Centralize season management

**Scalability Concerns:**
- Current single-DB architecture → Plan for read replicas
- No caching layer → Implement Redis early
- Synchronous calculations → Design for async from start
