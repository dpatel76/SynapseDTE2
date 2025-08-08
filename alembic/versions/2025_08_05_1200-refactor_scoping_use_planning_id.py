"""refactor scoping to use planning attribute id as primary identifier

Revision ID: refactor_scoping_use_planning_id
Revises: load_fry14m_test_data
Create Date: 2025-08-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'refactor_scoping_use_planning_id'
down_revision = 'load_fry14m_test_data'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Drop the existing primary key constraint on UUID attribute_id
    op.drop_constraint('cycle_report_scoping_attributes_reorder_temp_pkey', 'cycle_report_scoping_attributes', type_='primary')
    
    # Step 2: Rename the UUID attribute_id to old_attribute_id to avoid conflicts
    op.alter_column('cycle_report_scoping_attributes', 'attribute_id', new_column_name='old_attribute_id')
    
    # Step 3: Rename planning_attribute_id to attribute_id
    op.alter_column('cycle_report_scoping_attributes', 'planning_attribute_id', new_column_name='attribute_id')
    
    # Step 4: Create composite primary key on (version_id, attribute_id)
    op.create_primary_key(
        'pk_scoping_version_attribute',
        'cycle_report_scoping_attributes',
        ['version_id', 'attribute_id']
    )
    
    # Step 5: Create indexes for better performance
    op.create_index(
        'idx_scoping_attribute_id',
        'cycle_report_scoping_attributes',
        ['attribute_id']
    )
    
    # Step 6: Drop the old UUID column
    op.drop_column('cycle_report_scoping_attributes', 'old_attribute_id')


def downgrade():
    # Add back the UUID column
    op.add_column('cycle_report_scoping_attributes', 
        sa.Column('old_attribute_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False)
    )
    
    # Drop the composite primary key
    op.drop_constraint('pk_scoping_version_attribute', 'cycle_report_scoping_attributes', type_='primary')
    
    # Rename attribute_id back to planning_attribute_id
    op.alter_column('cycle_report_scoping_attributes', 'attribute_id', new_column_name='planning_attribute_id')
    
    # Rename old_attribute_id back to attribute_id
    op.alter_column('cycle_report_scoping_attributes', 'old_attribute_id', new_column_name='attribute_id')
    
    # Recreate the original primary key
    op.create_primary_key('cycle_report_scoping_attributes_pkey', 'cycle_report_scoping_attributes', ['attribute_id'])
    
    # Drop the indexes
    op.drop_index('idx_scoping_version_attribute', table_name='cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attribute_id', table_name='cycle_report_scoping_attributes')