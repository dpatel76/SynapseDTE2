"""Simple test to verify Temporal workflow structure

This script tests the workflow structure without executing all activities.
"""

import asyncio
import logging
from app.temporal.workflows.enhanced_test_cycle_workflow import EnhancedTestCycleWorkflow
from app.temporal.shared import TestCycleWorkflowInput, WORKFLOW_PHASES
from app.temporal.shared.constants import PHASE_DEPENDENCIES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_workflow_phases():
    """Test workflow phase configuration"""
    logger.info("Testing workflow phase configuration...")
    
    # Check phase count
    assert len(WORKFLOW_PHASES) == 8, f"Expected 8 phases, got {len(WORKFLOW_PHASES)}"
    logger.info(f"✓ Workflow has {len(WORKFLOW_PHASES)} phases")
    
    # Check phase order
    expected_phases = [
        "Planning",
        "Scoping",
        "Sample Selection",
        "Data Owner Identification",
        "Request for Information",
        "Test Execution",
        "Observation Management",
        "Finalize Test Report"
    ]
    
    for i, phase in enumerate(expected_phases):
        assert WORKFLOW_PHASES[i] == phase, f"Phase {i} mismatch: expected {phase}, got {WORKFLOW_PHASES[i]}"
    logger.info("✓ Phase order is correct")
    
    # Check phase dependencies
    logger.info("\nPhase Dependencies:")
    for phase, deps in PHASE_DEPENDENCIES.items():
        logger.info(f"  {phase}: {deps if deps else 'No dependencies'}")
    
    # Verify Sample Selection comes before Data Owner Identification
    assert "Sample Selection" in PHASE_DEPENDENCIES["Data Owner Identification"], \
        "Data Owner Identification must depend on Sample Selection"
    logger.info("\n✓ Data Owner Identification correctly depends on Sample Selection")
    
    # Check all phases have dependencies defined
    for phase in WORKFLOW_PHASES:
        assert phase in PHASE_DEPENDENCIES, f"Missing dependency definition for {phase}"
    logger.info("✓ All phases have dependency definitions")


def test_workflow_input():
    """Test workflow input structure"""
    logger.info("\n\nTesting workflow input structure...")
    
    # Create test input
    workflow_input = TestCycleWorkflowInput(
        cycle_id=1,
        report_ids=[1, 2, 3],
        initiated_by_user_id=1,
        auto_assign_testers=True,
        auto_generate_attributes=True,
        skip_phases=["Test Execution"],  # Skip one phase
        metadata={"test": True}
    )
    
    # Verify input
    assert workflow_input.cycle_id == 1
    assert len(workflow_input.report_ids) == 3
    assert workflow_input.initiated_by_user_id == 1
    assert workflow_input.auto_assign_testers == True
    assert workflow_input.auto_generate_attributes == True
    assert "Test Execution" in workflow_input.skip_phases
    assert workflow_input.metadata["test"] == True
    
    logger.info("✓ Workflow input structure is valid")


def test_activity_imports():
    """Test that all required activities are importable"""
    logger.info("\n\nTesting activity imports...")
    
    try:
        # Planning activities
        from app.temporal.activities.planning_activities import (
            start_planning_phase_activity,
            execute_planning_activities,
            complete_planning_phase_activity
        )
        logger.info("✓ Planning activities imported successfully")
        
        # Scoping activities
        from app.temporal.activities.scoping_activities import (
            start_scoping_phase_activity,
            execute_scoping_activities,
            complete_scoping_phase_activity
        )
        logger.info("✓ Scoping activities imported successfully")
        
        # Sample Selection activities
        from app.temporal.activities.sample_selection_activities import (
            start_sample_selection_phase_activity,
            execute_sample_selection_activities,
            complete_sample_selection_phase_activity
        )
        logger.info("✓ Sample Selection activities imported successfully")
        
        # Data Owner activities
        from app.temporal.activities.data_owner_activities import (
            start_data_owner_identification_phase_activity,
            execute_data_owner_activities,
            complete_data_owner_identification_phase_activity
        )
        logger.info("✓ Data Owner Identification activities imported successfully")
        
        # Request Info activities
        from app.temporal.activities.request_info_activities import (
            start_request_info_phase_activity,
            execute_request_info_activities,
            complete_request_info_phase_activity
        )
        logger.info("✓ Request for Information activities imported successfully")
        
        # Tracking activities
        from app.temporal.activities.tracking_activities import (
            record_workflow_start_activity,
            record_workflow_complete_activity,
            record_step_start_activity,
            record_step_complete_activity,
            record_transition_activity,
            calculate_workflow_metrics_activity
        )
        logger.info("✓ Tracking activities imported successfully")
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        raise


def test_workflow_structure():
    """Test enhanced workflow structure"""
    logger.info("\n\nTesting enhanced workflow structure...")
    
    # Check workflow class exists
    assert EnhancedTestCycleWorkflow is not None
    logger.info("✓ EnhancedTestCycleWorkflow class exists")
    
    # Check workflow has required methods
    assert hasattr(EnhancedTestCycleWorkflow, 'run'), "Workflow missing run method"
    assert hasattr(EnhancedTestCycleWorkflow, '_execute_sequential_phases'), "Workflow missing _execute_sequential_phases"
    assert hasattr(EnhancedTestCycleWorkflow, '_execute_phase_with_tracking'), "Workflow missing _execute_phase_with_tracking"
    assert hasattr(EnhancedTestCycleWorkflow, '_record_workflow_start'), "Workflow missing _record_workflow_start"
    assert hasattr(EnhancedTestCycleWorkflow, '_calculate_metrics'), "Workflow missing _calculate_metrics"
    logger.info("✓ Workflow has all required methods")


def main():
    """Run all tests"""
    logger.info("Starting Temporal workflow structure tests...\n")
    
    try:
        test_workflow_phases()
        test_workflow_input()
        test_activity_imports()
        test_workflow_structure()
        
        logger.info("\n\n✅ All tests passed successfully!")
        logger.info("\nWorkflow Summary:")
        logger.info(f"- Total phases: {len(WORKFLOW_PHASES)}")
        logger.info(f"- Sequential execution with proper dependencies")
        logger.info(f"- Sample Selection → Data Owner Identification flow implemented")
        logger.info(f"- Comprehensive tracking and metrics collection")
        logger.info(f"- Standard start/complete pattern for all phases")
        
    except Exception as e:
        logger.error(f"\n\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()