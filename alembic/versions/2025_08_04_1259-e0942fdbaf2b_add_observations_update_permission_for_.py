"""add_observations_update_permission_for_tester

Revision ID: e0942fdbaf2b
Revises: 8e57a38d62a2
Create Date: 2025-08-04 12:59:01.132676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0942fdbaf2b'
down_revision: Union[str, None] = '8e57a38d62a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add observations:update permission if it doesn't exist
    op.execute("""
        INSERT INTO rbac_permissions (resource, action, description, created_at, updated_at)
        SELECT 'observations', 'update', 'Update observations', NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM rbac_permissions 
            WHERE resource = 'observations' AND action = 'update'
        );
    """)
    
    # Grant the permission to Tester role
    op.execute("""
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT 
            r.role_id,
            p.permission_id,
            NOW(),
            NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Tester'
        AND p.resource = 'observations'
        AND p.action = 'update'
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp
            WHERE rp.role_id = r.role_id
            AND rp.permission_id = p.permission_id
        );
    """)
    
    # Also grant observation_enhanced permissions to Tester for the enhanced endpoints
    op.execute("""
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT 
            r.role_id,
            p.permission_id,
            NOW(),
            NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Tester'
        AND p.resource = 'observation_enhanced'
        AND p.action IN ('read', 'write', 'approve')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp
            WHERE rp.role_id = r.role_id
            AND rp.permission_id = p.permission_id
        );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove permissions from Tester role
    op.execute("""
        DELETE FROM rbac_role_permissions
        WHERE role_id IN (SELECT role_id FROM rbac_roles WHERE role_name = 'Tester')
        AND permission_id IN (
            SELECT permission_id FROM rbac_permissions 
            WHERE (resource = 'observations' AND action = 'update')
            OR (resource = 'observation_enhanced' AND action IN ('read', 'write', 'approve'))
        );
    """)
    
    # Remove the observations:update permission
    op.execute("""
        DELETE FROM rbac_permissions
        WHERE resource = 'observations' AND action = 'update';
    """)
