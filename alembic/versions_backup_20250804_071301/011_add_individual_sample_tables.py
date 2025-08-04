"""add individual sample tables

Revision ID: 010_add_individual_sample_tables
Revises: 
Create Date: 2024-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '011_add_individual_sample_tables'
down_revision: Union[str, None] = '010_add_data_profiling_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums first
    testerdecision = postgresql.ENUM('include', 'exclude', 'review_required', name='testerdecision')
    testerdecision.create(op.get_bind())
    
    reportownerdecision = postgresql.ENUM('approved', 'rejected', 'revision_required', name='reportownerdecision')
    reportownerdecision.create(op.get_bind())
    
    submissionstatus = postgresql.ENUM('draft', 'pending_approval', 'approved', 'rejected', 'revision_required', name='submissionstatus')
    submissionstatus.create(op.get_bind())

    # Create sample_submissions table first (since samples references it)
    op.create_table('sample_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.String(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('submitted_by_user_id', sa.Integer(), nullable=True),
        sa.Column('submission_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'pending_approval', 'approved', 'rejected', 'revision_required', name='submissionstatus'), nullable=True, default='pending_approval'),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('review_decision', sa.Enum('approved', 'rejected', 'revision_required', name='reportownerdecision'), nullable=True),
        sa.Column('review_feedback', sa.Text(), nullable=True),
        sa.Column('is_official_version', sa.Boolean(), nullable=True, default=False),
        sa.Column('total_samples', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['submitted_by_user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id')
    )
    op.create_index(op.f('ix_sample_submissions_id'), 'sample_submissions', ['id'], unique=False)
    op.create_index(op.f('ix_sample_submissions_submission_id'), 'sample_submissions', ['submission_id'], unique=True)
    op.create_index('ix_sample_submissions_cycle_report', 'sample_submissions', ['cycle_id', 'report_id'], unique=False)

    # Create individual_samples table
    op.create_table('individual_samples',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sample_id', sa.String(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('primary_key_value', sa.String(), nullable=False),
        sa.Column('sample_data', sa.JSON(), nullable=False),
        sa.Column('generation_method', sa.String(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('generated_by_user_id', sa.Integer(), nullable=True),
        sa.Column('tester_decision', sa.Enum('include', 'exclude', 'review_required', name='testerdecision'), nullable=True),
        sa.Column('tester_decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tester_decision_by_user_id', sa.Integer(), nullable=True),
        sa.Column('tester_notes', sa.Text(), nullable=True),
        sa.Column('report_owner_decision', sa.Enum('approved', 'rejected', 'revision_required', name='reportownerdecision'), nullable=True),
        sa.Column('report_owner_feedback', sa.Text(), nullable=True),
        sa.Column('is_submitted', sa.Boolean(), nullable=True, default=False),
        sa.Column('submission_id', sa.Integer(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=True, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['generated_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['sample_submissions.id'], ),
        sa.ForeignKeyConstraint(['tester_decision_by_user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sample_id')
    )
    op.create_index(op.f('ix_individual_samples_id'), 'individual_samples', ['id'], unique=False)
    op.create_index(op.f('ix_individual_samples_sample_id'), 'individual_samples', ['sample_id'], unique=True)
    op.create_index('ix_individual_samples_cycle_report', 'individual_samples', ['cycle_id', 'report_id'], unique=False)

    # Create sample_submission_items table
    op.create_table('sample_submission_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('sample_id', sa.Integer(), nullable=False),
        sa.Column('tester_decision', sa.Enum('include', 'exclude', 'review_required', name='testerdecision'), nullable=False),
        sa.Column('primary_key_value', sa.String(), nullable=False),
        sa.Column('sample_data_snapshot', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['sample_id'], ['individual_samples.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['sample_submissions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sample_submission_items_id'), 'sample_submission_items', ['id'], unique=False)
    op.create_index('ix_sample_submission_items_submission', 'sample_submission_items', ['submission_id'], unique=False)

    # Create sample_feedback table
    op.create_table('sample_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sample_id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('feedback_type', sa.String(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(), nullable=True, default='medium'),
        sa.Column('is_blocking', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, default=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['sample_id'], ['individual_samples.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['sample_submissions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sample_feedback_id'), 'sample_feedback', ['id'], unique=False)
    op.create_index('ix_sample_feedback_sample_submission', 'sample_feedback', ['sample_id', 'submission_id'], unique=False)

    # Create sample_audit_logs table
    op.create_table('sample_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sample_id', sa.Integer(), nullable=True),
        sa.Column('submission_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('action_details', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['sample_id'], ['individual_samples.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['sample_submissions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sample_audit_logs_id'), 'sample_audit_logs', ['id'], unique=False)
    op.create_index('ix_sample_audit_logs_sample', 'sample_audit_logs', ['sample_id'], unique=False)
    op.create_index('ix_sample_audit_logs_user', 'sample_audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_sample_audit_logs_user', table_name='sample_audit_logs')
    op.drop_index('ix_sample_audit_logs_sample', table_name='sample_audit_logs')
    op.drop_index(op.f('ix_sample_audit_logs_id'), table_name='sample_audit_logs')
    op.drop_table('sample_audit_logs')
    
    op.drop_index('ix_sample_feedback_sample_submission', table_name='sample_feedback')
    op.drop_index(op.f('ix_sample_feedback_id'), table_name='sample_feedback')
    op.drop_table('sample_feedback')
    
    op.drop_index('ix_sample_submission_items_submission', table_name='sample_submission_items')
    op.drop_index(op.f('ix_sample_submission_items_id'), table_name='sample_submission_items')
    op.drop_table('sample_submission_items')
    
    op.drop_index('ix_sample_submissions_cycle_report', table_name='sample_submissions')
    op.drop_index(op.f('ix_sample_submissions_submission_id'), table_name='sample_submissions')
    op.drop_index(op.f('ix_sample_submissions_id'), table_name='sample_submissions')
    op.drop_table('sample_submissions')
    
    op.drop_index('ix_individual_samples_cycle_report', table_name='individual_samples')
    op.drop_index(op.f('ix_individual_samples_sample_id'), table_name='individual_samples')
    op.drop_index(op.f('ix_individual_samples_id'), table_name='individual_samples')
    op.drop_table('individual_samples')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS testerdecision')
    op.execute('DROP TYPE IF EXISTS reportownerdecision')
    op.execute('DROP TYPE IF EXISTS submissionstatus')