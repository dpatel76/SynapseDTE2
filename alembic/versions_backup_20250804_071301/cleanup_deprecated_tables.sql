-- Cleanup deprecated tables after moving to universal assignments

-- Drop the old cdo_notifications table (now data_executive_notifications) 
-- since it's replaced by universal assignments
DROP TABLE IF EXISTS data_executive_notifications;

-- Also drop the original table name if it still exists
DROP TABLE IF EXISTS cdo_notifications;

-- Remove any foreign key constraints that might still reference these tables
-- This is handled automatically by CASCADE in most cases