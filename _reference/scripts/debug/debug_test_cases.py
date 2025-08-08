#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.request_info import TestCase
from app.models.user import User

async def test_data_owner_test_cases():
    """Test the data provider test cases query"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get the data provider user (ID 6)
            user_result = await db.execute(select(User).where(User.user_id == 6))
            user = user_result.scalar_one_or_none()
            
            if not user:
                print("Data provider user not found")
                return
                
            print(f"Testing for user: {user.first_name} {user.last_name} (ID: {user.user_id})")
            
            # Build the same query as the API
            query = select(TestCase).options(
                selectinload(TestCase.data_owner),
                selectinload(TestCase.assigned_by_user),
                selectinload(TestCase.document_submissions),
                selectinload(TestCase.cycle),
                selectinload(TestCase.report)
            ).where(TestCase.data_owner_id == user.user_id)
            
            result = await db.execute(query)
            test_cases = result.scalars().all()
            
            print(f"\nFound {len(test_cases)} test cases")
            
            if test_cases:
                tc = test_cases[0]
                print(f"\nFirst test case details:")
                print(f"  test_case_id: {tc.test_case_id}")
                print(f"  cycle_id: {tc.cycle_id}")
                print(f"  report_id: {tc.report_id}")
                print(f"  attribute_name: {tc.attribute_name}")
                print(f"  sample_identifier: {tc.sample_identifier}")
                print(f"  status: {tc.status}")
                
                # Check cycle relationship
                if tc.cycle:
                    print(f"  cycle.cycle_name: {tc.cycle.cycle_name}")
                else:
                    print(f"  cycle: None (relationship not loaded)")
                    
                # Check report relationship
                if tc.report:
                    print(f"  report.report_name: {tc.report.report_name}")
                else:
                    print(f"  report: None (relationship not loaded)")
                    
                # Check primary key attributes
                print(f"  primary_key_attributes: {tc.primary_key_attributes}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_data_owner_test_cases()) 