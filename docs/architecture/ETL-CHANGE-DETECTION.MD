# ETL Change Detection Strategy

## Overview
This document outlines the change detection and incremental loading strategy for OOTP Web's ETL process. The goal is to efficiently update data without unnecessary truncation of tables or recalculation of statistics.

## Data Classification by Change Frequency

### 1. Static Reference Data (Never/Rarely Changes)
**Tables**: continents, nations, states, cities, languages, parks
- **Change Frequency**: Never or only when game universe is modified
- **Strategy**: Load once, skip on updates unless file checksum changes
- **Detection Method**: MD5/SHA256 checksum comparison

### 2. Slowly Changing Dimensions (Occasional Changes)
**Tables**: teams, leagues, sub_leagues, divisions, coaches, players (basic info)
- **Change Frequency**: Season boundaries, trades, hirings
- **Strategy**: CDC (Change Data Capture) with effective dating
- **Detection Method**: Row-level comparison with composite keys

### 3. Frequently Updated Stats (Every Game)
**Tables**: players_career_batting_stats, players_career_pitching_stats, players_career_fielding_stats, team_batting_stats, team_pitching_stats
- **Change Frequency**: After every simulated game
- **Strategy**: Incremental updates with UPSERT
- **Detection Method**: Composite key matching with value comparison

### 4. Append-Only Tables
**Tables**: games, game_logs, transactions
- **Change Frequency**: New records added continuously
- **Strategy**: Append new records only
- **Detection Method**: Watermark tracking (max ID or date)

## Database Schema for Change Detection

### Metadata Tracking Table
```sql
CREATE TABLE IF NOT EXISTS etl_file_metadata (
    filename VARCHAR(100) PRIMARY KEY,
    file_path VARCHAR(500),
    last_modified TIMESTAMP,
    file_size BIGINT,
    row_count INTEGER,
    checksum VARCHAR(64),
    load_strategy VARCHAR(20) CHECK (load_strategy IN ('skip', 'full', 'incremental', 'append')),
    last_processed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_status VARCHAR(20) CHECK (last_status IN ('success', 'failed', 'skipped', 'in_progress')),
    processing_time_seconds INTEGER,
    rows_inserted INTEGER,
    rows_updated INTEGER,
    rows_deleted INTEGER,
    error_message TEXT
);

CREATE INDEX idx_etl_metadata_status ON etl_file_metadata(last_status, last_processed);
```

### Change Log Table
```sql
CREATE TABLE IF NOT EXISTS etl_change_log (
    change_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    primary_key_values TEXT NOT NULL,
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    changed_fields TEXT[], -- Array of field names that changed
    old_values JSONB, -- Previous values for UPDATE operations
    new_values JSONB, -- New values
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    season_year INTEGER,
    game_id INTEGER,
    batch_id UUID
);

CREATE INDEX idx_change_log_table_operation ON etl_change_log(table_name, operation, changed_at);
CREATE INDEX idx_change_log_game ON etl_change_log(game_id);
```

### Watermark Tracking Table
```sql
CREATE TABLE IF NOT EXISTS etl_watermarks (
    table_name VARCHAR(50) PRIMARY KEY,
    watermark_column VARCHAR(50) NOT NULL,
    watermark_value TEXT NOT NULL,
    watermark_type VARCHAR(20) CHECK (watermark_type IN ('integer', 'timestamp', 'date')),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Load Strategy Definitions

### SKIP Strategy (Static Reference Data)
```python
def process_static_reference(csv_file, table_name):
    """
    Only load if checksum has changed
    """
    current_checksum = calculate_file_checksum(csv_file)
    stored_metadata = get_file_metadata(csv_file.name)
    
    if stored_metadata and current_checksum == stored_metadata.checksum:
        log.info(f"Skipping {table_name} - no changes detected")
        update_metadata_status(csv_file.name, 'skipped')
        return
    
    # Full reload if checksum differs
    with transaction():
        truncate_table(table_name)
        load_csv_to_table(csv_file, table_name)
        update_file_metadata(csv_file, current_checksum, 'success')
```

### INCREMENTAL Strategy (Player Stats)
```python
def process_player_stats(csv_file, table_name):
    """
    Compare and update only changed records
    """
    # Define composite key for the table
    key_columns = get_table_keys(table_name)
    
    # Load CSV into staging table
    staging_table = f"staging_{table_name}"
    create_staging_table(staging_table, table_name)
    load_csv_to_staging(csv_file, staging_table)
    
    with transaction():
        # Insert new records
        inserted = insert_new_records(staging_table, table_name, key_columns)
        
        # Update existing records that have changed
        updated = update_changed_records(staging_table, table_name, key_columns)
        
        # Optionally handle deletions (players who retired)
        deleted = handle_deletions(staging_table, table_name, key_columns)
        
        # Update metadata
        update_file_metadata(csv_file, rows_inserted=inserted, 
                           rows_updated=updated, rows_deleted=deleted)
        
        # Trigger recalculation only for affected players
        if inserted + updated > 0:
            trigger_calculation_refresh(table_name, staging_table)
```

### APPEND Strategy (Games, Transactions)
```python
def process_append_only(csv_file, table_name, watermark_column='game_id'):
    """
    Only insert records newer than watermark
    """
    # Get current watermark
    current_watermark = get_watermark(table_name, watermark_column)
    
    # Load only new records
    new_records = load_csv_with_filter(
        csv_file, 
        filter_clause=f"{watermark_column} > {current_watermark}"
    )
    
    if new_records.empty:
        log.info(f"No new records for {table_name}")
        return
    
    with transaction():
        # Insert new records
        rows_inserted = insert_records(new_records, table_name)
        
        # Update watermark
        new_watermark = new_records[watermark_column].max()
        update_watermark(table_name, watermark_column, new_watermark)
        
        update_file_metadata(csv_file, rows_inserted=rows_inserted)
```

## Specific Implementation for Player Stats Tables

### Key Design Principles
1. **Never truncate stats tables** - Preserve calculated statistics
2. **Use composite keys** - (player_id, year, team_id, split_id, stint)
3. **Track field-level changes** - Only recalculate affected metrics
4. **Batch processing** - Group updates by player for efficiency

### Players Career Batting Stats Implementation

#### Table Structure with Change Tracking
```sql
-- Add audit columns to stats tables
ALTER TABLE players_career_batting_stats ADD COLUMN IF NOT EXISTS
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE players_career_batting_stats ADD COLUMN IF NOT EXISTS
    update_count INTEGER DEFAULT 0;
ALTER TABLE players_career_batting_stats ADD COLUMN IF NOT EXISTS
    calculation_status VARCHAR(20) DEFAULT 'pending';
```

#### UPSERT Implementation
```sql
-- Create unique constraint for upsert
ALTER TABLE players_career_batting_stats 
ADD CONSTRAINT uk_player_batting_stats 
UNIQUE (player_id, year, team_id, split_id, stint);

-- UPSERT function
CREATE OR REPLACE FUNCTION upsert_batting_stats(
    staging_table TEXT
) RETURNS TABLE (inserted INTEGER, updated INTEGER) AS $$
DECLARE
    rows_inserted INTEGER;
    rows_updated INTEGER;
BEGIN
    -- Insert new records
    WITH inserted AS (
        INSERT INTO players_career_batting_stats
        SELECT s.*, CURRENT_TIMESTAMP, 0, 'pending'
        FROM staging_table s
        WHERE NOT EXISTS (
            SELECT 1 FROM players_career_batting_stats p
            WHERE p.player_id = s.player_id
            AND p.year = s.year
            AND p.team_id = s.team_id
            AND p.split_id = s.split_id
            AND p.stint = s.stint
        )
        RETURNING 1
    )
    SELECT COUNT(*) INTO rows_inserted FROM inserted;
    
    -- Update existing records only if values changed
    WITH updated AS (
        UPDATE players_career_batting_stats p
        SET 
            ab = s.ab,
            h = s.h,
            hr = s.hr,
            rbi = s.rbi,
            -- ... other fields ...
            last_updated = CURRENT_TIMESTAMP,
            update_count = p.update_count + 1,
            calculation_status = 'pending'
        FROM staging_table s
        WHERE p.player_id = s.player_id
            AND p.year = s.year
            AND p.team_id = s.team_id
            AND p.split_id = s.split_id
            AND p.stint = s.stint
            AND (
                p.ab != s.ab OR
                p.h != s.h OR
                p.hr != s.hr OR
                p.rbi != s.rbi
                -- ... check other fields ...
            )
        RETURNING 1
    )
    SELECT COUNT(*) INTO rows_updated FROM updated;
    
    RETURN QUERY SELECT rows_inserted, rows_updated;
END;
$$ LANGUAGE plpgsql;
```

### Intelligent Calculation Refresh

#### Track Which Stats Need Recalculation
```sql
CREATE TABLE IF NOT EXISTS etl_calculation_queue (
    queue_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    player_id INTEGER,
    year INTEGER,
    team_id INTEGER,
    calculation_type VARCHAR(50), -- 'woba', 'war', 'wrc_plus', etc.
    priority INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX idx_calc_queue_status ON etl_calculation_queue(status, priority, created_at);
```

#### Calculation Trigger Function
```python
def queue_calculations_for_player(player_id, year, changes):
    """
    Queue only necessary calculations based on what changed
    """
    calculations_needed = set()
    
    # Determine which calculations are affected
    if any(field in changes for field in ['ab', 'h', 'bb', 'hbp']):
        calculations_needed.add('batting_average')
        calculations_needed.add('on_base_percentage')
        calculations_needed.add('woba')
    
    if any(field in changes for field in ['h', 'd', 't', 'hr']):
        calculations_needed.add('slugging_percentage')
        calculations_needed.add('iso')
    
    if 'woba' in calculations_needed:
        calculations_needed.add('wrc')
        calculations_needed.add('wrc_plus')
    
    # Queue calculations
    for calc_type in calculations_needed:
        queue_calculation(
            table_name='players_career_batting_stats',
            player_id=player_id,
            year=year,
            calculation_type=calc_type
        )
```

### Processing Pipeline

#### Main ETL Flow
```python
def process_batting_stats_update():
    """
    Complete pipeline for batting stats updates
    """
    # Phase 1: Load data to staging
    csv_file = 'players_career_batting_stats.csv'
    staging_table = 'staging_batting_stats'
    
    create_staging_table(staging_table)
    load_csv_to_staging(csv_file, staging_table)
    
    # Phase 2: Identify changes
    changes = identify_changed_records(staging_table, 'players_career_batting_stats')
    
    # Phase 3: Apply updates
    results = execute_upsert(staging_table)
    
    # Phase 4: Queue calculations for affected players
    for change in changes:
        queue_calculations_for_player(
            change.player_id, 
            change.year, 
            change.changed_fields
        )
    
    # Phase 5: Process calculation queue
    process_calculation_queue()
    
    # Phase 6: Cleanup
    drop_staging_table(staging_table)
    
    return results
```

## Performance Optimizations

### 1. Batch Processing
- Group updates by player to minimize calculation overhead
- Process current season more frequently than historical data

### 2. Parallel Processing
- Use multiple workers for calculation queue
- Partition large tables by year for parallel loading

### 3. Incremental Materialized Views
```sql
-- Create materialized view for league averages
CREATE MATERIALIZED VIEW mv_league_batting_averages AS
SELECT 
    year, 
    league_id, 
    AVG(batting_average) as league_avg,
    AVG(on_base_percentage) as league_obp,
    AVG(slugging_percentage) as league_slg
FROM players_career_batting_stats
WHERE split_id = 1  -- Overall stats
GROUP BY year, league_id;

-- Refresh only affected years
CREATE OR REPLACE FUNCTION refresh_league_averages(affected_years INTEGER[])
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_league_batting_averages
    WHERE year = ANY(affected_years);
END;
$$ LANGUAGE plpgsql;
```

### 4. Smart Indexing
```sql
-- Indexes for efficient change detection
CREATE INDEX idx_batting_stats_composite 
ON players_career_batting_stats(player_id, year, team_id, split_id, stint);

CREATE INDEX idx_batting_stats_updated 
ON players_career_batting_stats(last_updated, calculation_status);
```

## Monitoring and Logging

### ETL Dashboard Queries
```sql
-- Recent ETL activity
SELECT 
    filename,
    last_processed,
    last_status,
    rows_inserted + rows_updated as rows_affected,
    processing_time_seconds
FROM etl_file_metadata
ORDER BY last_processed DESC
LIMIT 20;

-- Calculation backlog
SELECT 
    calculation_type,
    COUNT(*) as pending_count,
    MIN(created_at) as oldest_request
FROM etl_calculation_queue
WHERE status = 'pending'
GROUP BY calculation_type;

-- Change velocity by table
SELECT 
    table_name,
    DATE(changed_at) as change_date,
    COUNT(*) as change_count,
    COUNT(DISTINCT primary_key_values) as unique_records
FROM etl_change_log
WHERE changed_at > CURRENT_DATE - INTERVAL '7 days'
GROUP BY table_name, DATE(changed_at)
ORDER BY change_date DESC, change_count DESC;
```

## Implementation Checklist

1. [ ] Create metadata tracking tables
2. [ ] Implement checksum calculation for static files
3. [ ] Build staging table framework
4. [ ] Create UPSERT procedures for each stat table
5. [ ] Implement calculation queue system
6. [ ] Set up monitoring dashboards
7. [ ] Test incremental updates with sample data
8. [ ] Document table-specific composite keys
9. [ ] Create rollback procedures
10. [ ] Set up performance benchmarks