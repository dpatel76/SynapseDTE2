"""Make lob_id nullable in sample selection

Revision ID: make_lob_id_nullable
Revises: 
Create Date: 2025-01-28 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_01_28_make_lob_nullable'
down_revision = '2025_01_25_create_rfi_version_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Make lob_id nullable in cycle_report_sample_selection_samples table
    op.alter_column('cycle_report_sample_selection_samples', 'lob_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)


def downgrade():
    # Revert lob_id back to non-nullable
    op.alter_column('cycle_report_sample_selection_samples', 'lob_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)