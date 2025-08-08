#!/usr/bin/env python
"""
Comprehensive test script for all phases
"""

import requests
import json
import time
import psycopg2
import logging
from datetime import datetime

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

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "synapse_dt",
    "user": "synapse_user",
    "password": "synapse_password"
}


class PhaseTestRunner:
    def __init__(self):
        self.token = None
        self.headers = None
        self.test_results = {}
        
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
    
    def reset_phase(self, phase_name):
        """Reset a phase to initial state"""
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        try:
            # Reset activities
            cur.execute("""
                UPDATE workflow_activities 
                SET status = 'NOT_STARTED', started_at = NULL, started_by = NULL,
                    completed_at = NULL, completed_by = NULL,
                    can_start = CASE WHEN activity_order = 1 THEN true ELSE false END,
                    can_complete = false
                WHERE cycle_id = %s AND report_id = %s AND phase_name = %s
            """, (CYCLE_ID, REPORT_ID, phase_name))
            
            # Reset phase
            cur.execute("""
                UPDATE workflow_phases
                SET status = 'Not Started', state = 'Not Started',
                    actual_start_date = NULL, started_by = NULL, progress_percentage = 0
                WHERE cycle_id = %s AND report_id = %s AND phase_name = %s
            """, (CYCLE_ID, REPORT_ID, phase_name))
            
            conn.commit()
            logger.info(f"  Reset {phase_name} phase")
            
        except Exception as e:
            logger.error(f"  Error resetting {phase_name}: {str(e)}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    def start_phase_activity(self, phase_name):
        """Start the first activity of a phase"""
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
            logger.info(f"  ✅ Started {phase_name}: {result.get('message', 'Success')}")
            return result
        else:
            logger.error(f"  ❌ Failed to start {phase_name}: {response.status_code}")
            if response.text:
                logger.error(f"     Error: {response.text}")
            return None
    
    def check_phase_initialization(self, phase_name):
        """Check if phase was properly initialized"""
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        checks = {}
        
        try:
            # Get phase_id
            cur.execute("""
                SELECT phase_id, status, state FROM workflow_phases 
                WHERE cycle_id = %s AND report_id = %s AND phase_name = %s
            """, (CYCLE_ID, REPORT_ID, phase_name))
            result = cur.fetchone()
            
            if result:
                phase_id, status, state = result
                checks['phase_exists'] = True
                checks['phase_status'] = status
                checks['phase_state'] = state
                
                # Phase-specific checks
                if phase_name == "Data Provider ID":
                    # Check for LOB attribute mappings
                    cur.execute("""
                        SELECT COUNT(*) FROM cycle_report_data_owner_lob_mapping
                        WHERE phase_id = %s
                    """, (phase_id,))
                    mapping_count = cur.fetchone()[0]
                    checks['lob_mappings_created'] = mapping_count > 0
                    checks['lob_mapping_count'] = mapping_count
                    
                elif phase_name == "Request Info":
                    # Check for test cases
                    cur.execute("""
                        SELECT COUNT(*) FROM cycle_report_test_cases
                        WHERE phase_id = %s
                    """, (phase_id,))
                    test_case_count = cur.fetchone()[0]
                    checks['test_cases_created'] = test_case_count > 0
                    checks['test_case_count'] = test_case_count
                    
                elif phase_name == "Scoping":
                    # Check for scoping attributes
                    cur.execute("""
                        SELECT COUNT(*) FROM cycle_report_scoping_attributes sa
                        JOIN cycle_report_scoping_versions sv ON sa.version_id = sv.version_id
                        WHERE sv.phase_id = %s
                    """, (phase_id,))
                    attr_count = cur.fetchone()[0]
                    checks['scoping_attributes_imported'] = attr_count > 0
                    checks['scoping_attribute_count'] = attr_count
            else:
                checks['phase_exists'] = False
                
        except Exception as e:
            logger.error(f"  Error checking {phase_name}: {str(e)}")
            checks['error'] = str(e)
        finally:
            cur.close()
            conn.close()
            
        return checks
    
    def test_phase(self, phase_name):
        """Test a single phase"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing {phase_name} Phase")
        logger.info(f"{'='*60}")
        
        # Reset phase
        self.reset_phase(phase_name)
        time.sleep(1)
        
        # Start phase
        start_result = self.start_phase_activity(phase_name)
        time.sleep(2)
        
        # Check initialization
        checks = self.check_phase_initialization(phase_name)
        
        # Log results
        logger.info(f"\n  Initialization Checks:")
        for key, value in checks.items():
            if isinstance(value, bool):
                symbol = "✅" if value else "❌"
                logger.info(f"    {symbol} {key}: {value}")
            else:
                logger.info(f"    ℹ️  {key}: {value}")
        
        # Determine success
        success = checks.get('phase_exists', False)
        
        # Phase-specific success criteria
        if phase_name == "Data Provider ID":
            success = success and checks.get('lob_mappings_created', False)
        elif phase_name == "Request Info":
            success = success and checks.get('test_cases_created', False)
        elif phase_name == "Scoping":
            success = success and checks.get('scoping_attributes_imported', False)
        
        self.test_results[phase_name] = {
            'success': success,
            'checks': checks,
            'start_result': start_result
        }
        
        return success
    
    def run_all_tests(self):
        """Run tests for all phases"""
        logger.info("\n" + "="*60)
        logger.info("COMPREHENSIVE PHASE TESTING")
        logger.info("="*60)
        
        if not self.login():
            logger.error("Failed to login, aborting tests")
            return False
        
        # List of phases to test in order
        phases = [
            "Planning",
            "Scoping",
            "Data Profiling",
            "Sample Selection",
            "Data Provider ID",
            "Request Info",
            "Test Execution",
            "Observations",
            "Finalize Test Report"
        ]
        
        # Test each phase
        for phase in phases:
            try:
                self.test_phase(phase)
            except Exception as e:
                logger.error(f"Error testing {phase}: {str(e)}")
                self.test_results[phase] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        
        success_count = 0
        failed_count = 0
        
        for phase, result in self.test_results.items():
            if result['success']:
                logger.info(f"✅ {phase}: PASSED")
                success_count += 1
            else:
                logger.info(f"❌ {phase}: FAILED")
                if 'error' in result:
                    logger.info(f"   Error: {result['error']}")
                failed_count += 1
        
        logger.info(f"\nTotal: {len(self.test_results)} phases tested")
        logger.info(f"Passed: {success_count}")
        logger.info(f"Failed: {failed_count}")
        
        overall_success = failed_count == 0
        
        if overall_success:
            logger.info("\n🎉 ALL TESTS PASSED!")
        else:
            logger.info(f"\n⚠️  {failed_count} PHASE(S) FAILED")
        
        return overall_success


if __name__ == "__main__":
    runner = PhaseTestRunner()
    success = runner.run_all_tests()
    exit(0 if success else 1)