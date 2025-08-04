"""Merge multiple heads

Revision ID: 2025_07_11_merge_heads
Revises: 010_add_data_profiling_tables, 2025_07_11_redesign
Create Date: 2025-07-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2025_07_11_merge_heads'
down_revision: Union[str, Sequence[str], None] = ('010_add_data_profiling_tables', '2025_07_11_redesign')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration - no changes needed"""
    pass


def downgrade() -> None:
    """Merge migration - no changes needed"""
    pass