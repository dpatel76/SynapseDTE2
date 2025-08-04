"""Standardize database table names for consistency

Revision ID: standardize_table_names
Revises: 012_add_audit_fields_to_all_tables
Create Date: 2024-01-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'standardize_table_names'
down_revision = '012_add_audit_fields_to_all_tables'
branch_labels = None
depends_on = None


def upgrade():
    """
    Standardize table names to follow consistent naming conventions:
    1. Use plural for entity tables (users, reports, etc.)
    2. Use singular for audit log tables (*_audit_log)
    3. Remove redundant naming
    """
    
    # Fix audit log tables that incorrectly use plural
    op.rename_table('test_execution_audit_logs', 'test_execution_audit_log')
    op.rename_table('observation_management_audit_logs', 'observation_management_audit_log')
    
    # Fix redundant table name
    op.rename_table('testing_test_executions', 'test_executions')
    
    # Standardize entity tables to plural (only those currently singular)
    # Note: Many core tables are already plural (users, reports, documents, etc.)
    # We'll standardize the remaining singular entity tables
    singular_to_plural_mappings = [
        ('audit_log', 'audit_logs'),
        ('llm_audit_log', 'llm_audit_logs'),
        ('version_history', 'universal_version_histories'),
        ('regulatory_data_dictionary', 'regulatory_data_dictionaries'),
        ('cycle_report', 'cycle_reports'),  # Already plural, skip
        ('data_owner_assignment', 'data_owner_assignments'),
        ('attribute_lob_assignment', 'attribute_lob_assignments'),
        ('historical_data_owner_assignment', 'historical_data_owner_assignments'),
        ('data_owner_sla_violation', 'data_owner_sla_violations'),
        ('data_owner_escalation_log', 'data_owner_escalation_logs'),
        ('data_owner_phase_audit_log', 'data_owner_phase_audit_logs'),
        ('data_profiling_phase', 'data_profiling_phases'),
        ('data_profiling_file', 'data_profiling_files'),
        ('profiling_rule', 'profiling_rules'),
        ('profiling_result', 'profiling_results'),
        ('attribute_profiling_score', 'attribute_profiling_scores'),
        ('document_access_log', 'document_access_logs'),
        ('document_extraction', 'document_extractions'),
        ('document_revision', 'document_revisions'),
        ('observation_group', 'observation_groups'),
        ('observation_clarification', 'observation_clarifications'),
        ('test_report_phase', 'test_report_phases'),
        ('test_report_section', 'test_report_sections'),
        ('observation_management_phase', 'observation_management_phases'),
        ('observation_record', 'observation_records'),
        ('observation_impact_assessment', 'observation_impact_assessments'),
        ('observation_approval', 'observation_approvals'),
        ('observation_resolution', 'observation_resolutions'),
        ('observation_management_audit_log', 'observation_management_audit_logs'),
        ('role_permission', 'role_permissions'),
        ('user_role', 'user_roles'),
        ('user_permission', 'user_permissions'),
        ('resource_permission', 'resource_permissions'),
        ('role_hierarchy', 'role_hierarchies'),
        ('permission_audit_log', 'permission_audit_logs'),
        ('data_source', 'data_sources'),
        ('report_attribute', 'report_attributes'),
        ('attribute_version_change_log', 'attribute_version_change_logs'),
        ('attribute_version_comparison', 'attribute_version_comparisons'),
        ('report_owner_assignment', 'report_owner_assignments'),
        ('report_owner_assignment_history', 'report_owner_assignment_histories'),
        ('request_info_phase', 'request_info_phases'),
        ('data_provider_notification', 'data_provider_notifications'),
        ('document_submission', 'document_submissions'),
        ('request_info_audit_log', 'request_info_audit_logs'),
        ('sample_set', 'sample_sets'),
        ('sample_record', 'sample_records'),
        ('sample_validation_result', 'sample_validation_results'),
        ('sample_validation_issue', 'sample_validation_issues'),
        ('sample_approval_history', 'sample_approval_histories'),
        ('llm_sample_generation', 'llm_sample_generations'),
        ('sample_upload_history', 'sample_upload_histories'),
        ('sample_selection_audit_log', 'sample_selection_audit_logs'),
        ('sample_selection_phase', 'sample_selection_phases'),
        ('attribute_scoping_recommendation', 'attribute_scoping_recommendations'),
        ('tester_scoping_decision', 'tester_scoping_decisions'),
        ('scoping_submission', 'scoping_submissions'),
        ('report_owner_scoping_review', 'report_owner_scoping_reviews'),
        ('scoping_audit_log', 'scoping_audit_logs'),
        ('sla_configuration', 'universal_sla_configurations'),
        ('sla_escalation_rule', 'universal_sla_escalation_rules'),
        ('sla_violation_tracking', 'universal_sla_violation_trackings'),
        ('escalation_email_log', 'escalation_email_logs'),
        ('test_execution_phase', 'test_execution_phases'),
        ('test_execution', 'test_executions'),
        ('document_analysis', 'document_analyses'),
        ('database_test', 'database_tests'),
        ('test_result_review', 'test_result_reviews'),
        ('test_comparison', 'test_comparisons'),
        ('bulk_test_execution', 'bulk_test_executions'),
        ('test_execution_audit_log', 'test_execution_audit_logs'),
        ('universal_assignment', 'universal_assignments'),
        ('universal_assignment_history', 'universal_assignment_histories'),
        ('assignment_template', 'assignment_templates'),
        ('data_profiling_rule_version', 'data_profiling_rule_versions'),
        ('test_execution_version', 'test_execution_versions'),
        ('observation_version', 'observation_versions'),
        ('scoping_decision_version', 'scoping_decision_versions'),
        ('versioned_attribute_scoping_recommendation', 'versioned_attribute_scoping_recommendations'),
        ('workflow_phase', 'workflow_phases'),
        ('workflow_activity', 'workflow_activities'),
        ('workflow_activity_history', 'workflow_activity_histories'),
        ('workflow_activity_dependency', 'workflow_activity_dependencies'),
        ('workflow_activity_template', 'workflow_activity_templates'),
        ('workflow_execution', 'workflow_executions'),
        ('workflow_step', 'workflow_steps'),
        ('workflow_transition', 'workflow_transitions'),
        ('workflow_metric', 'workflow_metrics'),
        ('workflow_alert', 'workflow_alerts'),
        ('phase_metric', 'phase_metrics'),
        ('execution_metric', 'execution_metrics'),
    ]
    
    # Apply renames only for tables that exist and aren't already plural
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    for old_name, new_name in singular_to_plural_mappings:
        if old_name in existing_tables and new_name not in existing_tables:
            op.rename_table(old_name, new_name)


def downgrade():
    """Revert table names to their original state"""
    
    # Revert audit log tables
    op.rename_table('test_execution_audit_log', 'test_execution_audit_logs')
    op.rename_table('observation_management_audit_log', 'observation_management_audit_logs')
    
    # Revert redundant table name
    op.rename_table('test_executions', 'testing_test_executions')
    
    # Revert plural to singular mappings
    # This would be the reverse of the upgrade mappings
    # Not implementing full reversal as it's rarely needed