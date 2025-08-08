#!/usr/bin/env python3

import sys
import os
import asyncio

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def test_connection():
    """Test database connection and check for tables"""
    try:
        print("Testing database connection...")
        
        session = AsyncSessionLocal()
        
        # Check if we can connect and what database we're using
        result = await session.execute(text("SELECT current_database(), current_user"))
        db_info = result.fetchone()
        print(f"Connected to database: {db_info[0]} as user: {db_info[1]}")
        
        # Check for existing tables
        result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"Found {len(tables)} tables:")
        for table in tables[:10]:  # Show first 10
            print(f"  - {table}")
        if len(tables) > 10:
            print(f"  ... and {len(tables) - 10} more")
        
        # Check specifically for RBAC tables
        rbac_tables = ['permissions', 'roles', 'role_permissions', 'user_roles']
        existing_rbac = [table for table in rbac_tables if table in tables]
        missing_rbac = [table for table in rbac_tables if table not in tables]
        
        print(f"\nRBAC Tables:")
        print(f"  Existing: {existing_rbac}")
        print(f"  Missing: {missing_rbac}")
        
        # Check for users
        if 'users' in tables:
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"\nUsers table has {user_count} users")
            
            result = await session.execute(text("SELECT email, role FROM users LIMIT 5"))
            users = result.fetchall()
            print("Sample users:")
            for email, role in users:
                print(f"  - {email}: {role}")
        
        await session.close()
        print("\n✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection()) 