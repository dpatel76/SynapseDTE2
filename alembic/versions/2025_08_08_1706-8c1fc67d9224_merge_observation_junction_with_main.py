"""merge_observation_junction_with_main

Revision ID: 8c1fc67d9224
Revises: add_obs_test_exec_junction, 46d5da8c4271
Create Date: 2025-08-08 17:06:34.756959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c1fc67d9224'
down_revision: Union[str, None] = ('add_obs_test_exec_junction', '46d5da8c4271')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
