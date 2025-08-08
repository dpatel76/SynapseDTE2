"""grant scoping write permission to tester role

Revision ID: grant_scoping_write_to_tester
Revises: refactor_scoping_use_planning_id
Create Date: 2025-08-05 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'grant_scoping_write_to_tester'
down_revision = 'refactor_scoping_use_planning_id'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    # Check if scoping:write permission exists, if not create it
    result = conn.execute(text("""
        SELECT permission_id FROM rbac_permissions 
        WHERE resource = 'scoping' AND action = 'write'
    """)).fetchone()
    
    if not result:
        # Create the permission
        conn.execute(text("""
            INSERT INTO rbac_permissions (resource, action, description, created_at, updated_at)
            VALUES ('scoping', 'write', 'Write access to scoping phase', NOW(), NOW())
        """))
    
    # Get the permission_id
    result = conn.execute(text("""
        SELECT permission_id FROM rbac_permissions 
        WHERE resource = 'scoping' AND action = 'write'
    """)).fetchone()
    
    permission_id = result[0]
    
    # Get the Tester role_id
    result = conn.execute(text("""
        SELECT role_id FROM rbac_roles WHERE role_name = 'Tester'
    """)).fetchone()
    
    if result:
        role_id = result[0]
        
        # Check if the permission is already granted
        existing = conn.execute(text("""
            SELECT 1 FROM rbac_role_permissions 
            WHERE role_id = :role_id AND permission_id = :permission_id
        """), {"role_id": role_id, "permission_id": permission_id}).fetchone()
        
        if not existing:
            # Grant the permission to Tester role
            conn.execute(text("""
                INSERT INTO rbac_role_permissions (role_id, permission_id, created_at, updated_at)
                VALUES (:role_id, :permission_id, NOW(), NOW())
            """), {"role_id": role_id, "permission_id": permission_id})
            
            print(f"Granted scoping:write permission to Tester role")
        else:
            print("Tester already has scoping:write permission")


def downgrade():
    conn = op.get_bind()
    
    # Remove the permission from Tester role
    conn.execute(text("""
        DELETE FROM rbac_role_permissions
        WHERE role_id = (SELECT role_id FROM rbac_roles WHERE role_name = 'Tester')
        AND permission_id = (SELECT permission_id FROM rbac_permissions WHERE resource = 'scoping' AND action = 'write')
    """))