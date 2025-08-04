#!/usr/bin/env python
"""Complete end-to-end test covering all 8 workflow phases"""

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
            logger.info("✅ Test data created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create test data: {str(e)}")
            await db.rollback()
            raise


async def test_complete_workflow():
    """Test the complete workflow from planning to observations"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Generate unique IDs
        cycle_id = random.randint(10000, 99999)
        report_id = random.randint(100000, 999999)
        user_id = 1
        
        logger.info(f"\n=== Starting Complete E2E Workflow Test ===")
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
        
        # Phase 1: Planning
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
                                "data_type": "String",
                                "description": "Unique customer identifier",
                                "cde_flag": True,
                                "historical_issues_flag": False
                            },
                            {
                                "attribute_name": "Account Balance",
                                "data_type": "Decimal",
                                "description": "Current account balance",
                                "cde_flag": True,
                                "historical_issues_flag": True
                            },
                            {
                                "attribute_name": "Credit Limit",
                                "data_type": "Decimal",
                                "description": "Maximum credit limit",
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
        
        # Step 1.3: Planning phase should complete automatically
        logger.info("Waiting for planning phase to complete...")
        await asyncio.sleep(5)  # Give time for the workflow to complete planning
        
        status = await handle.query("get_current_status")
        logger.info(f"Status after planning: {status}")
        
        if status.get("current_phase") != "Scoping":
            logger.warning(f"Planning phase not completed. Current phase: {status.get('current_phase')}")
        else:
            logger.info("✅ Planning phase completed")
        
        # Phase 2: Scoping
        logger.info("\n--- Phase 2: Scoping ---")
        status = await handle.query("get_current_status")
        
        if status.get("current_phase") == "Scoping":
            # Step 2.1: Wait for LLM recommendations then perform tester review
            await asyncio.sleep(3)  # Wait for LLM recommendations
            
            logger.info("Performing tester review...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_tester_review",
                signal_data={
                    "input_type": "tester_review",
                    "data": {
                        "reviewed_attributes": [
                            {"attribute_id": 1, "is_scoped": True, "rationale": "Critical for compliance"},
                            {"attribute_id": 2, "is_scoped": True, "rationale": "Has historical issues"},
                            {"attribute_id": 3, "is_scoped": True, "rationale": "Key risk indicator"}
                        ],
                        "notes": "All attributes reviewed and scoped in for testing"
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Tester review completed")
            await asyncio.sleep(3)
            
            # Step 2.2: Report owner approval
            logger.info("Performing report owner approval...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_report_owner_approval",
                signal_data={
                    "input_type": "report_owner_approval",
                    "data": {
                        "approved": True,
                        "notes": "All attributes approved for testing"
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Report owner approval completed")
            await asyncio.sleep(3)
        
        # Phases 3 & 4 run in parallel
        logger.info("\n--- Phases 3 & 4: Data Provider ID + Sample Selection (Parallel) ---")
        status = await handle.query("get_current_status")
        
        # Phase 3: Data Provider Identification
        await asyncio.sleep(3)  # Wait for phases to start
        logger.info("Reviewing data provider assignments...")
        await client.signal_workflow(
            workflow_id=workflow_id,
            signal_name="submit_dp_assignment_review",
            signal_data={
                "input_type": "dp_assignment_review",
                "data": {
                    "reviewed_assignments": [
                        {"attribute_id": 1, "lob_id": 1, "contact_info": "john.doe@bank.com"},
                        {"attribute_id": 2, "lob_id": 1, "contact_info": "jane.smith@bank.com"},
                        {"attribute_id": 3, "lob_id": 1, "contact_info": "bob.jones@bank.com"}
                    ]
                },
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        logger.info("✅ Data provider assignments reviewed")
        await asyncio.sleep(3)
        
        # Phase 4: Sample Selection - Define criteria first
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
        logger.info("✅ Selection criteria defined")
        await asyncio.sleep(3)
        
        # Approve samples
        logger.info("Approving sample selection...")
        await client.signal_workflow(
            workflow_id=workflow_id,
            signal_name="submit_sample_approval",
            signal_data={
                "input_type": "sample_approval",
                "data": {
                    "approved_samples": [
                            {
                                "attribute_id": 1,
                                "sample_size": 100,
                                "selection_method": "Random",
                                "confidence_level": 95.0,
                                "cycle_report_sample_selection_samples": [f"CUST{i:04d}" for i in range(1, 11)]  # Sample IDs
                            },
                            {
                                "attribute_id": 2,
                                "sample_size": 50,
                                "selection_method": "Stratified",
                                "confidence_level": 95.0,
                                "cycle_report_sample_selection_samples": [f"ACC{i:05d}" for i in range(1, 6)]
                            }
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
        )
        logger.info("✅ Sample approval completed")
        await asyncio.sleep(3)
        
        # Phase 5: Request for Information
        logger.info("\n--- Phase 5: Request for Information ---")
        status = await handle.query("get_current_status")
        
        if status.get("current_phase") == "Request Info":
            # RFI phase expects tracking of responses
            logger.info("Tracking RFI responses...")
            await asyncio.sleep(3)  # Simulate RFI being sent
            
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_rfi_responses",
                signal_data={
                    "input_type": "rfi_responses",
                    "data": {
                        "responses": [
                            {
                                "attribute_id": 1,
                                "request_type": "Document",
                                "status": "Received",
                                "documents": ["customer_onboarding.pdf"]
                            },
                            {
                                "attribute_id": 2,
                                "request_type": "Database Query",
                                "status": "Received",
                                "data_file": "account_balances.csv"
                            }
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ RFI responses tracked")
            await asyncio.sleep(3)
        
        # Phase 6: Test Execution
        logger.info("\n--- Phase 6: Test Execution ---")
        status = await handle.query("get_current_status")
        
        if status.get("current_phase") == "Testing":
            # Document tests first
            logger.info("Executing document tests...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_document_tests",
                signal_data={
                    "input_type": "document_tests",
                    "data": {
                        "document_test_results": [
                            {
                                "attribute_id": 1,
                                "sample_id": "CUST0001",
                                "source_value": "John Doe",
                                "target_value": "John Doe",
                                "test_result": "Pass",
                                "evidence_path": "/evidence/test1.pdf"
                            },
                            {
                                "attribute_id": 2,
                                "sample_id": "ACC00001",
                                "source_value": "50000.00",
                                "target_value": "49999.99",
                                "test_result": "Fail",
                                "variance": "0.01",
                                "notes": "Minor rounding difference"
                            }
                        ],
                        "summary": {
                            "total_document_tests": 100,
                            "passed": 98,
                            "failed": 2
                        }
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Document tests completed")
            await asyncio.sleep(3)
            
            # Database tests
            logger.info("Executing database tests...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_database_tests",
                signal_data={
                    "input_type": "cycle_report_test_execution_database_tests",
                    "data": {
                        "database_test_results": [
                            {
                                "attribute_id": 2,
                                "query": "SELECT balance FROM accounts WHERE account_id = ?",
                                "expected_count": 50,
                                "actual_count": 50,
                                "test_result": "Pass"
                            }
                        ],
                        "summary": {
                            "total_database_tests": 50,
                            "passed": 50,
                            "failed": 0
                        }
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Database tests completed")
            await asyncio.sleep(3)
        
        # Phase 7: Observations
        logger.info("\n--- Phase 7: Observations ---")
        status = await handle.query("get_current_status")
        
        if status.get("current_phase") == "Observations":
            # Create observations
            logger.info("Creating observations...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_observations",
                signal_data={
                    "input_type": "observations",
                    "data": {
                        "observations": [
                            {
                                "title": "Account Balance Discrepancy",
                                "description": "Minor rounding differences found in 2 accounts",
                                "severity": "Low",
                                "attribute_ids": [2],
                                "recommendation": "Review rounding logic in target system"
                            }
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Observations created")
            await asyncio.sleep(3)
            
            # Review observations
            logger.info("Reviewing observations...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_observation_review",
                signal_data={
                    "input_type": "observation_review",
                    "data": {
                        "reviewed_observations": [
                            {
                                "observation_id": 1,
                                "approved": True,
                                "notes": "Valid observation, proceed with remediation"
                            }
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Observations reviewed")
            await asyncio.sleep(3)
        
        # Phase 8: Test Report Preparation
        logger.info("\n--- Phase 8: Test Report Preparation ---")
        status = await handle.query("get_current_status")
        
        if status.get("current_phase") == "Preparing Test Report":
            # Wait for report generation to happen automatically
            logger.info("Waiting for report generation...")
            await asyncio.sleep(5)  # Give time for sections and summary generation
            
            # Review and approve report
            logger.info("Reviewing report...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_report_review",
                signal_data={
                    "input_type": "report_review",
                    "data": {
                        "approved": True,
                        "edits": [],
                        "notes": "Report reviewed and approved"
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Report reviewed and finalized")
            await asyncio.sleep(3)
        
        # Check final status
        await asyncio.sleep(3)
        final_status = await handle.query("get_current_status")
        logger.info(f"\n=== Final Workflow Status ===")
        logger.info(f"Current Phase: {final_status.get('current_phase')}")
        logger.info(f"Workflow Status: {final_status.get('workflow_status')}")
        logger.info(f"Completed Phases: {list(final_status.get('phase_results', {}).keys())}")
        
        # Get workflow execution status
        workflow_status = await client.get_workflow_status(workflow_id)
        logger.info(f"\nWorkflow Execution Status: {workflow_status['status']}")
        
        # Phase completion summary
        logger.info("\n=== Phase Completion Summary ===")
        phase_results = final_status.get('phase_results', {})
        for phase, result in phase_results.items():
            logger.info(f"{phase}: ✅ Completed")
        
        return {
            "workflow_id": workflow_id,
            "final_status": final_status,
            "execution_status": workflow_status,
            "all_phases_completed": len(phase_results) == 8
        }
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main test function"""
    logger.info("=== Temporal Complete E2E Workflow Test ===")
    logger.info("Testing all 8 phases of the workflow\n")
    
    try:
        result = await test_complete_workflow()
        
        logger.info(f"\n✅ Complete E2E Test Finished!")
        logger.info(f"Workflow ID: {result['workflow_id']}")
        logger.info(f"All Phases Completed: {result['all_phases_completed']}")
        logger.info(f"Final Status: {result['final_status']['workflow_status']}")
        logger.info(f"\nCheck Temporal UI at http://localhost:8088 for details")
        
        if result['all_phases_completed']:
            logger.info("\n🎉 SUCCESS: All 8 phases completed successfully!")
            return 0
        else:
            logger.warning("\n⚠️  WARNING: Not all phases were completed")
            return 1
        
    except Exception as e:
        logger.error(f"\n❌ E2E Test Failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)