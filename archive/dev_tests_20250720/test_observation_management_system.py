#!/usr/bin/env python3
"""
End-to-end test script for the unified observation management system
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.observation_management_service import create_observation_management_service
from app.services.observation_detection_service import create_observation_detection_service
from app.services.observation_detection_runner import create_observation_detection_runner
from app.models.observation_management_unified import ObservationGroup, Observation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObservationManagementSystemTest:
    """Test the unified observation management system end-to-end"""
    
    def __init__(self):
        # Create database session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()
        
        # Create services
        self.management_service = create_observation_management_service(self.db)
        self.detection_service = create_observation_detection_service(self.db)
        self.detection_runner = create_observation_detection_runner(self.db)
        
        # Test data
        self.test_phase_id = 1
        self.test_cycle_id = 1
        self.test_report_id = 1
        self.test_attribute_id = 1
        self.test_lob_id = 1
        self.test_user_id = 1
        
        # Test results
        self.test_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': []
        }
    
    async def run_all_tests(self):
        """Run all tests"""
        try:
            logger.info("Starting observation management system tests...")
            
            # Test 1: Database connectivity
            await self.test_database_connectivity()
            
            # Test 2: Create observation group
            group = await self.test_create_observation_group()
            
            # Test 3: Get observation groups
            await self.test_get_observation_groups()
            
            # Test 4: Submit for review
            await self.test_submit_for_review(group)
            
            # Test 5: Tester review
            await self.test_tester_review(group)
            
            # Test 6: Submit for approval
            await self.test_submit_for_approval(group)
            
            # Test 7: Report owner approval
            await self.test_report_owner_approval(group)
            
            # Test 8: Start resolution
            await self.test_start_resolution(group)
            
            # Test 9: Complete resolution
            await self.test_complete_resolution(group)
            
            # Test 10: Statistics
            await self.test_get_statistics()
            
            # Test 11: Detection service (if test data exists)
            await self.test_detection_service()
            
            # Print results
            self.print_test_results()
            
            return self.test_results['tests_failed'] == 0
            
        except Exception as e:
            logger.error(f"Test suite failed: {str(e)}")
            self.test_results['errors'].append(str(e))
            return False
        finally:
            self.db.close()
    
    async def test_database_connectivity(self):
        """Test database connectivity"""
        try:
            logger.info("Testing database connectivity...")
            
            # Test basic query
            result = self.db.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1
            
            # Test table existence
            tables = self.db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('cycle_report_observation_groups', 'cycle_report_observations')
            """)).fetchall()
            
            assert len(tables) == 2, f"Expected 2 tables, found {len(tables)}"
            
            self.record_test_result("Database connectivity", True)
            
        except Exception as e:
            self.record_test_result("Database connectivity", False, str(e))
    
    async def test_create_observation_group(self):
        """Test creating observation group"""
        try:
            logger.info("Testing create observation group...")
            
            group = await self.management_service.create_observation_group(
                phase_id=self.test_phase_id,
                cycle_id=self.test_cycle_id,
                report_id=self.test_report_id,
                attribute_id=self.test_attribute_id,
                lob_id=self.test_lob_id,
                group_name="Test Observation Group",
                issue_summary="Test issue summary for automated testing",
                severity_level="medium",
                issue_type="data_quality",
                created_by=self.test_user_id,
                group_description="Test group description",
                impact_description="Test impact description",
                proposed_resolution="Test proposed resolution"
            )
            
            assert group is not None
            assert group['group_name'] == "Test Observation Group"
            assert group['severity_level'] == "medium"
            assert group['issue_type'] == "data_quality"
            assert group['status'] == "draft"
            
            self.record_test_result("Create observation group", True)
            return group
            
        except Exception as e:
            self.record_test_result("Create observation group", False, str(e))
            return None
    
    async def test_get_observation_groups(self):
        """Test getting observation groups"""
        try:
            logger.info("Testing get observation groups...")
            
            result = await self.management_service.get_observation_groups(
                phase_id=self.test_phase_id,
                cycle_id=self.test_cycle_id,
                report_id=self.test_report_id,
                page=1,
                page_size=10
            )
            
            assert result is not None
            assert 'groups' in result
            assert 'pagination' in result
            assert len(result['groups']) > 0
            
            self.record_test_result("Get observation groups", True)
            
        except Exception as e:
            self.record_test_result("Get observation groups", False, str(e))
    
    async def test_submit_for_review(self, group):
        """Test submitting group for review"""
        if not group:
            self.record_test_result("Submit for review", False, "No group available")
            return
        
        try:
            logger.info("Testing submit for review...")
            
            result = await self.management_service.submit_for_tester_review(
                group_id=group['id'],
                submitted_by=self.test_user_id
            )
            
            assert result is not None
            assert result['status'] == "pending_tester_review"
            
            self.record_test_result("Submit for review", True)
            
        except Exception as e:
            self.record_test_result("Submit for review", False, str(e))
    
    async def test_tester_review(self, group):
        """Test tester review"""
        if not group:
            self.record_test_result("Tester review", False, "No group available")
            return
        
        try:
            logger.info("Testing tester review...")
            
            result = await self.management_service.tester_review_observation_group(
                group_id=group['id'],
                reviewer_id=self.test_user_id,
                review_decision="approved",
                review_notes="Test review notes",
                review_score=85
            )
            
            assert result is not None
            assert result['status'] == "tester_approved"
            assert result['tester_review_status'] == "approved"
            assert result['tester_review_score'] == 85
            
            self.record_test_result("Tester review", True)
            
        except Exception as e:
            self.record_test_result("Tester review", False, str(e))
    
    async def test_submit_for_approval(self, group):
        """Test submitting group for approval"""
        if not group:
            self.record_test_result("Submit for approval", False, "No group available")
            return
        
        try:
            logger.info("Testing submit for approval...")
            
            result = await self.management_service.submit_for_report_owner_approval(
                group_id=group['id'],
                submitted_by=self.test_user_id
            )
            
            assert result is not None
            assert result['status'] == "pending_report_owner_approval"
            
            self.record_test_result("Submit for approval", True)
            
        except Exception as e:
            self.record_test_result("Submit for approval", False, str(e))
    
    async def test_report_owner_approval(self, group):
        """Test report owner approval"""
        if not group:
            self.record_test_result("Report owner approval", False, "No group available")
            return
        
        try:
            logger.info("Testing report owner approval...")
            
            result = await self.management_service.report_owner_approve_observation_group(
                group_id=group['id'],
                approver_id=self.test_user_id,
                approval_decision="approved",
                approval_notes="Test approval notes"
            )
            
            assert result is not None
            assert result['status'] == "report_owner_approved"
            assert result['report_owner_approval_status'] == "approved"
            
            self.record_test_result("Report owner approval", True)
            
        except Exception as e:
            self.record_test_result("Report owner approval", False, str(e))
    
    async def test_start_resolution(self, group):
        """Test starting resolution"""
        if not group:
            self.record_test_result("Start resolution", False, "No group available")
            return
        
        try:
            logger.info("Testing start resolution...")
            
            result = await self.management_service.start_resolution(
                group_id=group['id'],
                resolution_owner_id=self.test_user_id,
                resolution_approach="Test resolution approach",
                resolution_timeline="2 weeks"
            )
            
            assert result is not None
            assert result['resolution_status'] == "in_progress"
            assert result['resolution_approach'] == "Test resolution approach"
            
            self.record_test_result("Start resolution", True)
            
        except Exception as e:
            self.record_test_result("Start resolution", False, str(e))
    
    async def test_complete_resolution(self, group):
        """Test completing resolution"""
        if not group:
            self.record_test_result("Complete resolution", False, "No group available")
            return
        
        try:
            logger.info("Testing complete resolution...")
            
            result = await self.management_service.complete_resolution(
                group_id=group['id'],
                resolver_id=self.test_user_id,
                resolution_notes="Test resolution completed successfully"
            )
            
            assert result is not None
            assert result['resolution_status'] == "completed"
            assert result['status'] == "resolved"
            
            self.record_test_result("Complete resolution", True)
            
        except Exception as e:
            self.record_test_result("Complete resolution", False, str(e))
    
    async def test_get_statistics(self):
        """Test getting statistics"""
        try:
            logger.info("Testing get statistics...")
            
            result = await self.management_service.get_observation_statistics(
                phase_id=self.test_phase_id,
                cycle_id=self.test_cycle_id,
                report_id=self.test_report_id
            )
            
            assert result is not None
            assert 'total_groups' in result
            assert 'total_observations' in result
            assert 'status_distribution' in result
            assert 'severity_distribution' in result
            assert 'issue_type_distribution' in result
            
            self.record_test_result("Get statistics", True)
            
        except Exception as e:
            self.record_test_result("Get statistics", False, str(e))
    
    async def test_detection_service(self):
        """Test detection service (simplified)"""
        try:
            logger.info("Testing detection service...")
            
            # Test getting detection statistics
            result = await self.detection_service.get_detection_statistics(
                phase_id=self.test_phase_id,
                cycle_id=self.test_cycle_id,
                report_id=self.test_report_id
            )
            
            assert result is not None
            assert 'total_failed_executions' in result
            assert 'failed_with_observations' in result
            assert 'detection_coverage' in result
            
            # Note: We don't run actual detection as it requires test execution data
            self.record_test_result("Detection service", True)
            
        except Exception as e:
            self.record_test_result("Detection service", False, str(e))
    
    def record_test_result(self, test_name: str, passed: bool, error: str = None):
        """Record test result"""
        self.test_results['tests_run'] += 1
        
        if passed:
            self.test_results['tests_passed'] += 1
            logger.info(f"✅ {test_name} - PASSED")
        else:
            self.test_results['tests_failed'] += 1
            error_msg = f"❌ {test_name} - FAILED"
            if error:
                error_msg += f": {error}"
            logger.error(error_msg)
            self.test_results['errors'].append(f"{test_name}: {error}")
    
    def print_test_results(self):
        """Print test results summary"""
        logger.info("\n" + "="*50)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*50)
        logger.info(f"Tests run: {self.test_results['tests_run']}")
        logger.info(f"Tests passed: {self.test_results['tests_passed']}")
        logger.info(f"Tests failed: {self.test_results['tests_failed']}")
        
        if self.test_results['tests_failed'] > 0:
            logger.info("\nFailed tests:")
            for error in self.test_results['errors']:
                logger.info(f"  - {error}")
        
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100
        logger.info(f"\nSuccess rate: {success_rate:.1f}%")
        
        if self.test_results['tests_failed'] == 0:
            logger.info("🎉 ALL TESTS PASSED! 🎉")
        else:
            logger.info("❌ Some tests failed. Please review the errors above.")
        
        logger.info("="*50)


async def main():
    """Main test function"""
    try:
        logger.info("Starting observation management system end-to-end tests...")
        
        test_suite = ObservationManagementSystemTest()
        success = await test_suite.run_all_tests()
        
        if success:
            logger.info("All tests passed successfully!")
            return 0
        else:
            logger.error("Some tests failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))