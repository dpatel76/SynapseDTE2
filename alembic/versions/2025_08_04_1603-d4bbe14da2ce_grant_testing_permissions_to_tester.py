"""grant_testing_permissions_to_tester

Revision ID: d4bbe14da2ce
Revises: b5dae5bcb74f
Create Date: 2025-08-04 16:03:51.102925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd4bbe14da2ce'
down_revision: Union[str, None] = 'b5dae5bcb74f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Grant testing and workflow permissions to Tester role."""
    op.execute(text("""
        -- Grant testing permissions to Tester role
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Tester'
        AND p.resource = 'testing'
        AND p.action IN ('execute', 'submit', 'read', 'complete')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );
        
        -- Grant workflow read permission to Tester role
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Tester'
        AND p.resource = 'workflow'
        AND p.action = 'read'
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );
        
        -- Also grant test execution permissions
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Tester'
        AND p.resource IN ('test_execution', 'test-execution')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );
    """))


def downgrade() -> None:
    """Remove testing and workflow permissions from Tester role."""
    op.execute(text("""
        -- Remove testing permissions from Tester
        DELETE FROM rbac_role_permissions
        WHERE role_id IN (
            SELECT role_id FROM rbac_roles WHERE role_name = 'Tester'
        )
        AND permission_id IN (
            SELECT permission_id FROM rbac_permissions 
            WHERE (resource = 'testing' AND action IN ('execute', 'submit', 'read', 'complete'))
            OR (resource = 'workflow' AND action = 'read')
            OR (resource IN ('test_execution', 'test-execution'))
        );
    """))
