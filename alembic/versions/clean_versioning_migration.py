"""
Clean versioning system migration - removes old tables and creates new structure

Revision ID: clean_versioning_001
Revises: 
Create Date: 2024-01-01 10:00:00.000000

This migration:
1. Drops all old versioning-related tables
2. Creates new clean versioning structure
3. No backward compatibility maintained
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'clean_versioning_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create clean versioning structure"""
    
    # Step 1: Drop old tables if they exist
    drop_old_tables()
    
    # Step 2: Create new versioning tables
    
    # Planning Phase
    op.create_table('planning_versions',
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', sa.String(20), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('workflow_run_id', sa.String(255), nullable=False),
        sa.Column('activity_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('total_attributes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('included_attributes', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('version_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id']),
        sa.UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_planning_version')
    )
    op.create_index('idx_planning_current', 'planning_versions', ['cycle_id', 'report_id', 'version_status'])
    op.create_index('idx_planning_workflow', 'planning_versions', ['workflow_execution_id'])
    
    op.create_table('attribute_decisions',
        sa.Column('decision_id', postgresql.UUID(), nullable=False),
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('attribute_name', sa.String(255), nullable=False),
        sa.Column('include_in_testing', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('risk_rating', sa.String(20), nullable=True),
        sa.PrimaryKeyConstraint('decision_id'),
        sa.ForeignKeyConstraint(['version_id'], ['planning_versions.version_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_id'], ['report_attributes.attribute_id'])
    )
    op.create_index('idx_attr_decision_version', 'attribute_decisions', ['version_id'])
    
    # Data Profiling Phase
    op.create_table('data_profiling_versions',
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', sa.String(20), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('workflow_run_id', sa.String(255), nullable=False),
        sa.Column('activity_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('source_files', postgresql.JSONB(), nullable=False),
        sa.Column('total_rules', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('approved_rules', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('version_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id']),
        sa.UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_profiling_version')
    )
    
    op.create_table('versioned_profiling_rules',
        sa.Column('rule_id', postgresql.UUID(), nullable=False),
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('rule_definition', postgresql.JSONB(), nullable=False),
        sa.Column('approval_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('rule_id'),
        sa.ForeignKeyConstraint(['version_id'], ['data_profiling_versions.version_id'], ondelete='CASCADE')
    )
    
    # Scoping Phase
    op.create_table('scoping_versions',
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', sa.String(20), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('workflow_run_id', sa.String(255), nullable=False),
        sa.Column('activity_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('total_attributes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('in_scope_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('version_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id']),
        sa.UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_scoping_version')
    )
    
    op.create_table('scoping_decisions',
        sa.Column('decision_id', postgresql.UUID(), nullable=False),
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('is_in_scope', sa.Boolean(), nullable=False),
        sa.Column('scoping_rationale', sa.Text(), nullable=True),
        sa.Column('risk_assessment', sa.String(20), nullable=True),
        sa.Column('approval_status', sa.String(20), nullable=False, server_default='pending'),
        sa.PrimaryKeyConstraint('decision_id'),
        sa.ForeignKeyConstraint(['version_id'], ['scoping_versions.version_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_id'], ['report_attributes.attribute_id'])
    )
    
    # Sample Selection Phase
    op.create_table('sample_selection_versions',
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', sa.String(20), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('workflow_run_id', sa.String(255), nullable=False),
        sa.Column('activity_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('selection_criteria', postgresql.JSONB(), nullable=False),
        sa.Column('target_sample_size', sa.Integer(), nullable=False),
        sa.Column('actual_sample_size', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('version_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id']),
        sa.UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_sample_version')
    )
    
    op.create_table('sample_decisions',
        sa.Column('decision_id', postgresql.UUID(), nullable=False),
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('sample_identifier', sa.String(255), nullable=False),
        sa.Column('sample_data', postgresql.JSONB(), nullable=False),
        sa.Column('sample_type', sa.String(50), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('source_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('decision_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('decision_notes', sa.Text(), nullable=True),
        sa.Column('carried_from_version_id', postgresql.UUID(), nullable=True),
        sa.Column('carried_from_decision_id', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('decision_id'),
        sa.ForeignKeyConstraint(['version_id'], ['sample_selection_versions.version_id'], ondelete='CASCADE')
    )
    op.create_index('idx_sample_decision_version', 'sample_decisions', ['version_id'])
    op.create_index('idx_sample_decision_status', 'sample_decisions', ['decision_status'])
    
    # Data Owner Assignment (Audit)
    op.create_table('versioned_data_owner_assignments',
        sa.Column('assignment_id', postgresql.UUID(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('lob_id', postgresql.UUID(), nullable=False),
        sa.Column('data_owner_id', sa.Integer(), nullable=False),
        sa.Column('assignment_type', sa.String(50), nullable=False, server_default='primary'),
        sa.Column('assigned_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('assigned_by_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('previous_assignment_id', postgresql.UUID(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('assignment_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id']),
        sa.ForeignKeyConstraint(['lob_id'], ['lobs.lob_id']),
        sa.ForeignKeyConstraint(['data_owner_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['previous_assignment_id'], ['versioned_data_owner_assignments.assignment_id'])
    )
    op.create_index('idx_owner_active', 'versioned_data_owner_assignments', 
                    ['cycle_id', 'report_id', 'lob_id', 'is_active'])
    op.create_index('idx_owner_workflow', 'versioned_data_owner_assignments', ['workflow_execution_id'])
    
    # Document Submission (Audit)
    op.create_table('versioned_document_submissions',
        sa.Column('submission_id', postgresql.UUID(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('lob_id', postgresql.UUID(), nullable=False),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('document_name', sa.String(255), nullable=False),
        sa.Column('document_type', sa.String(100), nullable=False),
        sa.Column('document_path', sa.String(500), nullable=False),
        sa.Column('document_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('document_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('replaces_submission_id', postgresql.UUID(), nullable=True),
        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('submitted_by_id', sa.Integer(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('submission_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id']),
        sa.ForeignKeyConstraint(['lob_id'], ['lobs.lob_id']),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['replaces_submission_id'], ['versioned_document_submissions.submission_id'])
    )
    op.create_index('idx_doc_current', 'versioned_document_submissions', 
                    ['cycle_id', 'report_id', 'lob_id', 'is_current'])
    op.create_index('idx_doc_workflow', 'versioned_document_submissions', ['workflow_execution_id'])
    
    # Test Execution Audit
    op.create_table('test_execution_audit',
        sa.Column('audit_id', postgresql.UUID(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('test_execution_id', sa.Integer(), nullable=False),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_details', postgresql.JSONB(), nullable=False),
        sa.Column('requested_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('requested_by_id', sa.Integer(), nullable=False),
        sa.Column('responded_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('responded_by_id', sa.Integer(), nullable=True),
        sa.Column('response_status', sa.String(50), nullable=True),
        sa.Column('turnaround_hours', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('audit_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id']),
        sa.ForeignKeyConstraint(['test_execution_id'], ['test_executions.execution_id']),
        sa.ForeignKeyConstraint(['requested_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['responded_by_id'], ['users.user_id'])
    )
    op.create_index('idx_test_audit_execution', 'test_execution_audit', ['test_execution_id'])
    op.create_index('idx_test_audit_workflow', 'test_execution_audit', ['workflow_execution_id'])
    
    # Observation Phase
    op.create_table('observation_versions',
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', sa.String(20), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('workflow_run_id', sa.String(255), nullable=False),
        sa.Column('activity_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('observation_period_start', sa.Date(), nullable=False),
        sa.Column('observation_period_end', sa.Date(), nullable=False),
        sa.Column('total_observations', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('version_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id']),
        sa.UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_observation_version')
    )
    
    op.create_table('observation_decisions',
        sa.Column('decision_id', postgresql.UUID(), nullable=False),
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('observation_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_references', postgresql.JSONB(), nullable=True),
        sa.Column('approval_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('requires_remediation', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('remediation_deadline', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('decision_id'),
        sa.ForeignKeyConstraint(['version_id'], ['observation_versions.version_id'], ondelete='CASCADE')
    )
    
    # Test Report Phase
    op.create_table('test_report_versions',
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', sa.String(20), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('workflow_run_id', sa.String(255), nullable=False),
        sa.Column('activity_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('report_title', sa.String(500), nullable=False),
        sa.Column('report_period', sa.String(100), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=True),
        sa.Column('draft_document_path', sa.String(500), nullable=True),
        sa.Column('final_document_path', sa.String(500), nullable=True),
        sa.Column('requires_executive_signoff', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('executive_signoff_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('version_id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id']),
        sa.UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_report_version')
    )
    
    op.create_table('report_sections',
        sa.Column('section_id', postgresql.UUID(), nullable=False),
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('section_type', sa.String(50), nullable=False),
        sa.Column('section_title', sa.String(255), nullable=False),
        sa.Column('section_content', sa.Text(), nullable=True),
        sa.Column('section_order', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('section_id'),
        sa.ForeignKeyConstraint(['version_id'], ['test_report_versions.version_id'], ondelete='CASCADE')
    )
    
    op.create_table('report_signoffs',
        sa.Column('signoff_id', postgresql.UUID(), nullable=False),
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('signoff_role', sa.String(50), nullable=False),
        sa.Column('signoff_user_id', sa.Integer(), nullable=True),
        sa.Column('signoff_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('signoff_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('signoff_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('signoff_id'),
        sa.ForeignKeyConstraint(['version_id'], ['test_report_versions.version_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['signoff_user_id'], ['users.user_id']),
        sa.UniqueConstraint('version_id', 'signoff_role', name='uq_report_signoff')
    )


def downgrade():
    """Drop all versioning tables"""
    # Drop in reverse order due to foreign keys
    op.drop_table('report_signoffs')
    op.drop_table('report_sections')
    op.drop_table('test_report_versions')
    
    op.drop_table('observation_decisions')
    op.drop_table('observation_versions')
    
    op.drop_table('test_execution_audit')
    op.drop_table('versioned_document_submissions')
    op.drop_table('versioned_data_owner_assignments')
    
    op.drop_table('sample_decisions')
    op.drop_table('sample_selection_versions')
    
    op.drop_table('scoping_decisions')
    op.drop_table('scoping_versions')
    
    op.drop_table('versioned_profiling_rules')
    op.drop_table('data_profiling_versions')
    
    op.drop_table('attribute_decisions')
    op.drop_table('planning_versions')


def drop_old_tables():
    """Drop old versioning-related tables if they exist"""
    
    # List of old tables to drop
    old_tables = [
        # Old versioning tables
        'version_history',
        'workflow_version_operations',
        
        # Old phase-specific version tables (if using mixed approach)
        'planning_phase_versions',
        'sample_selection_versions_old',
        'data_profiling_versions_old',
        'scoping_versions_old',
        'observation_versions_old',
        'test_report_versions_old',
        
        # Old decision tables
        'attribute_decisions_old',
        'sample_decisions_old',
        'scoping_decisions_old',
        'observation_decisions_old',
        
        # Old sample sets approach
        'sample_sets',
        'sample_records',
        'sample_validation_results',
        'sample_validation_issues',
        
        # Other legacy tables
        'attribute_version_change_log',
        'sample_selection_audit_log',
        'scoping_audit_log',
        
        # Old phase-specific tables
        'data_profiling_phases',
        'scoping_phases',
        'sample_selection_phases',
        'request_info_phases',
        'test_execution_phases',
        'observation_management_phases',
        'test_report_phases'
    ]
    
    # Drop each table if it exists
    for table in old_tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    
    # Drop old indexes if they exist
    old_indexes = [
        'idx_version_workflow_execution',
        'idx_version_workflow_step',
        'idx_wf_version_ops_execution',
        'idx_wf_version_ops_version'
    ]
    
    for index in old_indexes:
        op.execute(f"DROP INDEX IF EXISTS {index}")