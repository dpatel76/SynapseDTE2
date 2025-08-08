"""grant_data_sources_read_to_tester

Revision ID: grant_data_sources_read_001
Revises: load_fry14m_test_data
Create Date: 2025-08-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'grant_data_sources_read_001'
down_revision = 'load_fry14m_test_data'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    
    # First check if the permission exists, if not create it
    perm_check = conn.execute(text("""
        SELECT permission_id FROM rbac_permissions 
        WHERE resource = 'data_sources' AND action = 'read'
    """)).fetchone()
    
    if not perm_check:
        # Create the permission
        conn.execute(text("""
            INSERT INTO rbac_permissions (resource, action, description, created_at, updated_at)
            VALUES ('data_sources', 'read', 'Read data sources', NOW(), NOW())
        """))
        
        perm_check = conn.execute(text("""
            SELECT permission_id FROM rbac_permissions 
            WHERE resource = 'data_sources' AND action = 'read'
        """)).fetchone()
    
    permission_id = perm_check[0]
    
    # Get the Tester role ID
    role_check = conn.execute(text("""
        SELECT role_id FROM rbac_roles WHERE role_name = 'Tester'
    """)).fetchone()
    
    if role_check:
        role_id = role_check[0]
        
        # Check if role permission already exists
        rp_check = conn.execute(text("""
            SELECT 1 FROM rbac_role_permissions 
            WHERE role_id = :role_id AND permission_id = :permission_id
        """), {"role_id": role_id, "permission_id": permission_id}).fetchone()
        
        if not rp_check:
            # Add role permission
            conn.execute(text("""
                INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
                VALUES (:role_id, :permission_id, NOW(), NOW())
            """), {"role_id": role_id, "permission_id": permission_id})
            
    # Also grant to Report Owner role
    role_check = conn.execute(text("""
        SELECT role_id FROM rbac_roles WHERE role_name = 'Report Owner'
    """)).fetchone()
    
    if role_check:
        role_id = role_check[0]
        
        # Check if role permission already exists
        rp_check = conn.execute(text("""
            SELECT 1 FROM rbac_role_permissions 
            WHERE role_id = :role_id AND permission_id = :permission_id
        """), {"role_id": role_id, "permission_id": permission_id}).fetchone()
        
        if not rp_check:
            # Add role permission
            conn.execute(text("""
                INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
                VALUES (:role_id, :permission_id, NOW(), NOW())
            """), {"role_id": role_id, "permission_id": permission_id})

def downgrade():
    conn = op.get_bind()
    
    # Remove the permission grants
    conn.execute(text("""
        DELETE FROM rbac_role_permissions 
        WHERE permission_id = (
            SELECT permission_id FROM rbac_permissions 
            WHERE resource = 'data_sources' AND action = 'read'
        )
        AND role_id IN (
            SELECT role_id FROM rbac_roles 
            WHERE role_name IN ('Tester', 'Report Owner')
        )
    """))