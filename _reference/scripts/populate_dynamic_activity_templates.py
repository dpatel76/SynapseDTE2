"""
Populate Dynamic Activity Templates
Creates comprehensive activity templates for all workflow phases
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.workflow_activity import WorkflowActivityTemplate, ActivityType
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define comprehensive activity templates for each phase
ACTIVITY_TEMPLATES = [
    # Planning Phase Activities
    {
        "phase_name": "Planning",
        "activity_name": "Start Planning Phase",
        "activity_type": ActivityType.START,
        "activity_order": 1,
        "description": "Initialize planning phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Planning",
        "activity_name": "Generate Attributes",
        "activity_type": ActivityType.TASK,
        "activity_order": 2,
        "description": "Generate test attributes using LLM",
        "is_manual": False,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "GenerateAttributesHandler",
        "timeout_seconds": 300,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Planning",
        "activity_name": "Review Generated Attributes",
        "activity_type": ActivityType.REVIEW,
        "activity_order": 3,
        "description": "Tester reviews and modifies generated attributes",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,  # 24 hours
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Planning",
        "activity_name": "Submit for Approval",
        "activity_type": ActivityType.REVIEW,
        "activity_order": 4,
        "description": "Submit attributes for report owner approval",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 3600,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Planning",
        "activity_name": "Report Owner Approval",
        "activity_type": ActivityType.APPROVAL,
        "activity_order": 5,
        "description": "Report owner approves test attributes",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Report Owner",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 172800,  # 48 hours
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Planning",
        "activity_name": "Complete Planning Phase",
        "activity_type": ActivityType.COMPLETE,
        "activity_order": 6,
        "description": "Finalize planning phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    
    # Data Profiling Phase Activities
    {
        "phase_name": "Data Profiling",
        "activity_name": "Start Data Profiling",
        "activity_type": ActivityType.START,
        "activity_order": 1,
        "description": "Initialize data profiling phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Data Profiling",
        "activity_name": "Upload Data Files",
        "activity_type": ActivityType.TASK,
        "activity_order": 2,
        "description": "Upload data files for profiling",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Data Profiling",
        "activity_name": "Execute Data Profiling",
        "activity_type": ActivityType.TASK,
        "activity_order": 3,
        "description": "Analyze data patterns and generate insights",
        "is_manual": False,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "DataProfilingHandler",
        "timeout_seconds": 1800,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Data Profiling",
        "activity_name": "Review Profiling Results",
        "activity_type": ActivityType.REVIEW,
        "activity_order": 4,
        "description": "Review and validate profiling results",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 43200,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Data Profiling",
        "activity_name": "Complete Data Profiling",
        "activity_type": ActivityType.COMPLETE,
        "activity_order": 5,
        "description": "Finalize data profiling phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    
    # Scoping Phase Activities
    {
        "phase_name": "Scoping",
        "activity_name": "Start Scoping Phase",
        "activity_type": ActivityType.START,
        "activity_order": 1,
        "description": "Initialize scoping phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Scoping",
        "activity_name": "Execute Scoping",
        "activity_type": ActivityType.TASK,
        "activity_order": 2,
        "description": "Determine which attributes to test",
        "is_manual": False,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ExecuteScopingHandler",
        "timeout_seconds": 600,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Scoping",
        "activity_name": "Review Scoping Results",
        "activity_type": ActivityType.REVIEW,
        "activity_order": 3,
        "description": "Review and adjust scoping decisions",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 43200,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Scoping",
        "activity_name": "Scoping Approval",
        "activity_type": ActivityType.APPROVAL,
        "activity_order": 4,
        "description": "Approve final scope",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Report Owner",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Scoping",
        "activity_name": "Complete Scoping Phase",
        "activity_type": ActivityType.COMPLETE,
        "activity_order": 5,
        "description": "Finalize scoping phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    
    # Sample Selection Phase Activities
    {
        "phase_name": "Sample Selection",
        "activity_name": "Start Sample Selection",
        "activity_type": ActivityType.START,
        "activity_order": 1,
        "description": "Initialize sample selection phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Sample Selection",
        "activity_name": "Generate Samples",
        "activity_type": ActivityType.TASK,
        "activity_order": 2,
        "description": "Generate test samples with LOB tagging",
        "is_manual": False,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "GenerateSamplesHandler",
        "timeout_seconds": 600,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Sample Selection",
        "activity_name": "Review and Tag Samples",
        "activity_type": ActivityType.TASK,
        "activity_order": 3,
        "description": "Review samples and ensure LOB tags are correct",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Sample Selection",
        "activity_name": "Upload Additional Samples",
        "activity_type": ActivityType.TASK,
        "activity_order": 4,
        "description": "Upload any additional manual samples",
        "is_manual": True,
        "is_optional": True,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 43200,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Sample Selection",
        "activity_name": "Complete Sample Selection",
        "activity_type": ActivityType.COMPLETE,
        "activity_order": 5,
        "description": "Finalize sample selection phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    
    # Data Owner Identification Phase Activities
    {
        "phase_name": "Data Owner Identification",
        "activity_name": "Start Data Owner ID",
        "activity_type": ActivityType.START,
        "activity_order": 1,
        "description": "Initialize data owner identification phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Data Owner Identification",
        "activity_name": "Assign LOB Executives",
        "activity_type": ActivityType.TASK,
        "activity_order": 2,
        "description": "CDO assigns LOB executives based on sample tags",
        "is_manual": True,
        "is_optional": False,
        "required_role": "CDO",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Data Owner Identification",
        "activity_name": "Assign Data Owners",
        "activity_type": ActivityType.TASK,
        "activity_order": 3,
        "description": "LOB executives assign data owners",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Report Owner Executive",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Data Owner Identification",
        "activity_name": "Assign Data Providers",
        "activity_type": ActivityType.TASK,
        "activity_order": 4,
        "description": "Data owners assign data providers",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Data Owner",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Data Owner Identification",
        "activity_name": "Complete Provider ID",
        "activity_type": ActivityType.COMPLETE,
        "activity_order": 5,
        "description": "Finalize data owner identification phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    
    # Request for Information Phase Activities (Parallel)
    {
        "phase_name": "Request for Information",
        "activity_name": "Start Request Info",
        "activity_type": ActivityType.START,
        "activity_order": 1,
        "description": "Initialize request for information phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Request for Information",
        "activity_name": "Send Data Request",
        "activity_type": ActivityType.TASK,
        "activity_order": 2,
        "description": "Send data upload request to data owner",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "SendDataRequestHandler",
        "timeout_seconds": 300,
        "execution_mode": "parallel"  # Parallel by data owner
    },
    {
        "phase_name": "Request for Information",
        "activity_name": "Upload Data",
        "activity_type": ActivityType.TASK,
        "activity_order": 3,
        "description": "Data owner uploads requested data",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Data Owner",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 259200,  # 3 days
        "execution_mode": "parallel"
    },
    {
        "phase_name": "Request for Information",
        "activity_name": "Validate Data Upload",
        "activity_type": ActivityType.TASK,
        "activity_order": 4,
        "description": "Validate uploaded data completeness",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "ValidateDataUploadHandler",
        "timeout_seconds": 600,
        "execution_mode": "parallel"
    },
    {
        "phase_name": "Request for Information",
        "activity_name": "Generate Test Cases",
        "activity_type": ActivityType.TASK,
        "activity_order": 5,
        "description": "Generate test cases for uploaded data",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "GenerateTestCasesHandler",
        "timeout_seconds": 900,
        "execution_mode": "parallel"
    },
    {
        "phase_name": "Request for Information",
        "activity_name": "Data Upload Complete",
        "activity_type": ActivityType.COMPLETE,
        "activity_order": 6,
        "description": "Mark data upload as complete",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "parallel"
    },
    
    # Test Execution Phase Activities (Parallel)
    {
        "phase_name": "Test Execution",
        "activity_name": "Start Test Execution",
        "activity_type": ActivityType.START,
        "activity_order": 1,
        "description": "Initialize test execution phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Test Execution",
        "activity_name": "Execute Tests",
        "activity_type": ActivityType.TASK,
        "activity_order": 2,
        "description": "Execute tests on uploaded document",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "ExecuteTestsHandler",
        "timeout_seconds": 1800,
        "execution_mode": "parallel"  # Parallel by document
    },
    {
        "phase_name": "Test Execution",
        "activity_name": "Review Test Results",
        "activity_type": ActivityType.REVIEW,
        "activity_order": 3,
        "description": "Review automated test results",
        "is_manual": True,
        "is_optional": True,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 43200,
        "execution_mode": "parallel"
    },
    {
        "phase_name": "Test Execution",
        "activity_name": "Document Test Evidence",
        "activity_type": ActivityType.TASK,
        "activity_order": 4,
        "description": "Document test execution evidence",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "parallel"
    },
    {
        "phase_name": "Test Execution",
        "activity_name": "Complete Test Execution",
        "activity_type": ActivityType.COMPLETE,
        "activity_order": 5,
        "description": "Mark test execution as complete",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "parallel"
    },
    
    # Observation Management Phase Activities (Parallel)
    {
        "phase_name": "Observation Management",
        "activity_name": "Start Observation Management",
        "activity_type": ActivityType.START,
        "activity_order": 1,
        "description": "Initialize observation management phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Observation Management",
        "activity_name": "Create Observations",
        "activity_type": ActivityType.TASK,
        "activity_order": 2,
        "description": "Create observations for test failures",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "CreateObservationsHandler",
        "timeout_seconds": 600,
        "execution_mode": "parallel"  # Parallel by test execution
    },
    {
        "phase_name": "Observation Management",
        "activity_name": "Review Observations",
        "activity_type": ActivityType.REVIEW,
        "activity_order": 3,
        "description": "Review and categorize observations",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "parallel"
    },
    {
        "phase_name": "Observation Management",
        "activity_name": "Data Owner Response",
        "activity_type": ActivityType.TASK,
        "activity_order": 4,
        "description": "Data owner provides response to observations",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Data Owner",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 172800,
        "execution_mode": "parallel"
    },
    {
        "phase_name": "Observation Management",
        "activity_name": "Finalize Observations",
        "activity_type": ActivityType.APPROVAL,
        "activity_order": 5,
        "description": "Finalize observation status",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 43200,
        "execution_mode": "parallel"
    },
    {
        "phase_name": "Observation Management",
        "activity_name": "Complete Observation Management",
        "activity_type": ActivityType.COMPLETE,
        "activity_order": 6,
        "description": "Mark observation management as complete",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "parallel"
    },
    
    # Finalize Test Report Phase Activities
    {
        "phase_name": "Finalize Test Report",
        "activity_name": "Start Report Finalization",
        "activity_type": ActivityType.START,
        "activity_order": 1,
        "description": "Initialize report finalization phase",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential",
        "conditional_expression": '{"all_observations_complete": true}'
    },
    {
        "phase_name": "Finalize Test Report",
        "activity_name": "Generate Report Sections",
        "activity_type": ActivityType.TASK,
        "activity_order": 2,
        "description": "Generate test report sections",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "GenerateReportSectionsHandler",
        "timeout_seconds": 1800,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Finalize Test Report",
        "activity_name": "Review Report Draft",
        "activity_type": ActivityType.REVIEW,
        "activity_order": 3,
        "description": "Review and edit report draft",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Tester",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Finalize Test Report",
        "activity_name": "Quality Review",
        "activity_type": ActivityType.APPROVAL,
        "activity_order": 4,
        "description": "Quality review of test report",
        "is_manual": True,
        "is_optional": False,
        "required_role": "Test Manager",
        "handler_name": "ManualActivityHandler",
        "timeout_seconds": 86400,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Finalize Test Report",
        "activity_name": "Generate Final Report",
        "activity_type": ActivityType.TASK,
        "activity_order": 5,
        "description": "Generate final PDF report",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "GenerateFinalReportHandler",
        "timeout_seconds": 600,
        "execution_mode": "sequential"
    },
    {
        "phase_name": "Finalize Test Report",
        "activity_name": "Complete Report Finalization",
        "activity_type": ActivityType.COMPLETE,
        "activity_order": 6,
        "description": "Mark report as finalized",
        "is_manual": False,
        "is_optional": False,
        "required_role": None,
        "handler_name": "AutomatedActivityHandler",
        "timeout_seconds": 60,
        "execution_mode": "sequential"
    }
]


async def populate_templates(db: AsyncSession):
    """Populate workflow activity templates"""
    try:
        # Clear existing templates
        await db.execute(delete(WorkflowActivityTemplate))
        await db.commit()
        
        # Insert new templates
        for template_data in ACTIVITY_TEMPLATES:
            template = WorkflowActivityTemplate(**template_data)
            db.add(template)
        
        await db.commit()
        logger.info(f"Successfully populated {len(ACTIVITY_TEMPLATES)} activity templates")
        
    except Exception as e:
        logger.error(f"Error populating templates: {str(e)}")
        await db.rollback()
        raise


async def main():
    """Main function"""
    # Create async engine
    database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True
    )
    
    # Create session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        await populate_templates(session)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())