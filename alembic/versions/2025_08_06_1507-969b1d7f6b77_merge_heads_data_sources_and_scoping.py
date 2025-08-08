"""merge_heads_data_sources_and_scoping

Revision ID: 969b1d7f6b77
Revises: grant_scoping_write_to_tester, grant_data_sources_read_001
Create Date: 2025-08-06 15:07:48.916560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '969b1d7f6b77'
down_revision: Union[str, None] = ('grant_scoping_write_to_tester', 'grant_data_sources_read_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
