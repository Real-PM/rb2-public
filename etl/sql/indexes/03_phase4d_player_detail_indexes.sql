-- Phase 4D: Player Detail Page Performance Indexes
-- Created: 2025-10-24
-- Purpose: Add critical indexes for player detail page queries
-- Expected Impact: 60s → 10-15s cold load (80-85% improvement)
--
-- This file is included in database initialization and will persist across
-- environment refreshes. See migration/006_phase4d_player_detail_indexes.sql
-- for the full migration script with detailed documentation.
--
-- Related: docs/optimization/phase4d_under_5s_checklist.md

-- =============================================================================
-- BATTING STATS INDEXES
-- =============================================================================

-- Composite index for player + split + level (most efficient)
CREATE INDEX IF NOT EXISTS idx_batting_player_split_level
ON players_career_batting_stats(player_id, split_id, level_id);

-- Individual indexes for partial query coverage
CREATE INDEX IF NOT EXISTS idx_batting_player_split
ON players_career_batting_stats(player_id, split_id);

CREATE INDEX IF NOT EXISTS idx_batting_player_level
ON players_career_batting_stats(player_id, level_id);

-- Partial index for regular season (split_id=1) - most common query
CREATE INDEX IF NOT EXISTS idx_batting_player_regular_season
ON players_career_batting_stats(player_id, level_id)
WHERE split_id = 1;

-- =============================================================================
-- PITCHING STATS INDEXES
-- =============================================================================

-- Composite index for player + split + level (most efficient)
CREATE INDEX IF NOT EXISTS idx_pitching_player_split_level
ON players_career_pitching_stats(player_id, split_id, level_id);

-- Individual indexes for partial query coverage
CREATE INDEX IF NOT EXISTS idx_pitching_player_split
ON players_career_pitching_stats(player_id, split_id);

CREATE INDEX IF NOT EXISTS idx_pitching_player_level
ON players_career_pitching_stats(player_id, level_id);

-- Partial index for regular season (split_id=1) - most common query
CREATE INDEX IF NOT EXISTS idx_pitching_player_regular_season
ON players_career_pitching_stats(player_id, level_id)
WHERE split_id = 1;

-- =============================================================================
-- TRADE HISTORY INDEXES
-- =============================================================================
-- Note: These will be replaced with a single GIN array index in Phase 4
-- when array storage is implemented for player IDs.

-- Team 0 player slots
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_0 ON trade_history(player_id_0_0) WHERE player_id_0_0 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_1 ON trade_history(player_id_0_1) WHERE player_id_0_1 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_2 ON trade_history(player_id_0_2) WHERE player_id_0_2 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_3 ON trade_history(player_id_0_3) WHERE player_id_0_3 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_4 ON trade_history(player_id_0_4) WHERE player_id_0_4 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_5 ON trade_history(player_id_0_5) WHERE player_id_0_5 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_6 ON trade_history(player_id_0_6) WHERE player_id_0_6 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_7 ON trade_history(player_id_0_7) WHERE player_id_0_7 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_8 ON trade_history(player_id_0_8) WHERE player_id_0_8 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_0_9 ON trade_history(player_id_0_9) WHERE player_id_0_9 IS NOT NULL;

-- Team 1 player slots
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_0 ON trade_history(player_id_1_0) WHERE player_id_1_0 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_1 ON trade_history(player_id_1_1) WHERE player_id_1_1 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_2 ON trade_history(player_id_1_2) WHERE player_id_1_2 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_3 ON trade_history(player_id_1_3) WHERE player_id_1_3 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_4 ON trade_history(player_id_1_4) WHERE player_id_1_4 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_5 ON trade_history(player_id_1_5) WHERE player_id_1_5 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_6 ON trade_history(player_id_1_6) WHERE player_id_1_6 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_7 ON trade_history(player_id_1_7) WHERE player_id_1_7 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_8 ON trade_history(player_id_1_8) WHERE player_id_1_8 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_history_player_1_9 ON trade_history(player_id_1_9) WHERE player_id_1_9 IS NOT NULL;
