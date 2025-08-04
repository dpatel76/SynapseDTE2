"""Populate workflow activity templates and dependencies

Revision ID: populate_activity_templates
Revises: create_workflow_activities
Create Date: 2025-06-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'populate_activity_templates'
down_revision = 'create_workflow_activities'
branch_labels = None
depends_on = None

# Define tables for bulk insert
activity_templates = table('workflow_activity_templates',
    column('phase_name', sa.String),
    column('activity_name', sa.String),
    column('activity_type', sa.String),
    column('activity_order', sa.Integer),
    column('description', sa.Text),
    column('is_manual', sa.Boolean),
    column('is_optional', sa.Boolean),
    column('required_role', sa.String),
    column('auto_complete_on_event', sa.String),
    column('is_active', sa.Boolean)
)

activity_dependencies = table('workflow_activity_dependencies',
    column('phase_name', sa.String),
    column('activity_name', sa.String),
    column('depends_on_activity', sa.String),
    column('dependency_type', sa.String),
    column('is_active', sa.Boolean)
)


def upgrade():
    # Define activity templates for all phases
    templates_data = [
        # Planning Phase
        {'phase_name': 'Planning', 'activity_name': 'Start Planning Phase', 'activity_type': 'start', 'activity_order': 1, 
         'description': 'Initialize planning phase', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Planning', 'activity_name': 'Generate Attributes', 'activity_type': 'task', 'activity_order': 2,
         'description': 'Generate test attributes using LLM', 'is_manual': False, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Planning', 'activity_name': 'Review Attributes', 'activity_type': 'task', 'activity_order': 3,
         'description': 'Review and edit generated attributes', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Planning', 'activity_name': 'Tester Review', 'activity_type': 'review', 'activity_order': 4,
         'description': 'Submit for report owner review', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Planning', 'activity_name': 'Report Owner Approval', 'activity_type': 'approval', 'activity_order': 5,
         'description': 'Report owner approves attributes', 'is_manual': True, 'is_optional': False, 'required_role': 'Report Owner'},
        {'phase_name': 'Planning', 'activity_name': 'Complete Planning Phase', 'activity_type': 'complete', 'activity_order': 6,
         'description': 'Finalize planning phase', 'is_manual': False, 'is_optional': False, 'required_role': None},
        
        # Data Profiling Phase
        {'phase_name': 'Data Profiling', 'activity_name': 'Start Data Profiling', 'activity_type': 'start', 'activity_order': 1,
         'description': 'Initialize data profiling', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Data Profiling', 'activity_name': 'Profile Data Sources', 'activity_type': 'task', 'activity_order': 2,
         'description': 'Analyze data sources and patterns', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Data Profiling', 'activity_name': 'Document Findings', 'activity_type': 'task', 'activity_order': 3,
         'description': 'Document profiling results', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Data Profiling', 'activity_name': 'Complete Data Profiling', 'activity_type': 'complete', 'activity_order': 4,
         'description': 'Finalize data profiling', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        
        # Scoping Phase
        {'phase_name': 'Scoping', 'activity_name': 'Start Scoping Phase', 'activity_type': 'start', 'activity_order': 1,
         'description': 'Initialize scoping phase', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Scoping', 'activity_name': 'Define Scope', 'activity_type': 'task', 'activity_order': 2,
         'description': 'Define testing scope and boundaries', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Scoping', 'activity_name': 'Tester Review', 'activity_type': 'review', 'activity_order': 3,
         'description': 'Submit scope for approval', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Scoping', 'activity_name': 'Report Owner Approval', 'activity_type': 'approval', 'activity_order': 4,
         'description': 'Report owner approves scope', 'is_manual': True, 'is_optional': False, 'required_role': 'Report Owner'},
        {'phase_name': 'Scoping', 'activity_name': 'Complete Scoping Phase', 'activity_type': 'complete', 'activity_order': 5,
         'description': 'Finalize scoping phase', 'is_manual': False, 'is_optional': False, 'required_role': None},
        
        # Sample Selection Phase
        {'phase_name': 'Sample Selection', 'activity_name': 'Start Sample Selection', 'activity_type': 'start', 'activity_order': 1,
         'description': 'Initialize sample selection', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Sample Selection', 'activity_name': 'Generate Samples', 'activity_type': 'task', 'activity_order': 2,
         'description': 'Generate test samples', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Sample Selection', 'activity_name': 'Review Samples', 'activity_type': 'task', 'activity_order': 3,
         'description': 'Review and adjust samples', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Sample Selection', 'activity_name': 'Complete Sample Selection', 'activity_type': 'complete', 'activity_order': 4,
         'description': 'Finalize sample selection', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        
        # Data Provider ID Phase
        {'phase_name': 'Data Provider ID', 'activity_name': 'Start Data Provider ID', 'activity_type': 'start', 'activity_order': 1,
         'description': 'Initialize data provider identification', 'is_manual': True, 'is_optional': False, 'required_role': 'CDO'},
        {'phase_name': 'Data Provider ID', 'activity_name': 'LOB Executive Assignment', 'activity_type': 'task', 'activity_order': 2,
         'description': 'Assign LOB executives', 'is_manual': True, 'is_optional': False, 'required_role': 'CDO'},
        {'phase_name': 'Data Provider ID', 'activity_name': 'Data Owner Assignment', 'activity_type': 'task', 'activity_order': 3,
         'description': 'Assign data owners', 'is_manual': True, 'is_optional': False, 'required_role': 'Report Owner Executive'},
        {'phase_name': 'Data Provider ID', 'activity_name': 'Data Provider Assignment', 'activity_type': 'task', 'activity_order': 4,
         'description': 'Assign data providers', 'is_manual': True, 'is_optional': False, 'required_role': 'Data Owner'},
        {'phase_name': 'Data Provider ID', 'activity_name': 'Complete Provider ID', 'activity_type': 'complete', 'activity_order': 5,
         'description': 'Complete provider identification', 'is_manual': False, 'is_optional': False, 'required_role': None},
        
        # Data Owner ID Phase (similar structure)
        {'phase_name': 'Data Owner ID', 'activity_name': 'Start Data Owner ID', 'activity_type': 'start', 'activity_order': 1,
         'description': 'Initialize data owner identification', 'is_manual': True, 'is_optional': False, 'required_role': 'CDO'},
        {'phase_name': 'Data Owner ID', 'activity_name': 'Assign LOB Executives', 'activity_type': 'task', 'activity_order': 2,
         'description': 'CDO assigns LOB executives', 'is_manual': True, 'is_optional': False, 'required_role': 'CDO'},
        {'phase_name': 'Data Owner ID', 'activity_name': 'Assign Data Owners', 'activity_type': 'task', 'activity_order': 3,
         'description': 'Executives assign data owners', 'is_manual': True, 'is_optional': False, 'required_role': 'Report Owner Executive'},
        {'phase_name': 'Data Owner ID', 'activity_name': 'Complete Data Owner ID', 'activity_type': 'complete', 'activity_order': 4,
         'description': 'Complete data owner identification', 'is_manual': False, 'is_optional': False, 'required_role': None},
        
        # Request Info Phase
        {'phase_name': 'Request Info', 'activity_name': 'Start Request Info', 'activity_type': 'start', 'activity_order': 1,
         'description': 'Initialize request info phase', 'is_manual': False, 'is_optional': False, 'required_role': None,
         'auto_complete_on_event': 'sample_selection_complete'},
        {'phase_name': 'Request Info', 'activity_name': 'Generate Test Cases', 'activity_type': 'task', 'activity_order': 2,
         'description': 'Generate test cases FROM cycle_report_sample_selection_samples', 'is_manual': False, 'is_optional': False, 'required_role': None},
        {'phase_name': 'Request Info', 'activity_name': 'Data Provider Upload', 'activity_type': 'task', 'activity_order': 3,
         'description': 'Data providers upload documents', 'is_manual': True, 'is_optional': False, 'required_role': 'Data Provider'},
        {'phase_name': 'Request Info', 'activity_name': 'Complete Request Info', 'activity_type': 'complete', 'activity_order': 4,
         'description': 'Complete request info phase', 'is_manual': False, 'is_optional': False, 'required_role': None},
        
        # Test Execution Phase
        {'phase_name': 'Test Execution', 'activity_name': 'Start Test Execution', 'activity_type': 'start', 'activity_order': 1,
         'description': 'Initialize test execution', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Test Execution', 'activity_name': 'Execute Tests', 'activity_type': 'task', 'activity_order': 2,
         'description': 'Execute test cases', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Test Execution', 'activity_name': 'Document Results', 'activity_type': 'task', 'activity_order': 3,
         'description': 'Document test results', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Test Execution', 'activity_name': 'Complete Test Execution', 'activity_type': 'complete', 'activity_order': 4,
         'description': 'Complete test execution', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        
        # Observation Management Phase
        {'phase_name': 'Observation Management', 'activity_name': 'Start Observations', 'activity_type': 'start', 'activity_order': 1,
         'description': 'Initialize observation management', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Observation Management', 'activity_name': 'Create Observations', 'activity_type': 'task', 'activity_order': 2,
         'description': 'Create and document observations', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Observation Management', 'activity_name': 'Data Provider Response', 'activity_type': 'task', 'activity_order': 3,
         'description': 'Data providers respond to observations', 'is_manual': True, 'is_optional': True, 'required_role': 'Data Provider'},
        {'phase_name': 'Observation Management', 'activity_name': 'Finalize Observations', 'activity_type': 'task', 'activity_order': 4,
         'description': 'Finalize all observations', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Observation Management', 'activity_name': 'Complete Observations', 'activity_type': 'complete', 'activity_order': 5,
         'description': 'Complete observation management', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        
        # Test Report Phase
        {'phase_name': 'Test Report', 'activity_name': 'Start Test Report', 'activity_type': 'start', 'activity_order': 1,
         'description': 'Initialize test report generation', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Test Report', 'activity_name': 'Generate Report', 'activity_type': 'task', 'activity_order': 2,
         'description': 'Generate test report', 'is_manual': True, 'is_optional': False, 'required_role': 'Tester'},
        {'phase_name': 'Test Report', 'activity_name': 'Review Report', 'activity_type': 'review', 'activity_order': 3,
         'description': 'Review generated report', 'is_manual': True, 'is_optional': False, 'required_role': 'Test Manager'},
        {'phase_name': 'Test Report', 'activity_name': 'Approve Report', 'activity_type': 'approval', 'activity_order': 4,
         'description': 'Approve final report', 'is_manual': True, 'is_optional': False, 'required_role': 'Report Owner'},
        {'phase_name': 'Test Report', 'activity_name': 'Complete Test Report', 'activity_type': 'complete', 'activity_order': 5,
         'description': 'Complete test report phase', 'is_manual': False, 'is_optional': False, 'required_role': None},
    ]
    
    # Insert activity templates
    op.bulk_insert(activity_templates, templates_data)
    
    # Define activity dependencies
    dependencies_data = [
        # Planning Phase Dependencies
        {'phase_name': 'Planning', 'activity_name': 'Generate Attributes', 'depends_on_activity': 'Start Planning Phase', 'dependency_type': 'completion'},
        {'phase_name': 'Planning', 'activity_name': 'Review Attributes', 'depends_on_activity': 'Generate Attributes', 'dependency_type': 'completion'},
        {'phase_name': 'Planning', 'activity_name': 'Tester Review', 'depends_on_activity': 'Review Attributes', 'dependency_type': 'completion'},
        {'phase_name': 'Planning', 'activity_name': 'Report Owner Approval', 'depends_on_activity': 'Tester Review', 'dependency_type': 'completion'},
        {'phase_name': 'Planning', 'activity_name': 'Complete Planning Phase', 'depends_on_activity': 'Report Owner Approval', 'dependency_type': 'approval'},
        
        # Data Profiling Dependencies
        {'phase_name': 'Data Profiling', 'activity_name': 'Profile Data Sources', 'depends_on_activity': 'Start Data Profiling', 'dependency_type': 'completion'},
        {'phase_name': 'Data Profiling', 'activity_name': 'Document Findings', 'depends_on_activity': 'Profile Data Sources', 'dependency_type': 'completion'},
        {'phase_name': 'Data Profiling', 'activity_name': 'Complete Data Profiling', 'depends_on_activity': 'Document Findings', 'dependency_type': 'completion'},
        
        # Scoping Phase Dependencies
        {'phase_name': 'Scoping', 'activity_name': 'Define Scope', 'depends_on_activity': 'Start Scoping Phase', 'dependency_type': 'completion'},
        {'phase_name': 'Scoping', 'activity_name': 'Tester Review', 'depends_on_activity': 'Define Scope', 'dependency_type': 'completion'},
        {'phase_name': 'Scoping', 'activity_name': 'Report Owner Approval', 'depends_on_activity': 'Tester Review', 'dependency_type': 'completion'},
        {'phase_name': 'Scoping', 'activity_name': 'Complete Scoping Phase', 'depends_on_activity': 'Report Owner Approval', 'dependency_type': 'approval'},
        
        # Sample Selection Dependencies
        {'phase_name': 'Sample Selection', 'activity_name': 'Generate Samples', 'depends_on_activity': 'Start Sample Selection', 'dependency_type': 'completion'},
        {'phase_name': 'Sample Selection', 'activity_name': 'Review Samples', 'depends_on_activity': 'Generate Samples', 'dependency_type': 'completion'},
        {'phase_name': 'Sample Selection', 'activity_name': 'Complete Sample Selection', 'depends_on_activity': 'Review Samples', 'dependency_type': 'completion'},
        
        # Data Provider ID Dependencies
        {'phase_name': 'Data Provider ID', 'activity_name': 'LOB Executive Assignment', 'depends_on_activity': 'Start Data Provider ID', 'dependency_type': 'completion'},
        {'phase_name': 'Data Provider ID', 'activity_name': 'Data Owner Assignment', 'depends_on_activity': 'LOB Executive Assignment', 'dependency_type': 'completion'},
        {'phase_name': 'Data Provider ID', 'activity_name': 'Data Provider Assignment', 'depends_on_activity': 'Data Owner Assignment', 'dependency_type': 'completion'},
        {'phase_name': 'Data Provider ID', 'activity_name': 'Complete Provider ID', 'depends_on_activity': 'Data Provider Assignment', 'dependency_type': 'completion'},
        
        # Data Owner ID Dependencies
        {'phase_name': 'Data Owner ID', 'activity_name': 'Assign LOB Executives', 'depends_on_activity': 'Start Data Owner ID', 'dependency_type': 'completion'},
        {'phase_name': 'Data Owner ID', 'activity_name': 'Assign Data Owners', 'depends_on_activity': 'Assign LOB Executives', 'dependency_type': 'completion'},
        {'phase_name': 'Data Owner ID', 'activity_name': 'Complete Data Owner ID', 'depends_on_activity': 'Assign Data Owners', 'dependency_type': 'completion'},
        
        # Request Info Dependencies
        {'phase_name': 'Request Info', 'activity_name': 'Generate Test Cases', 'depends_on_activity': 'Start Request Info', 'dependency_type': 'completion'},
        {'phase_name': 'Request Info', 'activity_name': 'Data Provider Upload', 'depends_on_activity': 'Generate Test Cases', 'dependency_type': 'completion'},
        {'phase_name': 'Request Info', 'activity_name': 'Complete Request Info', 'depends_on_activity': 'Data Provider Upload', 'dependency_type': 'any'},
        
        # Test Execution Dependencies
        {'phase_name': 'Test Execution', 'activity_name': 'Execute Tests', 'depends_on_activity': 'Start Test Execution', 'dependency_type': 'completion'},
        {'phase_name': 'Test Execution', 'activity_name': 'Document Results', 'depends_on_activity': 'Execute Tests', 'dependency_type': 'any'},
        {'phase_name': 'Test Execution', 'activity_name': 'Complete Test Execution', 'depends_on_activity': 'Document Results', 'dependency_type': 'completion'},
        
        # Observation Management Dependencies
        {'phase_name': 'Observation Management', 'activity_name': 'Create Observations', 'depends_on_activity': 'Start Observations', 'dependency_type': 'completion'},
        {'phase_name': 'Observation Management', 'activity_name': 'Data Provider Response', 'depends_on_activity': 'Create Observations', 'dependency_type': 'any'},
        {'phase_name': 'Observation Management', 'activity_name': 'Finalize Observations', 'depends_on_activity': 'Create Observations', 'dependency_type': 'any'},
        {'phase_name': 'Observation Management', 'activity_name': 'Complete Observations', 'depends_on_activity': 'Finalize Observations', 'dependency_type': 'completion'},
        
        # Test Report Dependencies
        {'phase_name': 'Test Report', 'activity_name': 'Generate Report', 'depends_on_activity': 'Start Test Report', 'dependency_type': 'completion'},
        {'phase_name': 'Test Report', 'activity_name': 'Review Report', 'depends_on_activity': 'Generate Report', 'dependency_type': 'completion'},
        {'phase_name': 'Test Report', 'activity_name': 'Approve Report', 'depends_on_activity': 'Review Report', 'dependency_type': 'completion'},
        {'phase_name': 'Test Report', 'activity_name': 'Complete Test Report', 'depends_on_activity': 'Approve Report', 'dependency_type': 'approval'},
    ]
    
    # Insert dependencies
    op.bulk_insert(activity_dependencies, dependencies_data)


def downgrade():
    # Clear all data
    op.execute("DELETE FROM workflow_activity_dependencies")
    op.execute("DELETE FROM workflow_activity_templates")