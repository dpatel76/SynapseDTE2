-- Add unique constraint to prevent duplicate assignments
-- This ensures that for each phase, there can only be one assignment per attribute+LOB combination

-- First, check if any duplicates exist
SELECT phase_id, attribute_id, lob_id, COUNT(*) as count
FROM cycle_report_data_owner_lob_attribute_assignments
GROUP BY phase_id, attribute_id, lob_id
HAVING COUNT(*) > 1;

-- If the above query returns any results, you'll need to clean them up first
-- Then add the unique constraint

-- Create unique index (which enforces uniqueness)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_phase_attribute_lob 
ON cycle_report_data_owner_lob_attribute_assignments(phase_id, attribute_id, lob_id);

-- Alternatively, add a unique constraint
-- ALTER TABLE cycle_report_data_owner_lob_attribute_assignments
-- ADD CONSTRAINT unique_phase_attribute_lob UNIQUE (phase_id, attribute_id, lob_id);