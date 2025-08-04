"""Add sample set versioning and individual sample approval

Revision ID: 20b51ad6faa3
Revises: aed28248d79b
Create Date: 2025-06-08 17:38:23.631880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20b51ad6faa3'
down_revision: Union[str, None] = 'aed28248d79b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create new sample approval status enum (only if it doesn't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sample_approval_status_enum AS ENUM ('Pending', 'Approved', 'Rejected', 'Needs Changes');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add versioning fields to sample_sets table
    op.add_column('sample_sets', sa.Column('master_set_id', sa.String(36), nullable=True))
    op.add_column('sample_sets', sa.Column('version_number', sa.Integer(), nullable=False, server_default='1', comment='Version number of this sample set'))
    op.add_column('sample_sets', sa.Column('is_latest_version', sa.Boolean(), nullable=False, server_default='true', comment='Whether this is the latest version'))
    op.add_column('sample_sets', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether this version is active'))
    op.add_column('sample_sets', sa.Column('version_notes', sa.Text(), nullable=True, comment='Notes about what changed in this version'))
    op.add_column('sample_sets', sa.Column('change_reason', sa.String(100), nullable=True, comment='Reason for creating new version'))
    op.add_column('sample_sets', sa.Column('replaced_set_id', sa.String(36), nullable=True))
    op.add_column('sample_sets', sa.Column('version_created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('sample_sets', sa.Column('version_created_by', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('sample_sets', sa.Column('archived_at', sa.DateTime(), nullable=True))
    op.add_column('sample_sets', sa.Column('archived_by', sa.Integer(), nullable=True))
    
    # Add individual approval fields to sample_records table
    op.add_column('sample_records', sa.Column('approval_status', sa.Enum('Pending', 'Approved', 'Rejected', 'Needs Changes', name='sample_approval_status_enum'), nullable=False, server_default='Pending', comment='Individual sample approval status'))
    op.add_column('sample_records', sa.Column('approved_by', sa.Integer(), nullable=True, comment='User who approved this sample'))
    op.add_column('sample_records', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True, comment='When this sample was approved'))
    op.add_column('sample_records', sa.Column('rejection_reason', sa.Text(), nullable=True, comment='Reason for rejecting this sample'))
    op.add_column('sample_records', sa.Column('change_requests', sa.JSON(), nullable=True, comment='Specific changes requested for this sample'))
    
    # Add foreign key constraints
    op.create_foreign_key('fk_sample_sets_master_set', 'sample_sets', 'sample_sets', ['master_set_id'], ['set_id'])
    op.create_foreign_key('fk_sample_sets_replaced_set', 'sample_sets', 'sample_sets', ['replaced_set_id'], ['set_id'])
    op.create_foreign_key('fk_sample_sets_version_created_by', 'sample_sets', 'users', ['version_created_by'], ['user_id'])
    op.create_foreign_key('fk_sample_sets_archived_by', 'sample_sets', 'users', ['archived_by'], ['user_id'])
    op.create_foreign_key('fk_sample_records_approved_by', 'sample_records', 'users', ['approved_by'], ['user_id'])
    
    # Add indexes
    op.create_index('idx_sample_sets_master_set_id', 'sample_sets', ['master_set_id'])
    op.create_index('idx_sample_sets_version_number', 'sample_sets', ['version_number'])
    op.create_index('idx_sample_sets_is_latest_version', 'sample_sets', ['is_latest_version'])
    op.create_index('idx_sample_records_approval_status', 'sample_records', ['approval_status'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_sample_records_approval_status')
    op.drop_index('idx_sample_sets_is_latest_version')
    op.drop_index('idx_sample_sets_version_number')
    op.drop_index('idx_sample_sets_master_set_id')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_sample_records_approved_by', 'sample_records', type_='foreignkey')
    op.drop_constraint('fk_sample_sets_archived_by', 'sample_sets', type_='foreignkey')
    op.drop_constraint('fk_sample_sets_version_created_by', 'sample_sets', type_='foreignkey')
    op.drop_constraint('fk_sample_sets_replaced_set', 'sample_sets', type_='foreignkey')
    op.drop_constraint('fk_sample_sets_master_set', 'sample_sets', type_='foreignkey')
    
    # Drop columns from sample_records
    op.drop_column('sample_records', 'change_requests')
    op.drop_column('sample_records', 'rejection_reason')
    op.drop_column('sample_records', 'approved_at')
    op.drop_column('sample_records', 'approved_by')
    op.drop_column('sample_records', 'approval_status')
    
    # Drop columns from sample_sets
    op.drop_column('sample_sets', 'archived_by')
    op.drop_column('sample_sets', 'archived_at')
    op.drop_column('sample_sets', 'version_created_by')
    op.drop_column('sample_sets', 'version_created_at')
    op.drop_column('sample_sets', 'replaced_set_id')
    op.drop_column('sample_sets', 'change_reason')
    op.drop_column('sample_sets', 'version_notes')
    op.drop_column('sample_sets', 'is_active')
    op.drop_column('sample_sets', 'is_latest_version')
    op.drop_column('sample_sets', 'version_number')
    op.drop_column('sample_sets', 'master_set_id')
    
    # Drop enum type
    op.execute("DROP TYPE sample_approval_status_enum")
