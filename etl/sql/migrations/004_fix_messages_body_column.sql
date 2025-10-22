-- Migration: Fix messages.body column to allow NULL and set default
-- Date: 2025-10-22
-- Issue: messages.csv from OOTP doesn't include body column, causing NOT NULL violation

-- Drop NOT NULL constraint and add default empty string
ALTER TABLE messages
    ALTER COLUMN body DROP NOT NULL,
    ALTER COLUMN body SET DEFAULT '';

-- Add comment explaining the change
COMMENT ON COLUMN messages.body IS 'Message body text - may be empty as OOTP CSV export does not always include this field';
