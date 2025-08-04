#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.request_info import TestCase
from sqlalchemy.orm import selectinload
from sqlalchemy import select

async def test_api_logic():
    """Test the exact logic from the API endpoint"""
    
    # Get database session
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            # Build the query using SQLAlchemy 2.0 syntax (same as API)
            query = select(TestCase).options(
                selectinload(TestCase.data_owner),
                selectinload(TestCase.assigned_by_user),
                selectinload(TestCase.document_submissions),
                selectinload(TestCase.cycle),
                selectinload(TestCase.report)
            ).where(TestCase.data_owner_id == 6).limit(1)
            
            result = await db.execute(query)
            test_cases = result.scalars().all()
            
            print(f"Found {len(test_cases)} test cases")
            
            if test_cases:
                tc = test_cases[0]
                print(f"Test Case ID: {tc.test_case_id}")
                print(f"Cycle ID: {tc.cycle_id}")
                print(f"Report ID: {tc.report_id}")
                
                # Check relationships
                print(f"Cycle object: {tc.cycle}")
                print(f"Report object: {tc.report}")
                
                if tc.cycle:
                    print(f"Cycle name: {tc.cycle.cycle_name}")
                else:
                    print("Cycle relationship is None")
                    
                if tc.report:
                    print(f"Report name: {tc.report.report_name}")
                else:
                    print("Report relationship is None")
                
                # Build response like API does
                cycle_name = tc.cycle.cycle_name if tc.cycle else f"Cycle {tc.cycle_id}"
                report_name = tc.report.report_name if tc.report else f"Report {tc.report_id}"
                
                print(f"Final cycle_name: {cycle_name}")
                print(f"Final report_name: {report_name}")
                
                # Build the response dict like the API
                test_case_detail = {
                    "test_case_id": tc.test_case_id,
                    "cycle_id": tc.cycle_id,
                    "cycle_name": cycle_name,
                    "report_id": tc.report_id,
                    "report_name": report_name,
                    "attribute_name": tc.attribute_name,
                    "sample_identifier": tc.sample_identifier,
                    "status": tc.status
                }
                
                print(f"Response dict: {test_case_detail}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_logic()) 