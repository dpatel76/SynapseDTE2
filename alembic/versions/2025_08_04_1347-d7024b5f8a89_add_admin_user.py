"""add_admin_user

Revision ID: d7024b5f8a89
Revises: 82bb9fe518b2
Create Date: 2025-08-04 13:47:37.559660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd7024b5f8a89'
down_revision: Union[str, None] = '82bb9fe518b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add admin user with password123."""
    # The password hash is for "password123" using bcrypt
    # Generated using: bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode('utf-8')
    op.execute(text("""
        INSERT INTO users (
            first_name, 
            last_name, 
            email, 
            hashed_password,
            role,
            is_active,
            created_at,
            updated_at
        ) 
        SELECT 
            'Admin',
            'User',
            'admin@example.com',
            '$2b$12$oMNS1tfJFh10WSk5e91BCeCLkWkR0z7ihoZE000P.Vu0YiMj0KhGG',
            'Admin',
            true,
            NOW(),
            NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM users WHERE email = 'admin@example.com'
        );
    """))
    
    # Also ensure Admin role exists and assign it
    op.execute(text("""
        -- Ensure Admin role exists
        INSERT INTO rbac_roles (role_name, description, created_at, updated_at)
        SELECT 'Admin', 'System Administrator with full access', NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM rbac_roles WHERE role_name = 'Admin'
        );
        
        -- Assign Admin role to the admin user
        INSERT INTO rbac_user_roles (user_id, role_id, created_at, updated_at)
        SELECT 
            u.user_id,
            r.role_id,
            NOW(),
            NOW()
        FROM users u
        CROSS JOIN rbac_roles r
        WHERE u.email = 'admin@example.com'
        AND r.role_name = 'Admin'
        AND NOT EXISTS (
            SELECT 1 FROM rbac_user_roles ur
            WHERE ur.user_id = u.user_id
            AND ur.role_id = r.role_id
        );
        
        -- Grant all permissions to Admin role
        INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT 
            r.role_id,
            p.permission_id,
            NOW(),
            NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Admin'
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp
            WHERE rp.role_id = r.role_id
            AND rp.permission_id = p.permission_id
        );
    """))


def downgrade() -> None:
    """Remove admin user and their role assignments."""
    op.execute(text("""
        -- Remove user role assignments
        DELETE FROM rbac_user_roles
        WHERE user_id IN (
            SELECT user_id FROM users WHERE email = 'admin@example.com'
        );
        
        -- Remove the admin user
        DELETE FROM users WHERE email = 'admin@example.com';
    """))
