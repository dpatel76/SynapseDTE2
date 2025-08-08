#!/usr/bin/env python3

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.request_info_service import RequestInfoService
from app.core.database import AsyncSessionLocal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

# Create synchronous session for the service
sync_engine = create_engine(settings.database_url)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def test_data_owner_portal():
    """Test the data provider portal data retrieval"""
    
    # Use synchronous session for the service
    db = SyncSessionLocal()
    try:
        service = RequestInfoService(db)
        
        # Test with known values from our database check
        phase_id = "0980a908-336c-4d4e-9032-e30f0a335e84"
        data_owner_id = 6
        
        print(f"Testing data provider portal for:")
        print(f"  Phase ID: {phase_id}")
        print(f"  Data Provider ID: {data_owner_id}")
        print()
        
        try:
            portal_data = service.get_data_owner_portal_data(phase_id, data_owner_id)
            
            print("✅ SUCCESS! Portal data retrieved:")
            print(f"  Cycle: {portal_data.cycle_name}")
            print(f"  Report: {portal_data.report_name}")
            print(f"  Total test cases: {portal_data.total_test_cases}")
            print(f"  Submitted: {portal_data.submitted_test_cases}")
            print(f"  Pending: {portal_data.pending_test_cases}")
            print(f"  Completion: {portal_data.completion_percentage:.1f}%")
            print(f"  Days remaining: {portal_data.days_remaining}")
            print(f"  Submission deadline: {portal_data.submission_deadline}")
            print()
            
            print("Test cases:")
            for i, tc in enumerate(portal_data.test_cases[:3], 1):
                print(f"  {i}. {tc.attribute_name} - Sample: {tc.sample_identifier} - Status: {tc.status}")
            
            if len(portal_data.test_cases) > 3:
                print(f"  ... and {len(portal_data.test_cases) - 3} more")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_data_owner_portal() 