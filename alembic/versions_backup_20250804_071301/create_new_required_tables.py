"""Create new required tables for refactoring

Revision ID: create_new_required_tables
Revises: 
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_new_required_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create document versions table
    op.create_table('cycle_report_request_info_document_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_submission_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_submission_id', 'version_number', name='uq_submission_version')
    )
    op.create_index('idx_doc_versions_is_current', 'cycle_report_request_info_document_versions', ['is_current'], unique=False, postgresql_where=sa.text('is_current = true'))
    op.create_index('idx_doc_versions_submission_id', 'cycle_report_request_info_document_versions', ['document_submission_id'], unique=False)

    # Create preliminary findings table
    op.create_table('cycle_report_observation_mgmt_preliminary_findings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('finding_title', sa.String(length=500), nullable=False),
        sa.Column('finding_description', sa.Text(), nullable=False),
        sa.Column('finding_type', sa.String(length=50), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('severity_estimate', sa.String(length=20), nullable=True),
        sa.Column('evidence_summary', sa.Text(), nullable=True),
        sa.Column('supporting_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='draft'),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('conversion_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_reason', sa.Text(), nullable=True),
        sa.Column('dismissed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint("finding_type IN ('potential_issue', 'anomaly', 'clarification_needed', 'noteworthy')", name='check_finding_type'),
        sa.CheckConstraint("severity_estimate IN ('low', 'medium', 'high', 'critical', 'unknown')", name='check_severity_estimate'),
        sa.CheckConstraint("source_type IN ('test_execution', 'data_analysis', 'document_review', 'llm_analysis')", name='check_source_type'),
        sa.CheckConstraint("status IN ('draft', 'under_review', 'converted_to_observation', 'dismissed', 'merged')", name='check_status'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prelim_findings_assigned', 'cycle_report_observation_mgmt_preliminary_findings', ['assigned_to_id'], unique=False)
    op.create_index('idx_prelim_findings_cycle_report', 'cycle_report_observation_mgmt_preliminary_findings', ['cycle_id', 'report_id'], unique=False)
    op.create_index('idx_prelim_findings_status', 'cycle_report_observation_mgmt_preliminary_findings', ['status'], unique=False)
    op.create_index('idx_prelim_findings_tags', 'cycle_report_observation_mgmt_preliminary_findings', ['tags'], unique=False, postgresql_using='gin')


def downgrade():
    op.drop_index('idx_prelim_findings_tags', table_name='cycle_report_observation_mgmt_preliminary_findings', postgresql_using='gin')
    op.drop_index('idx_prelim_findings_status', table_name='cycle_report_observation_mgmt_preliminary_findings')
    op.drop_index('idx_prelim_findings_cycle_report', table_name='cycle_report_observation_mgmt_preliminary_findings')
    op.drop_index('idx_prelim_findings_assigned', table_name='cycle_report_observation_mgmt_preliminary_findings')
    op.drop_table('cycle_report_observation_mgmt_preliminary_findings')
    op.drop_index('idx_doc_versions_submission_id', table_name='cycle_report_request_info_document_versions')
    op.drop_index('idx_doc_versions_is_current', table_name='cycle_report_request_info_document_versions', postgresql_where=sa.text('is_current = true'))
    op.drop_table('cycle_report_request_info_document_versions')