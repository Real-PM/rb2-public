-- Migration: Fix numeric precision issues in team and league history stats
-- Date: 2025-10-22
-- Issue: sbp (stolen base percentage) DECIMAL(6,4) can't store 100.0 (perfect success rate)
-- Issue: rc27 may need headroom for extreme values

-- Fix team_history_batting_stats
ALTER TABLE team_history_batting_stats
    ALTER COLUMN sbp TYPE DECIMAL(5,2),  -- 0.00 to 100.00 percentage format
    ALTER COLUMN rc27 TYPE DECIMAL(7,4);  -- Increased headroom for extreme values

-- Fix league_history_batting_stats
ALTER TABLE league_history_batting_stats
    ALTER COLUMN sbp TYPE DECIMAL(5,2);  -- 0.00 to 100.00 percentage format

-- Add comments
COMMENT ON COLUMN team_history_batting_stats.sbp IS 'Stolen base percentage (0.00-100.00)';
COMMENT ON COLUMN team_history_batting_stats.rc27 IS 'Runs created per 27 outs - increased precision for extreme values';
COMMENT ON COLUMN league_history_batting_stats.sbp IS 'Stolen base percentage (0.00-100.00)';
