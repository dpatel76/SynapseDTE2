"""merge_fix_migrations_and_data_load

Revision ID: 75e09541c09f
Revises: fix_sample_selection_001, load_actual_fry14m_data
Create Date: 2025-08-06 21:09:07.503286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75e09541c09f'
down_revision: Union[str, None] = ('fix_sample_selection_001', 'load_actual_fry14m_data')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
