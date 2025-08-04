"""Add missing indexes for foreign keys and common queries

Revision ID: 001_add_missing_indexes
Revises: 
Create Date: 2024-12-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_missing_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing indexes for better query performance"""
    
    # Workflow phases indexes
    op.create_index('idx_workflow_phases_cycle_id', 'workflow_phases', ['cycle_id'])
    op.create_index('idx_workflow_phases_report_id', 'workflow_phases', ['report_id'])
    op.create_index('idx_workflow_phases_cycle_report', 'workflow_phases', ['cycle_id', 'report_id'])
    op.create_index('idx_workflow_phases_phase_name', 'workflow_phases', ['phase_name'])
    
    # Report attributes indexes
    op.create_index('idx_report_attributes_cycle_id', 'report_attributes', ['cycle_id'])
    op.create_index('idx_report_attributes_report_id', 'report_attributes', ['report_id'])
    op.create_index('idx_report_attributes_cycle_report', 'report_attributes', ['cycle_id', 'report_id'])
    op.create_index('idx_report_attributes_master_id', 'report_attributes', ['master_attribute_id'])
    
    # Data provider assignments indexes
    op.create_index('idx_data_owner_assignments_cycle_id', 'data_owner_assignments', ['cycle_id'])
    op.create_index('idx_data_owner_assignments_report_id', 'data_owner_assignments', ['report_id'])
    op.create_index('idx_data_owner_assignments_cycle_report', 'data_owner_assignments', ['cycle_id', 'report_id'])
    op.create_index('idx_data_owner_assignments_provider_id', 'data_owner_assignments', ['data_owner_id'])
    op.create_index('idx_data_owner_assignments_attribute_id', 'data_owner_assignments', ['attribute_id'])
    
    # Test executions indexes
    op.create_index('idx_test_executions_cycle_id', 'testing_test_executions', ['cycle_id'])
    op.create_index('idx_test_executions_report_id', 'testing_test_executions', ['report_id'])
    op.create_index('idx_test_executions_cycle_report', 'testing_test_executions', ['cycle_id', 'report_id'])
    op.create_index('idx_test_executions_attribute_id', 'testing_test_executions', ['attribute_id'])
    op.create_index('idx_test_executions_status', 'testing_test_executions', ['test_status'])
    
    # Sample sets indexes
    op.create_index('idx_sample_sets_cycle_id', 'sample_sets', ['cycle_id'])
    op.create_index('idx_sample_sets_report_id', 'sample_sets', ['report_id'])
    op.create_index('idx_sample_sets_cycle_report', 'sample_sets', ['cycle_id', 'report_id'])
    op.create_index('idx_sample_sets_master_set_id', 'sample_sets', ['master_set_id'])
    
    # Scoping submissions indexes
    op.create_index('idx_scoping_submissions_cycle_id', 'scoping_submissions', ['cycle_id'])
    op.create_index('idx_scoping_submissions_report_id', 'scoping_submissions', ['report_id'])
    op.create_index('idx_scoping_submissions_cycle_report', 'scoping_submissions', ['cycle_id', 'report_id'])
    op.create_index('idx_scoping_submissions_status', 'scoping_submissions', ['status'])
    
    # Observations indexes
    op.create_index('idx_observations_cycle_id', 'observations', ['cycle_id'])
    op.create_index('idx_observations_report_id', 'observations', ['report_id'])
    op.create_index('idx_observations_cycle_report', 'observations', ['cycle_id', 'report_id'])
    op.create_index('idx_observations_status', 'observations', ['status'])
    
    # Audit log indexes
    op.create_index('idx_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('idx_audit_log_timestamp', 'audit_log', ['timestamp'])
    op.create_index('idx_audit_log_entity', 'audit_log', ['entity_type', 'entity_id'])
    
    # LLM audit log indexes
    op.create_index('idx_llm_audit_log_user_id', 'llm_audit_log', ['user_id'])
    op.create_index('idx_llm_audit_log_timestamp', 'llm_audit_log', ['timestamp'])
    op.create_index('idx_llm_audit_log_operation', 'llm_audit_log', ['operation_type'])
    
    # SLA violation tracking indexes
    op.create_index('idx_sla_violations_entity', 'sla_violation_tracking', ['entity_type', 'entity_id'])
    op.create_index('idx_sla_violations_status', 'sla_violation_tracking', ['violation_status'])
    op.create_index('idx_sla_violations_due_date', 'sla_violation_tracking', ['due_date'])
    
    # Document access logs indexes
    op.create_index('idx_document_access_logs_user_id', 'document_access_logs', ['user_id'])
    op.create_index('idx_document_access_logs_document_id', 'document_access_logs', ['document_id'])
    op.create_index('idx_document_access_logs_timestamp', 'document_access_logs', ['accessed_at'])
    
    # Cycle reports composite unique constraint
    op.create_unique_constraint('uq_cycle_reports_cycle_report', 'cycle_reports', ['cycle_id', 'report_id'])


def downgrade() -> None:
    """Remove all created indexes"""
    
    # Drop all indexes in reverse order
    op.drop_constraint('uq_cycle_reports_cycle_report', 'cycle_reports', type_='unique')
    
    # Document access logs
    op.drop_index('idx_document_access_logs_timestamp', 'document_access_logs')
    op.drop_index('idx_document_access_logs_document_id', 'document_access_logs')
    op.drop_index('idx_document_access_logs_user_id', 'document_access_logs')
    
    # SLA violations
    op.drop_index('idx_sla_violations_due_date', 'sla_violation_tracking')
    op.drop_index('idx_sla_violations_status', 'sla_violation_tracking')
    op.drop_index('idx_sla_violations_entity', 'sla_violation_tracking')
    
    # LLM audit log
    op.drop_index('idx_llm_audit_log_operation', 'llm_audit_log')
    op.drop_index('idx_llm_audit_log_timestamp', 'llm_audit_log')
    op.drop_index('idx_llm_audit_log_user_id', 'llm_audit_log')
    
    # Audit log
    op.drop_index('idx_audit_log_entity', 'audit_log')
    op.drop_index('idx_audit_log_timestamp', 'audit_log')
    op.drop_index('idx_audit_log_user_id', 'audit_log')
    
    # Observations
    op.drop_index('idx_observations_status', 'observations')
    op.drop_index('idx_observations_cycle_report', 'observations')
    op.drop_index('idx_observations_report_id', 'observations')
    op.drop_index('idx_observations_cycle_id', 'observations')
    
    # Scoping submissions
    op.drop_index('idx_scoping_submissions_status', 'scoping_submissions')
    op.drop_index('idx_scoping_submissions_cycle_report', 'scoping_submissions')
    op.drop_index('idx_scoping_submissions_report_id', 'scoping_submissions')
    op.drop_index('idx_scoping_submissions_cycle_id', 'scoping_submissions')
    
    # Sample sets
    op.drop_index('idx_sample_sets_master_set_id', 'sample_sets')
    op.drop_index('idx_sample_sets_cycle_report', 'sample_sets')
    op.drop_index('idx_sample_sets_report_id', 'sample_sets')
    op.drop_index('idx_sample_sets_cycle_id', 'sample_sets')
    
    # Test executions
    op.drop_index('idx_test_executions_status', 'testing_test_executions')
    op.drop_index('idx_test_executions_attribute_id', 'testing_test_executions')
    op.drop_index('idx_test_executions_cycle_report', 'testing_test_executions')
    op.drop_index('idx_test_executions_report_id', 'testing_test_executions')
    op.drop_index('idx_test_executions_cycle_id', 'testing_test_executions')
    
    # Data provider assignments
    op.drop_index('idx_data_owner_assignments_attribute_id', 'data_owner_assignments')
    op.drop_index('idx_data_owner_assignments_provider_id', 'data_owner_assignments')
    op.drop_index('idx_data_owner_assignments_cycle_report', 'data_owner_assignments')
    op.drop_index('idx_data_owner_assignments_report_id', 'data_owner_assignments')
    op.drop_index('idx_data_owner_assignments_cycle_id', 'data_owner_assignments')
    
    # Report attributes
    op.drop_index('idx_report_attributes_master_id', 'report_attributes')
    op.drop_index('idx_report_attributes_cycle_report', 'report_attributes')
    op.drop_index('idx_report_attributes_report_id', 'report_attributes')
    op.drop_index('idx_report_attributes_cycle_id', 'report_attributes')
    
    # Workflow phases
    op.drop_index('idx_workflow_phases_phase_name', 'workflow_phases')
    op.drop_index('idx_workflow_phases_cycle_report', 'workflow_phases')
    op.drop_index('idx_workflow_phases_report_id', 'workflow_phases')
    op.drop_index('idx_workflow_phases_cycle_id', 'workflow_phases')