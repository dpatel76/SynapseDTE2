#!/usr/bin/env python3
"""
Check if RBAC tables exist in database
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import get_db


async def check_tables():
    async for db in get_db():
        try:
            # Get all tables
            result = await db.execute(
                text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """)
            )
            
            all_tables = [row[0] for row in result]
            
            print("\nAll tables in database:")
            print("=" * 50)
            for table in all_tables:
                print(f"  - {table}")
            
            # Check for RBAC tables
            rbac_tables = [
                "permissions",
                "resources", 
                "roles",
                "role_permissions",
                "user_roles",
                "user_permissions",
                "resource_permissions",
                "role_hierarchy",
                "permission_audit_log"
            ]
            
            print("\nRBAC Tables Check:")
            print("=" * 50)
            for table in rbac_tables:
                exists = table in all_tables
                status = "✅" if exists else "❌"
                print(f"  {status} {table}")
                
                if exists:
                    # Get row count
                    count_result = await db.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    )
                    count = count_result.scalar()
                    print(f"     Rows: {count}")
            
            # Check alembic version
            print("\nAlembic Version:")
            print("=" * 50)
            version_result = await db.execute(
                text("SELECT version_num FROM alembic_version")
            )
            version = version_result.scalar()
            print(f"  Current version: {version}")
            
            break
            
        except Exception as e:
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(check_tables())