#!/usr/bin/env python3
"""
Check RBAC configuration and status
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
import asyncio
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.user import User


async def check_config():
    """Check RBAC configuration settings"""
    print("="*60)
    print("RBAC CONFIGURATION CHECK")
    print("="*60)
    
    print(f"\n1. Feature Flag Status:")
    print(f"   USE_RBAC: {settings.use_rbac}")
    print(f"   RBAC_FALLBACK_TO_ROLES: {settings.rbac_fallback_to_roles}")
    print(f"   RBAC_CACHE_TTL: {settings.rbac_cache_ttl} seconds")
    
    if not settings.use_rbac:
        print("\n⚠️  WARNING: RBAC is currently DISABLED!")
        print("   To enable RBAC, set USE_RBAC=true in your environment")
        print("   Example: export USE_RBAC=true")


async def check_database():
    """Check RBAC database status"""
    print(f"\n2. Database Status:")
    
    async for db in get_db():
        try:
            # Count permissions
            result = await db.execute(select(func.count(Permission.permission_id)))
            permission_count = result.scalar()
            print(f"   Permissions: {permission_count}")
            
            # Count roles
            result = await db.execute(select(func.count(Role.role_id)))
            role_count = result.scalar()
            print(f"   Roles: {role_count}")
            
            # Count role-permission assignments
            result = await db.execute(select(func.count()).select_from(RolePermission))
            role_perm_count = result.scalar()
            print(f"   Role-Permission assignments: {role_perm_count}")
            
            # Count users with RBAC roles
            result = await db.execute(select(func.count(func.distinct(UserRole.user_id))))
            users_with_roles = result.scalar()
            print(f"   Users with RBAC roles: {users_with_roles}")
            
            # List roles
            result = await db.execute(select(Role).where(Role.is_active == True))
            roles = result.scalars().all()
            print(f"\n3. Active Roles:")
            for role in roles:
                # Count permissions for role
                perm_result = await db.execute(
                    select(func.count()).select_from(RolePermission)
                    .where(RolePermission.role_id == role.role_id)
                )
                perm_count = perm_result.scalar()
                print(f"   - {role.role_name}: {perm_count} permissions")
            
        except Exception as e:
            print(f"   ❌ Error checking database: {str(e)}")
        finally:
            await db.close()
            break


async def check_test_users():
    """Check if test users exist"""
    print(f"\n4. Test User Status:")
    
    test_emails = [
        "admin@synapsedt.com",
        "john.manager@synapsedt.com",
        "jane.tester@synapsedt.com",
        "bob.owner@synapsedt.com",
        "alice.executive@synapsedt.com",
        "charlie.provider@synapsedt.com",
        "diana.cdo@synapsedt.com"
    ]
    
    async for db in get_db():
        try:
            for email in test_emails:
                result = await db.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()
                if user:
                    # Check if user has RBAC roles
                    role_result = await db.execute(
                        select(UserRole, Role)
                        .join(Role, UserRole.role_id == Role.role_id)
                        .where(UserRole.user_id == user.user_id)
                    )
                    user_roles = role_result.all()
                    
                    rbac_roles = [role.role_name for _, role in user_roles]
                    rbac_info = f", RBAC: {', '.join(rbac_roles)}" if rbac_roles else ", RBAC: None"
                    
                    print(f"   ✅ {email} - Legacy: {user.role}{rbac_info}")
                else:
                    print(f"   ❌ {email} - NOT FOUND")
                    
        except Exception as e:
            print(f"   ❌ Error checking users: {str(e)}")
        finally:
            await db.close()
            break


def print_instructions():
    """Print setup instructions"""
    print(f"\n5. Setup Instructions:")
    
    if not settings.use_rbac:
        print(f"\n   To enable RBAC:")
        print(f"   1. Set environment variable: export USE_RBAC=true")
        print(f"   2. Restart the backend: uvicorn app.main:app --reload")
    
    print(f"\n   To populate RBAC data:")
    print(f"   1. Run: python scripts/populate_rbac_resources.py")
    print(f"   2. Run: python scripts/seed_rbac_permissions.py")
    print(f"   3. Run: python scripts/create_test_users.py")
    
    print(f"\n   To test RBAC:")
    print(f"   1. Run: python scripts/test_rbac_integration.py")
    print(f"   2. Run: python scripts/test_rbac_endpoints.py")


async def main():
    """Main function"""
    await check_config()
    await check_database()
    await check_test_users()
    print_instructions()
    
    print(f"\n{'='*60}")
    if settings.use_rbac:
        print("✅ RBAC is ENABLED and ready for testing!")
    else:
        print("⚠️  RBAC is DISABLED - enable it to test the new permission system")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())