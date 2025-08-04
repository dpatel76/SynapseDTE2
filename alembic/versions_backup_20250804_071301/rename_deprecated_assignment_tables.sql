-- Rename deprecated assignment and notification tables to _backup
-- This script renames tables that have been replaced by the Universal Assignment framework

-- 1. Data Executive Notifications (replaced by universal assignments)
ALTER TABLE IF EXISTS data_executive_notifications RENAME TO data_executive_notifications_backup;

-- 2. Data Provider Notifications (replaced by universal assignments)
ALTER TABLE IF EXISTS data_provider_notifications RENAME TO data_provider_notifications_backup;

-- 3. Report Owner Assignments (to be migrated to universal assignments)
ALTER TABLE IF EXISTS report_owner_assignments RENAME TO report_owner_assignments_backup;

-- 4. Report Owner Assignment Histories (to be migrated)
ALTER TABLE IF EXISTS report_owner_assignment_histories RENAME TO report_owner_assignment_histories_backup;

-- 5. Attribute LOB Assignments (to be evaluated for migration)
ALTER TABLE IF EXISTS attribute_lob_assignments RENAME TO attribute_lob_assignments_backup;

-- 6. Data Provider Assignments (if not being used)
ALTER TABLE IF EXISTS data_provider_assignments RENAME TO data_provider_assignments_backup;

-- 7. Entity Assignments (if not being used)
ALTER TABLE IF EXISTS entity_assignments RENAME TO entity_assignments_backup;

-- 8. Assignment Templates (if not being used with universal assignments)
ALTER TABLE IF EXISTS assignment_templates RENAME TO assignment_templates_backup;

-- Note: Keeping these tables as-is:
-- - universal_assignments (new framework)
-- - universal_assignment_histories (new framework)
-- - historical_data_owner_assignments (for historical tracking)
-- - historical_data_provider_assignments (for historical tracking)
-- - report_owner_executives (many-to-many relationship table)