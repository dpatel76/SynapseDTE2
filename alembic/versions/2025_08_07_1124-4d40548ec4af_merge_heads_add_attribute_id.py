"""merge_heads_add_attribute_id

Revision ID: 4d40548ec4af
Revises: 75e09541c09f, add_attribute_id_to_samples
Create Date: 2025-08-07 11:24:21.288188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d40548ec4af'
down_revision: Union[str, None] = ('75e09541c09f', 'add_attribute_id_to_samples')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
