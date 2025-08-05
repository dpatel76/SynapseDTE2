"""fix_workflow_activities_from_reference

Revision ID: fix_workflow_activities_001
Revises: sync_rbac_perms_001
Create Date: 2025-08-04 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'fix_workflow_activities_001'
down_revision = 'sync_rbac_perms_001'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    
    # First, delete all existing workflow activities for cycle 2, report 3
    conn.execute(text("""
        DELETE FROM workflow_activities 
        WHERE cycle_id = 2 AND report_id = 3
    """))
    
    # Now insert the correct activities based on reference database
    activities = [
        # Planning Phase
        ('Planning', 1, 'Start Planning Phase', 'START', False, True),
        ('Planning', 2, 'Load Attributes', 'TASK', False, True),
        ('Planning', 3, 'Add Data Source', 'TASK', True, True),  # optional
        ('Planning', 4, 'Map PDEs', 'TASK', True, True),  # optional
        ('Planning', 5, 'Review & Approve Attributes', 'REVIEW', False, True),
        ('Planning', 6, 'Complete Planning Phase', 'COMPLETE', False, False),
        
        # Scoping Phase
        ('Scoping', 1, 'Start Scoping Phase', 'START', False, False),
        ('Scoping', 2, 'Generate LLM Recommendations', 'TASK', False, False),
        ('Scoping', 3, 'Make Scoping Decisions', 'TASK', False, True),
        ('Scoping', 4, 'Report Owner Approval', 'APPROVAL', False, True),
        ('Scoping', 5, 'Complete Scoping Phase', 'COMPLETE', False, False),
        
        # Data Profiling Phase
        ('Data Profiling', 1, 'Start Data Profiling Phase', 'START', False, False),
        ('Data Profiling', 2, 'Upload Data Files', 'TASK', False, True),
        ('Data Profiling', 3, 'Generate LLM Data Profiling Rules', 'TASK', False, True),
        ('Data Profiling', 4, 'Review Profiling Rules', 'REVIEW', False, True),
        ('Data Profiling', 5, 'Report Owner Rule Approval', 'APPROVAL', False, True),
        ('Data Profiling', 6, 'Execute Data Profiling', 'TASK', False, True),
        ('Data Profiling', 7, 'Complete Data Profiling Phase', 'COMPLETE', False, False),
        
        # Data Provider ID Phase
        ('Data Provider ID', 1, 'Start Data Provider ID Phase', 'START', False, False),
        ('Data Provider ID', 2, 'Assign Data Providers', 'TASK', False, True),
        ('Data Provider ID', 3, 'Review Provider Assignments', 'TASK', False, True),
        ('Data Provider ID', 4, 'Complete Data Provider ID Phase', 'COMPLETE', False, False),
        
        # Request Info Phase
        ('Request Info', 1, 'Start Request Info Phase', 'START', False, False),
        ('Request Info', 2, 'Create Test Cases', 'TASK', False, True),
        ('Request Info', 3, 'Notify Data Providers', 'TASK', False, True),
        ('Request Info', 4, 'Collect Documents', 'TASK', False, True),
        ('Request Info', 5, 'Review Submissions', 'REVIEW', False, True),
        ('Request Info', 6, 'Complete Request Info Phase', 'COMPLETE', False, False),
        
        # Sample Selection Phase
        ('Sample Selection', 1, 'Start Sample Selection', 'START', False, False),
        ('Sample Selection', 2, 'Generate Samples', 'TASK', False, True),
        ('Sample Selection', 3, 'Review Samples', 'REVIEW', False, True),
        ('Sample Selection', 4, 'Approve Samples', 'APPROVAL', False, True),
        ('Sample Selection', 5, 'Complete Sample Selection', 'COMPLETE', False, False),
        
        # Test Execution Phase (renamed from Testing)
        ('Test Execution', 1, 'Start Test Execution Phase', 'START', False, False),
        ('Test Execution', 2, 'Load Test Cases', 'TASK', False, True),
        ('Test Execution', 3, 'Execute Tests', 'TASK', False, True),
        ('Test Execution', 4, 'Complete Test Execution', 'COMPLETE', False, False),
        
        # Observations Phase
        ('Observations', 1, 'Start Observations Phase', 'START', False, False),
        ('Observations', 2, 'Review Test Results', 'TASK', False, True),
        ('Observations', 3, 'Manage Observations', 'TASK', False, True),
        ('Observations', 4, 'Complete Observations', 'COMPLETE', False, False),
        
        # Finalize Test Report Phase
        ('Finalize Test Report', 1, 'Start Finalize Phase', 'START', False, False),
        ('Finalize Test Report', 2, 'Generate Report', 'TASK', False, True),
        ('Finalize Test Report', 3, 'Review Report', 'REVIEW', False, True),
        ('Finalize Test Report', 4, 'Approve Report', 'APPROVAL', False, True),
        ('Finalize Test Report', 5, 'Complete Report', 'COMPLETE', False, False),
    ]
    
    # Get the phase_id for each phase
    for phase_name, activity_order, activity_name, activity_type, is_optional, is_manual in activities:
        # Get phase_id
        phase_result = conn.execute(text("""
            SELECT phase_id FROM workflow_phases 
            WHERE cycle_id = 2 AND report_id = 3 AND phase_name = :phase_name
        """), {"phase_name": phase_name}).fetchone()
        
        if phase_result:
            phase_id = phase_result[0]
            
            # Insert workflow activity
            conn.execute(text("""
                INSERT INTO workflow_activities (
                    cycle_id, report_id, phase_id, phase_name, activity_name, 
                    activity_type, activity_order, status, can_start, can_complete,
                    is_manual, is_optional, metadata, created_at, updated_at
                ) VALUES (
                    2, 3, :phase_id, :phase_name, :activity_name,
                    :activity_type, :activity_order, 'NOT_STARTED', 
                    :can_start, false, :is_manual, :is_optional, 
                    :metadata, NOW(), NOW()
                )
            """), {
                "phase_id": phase_id,
                "phase_name": phase_name,
                "activity_name": activity_name,
                "activity_type": activity_type,
                "activity_order": activity_order,
                "can_start": activity_order == 1,  # Only first activity can start
                "is_manual": is_manual,
                "is_optional": is_optional,
                "metadata": '{"button_text": "Start"}' if activity_order == 1 else '{}'
            })

def downgrade():
    # Revert to previous state if needed
    pass
