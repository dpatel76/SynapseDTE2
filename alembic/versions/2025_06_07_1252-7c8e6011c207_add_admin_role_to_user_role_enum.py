"""Add Admin role to user_role_enum

Revision ID: 7c8e6011c207
Revises: 2025_06_07_1230_initial_schema
Create Date: 2025-06-07 12:52:45.697921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c8e6011c207'
down_revision: Union[str, None] = '2025_06_07_1230_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add 'Admin' to the user_role_enum
    op.execute("ALTER TYPE user_role_enum ADD VALUE 'Admin';")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type which is complex
    # For now, leave as no-op since enum values are not easily removable
    pass
