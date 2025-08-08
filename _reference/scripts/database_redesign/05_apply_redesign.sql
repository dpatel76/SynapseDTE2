-- Master script to apply complete database redesign
-- Run this script to create all tables in the correct order

-- Set up the database
\echo 'Starting complete database redesign...'
\echo '====================================='

-- Run scripts in order
\echo 'Creating base tables...'
\i 01_create_base_tables.sql

\echo 'Creating phase-specific tables...'
\i 02_create_phase_tables.sql

\echo 'Creating audit tables...'
\i 03_create_audit_tables.sql

\echo 'Creating universal assignment system...'
\i 04_create_universal_assignments.sql

\echo '====================================='
\echo 'Database redesign complete!'
\echo ''
\echo 'Summary of created objects:'
\echo '- Base tables: users, lobs, report_inventory, test_cycles, cycle_reports, data_sources'
\echo '- Phase tables: 9 phases with cycle_report_* naming pattern'
\echo '- Version history tables for versioned entities'
\echo '- Audit tables for compliance and tracking'
\echo '- Universal assignment system for flexible user assignments'
\echo '- RBAC tables for granular permissions'
\echo ''
\echo 'Next steps:'
\echo '1. Load reference data (permissions, workflow configuration)'
\echo '2. Migrate existing data if needed'
\echo '3. Update application models to use new schema'
\echo '4. Test all phases with sample data'