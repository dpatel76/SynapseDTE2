#!/usr/bin/env python3

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User
from app.models.request_info import RequestInfoPhase, TestCase
from app.models.testing import DataProviderAssignment
from app.core.database import AsyncSessionLocal
from sqlalchemy import select

async def check_data_owner_assignments():
    async with AsyncSessionLocal() as db:
        try:
            print("=== USERS IN SYSTEM ===")
            result = await db.execute(select(User))
            users = result.scalars().all()
            data_owners = []
            for user in users:
                print(f"ID: {user.user_id}, Email: {user.email}, Role: {user.role}, Name: {user.full_name}")
                if user.role == 'Data Owner':
                    data_owners.append(user)
            
            print(f"\n=== DATA PROVIDERS ({len(data_owners)}) ===")
            for dp in data_owners:
                print(f"- {dp.full_name} ({dp.email}) - ID: {dp.user_id}")
            
            print("\n=== REQUEST INFO PHASES ===")
            result = await db.execute(select(RequestInfoPhase))
            phases = result.scalars().all()
            for phase in phases:
                print(f"Phase ID: {phase.phase_id}, Cycle: {phase.cycle_id}, Report: {phase.report_id}, Status: {phase.phase_status}")
                
                # Check test cases for this phase
                result = await db.execute(
                    select(TestCase).where(TestCase.phase_id == phase.phase_id)
                )
                test_cases = result.scalars().all()
                print(f"  Test cases: {len(test_cases)}")
                
                for tc in test_cases[:3]:  # Show first 3
                    print(f"    - {tc.test_case_id}: {tc.attribute_name} (Sample: {tc.sample_identifier}) - Data Provider: {tc.data_owner_id}")
            
            print("\n=== DATA PROVIDER ASSIGNMENTS ===")
            result = await db.execute(select(DataProviderAssignment))
            assignments = result.scalars().all()
            print(f"Total assignments: {len(assignments)}")
            for assignment in assignments:
                print(f"Cycle: {assignment.cycle_id}, Report: {assignment.report_id}, Attribute: {assignment.attribute_id}, Data Provider: {assignment.data_owner_id}")
        
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(check_data_owner_assignments()) 