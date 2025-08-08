"""add selection criteria to sample selection versions

Revision ID: fix_sample_selection_001
Revises: fix_scoping_attrs_001
Create Date: 2025-08-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_sample_selection_001'
down_revision = 'fix_scoping_attrs_001'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('cycle_report_sample_selection_versions')]
    
    if 'selection_criteria' not in existing_columns:
        # Add selection criteria column for audit trail
        op.add_column('cycle_report_sample_selection_versions',
                      sa.Column('selection_criteria', postgresql.JSONB(), 
                               nullable=False, server_default='{}'))
        
        # Populate with meaningful default for existing records
        op.execute("""
            UPDATE cycle_report_sample_selection_versions
            SET selection_criteria = jsonb_build_object(
                'method', 'intelligent_sampling',
                'parameters', jsonb_build_object(
                    'target_sample_size', target_sample_size,
                    'actual_sample_size', actual_sample_size,
                    'version_number', version_number
                ),
                'timestamp', NOW()
            )
            WHERE selection_criteria = '{}'::jsonb
        """)


def downgrade():
    op.drop_column('cycle_report_sample_selection_versions', 'selection_criteria')