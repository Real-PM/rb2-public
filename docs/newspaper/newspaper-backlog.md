# Newspaper Section - Development Backlog

**Related Documents:**
- `docs/newspaper-implementation-plan.md` - Comprehensive implementation plan
- `docs/newspaper-brainstorm.md` - Technical specifications and code examples

**Status Legend:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Completed
- 🔵 Blocked/On Hold

---

## Phase 1: Foundation

### 1.1 Ollama Infrastructure Setup
**Status:** 🔴 Not Started
**Priority:** Critical
**Estimated Effort:** 4 hours

**Tasks:**
- [ ] Check if Ollama is installed on dev machine
- [ ] Install Ollama if not present
- [ ] Configure Ollama as systemd service (optional)
- [ ] Pull test models: `llama3.1:8b`, `qwen2.5:14b`
- [ ] Optional: Pull `llama3.1:70b` for high-priority article testing
- [ ] Test basic generation with sample prompt
- [ ] Document GPU utilization (nvidia-smi monitoring)

**Deliverables:**
- Ollama running and accessible at `http://localhost:11434`
- At least 2 models available for testing

**Notes:**
- Dev machine specs: i9-14900KF, 64GB RAM, RTX 4090 (24GB VRAM)
- Can run 70B models with GPU + CPU offloading
- Start with 8B and 14B models for speed

---

### 1.2 Model Benchmarking and Selection
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** 3-4 hours
**Dependencies:** Task 1.1

**Tasks:**
- [ ] Create benchmark test script
- [ ] Generate sample prompts based on real game data
- [ ] Test `llama3.1:8b` with identical prompts
- [ ] Test `qwen2.5:14b` with identical prompts
- [ ] Optional: Test `llama3.1:70b` for comparison
- [ ] Measure generation time for each model
- [ ] Evaluate article quality (readability, accuracy, style)
- [ ] Document optimal parameters (temperature, top_p, max_tokens)
- [ ] Select primary models for high/normal priority articles

**Deliverables:**
- `docs/ollama-model-benchmarks.md` with results
- `etl/config/newspaper_config.yaml` with model selections
- Sample generated articles for review

**Benchmark Criteria:**
- Generation time (target: <30s for 8B, <60s for 14B)
- Article quality score (subjective 1-10 rating)
- Factual accuracy (verify stats match game data)
- Style adherence (journalistic, period-appropriate)

---

### 1.3 Database Schema Creation
**Status:** 🔴 Not Started
**Priority:** Critical
**Estimated Effort:** 2-3 hours

**Tasks:**
- [ ] Create migration script: `scripts/migrations/001_create_newspaper_tables.sql`
- [ ] Define `newspaper_articles` table with all columns
- [ ] Define `branch_game_moments` table
- [ ] Add indexes for performance
- [ ] Add constraints (valid_score, valid_status)
- [ ] Run migration on `ootp_dev` database
- [ ] Verify tables created successfully
- [ ] Test insert/query operations
- [ ] Document schema in `docs/DATA-MODEL.MD`

**Deliverables:**
- `newspaper_articles` table created
- `branch_game_moments` table created
- All indexes and constraints in place
- Schema documentation updated

**Schema Highlights:**
- `newspaper_articles`: Main article storage with editorial workflow columns
- `branch_game_moments`: Extracted play-by-play for Branch players
- Player/team IDs stored as PostgreSQL arrays
- Status workflow: draft → published/rejected

---

## Phase 2: Article Generation Pipeline

### 2.1 Branch Family Game Detection
**Status:** 🔴 Not Started
**Priority:** Critical
**Estimated Effort:** 1 day
**Dependencies:** Task 1.3

**Tasks:**
- [ ] Create `etl/src/newspaper/` module structure
- [ ] Implement `branch_detector.py`:
  - [ ] `get_branch_family_ids()` - Query Branch family members
  - [ ] `detect_branch_games()` - Scan batting/pitching stats
  - [ ] `detect_multi_branch_games()` - Find Branch vs Branch games
- [ ] Implement `newsworthiness.py`:
  - [ ] `calculate_newsworthiness()` - Scoring algorithm
  - [ ] `prioritize_games()` - Assign priority tiers
- [ ] Implement `game_context.py`:
  - [ ] `get_game_context()` - Fetch game metadata
  - [ ] `get_branch_player_details()` - Get player stats
- [ ] Create unit tests: `etl/tests/test_branch_detector.py`
- [ ] Test with real game data
- [ ] Verify multi-Branch game detection works

**Deliverables:**
- `etl/src/newspaper/` module created
- Branch game detection working
- Newsworthiness scoring accurate
- Unit tests passing

**Newsworthiness Scoring:**
- MUST_GENERATE (≥80): Multi-HR, shutout, no-hitter, milestones
- SHOULD_GENERATE (50-79): Quality start, 3+ hit game, save
- COULD_GENERATE (20-49): 2-hit game, relief win
- SKIP (<20): Minimal performance

---

### 2.2 game_logs.csv Parser
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** 1-2 days
**Dependencies:** Task 2.1

**Tasks:**
- [ ] Implement `game_log_parser.py`:
  - [ ] `extract_branch_plays_from_game_log()` - Parse CSV for Branch plays
  - [ ] `structure_branch_at_bats()` - Convert to at-bat summaries
  - [ ] `save_branch_moments_to_db()` - Store in database
- [ ] Implement `game_log_archiver.py`:
  - [ ] `prune_game_logs()` - Archive historical data
  - [ ] `get_game_log_from_archive()` - Retrieve archived logs
- [ ] Test with real game_logs.csv data
- [ ] Verify play-by-play extraction accuracy
- [ ] Test archival and retrieval process
- [ ] Handle edge cases (extra innings, pinch hitters)

**Deliverables:**
- `game_log_parser.py` functional
- `game_log_archiver.py` functional
- Branch moments extracted and stored
- Archival strategy documented

**Parsing Strategy:**
- Filter by game_id and Branch player mentions
- Extract pitch sequences, outcomes, exit velocity
- Maintain context (5 lines before/after)
- Store in `branch_game_moments` for regeneration

**Challenge:**
- game_logs.csv is 665K lines, 36MB
- Need efficient parsing (don't load entire file)
- Archive strategy to prevent unbounded growth

---

### 2.3 LLM Prompt Builder
**Status:** 🔴 Not Started
**Priority:** Critical
**Estimated Effort:** 1 day
**Dependencies:** Task 2.1, 2.2

**Tasks:**
- [ ] Implement `prompt_builder.py`:
  - [ ] `build_article_prompt()` - Single Branch player game
  - [ ] `build_multi_branch_prompt()` - Multiple Branch players
  - [ ] `build_regeneration_prompt()` - Refinement with feedback
- [ ] Create prompt templates with structured format
- [ ] Add style guidelines (1960s journalistic language)
- [ ] Add output format instructions (HEADLINE: / body)
- [ ] Test prompts manually with Ollama
- [ ] Iterate on prompt quality based on output
- [ ] Document prompt engineering decisions
- [ ] Create `docs/sample-prompts.md` with examples

**Deliverables:**
- `prompt_builder.py` complete
- High-quality prompts generating good articles
- Sample prompts documented

**Prompt Components:**
- Game metadata (teams, score, date, attendance)
- Branch player stats (batting/pitching line)
- Play-by-play details (if available)
- Style instructions (past tense, factual, engaging)
- Word count target (200-250 words)
- Output format specification

**Prompt Engineering Goals:**
- Factual accuracy (no hallucinations)
- Period-appropriate language
- Engaging narrative style
- Consistent structure

---

### 2.4 Ollama Client Implementation
**Status:** 🔴 Not Started
**Priority:** Critical
**Estimated Effort:** 1 day
**Dependencies:** Task 1.2, 2.3

**Tasks:**
- [ ] Implement `ollama_client.py`:
  - [ ] `OllamaClient` class with configurable endpoint
  - [ ] `generate_article()` - Call /api/generate
  - [ ] `generate_with_retry()` - Retry logic with backoff
  - [ ] `check_model_availability()` - Verify model exists
  - [ ] `benchmark_model()` - Testing utility
- [ ] Create `etl/config/newspaper_config.yaml`
- [ ] Configure model selection based on priority
- [ ] Implement error handling (network, timeout, parse errors)
- [ ] Add logging for generation time and failures
- [ ] Create unit tests: `etl/tests/test_ollama_client.py`
- [ ] Test with various failure scenarios

**Deliverables:**
- `ollama_client.py` functional
- Config file created
- Retry logic working
- Error handling robust

**Configuration:**
```yaml
ollama:
  base_url: http://localhost:11434
  models:
    high_priority: qwen2.5:14b
    normal_priority: llama3.1:8b
  timeout: 120
  max_retries: 3
```

**Error Handling:**
- Network error → Retry with exponential backoff
- Model not found → Fallback to smaller model
- Timeout → Log and mark article as failed
- Malformed response → Log raw output for debugging

---

### 2.5 Article Parser and Storage
**Status:** 🔴 Not Started
**Priority:** Critical
**Estimated Effort:** 1 day
**Dependencies:** Task 2.4

**Tasks:**
- [ ] Implement `article_processor.py`:
  - [ ] `parse_article_output()` - Extract headline/body
  - [ ] `validate_article()` - Quality checks
  - [ ] `save_article()` - Store in database
  - [ ] `regenerate_article()` - Create new version with feedback
- [ ] Define validation rules:
  - [ ] Headline length (10-255 chars)
  - [ ] Body word count (150-300 words)
  - [ ] Player/team name accuracy
  - [ ] Score accuracy
- [ ] Create unit tests: `etl/tests/test_article_processor.py`
- [ ] Test with sample LLM outputs
- [ ] Verify database storage works

**Deliverables:**
- `article_processor.py` functional
- Validation rules working
- Articles stored correctly
- Regeneration capability working

**Validation Checks:**
- Headline present and reasonable length
- Body within word count range
- No obvious hallucinations (fuzzy match player/team names)
- Score matches game_context

**Database Fields:**
- status: 'draft' (always for now)
- generation_method: 'llm_ollama'
- model_used: Model name used
- newsworthiness_score: Priority score
- generation_count: Track regenerations
- previous_version_id: Link to original if regenerated

---

### 2.6 End-to-End Pipeline Integration
**Status:** 🔴 Not Started
**Priority:** Critical
**Estimated Effort:** 1 day
**Dependencies:** Tasks 2.1-2.5

**Tasks:**
- [ ] Implement `pipeline.py`:
  - [ ] `generate_branch_articles_pipeline()` - Main orchestration
  - [ ] Handle date_range parameter for incremental processing
  - [ ] Check for existing articles (skip unless force_regenerate)
  - [ ] Loop through prioritized games
  - [ ] Gather context, build prompts, generate, validate, save
  - [ ] Return summary statistics
- [ ] Integrate with ETL `main.py`:
  - [ ] Add post-update hook
  - [ ] Call pipeline after successful data import
  - [ ] Pass date_range from ETL run
  - [ ] Log results
- [ ] Test end-to-end with real data
- [ ] Verify articles appear in database
- [ ] Handle failures gracefully (don't break ETL)

**Deliverables:**
- `pipeline.py` complete
- ETL integration working
- Articles generated automatically on update
- Error handling prevents ETL failures

**Pipeline Flow:**
1. Get Branch family IDs
2. Detect Branch games in date_range
3. Check for existing articles
4. Prioritize by newsworthiness
5. Filter to MUST/SHOULD generate
6. For each game:
   - Gather context
   - Extract plays
   - Build prompt
   - Select model
   - Generate article
   - Validate
   - Save as draft
7. Return summary (generated, failed, skipped)

---

## Phase 3: Editorial & User Input

### 3.1 Editorial Review Interface - Draft List
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** 1 day
**Dependencies:** Task 2.6

**Tasks:**
- [ ] Create `web/app/routes/newspaper_admin.py` blueprint
- [ ] Implement `/newspaper/admin/drafts` route
- [ ] Create `templates/newspaper/admin/drafts.html`
- [ ] Display draft articles in table/grid:
  - [ ] Headline
  - [ ] Game info (teams, score, date)
  - [ ] Featured players
  - [ ] Newsworthiness score
  - [ ] Generation metadata (model, time)
  - [ ] Actions: [Review] [Delete]
- [ ] Add sorting (by score, date)
- [ ] Add basic authentication (Flask-Login or HTTP auth)
- [ ] Register blueprint in `app/__init__.py`
- [ ] Test with generated drafts

**Deliverables:**
- Admin blueprint created
- Draft list page functional
- Authentication working
- Can view all draft articles

**UI Features:**
- Table with sortable columns
- Quick preview of article text
- Color-coded priority (red=MUST, yellow=SHOULD)
- Click headline to go to review page

---

### 3.2 Editorial Review Interface - Review Page
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** 1 day
**Dependencies:** Task 3.1

**Tasks:**
- [ ] Implement `/newspaper/admin/review/<article_id>` route
- [ ] Create `templates/newspaper/admin/review.html`
- [ ] Display full article with formatting
- [ ] Display game context and box score summary
- [ ] Display featured player stats
- [ ] Add action buttons:
  - [ ] [Publish] - Update status, set reviewed_by/reviewed_at
  - [ ] [Regenerate] - Show feedback form modal
  - [ ] [Edit] - Inline editing (future enhancement - skip for MVP)
  - [ ] [Reject] - Update status to rejected
- [ ] Implement publish handler route
- [ ] Implement regenerate handler route
- [ ] Implement reject handler route
- [ ] Test all actions

**Deliverables:**
- Review page functional
- All actions working
- Published articles appear on public site
- Regeneration creates new draft version

**Review Page Layout:**
- Full article preview (as it will appear)
- Metadata sidebar (score, model, generation time)
- Action buttons at top and bottom
- Related game info below article

---

### 3.3 Article Regeneration with Feedback
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 4 hours
**Dependencies:** Task 3.2

**Tasks:**
- [ ] Create regenerate feedback form (modal or separate page)
- [ ] Implement `build_regeneration_prompt()` in prompt_builder.py
- [ ] Implement regeneration route handler:
  - [ ] Accept feedback text
  - [ ] Call article_processor.regenerate_article()
  - [ ] Generate new version with refinement prompt
  - [ ] Save with previous_version_id link
  - [ ] Increment generation_count
  - [ ] Redirect to review page for new version
- [ ] Test regeneration workflow
- [ ] Verify version tracking works

**Deliverables:**
- Regeneration form working
- Feedback incorporated into prompt
- New version created and linked
- Can compare versions

**Feedback Examples:**
- "Focus more on the winning pitcher's performance"
- "Make the tone more exciting"
- "Include more details about the key at-bat"

---

### 3.4 User Content Creation Interface
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** 1-2 days
**Dependencies:** Task 3.1

**Tasks:**
- [ ] Implement `/newspaper/admin/create` route (GET/POST)
- [ ] Create `templates/newspaper/admin/create.html`
- [ ] Add form fields:
  - [ ] article_type dropdown (journal_entry, historical_article)
  - [ ] article_date date picker
  - [ ] headline text input
  - [ ] body rich text editor (TinyMCE integration)
  - [ ] player_mentions autocomplete multi-select
  - [ ] team_mentions autocomplete multi-select
  - [ ] game_link optional dropdown
- [ ] Implement autocomplete API endpoints:
  - [ ] `/api/players/search` - Search players by name
  - [ ] `/api/teams/search` - Search teams by name/abbr
- [ ] Integrate TinyMCE or similar editor
- [ ] Implement save handler:
  - [ ] Parse autocomplete selections
  - [ ] Store player_ids/team_ids arrays
  - [ ] Save article with status='published'
  - [ ] Redirect to article detail page
- [ ] Test full workflow

**Deliverables:**
- Create article form functional
- Rich text editor working
- Autocomplete working for players/teams
- User articles saved and published
- Player/team IDs stored correctly

**Autocomplete Implementation:**
- Use Select2 or similar JavaScript library
- AJAX calls to search endpoints
- Tag-style multi-select UI
- Store selected IDs in hidden form fields

**Rich Text Editor:**
- TinyMCE recommended (easy integration)
- Toolbar: Bold, italic, paragraph, links, lists
- Character/word counter
- Paste cleanup

---

## Phase 4: Frontend Display

### 4.1 Newspaper Homepage Layout
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** 1-2 days
**Dependencies:** Task 2.6 (need published articles)

**Tasks:**
- [ ] Create `web/app/routes/newspaper.py` blueprint (public routes)
- [ ] Implement `/newspaper` homepage route
- [ ] Create `templates/newspaper/index.html`
- [ ] Implement hero article selection logic:
  - [ ] Highest newsworthiness from last 7 days
  - [ ] Fallback to most recent if no high-priority
- [ ] Implement article grid query:
  - [ ] Recent published articles (last 30 days)
  - [ ] Sort by date DESC, newsworthiness DESC
  - [ ] Pagination (20 per page)
- [ ] Design responsive layout:
  - [ ] Desktop: Hero + 3-column grid
  - [ ] Tablet: Hero + 2-column grid
  - [ ] Mobile: Hero + 1-column stack
- [ ] Apply newspaper-style typography:
  - [ ] Serif fonts (Georgia)
  - [ ] Clean hierarchy
  - [ ] Print-inspired aesthetic
- [ ] Register blueprint
- [ ] Test responsive behavior

**Deliverables:**
- Newspaper homepage functional
- Hero article auto-selected
- Responsive layout working
- Newspaper aesthetic styling

**Layout Features:**
- Hero article with large headline and preview
- Grid of recent articles with headlines and excerpts
- "Read more" links to full articles
- Simple navigation (filter by type, date range - future)

---

### 4.2 Article Detail Page
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** 1 day
**Dependencies:** Task 4.1

**Tasks:**
- [ ] Implement `/newspaper/article/<article_id>` route
- [ ] Create `templates/newspaper/article.html`
- [ ] Display full article content:
  - [ ] Headline
  - [ ] Article date
  - [ ] Author info (AI-generated vs user-written)
  - [ ] Full body text with formatting
- [ ] Display featured players section:
  - [ ] Query players from player_ids array
  - [ ] Link to player detail pages
- [ ] Display game summary (if game_id present):
  - [ ] Final score
  - [ ] Hits, errors
  - [ ] W/L/S pitchers
  - [ ] Optional: Link to full box score
- [ ] Display related articles:
  - [ ] Same player_ids or game_id
  - [ ] Limit to 5 most recent
- [ ] Add social sharing buttons (optional)
- [ ] Test with various article types

**Deliverables:**
- Article detail page functional
- Featured players linked correctly
- Game context displayed
- Related articles showing

**Page Structure:**
- Clean, readable typography
- Newspaper article styling
- Metadata at top (date, author)
- Related content at bottom
- Breadcrumb navigation

---

### 4.3 Player Article Archive
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 4 hours
**Dependencies:** Task 4.2

**Tasks:**
- [ ] Implement `/newspaper/player/<player_id>` route
- [ ] Create `templates/newspaper/player_articles.html`
- [ ] Query articles where player_id in player_ids array
- [ ] Display player name and bio summary
- [ ] List articles chronologically
- [ ] Add article count
- [ ] Integrate with main player detail page:
  - [ ] Add "Newspaper Articles" tab or section
  - [ ] Show count badge
  - [ ] Link to player archive
- [ ] Test with various players

**Deliverables:**
- Player archive page functional
- Integration on player pages working
- Article count accurate

**Page Features:**
- Player header with photo and basic info
- Chronological article list
- Preview excerpts
- Pagination if many articles

---

### 4.4 Team Article Archive
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 4 hours
**Dependencies:** Task 4.2

**Tasks:**
- [ ] Implement `/newspaper/team/<team_id>` route
- [ ] Create `templates/newspaper/team_articles.html`
- [ ] Query articles where team_id in team_ids array
- [ ] Display team name and logo
- [ ] List articles chronologically
- [ ] Integrate with team pages:
  - [ ] Add "News" tab
  - [ ] Link to team archive
- [ ] Test with various teams

**Deliverables:**
- Team archive page functional
- Integration on team pages working

**Page Features:**
- Team header with logo
- Chronological article list
- Filter by season (future)

---

### 4.5 Navigation and Homepage Integration
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 2 hours
**Dependencies:** Task 4.1

**Tasks:**
- [ ] Add "Newspaper" link to main site navigation
- [ ] Add newspaper section to homepage:
  - [ ] "Latest from the Chronicle" section
  - [ ] 3 most recent articles with headlines
  - [ ] "View all articles" link to /newspaper
- [ ] Update breadcrumb navigation
- [ ] Add meta tags for SEO (optional)
- [ ] Test navigation flow

**Deliverables:**
- Newspaper accessible from main nav
- Homepage integration working
- Navigation consistent across site

---

## Phase 5: Messages Integration

### 5.1 Messages Table Analysis
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 1 day
**Dependencies:** Messages table populated with data

**Tasks:**
- [ ] Wait for messages data to be imported
- [ ] Analyze message_type codes and meanings
- [ ] Analyze importance and hype distributions
- [ ] Review subject patterns
- [ ] Assess body content quality and length
- [ ] Determine filtering criteria:
  - [ ] Which message_types suitable for newspaper
  - [ ] Minimum importance threshold
  - [ ] Minimum hype threshold
  - [ ] Text quality requirements
- [ ] Document findings in `docs/messages-analysis.md`
- [ ] Define constants for filtering

**Deliverables:**
- `docs/messages-analysis.md` created
- Message type mapping documented
- Filtering criteria defined
- Constants defined in config

**Analysis Questions:**
- What message_types exist? (trades, awards, injuries, etc.)
- Which have journalistic value?
- What's the quality distribution?
- How many messages per season?

---

### 5.2 Messages Importer Implementation
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 1 day
**Dependencies:** Task 5.1, Task 1.3

**Tasks:**
- [ ] Add source_message_id column to newspaper_articles:
  - [ ] Create migration: `002_add_message_source_column.sql`
  - [ ] Run migration
- [ ] Implement `etl/src/newspaper/messages_importer.py`:
  - [ ] `import_newsworthy_messages()` - Main function
  - [ ] `process_message_links()` - Convert IDs to hyperlinks
- [ ] Define filtering constants in config
- [ ] Implement deduplication (check source_message_id)
- [ ] Integrate with ETL pipeline (run after Branch article generation)
- [ ] Test with real messages data
- [ ] Verify articles created correctly

**Deliverables:**
- `messages_importer.py` functional
- Schema migration complete
- Messages imported as articles
- Player/team links working

**Import Logic:**
```python
def import_newsworthy_messages(date_range=None):
    # Query messages with filters
    # For each message:
    #   - Check if already imported (source_message_id)
    #   - Create article record
    #   - article_type = 'message_reprint'
    #   - status = 'published'
    #   - Process player/team links in body
    #   - Save
```

**Linking Strategy:**
- Fetch player/team names from IDs
- Find name mentions in body text
- Replace with `<a href="/player/123">Name</a>` tags
- Store processed HTML in body field

---

### 5.3 Message Article Styling
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** 2 hours
**Dependencies:** Task 5.2

**Tasks:**
- [ ] Update `templates/newspaper/index.html`:
  - [ ] Add conditional styling for message_reprint type
  - [ ] Different border/background for reprints
- [ ] Update `templates/newspaper/article.html`:
  - [ ] Show "From the Wire" or "League News" badge
  - [ ] Different styling for reprint articles
- [ ] Define CSS classes for message reprints
- [ ] Test visual distinction
- [ ] Ensure consistent across all newspaper pages

**Deliverables:**
- Visual distinction for message reprints
- Consistent styling across pages
- "From the Wire" badge displaying

**Styling Ideas:**
- Blue left border for reprints (vs black for articles)
- Lighter background color
- "League News" badge in header
- Slightly smaller font (optional)

---

## Phase 6: Enhancements (Optional/Future)

### 6.1 Box Score Fetching Integration
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** 1 day

**Tasks:**
- [ ] Extend fetch script to retrieve box score HTML files
- [ ] Pattern: `game_box_<game_id>.html`
- [ ] Store in `etl/data/incoming/box_scores/`
- [ ] Create parser for key stats (optional)
- [ ] Integrate into article detail page:
  - [ ] Embed box score HTML, or
  - [ ] Link to box score, or
  - [ ] Extract key stats for summary
- [ ] Test with real box score files

**Deliverables:**
- Box score fetching working
- Display on article pages (if desired)

**Use Cases:**
- Embed full box score in article
- Link to box score from article
- Parse for additional LLM context

---

### 6.2 Career Context in Prompts
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 4 hours

**Tasks:**
- [ ] Extend `prompt_builder.py`:
  - [ ] `add_career_context()` - Query season stats
  - [ ] Include in article prompt
- [ ] Query player season stats through game date
- [ ] Add to prompt: "Branch improved to .312 on the season..."
- [ ] Test articles with career context
- [ ] Evaluate improvement in article quality

**Deliverables:**
- Career stats in prompts
- More contextual articles

**Career Stats to Include:**
- Season batting average (through this game)
- Season HR/RBI totals
- Season ERA/W-L record (pitchers)
- Recent streak (if applicable)

---

### 6.3 Milestone Detection
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 1 day

**Tasks:**
- [ ] Extend `newsworthiness.py`:
  - [ ] `check_milestones()` - Detect career milestones
- [ ] Check for milestones crossed in this game:
  - [ ] 500th, 1000th, 1500th hit
  - [ ] 100th, 200th, 300th HR
  - [ ] 100th, 200th win
  - [ ] First career HR/win/save
- [ ] Boost newsworthiness to 95+ if milestone
- [ ] Flag as MUST_GENERATE
- [ ] Use high-quality model for milestones
- [ ] Include milestone in article prompt
- [ ] Test with milestone games

**Deliverables:**
- Milestone detection working
- Milestones prioritized correctly
- High-quality articles for milestones

**Milestone Logic:**
```python
# Calculate career total through this game
career_total = query_career_stats(player_id, through_date)

# Check if milestone was crossed
if career_total >= 500 and career_total - game_stats < 500:
    milestone = "500th career hit"
```

---

### 6.4 Rivalry Context
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** 4 hours

**Tasks:**
- [ ] Implement `get_rivalry_context()` in `game_context.py`
- [ ] Query head-to-head record for season
- [ ] Include in article prompt
- [ ] Test with rivalry games
- [ ] Evaluate improvement

**Deliverables:**
- Rivalry stats in prompts
- Articles mention head-to-head records

**Example:**
"The Pilots improved to 7-5 against the Mariners this season..."

---

### 6.5 Streak Detection
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** 4 hours

**Tasks:**
- [ ] Implement `detect_hot_streak()` in `game_context.py`
- [ ] Detect hitting streaks (3+ games with hit)
- [ ] Detect shutout streaks
- [ ] Include in article prompt if streak ≥3 games
- [ ] Test with streak games

**Deliverables:**
- Streak detection working
- Articles mention active streaks

**Example:**
"Branch extended his hitting streak to 12 games..."

---

### 6.6 Auto-Publish Based on Confidence
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** 4 hours

**Tasks:**
- [ ] Define auto-publish criteria:
  - [ ] Newsworthiness < 60 (routine games)
  - [ ] Validation passed with no issues
  - [ ] Model used is trusted
  - [ ] Not a milestone (always review)
- [ ] Implement `should_auto_publish()` in `article_processor.py`
- [ ] Update `save_article()` to check criteria
- [ ] Set status='published' if auto-publish
- [ ] Otherwise status='draft'
- [ ] Add configuration flag to enable/disable
- [ ] Test thoroughly before enabling

**Deliverables:**
- Auto-publish logic implemented
- Configuration flag added
- Disabled by default (enable after testing)

**Safety:**
- Start with manual review for all articles
- Once confident in quality, enable auto-publish for low-priority
- Always review high-priority and milestones

---

### 6.7 Article Search and Filtering
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** 1 day

**Tasks:**
- [ ] Add search box to newspaper homepage
- [ ] Implement full-text search across articles
- [ ] Add filters:
  - [ ] Date range
  - [ ] Article type
  - [ ] Featured player
  - [ ] Featured team
- [ ] Update homepage route to handle filters
- [ ] Add pagination
- [ ] Test search performance

**Deliverables:**
- Search functionality working
- Filters functional
- Performance acceptable

---

### 6.8 Article Analytics
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** 1-2 days

**Tasks:**
- [ ] Add article_views table:
  - [ ] Track views per article
  - [ ] Track reading time (optional)
- [ ] Add view tracking to article detail route
- [ ] Create analytics dashboard:
  - [ ] Most viewed articles
  - [ ] Views over time
  - [ ] Popular players/teams
- [ ] Display view count on articles (optional)

**Deliverables:**
- View tracking working
- Analytics dashboard functional

---

### 6.9 Newsletter Integration
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** 2-3 days

**Tasks:**
- [ ] Design email template for weekly digest
- [ ] Implement email generation:
  - [ ] Top 5 articles from week
  - [ ] Headlines and excerpts
  - [ ] Links to full articles
- [ ] Set up email service (SendGrid, Mailgun, etc.)
- [ ] Create subscription management:
  - [ ] Subscribe form
  - [ ] Unsubscribe link
  - [ ] Manage subscribers list
- [ ] Schedule weekly send (cron job)
- [ ] Test email delivery

**Deliverables:**
- Email template designed
- Subscription management working
- Weekly digest sending

---

### 6.10 Reader Comments
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** 2-3 days

**Tasks:**
- [ ] Create article_comments table
- [ ] Add comment form to article detail page
- [ ] Implement comment submission route
- [ ] Add moderation workflow:
  - [ ] Approve/reject comments
  - [ ] Admin moderation page
- [ ] Display approved comments on articles
- [ ] Add threading (optional)
- [ ] Add spam protection (reCAPTCHA)

**Deliverables:**
- Comment system functional
- Moderation workflow working
- Spam protection in place

---

## Testing & Quality Assurance

### Unit Testing
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** Ongoing

**Tasks:**
- [ ] Write unit tests for all modules:
  - [ ] `test_branch_detector.py`
  - [ ] `test_newsworthiness.py`
  - [ ] `test_game_log_parser.py`
  - [ ] `test_prompt_builder.py`
  - [ ] `test_ollama_client.py`
  - [ ] `test_article_processor.py`
- [ ] Achieve >80% code coverage
- [ ] Run tests in CI/CD (optional)

**Deliverables:**
- Comprehensive test suite
- All tests passing
- Good code coverage

---

### Integration Testing
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** 1 day

**Tasks:**
- [ ] Test full pipeline with real data:
  - [ ] ETL triggers article generation
  - [ ] Articles generated correctly
  - [ ] Drafts saved to database
  - [ ] Editorial review works
  - [ ] Publishing works
- [ ] Test edge cases:
  - [ ] Multi-Branch games
  - [ ] Extra-inning games
  - [ ] No-hitters, perfect games
  - [ ] Games with errors/missing data
- [ ] Document test scenarios

**Deliverables:**
- Integration tests passing
- Edge cases handled
- Test documentation

---

### Performance Testing
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 4 hours

**Tasks:**
- [ ] Benchmark article generation time:
  - [ ] Test with 8B model
  - [ ] Test with 14B model
  - [ ] Test with 70B model (if used)
- [ ] Benchmark database query performance:
  - [ ] Homepage load time
  - [ ] Article detail load time
  - [ ] Archive page load time
- [ ] Test batch generation (100+ games)
- [ ] Optimize slow queries
- [ ] Add caching if needed

**Deliverables:**
- Performance benchmarks documented
- Slow queries optimized
- Caching implemented if needed

**Performance Targets:**
- Article generation: <30s for 8B, <60s for 14B
- Homepage load: <1s
- Article detail: <500ms

---

### Manual QA Testing
**Status:** 🔴 Not Started
**Priority:** High
**Estimated Effort:** 1 day

**Tasks:**
- [ ] Review generated articles for quality:
  - [ ] Factual accuracy
  - [ ] Readability
  - [ ] Style consistency
  - [ ] No hallucinations
- [ ] Test all user workflows:
  - [ ] Editorial review
  - [ ] Article creation
  - [ ] Publishing
  - [ ] Navigation
- [ ] Test on multiple browsers/devices:
  - [ ] Desktop: Chrome, Firefox, Safari
  - [ ] Mobile: iOS Safari, Android Chrome
- [ ] Test responsive design
- [ ] Create QA checklist

**Deliverables:**
- All workflows tested
- Cross-browser compatibility verified
- QA checklist complete

---

## Documentation

### Code Documentation
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** Ongoing

**Tasks:**
- [ ] Add docstrings to all functions
- [ ] Add inline comments for complex logic
- [ ] Follow consistent documentation style
- [ ] Generate API documentation (Sphinx, optional)

---

### User Documentation
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 1 day

**Tasks:**
- [ ] Create `docs/newspaper-user-guide.md`:
  - [ ] How to review articles
  - [ ] How to create articles
  - [ ] How to regenerate articles
  - [ ] How to publish articles
- [ ] Create admin interface help text
- [ ] Add tooltips for form fields

**Deliverables:**
- User guide complete
- Help text in UI

---

### Technical Documentation Updates
**Status:** 🔴 Not Started
**Priority:** Medium
**Estimated Effort:** 4 hours

**Tasks:**
- [ ] Update `docs/OVERVIEW.MD` with newspaper section
- [ ] Update `docs/DATA-MODEL.MD` with new tables
- [ ] Update `docs/WEBSITE-SPECS.MD` with newspaper pages
- [ ] Create `docs/newspaper-api.md` for admin API routes

**Deliverables:**
- All documentation updated
- API documentation complete

---

## Deployment & Operations

### Production Configuration
**Status:** 🔴 Not Started
**Priority:** Low (when ready for production)
**Estimated Effort:** 4 hours

**Tasks:**
- [ ] Configure Ollama for production:
  - [ ] Systemd service
  - [ ] Auto-start on boot
  - [ ] Resource limits
- [ ] Configure database backups for newspaper tables
- [ ] Set up monitoring:
  - [ ] Article generation failures
  - [ ] Ollama service health
  - [ ] Database performance
- [ ] Set up logging:
  - [ ] ETL newspaper pipeline logs
  - [ ] Web application logs
- [ ] Configure error alerting

**Deliverables:**
- Production configuration complete
- Monitoring in place
- Backup strategy implemented

---

### Rollout Plan
**Status:** 🔴 Not Started
**Priority:** Low
**Estimated Effort:** Planning

**Tasks:**
- [ ] Define rollout phases:
  - [ ] Phase 1: Internal testing (drafts only)
  - [ ] Phase 2: Limited publishing (manual review)
  - [ ] Phase 3: Full publishing (with auto-publish)
- [ ] Create rollback plan
- [ ] Document deployment procedure
- [ ] Train on editorial workflow (if needed)

---

## Project Management

### Current Status Summary

**Overall Progress:** 🔴 Not Started (Planning Complete)

**Phase 1 (Foundation):** 🔴 0% Complete
**Phase 2 (Pipeline):** 🔴 0% Complete
**Phase 3 (Editorial):** 🔴 0% Complete
**Phase 4 (Frontend):** 🔴 0% Complete
**Phase 5 (Messages):** 🔴 0% Complete
**Phase 6 (Enhancements):** 🔴 0% Complete (Optional)

---

### Next Actions

**Immediate (Start Here):**
1. Task 1.1: Install and configure Ollama
2. Task 1.2: Benchmark models
3. Task 1.3: Create database schema

**After Foundation:**
4. Task 2.1: Branch game detection
5. Task 2.3: Prompt builder (can parallel with 2.2)
6. Task 2.4: Ollama client

---

### Dependencies Map

```
1.1 (Ollama Setup) → 1.2 (Benchmarking) → 2.4 (Ollama Client)
1.3 (Database) → 2.1 (Branch Detection) → 2.2 (game_logs Parser)
2.1 + 2.2 + 2.3 + 2.4 → 2.5 (Article Processor) → 2.6 (Pipeline)
2.6 → 3.1 (Editorial) → 3.2 → 3.3
2.6 → 4.1 (Homepage) → 4.2 → 4.3 + 4.4
5.1 (Messages Analysis) → 5.2 → 5.3
```

---

### Timeline Estimate

**MVP Timeline:** ~13-18 days (concentrated development)
- Phase 1: 1-2 days
- Phase 2: 4-5 days
- Phase 3: 3-4 days
- Phase 4: 3-4 days
- Phase 5: 2-3 days

**With Enhancements:** +5-10 days

---

### Success Metrics

**MVP Success Criteria:**
- [ ] Ollama running with 2+ models
- [ ] Database schema created
- [ ] ETL generates articles automatically
- [ ] Articles saved as drafts
- [ ] Editorial review functional
- [ ] Articles publish to homepage
- [ ] User can create manual articles

**Quality Metrics:**
- [ ] Generation success rate >90%
- [ ] Generation time <30s (8B), <60s (14B)
- [ ] Editorial rejection rate <20%
- [ ] Zero factual errors in articles

---

## Notes and Decisions

### Key Design Decisions
- **LLM Platform:** Ollama (local, cost-free, good performance)
- **Model Strategy:** Multi-tier (8B for routine, 14B/70B for important)
- **Workflow:** Draft-first with editorial review
- **Trigger:** Post-ETL automatic generation
- **Multi-Branch:** Single combined article

### Open Questions
- [ ] Should milestone articles use Claude API for highest quality?
- [ ] How to handle non-Branch milestone games (future)?
- [ ] Should we generate general game recaps (non-Branch)?
- [ ] What's the ideal prompt temperature (test in benchmarking)?

### Risks
- LLM hallucinations → Mitigate with validation and review
- Slow generation → Mitigate with model selection
- Poor quality → Mitigate with prompt engineering
- game_logs.csv growth → Mitigate with archival strategy

---

**Document Version:** 1.0
**Created:** 2025-10-15
**Last Updated:** 2025-10-15
**Status:** Planning Complete - Ready for Implementation
