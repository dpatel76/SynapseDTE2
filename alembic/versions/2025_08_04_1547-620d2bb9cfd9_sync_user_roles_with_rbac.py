"""sync_user_roles_with_rbac

Revision ID: 620d2bb9cfd9
Revises: 7c2c4cd35615
Create Date: 2025-08-04 15:47:41.029389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '620d2bb9cfd9'
down_revision: Union[str, None] = '7c2c4cd35615'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Sync user roles with RBAC roles - ensure all users have matching RBAC role assignments."""
    op.execute(text("""
        -- Assign matching RBAC roles to all users based on their user.role field
        INSERT INTO rbac_user_roles (user_id, role_id, created_at, updated_at)
        SELECT DISTINCT u.user_id, r.role_id, NOW(), NOW()
        FROM users u
        INNER JOIN rbac_roles r ON u.role::text = r.role_name
        WHERE u.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM rbac_user_roles ur
            WHERE ur.user_id = u.user_id
            AND ur.role_id = r.role_id
        );
    """))


def downgrade() -> None:
    """Remove auto-assigned RBAC roles (keeping manually assigned ones)."""
    # Note: This is a best-effort downgrade. We can't distinguish between
    # auto-assigned and manually-assigned roles perfectly, so we'll remove
    # all role assignments that match user.role = rbac_role.role_name
    op.execute(text("""
        -- Remove RBAC role assignments that match user.role field
        DELETE FROM rbac_user_roles
        WHERE (user_id, role_id) IN (
            SELECT u.user_id, r.role_id
            FROM users u
            INNER JOIN rbac_roles r ON u.role::text = r.role_name
        );
    """))
