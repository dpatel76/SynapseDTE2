"""Add data_owner_id to document_submissions

Revision ID: 005_add_data_owner_id
Revises: 004_add_document_revision_tracking
Create Date: 2025-06-15 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_data_owner_id'
down_revision = '004_add_document_revision_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add data_owner_id column to document_submissions
    op.add_column('document_submissions', 
        sa.Column('data_owner_id', sa.Integer(), nullable=True)
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_document_submissions_data_owner_id',
        'document_submissions', 
        'users',
        ['data_owner_id'], 
        ['user_id']
    )
    
    # Create index for performance
    op.create_index(
        'ix_document_submissions_data_owner_id',
        'document_submissions',
        ['data_owner_id']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_document_submissions_data_owner_id', 'document_submissions')
    
    # Drop foreign key
    op.drop_constraint('fk_document_submissions_data_owner_id', 'document_submissions', type_='foreignkey')
    
    # Drop column
    op.drop_column('document_submissions', 'data_owner_id')