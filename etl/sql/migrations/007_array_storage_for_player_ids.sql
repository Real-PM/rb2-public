-- Migration 007: Array Storage for Player IDs in trade_history and messages
-- Purpose: Replace 20-way OR filters with efficient array containment queries using GIN indexes
-- Expected Impact: Reduce player lookup queries from ~5s to <100ms
-- Date: 2025-10-24
-- Related: Phase 4D optimization (docs/optimization/phase4d_under_5s_checklist.md)

-- ============================================================================
-- STEP 1: Add array columns to trade_history
-- ============================================================================

ALTER TABLE trade_history
ADD COLUMN IF NOT EXISTS all_player_ids INTEGER[];

-- Populate the array from existing columns
UPDATE trade_history
SET all_player_ids = (
    SELECT array_agg(DISTINCT pid)
    FROM unnest(ARRAY[
        player_id_0_0, player_id_0_1, player_id_0_2, player_id_0_3, player_id_0_4,
        player_id_0_5, player_id_0_6, player_id_0_7, player_id_0_8, player_id_0_9,
        player_id_1_0, player_id_1_1, player_id_1_2, player_id_1_3, player_id_1_4,
        player_id_1_5, player_id_1_6, player_id_1_7, player_id_1_8, player_id_1_9
    ]) AS pid
    WHERE pid IS NOT NULL
);

-- Create GIN index for fast array containment queries
CREATE INDEX IF NOT EXISTS idx_trade_history_all_players_gin
ON trade_history USING GIN (all_player_ids);

-- ============================================================================
-- STEP 2: Add array columns to messages
-- ============================================================================

ALTER TABLE messages
ADD COLUMN IF NOT EXISTS all_player_ids INTEGER[];

-- Populate the array from existing columns
UPDATE messages
SET all_player_ids = (
    SELECT array_agg(DISTINCT pid)
    FROM unnest(ARRAY[
        player_id_0, player_id_1, player_id_2, player_id_3, player_id_4,
        player_id_5, player_id_6, player_id_7, player_id_8, player_id_9
    ]) AS pid
    WHERE pid IS NOT NULL
);

-- Create GIN index for fast array containment queries
CREATE INDEX IF NOT EXISTS idx_messages_all_players_gin
ON messages USING GIN (all_player_ids);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify trade_history array population
-- Expected: Should match count of trades with player_id in any column
DO $$
DECLARE
    array_count INTEGER;
    or_count INTEGER;
BEGIN
    -- Count using new array column (for a sample player)
    SELECT COUNT(*) INTO array_count
    FROM trade_history
    WHERE 3000 = ANY(all_player_ids);

    -- Count using old OR filter (for same player)
    SELECT COUNT(*) INTO or_count
    FROM trade_history
    WHERE player_id_0_0 = 3000 OR player_id_0_1 = 3000 OR player_id_0_2 = 3000 OR
          player_id_0_3 = 3000 OR player_id_0_4 = 3000 OR player_id_0_5 = 3000 OR
          player_id_0_6 = 3000 OR player_id_0_7 = 3000 OR player_id_0_8 = 3000 OR
          player_id_0_9 = 3000 OR player_id_1_0 = 3000 OR player_id_1_1 = 3000 OR
          player_id_1_2 = 3000 OR player_id_1_3 = 3000 OR player_id_1_4 = 3000 OR
          player_id_1_5 = 3000 OR player_id_1_6 = 3000 OR player_id_1_7 = 3000 OR
          player_id_1_8 = 3000 OR player_id_1_9 = 3000;

    RAISE NOTICE 'Trade History - Array method: %, OR method: %', array_count, or_count;

    IF array_count != or_count THEN
        RAISE WARNING 'Mismatch in trade_history counts! Array: %, OR: %', array_count, or_count;
    END IF;
END $$;

-- Verify messages array population
DO $$
DECLARE
    array_count INTEGER;
    or_count INTEGER;
BEGIN
    -- Count using new array column (for a sample player)
    SELECT COUNT(*) INTO array_count
    FROM messages
    WHERE 3000 = ANY(all_player_ids);

    -- Count using old OR filter (for same player)
    SELECT COUNT(*) INTO or_count
    FROM messages
    WHERE player_id_0 = 3000 OR player_id_1 = 3000 OR player_id_2 = 3000 OR
          player_id_3 = 3000 OR player_id_4 = 3000 OR player_id_5 = 3000 OR
          player_id_6 = 3000 OR player_id_7 = 3000 OR player_id_8 = 3000 OR
          player_id_9 = 3000;

    RAISE NOTICE 'Messages - Array method: %, OR method: %', array_count, or_count;

    IF array_count != or_count THEN
        RAISE WARNING 'Mismatch in messages counts! Array: %, OR: %', array_count, or_count;
    END IF;
END $$;

-- ============================================================================
-- STATISTICS
-- ============================================================================

-- Show statistics about array sizes
SELECT
    'trade_history' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE all_player_ids IS NOT NULL) as rows_with_players,
    AVG(array_length(all_player_ids, 1)) as avg_players_per_trade,
    MAX(array_length(all_player_ids, 1)) as max_players_per_trade
FROM trade_history

UNION ALL

SELECT
    'messages' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE all_player_ids IS NOT NULL) as rows_with_players,
    AVG(array_length(all_player_ids, 1)) as avg_players_per_message,
    MAX(array_length(all_player_ids, 1)) as max_players_per_message
FROM messages;

-- ============================================================================
-- NOTES
-- ============================================================================

-- Performance Testing:
-- After migration, test query performance with:
--
-- EXPLAIN ANALYZE
-- SELECT * FROM trade_history WHERE 3000 = ANY(all_player_ids);
--
-- Expected: GIN index scan with execution time < 1ms

-- Future Steps:
-- 1. Update SQLAlchemy models (web/app/models/history.py, web/app/models/message.py)
-- 2. Update service queries (web/app/services/player_service.py)
-- 3. Update ETL to populate all_player_ids on new data loads
-- 4. After verification period, can drop old player_id_X_X columns to save space

-- Rollback (if needed):
-- DROP INDEX IF EXISTS idx_trade_history_all_players_gin;
-- DROP INDEX IF EXISTS idx_messages_all_players_gin;
-- ALTER TABLE trade_history DROP COLUMN IF EXISTS all_player_ids;
-- ALTER TABLE messages DROP COLUMN IF EXISTS all_player_ids;
