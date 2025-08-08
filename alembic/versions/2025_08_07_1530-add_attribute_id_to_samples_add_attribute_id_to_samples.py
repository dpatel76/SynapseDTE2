"""add_attribute_id_to_samples

Revision ID: add_attribute_id_to_samples
Revises: 969b1d7f6b77
Create Date: 2025-08-07 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_attribute_id_to_samples'
down_revision = '969b1d7f6b77'
branch_labels = None
depends_on = None

def upgrade():
    # Add attribute_id column to cycle_report_sample_selection_samples
    op.add_column('cycle_report_sample_selection_samples', 
        sa.Column('attribute_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint to planning attributes
    op.create_foreign_key(
        'fk_sample_selection_samples_attribute_id',
        'cycle_report_sample_selection_samples', 
        'cycle_report_planning_attributes',
        ['attribute_id'], 
        ['id']
    )
    
    # Add index for better query performance
    op.create_index(
        'ix_sample_selection_samples_attribute_id', 
        'cycle_report_sample_selection_samples', 
        ['attribute_id']
    )

def downgrade():
    # Remove index
    op.drop_index('ix_sample_selection_samples_attribute_id', 'cycle_report_sample_selection_samples')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_sample_selection_samples_attribute_id', 'cycle_report_sample_selection_samples', type_='foreignkey')
    
    # Remove column
    op.drop_column('cycle_report_sample_selection_samples', 'attribute_id')
