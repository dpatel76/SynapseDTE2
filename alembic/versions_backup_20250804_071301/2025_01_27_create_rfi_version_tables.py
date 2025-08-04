"""Create RFI version tables

Revision ID: create_rfi_version_tables
Revises: 2025_01_25_request_info_enhancements
Create Date: 2025-01-27 10:00:00.000000

This migration creates version tables for the RFI (Request for Information) phase,
following the same pattern as sample selection and scoping phases.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'create_rfi_version_tables'
down_revision = '2025_01_25_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE version_status_enum AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'superseded');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE evidence_status_enum AS ENUM ('pending', 'approved', 'rejected', 'request_changes');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create Request Info Evidence versions table
    op.create_table('cycle_report_request_info_evidence_versions',
        sa.Column('version_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', postgresql.ENUM('draft', 'pending_approval', 'approved', 'rejected', 'superseded', name='version_status_enum'), nullable=False, server_default='draft'),
        sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Summary statistics
        sa.Column('total_test_cases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('submitted_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('approved_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rejected_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pending_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Evidence type breakdown
        sa.Column('document_evidence_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('data_source_evidence_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Submission tracking
        sa.Column('submission_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_schedule', postgresql.JSONB(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        
        # Approval workflow
        sa.Column('submitted_by_id', sa.Integer(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        
        # Report owner review metadata
        sa.Column('report_owner_review_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('report_owner_review_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('report_owner_feedback_summary', postgresql.JSONB(), nullable=True),
        
        # Workflow tracking
        sa.Column('workflow_execution_id', sa.String(255), nullable=True),
        sa.Column('workflow_run_id', sa.String(255), nullable=True),
        
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['parent_version_id'], ['cycle_report_request_info_evidence_versions.version_id'], ),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('version_id')
    )
    
    # Create indexes for Request Info Evidence versions
    op.create_index('idx_request_info_versions_phase_id', 'cycle_report_request_info_evidence_versions', ['phase_id'])
    op.create_index('idx_request_info_versions_version_status', 'cycle_report_request_info_evidence_versions', ['version_status'])
    op.create_index('idx_request_info_versions_phase_version', 'cycle_report_request_info_evidence_versions', ['phase_id', 'version_number'], unique=True)
    
    # Create Request Info evidence table
    op.create_table('cycle_report_request_info_evidence',
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.Integer(), nullable=False),
        sa.Column('sample_id', sa.String(255), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('attribute_name', sa.String(255), nullable=False),
        
        # Evidence type and details
        sa.Column('evidence_type', sa.String(20), nullable=False),  # 'document' or 'data_source'
        sa.Column('evidence_status', postgresql.ENUM('pending', 'approved', 'rejected', 'request_changes', name='evidence_status_enum'), nullable=False, server_default='pending'),
        
        # Common submission fields
        sa.Column('data_owner_id', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submission_notes', sa.Text(), nullable=True),
        
        # Document specific fields
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('stored_filename', sa.String(255), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        
        # Data source specific fields
        sa.Column('data_source_id', sa.Integer(), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=True),
        sa.Column('query_parameters', postgresql.JSONB(), nullable=True),
        sa.Column('query_result_sample', postgresql.JSONB(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        
        # Tester decision fields
        sa.Column('tester_decision', postgresql.ENUM('approved', 'rejected', 'request_changes', name='decision_enum'), nullable=True),
        sa.Column('tester_notes', sa.Text(), nullable=True),
        sa.Column('tester_decided_by', sa.Integer(), nullable=True),
        sa.Column('tester_decided_at', sa.DateTime(timezone=True), nullable=True),
        
        # Report owner decision fields
        sa.Column('report_owner_decision', postgresql.ENUM('approved', 'rejected', 'request_changes', name='decision_enum'), nullable=True),
        sa.Column('report_owner_notes', sa.Text(), nullable=True),
        sa.Column('report_owner_decided_by', sa.Integer(), nullable=True),
        sa.Column('report_owner_decided_at', sa.DateTime(timezone=True), nullable=True),
        
        # Resubmission tracking
        sa.Column('requires_resubmission', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resubmission_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resubmission_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parent_evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Validation tracking
        sa.Column('validation_status', sa.String(50), nullable=True, server_default='pending'),
        sa.Column('validation_notes', sa.Text(), nullable=True),
        sa.Column('validated_by', sa.Integer(), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        
        sa.ForeignKeyConstraint(['attribute_id'], ['cycle_report_planning_attributes.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['data_owner_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['data_source_id'], ['cycle_report_planning_data_sources.id'], ),
        sa.ForeignKeyConstraint(['parent_evidence_id'], ['cycle_report_request_info_evidence.evidence_id'], ),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['report_owner_decided_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['test_case_id'], ['cycle_report_test_cases.id'], ),
        sa.ForeignKeyConstraint(['tester_decided_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['validated_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['cycle_report_request_info_evidence_versions.version_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('evidence_id'),
        sa.CheckConstraint(
            "(evidence_type = 'document' AND original_filename IS NOT NULL AND file_path IS NOT NULL) OR "
            "(evidence_type = 'data_source' AND query_text IS NOT NULL)",
            name='check_evidence_type_fields_versioned'
        ),
    )
    
    # Create indexes for Request Info evidence
    op.create_index('idx_request_info_evidence_version_id', 'cycle_report_request_info_evidence', ['version_id'])
    op.create_index('idx_request_info_evidence_test_case_id', 'cycle_report_request_info_evidence', ['test_case_id'])
    op.create_index('idx_request_info_evidence_sample_id', 'cycle_report_request_info_evidence', ['sample_id'])
    op.create_index('idx_request_info_evidence_data_owner_id', 'cycle_report_request_info_evidence', ['data_owner_id'])
    op.create_index('idx_request_info_evidence_evidence_status', 'cycle_report_request_info_evidence', ['evidence_status'])
    
    # Add can_be_edited computed column to versions table
    op.execute("""
        ALTER TABLE cycle_report_request_info_evidence_versions
        ADD COLUMN can_be_edited BOOLEAN GENERATED ALWAYS AS 
        (CASE WHEN version_status = 'draft' THEN true ELSE false END) STORED;
    """)
    
    # Create helper view for latest versions
    op.execute("""
        CREATE OR REPLACE VIEW cycle_report_request_info_latest_versions AS
        SELECT DISTINCT ON (phase_id) *
        FROM cycle_report_request_info_evidence_versions
        WHERE version_status IN ('approved', 'pending_approval')
        ORDER BY phase_id, version_number DESC;
    """)


def downgrade():
    # Drop view
    op.execute("DROP VIEW IF EXISTS cycle_report_request_info_latest_versions")
    
    # Drop indexes
    op.drop_index('idx_request_info_evidence_evidence_status', table_name='cycle_report_request_info_evidence')
    op.drop_index('idx_request_info_evidence_data_owner_id', table_name='cycle_report_request_info_evidence')
    op.drop_index('idx_request_info_evidence_sample_id', table_name='cycle_report_request_info_evidence')
    op.drop_index('idx_request_info_evidence_test_case_id', table_name='cycle_report_request_info_evidence')
    op.drop_index('idx_request_info_evidence_version_id', table_name='cycle_report_request_info_evidence')
    
    op.drop_index('idx_request_info_versions_phase_version', table_name='cycle_report_request_info_evidence_versions')
    op.drop_index('idx_request_info_versions_version_status', table_name='cycle_report_request_info_evidence_versions')
    op.drop_index('idx_request_info_versions_phase_id', table_name='cycle_report_request_info_evidence_versions')
    
    # Drop tables
    op.drop_table('cycle_report_request_info_evidence')
    op.drop_table('cycle_report_request_info_evidence_versions')
    
    # Note: We don't drop the enum types as they might be used by other tables