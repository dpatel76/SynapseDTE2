import asyncio
import sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check_data():
    async with AsyncSessionLocal() as db:
        # Check the test tester user specifically
        result = await db.execute(text('SELECT user_id, email, role, hashed_password FROM users WHERE email = :email'), {'email': 'test.tester@example.com'})
        test_tester = result.fetchone()
        print(f'Test tester user: {test_tester}')
        
        # Check cycle_reports table
        result = await db.execute(text('SELECT cycle_id, report_id, tester_id FROM cycle_reports WHERE cycle_id = 1 AND report_id = 12'))
        cycle_report = result.fetchone()
        print(f'CycleReport(1,12): {cycle_report}')
        
        if cycle_report:
            tester_id = cycle_report[2]
            # Get the assigned tester details
            result = await db.execute(text('SELECT user_id, email, role FROM users WHERE user_id = :tester_id'), {'tester_id': tester_id})
            assigned_tester = result.fetchone()
            print(f'Assigned tester (user_id={tester_id}): {assigned_tester}')
        
        # Check admin user for comparison
        result = await db.execute(text('SELECT user_id, email, role FROM users WHERE email = :email'), {'email': 'admin@example.com'})
        admin_user = result.fetchone()
        print(f'Admin user: {admin_user}')
        
        # Check all users to see what's available
        result = await db.execute(text('SELECT user_id, email, role FROM users ORDER BY user_id'))
        all_users = result.fetchall()
        print(f'All users in database:')
        for user in all_users:
            print(f'  - user_id={user[0]}, email={user[1]}, role={user[2]}')
        
        # Check if any cycle_reports exist
        result = await db.execute(text('SELECT cycle_id, report_id, tester_id FROM cycle_reports LIMIT 5'))
        all_reports = result.fetchall()
        print(f'Available cycle_reports: {all_reports}')

if __name__ == "__main__":
    asyncio.run(check_data()) 