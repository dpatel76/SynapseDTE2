"""grant_metrics_permissions_to_test_executive

Revision ID: b5dae5bcb74f
Revises: 620d2bb9cfd9
Create Date: 2025-08-04 15:56:52.039545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'b5dae5bcb74f'
down_revision: Union[str, None] = '620d2bb9cfd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Grant metrics permissions to Test Executive role."""
    op.execute(text("""
        -- Grant metrics permissions to Test Executive
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Test Executive'
        AND p.resource = 'metrics'
        AND p.action IN ('read', 'generate')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );
        
        -- Also grant metrics permissions to other executive roles
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name IN ('Report Executive', 'Admin')
        AND p.resource = 'metrics'
        AND p.action IN ('read', 'generate')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );
    """))


def downgrade() -> None:
    """Remove metrics permissions from Test Executive role."""
    op.execute(text("""
        -- Remove metrics permissions from Test Executive
        DELETE FROM rbac_role_permissions
        WHERE role_id IN (
            SELECT role_id FROM rbac_roles WHERE role_name = 'Test Executive'
        )
        AND permission_id IN (
            SELECT permission_id FROM rbac_permissions 
            WHERE resource = 'metrics'
            AND action IN ('read', 'generate')
        );
        
        -- Remove metrics permissions from other executive roles added in this migration
        DELETE FROM rbac_role_permissions
        WHERE role_id IN (
            SELECT role_id FROM rbac_roles WHERE role_name IN ('Report Executive', 'Admin')
        )
        AND permission_id IN (
            SELECT permission_id FROM rbac_permissions 
            WHERE resource = 'metrics'
            AND action IN ('read', 'generate')
        );
    """))
