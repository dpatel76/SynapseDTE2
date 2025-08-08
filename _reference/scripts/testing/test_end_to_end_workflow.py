#!/usr/bin/env python
"""End-to-end test of the Temporal workflow system"""

import asyncio
import logging
from datetime import datetime
import random
import time
from app.temporal.client import get_temporal_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_full_workflow():
    """Test the complete workflow from planning to observations"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Generate unique IDs
        cycle_id = random.randint(1000, 9999)
        report_id = random.randint(10000, 99999)
        user_id = 1
        
        logger.info(f"\n=== Starting E2E Workflow Test ===")
        logger.info(f"Cycle ID: {cycle_id}")
        logger.info(f"Report ID: {report_id}")
        
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
            await asyncio.sleep(2)
        
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
            await asyncio.sleep(2)
        
        # Step 1.3: Review and complete planning
        status = await handle.query("get_current_status")
        if status.get("awaiting_action") == "review_planning_checklist":
            logger.info("Reviewing planning checklist...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_planning_review",
                signal_data={
                    "input_type": "planning_review",
                    "data": {
                        "checklist_approved": True,
                        "notes": "All planning requirements met"
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Planning phase completed")
            await asyncio.sleep(2)
        
        # Test Phase 2: Scoping
        logger.info("\n--- Phase 2: Scoping ---")
        status = await handle.query("get_current_status")
        
        if status.get("current_phase") == "Scoping":
            # Step 2.1: LLM recommendations
            if status.get("awaiting_action") == "generate_scoping_recommendations":
                logger.info("Generating scoping recommendations...")
                await client.signal_workflow(
                    workflow_id=workflow_id,
                    signal_name="submit_scoping_recommendations",
                    signal_data={
                        "input_type": "scoping_recommendations",
                        "data": {
                            "recommendations": [
                                {
                                    "attribute_id": 1,
                                    "scope_flag": True,
                                    "rationale": "Critical customer identifier"
                                },
                                {
                                    "attribute_id": 2,
                                    "scope_flag": True,
                                    "rationale": "Financial data with historical issues"
                                },
                                {
                                    "attribute_id": 3,
                                    "scope_flag": False,
                                    "rationale": "Low risk metadata field"
                                }
                            ]
                        },
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                logger.info("✅ Scoping recommendations generated")
                await asyncio.sleep(2)
            
            # Step 2.2: Tester decisions
            status = await handle.query("get_current_status")
            if status.get("awaiting_action") == "cycle_report_scoping_tester_decisions":
                logger.info("Making tester scoping decisions...")
                await client.signal_workflow(
                    workflow_id=workflow_id,
                    signal_name="submit_tester_decisions",
                    signal_data={
                        "input_type": "tester_decisions",
                        "data": {
                            "decisions": [
                                {
                                    "attribute_id": 1,
                                    "scope_flag": True,
                                    "notes": "Agreed with recommendation"
                                },
                                {
                                    "attribute_id": 2,
                                    "scope_flag": True,
                                    "notes": "Critical for testing"
                                }
                            ]
                        },
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                logger.info("✅ Tester decisions submitted")
                await asyncio.sleep(2)
            
            # Step 2.3: Report owner review
            status = await handle.query("get_current_status")
            if status.get("awaiting_action") == "report_owner_review":
                logger.info("Report owner reviewing scoping...")
                await client.signal_workflow(
                    workflow_id=workflow_id,
                    signal_name="submit_report_owner_review",
                    signal_data={
                        "input_type": "report_owner_review",
                        "data": {
                            "approved": True,
                            "comments": "Scoping approved"
                        },
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                logger.info("✅ Scoping phase completed")
                await asyncio.sleep(2)
        
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
    logger.info("=== Temporal E2E Workflow Test ===")
    logger.info("Testing complete workflow with all phases\n")
    
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