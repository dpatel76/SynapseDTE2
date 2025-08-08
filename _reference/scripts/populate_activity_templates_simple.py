"""Simple script to populate activity templates"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TEMPLATES_SQL = """
-- Clear existing templates
DELETE FROM workflow_activity_templates;

-- Planning Phase Activities
INSERT INTO workflow_activity_templates 
(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, handler_name, timeout_seconds, execution_mode)
VALUES
('Planning', 'Start Planning Phase', 'START', 1, 'Initialize planning phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential'),
('Planning', 'Generate Attributes', 'TASK', 2, 'Generate test attributes using LLM', false, false, 'Tester', 'GenerateAttributesHandler', 300, 'sequential'),
('Planning', 'Review Generated Attributes', 'REVIEW', 3, 'Tester reviews and modifies generated attributes', true, false, 'Tester', 'ManualActivityHandler', 86400, 'sequential'),
('Planning', 'Submit for Approval', 'REVIEW', 4, 'Submit attributes for report owner approval', true, false, 'Tester', 'ManualActivityHandler', 3600, 'sequential'),
('Planning', 'Report Owner Approval', 'APPROVAL', 5, 'Report owner approves test attributes', true, false, 'Report Owner', 'ManualActivityHandler', 172800, 'sequential'),
('Planning', 'Complete Planning Phase', 'COMPLETE', 6, 'Finalize planning phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential');

-- Data Profiling Phase Activities
INSERT INTO workflow_activity_templates 
(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, handler_name, timeout_seconds, execution_mode)
VALUES
('Data Profiling', 'Start Data Profiling', 'START', 1, 'Initialize data profiling phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential'),
('Data Profiling', 'Upload Data Files', 'TASK', 2, 'Upload data files for profiling', true, false, 'Tester', 'ManualActivityHandler', 86400, 'sequential'),
('Data Profiling', 'Execute Data Profiling', 'TASK', 3, 'Analyze data patterns and generate insights', false, false, 'Tester', 'DataProfilingHandler', 1800, 'sequential'),
('Data Profiling', 'Review Profiling Results', 'REVIEW', 4, 'Review and validate profiling results', true, false, 'Tester', 'ManualActivityHandler', 43200, 'sequential'),
('Data Profiling', 'Complete Data Profiling', 'COMPLETE', 5, 'Finalize data profiling phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential');

-- Scoping Phase Activities
INSERT INTO workflow_activity_templates 
(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, handler_name, timeout_seconds, execution_mode)
VALUES
('Scoping', 'Start Scoping Phase', 'START', 1, 'Initialize scoping phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential'),
('Scoping', 'Execute Scoping', 'TASK', 2, 'Determine which attributes to test', false, false, 'Tester', 'ExecuteScopingHandler', 600, 'sequential'),
('Scoping', 'Review Scoping Results', 'REVIEW', 3, 'Review and adjust scoping decisions', true, false, 'Tester', 'ManualActivityHandler', 43200, 'sequential'),
('Scoping', 'Scoping Approval', 'APPROVAL', 4, 'Approve final scope', true, false, 'Report Owner', 'ManualActivityHandler', 86400, 'sequential'),
('Scoping', 'Complete Scoping Phase', 'COMPLETE', 5, 'Finalize scoping phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential');

-- Sample Selection Phase Activities
INSERT INTO workflow_activity_templates 
(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, handler_name, timeout_seconds, execution_mode)
VALUES
('Sample Selection', 'Start Sample Selection', 'START', 1, 'Initialize sample selection phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential'),
('Sample Selection', 'Generate Samples', 'TASK', 2, 'Generate test samples with LOB tagging', false, false, 'Tester', 'GenerateSamplesHandler', 600, 'sequential'),
('Sample Selection', 'Review and Tag Samples', 'TASK', 3, 'Review samples and ensure LOB tags are correct', true, false, 'Tester', 'ManualActivityHandler', 86400, 'sequential'),
('Sample Selection', 'Upload Additional Samples', 'TASK', 4, 'Upload any additional manual samples', true, true, 'Tester', 'ManualActivityHandler', 43200, 'sequential'),
('Sample Selection', 'Complete Sample Selection', 'COMPLETE', 5, 'Finalize sample selection phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential');

-- Data Owner Identification Phase Activities
INSERT INTO workflow_activity_templates 
(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, handler_name, timeout_seconds, execution_mode)
VALUES
('Data Owner Identification', 'Start Data Owner ID', 'START', 1, 'Initialize data owner identification phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential'),
('Data Owner Identification', 'Assign LOB Executives', 'TASK', 2, 'CDO assigns LOB executives based on sample tags', true, false, 'CDO', 'ManualActivityHandler', 86400, 'sequential'),
('Data Owner Identification', 'Assign Data Owners', 'TASK', 3, 'LOB executives assign data owners', true, false, 'Report Owner Executive', 'ManualActivityHandler', 86400, 'sequential'),
('Data Owner Identification', 'Assign Data Providers', 'TASK', 4, 'Data owners assign data providers', true, false, 'Data Owner', 'ManualActivityHandler', 86400, 'sequential'),
('Data Owner Identification', 'Complete Provider ID', 'COMPLETE', 5, 'Finalize data owner identification phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential');

-- Request for Information Phase Activities (Parallel)
INSERT INTO workflow_activity_templates 
(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, handler_name, timeout_seconds, execution_mode)
VALUES
('Request for Information', 'Start Request Info', 'START', 1, 'Initialize request for information phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential'),
('Request for Information', 'Send Data Request', 'TASK', 2, 'Send data upload request to data owner', false, false, NULL, 'SendDataRequestHandler', 300, 'parallel'),
('Request for Information', 'Upload Data', 'TASK', 3, 'Data owner uploads requested data', true, false, 'Data Owner', 'ManualActivityHandler', 259200, 'parallel'),
('Request for Information', 'Validate Data Upload', 'TASK', 4, 'Validate uploaded data completeness', false, false, NULL, 'ValidateDataUploadHandler', 600, 'parallel'),
('Request for Information', 'Generate Test Cases', 'TASK', 5, 'Generate test cases for uploaded data', false, false, NULL, 'GenerateTestCasesHandler', 900, 'parallel'),
('Request for Information', 'Data Upload Complete', 'COMPLETE', 6, 'Mark data upload as complete', false, false, NULL, 'AutomatedActivityHandler', 60, 'parallel');

-- Test Execution Phase Activities (Parallel)
INSERT INTO workflow_activity_templates 
(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, handler_name, timeout_seconds, execution_mode)
VALUES
('Test Execution', 'Start Test Execution', 'START', 1, 'Initialize test execution phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential'),
('Test Execution', 'Execute Tests', 'TASK', 2, 'Execute tests on uploaded document', false, false, NULL, 'ExecuteTestsHandler', 1800, 'parallel'),
('Test Execution', 'Review Test Results', 'REVIEW', 3, 'Review automated test results', true, true, 'Tester', 'ManualActivityHandler', 43200, 'parallel'),
('Test Execution', 'Document Test Evidence', 'TASK', 4, 'Document test execution evidence', true, false, 'Tester', 'ManualActivityHandler', 86400, 'parallel'),
('Test Execution', 'Complete Test Execution', 'COMPLETE', 5, 'Mark test execution as complete', false, false, NULL, 'AutomatedActivityHandler', 60, 'parallel');

-- Observation Management Phase Activities (Parallel)
INSERT INTO workflow_activity_templates 
(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, handler_name, timeout_seconds, execution_mode)
VALUES
('Observation Management', 'Start Observation Management', 'START', 1, 'Initialize observation management phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential'),
('Observation Management', 'Create Observations', 'TASK', 2, 'Create observations for test failures', false, false, NULL, 'CreateObservationsHandler', 600, 'parallel'),
('Observation Management', 'Review Observations', 'REVIEW', 3, 'Review and categorize observations', true, false, 'Tester', 'ManualActivityHandler', 86400, 'parallel'),
('Observation Management', 'Data Owner Response', 'TASK', 4, 'Data owner provides response to observations', true, false, 'Data Owner', 'ManualActivityHandler', 172800, 'parallel'),
('Observation Management', 'Finalize Observations', 'APPROVAL', 5, 'Finalize observation status', true, false, 'Tester', 'ManualActivityHandler', 43200, 'parallel'),
('Observation Management', 'Complete Observation Management', 'COMPLETE', 6, 'Mark observation management as complete', false, false, NULL, 'AutomatedActivityHandler', 60, 'parallel');

-- Finalize Test Report Phase Activities
INSERT INTO workflow_activity_templates 
(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, handler_name, timeout_seconds, execution_mode)
VALUES
('Finalize Test Report', 'Start Report Finalization', 'START', 1, 'Initialize report finalization phase', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential'),
('Finalize Test Report', 'Generate Report Sections', 'TASK', 2, 'Generate test report sections', false, false, NULL, 'GenerateReportSectionsHandler', 1800, 'sequential'),
('Finalize Test Report', 'Review Report Draft', 'REVIEW', 3, 'Review and edit report draft', true, false, 'Tester', 'ManualActivityHandler', 86400, 'sequential'),
('Finalize Test Report', 'Quality Review', 'APPROVAL', 4, 'Quality review of test report', true, false, 'Test Manager', 'ManualActivityHandler', 86400, 'sequential'),
('Finalize Test Report', 'Generate Final Report', 'TASK', 5, 'Generate final PDF report', false, false, NULL, 'GenerateFinalReportHandler', 600, 'sequential'),
('Finalize Test Report', 'Complete Report Finalization', 'COMPLETE', 6, 'Mark report as finalized', false, false, NULL, 'AutomatedActivityHandler', 60, 'sequential');

-- Update retry policies
UPDATE workflow_activity_templates
SET retry_policy = '{"max_attempts": 3, "initial_interval": 2, "max_interval": 60, "backoff": 2}'::json
WHERE activity_type IN ('TASK', 'START', 'COMPLETE')
AND is_manual = false;
"""


async def populate_templates():
    """Populate activity templates"""
    
    # Create async engine
    database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url)
    
    async with engine.begin() as conn:
        try:
            # Clear existing templates
            await conn.execute(text("DELETE FROM workflow_activity_templates"))
            logger.info("Cleared existing templates")
            
            # Insert templates one phase at a time
            templates = [
                # Planning Phase
                ('Planning', 'Start Planning Phase', 'START', 1, 'Initialize planning phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                ('Planning', 'Generate Attributes', 'TASK', 2, 'Generate test attributes using LLM', False, False, 'Tester', 'GenerateAttributesHandler', 300, 'sequential'),
                ('Planning', 'Review Generated Attributes', 'REVIEW', 3, 'Tester reviews and modifies generated attributes', True, False, 'Tester', 'ManualActivityHandler', 86400, 'sequential'),
                ('Planning', 'Submit for Approval', 'REVIEW', 4, 'Submit attributes for report owner approval', True, False, 'Tester', 'ManualActivityHandler', 3600, 'sequential'),
                ('Planning', 'Report Owner Approval', 'APPROVAL', 5, 'Report owner approves test attributes', True, False, 'Report Owner', 'ManualActivityHandler', 172800, 'sequential'),
                ('Planning', 'Complete Planning Phase', 'COMPLETE', 6, 'Finalize planning phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                
                # Data Profiling Phase
                ('Data Profiling', 'Start Data Profiling', 'START', 1, 'Initialize data profiling phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                ('Data Profiling', 'Upload Data Files', 'TASK', 2, 'Upload data files for profiling', True, False, 'Tester', 'ManualActivityHandler', 86400, 'sequential'),
                ('Data Profiling', 'Execute Data Profiling', 'TASK', 3, 'Analyze data patterns and generate insights', False, False, 'Tester', 'DataProfilingHandler', 1800, 'sequential'),
                ('Data Profiling', 'Review Profiling Results', 'REVIEW', 4, 'Review and validate profiling results', True, False, 'Tester', 'ManualActivityHandler', 43200, 'sequential'),
                ('Data Profiling', 'Complete Data Profiling', 'COMPLETE', 5, 'Finalize data profiling phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                
                # Scoping Phase
                ('Scoping', 'Start Scoping Phase', 'START', 1, 'Initialize scoping phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                ('Scoping', 'Execute Scoping', 'TASK', 2, 'Determine which attributes to test', False, False, 'Tester', 'ExecuteScopingHandler', 600, 'sequential'),
                ('Scoping', 'Review Scoping Results', 'REVIEW', 3, 'Review and adjust scoping decisions', True, False, 'Tester', 'ManualActivityHandler', 43200, 'sequential'),
                ('Scoping', 'Scoping Approval', 'APPROVAL', 4, 'Approve final scope', True, False, 'Report Owner', 'ManualActivityHandler', 86400, 'sequential'),
                ('Scoping', 'Complete Scoping Phase', 'COMPLETE', 5, 'Finalize scoping phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                
                # Sample Selection Phase
                ('Sample Selection', 'Start Sample Selection', 'START', 1, 'Initialize sample selection phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                ('Sample Selection', 'Generate Samples', 'TASK', 2, 'Generate test samples with LOB tagging', False, False, 'Tester', 'GenerateSamplesHandler', 600, 'sequential'),
                ('Sample Selection', 'Review and Tag Samples', 'TASK', 3, 'Review samples and ensure LOB tags are correct', True, False, 'Tester', 'ManualActivityHandler', 86400, 'sequential'),
                ('Sample Selection', 'Upload Additional Samples', 'TASK', 4, 'Upload any additional manual samples', True, True, 'Tester', 'ManualActivityHandler', 43200, 'sequential'),
                ('Sample Selection', 'Complete Sample Selection', 'COMPLETE', 5, 'Finalize sample selection phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                
                # Data Owner Identification Phase
                ('Data Owner Identification', 'Start Data Owner ID', 'START', 1, 'Initialize data owner identification phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                ('Data Owner Identification', 'Assign LOB Executives', 'TASK', 2, 'CDO assigns LOB executives based on sample tags', True, False, 'CDO', 'ManualActivityHandler', 86400, 'sequential'),
                ('Data Owner Identification', 'Assign Data Owners', 'TASK', 3, 'LOB executives assign data owners', True, False, 'Report Owner Executive', 'ManualActivityHandler', 86400, 'sequential'),
                ('Data Owner Identification', 'Assign Data Providers', 'TASK', 4, 'Data owners assign data providers', True, False, 'Data Owner', 'ManualActivityHandler', 86400, 'sequential'),
                ('Data Owner Identification', 'Complete Provider ID', 'COMPLETE', 5, 'Finalize data owner identification phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                
                # Request for Information Phase (Parallel)
                ('Request for Information', 'Start Request Info', 'START', 1, 'Initialize request for information phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                ('Request for Information', 'Send Data Request', 'TASK', 2, 'Send data upload request to data owner', False, False, None, 'SendDataRequestHandler', 300, 'parallel'),
                ('Request for Information', 'Upload Data', 'TASK', 3, 'Data owner uploads requested data', True, False, 'Data Owner', 'ManualActivityHandler', 259200, 'parallel'),
                ('Request for Information', 'Validate Data Upload', 'TASK', 4, 'Validate uploaded data completeness', False, False, None, 'ValidateDataUploadHandler', 600, 'parallel'),
                ('Request for Information', 'Generate Test Cases', 'TASK', 5, 'Generate test cases for uploaded data', False, False, None, 'GenerateTestCasesHandler', 900, 'parallel'),
                ('Request for Information', 'Data Upload Complete', 'COMPLETE', 6, 'Mark data upload as complete', False, False, None, 'AutomatedActivityHandler', 60, 'parallel'),
                
                # Test Execution Phase (Parallel)
                ('Test Execution', 'Start Test Execution', 'START', 1, 'Initialize test execution phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                ('Test Execution', 'Execute Tests', 'TASK', 2, 'Execute tests on uploaded document', False, False, None, 'ExecuteTestsHandler', 1800, 'parallel'),
                ('Test Execution', 'Review Test Results', 'REVIEW', 3, 'Review automated test results', True, True, 'Tester', 'ManualActivityHandler', 43200, 'parallel'),
                ('Test Execution', 'Document Test Evidence', 'TASK', 4, 'Document test execution evidence', True, False, 'Tester', 'ManualActivityHandler', 86400, 'parallel'),
                ('Test Execution', 'Complete Test Execution', 'COMPLETE', 5, 'Mark test execution as complete', False, False, None, 'AutomatedActivityHandler', 60, 'parallel'),
                
                # Observation Management Phase (Parallel)
                ('Observation Management', 'Start Observation Management', 'START', 1, 'Initialize observation management phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                ('Observation Management', 'Create Observations', 'TASK', 2, 'Create observations for test failures', False, False, None, 'CreateObservationsHandler', 600, 'parallel'),
                ('Observation Management', 'Review Observations', 'REVIEW', 3, 'Review and categorize observations', True, False, 'Tester', 'ManualActivityHandler', 86400, 'parallel'),
                ('Observation Management', 'Data Owner Response', 'TASK', 4, 'Data owner provides response to observations', True, False, 'Data Owner', 'ManualActivityHandler', 172800, 'parallel'),
                ('Observation Management', 'Finalize Observations', 'APPROVAL', 5, 'Finalize observation status', True, False, 'Tester', 'ManualActivityHandler', 43200, 'parallel'),
                ('Observation Management', 'Complete Observation Management', 'COMPLETE', 6, 'Mark observation management as complete', False, False, None, 'AutomatedActivityHandler', 60, 'parallel'),
                
                # Finalize Test Report Phase
                ('Finalize Test Report', 'Start Report Finalization', 'START', 1, 'Initialize report finalization phase', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
                ('Finalize Test Report', 'Generate Report Sections', 'TASK', 2, 'Generate test report sections', False, False, None, 'GenerateReportSectionsHandler', 1800, 'sequential'),
                ('Finalize Test Report', 'Review Report Draft', 'REVIEW', 3, 'Review and edit report draft', True, False, 'Tester', 'ManualActivityHandler', 86400, 'sequential'),
                ('Finalize Test Report', 'Quality Review', 'APPROVAL', 4, 'Quality review of test report', True, False, 'Test Manager', 'ManualActivityHandler', 86400, 'sequential'),
                ('Finalize Test Report', 'Generate Final Report', 'TASK', 5, 'Generate final PDF report', False, False, None, 'GenerateFinalReportHandler', 600, 'sequential'),
                ('Finalize Test Report', 'Complete Report Finalization', 'COMPLETE', 6, 'Mark report as finalized', False, False, None, 'AutomatedActivityHandler', 60, 'sequential'),
            ]
            
            # Insert all templates (using existing columns)
            insert_sql = """INSERT INTO workflow_activity_templates 
                (phase_name, activity_name, activity_type, activity_order, description, 
                 is_manual, is_optional, required_role, is_active)
                VALUES (:p1, :p2, :p3, :p4, :p5, :p6, :p7, :p8, :p9)"""
            
            for template in templates:
                await conn.execute(text(insert_sql), {
                    "p1": template[0], "p2": template[1], "p3": template[2],
                    "p4": template[3], "p5": template[4], "p6": template[5],
                    "p7": template[6], "p8": template[7], "p9": True  # is_active
                })
            
            logger.info(f"✅ Successfully populated {len(templates)} activity templates!")
            
            # Note: retry_policy column will be used when schema is updated
            
        except Exception as e:
            logger.error(f"Error populating templates: {e}")
            raise
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(populate_templates())