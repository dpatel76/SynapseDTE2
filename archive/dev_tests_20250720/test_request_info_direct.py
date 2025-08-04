#!/usr/bin/env python3
"""
Direct test of Request Info phase functionality
"""

import asyncio
from datetime import datetime, timedelta
from app.application.use_cases.request_info import StartRequestInfoPhaseUseCase, GetRequestInfoPhaseStatusUseCase
from app.application.dtos.request_info import RequestInfoPhaseStartDTO
from app.models.workflow import WorkflowPhase
# from app.core.database import get_db_context  # Not needed
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/synapse_dt"

async def test_request_info_phase():
    """Test the request info phase start and status"""
    
    # Create database engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        print("Testing Request Info Phase...")
        print("=" * 50)
        
        # Test data
        cycle_id = 55
        report_id = 156
        user_id = 1  # Assuming user ID 1 exists
        
        # Check current status
        print(f"\n1. Checking current status for cycle {cycle_id}, report {report_id}...")
        status_use_case = GetRequestInfoPhaseStatusUseCase()
        
        try:
            status = await status_use_case.execute(cycle_id, report_id, db)
            print(f"   Phase Status: {status.phase_status}")
            print(f"   Total Test Cases: {status.total_test_cases}")
            print(f"   Submitted: {status.submitted_test_cases}")
            print(f"   Pending: {status.pending_test_cases}")
            print(f"   Data Owners Notified: {status.data_owners_notified}")
        except Exception as e:
            print(f"   Error getting status: {str(e)}")
        
        # Try to start the phase
        print(f"\n2. Starting Request Info phase...")
        start_use_case = StartRequestInfoPhaseUseCase()
        
        start_data = RequestInfoPhaseStartDTO(
            instructions="Please provide source evidence for all assigned attributes",
            submission_deadline=datetime.utcnow() + timedelta(days=14)
        )
        
        try:
            result = await start_use_case.execute(
                cycle_id, report_id, start_data, user_id, db
            )
            print(f"   Phase started successfully!")
            print(f"   Phase Status: {result.phase_status}")
            print(f"   Total Test Cases Created: {result.total_test_cases}")
            print(f"   Can Complete: {result.can_complete}")
            print(f"   Completion Requirements: {result.completion_requirements}")
        except ValueError as e:
            print(f"   Warning: {str(e)}")
        except Exception as e:
            print(f"   Error starting phase: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Check status again after starting
        print(f"\n3. Checking status after start...")
        try:
            status = await status_use_case.execute(cycle_id, report_id, db)
            print(f"   Phase Status: {status.phase_status}")
            print(f"   Total Test Cases: {status.total_test_cases}")
            print(f"   Total Attributes: {status.total_attributes}")
            print(f"   Total Samples: {status.total_samples}")
        except Exception as e:
            print(f"   Error getting status: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_request_info_phase())