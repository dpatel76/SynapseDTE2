#!/usr/bin/env python3
"""Check all users in the database"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db
from sqlalchemy import text


async def check_users():
    """Check all users"""
    async for db in get_db():
        try:
            # Get all users
            result = await db.execute(text("""
                SELECT 
                    user_id,
                    username,
                    email,
                    role,
                    is_active
                FROM users
                ORDER BY role, user_id
            """))
            
            users = result.fetchall()
            print(f"Total users in system: {len(users)}")
            print("="*100)
            print(f"{'ID':<5} {'Username':<20} {'Email':<35} {'Role':<25} {'Active':<8}")
            print("="*100)
            
            for user in users:
                print(f"{user[0]:<5} {user[1]:<20} {user[2]:<35} {user[3]:<25} {user[4]}")
            
            print("\n\nReport Owners specifically:")
            print("="*100)
            for user in users:
                if 'Report Owner' in user[3]:
                    print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}")
            
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(check_users())