#!/usr/bin/env python3
"""
Create a test cycle in Planning status to test the Start Cycle functionality
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.test_cycle import TestCycle
from app.models.user import User
from datetime import datetime, timedelta

async def create_planning_cycle():
    """Create a test cycle in Planning status"""
    
    async for db in get_db():
        try:
            # Find test manager user
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.email == "test.manager@example.com")
            )
            test_manager = result.scalar_one_or_none()
            
            if not test_manager:
                print("Test manager user not found!")
                return
            
            # Create a new test cycle in Planning status
            cycle = TestCycle(
                cycle_name="Q1 2025 Testing Cycle",
                description="First quarter testing cycle for regulatory reports",
                test_manager_id=test_manager.user_id,
                start_date=datetime.now().date(),
                end_date=(datetime.now() + timedelta(days=90)).date(),
                status="Planning"
            )
            
            db.add(cycle)
            await db.commit()
            await db.refresh(cycle)
            
            print(f"✅ Created test cycle '{cycle.cycle_name}' with ID {cycle.cycle_id}")
            print(f"   Status: {cycle.status}")
            print(f"   Start Date: {cycle.start_date}")
            print(f"   End Date: {cycle.end_date}")
            print("\nNext steps:")
            print("1. Log in as test.manager@example.com")
            print("2. Go to Test Cycles page")
            print("3. Click the menu (three dots) for this cycle")
            print("4. Select 'Add Reports' to add reports to the cycle")
            print("5. Select 'Start Cycle' to change status from Planning to Active")
            
        except Exception as e:
            print(f"Error creating test cycle: {str(e)}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(create_planning_cycle())