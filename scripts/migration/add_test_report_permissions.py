"""
Add test report permissions to RBAC system
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.rbac import Permission

async def add_test_report_permissions():
    """Add test report permissions for various roles"""
    
    # Create async engine
    # Convert sync URL to async URL
    async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(async_url, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        try:
            # Define test report permissions
            test_report_permissions = [
                # Basic permissions
                {'resource': 'test_report', 'action': 'read', 'description': 'View test report content'},
                {'resource': 'test_report', 'action': 'write', 'description': 'Generate and configure test reports'},
                {'resource': 'test_report', 'action': 'approve', 'description': 'Approve test reports'},
                
                # Enhanced observation permissions
                {'resource': 'observation_enhanced', 'action': 'read', 'description': 'View enhanced observation management'},
                {'resource': 'observation_enhanced', 'action': 'write', 'description': 'Create and manage enhanced observations'},
                {'resource': 'observation_enhanced', 'action': 'rate', 'description': 'Rate observation severity'},
                {'resource': 'observation_enhanced', 'action': 'approve', 'description': 'Approve or reject observations'},
                {'resource': 'observation_enhanced', 'action': 'finalize', 'description': 'Finalize observation groups'},
            ]
            
            # Create permissions
            for perm_data in test_report_permissions:
                # Check if permission already exists
                result = await session.execute(
                    text("SELECT permission_id FROM permissions WHERE resource = :resource AND action = :action"),
                    {"resource": perm_data['resource'], "action": perm_data['action']}
                )
                existing = result.scalar()
                
                if not existing:
                    permission = Permission(
                        resource=perm_data['resource'],
                        action=perm_data['action'],
                        description=perm_data['description']
                    )
                    session.add(permission)
                    print(f"Created permission: {perm_data['resource']}.{perm_data['action']}")
                else:
                    print(f"Permission already exists: {perm_data['resource']}.{perm_data['action']}")
            
            await session.commit()
            
            # Now grant permissions to roles
            role_permissions = [
                # Tester can view and create observations, view reports
                ('Tester', 'test_report', 'read'),
                ('Tester', 'observation_enhanced', 'read'),
                ('Tester', 'observation_enhanced', 'write'),
                
                # Test Manager can do everything with test reports and observations
                ('Test Manager', 'test_report', 'read'),
                ('Test Manager', 'test_report', 'write'),
                ('Test Manager', 'test_report', 'approve'),
                ('Test Manager', 'observation_enhanced', 'read'),
                ('Test Manager', 'observation_enhanced', 'write'),
                ('Test Manager', 'observation_enhanced', 'rate'),
                ('Test Manager', 'observation_enhanced', 'approve'),
                ('Test Manager', 'observation_enhanced', 'finalize'),
                
                # Report Owner can view, rate, and approve observations
                ('Report Owner', 'test_report', 'read'),
                ('Report Owner', 'test_report', 'approve'),
                ('Report Owner', 'observation_enhanced', 'read'),
                ('Report Owner', 'observation_enhanced', 'rate'),
                ('Report Owner', 'observation_enhanced', 'approve'),
                
                # Report Owner Executive can view and approve
                ('Report Owner Executive', 'test_report', 'read'),
                ('Report Owner Executive', 'test_report', 'approve'),
                ('Report Owner Executive', 'observation_enhanced', 'read'),
                ('Report Owner Executive', 'observation_enhanced', 'approve'),
                
                # Data Executive can view and approve observations
                ('Data Executive', 'test_report', 'read'),
                ('Data Executive', 'observation_enhanced', 'read'),
                ('Data Executive', 'observation_enhanced', 'approve'),
                
                # Data Owner can view observations that affect them
                ('Data Owner', 'observation_enhanced', 'read'),
            ]
            
            # Grant permissions to roles
            for role_name, resource, action in role_permissions:
                # Get role ID
                result = await session.execute(
                    text("SELECT role_id FROM roles WHERE role_name = :role_name"),
                    {"role_name": role_name}
                )
                role_id = result.scalar()
                
                if role_id:
                    # Get permission ID
                    result = await session.execute(
                        text("SELECT permission_id FROM permissions WHERE resource = :resource AND action = :action"),
                        {"resource": resource, "action": action}
                    )
                    permission_id = result.scalar()
                    
                    if permission_id:
                        # Check if role permission already exists
                        result = await session.execute(
                            text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
                            {"role_id": role_id, "permission_id": permission_id}
                        )
                        exists = result.scalar()
                        
                        if not exists:
                            await session.execute(
                                text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)"),
                                {"role_id": role_id, "permission_id": permission_id}
                            )
                            print(f"Granted {resource}.{action} to {role_name}")
                        else:
                            print(f"Role {role_name} already has {resource}.{action}")
                    else:
                        print(f"Permission not found: {resource}.{action}")
                else:
                    print(f"Role not found: {role_name}")
            
            await session.commit()
            print("\nTest report permissions added successfully!")
            
        except Exception as e:
            print(f"Error adding permissions: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(add_test_report_permissions())