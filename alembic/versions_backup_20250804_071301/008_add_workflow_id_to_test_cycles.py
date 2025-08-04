"""Add workflow_id to test_cycles table

Revision ID: 008_add_workflow_id
Revises: 007_add_test_report_tables
Create Date: 2025-06-17 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_workflow_id'
down_revision = '007_add_test_report_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add workflow_id column to test_cycles table
    op.add_column('test_cycles', 
        sa.Column('workflow_id', sa.String(length=255), nullable=True)
    )
    
    # Create index on workflow_id for faster lookups
    op.create_index('ix_test_cycles_workflow_id', 'test_cycles', ['workflow_id'])
    
    # Create composite index for cycle_id and workflow_id
    op.create_index('ix_test_cycles_cycle_workflow', 'test_cycles', ['cycle_id', 'workflow_id'])


def downgrade():
    # Drop indexes first
    op.drop_index('ix_test_cycles_cycle_workflow', table_name='test_cycles')
    op.drop_index('ix_test_cycles_workflow_id', table_name='test_cycles')
    
    # Drop the column
    op.drop_column('test_cycles', 'workflow_id')