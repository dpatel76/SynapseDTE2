#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select
from app.models.rbac import Permission, Role, RolePermission
from app.models.user import User
import aiohttp
import json

async def test_admin_permissions_api():
    DATABASE_URL = 'postgresql+asyncpg://dineshpatel@localhost:5432/synapse_dt'
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get admin user
        admin_result = await session.execute(
            select(User).where(User.email == 'admin@synapsedt.com')
        )
        admin_user = admin_result.scalar_one_or_none()
        
        if not admin_user:
            print('Admin user not found')
            return
            
        print(f'Found admin user: {admin_user.email} (ID: {admin_user.user_id})')
        print(f'Admin user role: {admin_user.role}')
        
        # Test API call to get user permissions (what the frontend would call)
        async with aiohttp.ClientSession() as client_session:
            try:
                # First login to get a token - using JSON format
                login_data = {
                    'email': 'admin@synapsedt.com',
                    'password': 'password123'
                }
                
                async with client_session.post(
                    'http://localhost:8000/api/v1/auth/login',
                    json=login_data,  # Changed to json instead of data
                    headers={'Content-Type': 'application/json'}
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        print(f'Login failed with status {resp.status}: {error_text}')
                        return
                    
                    login_result = await resp.json()
                    token = login_result['access_token']
                    print(f'Got auth token: {token[:20]}...')
                
                # Now try to get user permissions
                headers = {'Authorization': f'Bearer {token}'}
                
                async with client_session.get(
                    f'http://localhost:8000/api/v1/admin/rbac/users/{admin_user.user_id}/permissions',
                    headers=headers
                ) as resp:
                    print(f'Permission API response status: {resp.status}')
                    
                    if resp.status == 200:
                        perms_data = await resp.json()
                        print('API returned permissions:')
                        print(f'  All permissions: {len(perms_data["data"]["all_permissions"])} permissions')
                        print(f'  Sample permissions: {perms_data["data"]["all_permissions"][:10]}')
                        
                        # Check specifically for reports permissions
                        reports_perms = [p for p in perms_data["data"]["all_permissions"] if p.startswith('reports:')]
                        print(f'  Reports permissions: {reports_perms}')
                        
                        # Check if reports:create is there
                        if 'reports:create' in perms_data["data"]["all_permissions"]:
                            print('✅ Admin has reports:create permission!')
                        else:
                            print('❌ Admin missing reports:create permission!')
                        
                    else:
                        error_text = await resp.text()
                        print(f'API error: {error_text}')
                        
                        # Check if it's using fallback permissions
                        print('\nChecking fallback permissions based on role...')
                        role = admin_user.role
                        print(f'User role: {role}')
                        
                        # This matches the fallback logic in PermissionContext.tsx
                        role_permissions = {
                            'Admin': ['*:*'],
                            'ADMIN': ['*:*']
                        }
                        
                        fallback_perms = role_permissions.get(role, [])
                        print(f'Fallback permissions for {role}: {fallback_perms}')
                        
                        if '*:*' in fallback_perms:
                            print('✅ Admin has wildcard permissions - should have reports:create via fallback')
                        
            except Exception as e:
                print(f'Error testing API: {e}')

if __name__ == "__main__":
    asyncio.run(test_admin_permissions_api()) 