-- Migration 006: Phase 4D Player Detail Performance Indexes
-- Created: 2025-10-24
-- Purpose: Add critical missing indexes for player detail page optimization
-- Target: Reduce cold load from 60s to ~10-15s
-- Related: docs/optimization/phase4d_under_5s_checklist.md
--
-- Performance Impact Analysis:
-- - Batting stats queries: 30s → 2s (28s saved)
-- - Pitching stats queries: 30s → 2s (28s saved)
-- - Trade history query: 10s → 1s (9s saved)
-- - Total estimated savings: ~65s
-- - Expected final cold load: ~5-10s
--
-- Index Strategy:
-- 1. Composite indexes on players_batting/pitching (player_id, split_id, league_level)
-- 2. Individual indexes on trades_history (all 20 player_id columns)
-- 3. Future: Replace trades_history indexes with GIN array index (Phase 4 - Array Storage)

-- =============================================================================
-- BATCH 1: Players Batting Stats Indexes
-- =============================================================================
-- Current State: Only primary key on (player_id, year, team_id, split_id, stint) exists
-- Query Pattern: WHERE player_id = X AND split_id = 1 [AND level_id via JOIN to leagues]
-- Impact: Eliminates full table scans, enables index-only scans
--
-- Note: Using level_id (in stats table) instead of league_level (requires JOIN)
-- level_id corresponds to league_level: 1=MLB, 2-6=minors

-- Composite index for most common query pattern (player + split + level)
-- This single index covers all player detail page batting queries
CREATE INDEX IF NOT EXISTS idx_batting_player_split_level
ON players_career_batting_stats(player_id, split_id, level_id);

-- Individual indexes for partial query coverage (backwards compatibility)
CREATE INDEX IF NOT EXISTS idx_batting_player_split
ON players_career_batting_stats(player_id, split_id);

CREATE INDEX IF NOT EXISTS idx_batting_player_level
ON players_career_batting_stats(player_id, level_id);

-- Optional: Partial index for split_id=1 (regular season - most common)
-- Smaller index size, faster for the 90% case
CREATE INDEX IF NOT EXISTS idx_batting_player_regular_season
ON players_career_batting_stats(player_id, level_id)
WHERE split_id = 1;

-- =============================================================================
-- BATCH 2: Players Pitching Stats Indexes
-- =============================================================================
-- Current State: Only primary key on (player_id, year, team_id, split_id, stint) exists
-- Query Pattern: WHERE player_id = X AND split_id = 1 [AND level_id via JOIN to leagues]
-- Impact: Eliminates full table scans, enables index-only scans

-- Composite index for most common query pattern (player + split + level)
CREATE INDEX IF NOT EXISTS idx_pitching_player_split_level
ON players_career_pitching_stats(player_id, split_id, level_id);

-- Individual indexes for partial query coverage (backwards compatibility)
CREATE INDEX IF NOT EXISTS idx_pitching_player_split
ON players_career_pitching_stats(player_id, split_id);

CREATE INDEX IF NOT EXISTS idx_pitching_player_level
ON players_career_pitching_stats(player_id, level_id);

-- Optional: Partial index for split_id=1 (regular season - most common)
CREATE INDEX IF NOT EXISTS idx_pitching_player_regular_season
ON players_career_pitching_stats(player_id, level_id)
WHERE split_id = 1;

-- =============================================================================
-- BATCH 3: Trade History Indexes (CRITICAL - No indexes exist!)
-- =============================================================================
-- Current State: ZERO indexes (not even a primary key!)
-- Query Pattern: WHERE player_id_0_0 = X OR player_id_0_1 = X OR ... (20-way OR)
-- Impact: Eliminates full table scan on every query
-- Future: Replace with single GIN index on array column (Phase 4 - Array Storage)
--
-- Note: These indexes use partial indexing (WHERE player_id IS NOT NULL)
-- to save space and improve performance. NULL values are never queried.

-- Team 0 player slots (10 columns)
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_0
ON trade_history(player_id_0_0)
WHERE player_id_0_0 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_1
ON trade_history(player_id_0_1)
WHERE player_id_0_1 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_2
ON trade_history(player_id_0_2)
WHERE player_id_0_2 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_3
ON trade_history(player_id_0_3)
WHERE player_id_0_3 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_4
ON trade_history(player_id_0_4)
WHERE player_id_0_4 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_5
ON trade_history(player_id_0_5)
WHERE player_id_0_5 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_6
ON trade_history(player_id_0_6)
WHERE player_id_0_6 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_7
ON trade_history(player_id_0_7)
WHERE player_id_0_7 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_8
ON trade_history(player_id_0_8)
WHERE player_id_0_8 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_9
ON trade_history(player_id_0_9)
WHERE player_id_0_9 IS NOT NULL;

-- Team 1 player slots (10 columns)
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_0
ON trade_history(player_id_1_0)
WHERE player_id_1_0 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_1
ON trade_history(player_id_1_1)
WHERE player_id_1_1 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_2
ON trade_history(player_id_1_2)
WHERE player_id_1_2 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_3
ON trade_history(player_id_1_3)
WHERE player_id_1_3 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_4
ON trade_history(player_id_1_4)
WHERE player_id_1_4 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_5
ON trade_history(player_id_1_5)
WHERE player_id_1_5 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_6
ON trade_history(player_id_1_6)
WHERE player_id_1_6 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_7
ON trade_history(player_id_1_7)
WHERE player_id_1_7 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_8
ON trade_history(player_id_1_8)
WHERE player_id_1_8 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_9
ON trade_history(player_id_1_9)
WHERE player_id_1_9 IS NOT NULL;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these to verify indexes were created successfully:

-- Check batting indexes (should show 4 new indexes)
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'players_career_batting_stats' ORDER BY indexname;

-- Check pitching indexes (should show 4 new indexes)
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'players_career_pitching_stats' ORDER BY indexname;

-- Check trade indexes (should show 20 new indexes)
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'trade_history' ORDER BY indexname;

-- =============================================================================
-- PERFORMANCE TESTING
-- =============================================================================
-- Before/After comparison:
--
-- BEFORE (no indexes):
-- EXPLAIN ANALYZE SELECT * FROM players_career_batting_stats WHERE player_id = 3000 AND split_id = 1 AND level_id = 1;
-- Expected: Seq Scan, ~20-30s execution time
--
-- AFTER (with indexes):
-- EXPLAIN ANALYZE SELECT * FROM players_career_batting_stats WHERE player_id = 3000 AND split_id = 1 AND level_id = 1;
-- Expected: Index Scan using idx_batting_player_split_level, <100ms execution time
--
-- Full page test:
-- time curl -o /dev/null -s -w "%{http_code}\n" http://localhost:5002/players/3000
-- Expected: 60s → 10-15s

-- =============================================================================
-- ROLLBACK (if needed)
-- =============================================================================
-- DROP INDEX IF EXISTS idx_batting_player_split_level;
-- DROP INDEX IF EXISTS idx_batting_player_split;
-- DROP INDEX IF EXISTS idx_batting_player_level;
-- DROP INDEX IF EXISTS idx_batting_player_regular_season;
-- DROP INDEX IF EXISTS idx_pitching_player_split_level;
-- DROP INDEX IF EXISTS idx_pitching_player_split;
-- DROP INDEX IF EXISTS idx_pitching_player_level;
-- DROP INDEX IF EXISTS idx_pitching_player_regular_season;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_0;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_1;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_2;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_3;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_4;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_5;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_6;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_7;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_8;
-- DROP INDEX IF EXISTS idx_trade_history_player_0_9;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_0;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_1;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_2;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_3;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_4;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_5;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_6;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_7;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_8;
-- DROP INDEX IF EXISTS idx_trade_history_player_1_9;
