#!/usr/bin/env python
"""Debug version of e2e test with detailed phase tracking"""

import asyncio
import logging
from datetime import datetime, date
import random
from sqlalchemy.ext.asyncio import AsyncSession
from app.temporal.client import get_temporal_client
from app.core.database import get_db
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.lob import LOB

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def setup_test_data(cycle_id: int, report_id: int):
    """Create necessary test data in the database"""
    async for db in get_db():
        try:
            # Check if test user exists
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.user_id == 1))
            user = result.scalar_one_or_none()
            
            if not user:
                logger.info("Creating test user...")
                user = User(
                    user_id=1,
                    username="test_user",
                    email="test@example.com",
                    first_name="Test",
                    last_name="User",
                    role="Tester",
                    is_active=True
                )
                db.add(user)
                await db.commit()
            
            # Check/create LOB
            result = await db.execute(select(LOB).where(LOB.lob_id == 1))
            lob = result.scalar_one_or_none()
            
            if not lob:
                logger.info("Creating test LOB...")
                lob = LOB(
                    lob_id=1,
                    lob_name="Consumer Banking"
                )
                db.add(lob)
                await db.commit()
            
            # Create test cycle
            logger.info(f"Creating test cycle {cycle_id}...")
            cycle = TestCycle(
                cycle_id=cycle_id,
                cycle_name=f"E2E Debug Test Cycle {cycle_id}",
                description="Debug e2e test cycle",
                test_manager_id=1,
                start_date=date.today(),
                status="Active"
            )
            db.add(cycle)
            
            # Create report
            logger.info(f"Creating report {report_id}...")
            report = Report(
                report_id=report_id,
                report_name=f"E2E Debug Test Report {report_id}",
                regulation="Basel III",
                lob_id=1,
                frequency="Quarterly",
                report_owner_id=1,
                description="Test report for debug e2e testing"
            )
            db.add(report)
            
            # Create cycle-report association
            logger.info("Creating cycle-report association...")
            cycle_report = CycleReport(
                cycle_id=cycle_id,
                report_id=report_id,
                tester_id=1
            )
            db.add(cycle_report)
            
            await db.commit()
            logger.info("✅ Test data created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create test data: {str(e)}")
            await db.rollback()
            raise


async def test_phase_by_phase():
    """Test workflow phase by phase with detailed debugging"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Generate unique IDs
        cycle_id = random.randint(20000, 29999)
        report_id = random.randint(200000, 299999)
        user_id = 1
        
        logger.info(f"\n=== Starting Debug E2E Test ===")
        logger.info(f"Cycle ID: {cycle_id}")
        logger.info(f"Report ID: {report_id}")
        
        # Setup test data
        await setup_test_data(cycle_id, report_id)
        
        # Start the workflow
        workflow_id = await client.start_testing_workflow(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=user_id
        )
        
        logger.info(f"✅ Workflow started: {workflow_id}")
        
        # Get workflow handle
        handle = client.client.get_workflow_handle(workflow_id)
        
        # Helper function to check and log status
        async def check_status(phase_name: str):
            status = await handle.query("get_current_status")
            logger.info(f"\n--- {phase_name} Status ---")
            logger.info(f"Current phase: {status.get('current_phase')}")
            logger.info(f"Awaiting action: {status.get('awaiting_action')}")
            logger.info(f"Workflow status: {status.get('workflow_status')}")
            logger.info(f"Completed phases: {list(status.get('phase_results', {}).keys())}")
            return status
        
        # Phase 1: Planning
        logger.info("\n=== PHASE 1: PLANNING ===")
        await asyncio.sleep(2)
        
        status = await check_status("Initial Planning")
        
        # Step 1: Upload documents
        if status.get("awaiting_action") == "upload_planning_documents":
            logger.info("Uploading planning documents...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_planning_documents",
                signal_data={
                    "input_type": "planning_documents",
                    "data": {
                        "documents": [
                            {"name": "test.pdf", "type": "regulatory", "size": 1024}
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            await asyncio.sleep(2)
            await check_status("After document upload")
        
        # Step 2: Create attributes
        status = await handle.query("get_current_status")
        if status.get("awaiting_action") == "create_planning_attributes":
            logger.info("Creating planning attributes...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_planning_attributes",
                signal_data={
                    "input_type": "planning_attributes",
                    "data": {
                        "manual_attributes": [
                            {
                                "attribute_name": "Test Attribute",
                                "data_type": "String",
                                "description": "Test",
                                "cde_flag": True,
                                "historical_issues_flag": False
                            }
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            await asyncio.sleep(3)
            await check_status("After attributes creation")
        
        # Wait for planning to complete
        logger.info("Waiting for planning phase to complete...")
        await asyncio.sleep(5)
        status = await check_status("Planning completion")
        
        # Check if we moved to Scoping
        if status.get("current_phase") != "Scoping":
            logger.warning(f"Expected Scoping phase but got: {status.get('current_phase')}")
            
        # Get final workflow status
        logger.info("\n=== CHECKING WORKFLOW EXECUTION STATUS ===")
        try:
            workflow_desc = await handle.describe()
            logger.info(f"Workflow execution status: {workflow_desc.status}")
            logger.info(f"Workflow start time: {workflow_desc.start_time}")
            if workflow_desc.close_time:
                logger.info(f"Workflow close time: {workflow_desc.close_time}")
        except Exception as e:
            logger.error(f"Failed to describe workflow: {e}")
        
        return {
            "workflow_id": workflow_id,
            "final_status": status
        }
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main test function"""
    logger.info("=== Temporal Debug E2E Test ===")
    
    try:
        result = await test_phase_by_phase()
        logger.info(f"\n✅ Debug Test Completed!")
        logger.info(f"Final status: {result['final_status']}")
        
    except Exception as e:
        logger.error(f"\n❌ Debug Test Failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)