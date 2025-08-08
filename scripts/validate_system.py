#!/usr/bin/env python
"""
System validation script - checks all components are working
"""

import requests
import psycopg2
import logging
import sys
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8001"
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "synapse_dt",
    "user": "synapse_user",
    "password": "synapse_password"
}

TEST_CREDENTIALS = {
    "email": "tester@example.com",
    "password": "password123"
}


class SystemValidator:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        
    def check_api_health(self):
        """Check if API is responding"""
        logger.info("Checking API health...")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ API is healthy")
                self.checks_passed += 1
                return True
            else:
                logger.error(f"❌ API returned status {response.status_code}")
                self.checks_failed += 1
                return False
        except Exception as e:
            logger.error(f"❌ API check failed: {str(e)}")
            self.checks_failed += 1
            return False
    
    def check_database_connection(self):
        """Check database connectivity"""
        logger.info("Checking database connection...")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result and result[0] == 1:
                logger.info("✅ Database connection successful")
                self.checks_passed += 1
                return True
            else:
                logger.error("❌ Database query failed")
                self.checks_failed += 1
                return False
        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            self.checks_failed += 1
            return False
    
    def check_authentication(self):
        """Check authentication works"""
        logger.info("Checking authentication...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=TEST_CREDENTIALS,
                timeout=5
            )
            
            if response.status_code == 200 and "access_token" in response.json():
                logger.info("✅ Authentication successful")
                self.checks_passed += 1
                return response.json()["access_token"]
            else:
                logger.error(f"❌ Authentication failed: {response.status_code}")
                self.checks_failed += 1
                return None
        except Exception as e:
            logger.error(f"❌ Authentication check failed: {str(e)}")
            self.checks_failed += 1
            return None
    
    def check_required_tables(self):
        """Check if all required tables exist"""
        logger.info("Checking required tables...")
        
        required_tables = [
            "workflow_phases",
            "workflow_activities",
            "cycle_report_planning_attributes",
            "cycle_report_scoping_attributes",
            "cycle_report_scoping_versions",
            "cycle_report_data_profiling_rules",
            "cycle_report_sample_selection_samples",
            "cycle_report_sample_selection_versions",
            "cycle_report_data_owner_lob_mapping",
            "cycle_report_data_owner_lob_mapping_versions",
            "cycle_report_test_cases",
            "test_case_evidence",
            "cycle_report_observations"
        ]
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            missing_tables = []
            for table in required_tables:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table,))
                exists = cur.fetchone()[0]
                
                if not exists:
                    missing_tables.append(table)
            
            cur.close()
            conn.close()
            
            if missing_tables:
                logger.error(f"❌ Missing tables: {', '.join(missing_tables)}")
                self.checks_failed += 1
                return False
            else:
                logger.info(f"✅ All {len(required_tables)} required tables exist")
                self.checks_passed += 1
                return True
                
        except Exception as e:
            logger.error(f"❌ Table check failed: {str(e)}")
            self.checks_failed += 1
            return False
    
    def check_phase_activities(self, token):
        """Check if workflow activities are accessible"""
        logger.info("Checking workflow activities...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/activity-management/phases/Planning/activities",
                headers=headers,
                params={"cycle_id": 2, "report_id": 3},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if "activities" in data and len(data["activities"]) > 0:
                    logger.info(f"✅ Found {len(data['activities'])} activities for Planning phase")
                    self.checks_passed += 1
                    return True
                else:
                    logger.error("❌ No activities found")
                    self.checks_failed += 1
                    return False
            else:
                logger.error(f"❌ Failed to get activities: {response.status_code}")
                self.checks_failed += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Activity check failed: {str(e)}")
            self.checks_failed += 1
            return False
    
    def check_phase_data(self):
        """Check if test data exists"""
        logger.info("Checking phase data...")
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Check for workflow phases
            cur.execute("""
                SELECT COUNT(*) FROM workflow_phases 
                WHERE cycle_id = 2 AND report_id = 3
            """)
            phase_count = cur.fetchone()[0]
            
            # Check for activities
            cur.execute("""
                SELECT COUNT(*) FROM workflow_activities 
                WHERE cycle_id = 2 AND report_id = 3
            """)
            activity_count = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            if phase_count > 0 and activity_count > 0:
                logger.info(f"✅ Found {phase_count} phases and {activity_count} activities")
                self.checks_passed += 1
                return True
            else:
                logger.error(f"❌ Insufficient test data: {phase_count} phases, {activity_count} activities")
                self.checks_failed += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Data check failed: {str(e)}")
            self.checks_failed += 1
            return False
    
    def run_validation(self):
        """Run all validation checks"""
        logger.info("="*60)
        logger.info("SYSTEM VALIDATION")
        logger.info("="*60)
        
        # Run checks
        self.check_api_health()
        self.check_database_connection()
        token = self.check_authentication()
        self.check_required_tables()
        self.check_phase_data()
        
        if token:
            self.check_phase_activities(token)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Checks Passed: {self.checks_passed}")
        logger.info(f"Checks Failed: {self.checks_failed}")
        
        if self.checks_failed == 0:
            logger.info("\n🎉 SYSTEM VALIDATION PASSED!")
            logger.info("All components are working correctly.")
            return True
        else:
            logger.info(f"\n⚠️ SYSTEM VALIDATION FAILED!")
            logger.info(f"{self.checks_failed} check(s) failed. Please investigate.")
            return False


def main():
    validator = SystemValidator()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())