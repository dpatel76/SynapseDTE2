"""add_scoping_versioning_columns_only

Revision ID: 1f8b43c51c29
Revises: 2a690861a41b
Create Date: 2025-06-08 10:04:52.321842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f8b43c51c29'
down_revision: Union[str, None] = '2a690861a41b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add versioning columns to scoping_submissions table."""
    # Add version column with default value of 1
    op.add_column('scoping_submissions', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # Add previous_version_id column (nullable, self-referencing foreign key)
    op.add_column('scoping_submissions', sa.Column('previous_version_id', sa.Integer(), nullable=True))
    
    # Add changes_from_previous column (JSON, nullable)
    op.add_column('scoping_submissions', sa.Column('changes_from_previous', sa.JSON(), nullable=True))
    
    # Add revision_reason column (Text, nullable)
    op.add_column('scoping_submissions', sa.Column('revision_reason', sa.Text(), nullable=True))
    
    # Create foreign key constraint for previous_version_id
    op.create_foreign_key(
        'fk_scoping_submissions_previous_version', 
        'scoping_submissions', 
        'scoping_submissions', 
        ['previous_version_id'], 
        ['submission_id']
    )


def downgrade() -> None:
    """Remove versioning columns FROM cycle_report_scoping_submissions table."""
    # Drop foreign key constraint
    op.drop_constraint('fk_scoping_submissions_previous_version', 'scoping_submissions', type_='foreignkey')
    
    # Drop columns
    op.drop_column('scoping_submissions', 'revision_reason')
    op.drop_column('scoping_submissions', 'changes_from_previous')
    op.drop_column('scoping_submissions', 'previous_version_id')
    op.drop_column('scoping_submissions', 'version')
