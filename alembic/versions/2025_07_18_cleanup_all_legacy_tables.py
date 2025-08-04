"""Cleanup All Legacy Tables

Revision ID: 2025_07_18_cleanup_all_legacy_tables
Revises: 2025_07_18_drop_legacy_planning_tables
Create Date: 2025-07-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers
revision = '2025_07_18_cleanup_all_legacy_tables'
down_revision = '2025_07_18_drop_legacy_planning_tables'
branch_labels = None
depends_on = None

def upgrade():
    """Cleanup all legacy tables and obsolete database objects"""
    
    # =============================================================================
    # PHASE 1: DROP SAMPLE SELECTION LEGACY TABLES
    # =============================================================================
    
    print("Dropping sample selection legacy tables...")
    
    # Drop child tables first (to avoid foreign key constraint issues)
    op.execute("DROP TABLE IF EXISTS sample_submission_items CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_feedback CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_audit_logs CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_validation_issues CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_validation_results CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_approval_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_upload_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS llm_sample_generations CASCADE;")
    
    # Drop main sample tables
    op.execute("DROP TABLE IF EXISTS individual_samples CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_records CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_submissions CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_sets CASCADE;")
    
    # Drop sample selection phase tracking tables
    op.execute("DROP TABLE IF EXISTS sample_selection_phases CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_selection_audit_logs CASCADE;")
    
    # Drop enhancement tables
    op.execute("DROP TABLE IF EXISTS sample_pools CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_lineage CASCADE;")
    op.execute("DROP TABLE IF EXISTS intelligent_samples CASCADE;")
    op.execute("DROP TABLE IF EXISTS sampling_rules CASCADE;")
    op.execute("DROP TABLE IF EXISTS intelligent_sampling_jobs CASCADE;")
    
    # =============================================================================
    # PHASE 2: DROP VERSIONING LEGACY TABLES  
    # =============================================================================
    
    print("Dropping versioning legacy tables...")
    
    # Drop old versioning tables
    op.execute("DROP TABLE IF EXISTS version_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_version_operations CASCADE;")
    op.execute("DROP TABLE IF EXISTS planning_phase_versions CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_selection_versions_old CASCADE;")
    op.execute("DROP TABLE IF EXISTS data_profiling_versions_old CASCADE;")
    op.execute("DROP TABLE IF EXISTS scoping_versions_old CASCADE;")
    op.execute("DROP TABLE IF EXISTS observation_versions_old CASCADE;")
    op.execute("DROP TABLE IF EXISTS test_report_versions_old CASCADE;")
    
    # =============================================================================
    # PHASE 3: DROP LEGACY PHASE TRACKING TABLES
    # =============================================================================
    
    print("Dropping legacy phase tracking tables...")
    
    # Drop old phase tracking tables (replaced by unified workflow activities)
    op.execute("DROP TABLE IF EXISTS data_profiling_phases CASCADE;")
    op.execute("DROP TABLE IF EXISTS scoping_phases CASCADE;")
    op.execute("DROP TABLE IF EXISTS test_execution_phases CASCADE;")
    op.execute("DROP TABLE IF EXISTS observation_management_phases CASCADE;")
    op.execute("DROP TABLE IF EXISTS test_report_phases CASCADE;")
    op.execute("DROP TABLE IF EXISTS request_info_phases CASCADE;")
    
    # =============================================================================
    # PHASE 4: DROP LEGACY DECISION TABLES
    # =============================================================================
    
    print("Dropping legacy decision tables...")
    
    # Drop old decision tracking tables
    op.execute("DROP TABLE IF EXISTS attribute_decisions_old CASCADE;")
    op.execute("DROP TABLE IF EXISTS sample_decisions_old CASCADE;")
    op.execute("DROP TABLE IF EXISTS scoping_decisions_old CASCADE;")
    op.execute("DROP TABLE IF EXISTS observation_decisions_old CASCADE;")
    op.execute("DROP TABLE IF EXISTS cycle_report_scoping_decisions CASCADE;")
    
    # =============================================================================
    # PHASE 5: DROP LEGACY WORKFLOW TABLES
    # =============================================================================
    
    print("Dropping legacy workflow tables...")
    
    # Drop old workflow tracking tables
    op.execute("DROP TABLE IF EXISTS workflow_executions CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_steps CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_transitions CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_metrics CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_alerts CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_activity_retry_log CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_compensation_log CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_retry_policy_config CASCADE;")
    
    # =============================================================================
    # PHASE 6: DROP DATA SOURCE CONFIG LEGACY TABLES (if not already done)
    # =============================================================================
    
    print("Dropping data source configuration legacy tables...")
    
    # These might have been dropped already, but ensure they're cleaned up
    op.execute("DROP TABLE IF EXISTS data_source_config CASCADE;")
    op.execute("DROP TABLE IF EXISTS data_sources_v2 CASCADE;")
    op.execute("DROP TABLE IF EXISTS cycle_report_data_sources CASCADE;")
    op.execute("DROP TABLE IF EXISTS cycle_report_pde_mappings CASCADE;")
    op.execute("DROP TABLE IF EXISTS cycle_report_pde_classifications CASCADE;")
    
    # =============================================================================
    # PHASE 7: DROP MIGRATION TRACKING TABLES
    # =============================================================================
    
    print("Dropping migration tracking tables...")
    
    # Drop temporary migration tracking tables
    op.execute("DROP TABLE IF EXISTS sample_selection_migration_tracking CASCADE;")
    op.execute("DROP TABLE IF EXISTS scoping_migration_tracking CASCADE;")
    op.execute("DROP TABLE IF EXISTS data_profiling_migration_tracking CASCADE;")
    op.execute("DROP TABLE IF EXISTS planning_migration_tracking CASCADE;")
    
    # =============================================================================
    # PHASE 8: DROP LEGACY SEQUENCES
    # =============================================================================
    
    print("Dropping legacy sequences...")
    
    # Drop sequences for dropped tables
    op.execute("DROP SEQUENCE IF EXISTS sample_sets_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS sample_records_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS sample_submissions_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS individual_samples_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS sample_validation_results_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS sample_validation_issues_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS sample_approval_history_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS sample_upload_history_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS sample_submission_items_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS sample_feedback_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS sample_audit_logs_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS llm_sample_generations_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS version_history_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS workflow_version_operations_id_seq CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS data_source_config_id_seq CASCADE;")
    
    # =============================================================================
    # PHASE 9: DROP LEGACY ENUMS
    # =============================================================================
    
    print("Dropping legacy enums...")
    
    # Drop enums from sample selection
    op.execute("DROP TYPE IF EXISTS testerdecision CASCADE;")
    op.execute("DROP TYPE IF EXISTS reportownerdecision CASCADE;")
    op.execute("DROP TYPE IF EXISTS submissionstatus CASCADE;")
    op.execute("DROP TYPE IF EXISTS samplestatus CASCADE;")
    op.execute("DROP TYPE IF EXISTS sample_validation_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS sample_decision_status CASCADE;")
    
    # Drop enums from versioning
    op.execute("DROP TYPE IF EXISTS version_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS version_change_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS workflow_version_status CASCADE;")
    
    # Drop enums from data source config
    op.execute("DROP TYPE IF EXISTS data_source_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS data_source_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS pde_mapping_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS pde_classification_status CASCADE;")
    
    # Drop other legacy enums
    op.execute("DROP TYPE IF EXISTS phase_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS decision_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS workflow_status CASCADE;")
    
    # =============================================================================
    # PHASE 10: DROP ORPHANED INDEXES AND CONSTRAINTS
    # =============================================================================
    
    print("Dropping orphaned indexes...")
    
    # Drop any remaining indexes that might be orphaned
    op.execute("DROP INDEX IF EXISTS idx_sample_sets_cycle_report CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_sample_records_sample_set CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_sample_submissions_cycle_report CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_individual_samples_submission CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_sample_validation_results_sample CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_version_history_entity CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_workflow_version_operations_entity CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_data_source_config_cycle_report CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_legacy_planning_attributes CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_legacy_planning_mappings CASCADE;")
    
    # =============================================================================
    # PHASE 11: CLEAN UP FUNCTIONS AND TRIGGERS
    # =============================================================================
    
    print("Dropping legacy functions and triggers...")
    
    # Drop any legacy functions
    op.execute("DROP FUNCTION IF EXISTS update_sample_set_total() CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS calculate_sample_validation_score() CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS update_version_history() CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS update_workflow_version_status() CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS legacy_planning_attribute_trigger_fn() CASCADE;")
    
    # Drop any legacy triggers (they should be dropped with functions, but being explicit)
    op.execute("DROP TRIGGER IF EXISTS tr_sample_set_update ON sample_sets CASCADE;")
    op.execute("DROP TRIGGER IF EXISTS tr_version_history_update ON version_history CASCADE;")
    op.execute("DROP TRIGGER IF EXISTS tr_workflow_version_update ON workflow_version_operations CASCADE;")
    
    print("✅ Legacy table cleanup completed successfully!")
    print("📊 Cleaned up:")
    print("   - Sample selection legacy tables (15+ tables)")
    print("   - Versioning legacy tables (8+ tables)")
    print("   - Phase tracking legacy tables (6+ tables)")
    print("   - Decision tracking legacy tables (5+ tables)")
    print("   - Workflow legacy tables (8+ tables)")
    print("   - Data source config legacy tables (5+ tables)")
    print("   - Migration tracking tables (4+ tables)")
    print("   - Legacy sequences (15+ sequences)")
    print("   - Legacy enums (20+ enums)")
    print("   - Orphaned indexes and constraints")
    print("   - Legacy functions and triggers")


def downgrade():
    """This migration is not reversible as it drops legacy tables"""
    
    # Note: This migration is not reversible because we're dropping legacy tables
    # that have been replaced by the new unified architecture.
    # If you need to rollback, you would need to restore from a backup.
    
    raise Exception(
        "Cannot rollback this migration. Legacy tables have been dropped "
        "and replaced by the new unified architecture. To rollback, restore from backup."
    )