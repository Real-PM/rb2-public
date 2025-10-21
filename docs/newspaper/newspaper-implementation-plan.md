# Newspaper Section - Implementation Plan

## Project Overview

Implementation of an LLM-powered newspaper section for the RB2 baseball reference website. The system will automatically generate newspaper-style articles about Branch family member performances, integrate user-written content, and reprint game messages as filler stories.

**Related Documents:**
- `docs/newspaper-brainstorm.md` - Detailed technical specifications and code examples
- `docs/WEBSITE-SPECS.MD` - Overall UI/UX specifications

---

## System Requirements

### Hardware (Development Machine)
- **CPU:** Intel i9-14900KF
- **RAM:** 64GB
- **GPU:** NVIDIA RTX 4090 (24GB VRAM)
- **OS:** Linux (confirmed)

### Software Stack
- **LLM Platform:** Ollama (local inference)
- **Backend:** Flask (existing)
- **Database:** PostgreSQL (existing at 192.168.10.94:5432)
- **Frontend:** Tailwind CSS, Jinja2 templates

---

## Design Decisions

### 1. Article Generation Trigger
**Decision:** Post-ETL update hook

When the ETL update completes (after importing new game data), automatically trigger the article generation pipeline for any games featuring Branch family members.

**Rationale:**
- Ensures articles are generated for fresh data
- Single automated workflow
- No manual intervention needed for routine games

### 2. Multi-Branch Game Handling
**Decision:** Single combined article when multiple Branch family members play in the same game

**Implementation:**
- Detect all Branch players in game
- Prioritize based on combined newsworthiness
- Generate one article featuring all Branch performances
- Store all player_ids in article record

### 3. Editorial Workflow
**Decision:** Draft → Review → Publish with regeneration capability

**Initial Phase (MVP):**
- All generated articles saved as drafts
- Manual editorial review required
- Approve/publish or regenerate with refinement
- Reject/delete option

**Future Phase:**
- Auto-publish based on confidence score
- Spot-check workflow for high-priority games
- Manual intervention only for milestones

### 4. LLM Model Selection
**Decision:** Ollama with multi-model strategy

**Model Tiers:**
1. **High Priority (newsworthiness ≥ 80):**
   - Primary: `qwen2.5:14b` or `llama3.1:70b`
   - Use case: Milestones, multi-HR games, shutouts, no-hitters
   - Quality over speed

2. **Normal Priority (50-79):**
   - Primary: `llama3.1:8b` or `qwen2.5:14b`
   - Use case: Solid performances (3-hit game, quality start, save)
   - Balance speed and quality

3. **Testing Candidates:**
   - `llama3.1:8b` (~5GB VRAM) - Fast baseline
   - `qwen2.5:14b` (~8GB VRAM) - Best for journalistic writing
   - `llama3.1:70b` (~40GB total) - Highest quality, slower
   - `mixtral:8x7b` (~26GB) - Alternative high-quality option

**Testing Protocol:**
- Benchmark each model with identical prompts
- Measure: generation time, article quality, factual accuracy
- Document optimal parameters (temperature, top_p, max_tokens)

### 5. Article Types

| Type | Source | Priority | Auto-Publish |
|------|--------|----------|--------------|
| `game_recap_branch` | AI-generated | Variable | After review |
| `game_recap_general` | AI-generated | Low | Future phase |
| `journal_entry` | User-written | N/A | Manual |
| `historical_article` | User-written | N/A | Manual |
| `milestone` | AI-generated | Critical | After review |
| `message_reprint` | From `messages` table | Filler | Auto |

---

## Implementation Phases

### Phase 1: Foundation

#### Task 1.1: Ollama Infrastructure Setup
**Objective:** Install and configure Ollama with optimal models

**Steps:**
1. Check if Ollama is installed: `which ollama`
2. Install if needed: Follow official Ollama installation
3. Start Ollama service: `ollama serve` (or systemd service)
4. Pull test models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull qwen2.5:14b
   ollama pull llama3.1:70b  # If testing high-quality
   ```
5. Test basic generation:
   ```bash
   ollama run llama3.1:8b "Write a 200-word newspaper article about a baseball game."
   ```

**Deliverables:**
- Ollama running as service
- At least 2 models pulled and tested
- Benchmark document: `docs/ollama-model-benchmarks.md`

---

#### Task 1.2: Database Schema Creation
**Objective:** Create tables for newspaper articles and game moments

**Schema 1: `newspaper_articles`**
```sql
CREATE TABLE newspaper_articles (
    article_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(game_id),
    article_date DATE NOT NULL,
    headline VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    article_type VARCHAR(50) NOT NULL,
    generation_method VARCHAR(50),
    model_used VARCHAR(50),
    newsworthiness_score INT,
    player_ids INT[],
    team_ids INT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Editorial workflow
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'published', 'rejected'
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,

    -- Regeneration tracking
    generation_count INT DEFAULT 1,
    previous_version_id INT REFERENCES newspaper_articles(article_id),

    CONSTRAINT valid_score CHECK (newsworthiness_score >= 0 AND newsworthiness_score <= 100),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'published', 'rejected'))
);

CREATE INDEX idx_articles_date ON newspaper_articles(article_date DESC);
CREATE INDEX idx_articles_player_ids ON newspaper_articles USING GIN(player_ids);
CREATE INDEX idx_articles_game_id ON newspaper_articles(game_id);
CREATE INDEX idx_articles_status ON newspaper_articles(status);
CREATE INDEX idx_articles_published ON newspaper_articles(article_date DESC)
    WHERE status = 'published';
```

**Schema 2: `branch_game_moments`**
```sql
CREATE TABLE branch_game_moments (
    moment_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(game_id),
    player_id INT REFERENCES players_core(player_id),
    inning INT,
    inning_half VARCHAR(10),  -- 'top' or 'bottom'
    moment_type VARCHAR(50),   -- 'at_bat', 'pitching_inning', 'defensive_play'
    play_sequence JSONB,       -- Array of play-by-play lines
    outcome VARCHAR(200),
    exit_velocity DECIMAL(5,1),
    hit_location VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_inning_half CHECK (inning_half IN ('top', 'bottom'))
);

CREATE INDEX idx_moments_game_player ON branch_game_moments(game_id, player_id);
CREATE INDEX idx_moments_player ON branch_game_moments(player_id);
CREATE INDEX idx_moments_game ON branch_game_moments(game_id);
```

**Schema 3: Staging Tables for Volatile CSV Data (Added 2025-10-20)**
```sql
-- Staging table for per-game batting stats from players_game_batting.csv
CREATE TABLE IF NOT EXISTS staging_branch_game_batting (
    player_id INTEGER NOT NULL,
    year SMALLINT,
    team_id INTEGER,
    game_id INTEGER NOT NULL,
    league_id INTEGER,
    level_id SMALLINT,
    split_id SMALLINT,
    position SMALLINT,
    ab SMALLINT,
    h SMALLINT,
    k SMALLINT,
    pa SMALLINT,
    g SMALLINT,
    d SMALLINT,  -- doubles
    t SMALLINT,  -- triples
    hr SMALLINT,
    r SMALLINT,
    rbi SMALLINT,
    sb SMALLINT,
    bb SMALLINT,
    wpa NUMERIC,
    loaded_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (player_id, game_id)
);

-- Staging table for per-game pitching stats from players_game_pitching_stats.csv
CREATE TABLE IF NOT EXISTS staging_branch_game_pitching (
    player_id INTEGER NOT NULL,
    year SMALLINT,
    team_id INTEGER,
    game_id INTEGER NOT NULL,
    league_id INTEGER,
    level_id SMALLINT,
    split_id SMALLINT,
    g SMALLINT,
    gs SMALLINT,
    ip NUMERIC,
    h SMALLINT,
    r SMALLINT,
    er SMALLINT,
    hr SMALLINT,
    bb SMALLINT,
    k SMALLINT,
    w SMALLINT,
    l SMALLINT,
    sv SMALLINT,
    hld SMALLINT,
    wpa NUMERIC,
    loaded_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (player_id, game_id)
);

CREATE INDEX IF NOT EXISTS idx_staging_batting_game ON staging_branch_game_batting(game_id);
CREATE INDEX IF NOT EXISTS idx_staging_pitching_game ON staging_branch_game_pitching(game_id);

COMMENT ON TABLE staging_branch_game_batting IS 'Temporary staging for Branch player batting stats from players_game_batting.csv';
COMMENT ON TABLE staging_branch_game_pitching IS 'Temporary staging for Branch player pitching stats from players_game_pitching_stats.csv';
```

**Note:** These staging tables are truncated after each article generation run to ensure fresh data from volatile CSV exports.

**Deliverables:**
- ✅ SQL migration script: `etl/sql/migrations/002_newspaper_llm_enhancements.sql` (COMPLETED 2025-10-20)
- ✅ Tables created in `ootp_dev` database (COMPLETED 2025-10-20)
- ✅ Verification queries run successfully (COMPLETED 2025-10-20)
- [ ] Create staging tables migration script
- [ ] Document CSV data flow

---

### Phase 2: Article Generation Pipeline

#### Task 2.1: Branch Game Detection
**Objective:** Identify games featuring Branch family members and prioritize

**Location:** `etl/src/newspaper/` (new module)

**Files to Create:**
```
etl/src/newspaper/
├── __init__.py
├── branch_detector.py     # Detect Branch games
├── newsworthiness.py      # Scoring algorithm
└── game_context.py        # Gather game data
```

**Data Sources:**

**CSV Files Used (Updated Strategy - 2025-10-20):**
- **`players_game_batting.csv`** - Per-game batting stats (PRIMARY SOURCE)
- **`players_game_pitching_stats.csv`** - Per-game pitching stats (PRIMARY SOURCE)
- **`game_logs.csv`** - Play-by-play narrative details (Task 2.2)
- **`players_at_bat_batting_stats.csv`** - PA-level details (FUTURE ENHANCEMENT)

**Staging Table Strategy:**
These CSV files are volatile and overwritten on each OOTP export. To handle them:
1. Load `players_game_batting.csv` and `players_game_pitching_stats.csv` into temporary staging tables
2. Filter immediately to Branch family player IDs
3. Use for game detection and newsworthiness scoring
4. **Truncate staging tables after processing** to avoid stale data issues
5. Alternative: Add `etl_run_id` column for debugging (keep last 3 runs)

**Key Functions:**

**`branch_detector.py`:**
```python
def get_branch_family_ids(db_connection):
    """
    Query all Branch family player IDs.
    Checks branch_family_members table or players_core with last_name='Branch'.
    """

def load_game_stats_to_staging(csv_path, stats_type='batting'):
    """
    Load players_game_batting.csv or players_game_pitching_stats.csv
    to staging tables, filtered to Branch players only.

    Args:
        csv_path: Path to CSV file
        stats_type: 'batting' or 'pitching'

    Returns: Number of records loaded
    """

def detect_branch_games(branch_ids, date_range=None):
    """
    Scan staging tables (loaded from players_game_batting/pitching CSVs)
    for Branch appearances.

    Filters:
    - player_id IN branch_ids
    - date_range if specified
    - Exclude games already processed (check newspaper_articles)

    Returns: List of dicts with game_id, player_id(s), stats
    """

def detect_multi_branch_games(branch_games):
    """
    Identify games where multiple Branch players appeared.
    Merge into single record for combined article.

    Returns: Deduplicated list with player_ids array
    """

def cleanup_staging_tables():
    """
    Truncate staging tables after article generation completes.
    Ensures fresh data on next run.
    """
```

**`newsworthiness.py`:**
```python
def calculate_newsworthiness(performance):
    """
    Score games 0-100 based on performance quality.

    Batting:
    - Multi-HR game: 50+ points
    - 4+ hits: 40 points
    - 5+ RBI: 45 points
    - Cycle: 90 points

    Pitching:
    - Shutout: 70 points
    - No-hitter: 95 points
    - Quality start + 10K: 60 points
    - Complete game: 50 points

    Returns: int (0-100)
    """

def prioritize_games(branch_games):
    """
    Add priority tier based on score:
    - MUST_GENERATE: ≥80
    - SHOULD_GENERATE: 50-79
    - COULD_GENERATE: 20-49
    - SKIP: <20

    Returns: Sorted list with priority field
    """
```

**`game_context.py`:**
```python
def get_game_context(game_id):
    """
    Fetch complete game metadata:
    - Teams, score, attendance
    - Winning/losing/save pitchers
    - Date, innings, hits/errors

    Returns: dict
    """

def get_branch_player_details(player_id, game_id, perf_type):
    """
    Get player bio and full game stats.

    Returns: dict with player info and stats
    """
```

**Deliverables:**
- `etl/src/newspaper/` module created
- Unit tests: `etl/tests/test_branch_detector.py`
- Successfully detects Branch games from test data

---

#### Task 2.2: game_logs.csv Parser
**Objective:** Extract play-by-play details for Branch at-bats/innings

**Location:** `etl/src/newspaper/game_log_parser.py`

**Key Functions:**
```python
def extract_branch_plays_from_game_log(game_id, branch_player_ids):
    """
    Parse game_logs.csv for specific game.
    Extract only plays involving Branch family members.

    Strategy:
    - Read CSV line by line
    - Filter by game_id
    - Detect Branch player mentions (player_XXX.html pattern)
    - Extract play sequence with context (5 lines before/after)
    - Track inning context

    Returns: List of play dicts
    """

def structure_branch_at_bats(branch_plays, player_id):
    """
    Convert raw play sequence into structured at-bat summaries.

    Parse:
    - Pitch sequence (Ball, Strike, Foul)
    - Outcome (single, HR, strikeout, etc.)
    - Exit velocity (if available)
    - Hit location

    Returns: List of at-bat dicts
    """

def save_branch_moments_to_db(game_id, player_id, at_bats):
    """
    Store extracted moments in branch_game_moments table.
    For future article regeneration without re-parsing CSV.
    """
```

**game_logs.csv Management:**

Per brainstorm specs, implement rolling window strategy:
- Keep current season in active CSV
- Archive historical seasons as compressed files
- On-demand retrieval from archives for regeneration

**File:** `etl/src/newspaper/game_log_archiver.py`
```python
def prune_game_logs(current_season_year):
    """
    Archive historical game_logs, keep current season only.
    Run at end of each season.
    """

def get_game_log_from_archive(game_id):
    """
    Retrieve archived game logs if regenerating old article.
    """
```

**Deliverables:**
- ✅ `game_log_parser.py` created (2025-10-20)
- ✅ `game_log_archiver.py` created (2025-10-20)
- ✅ Tested with sample game_logs data
- ✅ Successfully extracts Branch at-bats with details

**Implementation Notes:**
- Parser correctly extracts player IDs from HTML links using regex
- Tracks inning context (top/bottom, inning number) throughout game
- Classifies outcomes into categories: home_run, single, double, triple, walk, strikeout, ground_out, fly_out, etc.
- Extracts exit velocity and hit location codes from play descriptions
- Saves parsed moments to `branch_game_moments` table for efficient regeneration
- Archiver implements gzip compression for historical seasons
- `get_game_log_entries()` automatically checks active CSV first, then archives
- Tested with game_id=1, extracted 11 at-bats for 3 test players successfully

---

#### Task 2.3: LLM Prompt Builder
**Objective:** Construct detailed prompts for article generation

**Location:** `etl/src/newspaper/prompt_builder.py`

**Key Functions:**
```python
def build_article_prompt(game_context, branch_player_details, branch_at_bats=None):
    """
    Construct comprehensive prompt with:
    - Game metadata (teams, score, date, attendance)
    - Branch player stats (batting line or pitching line)
    - Play-by-play details (if available from game_logs)
    - Instructions for journalistic style
    - Period-appropriate language guidelines (1960s-era)
    - Output format (HEADLINE: / body structure)

    Returns: string prompt
    """

def build_multi_branch_prompt(game_context, branch_players_details, at_bats_dict):
    """
    Special prompt for games with multiple Branch family members.
    Focus on family angle, compare performances.
    """

def build_regeneration_prompt(original_article, feedback):
    """
    Prompt for article refinement.
    Include original text + editorial feedback.
    Request specific improvements.
    """
```

**Prompt Engineering Guidelines:**
- Use structured format for game data
- Provide explicit style instructions
- Include examples of good vs bad journalism
- Request specific word count (200-250 words)
- Emphasize factual accuracy
- Period-appropriate terminology

**Deliverables:**
- ✅ `prompt_builder.py` created (2025-10-20)
- ✅ Sample prompts saved: `docs/newspaper/sample-prompts.md`
- ⏳ Test prompts with Ollama manually (pending Task 2.4)

**Implementation Notes:**
- Three main prompt types: single player, multi-Branch family, and regeneration
- Formats batting lines (e.g., "3-for-4 with 2 home runs and 5 RBI")
- Formats pitching lines (e.g., "7.0 innings, allowing 3 hits and 1 earned run with 9 strikeouts")
- Includes play-by-play narrative integration from game_log_parser
- Model selection based on priority tier: qwen2.5:14b (MUST), 7b (SHOULD), 3b (COULD)
- Temperature adjustment by priority: 0.6 (MUST), 0.7 (SHOULD), 0.75 (COULD)
- Token estimation and validation functions included
- **ERA-APPROPRIATE STYLING**: Dynamically adjusts journalistic style based on game date
  - 1920s "Roaring Twenties": Flowery prose, dramatic verbs, entertainment focus
  - 1930s-1940s "Golden Age": Formal, reverent, players as heroes, WWII context awareness
  - 1950s-1960s "Post-War Era": Wire service clarity, objective, just-the-facts
  - 1970s-1980s "Modern Era": Casual professional, early sabermetrics
  - 1990s-2000s "Contemporary Era": Analytical, OPS/advanced stats
  - 2010s+ "Digital Era": Data-driven, exit velocity, launch angle, sabermetric terms
- Prompts target 200-250 words for single player, 250-300 for multi-player
- Sample prompts demonstrate ~418-452 tokens per prompt (well within model limits)

---

#### Task 2.4: Ollama Client Implementation
**Objective:** API client for Ollama with error handling and retry logic

**Location:** `etl/src/newspaper/ollama_client.py`

**Key Functions:**
```python
class OllamaClient:
    def __init__(self, base_url='http://localhost:11434', default_model='qwen2.5:14b'):
        """Initialize client with configurable endpoint."""

    def generate_article(self, prompt, model=None, temperature=0.7, max_tokens=400):
        """
        Call Ollama /api/generate endpoint.

        Args:
            prompt: Full prompt string
            model: Override default model
            temperature: 0.0-1.0 (0.7 recommended for journalism)
            max_tokens: ~400 for 250-word articles

        Returns: Generated text
        """

    def generate_with_retry(self, prompt, max_retries=3, backoff=2):
        """
        Retry logic for network failures or timeouts.
        Exponential backoff.
        """

    def check_model_availability(self, model_name):
        """Verify model is pulled and ready."""

    def benchmark_model(self, model_name, test_prompt):
        """
        Test generation time and output quality.
        For model selection benchmarking.
        """
```

**Configuration:**
- Store model preferences in config file
- Map priority scores to model selection
- Configurable timeouts (60s for small models, 120s for 70B)

**Error Handling:**
- Network errors: Retry with backoff
- Model not found: Fallback to smaller model
- Timeout: Log and mark article as failed
- Parse errors: Log raw output for debugging

**Deliverables:**
- `ollama_client.py` created
- Config file: `etl/config/ollama_config.yaml`
- Unit tests: `etl/tests/test_ollama_client.py`
- Successfully generates test articles

---

#### Task 2.5: Article Parser and Storage
**Objective:** Extract headline/body from LLM output and save to database

**Status:** ✅ COMPLETED (2025-10-20)

**Location:** `etl/src/newspaper/article_processor.py`

**Implementation Notes:**
- **ArticleProcessor class** created with full CRUD operations
- **Article parsing:** Extracts headline and body from LLM format (`HEADLINE:` marker or fallback)
- **Validation logic:** Checks headline length (10-255 chars), body length (100-5000 chars), word count (50-1000), placeholder text detection
- **Slug generation:** URL-friendly slugs with date prefixes and database-enforced uniqueness
- **Database storage:** Inserts to `newspaper_articles` with automatic excerpt generation
- **Player/Team tagging:** Creates records in `article_player_tags` and `article_team_tags` (first tagged as primary)
- **Game tagging:** Creates record in `article_game_tags` (marked as recap)
- **Regeneration support:** Creates new article version linked via `previous_version_id`, increments `generation_count`, copies all tags
- **Complete workflow:** `process_and_save()` method handles parse → validate → save in single call

**Test Results:**
- ✅ All 6/6 unit tests passing (`test_article_processor.py`)
- ✅ End-to-end integration test passing with database storage
- ✅ Articles successfully parsed, validated, saved, and retrieved
- ✅ Regeneration creates properly linked versions

**Files Created:**
- `etl/src/newspaper/article_processor.py` (660 lines)
- `etl/src/newspaper/test_article_processor.py` (450 lines)

**Files Updated:**
- `etl/src/newspaper/test_end_to_end.py` - Added database storage step to pipeline

---

#### Task 2.6: End-to-End Pipeline Integration
**Objective:** Orchestrate full article generation workflow

**Location:** `etl/src/newspaper/pipeline.py`

**Main Function:**
```python
def generate_branch_articles_pipeline(date_range=None, force_regenerate=False):
    """
    End-to-end pipeline for Branch family article generation.

    Workflow:
    1. Get Branch family player IDs
    2. Detect Branch games in date_range
    3. Check for existing articles (skip unless force_regenerate)
    4. Prioritize by newsworthiness
    5. Filter to MUST_GENERATE and SHOULD_GENERATE
    6. For each game:
        a. Gather game context
        b. Get player details
        c. Extract/retrieve game_log plays
        d. Save moments to branch_game_moments
        e. Build prompt
        f. Select model based on priority
        g. Generate article via Ollama
        h. Parse and validate output
        i. Save to database as draft
        j. Log results
    7. Return summary statistics

    Returns: dict with counts (generated, failed, skipped)
    """
```

**ETL Hook Integration:**

**File:** `etl/main.py` (modify existing)
```python
# Add at end of successful ETL run
from src.newspaper.pipeline import generate_branch_articles_pipeline

def run_etl():
    # ... existing ETL logic ...

    # After successful data import
    if etl_successful:
        logger.info("Starting newspaper article generation...")
        try:
            results = generate_branch_articles_pipeline(
                date_range=(etl_start_date, etl_end_date)
            )
            logger.info(f"Article generation complete: {results}")
        except Exception as e:
            logger.error(f"Article generation failed: {e}")
            # Don't fail ETL if article generation fails
```

**Deliverables:**
- `pipeline.py` created
- ETL integration in `main.py`
- End-to-end test with real game data
- Generated articles visible in database

---

### Phase 3: Editorial & User Input

**Status:** ✅ **FULLY COMPLETED (2025-10-20)**

All admin and user content creation interfaces built and tested. Ready for Phase 2 pipeline integration.

#### Task 3.1: Editorial Review Interface
**Objective:** Admin page for reviewing and publishing draft articles

**Status:** ✅ COMPLETED (2025-10-20)

**Location:** `web/app/routes/newspaper_admin.py` (new blueprint)

**Authentication:**
- **Development:** No authentication required (open access)
- **Staging/Production:** TODO - Implement Flask-Login with User model
  - See `docs/newspaper/AUTHENTICATION-TODO.md` for complete implementation guide
  - See decorator documentation in `newspaper_admin.py` for implementation notes
  - Will require: flask-login package, User model, login/logout routes, role-based access

**Routes:**

**1. Draft Article List**
```python
@bp.route('/newspaper/admin/drafts')
@login_required  # Add authentication
def draft_list():
    """
    Show all draft articles, sorted by:
    - Newsworthiness score (desc)
    - Article date (desc)

    Display:
    - Headline
    - Game info (teams, score, date)
    - Featured players
    - Newsworthiness score
    - Generation metadata (model, time)
    - Actions: [Review] [Delete]
    """
```

**2. Article Review Page**
```python
@bp.route('/newspaper/admin/review/<int:article_id>')
@login_required
def review_article(article_id):
    """
    Full article display with editorial controls.

    Display:
    - Full article (headline + body)
    - Game box score (summary)
    - Featured player stats
    - Generation metadata

    Actions:
    - [Publish] - Set status='published', record reviewer
    - [Regenerate] - Show feedback form
    - [Edit] - Inline editing (future enhancement)
    - [Reject] - Set status='rejected'
    """
```

**3. Regenerate Handler**
```python
@bp.route('/newspaper/admin/regenerate/<int:article_id>', methods=['POST'])
@login_required
def regenerate_article(article_id):
    """
    Regenerate article with optional feedback.

    Form fields:
    - feedback: Optional text (e.g., "Focus more on pitcher performance")
    - model_override: Optional model selection

    Workflow:
    - Call article_processor.regenerate_article()
    - Redirect to review page for new version
    """
```

**4. Publish Handler**
```python
@bp.route('/newspaper/admin/publish/<int:article_id>', methods=['POST'])
@login_required
def publish_article(article_id):
    """
    Update status='published', set reviewed_by and reviewed_at.
    Redirect to published article on public site.
    """
```

**Templates:**
- `templates/newspaper/admin/drafts.html` - List view
- `templates/newspaper/admin/review.html` - Review interface

**Deliverables:**
- ✅ `newspaper_admin.py` blueprint created and registered (2025-10-20)
- ✅ Templates created with design-system.md styling (2025-10-20)
- ⏳ Authentication deferred - Flask-Login for staging/prod (documented in code)
- ✅ Functional review workflow (2025-10-20)

**Implementation Notes (2025-10-20):**
- ✅ All admin routes functional: drafts list, review, publish, reject, delete, regenerate
- ✅ Templates follow vintage newspaper design system (docs/newspaper/design-system.md)
- ✅ Player/team autocomplete APIs implemented
- ✅ Regeneration route ready for Phase 2 pipeline integration
- ✅ Templates created: drafts.html, review.html, regenerate.html
- ✅ Tested and working in development environment

---

#### Task 3.2: User Content Creation Interface
**Objective:** Form for manually creating journal entries and historical articles

**Location:** `web/app/routes/newspaper_admin.py` (extend)

**Route:**
```python
@bp.route('/newspaper/admin/create', methods=['GET', 'POST'])
@login_required
def create_article():
    """
    Manual article creation form.

    Form fields:
    - article_type: Select (journal_entry, historical_article)
    - article_date: Date picker
    - headline: Text input
    - body: Rich text editor (TinyMCE or similar)
    - player_mentions: Autocomplete multi-select
    - team_mentions: Autocomplete multi-select
    - game_link: Optional game_id dropdown

    On submit:
    - Parse player/team autocomplete IDs
    - Store in player_ids/team_ids arrays
    - Convert mentions to hyperlinks in body HTML
    - Save with status='published' (user content auto-publishes)
    - Redirect to article detail page
    """
```

**Autocomplete Implementation:**

**API Endpoints:**
```python
@bp.route('/api/players/search')
def search_players():
    """
    Search players_core by name.

    Query params:
    - q: Search query
    - limit: Max results (default 10)

    Returns: JSON array of {player_id, name, position, team}
    """

@bp.route('/api/teams/search')
def search_teams():
    """
    Search teams by name or abbreviation.

    Returns: JSON array of {team_id, name, nickname, abbr}
    """
```

**Frontend JavaScript:**
- Use Select2 or similar library for autocomplete
- AJAX calls to search endpoints
- Tag-style multi-select UI
- Store selected IDs in hidden form fields

**Rich Text Editor:**
- TinyMCE (recommended) or CKEditor
- Toolbar: Bold, italic, paragraph, links, lists
- Paste cleanup (strip Word formatting)
- Character/word counter

**Player/Team Linking:**
- User selects players/teams via autocomplete
- Store IDs in arrays
- When rendering article on frontend, hyperlink player/team names
  - Regex or manual tagging during editing
  - Or: Post-process body text to detect and link names

**Template:**
`templates/newspaper/admin/create.html`
- Form layout with TinyMCE integration
- Autocomplete fields for players/teams
- Save/Preview buttons

**Deliverables:**
- ✅ Create article route and form (2025-10-20)
- ✅ Autocomplete API endpoints for players and teams (2025-10-20)
- ⏳ Rich text editor - using plain textarea (TinyMCE deferred for future)
- ✅ Successfully creates and saves user articles (2025-10-20)

**Implementation Notes (2025-10-20):**
- ✅ Form creates articles with status='published' (user content auto-publishes)
- ✅ JavaScript autocomplete for players/teams with tag-style UI
- ✅ Player/team tags stored in junction tables (first tag marked as primary)
- ✅ Slug generation with date prefix and uniqueness validation
- ✅ HTML allowed in content field for basic formatting
- ✅ Date picker defaults to current game date (1965-09-01)
- ✅ **Auto-linking implemented** - Player/team names automatically become clickable links
  - Created `/web/app/utils/article_links.py`
  - Function: `auto_link_content()` and `process_article_for_display()`
  - Smart matching: full names, last names, team nicknames
  - Won't double-link or break existing HTML
  - Applied to public article detail pages
- ✅ Template created: create.html
- ✅ Tested and working - successfully creates articles with auto-linked content

**Enhancement: Article Image Support (2025-10-21):**
- ✅ **Database schema** - `article_images` table with three image types:
  - `player`: Links to player_id, serves from `etl/data/images/players/player_{id}.png`
  - `team_logo`: Links to team_id with size variants (default, 16, 25, 40, 50, 110)
  - `uploaded`: Custom user uploads stored in `web/app/static/uploads/articles/`
  - Supports captions, alt text, and display ordering
- ✅ **Backend infrastructure**:
  - ArticleImage model with `get_image_url()` method
  - Static route `/etl-images/<path>` to serve images from ETL directory
  - Image upload handling with secure filenames and UUID prefixes
  - Migration: `etl/sql/migrations/003_article_images.sql`
  - DDL updated: `etl/sql/tables/07_newspaper.sql`
- ✅ **Frontend UI** - Three-tab interface in article creation form:
  - **Player Pictures**: Radio selection from tagged players
  - **Team Logos**: Radio selection from tagged teams with size selector
  - **Upload Custom**: File upload with preview and caption
  - Dynamic updates when players/teams are tagged/removed
  - Visual feedback showing selected images
- ✅ **Image display**:
  - Article detail page shows images between byline and body
  - Vintage newspaper styling with tan borders
  - Optional captions displayed below images
  - Proper alt text for accessibility
- ✅ Files modified:
  - `web/app/models/newspaper.py` - Added ArticleImage model
  - `web/app/routes/main.py` - Added image serving route
  - `web/app/routes/newspaper_admin.py` - Added image upload handling
  - `web/app/templates/newspaper/admin/create.html` - Added image selection UI
  - `web/app/templates/newspaper/article.html` - Added image display

---

**Bug Fixes (2025-10-20):**
- Fixed: Foreign key error with `games` table - removed ForeignKey declarations from Article and ArticleGameTag models (Game model not yet defined)
- Fixed: SQLAlchemy lambda syntax error in related articles query - changed to proper join syntax
- Fixed: Missing `regenerate.html` template - created with feedback form and model override options

---

### Phase 4: Frontend Display

**Status:** ✅ **COMPLETED (2025-10-20)** - Public templates built and tested

**Note:** Player/Team article archives (Task 4.3, 4.4) deferred for future implementation

#### Task 4.1: Newspaper Homepage Layout
**Objective:** Design responsive newspaper-style homepage

**Route:** `web/app/routes/newspaper.py` (new blueprint)

**Homepage Route:**
```python
@bp.route('/newspaper')
def newspaper_home():
    """
    Newspaper homepage with hero article + grid.

    Layout:
    - Hero article (top): Highest newsworthiness from last 7 days
    - 3-column grid (desktop) / 1-column (mobile): Recent articles
    - Pagination or infinite scroll

    Query:
    - Get published articles from last 30 days
    - Sort by article_date DESC, newsworthiness_score DESC
    - Limit 20 per page
    """
```

**Template:** `templates/newspaper/index.html`

**Layout Structure:**
```html
<div class="newspaper-container max-w-7xl mx-auto px-4">
    <!-- Hero Article -->
    <article class="hero-article mb-8 border-b-4 border-gray-800 pb-6">
        <h1 class="text-5xl font-bold mb-2">{{ hero.headline }}</h1>
        <div class="text-sm text-gray-600 mb-4">
            {{ hero.article_date }} | By Branch Family Chronicle
        </div>
        <div class="text-lg leading-relaxed">
            {{ hero.body[:400] }}...
        </div>
        <a href="{{ url_for('newspaper.article_detail', article_id=hero.article_id) }}">
            Read more →
        </a>
    </article>

    <!-- 3-Column Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        {% for article in articles %}
        <article class="border-b pb-4">
            <h3 class="text-xl font-bold mb-2">
                <a href="{{ url_for('newspaper.article_detail', article_id=article.article_id) }}">
                    {{ article.headline }}
                </a>
            </h3>
            <div class="text-sm text-gray-600 mb-2">{{ article.article_date }}</div>
            <p class="text-sm">{{ article.body[:150] }}...</p>
        </article>
        {% endfor %}
    </div>
</div>
```

**Responsive Design:**
- Desktop: Hero + 3 columns
- Tablet: Hero + 2 columns
- Mobile: Hero + 1 column (stacked)

**Hero Article Selection Logic:**
```python
def get_hero_article():
    """
    Select hero article:
    - Published status
    - Last 7 days
    - Highest newsworthiness score
    - Fallback: Most recent if no high-priority articles
    """
```

**Styling:**
- Newspaper-style fonts (Georgia, serif for body)
- Clean typography hierarchy
- Subtle borders/dividers
- Print-inspired aesthetic

**Deliverables:**
- `newspaper.py` blueprint created
- Homepage template with responsive layout
- Hero article auto-selection working
- Mobile-friendly design

---

#### Task 4.2: Article Detail Page
**Objective:** Full article view with game context

**Route:**
```python
@bp.route('/newspaper/article/<int:article_id>')
def article_detail(article_id):
    """
    Individual article page.

    Display:
    - Full headline and body
    - Article metadata (date, author type)
    - Featured players (with links to player pages)
    - Game box score summary (if game_id present)
    - Related articles (same players or same game)

    Query:
    - Get article by ID
    - Get featured players from player_ids array
    - Get game summary if game_id present
    - Get related articles (same player_ids or game_id)
    """
```

**Template:** `templates/newspaper/article.html`

**Layout:**
```html
<div class="article-container max-w-4xl mx-auto px-4">
    <article>
        <!-- Headline -->
        <h1 class="text-4xl font-bold mb-4">{{ article.headline }}</h1>

        <!-- Metadata -->
        <div class="text-sm text-gray-600 mb-6">
            {{ article.article_date }} |
            {% if article.article_type == 'game_recap_branch' %}
                Generated by {{ article.model_used }}
            {% else %}
                Written by Jay Branch
            {% endif %}
        </div>

        <!-- Body -->
        <div class="article-body text-lg leading-relaxed mb-8">
            {{ article.body | safe }}
        </div>

        <!-- Featured Players -->
        <div class="featured-players mb-8">
            <h3 class="font-bold mb-2">Featured Players:</h3>
            {% for player in featured_players %}
                <a href="{{ url_for('players.player_detail', player_id=player.player_id) }}">
                    {{ player.first_name }} {{ player.last_name }}
                </a>
            {% endfor %}
        </div>

        <!-- Box Score Summary (if game_id) -->
        {% if box_score %}
        <div class="box-score mb-8">
            <h3 class="font-bold mb-2">Game Summary</h3>
            {{ box_score | safe }}
        </div>
        {% endif %}

        <!-- Related Articles -->
        {% if related_articles %}
        <div class="related-articles">
            <h3 class="font-bold mb-2">Related Articles:</h3>
            <ul>
                {% for related in related_articles %}
                <li>
                    <a href="{{ url_for('newspaper.article_detail', article_id=related.article_id) }}">
                        {{ related.headline }}
                    </a>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </article>
</div>
```

**Box Score Integration:**
```python
def get_box_score_summary(game_id):
    """
    Generate simple box score HTML from games table.

    Display:
    - Final score
    - Hits, errors
    - Winning/losing/save pitchers
    - Link to full game page (future)
    """
```

**Deliverables:**
- Article detail route and template
- Related articles query working
- Box score summary integration
- Player links functional

---

#### Task 4.3: Player Article Archive
**Objective:** List all articles featuring a specific player

**Route:**
```python
@bp.route('/newspaper/player/<int:player_id>')
def player_articles(player_id):
    """
    All articles mentioning a specific player.

    Query:
    - WHERE player_id = ANY(player_ids)
    - Order by article_date DESC
    - Published only

    Display:
    - Player name and bio summary
    - Chronological list of articles
    - Count of articles
    """
```

**Template:** `templates/newspaper/player_articles.html`

**Integration with Main Site:**
- Add "Newspaper Articles" tab to player detail pages
- Show article count badge
- Link to `/newspaper/player/<player_id>`

**Deliverables:**
- Player archive route and template
- Integration link on player pages
- Functional article list

---

#### Task 4.4: Team Article Archive
**Objective:** List all articles featuring a specific team

**Route:**
```python
@bp.route('/newspaper/team/<int:team_id>')
def team_articles(team_id):
    """
    All articles mentioning a specific team.
    Similar to player archive.
    """
```

**Deliverables:**
- Team archive route and template
- Integration link on team pages

---

### Phase 5: Messages Integration

#### Task 5.1: Messages Table Analysis and Mapping
**Objective:** Understand messages data and map to newspaper content

**Analysis Steps:**
1. Once messages data is populated, analyze:
   - `message_type` codes and meanings
   - `importance` and `hype` distributions
   - `subject` patterns
   - `body` content quality

2. Determine filtering criteria:
   - Which message_types are suitable for newspaper?
   - Minimum importance/hype threshold
   - Text quality checks (length, formatting)

**Mapping:**
```python
# In config or constants file
NEWSPAPER_WORTHY_MESSAGE_TYPES = [
    1,   # Trade announcements
    5,   # Award winners
    12,  # Milestone achievements
    # ... (to be determined from data)
]

MINIMUM_IMPORTANCE = 5
MINIMUM_HYPE = 3
```

**Deliverables:**
- Documentation: `docs/messages-analysis.md`
- Message type mapping defined
- Filtering criteria established

---

#### Task 5.2: Messages Importer
**Objective:** Import suitable messages as newspaper articles

**Location:** `etl/src/newspaper/messages_importer.py`

**Key Functions:**
```python
def import_newsworthy_messages(date_range=None):
    """
    Query messages table for newspaper-worthy content.

    Filters:
    - message_type in NEWSPAPER_WORTHY_MESSAGE_TYPES
    - importance >= MINIMUM_IMPORTANCE
    - hype >= MINIMUM_HYPE
    - body length >= 100 chars
    - Not already imported (check by message_id reference)

    For each message:
    - Create article record
    - article_type = 'message_reprint'
    - headline = subject
    - body = message body
    - player_ids = [player_id_0, ..., player_id_9] (exclude NULLs)
    - team_ids = [team_id_0, ..., team_id_4]
    - status = 'published' (auto-publish messages)
    - Store message_id reference for deduplication

    Returns: Count of imported messages
    """
```

**HTML Linking:**
```python
def process_message_links(body_text, player_ids, team_ids):
    """
    Convert player/team IDs to hyperlinks in message body.

    Strategy:
    - Fetch player/team names from IDs
    - Find name mentions in body text
    - Replace with <a> tags linking to player/team pages

    Returns: HTML with links
    """
```

**Schema Extension:**
Add to `newspaper_articles`:
```sql
ALTER TABLE newspaper_articles
ADD COLUMN source_message_id INT REFERENCES messages(message_id);

CREATE INDEX idx_articles_message_id ON newspaper_articles(source_message_id);
```

**ETL Integration:**
Add to `etl/main.py` after Branch article generation:
```python
from src.newspaper.messages_importer import import_newsworthy_messages

results = import_newsworthy_messages(date_range=(etl_start_date, etl_end_date))
logger.info(f"Imported {results} messages as articles")
```

**Deliverables:**
- `messages_importer.py` created
- Schema migration for source_message_id
- ETL integration complete
- Messages appearing in newspaper feed

---

#### Task 5.3: Message Article Styling
**Objective:** Distinct visual styling for message reprints

**Template Updates:**
Modify `newspaper/index.html` and `article.html`:

```html
<!-- In article list/grid -->
{% if article.article_type == 'message_reprint' %}
    <div class="message-reprint border-l-4 border-blue-500 pl-4">
        <!-- Article content with "From the Wire" badge -->
    </div>
{% else %}
    <!-- Regular article styling -->
{% endif %}
```

**CSS Additions:**
- Different border color for reprints
- "From the Wire" or "League News" badge
- Lighter background color
- Smaller font size (optional)

**Deliverables:**
- Visual distinction for message reprints
- Consistent styling across homepage and detail pages

---

### Phase 6: Enhancements (Optional/Future)

#### Task 6.1: Box Score Fetching
**Objective:** Retrieve box score HTML files from game machine

**Location:** `etl/src/fetchers/box_score_fetcher.py`

**Implementation:**
- Extend existing fetch script infrastructure
- Fetch pattern: `game_box_<game_id>.html`
- Store in `etl/data/incoming/box_scores/`
- Parse or serve as-is

**Use Cases:**
1. Embed in article detail pages
2. Parse for additional LLM prompt context
3. Link from articles

**Deliverables:**
- Box score fetching integrated
- Storage and access working
- Optional: Parser for key stats

---

#### Task 6.2: Career Context Integration
**Objective:** Add season/career stats to article prompts

**Enhancement to `prompt_builder.py`:**
```python
def add_career_context(player_id, game_date):
    """
    Add season stats to prompt:
    - Current batting average
    - Season HR/RBI totals
    - Recent streak (hitting, shutout, etc.)

    Example: "Branch improved to .312 on the season..."
    """
```

**Deliverables:**
- Career context in prompts
- More contextual articles

---

#### Task 6.3: Milestone Detection
**Objective:** Auto-detect career milestones and boost priority

**Enhancement to `newsworthiness.py`:**
```python
def check_milestones(player_id, game_stats):
    """
    Detect:
    - 500th, 1000th hit
    - 100th, 200th HR
    - 100th, 200th win
    - First career HR, win, save

    If milestone crossed in this game:
    - Boost newsworthiness to 95+
    - Flag as MUST_GENERATE
    - Use high-quality model
    """
```

**Deliverables:**
- Milestone detection working
- Milestones prioritized correctly

---

#### Task 6.4: Rivalry Context
**Objective:** Add head-to-head records to article prompts

**Enhancement:**
```python
def get_rivalry_context(team1_id, team2_id, current_date):
    """
    Fetch season head-to-head record.
    Include in prompt for added context.
    """
```

---

#### Task 6.5: Auto-Publish Based on Confidence
**Objective:** Trust high-scoring articles to auto-publish

**Logic:**
```python
def should_auto_publish(article, newsworthiness_score, validation_result):
    """
    Criteria for auto-publish:
    - Newsworthiness < 60 (routine games)
    - Validation passed with no issues
    - Model used is trusted (qwen2.5:14b or better)
    - Not a milestone (always review)

    Returns: bool
    """
```

**Implementation:**
In `article_processor.save_article()`:
- Check auto-publish criteria
- Set status='published' if criteria met
- Otherwise status='draft'

---

## Testing Strategy

### Unit Tests
- Branch game detection logic
- Newsworthiness scoring algorithm
- Article parsing and validation
- Ollama client retry logic

**Location:** `etl/tests/`

### Integration Tests
- Full pipeline with test data
- Database insert/query operations
- ETL trigger workflow

### Manual Testing
- Generate articles for known games
- Review article quality
- Test editorial workflow (approve, regenerate, reject)
- Test user content creation

### Performance Testing
- Benchmark model generation times
- Monitor database query performance
- Test with large batches (100+ games)

---

## Configuration Management

### Config Files

**`etl/config/newspaper_config.yaml`:**
```yaml
ollama:
  base_url: http://localhost:11434
  models:
    high_priority: qwen2.5:14b
    normal_priority: llama3.1:8b
  default_temperature: 0.7
  default_max_tokens: 400
  timeout: 120

generation:
  priority_thresholds:
    must_generate: 80
    should_generate: 50
    could_generate: 20
  auto_publish_threshold: 60  # Future use

archive:
  game_logs_path: etl/data/incoming/csv/game_logs.csv
  archive_path: etl/data/archive/game_logs/

messages:
  worthy_message_types: [1, 5, 12]
  minimum_importance: 5
  minimum_hype: 3
```

**Environment Variables:**
- Database credentials (existing)
- API keys (if using Claude fallback)

---

## Documentation Deliverables

1. **This file:** `docs/newspaper-implementation-plan.md`
2. **Model benchmarks:** `docs/ollama-model-benchmarks.md`
3. **Sample prompts:** `docs/sample-prompts.md`
4. **Messages analysis:** `docs/messages-analysis.md` (after data available)
5. **API documentation:** `docs/newspaper-api.md` (for admin routes)

---

## Dependencies and Installation

### Python Packages (add to requirements.txt)
```
requests>=2.31.0       # Ollama API calls
beautifulsoup4>=4.12.0 # Box score parsing (if needed)
```

### System Dependencies
- Ollama (install via official script)
- CUDA drivers (already present for RTX 4090)

### Installation Steps
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull initial models
ollama pull llama3.1:8b
ollama pull qwen2.5:14b

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
psql -h 192.168.10.94 -U ootp_etl -d ootp_dev -f scripts/migrations/001_create_newspaper_tables.sql
```

---

## Timeline Estimates

**Phase 1: Foundation** - 1-2 days
- Ollama setup: 2-4 hours
- Database schema: 2-3 hours
- Model testing: 3-4 hours

**Phase 2: Article Generation** - 4-5 days
- Branch detection: 1 day
- game_logs parser: 1-2 days
- Prompt builder: 1 day
- Ollama client: 1 day
- Pipeline integration: 1 day

**Phase 3: Editorial & User Input** - 3-4 days
- Editorial interface: 2 days
- User content form: 1-2 days

**Phase 4: Frontend Display** - 3-4 days
- Homepage layout: 1-2 days
- Article detail: 1 day
- Archives: 1 day

**Phase 5: Messages Integration** - 2-3 days
- Analysis: 1 day (after data available)
- Importer: 1 day
- Styling: 0.5 day

**Total Estimated Time:** 13-18 days (concentrated development)

---

## Success Criteria

### MVP (Minimum Viable Product)
- [x] Ollama running with at least one model
- [ ] Database schema created
- [ ] ETL detects Branch games and generates articles
- [ ] Articles saved as drafts
- [ ] Editorial review interface functional
- [ ] Articles publish to newspaper homepage
- [ ] User can create manual articles

### Full Feature Set
- [ ] Multiple models tested and configured
- [ ] game_logs parser extracts play-by-play details
- [ ] High-quality prompts generate readable articles
- [ ] Editorial workflow includes regeneration
- [ ] Messages integrated as filler content
- [ ] Responsive newspaper layout
- [ ] Player/team article archives

### Quality Metrics
- Article generation success rate: >90%
- Average generation time: <30 seconds (for 8B models)
- Editorial rejection rate: <20% (after tuning prompts)
- User satisfaction with article quality (subjective)

---

## Risk Mitigation

### Risk: LLM hallucinations (incorrect stats/names)
**Mitigation:**
- Strict validation in `article_processor.py`
- Editorial review before publishing
- Provide highly structured prompts with explicit data
- Test with known games and verify accuracy

### Risk: Slow generation times
**Mitigation:**
- Use smaller models for routine games
- Run generation asynchronously (background job)
- Benchmark and optimize model selection

### Risk: Ollama service downtime
**Mitigation:**
- Retry logic with exponential backoff
- Log failures for manual review
- Consider cloud API fallback (Claude) for critical articles

### Risk: Poor article quality
**Mitigation:**
- Prompt engineering and iteration
- Test multiple models
- Editorial review process
- Regeneration option with feedback

### Risk: game_logs.csv growth
**Mitigation:**
- Implement archival strategy (Task 2.2)
- Extract Branch moments to database
- Prune historical data annually

---

## Future Enhancements (Beyond MVP)

1. **Advanced Analytics Integration**
   - Include WPA, xBA, spin rate in articles
   - Modern analytics for contemporary seasons

2. **Multi-Language Support**
   - Generate articles in Spanish
   - Use multilingual models

3. **Audio Articles**
   - Text-to-speech for podcast-style delivery
   - Integration with audio players

4. **Social Media Integration**
   - Auto-post headlines to Twitter/X
   - Generate social-friendly summaries

5. **Reader Comments**
   - Allow user comments on articles
   - Moderation workflow

6. **Newsletter Integration**
   - Email digest of weekly articles
   - Subscription management

7. **Advanced Search**
   - Full-text search across articles
   - Filter by date range, player, team, article type

8. **Article Analytics**
   - Track views, reading time
   - Popular articles dashboard

---

## Appendix: Code Organization

### New Directories
```
etl/src/newspaper/
├── __init__.py
├── branch_detector.py
├── newsworthiness.py
├── game_context.py
├── game_log_parser.py
├── game_log_archiver.py
├── prompt_builder.py
├── ollama_client.py
├── article_processor.py
├── messages_importer.py
└── pipeline.py

etl/tests/
├── test_branch_detector.py
├── test_newsworthiness.py
├── test_ollama_client.py
└── test_article_processor.py

etl/config/
└── newspaper_config.yaml

web/app/routes/
├── newspaper.py        # Public routes
└── newspaper_admin.py  # Admin routes

web/app/templates/newspaper/
├── index.html
├── article.html
├── player_articles.html
├── team_articles.html
└── admin/
    ├── drafts.html
    ├── review.html
    └── create.html

scripts/migrations/
├── 001_create_newspaper_tables.sql
└── 002_add_message_source_column.sql
```

---

## Appendix: Database Schema Reference

See **Phase 1, Task 1.2** for complete schema definitions.

**Key Tables:**
- `newspaper_articles` - All article content and metadata
- `branch_game_moments` - Extracted play-by-play for Branch players
- `messages` - Source data for reprints (existing table)

**Key Relationships:**
- `newspaper_articles.game_id` → `games.game_id`
- `newspaper_articles.player_ids[]` → `players_core.player_id` (array)
- `newspaper_articles.source_message_id` → `messages.message_id`
- `branch_game_moments.player_id` → `players_core.player_id`

---

## Contact and Support

**Project Lead:** Jay (user)
**Development Tool:** Claude Code
**Architecture Decisions:** @architect subagent

For implementation questions, refer to:
- This document for overall plan
- `docs/newspaper-brainstorm.md` for technical details
- `docs/WEBSITE-SPECS.MD` for UI/UX guidelines

---

## Session Notes

### Session: 2025-10-21
**Focus:** Phase 3 Enhancement - Article Image Support

**Completed:**
- ✅ **Article Image Support** - Enhanced Task 3.2 (User Content Creation Interface)
  - Database: Created `article_images` table with three image types:
    - `player`: Player pictures from `etl/data/images/players/player_{id}.png`
    - `team_logo`: Team logos from `etl/data/images/team_logos/{name}_{nickname}_{size}.png`
    - `uploaded`: Custom uploads in `web/app/static/uploads/articles/`
  - Backend: ArticleImage model, image serving route `/etl-images/<path>`, upload handling
  - Frontend: Three-tab UI (Player Pictures, Team Logos, Upload Custom) with dynamic updates
  - Display: Images shown between byline and body with vintage newspaper styling
  - Migration: `etl/sql/migrations/003_article_images.sql` + updated DDL in `07_newspaper.sql`

- ✅ **Bug Fixes:**
  - Fixed team logo path construction to include both name and nickname
  - Fixed slug generation to remove punctuation (periods, commas, etc.)

- ✅ **Homepage Widget Optimization** - "Born This Week"
  - Reduced from 50 to 12 players
  - Added WAR-based ordering (total career batting + pitching WAR)
  - Updated both normal and year-wraparound query variants
  - Performance: Minimal impact due to LIMIT 12 and 24-hour caching

**Files Modified:**
- `web/app/models/newspaper.py` - Added ArticleImage model
- `web/app/routes/main.py` - Added `/etl-images/<path>` serving route
- `web/app/routes/newspaper_admin.py` - Added image upload handling, fixed slug generation
- `web/app/templates/newspaper/admin/create.html` - Added image selection UI
- `web/app/templates/newspaper/article.html` - Added image display
- `web/app/services/player_service.py` - Optimized `get_players_born_this_week()`
- `etl/sql/tables/07_newspaper.sql` - Added article_images table DDL

**Next Steps:**
- Phase 4: Consider implementing deferred tasks (Player/Team article archives)
- Phase 2: Begin article generation pipeline integration

---

**Document Version:** 1.1
**Last Updated:** 2025-10-21
**Status:** Phase 3 Complete with Enhancements