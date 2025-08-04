"""Merge all heads

Revision ID: aed28248d79b
Revises: 7d8540cc2291, 1f8b43c51c29
Create Date: 2025-06-08 12:44:07.621953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aed28248d79b'
down_revision: Union[str, None] = ('7d8540cc2291', '1f8b43c51c29')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
