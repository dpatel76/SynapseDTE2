"""add_regulatory_data_dictionary_table

Revision ID: 8a35f71596ce
Revises: 0fc64ad9fd82
Create Date: 2025-06-07 14:31:15.095446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a35f71596ce'
down_revision: Union[str, None] = '0fc64ad9fd82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add regulatory data dictionary table."""
    op.create_table(
        'regulatory_data_dictionary',
        sa.Column('dict_id', sa.Integer(), nullable=False),
        sa.Column('report_name', sa.String(255), nullable=False, index=True),
        sa.Column('schedule_name', sa.String(255), nullable=False, index=True),
        sa.Column('line_item_number', sa.String(50), nullable=True),
        sa.Column('line_item_name', sa.String(500), nullable=False, index=True),
        sa.Column('technical_line_item_name', sa.String(500), nullable=True),
        sa.Column('mdrm', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('static_or_dynamic', sa.String(20), nullable=True),
        sa.Column('mandatory_or_optional', sa.String(20), nullable=True, index=True),
        sa.Column('format_specification', sa.String(200), nullable=True),
        sa.Column('num_reports_schedules_used', sa.String(50), nullable=True),
        sa.Column('other_schedule_reference', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('dict_id'),
        sa.Index('ix_rdd_report_schedule', 'report_name', 'schedule_name'),
        sa.Index('ix_rdd_item_name_search', 'line_item_name'),
        sa.Index('ix_rdd_mandatory_search', 'mandatory_or_optional'),
    )


def downgrade() -> None:
    """Drop regulatory data dictionary table."""
    op.drop_table('regulatory_data_dictionary')
