#!/usr/bin/env python3
"""
Create all test users with proper passwords
"""

import asyncio
from app.core.database import get_async_db
from app.core.security import get_password_hash
from app.models import User
from sqlalchemy import select

async def create_test_users():
    """Create test users for all roles"""
    
    test_users = [
        ('Test', 'Manager', 'testmgr@synapse.com', 'Test Executive', 1),
        ('Test', 'Tester', 'tester@synapse.com', 'Tester', 1),
        ('Report', 'Owner', 'owner@synapse.com', 'Report Owner', 1),
        ('Executive', 'Owner', 'exec@synapse.com', 'Report Owner Executive', 1),
        ('Data', 'Provider', 'provider@synapse.com', 'Data Owner', 1),
        ('Chief', 'DataOfficer', 'cdo@synapse.com', 'Data Executive', None)
    ]
    
    async with get_async_db() as db:
        for first, last, email, role, lob_id in test_users:
            # Check if user exists
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                user = User(
                    first_name=first,
                    last_name=last,
                    email=email,
                    role=role,
                    lob_id=lob_id,
                    hashed_password=get_password_hash('TestUser123!'),
                    is_active=True
                )
                db.add(user)
                print(f'✅ Created user: {email} ({role})')
            else:
                # Update password if user exists
                existing_user.hashed_password = get_password_hash('TestUser123!')
                print(f'✅ Updated password for: {email}')
        
        await db.commit()
        print('✅ All test users created/updated successfully!')

if __name__ == "__main__":
    asyncio.run(create_test_users())