#!/usr/bin/env python3
"""
Create test users for RBAC testing using SQLAlchemy
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.auth import get_password_hash, UserRoles
from app.models.user import User
from app.models.lob import LOB
from app.models.rbac import Role, UserRole
from app.core.logging import get_logger

logger = get_logger(__name__)

# Test users to create
TEST_USERS = [
    {
        "email": "admin@synapsedt.com",
        "password": "admin123",
        "first_name": "Admin",
        "last_name": "User",
        "role": UserRoles.ADMIN,
        "lob_id": None,
        "rbac_role": "Administrator"
    },
    {
        "email": "john.manager@synapsedt.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Manager",
        "role": UserRoles.TEST_EXECUTIVE,
        "lob_id": 1,
        "rbac_role": "Test Executive"
    },
    {
        "email": "jane.tester@synapsedt.com",
        "password": "password123",
        "first_name": "Jane",
        "last_name": "Tester",
        "role": UserRoles.TESTER,
        "lob_id": 1,
        "rbac_role": "Tester"
    },
    {
        "email": "bob.owner@synapsedt.com",
        "password": "password123",
        "first_name": "Bob",
        "last_name": "Owner",
        "role": UserRoles.REPORT_OWNER,
        "lob_id": 1,
        "rbac_role": "Report Owner"
    },
    {
        "email": "alice.executive@synapsedt.com",
        "password": "password123",
        "first_name": "Alice",
        "last_name": "Executive",
        "role": UserRoles.REPORT_OWNER_EXECUTIVE,
        "lob_id": 1,
        "rbac_role": "Report Owner Executive"
    },
    {
        "email": "charlie.provider@synapsedt.com",
        "password": "password123",
        "first_name": "Charlie",
        "last_name": "Provider",
        "role": UserRoles.DATA_OWNER,
        "lob_id": 1,
        "rbac_role": "Data Owner"
    },
    {
        "email": "diana.cdo@synapsedt.com",
        "password": "password123",
        "first_name": "Diana",
        "last_name": "Data Executive",
        "role": UserRoles.DATA_EXECUTIVE,
        "lob_id": None,
        "rbac_role": "Chief Data Officer"
    }
]


async def ensure_lob_exists(db: AsyncSession, lob_id: int) -> bool:
    """Ensure LOB exists in database"""
    if lob_id is None:
        return True
        
    result = await db.execute(
        select(LOB).where(LOB.lob_id == lob_id)
    )
    lob = result.scalar_one_or_none()
    
    if not lob:
        # Create default LOB
        default_lob = LOB(
            lob_id=lob_id,
            lob_name="Default LOB",
            lob_code="DEFAULT",
            is_active=True
        )
        db.add(default_lob)
        await db.commit()
        print(f"✅ Created default LOB with ID {lob_id}")
        return True
    
    return True


async def get_rbac_role(db: AsyncSession, role_name: str) -> Role:
    """Get RBAC role by name"""
    result = await db.execute(
        select(Role).where(Role.role_name == role_name)
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise ValueError(f"RBAC role '{role_name}' not found. Run seed_rbac_permissions.py first.")
    
    return role


async def create_user(db: AsyncSession, user_data: dict) -> bool:
    """Create a single user"""
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"ℹ️  User already exists: {user_data['email']}")
            
            # Check if user has RBAC role
            if user_data.get("rbac_role"):
                rbac_role = await get_rbac_role(db, user_data["rbac_role"])
                
                # Check if user already has this role
                role_result = await db.execute(
                    select(UserRole).where(
                        UserRole.user_id == existing_user.user_id,
                        UserRole.role_id == rbac_role.role_id
                    )
                )
                existing_role = role_result.scalar_one_or_none()
                
                if not existing_role:
                    # Assign RBAC role
                    user_role = UserRole(
                        user_id=existing_user.user_id,
                        role_id=rbac_role.role_id
                    )
                    db.add(user_role)
                    await db.commit()
                    print(f"   ✅ Assigned RBAC role: {user_data['rbac_role']}")
                else:
                    print(f"   ℹ️  Already has RBAC role: {user_data['rbac_role']}")
            
            return False
        
        # Ensure LOB exists if needed
        if user_data.get("lob_id"):
            await ensure_lob_exists(db, user_data["lob_id"])
        
        # Create user
        new_user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role=user_data["role"],
            lob_id=user_data.get("lob_id"),
            is_active=True
        )
        db.add(new_user)
        await db.flush()  # Get the user ID
        
        # Assign RBAC role if specified
        if user_data.get("rbac_role"):
            rbac_role = await get_rbac_role(db, user_data["rbac_role"])
            user_role = UserRole(
                user_id=new_user.user_id,
                role_id=rbac_role.role_id
            )
            db.add(user_role)
        
        await db.commit()
        print(f"✅ Created user: {user_data['email']} ({user_data['role']}) with RBAC role: {user_data.get('rbac_role', 'None')}")
        return True
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Error creating user {user_data['email']}: {str(e)}")
        return False


async def main():
    """Main function"""
    print("Creating RBAC Test Users")
    print("=" * 60)
    
    created_count = 0
    
    async for db in get_db():
        try:
            for user_data in TEST_USERS:
                if await create_user(db, user_data):
                    created_count += 1
            
            print(f"\n{'='*60}")
            print(f"Summary: Created {created_count} new users")
            print(f"Total test users: {len(TEST_USERS)}")
            
            if created_count == 0:
                print("\nℹ️  All test users already exist.")
            
            print("\nLogin credentials for testing:")
            print("-" * 40)
            for user in TEST_USERS:
                print(f"{user['email']:<30} : {user['password']}")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            await db.rollback()
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(main())