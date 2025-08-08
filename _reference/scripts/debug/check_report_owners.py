#!/usr/bin/env python3
"""Check report owners in the database"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db
from sqlalchemy import text


async def check_report_owners():
    """Check report owners"""
    async for db in get_db():
        try:
            # Get all Report Owners
            result = await db.execute(text("""
                SELECT 
                    u.user_id,
                    u.username,
                    u.email,
                    u.role,
                    COUNT(r.report_id) as owned_reports
                FROM users u
                LEFT JOIN reports r ON r.report_owner_id = u.user_id
                WHERE u.role IN ('Report Owner', 'Report Owner Executive')
                GROUP BY u.user_id, u.username, u.email, u.role
                ORDER BY u.user_id
            """))
            
            report_owners = result.fetchall()
            print("Report Owners in the system:")
            print("="*80)
            for ro in report_owners:
                print(f"ID: {ro[0]}, Username: {ro[1]}, Email: {ro[2]}, Role: {ro[3]}, Reports: {ro[4]}")
            
            # Check specific report 156
            print("\n\nReport 156 ownership:")
            print("="*80)
            result = await db.execute(text("""
                SELECT 
                    r.report_id,
                    r.report_name,
                    r.report_owner_id,
                    u.username,
                    u.email
                FROM reports r
                LEFT JOIN users u ON r.report_owner_id = u.user_id
                WHERE r.report_id = 156
            """))
            
            row = result.first()
            if row:
                print(f"Report: {row[1]} (ID: {row[0]})")
                print(f"Owner ID: {row[2]}")
                print(f"Owner Username: {row[3]}")
                print(f"Owner Email: {row[4]}")
            
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(check_report_owners())