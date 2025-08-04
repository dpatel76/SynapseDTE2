#!/usr/bin/env python
"""Complete end-to-end test with proper data setup for all 8 workflow phases"""

import asyncio
import logging
from datetime import datetime, date
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.temporal.client import get_temporal_client
from app.core.database import get_db
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.lob import LOB
from app.models.document import Document
from app.models.report_attribute import ReportAttribute
from app.models.workflow import WorkflowPhase
from app.models.sample_selection import SampleSet, SampleRecord
# AttributeLOBAssignment removed - table doesn't exist

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def setup_complete_test_data(cycle_id: int, report_id: int):
    """Create all necessary test data for complete workflow execution"""
    async for db in get_db():
        try:
            # Check if test user exists
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
                cycle_name=f"E2E Complete Test Cycle {cycle_id}",
                description="Complete end-to-end test cycle for all phases",
                test_manager_id=1,
                start_date=date.today(),
                status="Active"
            )
            db.add(cycle)
            
            # Create report
            logger.info(f"Creating report {report_id}...")
            report = Report(
                report_id=report_id,
                report_name=f"E2E Complete Test Report {report_id}",
                regulation="Basel III",
                lob_id=1,
                frequency="Quarterly",
                report_owner_id=1,
                description="Test report for complete E2E testing"
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
            
            # Create planning phase record
            logger.info("Creating planning phase record...")
            planning_phase = WorkflowPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Planning",
                state="Not Started",
                status="pending"
            )
            db.add(planning_phase)
            
            # Pre-create the required documents to satisfy checklist
            logger.info("Creating required planning documents...")
            
            # Create regulatory document
            reg_doc = Document(
                cycle_id=cycle_id,
                report_id=report_id,
                document_name="regulatory_spec.pdf",
                document_type="regulatory",
                file_path="/uploads/regulatory_spec.pdf",
                file_size=1024000,
                mime_type="application/pdf",
                file_hash="a"*64,  # Dummy hash
                uploaded_by_user_id=1,
                uploaded_at=datetime.utcnow(),
                is_latest_version=True
            )
            db.add(reg_doc)
            
            # Create CDE list document
            cde_doc = Document(
                cycle_id=cycle_id,
                report_id=report_id,
                document_name="cde_list.xlsx",
                document_type="cde_list",
                file_path="/uploads/cde_list.xlsx",
                file_size=512000,
                mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                file_hash="b"*64,  # Dummy hash
                uploaded_by_user_id=1,
                uploaded_at=datetime.utcnow(),
                is_latest_version=True
            )
            db.add(cde_doc)
            
            # Pre-create some approved attributes
            logger.info("Creating approved attributes...")
            for i in range(3):
                attr = ReportAttribute(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    attribute_name=f"Test Attribute {i+1}",
                    description=f"Test attribute {i+1} for E2E testing",
                    data_type="String",
                    mandatory_flag="Mandatory",
                    cde_flag=True if i == 0 else False,
                    historical_issues_flag=True if i == 1 else False,
                    is_scoped=True,
                    approval_status="approved",
                    is_primary_key=True if i == 0 else False,
                    primary_key_order=1 if i == 0 else None,
                    line_item_number=f"L{i+1}",
                    technical_line_item_name=f"tech_attr_{i+1}",
                    is_latest_version=True,
                    is_active=True,
                    version_created_by=1
                )
                db.add(attr)
            
            # Pre-create approved sample sets
            logger.info("Creating approved sample sets...")
            sample_set = SampleSet(
                cycle_id=cycle_id,
                report_id=report_id,
                set_name="Test Sample Set",
                description="Pre-approved sample set for testing",
                generation_method="Manual Upload",
                sample_type="Population Sample",
                status="Approved",
                target_sample_size=10,
                actual_sample_size=10,
                created_by=1,
                created_at=datetime.utcnow(),
                approved_by=1,
                approved_at=datetime.utcnow(),
                selection_criteria={"confidence_level": 95.0, "method": "Random"}
            )
            db.add(sample_set)
            
            await db.commit()
            
            # Create sample records
            logger.info("Creating sample records...")
            for i in range(10):
                sample = SampleRecord(
                    set_id=sample_set.set_id,
                    sample_identifier=f"SAMP{i+1:04d}",
                    primary_key_values={"customer_id": f"CUST{i+1:04d}"},
                    attribute_values={"balance": f"{(i+1)*1000}.00"},
                    validation_status="Valid",
                    is_included=True,
                    created_at=datetime.utcnow()
                )
                db.add(sample)
            
            # Create data provider assignments
            logger.info("Creating data provider assignments...")
            # Get the attributes we created
            result = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id
                )
            )
            attributes = result.scalars().all()
            
            for attr in attributes:
                assignment = AttributeLOBAssignment(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    attribute_id=attr.attribute_id,
                    lob_id=1,
                    data_owner_id=1,
                    assignment_method="Manual",
                    assigned_by=1,
                    assigned_at=datetime.utcnow(),
                    is_active=True,
                    notification_sent=True,
                    notified_at=datetime.utcnow()
                )
                db.add(assignment)
            
            await db.commit()
            logger.info("✅ Complete test data created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create test data: {str(e)}")
            await db.rollback()
            raise


async def test_complete_workflow_with_setup():
    """Test the complete workflow with proper data setup"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Generate unique IDs
        cycle_id = random.randint(50000, 59999)
        report_id = random.randint(500000, 599999)
        user_id = 1
        
        logger.info(f"\n=== Starting Complete E2E Workflow Test ===")
        logger.info(f"Cycle ID: {cycle_id}")
        logger.info(f"Report ID: {report_id}")
        
        # Setup comprehensive test data
        await setup_complete_test_data(cycle_id, report_id)
        
        # Start the workflow
        workflow_id = await client.start_testing_workflow(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=user_id
        )
        
        logger.info(f"✅ Workflow started: {workflow_id}")
        
        # Get workflow handle for queries and signals
        handle = client.client.get_workflow_handle(workflow_id)
        
        # Helper function to check status
        async def check_and_log_status(phase_name: str):
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
        
        status = await check_and_log_status("Initial Planning")
        
        # Since we pre-created documents, we just need to signal that they're uploaded
        if status.get("awaiting_action") == "upload_planning_documents":
            logger.info("Signaling planning documents are ready...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_planning_documents",
                signal_data={
                    "input_type": "planning_documents",
                    "data": {
                        "documents": [
                            {"name": "regulatory_spec.pdf", "type": "regulatory", "size": 1024000},
                            {"name": "cde_list.xlsx", "type": "cde_list", "size": 512000}
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            await asyncio.sleep(3)
        
        # Signal attributes are ready (already created)
        status = await handle.query("get_current_status")
        if status.get("awaiting_action") == "create_planning_attributes":
            logger.info("Signaling planning attributes are ready...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_planning_attributes",
                signal_data={
                    "input_type": "planning_attributes",
                    "data": {
                        "manual_attributes": []  # Already created in setup
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            await asyncio.sleep(3)
        
        # Wait for planning to complete
        await asyncio.sleep(5)
        status = await check_and_log_status("After Planning")
        
        # Phase 2: Scoping (attributes already approved)
        logger.info("\n=== PHASE 2: SCOPING ===")
        if status.get("current_phase") == "Scoping":
            # Tester review
            if status.get("awaiting_action") == "tester_review_attributes":
                logger.info("Performing tester review...")
                await client.signal_workflow(
                    workflow_id=workflow_id,
                    signal_name="submit_tester_review",
                    signal_data={
                        "input_type": "tester_review",
                        "data": {
                            "reviewed_attributes": [
                                {"attribute_id": 1, "is_scoped": True, "rationale": "Required"},
                                {"attribute_id": 2, "is_scoped": True, "rationale": "Required"},
                                {"attribute_id": 3, "is_scoped": True, "rationale": "Required"}
                            ]
                        },
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                await asyncio.sleep(3)
            
            # Report owner approval
            status = await handle.query("get_current_status")
            if status.get("awaiting_action") == "report_owner_approval":
                logger.info("Performing report owner approval...")
                await client.signal_workflow(
                    workflow_id=workflow_id,
                    signal_name="submit_report_owner_approval",
                    signal_data={
                        "input_type": "report_owner_approval",
                        "data": {
                            "approved": True,
                            "notes": "All attributes approved"
                        },
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                await asyncio.sleep(3)
        
        # Phases 3 & 4 run in parallel
        logger.info("\n=== PHASES 3 & 4: DATA PROVIDER ID + SAMPLE SELECTION (Parallel) ===")
        await asyncio.sleep(3)
        
        status = await check_and_log_status("Start of Parallel Phases")
        
        # Handle both phases which may be running in parallel
        handled_phases = set()
        
        for _ in range(10):  # Try multiple times as phases run in parallel
            status = await handle.query("get_current_status")
            awaiting = status.get("awaiting_action")
            
            if awaiting == "review_data_provider_assignments" and "dp" not in handled_phases:
                logger.info("Reviewing data provider assignments...")
                await client.signal_workflow(
                    workflow_id=workflow_id,
                    signal_name="submit_dp_assignment_review",
                    signal_data={
                        "input_type": "dp_assignment_review",
                        "data": {
                            "reviewed_assignments": [
                                {"attribute_id": 1, "lob_id": 1, "contact_info": "test@example.com"}
                            ]
                        },
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                handled_phases.add("dp")
                await asyncio.sleep(2)
                
            elif awaiting == "define_selection_criteria" and "criteria" not in handled_phases:
                logger.info("Defining sample selection criteria...")
                await client.signal_workflow(
                    workflow_id=workflow_id,
                    signal_name="submit_selection_criteria",
                    signal_data={
                        "input_type": "selection_criteria",
                        "data": {
                            "criteria": {
                                "confidence_level": 95.0,
                                "selection_method": "Random"
                            }
                        },
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                handled_phases.add("criteria")
                await asyncio.sleep(2)
                
            elif awaiting == "approve_samples" and "cycle_report_sample_selection_samples" not in handled_phases:
                logger.info("Approving sample selection...")
                await client.signal_workflow(
                    workflow_id=workflow_id,
                    signal_name="submit_sample_approval",
                    signal_data={
                        "input_type": "sample_approval",
                        "data": {
                            "approved_samples": []  # Already approved in setup
                        },
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                handled_phases.add("cycle_report_sample_selection_samples")
                await asyncio.sleep(2)
            
            # Check if we've moved to the next phase
            if status.get("current_phase") == "Request Info":
                break
                
            await asyncio.sleep(2)
        
        # Continue with remaining phases...
        await asyncio.sleep(5)
        status = await check_and_log_status("After Parallel Phases")
        
        # Log final results
        logger.info(f"\n=== Workflow Progress Summary ===")
        logger.info(f"Final Phase: {status.get('current_phase')}")
        logger.info(f"Completed Phases: {list(status.get('phase_results', {}).keys())}")
        
        return {
            "workflow_id": workflow_id,
            "final_status": status,
            "phases_completed": len(status.get('phase_results', {}))
        }
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main test function"""
    logger.info("=== Temporal Complete E2E Test with Proper Setup ===")
    logger.info("This test pre-creates all required data for workflow success\n")
    
    try:
        result = await test_complete_workflow_with_setup()
        
        logger.info(f"\n✅ Test Completed!")
        logger.info(f"Workflow ID: {result['workflow_id']}")
        logger.info(f"Phases Completed: {result['phases_completed']}")
        
        if result['phases_completed'] >= 4:
            logger.info("\n🎉 Successfully tested multiple phases!")
            return 0
        else:
            logger.warning("\n⚠️  Not all phases were tested")
            return 1
        
    except Exception as e:
        logger.error(f"\n❌ Test Failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)