# Newspaper ETL Integration & E2E Testing Strategy

## Overview

We need to test TWO complete ETL paths:

1. **FULL LOAD PATH** - Initial database setup with all data
2. **UPDATE PATH** - Incremental updates with fresh game data

Both paths must successfully generate newspaper articles at the end.

## Current ETL Flow Analysis

Based on `etl/main.py`, the current ETL has these commands:

1. **`fetch-data`** - Fetches CSVs from game machine
2. **`load-reference`** - Loads reference tables (leagues, teams, etc.)
3. **`load-stats`** - Loads player stats and calculates league constants
4. **`refresh-views`** - Refreshes materialized views for web performance
5. **`init-db`** - Database schema initialization
6. **`check-status`** - Health check

## Path 1: FULL LOAD (From Scratch)

**Assumption**: `data/incoming/csv/` has been populated with game files

### Command Sequence

```bash
# Step 1: Initialize database schema
python main.py init-db

# Step 2: Load reference data (forced full reload)
python main.py load-reference --force

# Step 3: Load stats with full constant calculation
python main.py load-stats --force-all-constants

# Step 4: Generate newspaper articles
python main.py generate-articles --priority MUST_GENERATE --priority SHOULD_GENERATE
```

### Flow Diagram

```
FULL LOAD PATH:
1. init-db
   ↓
   └─> Create all tables (reference, stats, newspaper)
   └─> Create indexes
   └─> Create constraints
   ↓
2. load-reference --force
   ↓
   └─> Load leagues, teams, divisions, sub_leagues
   └─> Full replace (no change detection)
   ↓
3. load-stats --force-all-constants
   ↓
   └─> Load players
   └─> Load batting stats
   └─> Load pitching stats
   └─> Calculate constants for ALL years
   └─> Load history tables
   └─> Load coaches and rosters
   └─> Refresh materialized views
   ↓
4. generate-articles (NEW)
   ↓
   └─> Detect all Branch games in database
   └─> Score newsworthiness
   └─> Generate articles (Ollama)
   └─> Save to newspaper_articles table
```

## Path 2: UPDATE (Incremental with Fresh Data)

**Assumption**: There's an update waiting on the game machine

### Command Sequence

```bash
# Step 1: Fetch fresh data from game machine
python main.py fetch-data

# Step 2: Load reference data (incremental, only changed)
python main.py load-reference

# Step 3: Load stats (incremental, only new/changed players)
python main.py load-stats

# Step 4: Generate newspaper articles (only new games)
python main.py generate-articles --priority MUST_GENERATE --priority SHOULD_GENERATE
```

### Flow Diagram

```
UPDATE PATH:
1. fetch-data
   ↓
   └─> rsync CSVs from game machine
   └─> Overwrite data/incoming/csv/*
   ↓
2. load-reference
   ↓
   └─> Check MD5 hashes (change detection)
   └─> Load only changed reference tables
   ↓
3. load-stats
   ↓
   └─> Load new/updated players
   └─> Load new batting/pitching stats
   └─> Calculate constants for NEW years only
   └─> Load new history records
   └─> Load new coaches/rosters
   └─> Refresh materialized views
   ↓
4. generate-articles
   ↓
   └─> Detect NEW Branch games (not already processed)
   └─> Score newsworthiness
   └─> Generate articles (Ollama)
   └─> Save to newspaper_articles table
   └─> Skip games that already have articles
```

## Newspaper Integration Design

### New CLI Command: `generate-articles`

Add to `etl/main.py`:

```python
@cli.command('generate-articles')
@click.option('--date-range', help='Date range YYYY-MM-DD:YYYY-MM-DD')
@click.option('--force', is_flag=True, help='Regenerate existing articles')
@click.option('--priority', multiple=True, default=['MUST_GENERATE', 'SHOULD_GENERATE'],
              help='Priority tiers to generate')
def generate_newspaper_articles(date_range, force, priority):
    """Generate newspaper articles for Branch family performances"""
    from src.newspaper.pipeline import generate_branch_articles_pipeline
    from datetime import datetime

    logger.info("Starting newspaper article generation...")

    # Parse date range if provided
    date_range_tuple = None
    if date_range:
        start_str, end_str = date_range.split(':')
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        date_range_tuple = (start_date, end_date)

    # Parse priority filter
    priority_filter = list(priority) if priority else None

    try:
        results = generate_branch_articles_pipeline(
            date_range=date_range_tuple,
            force_regenerate=force,
            priority_filter=priority_filter
        )

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("NEWSPAPER GENERATION RESULTS")
        click.echo("=" * 60)
        click.echo(f"Detected: {results['detected']} games")
        click.echo(f"Generated: {results['generated']} articles")
        click.echo(f"Failed: {results['failed']} articles")
        click.echo(f"Skipped: {results['skipped']} articles")

        if results['errors']:
            click.echo(f"\nErrors: {len(results['errors'])}")
            for error in results['errors'][:5]:
                click.echo(f"  - {error}")

        if results['generated'] > 0:
            click.echo("\n✓ Articles generated successfully")
            return 0
        elif results['failed'] > 0:
            click.echo("\n⚠ Some articles failed to generate")
            return 1
        else:
            click.echo("\n⚠ No articles generated (this may be normal)")
            return 0

    except Exception as e:
        logger.error(f"Article generation failed: {e}")
        click.echo(f"✗ Article generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
```

## E2E Test Strategy

### Test Directory Structure

```
/test/
├── README.md                              # Test documentation
├── e2e/
│   ├── test_full_load_path.py            # Test Path 1: Full load
│   ├── test_update_path.py               # Test Path 2: Incremental update
│   └── verify_results.py                 # Result verification helper
└── conftest.py                            # Pytest fixtures
```

## Test 1: FULL LOAD PATH

### Acceptance Criteria

**Pre-conditions:**
- ✅ Database exists (ootp_dev)
- ✅ `data/incoming/csv/` is populated with current game files
- ✅ Ollama is running with required models
- ✅ Database is empty or can be dropped/recreated

**Test Steps:**

```bash
# 1. Initialize database
python main.py init-db

# 2. Load reference data (full)
python main.py load-reference --force

# 3. Load stats (full)
python main.py load-stats --force-all-constants

# 4. Generate articles
python main.py generate-articles
```

**Success Criteria:**

✅ **SC1: Database Schema Created**
- All tables exist (verify with `\dt` in psql)
- All indexes created
- All foreign keys created
- `newspaper_articles` table exists
- `article_player_tags`, `article_team_tags`, `article_game_tags` exist

✅ **SC2: Reference Data Loaded**
- `teams` table populated (COUNT(*) > 0)
- `leagues` table populated
- `divisions` table populated
- `sub_leagues` table populated
- No duplicate IDs

✅ **SC3: Player Data Loaded**
- `players_core` table populated
- Branch family members exist (SELECT * WHERE last_name='Branch')
- At least 1 Branch player found

✅ **SC4: Statistics Loaded**
- `players_career_batting_stats` populated
- `players_career_pitching_stats` populated
- `players_game_batting_stats` populated
- `players_game_pitching_stats` populated
- Stats data matches player_ids in `players_core`

✅ **SC5: League Constants Calculated**
- `league_batting_constants` has records
- `league_pitching_constants` has records
- All years represented
- No NULL values in key columns

✅ **SC6: History and Roster Data Loaded**
- `league_history` populated
- `team_history` populated
- `coaches` populated
- `team_roster` populated
- `team_roster_staff` populated

✅ **SC7: Materialized Views Refreshed**
- `mv_batting_leaders` returns data
- `mv_pitching_leaders` returns data
- Views have current data

✅ **SC8: Branch Games Detected**
- Pipeline detects Branch performances
- Both batting and pitching detected
- Games from `players_game_batting_stats` and `players_game_pitching_stats`
- Detection count > 0

✅ **SC9: Newsworthiness Scored**
- All games have score 0-100
- High-performance games scored ≥50
- Routine games scored <50
- Priority tiers assigned

✅ **SC10: Articles Generated**
- At least 1 article created
- `newspaper_articles` table has records
- Articles have `status='draft'`
- Articles have `generation_method='ai_generated'`

✅ **SC11: Articles Properly Tagged**
- `article_player_tags` created for each article
- `article_team_tags` created for each article
- `article_game_tags` created for each article
- Primary tags set correctly (is_primary=true)

✅ **SC12: Article Content Quality**
- Headline not empty
- Body not empty
- Word count ≥50
- No validation errors
- Player names in article text
- Team names in article text

✅ **SC13: No Errors**
- No database constraint violations
- No orphaned records
- No duplicate articles
- Pipeline returns success

## Test 2: UPDATE PATH

### Acceptance Criteria

**Pre-conditions:**
- ✅ Test 1 (Full Load) has completed successfully
- ✅ There's a game update waiting on the game machine
- ✅ Existing articles in database from Test 1

**Test Steps:**

```bash
# 1. Fetch fresh data
python main.py fetch-data

# 2. Load reference (incremental)
python main.py load-reference

# 3. Load stats (incremental)
python main.py load-stats

# 4. Generate new articles
python main.py generate-articles
```

**Success Criteria:**

✅ **SC1: Data Fetched Successfully**
- `fetch-data` command completes without errors
- CSV files updated in `data/incoming/csv/`
- Newer timestamps on fetched files
- All expected CSV files present

✅ **SC2: Reference Data Updated (If Changed)**
- Change detection working (MD5 hashes)
- Only modified tables reloaded
- No data loss from unchanged tables

✅ **SC3: New Player Stats Loaded**
- New games in `players_game_batting_stats`
- New games in `players_game_pitching_stats`
- Existing records unchanged
- No duplicate game_id + player_id combinations

✅ **SC4: League Constants Updated**
- New year constants calculated (if new season)
- Existing year constants unchanged
- No recalculation of old years

✅ **SC5: Materialized Views Current**
- Views refreshed with new data
- New stats appear in leaderboards

✅ **SC6: New Branch Games Detected**
- Only NEW games detected (not previously processed)
- Game count reflects new data only
- Previously processed games not re-detected

✅ **SC7: New Articles Generated**
- Articles created for NEW high-priority games
- Existing articles NOT regenerated (unless --force)
- Article count increases from Test 1

✅ **SC8: No Duplicate Articles**
- One article per game+player combination
- Check: SELECT game_id, COUNT(*) FROM newspaper_articles GROUP BY game_id HAVING COUNT(*) > 1
- Result: 0 rows

✅ **SC9: Idempotency Check**
- Run `generate-articles` again (no --force)
- Result: 0 new articles generated
- All games skipped (already have articles)

✅ **SC10: Performance Acceptable**
- `fetch-data`: < 5 minutes
- `load-reference`: < 30 seconds
- `load-stats`: < 2 minutes
- `generate-articles`: < 5 minutes for typical update

## Verification Queries

### Database Integrity Checks

```sql
-- Check for Branch family members
SELECT player_id, first_name, last_name, position
FROM players_core
WHERE last_name = 'Branch'
ORDER BY player_id;

-- Check Branch game performances
SELECT
    p.first_name || ' ' || p.last_name as player_name,
    b.game_id,
    b.ab, b.h, b.hr, b.rbi
FROM players_game_batting_stats b
JOIN players_core p ON b.player_id = p.player_id
WHERE p.last_name = 'Branch'
ORDER BY b.game_id DESC
LIMIT 10;

-- Check articles generated
SELECT
    a.article_id,
    a.title,
    a.status,
    a.newsworthiness_score,
    a.model_used,
    a.created_at
FROM newspaper_articles a
ORDER BY a.newsworthiness_score DESC;

-- Check article tags
SELECT
    a.article_id,
    a.title,
    p.first_name || ' ' || p.last_name as player_name,
    apt.is_primary
FROM newspaper_articles a
JOIN article_player_tags apt ON a.article_id = apt.article_id
JOIN players_core p ON apt.player_id = p.player_id
ORDER BY a.article_id;

-- Check for duplicate articles per game
SELECT game_id, COUNT(*) as count
FROM newspaper_articles
GROUP BY game_id
HAVING COUNT(*) > 1;

-- Should return 0 rows
```

### Article Quality Checks

```sql
-- Check headline quality
SELECT article_id, title, LENGTH(title) as title_length
FROM newspaper_articles
WHERE LENGTH(title) < 10 OR LENGTH(title) > 255;

-- Should return 0 rows

-- Check body quality
SELECT article_id, title, LENGTH(content) as content_length
FROM newspaper_articles
WHERE LENGTH(content) < 100 OR content LIKE '%TODO%' OR content LIKE '%[INSERT%';

-- Should return 0 rows

-- Check article stats
SELECT
    COUNT(*) as total_articles,
    AVG(newsworthiness_score) as avg_score,
    MIN(newsworthiness_score) as min_score,
    MAX(newsworthiness_score) as max_score,
    COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_count,
    COUNT(CASE WHEN status = 'published' THEN 1 END) as published_count
FROM newspaper_articles;
```

## Test Execution Plan

### Day 1: Full Load Test

1. **Preparation** (30 min)
   - Ensure Ollama running with models pulled
   - Verify data files in `data/incoming/csv/`
   - Document current state

2. **Execute Full Load** (15-30 min)
   - Run init-db
   - Run load-reference --force
   - Run load-stats --force-all-constants
   - Run generate-articles

3. **Verification** (30 min)
   - Run all verification queries
   - Check article quality manually
   - Document any issues
   - Take database snapshot

### Day 2: Update Test

1. **Preparation** (15 min)
   - Confirm game update available
   - Document current article count

2. **Execute Update** (10-20 min)
   - Run fetch-data
   - Run load-reference
   - Run load-stats
   - Run generate-articles

3. **Verification** (30 min)
   - Verify new articles only
   - Check no duplicates
   - Test idempotency
   - Document results

## Success Metrics

### Critical (Must Pass)
- ✅ Both paths complete without errors
- ✅ All database integrity checks pass
- ✅ At least 1 article generated in each path
- ✅ No duplicate articles
- ✅ Idempotency verified

### Important (Should Pass)
- ✅ Article generation success rate ≥ 90%
- ✅ All high-priority games have articles
- ✅ Performance within acceptable ranges
- ✅ No manual intervention required

### Nice-to-Have
- ✅ Article quality score (manual) ≥ 7/10
- ✅ Zero hallucinations
- ✅ All articles grammatically correct

## Next Steps

1. ✅ Update `etl/main.py` with `generate-articles` command
2. ✅ Create `/test` directory with README
3. ✅ Execute Test 1: Full Load Path
4. ✅ Document Test 1 results
5. ✅ Execute Test 2: Update Path
6. ✅ Document Test 2 results
7. ✅ Fix any issues found
8. ✅ Update implementation plan with final status
