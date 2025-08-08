#!/usr/bin/env python
"""
Test all phase initializations
"""

import asyncio
import logging
from sqlalchemy import select, and_, text
from datetime import datetime
import requests
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8001"
CYCLE_ID = 2
REPORT_ID = 3

# Test credentials
TEST_CREDENTIALS = {
    "email": "tester@example.com",
    "password": "password123"
}


class PhaseInitializationTester:
    def __init__(self):
        self.token = None
        self.headers = None
        
    def login(self):
        """Login and get authentication token"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=TEST_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            logger.info("✅ Login successful")
            return True
        else:
            logger.error(f"❌ Login failed: {response.status_code}")
            return False
    
    async def reset_all_phases(self):
        """Reset all phases to initial state"""
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                # Reset all workflow activities
                await db.execute(text("""
                    UPDATE workflow_activities 
                    SET status = 'NOT_STARTED', started_at = NULL, started_by = NULL,
                        completed_at = NULL, completed_by = NULL,
                        can_start = CASE WHEN activity_order = 1 THEN true ELSE false END,
                        can_complete = false
                    WHERE cycle_id = :cycle_id AND report_id = :report_id
                """), {"cycle_id": CYCLE_ID, "report_id": REPORT_ID})
                
                # Reset all workflow phases
                await db.execute(text("""
                    UPDATE workflow_phases
                    SET status = 'Not Started', state = 'Not Started',
                        actual_start_date = NULL, started_by = NULL, progress_percentage = 0
                    WHERE cycle_id = :cycle_id AND report_id = :report_id
                """), {"cycle_id": CYCLE_ID, "report_id": REPORT_ID})
                
                await db.commit()
                logger.info("✅ All phases reset")
                
            except Exception as e:
                logger.error(f"❌ Error resetting phases: {str(e)}")
                await db.rollback()
    
    def start_phase(self, phase_name):
        """Start a phase via API"""
        activity_code = f"{phase_name.replace(' ', '_')}_1"
        
        response = requests.post(
            f"{BASE_URL}/api/v1/activity-management/activities/{activity_code}/start",
            headers=self.headers,
            json={
                "cycle_id": CYCLE_ID,
                "report_id": REPORT_ID,
                "phase_name": phase_name
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            logger.error(f"Failed to start {phase_name}: {response.status_code}")
            if response.text:
                logger.error(f"Error: {response.text}")
            return None
    
    async def check_phase_initialization(self, phase_name):
        """Check if a phase was properly initialized"""
        from app.core.database import AsyncSessionLocal
        from app.models.workflow import WorkflowPhase
        
        async with AsyncSessionLocal() as db:
            checks = {}
            
            try:
                # Get phase
                phase_query = select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == CYCLE_ID,
                        WorkflowPhase.report_id == REPORT_ID,
                        WorkflowPhase.phase_name == phase_name
                    )
                )
                phase_result = await db.execute(phase_query)
                phase = phase_result.scalar_one_or_none()
                
                if not phase:
                    checks['phase_exists'] = False
                    return checks
                
                checks['phase_exists'] = True
                checks['phase_status'] = phase.status
                checks['phase_state'] = phase.state
                
                # Phase-specific checks
                if phase_name == "Scoping":
                    # Check for scoping attributes
                    result = await db.execute(text("""
                        SELECT COUNT(*) FROM cycle_report_scoping_attributes sa
                        JOIN cycle_report_scoping_versions sv ON sa.version_id = sv.version_id
                        WHERE sv.phase_id = :phase_id
                    """), {"phase_id": phase.phase_id})
                    count = result.scalar()
                    checks['scoping_attributes_imported'] = count > 0
                    checks['scoping_attribute_count'] = count
                    
                elif phase_name == "Data Provider ID":
                    # Check for LOB attribute mappings
                    result = await db.execute(text("""
                        SELECT COUNT(*) FROM cycle_report_data_owner_lob_mapping
                        WHERE phase_id = :phase_id
                    """), {"phase_id": phase.phase_id})
                    count = result.scalar()
                    checks['lob_mappings_created'] = count > 0
                    checks['lob_mapping_count'] = count
                    
                elif phase_name == "Request Info":
                    # Check for test cases
                    result = await db.execute(text("""
                        SELECT COUNT(*) FROM cycle_report_test_cases
                        WHERE phase_id = :phase_id
                    """), {"phase_id": phase.phase_id})
                    count = result.scalar()
                    checks['test_cases_created'] = count > 0
                    checks['test_case_count'] = count
                    
            except Exception as e:
                logger.error(f"Error checking {phase_name}: {str(e)}")
                checks['error'] = str(e)
            
            return checks
    
    async def test_phase_initialization(self, phase_name):
        """Test a phase initialization"""
        logger.info(f"\nTesting {phase_name} initialization...")
        
        # Start the phase
        result = self.start_phase(phase_name)
        if not result:
            return False
        
        # Wait for initialization
        time.sleep(2)
        
        # Check initialization
        checks = await self.check_phase_initialization(phase_name)
        
        # Log results
        for key, value in checks.items():
            if isinstance(value, bool):
                symbol = "✅" if value else "❌"
                logger.info(f"  {symbol} {key}: {value}")
            else:
                logger.info(f"  ℹ️ {key}: {value}")
        
        # Determine success based on phase
        if phase_name == "Scoping":
            return checks.get('scoping_attributes_imported', False)
        elif phase_name == "Data Provider ID":
            return checks.get('lob_mappings_created', False)
        elif phase_name == "Request Info":
            return checks.get('test_cases_created', False)
        else:
            return checks.get('phase_exists', False)
    
    async def run_all_tests(self):
        """Run all initialization tests"""
        logger.info("="*60)
        logger.info("PHASE INITIALIZATION TESTING")
        logger.info("="*60)
        
        if not self.login():
            logger.error("Failed to login")
            return False
        
        # Reset all phases
        await self.reset_all_phases()
        time.sleep(1)
        
        # Test phases that have special initialization
        phases_to_test = [
            "Scoping",           # Should import planning attributes
            "Data Provider ID",  # Should create LOB attribute mappings
            "Request Info"       # Should generate test cases
        ]
        
        results = {}
        for phase in phases_to_test:
            success = await self.test_phase_initialization(phase)
            results[phase] = success
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        
        for phase, success in results.items():
            symbol = "✅" if success else "❌"
            logger.info(f"{symbol} {phase}: {'PASSED' if success else 'FAILED'}")
        
        all_passed = all(results.values())
        if all_passed:
            logger.info("\n🎉 ALL INITIALIZATION TESTS PASSED!")
        else:
            failed_count = sum(1 for s in results.values() if not s)
            logger.info(f"\n⚠️ {failed_count} INITIALIZATION(S) FAILED")
        
        return all_passed


async def main():
    tester = PhaseInitializationTester()
    success = await tester.run_all_tests()
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)