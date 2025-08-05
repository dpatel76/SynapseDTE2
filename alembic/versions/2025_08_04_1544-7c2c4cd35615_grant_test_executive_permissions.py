"""grant_test_executive_permissions

Revision ID: 7c2c4cd35615
Revises: d7024b5f8a89
Create Date: 2025-08-04 15:44:43.386091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '7c2c4cd35615'
down_revision: Union[str, None] = 'd7024b5f8a89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Grant necessary permissions to Test Executive role."""
    op.execute(text("""
        -- Grant cycles permissions to Test Executive
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Test Executive'
        AND p.resource = 'cycles'
        AND p.action IN ('read', 'create', 'update', 'assign')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );

        -- Grant reports read permission to Test Executive
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Test Executive'
        AND p.resource = 'reports'
        AND p.action IN ('read', 'approve')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );

        -- Grant test execution related permissions
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Test Executive'
        AND p.resource IN ('test_execution', 'test-execution', 'test-cycles', 'test_report')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );

        -- Grant read permissions for other necessary resources
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Test Executive'
        AND p.resource IN ('planning', 'scoping', 'sample_selection', 'observations', 'users', 'lobs')
        AND p.action = 'read'
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );

        -- Grant data owner management permissions for test execution oversight
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Test Executive'
        AND p.resource = 'data_owner'
        AND p.action IN ('read', 'identify', 'assign', 'execute')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );

        -- Grant observation management permissions
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Test Executive'
        AND p.resource = 'observations'
        AND p.action IN ('create', 'update', 'approve')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );

        -- Grant workflow permissions
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Test Executive'
        AND p.resource = 'workflow'
        AND p.action IN ('read', 'start', 'update')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );
    """))
    
    # Also grant permissions to other testing roles
    op.execute(text("""
        -- Grant basic permissions to Tester role
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT r.role_id, p.permission_id, NOW(), NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Tester'
        AND p.resource IN ('cycles', 'reports', 'test-cycles')
        AND p.action = 'read'
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id 
            AND rp.permission_id = p.permission_id
        );
    """))


def downgrade() -> None:
    """Remove Test Executive permissions."""
    op.execute(text("""
        -- Remove all permissions granted to Test Executive in this migration
        DELETE FROM rbac_role_permissions
        WHERE role_id IN (
            SELECT role_id FROM rbac_roles WHERE role_name = 'Test Executive'
        )
        AND permission_id IN (
            SELECT permission_id FROM rbac_permissions 
            WHERE (resource = 'cycles' AND action IN ('read', 'create', 'update', 'assign'))
            OR (resource = 'reports' AND action IN ('read', 'approve'))
            OR (resource IN ('test_execution', 'test-execution', 'test-cycles', 'test_report'))
            OR (resource IN ('planning', 'scoping', 'sample_selection', 'observations', 'users', 'lobs') AND action = 'read')
            OR (resource = 'data_owner' AND action IN ('read', 'identify', 'assign', 'execute'))
            OR (resource = 'observations' AND action IN ('create', 'update', 'approve'))
            OR (resource = 'workflow' AND action IN ('read', 'start', 'update'))
        );

        -- Remove Tester permissions added in this migration
        DELETE FROM rbac_role_permissions
        WHERE role_id IN (
            SELECT role_id FROM rbac_roles WHERE role_name = 'Tester'
        )
        AND permission_id IN (
            SELECT permission_id FROM rbac_permissions 
            WHERE resource IN ('cycles', 'reports', 'test-cycles')
            AND action = 'read'
        );
    """))
