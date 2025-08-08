"""merge_heads_for_attribute_id

Revision ID: 46d5da8c4271
Revises: 4d40548ec4af, add_calculated_status
Create Date: 2025-08-07 22:18:25.615261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46d5da8c4271'
down_revision: Union[str, None] = ('4d40548ec4af', 'add_calculated_status')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
