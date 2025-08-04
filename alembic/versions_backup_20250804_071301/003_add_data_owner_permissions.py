"""Add data owner permissions for data source management

Revision ID: 003_add_data_owner_permissions
Revises: 002_seed_rbac_data
Create Date: 2025-01-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '003_add_data_owner_permissions'
down_revision = 'create_rfi_version_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add data source management permissions for Data Owner role"""
    
    # Create references to tables
    permissions_table = table('rbac_permissions',
        column('permission_id', sa.Integer),
        column('permission_name', sa.String),
        column('resource', sa.String),
        column('action', sa.String),
        column('description', sa.Text),
        column('created_at', sa.DateTime)
    )
    
    role_permissions_table = table('rbac_role_permissions',
        column('role_id', sa.Integer),
        column('permission_id', sa.Integer),
        column('created_at', sa.DateTime)
    )
    
    # Insert new permissions for data source management
    new_permissions = [
        {
            'permission_id': 70,
            'permission_name': 'manage_data_sources',
            'resource': 'data_source',
            'action': 'manage',
            'description': 'Create, update and test data sources',
            'created_at': datetime.utcnow()
        },
        {
            'permission_id': 71,
            'permission_name': 'request_info_write',
            'resource': 'request_info',
            'action': 'write',
            'description': 'Write access to request info resources',
            'created_at': datetime.utcnow()
        },
        {
            'permission_id': 72,
            'permission_name': 'request_info_read',
            'resource': 'request_info',
            'action': 'read',
            'description': 'Read access to request info resources',
            'created_at': datetime.utcnow()
        }
    ]
    
    op.bulk_insert(permissions_table, new_permissions)
    
    # Grant these permissions to Data Owner role (role_id = 3)
    new_role_permissions = [
        {
            'role_id': 3,  # Data Owner
            'permission_id': 70,  # manage_data_sources
            'created_at': datetime.utcnow()
        },
        {
            'role_id': 3,  # Data Owner
            'permission_id': 71,  # request_info_write
            'created_at': datetime.utcnow()
        },
        {
            'role_id': 3,  # Data Owner
            'permission_id': 72,  # request_info_read
            'created_at': datetime.utcnow()
        },
        # Also grant to Admin (role_id = 7)
        {
            'role_id': 7,  # Admin
            'permission_id': 70,
            'created_at': datetime.utcnow()
        },
        {
            'role_id': 7,  # Admin
            'permission_id': 71,
            'created_at': datetime.utcnow()
        },
        {
            'role_id': 7,  # Admin
            'permission_id': 72,
            'created_at': datetime.utcnow()
        }
    ]
    
    op.bulk_insert(role_permissions_table, new_role_permissions)
    
    # Log the changes
    print("Added data source management permissions for Data Owner role")
    print("- manage_data_sources (id: 70)")
    print("- request_info_write (id: 71)")
    print("- request_info_read (id: 72)")


def downgrade() -> None:
    """Remove added permissions"""
    
    # Remove role-permission mappings first
    op.execute("DELETE FROM rbac_role_permissions WHERE permission_id IN (70, 71, 72)")
    
    # Remove permissions
    op.execute("DELETE FROM rbac_permissions WHERE permission_id IN (70, 71, 72)")