"""Add document revision tracking

Revision ID: 004_add_document_revision_tracking
Revises: 003_create_unified_audit_log
Create Date: 2025-06-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_document_revision_tracking'
down_revision = '003_create_unified_audit_log'
branch_labels = None
depends_on = None


def upgrade():
    # Add revision tracking columns to document_submissions
    op.add_column('document_submissions', sa.Column('revision_number', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('document_submissions', sa.Column('parent_submission_id', sa.String(36), nullable=True))
    op.add_column('document_submissions', sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('document_submissions', sa.Column('notes', sa.Text(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_document_submissions_parent',
        'document_submissions', 
        'document_submissions',
        ['parent_submission_id'], 
        ['submission_id']
    )
    
    # Add index for performance
    op.create_index('idx_document_submissions_current', 'document_submissions', ['test_case_id', 'is_current'])
    op.create_index('idx_document_submissions_parent', 'document_submissions', ['parent_submission_id'])


def downgrade():
    # Remove indexes
    op.drop_index('idx_document_submissions_parent', 'document_submissions')
    op.drop_index('idx_document_submissions_current', 'document_submissions')
    
    # Remove foreign key
    op.drop_constraint('fk_document_submissions_parent', 'document_submissions', type_='foreignkey')
    
    # Remove columns
    op.drop_column('document_submissions', 'notes')
    op.drop_column('document_submissions', 'is_current')
    op.drop_column('document_submissions', 'parent_submission_id')
    op.drop_column('document_submissions', 'revision_number')