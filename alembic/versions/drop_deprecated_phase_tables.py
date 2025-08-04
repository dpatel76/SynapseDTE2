"""Drop deprecated phase tables

Revision ID: drop_deprecated_phase_tables
Revises: create_new_required_tables
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'drop_deprecated_phase_tables'
down_revision = 'create_new_required_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Drop foreign key constraints first
    op.drop_constraint('data_profiling_files_phase_id_fkey', 'data_profiling_files', type_='foreignkey')
    op.drop_constraint('profiling_rules_phase_id_fkey', 'profiling_rules', type_='foreignkey')
    op.drop_constraint('profiling_results_phase_id_fkey', 'profiling_results', type_='foreignkey')
    op.drop_constraint('attribute_profiling_scores_phase_id_fkey', 'attribute_profiling_scores', type_='foreignkey')
    
    op.drop_constraint('test_executions_phase_id_fkey', 'test_executions', type_='foreignkey')
    op.drop_constraint('test_execution_audit_log_phase_id_fkey', 'test_execution_audit_log', type_='foreignkey')
    
    op.drop_constraint('observation_records_phase_id_fkey', 'observation_records', type_='foreignkey')
    op.drop_constraint('observation_records_backup_phase_id_fkey', 'observation_records_backup', type_='foreignkey')
    op.drop_constraint('observation_management_audit_log_phase_id_fkey', 'observation_management_audit_log', type_='foreignkey')
    
    op.drop_constraint('test_report_sections_phase_id_fkey', 'test_report_sections', type_='foreignkey')
    
    # Drop the deprecated phase tables
    op.drop_table('data_profiling_phases')
    op.drop_table('sample_selection_phases')
    op.drop_table('test_execution_phases')
    op.drop_table('observation_management_phases')
    op.drop_table('test_report_phases')
    
    # Drop other deprecated tables if they exist
    op.execute("DROP TABLE IF EXISTS cycle_report_request_info_phases CASCADE")
    op.execute("DROP TABLE IF EXISTS cycle_report_sample_sets CASCADE")
    op.execute("DROP TABLE IF EXISTS data_owner_sla_violations CASCADE")
    op.execute("DROP TABLE IF EXISTS data_owner_escalation_log CASCADE")
    op.execute("DROP TABLE IF EXISTS data_owner_notifications CASCADE")


def downgrade():
    # Recreate tables - would need full schema definitions
    pass