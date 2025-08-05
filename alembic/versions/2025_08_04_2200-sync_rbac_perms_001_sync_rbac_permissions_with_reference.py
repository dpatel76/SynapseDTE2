"""sync_rbac_permissions_with_reference

Revision ID: sync_rbac_perms_001
Revises: 82bb9fe518b2
Create Date: 2025-08-04 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'sync_rbac_perms_001'
down_revision = 'd4bbe14da2ce'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    
    # First, add any missing permissions that exist in reference but not in container
    missing_permissions = [
        # These are all present, container has all ref permissions plus observations:update
    ]
    
    # Add missing role permissions for Test Executive
    test_executive_permissions = [
        ('Test Executive', 'analytics', 'read'),
        ('Test Executive', 'cycles', 'delete'),
        ('Test Executive', 'data_profiling', 'assign'),
        ('Test Executive', 'reports', 'assign'),
        ('Test Executive', 'reports', 'create'),
        ('Test Executive', 'testing', 'read'),
        ('Test Executive', 'workflow', 'approve')
    ]
    
    # Add missing role permissions for Tester
    tester_permissions = [
        ('Tester', 'data_owner', 'complete'),
        ('Tester', 'data_owner', 'execute'),
        ('Tester', 'data_owner', 'read'),
        ('Tester', 'data_owner', 'upload'),
        ('Tester', 'data_profiling', 'assign'),
        ('Tester', 'lobs', 'read'),
        ('Tester', 'metrics', 'read'),
        ('Tester', 'observations', 'approve'),
        ('Tester', 'observations', 'create'),
        ('Tester', 'observations', 'delete'),
        ('Tester', 'observations', 'override'),
        ('Tester', 'observations', 'read'),
        ('Tester', 'observations', 'review'),
        ('Tester', 'observations', 'submit'),
        ('Tester', 'planning', 'complete'),
        ('Tester', 'planning', 'create'),
        ('Tester', 'planning', 'delete'),
        ('Tester', 'planning', 'execute'),
        ('Tester', 'planning', 'update'),
        ('Tester', 'planning', 'upload'),
        ('Tester', 'request_info', 'complete'),
        ('Tester', 'request_info', 'execute'),
        ('Tester', 'request_info', 'provide'),
        ('Tester', 'request_info', 'read'),
        ('Tester', 'request_info', 'review'),
        ('Tester', 'request_info', 'upload'),
        ('Tester', 'sample_selection', 'complete'),
        ('Tester', 'sample_selection', 'execute'),
        ('Tester', 'sample_selection', 'generate'),
        ('Tester', 'sample_selection', 'read'),
        ('Tester', 'sample_selection', 'upload'),
        ('Tester', 'scoping', 'complete'),
        ('Tester', 'scoping', 'execute'),
        ('Tester', 'scoping', 'generate'),
        ('Tester', 'scoping', 'submit'),
        ('Tester', 'test_report', 'approve'),
        ('Tester', 'test_report', 'read'),
        ('Tester', 'test_report', 'write'),
        ('Tester', 'testing', 'approve'),
        ('Tester', 'testing', 'review')
    ]
    
    # Add missing role permissions for Report Owner
    report_owner_permissions = [
        ('Report Owner', 'cycles', 'read'),
        ('Report Owner', 'lobs', 'read'),
        ('Report Owner', 'metrics', 'read'),
        ('Report Owner', 'observation_enhanced', 'approve'),
        ('Report Owner', 'observation_enhanced', 'rate'),
        ('Report Owner', 'observation_enhanced', 'read'),
        ('Report Owner', 'observations', 'approve'),
        ('Report Owner', 'observations', 'read'),
        ('Report Owner', 'observations', 'review'),
        ('Report Owner', 'reports', 'approve'),
        ('Report Owner', 'reports', 'read'),
        ('Report Owner', 'sample_selection', 'approve'),
        ('Report Owner', 'sample_selection', 'read'),
        ('Report Owner', 'scoping', 'approve'),
        ('Report Owner', 'scoping', 'read'),
        ('Report Owner', 'test_report', 'approve'),
        ('Report Owner', 'test_report', 'read'),
        ('Report Owner', 'test-cycles', 'read'),
        ('Report Owner', 'testing', 'approve'),
        ('Report Owner', 'testing', 'read'),
        ('Report Owner', 'testing', 'review'),
        ('Report Owner', 'workflow', 'approve'),
        ('Report Owner', 'workflow', 'read')
    ]
    
    # Add missing role permissions for Data Owner
    data_owner_permissions = [
        ('Data Owner', 'cycles', 'read'),
        ('Data Owner', 'data_owner', 'execute'),
        ('Data Owner', 'data_owner', 'read'),
        ('Data Owner', 'data_owner', 'upload'),
        ('Data Owner', 'data_source', 'manage'),
        ('Data Owner', 'metrics', 'read'),
        ('Data Owner', 'observation_enhanced', 'read'),
        ('Data Owner', 'request_info', 'provide'),
        ('Data Owner', 'request_info', 'read'),
        ('Data Owner', 'request_info', 'upload'),
        ('Data Owner', 'request_info', 'write'),
        ('Data Owner', 'sample_selection', 'read'),
        ('Data Owner', 'test_report', 'read'),
        ('Data Owner', 'test-cycles', 'read'),
        ('Data Owner', 'workflow', 'read')
    ]
    
    # Process all role permissions
    all_permissions = (
        test_executive_permissions + 
        tester_permissions + 
        report_owner_permissions + 
        data_owner_permissions
    )
    
    for role_name, resource, action in all_permissions:
        # Check if permission exists, if not create it
        perm_check = conn.execute(text("""
            SELECT permission_id FROM rbac_permissions 
            WHERE resource = :resource AND action = :action
        """), {"resource": resource, "action": action}).fetchone()
        
        if not perm_check:
            # Create the permission
            conn.execute(text("""
                INSERT INTO rbac_permissions (resource, action, description, created_at, updated_at)
                VALUES (:resource, :action, :description, NOW(), NOW())
            """), {
                "resource": resource, 
                "action": action,
                "description": f"{action.title()} {resource.replace('_', ' ')}"
            })
            
            perm_check = conn.execute(text("""
                SELECT permission_id FROM rbac_permissions 
                WHERE resource = :resource AND action = :action
            """), {"resource": resource, "action": action}).fetchone()
        
        permission_id = perm_check[0]
        
        # Get role ID
        role_check = conn.execute(text("""
            SELECT role_id FROM rbac_roles WHERE role_name = :role_name
        """), {"role_name": role_name}).fetchone()
        
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
    # This migration is meant to sync with reference, so no downgrade
    pass
