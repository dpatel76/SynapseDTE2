#!/usr/bin/env python
"""End-to-end test with proper database setup"""

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
    level=logging.INFO,
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
                cycle_name=f"E2E Test Cycle {cycle_id}",
                description="End-to-end test cycle",
                test_manager_id=1,
                start_date=date.today(),
                status="Active"
            )
            db.add(cycle)
            
            # Create report
            logger.info(f"Creating report {report_id}...")
            report = Report(
                report_id=report_id,
                report_name=f"E2E Test Report {report_id}",
                regulation="Basel III",
                lob_id=1,
                frequency="Quarterly",
                report_owner_id=1,
                description="Test report for E2E testing"
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


async def test_full_workflow():
    """Test the complete workflow from planning to observations"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Generate unique IDs
        cycle_id = random.randint(10000, 99999)
        report_id = random.randint(100000, 999999)
        user_id = 1
        
        logger.info(f"\n=== Starting E2E Workflow Test ===")
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
        
        # Get workflow handle for queries and signals
        handle = client.client.get_workflow_handle(workflow_id)
        
        # Test Phase 1: Planning
        logger.info("\n--- Phase 1: Planning ---")
        
        # Wait for workflow to be ready
        await asyncio.sleep(2)
        
        # Check initial status
        status = await handle.query("get_current_status")
        logger.info(f"Initial status: {status}")
        
        # Step 1.1: Upload planning documents
        if status.get("awaiting_action") == "upload_planning_documents":
            logger.info("Sending planning documents...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_planning_documents",
                signal_data={
                    "input_type": "planning_documents",
                    "data": {
                        "documents": [
                            {"name": "regulatory_spec.pdf", "type": "regulatory", "size": 1024000},
                            {"name": "cde_list.xlsx", "type": "cde_list", "size": 512000},
                            {"name": "historical_issues.pdf", "type": "historical", "size": 256000}
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Planning documents uploaded")
            await asyncio.sleep(3)
        
        # Step 1.2: Create planning attributes
        status = await handle.query("get_current_status")
        logger.info(f"Status after documents: {status}")
        
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
                                "attribute_name": "Customer ID",
                                "attribute_type": "string",
                                "description": "Unique customer identifier",
                                "cde_flag": True,
                                "historical_issues_flag": False
                            },
                            {
                                "attribute_name": "Account Balance",
                                "attribute_type": "decimal",
                                "description": "Current account balance",
                                "cde_flag": True,
                                "historical_issues_flag": True
                            },
                            {
                                "attribute_name": "Transaction Date",
                                "attribute_type": "date",
                                "description": "Date of transaction",
                                "cde_flag": False,
                                "historical_issues_flag": False
                            }
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Planning attributes created")
            await asyncio.sleep(3)
        
        # Step 1.3: Review and complete planning
        status = await handle.query("get_current_status")
        logger.info(f"Status after attributes: {status}")
        
        if status.get("awaiting_action") == "review_planning_checklist":
            logger.info("Reviewing planning checklist...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_planning_review",
                signal_data={
                    "input_type": "planning_review",
                    "data": {
                        "checklist": {
                            "can_complete_phase": True,
                            "all_required_complete": True
                        },
                        "notes": "All planning requirements met"
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Planning phase completed")
            await asyncio.sleep(3)
        
        # Check final status
        final_status = await handle.query("get_current_status")
        logger.info(f"\n=== Final Workflow Status ===")
        logger.info(f"Current Phase: {final_status.get('current_phase')}")
        logger.info(f"Awaiting Action: {final_status.get('awaiting_action')}")
        logger.info(f"Completed Phases: {list(final_status.get('phase_results', {}).keys())}")
        
        # Get workflow execution status
        workflow_status = await client.get_workflow_status(workflow_id)
        logger.info(f"\nWorkflow Execution Status: {workflow_status['status']}")
        
        return {
            "workflow_id": workflow_id,
            "final_status": final_status,
            "execution_status": workflow_status
        }
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main test function"""
    logger.info("=== Temporal E2E Workflow Test with Setup ===")
    logger.info("Testing complete workflow with proper data setup\n")
    
    try:
        result = await test_full_workflow()
        
        logger.info(f"\n✅ E2E Test Completed Successfully!")
        logger.info(f"Workflow ID: {result['workflow_id']}")
        logger.info(f"Final Phase: {result['final_status']['current_phase']}")
        logger.info(f"Check Temporal UI at http://localhost:8088 for details")
        
    except Exception as e:
        logger.error(f"\n❌ E2E Test Failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)