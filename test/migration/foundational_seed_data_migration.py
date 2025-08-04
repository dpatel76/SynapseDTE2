"""
Clean foundational seed data migration for SynapseDTE

This migration creates all foundational data required for the system to function:
- User roles and RBAC permissions
- Workflow phase configurations
- SLA configurations
- Lines of Business (LOBs)
- Essential reference data

Based on analysis of existing models, migrations, and system requirements.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime


def upgrade() -> None:
    """Create foundational seed data"""
    
    print("🌱 Seeding foundational data for SynapseDTE...")
    
    # Create enum types first
    user_role_enum = ENUM(
        'Tester',
        'Test Executive', 
        'Report Owner',
        'Report Owner Executive',
        'Data Owner',
        'Data Executive',
        'Admin',
        name='user_role_enum'
    )
    
    # Create phase status enum
    phase_status_enum = ENUM(
        'not_started',
        'in_progress', 
        'pending_review',
        'completed',
        'blocked',
        'skipped',
        name='phase_status_enum'
    )
    
    # Create workflow state enum
    workflow_state_enum = ENUM(
        'draft',
        'active',
        'paused',
        'completed',
        'cancelled',
        name='workflow_state_enum'
    )
    
    # Create report status enum
    report_status_enum = ENUM(
        'draft',
        'active',
        'in_testing',
        'completed',
        'archived',
        name='report_status_enum'
    )
    
    # Create cycle status enum  
    cycle_status_enum = ENUM(
        'planning',
        'active',
        'completed',
        'cancelled',
        name='cycle_status_enum'
    )
    
    # Note: Enums are typically created in the main schema migration
    # This is just for reference - they should already exist
    
    # Define table references for bulk inserts
    lobs_table = table('lobs',
        column('lob_id', sa.Integer),
        column('lob_name', sa.String),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )
    
    roles_table = table('rbac_roles',
        column('role_id', sa.Integer),
        column('role_name', sa.String),
        column('description', sa.Text),
        column('is_system', sa.Boolean),
        column('is_active', sa.Boolean),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )
    
    permissions_table = table('rbac_permissions',
        column('permission_id', sa.Integer),
        column('resource', sa.String),
        column('action', sa.String),
        column('description', sa.Text),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )
    
    role_permissions_table = table('rbac_role_permissions',
        column('role_id', sa.Integer),
        column('permission_id', sa.Integer),
        column('granted_at', sa.DateTime)
    )
    
    sla_configurations_table = table('universal_sla_configurations',
        column('sla_id', sa.Integer),
        column('sla_type', sa.String),
        column('duration_hours', sa.Integer),
        column('warning_hours', sa.Integer),
        column('business_hours_only', sa.Boolean),
        column('exclude_weekends', sa.Boolean),
        column('escalation_enabled', sa.Boolean),
        column('is_active', sa.Boolean),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )
    
    # 1. Insert Lines of Business (LOBs)
    print("  📊 Seeding Lines of Business...")
    lob_data = [
        {'lob_id': 1, 'lob_name': 'Consumer Banking'},
        {'lob_id': 2, 'lob_name': 'Commercial Banking'},
        {'lob_id': 3, 'lob_name': 'Investment Banking'},
        {'lob_id': 4, 'lob_name': 'Wealth Management'},
        {'lob_id': 5, 'lob_name': 'Capital Markets'},
        {'lob_id': 6, 'lob_name': 'Risk Management'},
        {'lob_id': 7, 'lob_name': 'Corporate Treasury'},
        {'lob_id': 8, 'lob_name': 'Compliance & Legal'},
    ]
    
    for lob in lob_data:
        lob['created_at'] = datetime.utcnow()
        lob['updated_at'] = datetime.utcnow()
    
    op.bulk_insert(lobs_table, lob_data)
    
    # 2. Insert RBAC Roles
    print("  👥 Seeding RBAC Roles...")
    role_data = [
        {
            'role_id': 1,
            'role_name': 'tester',
            'description': 'Executes testing workflow phases and creates test cases',
            'is_system': True,
            'is_active': True
        },
        {
            'role_id': 2,
            'role_name': 'test_executive',
            'description': 'Manages test cycles and assigns reports to testers',
            'is_system': True,
            'is_active': True
        },
        {
            'role_id': 3,
            'role_name': 'report_owner',
            'description': 'Approves testing decisions and reviews observations',
            'is_system': True,
            'is_active': True
        },
        {
            'role_id': 4,
            'role_name': 'report_owner_executive',
            'description': 'Executive oversight of report portfolio',
            'is_system': True,
            'is_active': True
        },
        {
            'role_id': 5,
            'role_name': 'data_owner',
            'description': 'Provides source data and confirms information accuracy',
            'is_system': True,
            'is_active': True
        },
        {
            'role_id': 6,
            'role_name': 'data_executive',
            'description': 'Manages data owner assignments for line of business',
            'is_system': True,
            'is_active': True
        },
        {
            'role_id': 7,
            'role_name': 'admin',
            'description': 'System administrator with full access',
            'is_system': True,
            'is_active': True
        }
    ]
    
    for role in role_data:
        role['created_at'] = datetime.utcnow()
        role['updated_at'] = datetime.utcnow()
    
    op.bulk_insert(roles_table, role_data)
    
    # 3. Insert Permissions
    print("  🔐 Seeding Permissions...")
    permission_data = [
        # Dashboard permissions
        {'permission_id': 1, 'resource': 'dashboard', 'action': 'view', 'description': 'View dashboard'},
        {'permission_id': 2, 'resource': 'dashboard', 'action': 'view_tester', 'description': 'View tester dashboard'},
        {'permission_id': 3, 'resource': 'dashboard', 'action': 'view_executive', 'description': 'View executive dashboard'},
        {'permission_id': 4, 'resource': 'dashboard', 'action': 'view_data_owner', 'description': 'View data owner dashboard'},
        {'permission_id': 5, 'resource': 'dashboard', 'action': 'view_cdo', 'description': 'View CDO dashboard'},
        
        # Test cycle management
        {'permission_id': 10, 'resource': 'test_cycle', 'action': 'create', 'description': 'Create test cycles'},
        {'permission_id': 11, 'resource': 'test_cycle', 'action': 'read', 'description': 'View test cycles'},
        {'permission_id': 12, 'resource': 'test_cycle', 'action': 'update', 'description': 'Update test cycles'},
        {'permission_id': 13, 'resource': 'test_cycle', 'action': 'delete', 'description': 'Delete test cycles'},
        
        # Report management
        {'permission_id': 20, 'resource': 'report', 'action': 'create', 'description': 'Create reports'},
        {'permission_id': 21, 'resource': 'report', 'action': 'read', 'description': 'View reports'},
        {'permission_id': 22, 'resource': 'report', 'action': 'update', 'description': 'Update reports'},
        {'permission_id': 23, 'resource': 'report', 'action': 'delete', 'description': 'Delete reports'},
        {'permission_id': 24, 'resource': 'report', 'action': 'assign', 'description': 'Assign reports to testers'},
        
        # Workflow phase permissions
        {'permission_id': 30, 'resource': 'planning_phase', 'action': 'execute', 'description': 'Execute planning phase'},
        {'permission_id': 31, 'resource': 'scoping_phase', 'action': 'execute', 'description': 'Execute scoping phase'},
        {'permission_id': 32, 'resource': 'scoping_phase', 'action': 'approve', 'description': 'Approve scoping submissions'},
        {'permission_id': 33, 'resource': 'sample_selection_phase', 'action': 'execute', 'description': 'Execute sample selection'},
        {'permission_id': 34, 'resource': 'sample_selection_phase', 'action': 'approve', 'description': 'Approve sample selection'},
        {'permission_id': 35, 'resource': 'data_owner_phase', 'action': 'assign', 'description': 'Assign data owners'},
        {'permission_id': 36, 'resource': 'data_owner_phase', 'action': 'execute', 'description': 'Execute data owner tasks'},
        {'permission_id': 37, 'resource': 'request_info_phase', 'action': 'submit', 'description': 'Submit request information'},
        {'permission_id': 38, 'resource': 'test_execution_phase', 'action': 'execute', 'description': 'Execute testing phase'},
        {'permission_id': 39, 'resource': 'observation_phase', 'action': 'create', 'description': 'Create observations'},
        {'permission_id': 40, 'resource': 'observation_phase', 'action': 'approve', 'description': 'Approve observations'},
        
        # User management
        {'permission_id': 50, 'resource': 'user', 'action': 'create', 'description': 'Create users'},
        {'permission_id': 51, 'resource': 'user', 'action': 'read', 'description': 'View users'},
        {'permission_id': 52, 'resource': 'user', 'action': 'update', 'description': 'Update users'},
        {'permission_id': 53, 'resource': 'user', 'action': 'delete', 'description': 'Delete users'},
        {'permission_id': 54, 'resource': 'user', 'action': 'manage_roles', 'description': 'Manage user roles'},
        
        # RBAC management
        {'permission_id': 60, 'resource': 'rbac', 'action': 'manage', 'description': 'Manage RBAC system'},
        {'permission_id': 61, 'resource': 'role', 'action': 'create', 'description': 'Create roles'},
        {'permission_id': 62, 'resource': 'role', 'action': 'read', 'description': 'View roles'},
        {'permission_id': 63, 'resource': 'role', 'action': 'update', 'description': 'Update roles'},
        {'permission_id': 64, 'resource': 'role', 'action': 'delete', 'description': 'Delete roles'},
        {'permission_id': 65, 'resource': 'permission', 'action': 'manage', 'description': 'Manage permissions'},
        
        # Audit and monitoring
        {'permission_id': 70, 'resource': 'audit', 'action': 'read', 'description': 'View audit logs'},
        {'permission_id': 71, 'resource': 'metrics', 'action': 'read', 'description': 'View system metrics'},
        {'permission_id': 72, 'resource': 'sla', 'action': 'manage', 'description': 'Manage SLA configurations'},
        
        # Data management
        {'permission_id': 80, 'resource': 'data_dictionary', 'action': 'read', 'description': 'View data dictionary'},
        {'permission_id': 81, 'resource': 'data_dictionary', 'action': 'update', 'description': 'Update data dictionary'},
        {'permission_id': 82, 'resource': 'data_profiling', 'action': 'execute', 'description': 'Execute data profiling'},
        {'permission_id': 83, 'resource': 'document', 'action': 'upload', 'description': 'Upload documents'},
        {'permission_id': 84, 'resource': 'document', 'action': 'download', 'description': 'Download documents'},
    ]
    
    for perm in permission_data:
        perm['created_at'] = datetime.utcnow()
        perm['updated_at'] = datetime.utcnow()
    
    op.bulk_insert(permissions_table, permission_data)
    
    # 4. Insert Role-Permission mappings
    print("  🔗 Seeding Role-Permission mappings...")
    
    # Define role permissions based on system design
    role_permission_mappings = [
        # Tester permissions (role_id: 1)
        (1, 1), (1, 2), (1, 11), (1, 21), (1, 30), (1, 31), (1, 33), (1, 38), (1, 39), (1, 84),
        
        # Test Executive permissions (role_id: 2) - includes tester + management
        (2, 1), (2, 2), (2, 3), (2, 10), (2, 11), (2, 12), (2, 20), (2, 21), (2, 22), (2, 24),
        (2, 30), (2, 31), (2, 33), (2, 38), (2, 39), (2, 71), (2, 84),
        
        # Report Owner permissions (role_id: 3)
        (3, 1), (3, 2), (3, 11), (3, 21), (3, 32), (3, 34), (3, 40), (3, 84),
        
        # Report Owner Executive permissions (role_id: 4)
        (4, 1), (4, 3), (4, 11), (4, 21), (4, 32), (4, 34), (4, 40), (4, 70), (4, 71), (4, 84),
        
        # Data Owner permissions (role_id: 5)
        (5, 1), (5, 4), (5, 11), (5, 21), (5, 36), (5, 37), (5, 80), (5, 83), (5, 84),
        
        # Data Executive permissions (role_id: 6)
        (6, 1), (6, 4), (6, 5), (6, 11), (6, 21), (6, 35), (6, 36), (6, 80), (6, 81), (6, 82), (6, 83), (6, 84),
        
        # Admin permissions (role_id: 7) - all permissions
        *[(7, perm_id) for perm_id in range(1, 85)]
    ]
    
    role_permission_data = []
    for role_id, permission_id in role_permission_mappings:
        role_permission_data.append({
            'role_id': role_id,
            'permission_id': permission_id,
            'granted_at': datetime.utcnow()
        })
    
    op.bulk_insert(role_permissions_table, role_permission_data)
    
    # 5. Insert SLA Configurations
    print("  ⏰ Seeding SLA Configurations...")
    sla_data = [
        {
            'sla_id': 1,
            'sla_type': 'planning_phase',
            'duration_hours': 72,
            'warning_hours': 24,
            'business_hours_only': True,
            'exclude_weekends': True,
            'escalation_enabled': True,
            'is_active': True
        },
        {
            'sla_id': 2,
            'sla_type': 'scoping_phase',
            'duration_hours': 48,
            'warning_hours': 12,
            'business_hours_only': True,
            'exclude_weekends': True,
            'escalation_enabled': True,
            'is_active': True
        },
        {
            'sla_id': 3,
            'sla_type': 'sample_selection_phase',
            'duration_hours': 48,
            'warning_hours': 12,
            'business_hours_only': True,
            'exclude_weekends': True,
            'escalation_enabled': True,
            'is_active': True
        },
        {
            'sla_id': 4,
            'sla_type': 'data_owner_assignment',
            'duration_hours': 24,
            'warning_hours': 6,
            'business_hours_only': True,
            'exclude_weekends': True,
            'escalation_enabled': True,
            'is_active': True
        },
        {
            'sla_id': 5,
            'sla_type': 'request_info_phase',
            'duration_hours': 120,
            'warning_hours': 24,
            'business_hours_only': True,
            'exclude_weekends': True,
            'escalation_enabled': True,
            'is_active': True
        },
        {
            'sla_id': 6,
            'sla_type': 'test_execution_phase',
            'duration_hours': 168,
            'warning_hours': 48,
            'business_hours_only': True,
            'exclude_weekends': True,
            'escalation_enabled': True,
            'is_active': True
        },
        {
            'sla_id': 7,
            'sla_type': 'observation_phase',
            'duration_hours': 48,
            'warning_hours': 12,
            'business_hours_only': True,
            'exclude_weekends': True,
            'escalation_enabled': True,
            'is_active': True
        },
        {
            'sla_id': 8,
            'sla_type': 'approval_request',
            'duration_hours': 24,
            'warning_hours': 6,
            'business_hours_only': True,
            'exclude_weekends': True,
            'escalation_enabled': True,
            'is_active': True
        }
    ]
    
    for sla in sla_data:
        sla['created_at'] = datetime.utcnow()
        sla['updated_at'] = datetime.utcnow()
    
    op.bulk_insert(sla_configurations_table, sla_data)
    
    print("✅ Foundational seed data migration completed successfully!")


def downgrade() -> None:
    """Remove foundational seed data"""
    
    print("🧹 Removing foundational seed data...")
    
    # Delete in reverse order due to foreign key constraints
    op.execute("DELETE FROM rbac_role_permissions WHERE role_id IN (1,2,3,4,5,6,7)")
    op.execute("DELETE FROM rbac_permissions WHERE permission_id BETWEEN 1 AND 84")
    op.execute("DELETE FROM rbac_roles WHERE role_id IN (1,2,3,4,5,6,7)")
    op.execute("DELETE FROM universal_sla_configurations WHERE sla_id BETWEEN 1 AND 8")
    op.execute("DELETE FROM lobs WHERE lob_id BETWEEN 1 AND 8")
    
    print("✅ Foundational seed data removed")