"""Request for Information phase enhancements
Revision ID: 2025_01_25_001
Revises: latest
Create Date: 2025-01-25 10:00:00.000000

This migration adds missing functionality for Request for Information phase:
1. Data source configurations for test cases
2. Query management for test cases
3. Revision request tracking
4. Query execution audit
5. Enhanced test case management

Naming convention:
- cycle_report_test_cases_* for all test case related tables
- No request_info prefix needed since context is clear
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers
revision = '2025_01_25_001'
down_revision = None  # Update with latest revision
branch_labels = None
depends_on = None


def upgrade():
    """Apply database enhancements for Request for Information phase"""
    
    # 1. Create reusable data source configurations table
    op.create_table(
        'cycle_report_test_cases_data_sources',
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False, index=True),
        sa.Column('cycle_id', sa.Integer, sa.ForeignKey('test_cycles.cycle_id'), nullable=False, index=True),
        sa.Column('report_id', sa.Integer, sa.ForeignKey('reports.id'), nullable=False, index=True),
        sa.Column('planning_data_source_id', sa.Integer, sa.ForeignKey('cycle_report_planning_data_sources.id'), nullable=False),
        sa.Column('source_name', sa.String(255), nullable=False),
        sa.Column('source_description', sa.Text, nullable=True),
        sa.Column('connection_validated', sa.Boolean, nullable=False, default=False),
        sa.Column('validation_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('usage_count', sa.Integer, nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('phase_id', 'source_name', name='uq_test_cases_data_source_phase_name')
    )
    
    # 2. Create test case specific queries table
    op.create_table(
        'cycle_report_test_cases_queries',
        sa.Column('query_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('test_case_id', sa.Integer, sa.ForeignKey('cycle_report_test_cases.id'), nullable=False, index=True),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cycle_report_test_cases_data_sources.data_source_id'), nullable=False),
        sa.Column('query_text', sa.Text, nullable=False),
        sa.Column('query_parameters', postgresql.JSONB, nullable=True),  # Runtime parameters
        sa.Column('attribute_mappings', postgresql.JSONB, nullable=False),  # Maps result columns to attributes
        sa.Column('primary_key_columns', postgresql.JSONB, nullable=False),  # Which columns are PKs
        sa.Column('target_attribute', sa.String(255), nullable=False),  # The non-PK attribute being tested
        sa.Column('is_template', sa.Boolean, nullable=False, default=False),  # Can be reused as template
        sa.Column('template_name', sa.String(255), nullable=True),  # Name if saved as template
        sa.Column('validation_status', sa.Enum('pending', 'valid', 'invalid', name='query_validation_status_enum'), nullable=False, default='pending'),
        sa.Column('validation_notes', sa.Text, nullable=True),
        sa.Column('validated_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("(is_template = false) OR (is_template = true AND template_name IS NOT NULL)", name='check_template_name'),
        sa.UniqueConstraint('test_case_id', 'is_active', name='uq_test_case_active_query', postgresql_where=sa.text('is_active = true'))
    )
    
    # 3. Create revision requests table for evidence resubmission workflow
    op.create_table(
        'cycle_report_test_cases_revision_requests',
        sa.Column('revision_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False, index=True),
        sa.Column('test_case_id', sa.Integer, sa.ForeignKey('cycle_report_test_cases.id'), nullable=False, index=True),
        sa.Column('current_evidence_id', sa.Integer, sa.ForeignKey('cycle_report_request_info_testcase_source_evidence.id'), nullable=False),
        sa.Column('revision_number', sa.Integer, nullable=False, default=1),
        sa.Column('revision_type', sa.Enum('document_quality', 'missing_data', 'incorrect_data', 'additional_info', 'query_issue', name='revision_type_enum'), nullable=False),
        sa.Column('revision_reason', sa.Text, nullable=False),
        sa.Column('specific_requirements', postgresql.JSONB, nullable=True),  # Structured requirements like missing fields
        sa.Column('requested_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='revision_priority_enum'), nullable=False, default='medium'),
        sa.Column('status', sa.Enum('pending', 'acknowledged', 'in_progress', 'resubmitted', 'approved', 'rejected', name='revision_status_enum'), nullable=False, default='pending'),
        sa.Column('new_evidence_id', sa.Integer, sa.ForeignKey('cycle_report_request_info_testcase_source_evidence.id'), nullable=True),  # Links to new evidence version when resubmitted
        sa.Column('data_owner_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resubmitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text, nullable=True),
        sa.Column('reviewed_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_sent', sa.Boolean, nullable=False, default=False),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_count', sa.Integer, nullable=False, default=0),
        sa.Column('last_reminder_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index('idx_revision_request_status', 'status'),
        sa.Index('idx_revision_request_due_date', 'due_date'),
        sa.Index('idx_revision_request_data_owner', 'data_owner_id', 'status'),
        sa.CheckConstraint("(status != 'resubmitted') OR (status = 'resubmitted' AND new_evidence_id IS NOT NULL)", name='check_resubmitted_evidence')
    )
    
    # 4. Create query execution log table
    op.create_table(
        'cycle_report_test_cases_query_executions',
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False, index=True),
        sa.Column('test_case_id', sa.Integer, sa.ForeignKey('cycle_report_test_cases.id'), nullable=False, index=True),
        sa.Column('query_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cycle_report_test_cases_queries.query_id'), nullable=False),
        sa.Column('evidence_id', sa.Integer, sa.ForeignKey('cycle_report_request_info_testcase_source_evidence.id'), nullable=True),
        sa.Column('query_text', sa.Text, nullable=False),
        sa.Column('query_parameters', postgresql.JSONB, nullable=True),
        sa.Column('execution_status', sa.Enum('pending', 'running', 'success', 'failed', 'timeout', name='query_execution_status_enum'), nullable=False, default='pending'),
        sa.Column('executed_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('execution_duration_ms', sa.Integer, nullable=True),
        sa.Column('row_count', sa.Integer, nullable=True),
        sa.Column('result_sample', postgresql.JSONB, nullable=True),  # First N rows for preview
        sa.Column('result_hash', sa.String(64), nullable=True),  # SHA256 of results for comparison
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('validation_status', sa.Enum('pending', 'passed', 'failed', 'warning', name='query_validation_status_enum'), nullable=True),
        sa.Column('validation_messages', postgresql.JSONB, nullable=True),
        sa.Column('comparison_status', sa.Enum('pending', 'matched', 'mismatched', 'partial_match', name='comparison_status_enum'), nullable=True),
        sa.Column('comparison_notes', sa.Text, nullable=True),
        sa.Column('approved_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index('idx_query_execution_status', 'execution_status'),
        sa.Index('idx_query_execution_test_case', 'test_case_id', 'executed_at')
    )
    
    # 5. Create query result comparison table
    op.create_table(
        'cycle_report_test_cases_query_comparisons',
        sa.Column('comparison_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cycle_report_test_cases_query_executions.execution_id'), nullable=False),
        sa.Column('test_case_id', sa.Integer, sa.ForeignKey('cycle_report_test_cases.id'), nullable=False),
        sa.Column('attribute_name', sa.String(255), nullable=False),
        sa.Column('expected_value', sa.Text, nullable=True),
        sa.Column('actual_value', sa.Text, nullable=True),
        sa.Column('primary_key_values', postgresql.JSONB, nullable=False),  # PK values for this row
        sa.Column('match_status', sa.Enum('exact_match', 'partial_match', 'no_match', 'missing', name='match_status_enum'), nullable=False),
        sa.Column('match_confidence', sa.Float, nullable=True),  # 0.0 to 1.0
        sa.Column('comparison_notes', sa.Text, nullable=True),
        sa.Column('compared_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('compared_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('manual_override', sa.Boolean, nullable=False, default=False),
        sa.Column('override_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Index('idx_comparison_execution', 'execution_id'),
        sa.Index('idx_comparison_match_status', 'match_status')
    )
    
    # 6. Add missing columns to existing tables
    
    # Add columns to cycle_report_test_cases for better tracking
    op.add_column('cycle_report_test_cases', 
        sa.Column('primary_key_attributes', postgresql.JSONB, nullable=True))
    op.add_column('cycle_report_test_cases',
        sa.Column('sample_identifier', sa.String(500), nullable=True))
    op.add_column('cycle_report_test_cases',
        sa.Column('expected_evidence_type', sa.Enum('document', 'data_source', 'either', name='expected_evidence_type_enum'), nullable=True, server_default='either'))
    op.add_column('cycle_report_test_cases',
        sa.Column('revision_count', sa.Integer, nullable=False, server_default='0'))
    op.add_column('cycle_report_test_cases',
        sa.Column('last_revision_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('cycle_report_test_cases',
        sa.Column('preferred_data_source_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_test_cases_last_revision',
        'cycle_report_test_cases',
        'cycle_report_test_cases_revision_requests',
        ['last_revision_id'],
        ['revision_id']
    )
    op.create_foreign_key(
        'fk_test_cases_preferred_data_source',
        'cycle_report_test_cases',
        'cycle_report_test_cases_data_sources',
        ['preferred_data_source_id'],
        ['data_source_id']
    )
    
    # Add columns to cycle_report_request_info_testcase_source_evidence
    op.add_column('cycle_report_request_info_testcase_source_evidence',
        sa.Column('query_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('cycle_report_request_info_testcase_source_evidence',
        sa.Column('query_execution_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('cycle_report_request_info_testcase_source_evidence',
        sa.Column('revision_request_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('cycle_report_request_info_testcase_source_evidence',
        sa.Column('pk_attributes_included', postgresql.JSONB, nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_evidence_query',
        'cycle_report_request_info_testcase_source_evidence',
        'cycle_report_test_cases_queries',
        ['query_id'],
        ['query_id']
    )
    op.create_foreign_key(
        'fk_evidence_query_execution',
        'cycle_report_request_info_testcase_source_evidence',
        'cycle_report_test_cases_query_executions',
        ['query_execution_id'],
        ['execution_id']
    )
    op.create_foreign_key(
        'fk_evidence_revision_request',
        'cycle_report_request_info_testcase_source_evidence',
        'cycle_report_test_cases_revision_requests',
        ['revision_request_id'],
        ['revision_id']
    )
    
    # 7. Create indexes for performance
    op.create_index('idx_evidence_query', 'cycle_report_request_info_testcase_source_evidence', ['query_id'])
    op.create_index('idx_evidence_revision_request', 'cycle_report_request_info_testcase_source_evidence', ['revision_request_id'])
    op.create_index('idx_test_case_revision_count', 'cycle_report_test_cases', ['revision_count'])
    op.create_index('idx_test_case_preferred_data_source', 'cycle_report_test_cases', ['preferred_data_source_id'])
    
    # 8. Create notification preferences table for data owners
    op.create_table(
        'cycle_report_test_cases_notification_preferences',
        sa.Column('preference_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=True),
        sa.Column('notification_type', sa.Enum('assignment', 'revision_request', 'reminder', 'deadline', name='rfi_notification_type_enum'), nullable=False),
        sa.Column('enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('email_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('in_app_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('frequency', sa.Enum('immediate', 'hourly', 'daily', 'weekly', name='notification_frequency_enum'), nullable=False, default='immediate'),
        sa.Column('quiet_hours_start', sa.Time, nullable=True),
        sa.Column('quiet_hours_end', sa.Time, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', 'phase_id', 'notification_type', name='uq_user_phase_notification_type')
    )


def downgrade():
    """Remove Request for Information phase enhancements"""
    
    # Drop notification preferences
    op.drop_table('cycle_report_request_info_notification_preferences')
    
    # Drop indexes
    op.drop_index('idx_test_case_revision_count', 'cycle_report_test_cases')
    op.drop_index('idx_evidence_revision', 'cycle_report_request_info_testcase_source_evidence')
    op.drop_index('idx_evidence_template', 'cycle_report_request_info_testcase_source_evidence')
    
    # Drop foreign keys from evidence table
    op.drop_constraint('fk_evidence_revision', 'cycle_report_request_info_testcase_source_evidence', type_='foreignkey')
    op.drop_constraint('fk_evidence_query_execution', 'cycle_report_request_info_testcase_source_evidence', type_='foreignkey')
    op.drop_constraint('fk_evidence_template', 'cycle_report_request_info_testcase_source_evidence', type_='foreignkey')
    
    # Drop columns from evidence table
    op.drop_column('cycle_report_request_info_testcase_source_evidence', 'pk_attributes_included')
    op.drop_column('cycle_report_request_info_testcase_source_evidence', 'revision_id')
    op.drop_column('cycle_report_request_info_testcase_source_evidence', 'query_execution_id')
    op.drop_column('cycle_report_request_info_testcase_source_evidence', 'template_id')
    
    # Drop foreign key from test cases
    op.drop_constraint('fk_test_cases_last_revision', 'cycle_report_test_cases', type_='foreignkey')
    
    # Drop columns from test cases
    op.drop_column('cycle_report_test_cases', 'last_revision_id')
    op.drop_column('cycle_report_test_cases', 'revision_count')
    op.drop_column('cycle_report_test_cases', 'expected_evidence_type')
    op.drop_column('cycle_report_test_cases', 'sample_identifier')
    op.drop_column('cycle_report_test_cases', 'primary_key_attributes')
    
    # Drop new tables
    op.drop_table('cycle_report_request_info_query_comparisons')
    op.drop_table('cycle_report_request_info_query_executions')
    op.drop_table('cycle_report_request_info_revision_requests')
    op.drop_table('cycle_report_request_info_data_source_templates')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS revision_priority_enum')
    op.execute('DROP TYPE IF EXISTS revision_status_enum')
    op.execute('DROP TYPE IF EXISTS query_execution_status_enum')
    op.execute('DROP TYPE IF EXISTS query_validation_status_enum')
    op.execute('DROP TYPE IF EXISTS comparison_status_enum')
    op.execute('DROP TYPE IF EXISTS match_status_enum')
    op.execute('DROP TYPE IF EXISTS expected_evidence_type_enum')
    op.execute('DROP TYPE IF EXISTS rfi_notification_type_enum')
    op.execute('DROP TYPE IF EXISTS notification_frequency_enum')