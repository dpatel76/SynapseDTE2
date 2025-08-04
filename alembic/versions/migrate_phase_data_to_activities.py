"""Migrate existing phase_data to workflow_activities table

Revision ID: migrate_phase_data
Revises: populate_activity_templates
Create Date: 2025-06-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
import json
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'migrate_phase_data'
down_revision = 'populate_activity_templates'
branch_labels = None
depends_on = None


def upgrade():
    # Create a connection to execute raw SQL
    conn = op.get_bind()
    
    # Get all workflow phases with phase_data
    result = conn.execute(text("""
        SELECT phase_id, cycle_id, report_id, phase_name, phase_data, 
               actual_start_date, actual_end_date, started_by, completed_by
        FROM workflow_phases 
        WHERE phase_data IS NOT NULL AND phase_data != '{}'::jsonb
    """))
    
    for row in result:
        phase_id, cycle_id, report_id, phase_name, phase_data, start_date, end_date, started_by, completed_by = row
        
        if not phase_data:
            continue
            
        # Parse the phase_data JSON
        data = phase_data if isinstance(phase_data, dict) else json.loads(phase_data)
        activities = data.get('activities', {})
        
        if not activities:
            continue
        
        # Get activity templates for this phase to maintain proper order
        templates = conn.execute(text("""
            SELECT activity_name, activity_type, activity_order, is_manual, is_optional, required_role
            FROM workflow_activity_templates
            WHERE phase_name = :phase_name AND is_active = true
            ORDER BY activity_order
        """), {'phase_name': phase_name})
        
        template_map = {t[0]: {'type': t[1], 'order': t[2], 'is_manual': t[3], 'is_optional': t[4], 'required_role': t[5]} 
                       for t in templates}
        
        # Process each activity
        for activity_name, activity_data in activities.items():
            # Get template info
            template = template_map.get(activity_name, {})
            if not template:
                # Activity not in template, skip or use defaults
                print(f"Warning: Activity '{activity_name}' not found in templates for phase '{phase_name}'")
                continue
            
            # Map old state to new status
            old_state = activity_data.get('state', 'NOT_STARTED')
            status_map = {
                'NOT_STARTED': 'not_started',
                'IN_PROGRESS': 'in_progress',
                'COMPLETED': 'completed',
                'REVISION_REQUESTED': 'revision_requested'
            }
            status = status_map.get(old_state, 'not_started')
            
            # Extract timestamps
            started_at = activity_data.get('started_at')
            completed_at = activity_data.get('completed_at')
            
            # Convert string timestamps to datetime if needed
            if started_at and isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            if completed_at and isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            
            # Determine can_start and can_complete based on status
            can_start = status == 'not_started'
            can_complete = status == 'in_progress'
            
            # Insert into workflow_activities
            conn.execute(text("""
                INSERT INTO workflow_activities (
                    cycle_id, report_id, phase_name, activity_name, activity_type, 
                    activity_order, status, can_start, can_complete, is_manual, is_optional,
                    started_at, started_by, completed_at, completed_by, metadata,
                    created_at, updated_at
                ) VALUES (
                    :cycle_id, :report_id, :phase_name, :activity_name, :activity_type,
                    :activity_order, :status, :can_start, :can_complete, :is_manual, :is_optional,
                    :started_at, :started_by, :completed_at, :completed_by, :metadata,
                    NOW(), NOW()
                )
                ON CONFLICT (cycle_id, report_id, phase_name, activity_name) DO UPDATE SET
                    status = EXCLUDED.status,
                    started_at = EXCLUDED.started_at,
                    started_by = EXCLUDED.started_by,
                    completed_at = EXCLUDED.completed_at,
                    completed_by = EXCLUDED.completed_by,
                    updated_at = NOW()
            """), {
                'cycle_id': cycle_id,
                'report_id': report_id,
                'phase_name': phase_name,
                'activity_name': activity_name,
                'activity_type': template['type'],
                'activity_order': template['order'],
                'status': status,
                'can_start': can_start,
                'can_complete': can_complete,
                'is_manual': template['is_manual'],
                'is_optional': template['is_optional'],
                'started_at': started_at,
                'started_by': activity_data.get('started_by'),
                'completed_at': completed_at,
                'completed_by': activity_data.get('completed_by'),
                'metadata': json.dumps(activity_data.get('metadata', {})) if activity_data.get('metadata') else None
            })
            
            # Add history entry for completed activities
            if status == 'completed' and completed_at:
                activity_id = conn.execute(text("""
                    SELECT activity_id FROM workflow_activities 
                    WHERE cycle_id = :cycle_id AND report_id = :report_id 
                    AND phase_name = :phase_name AND activity_name = :activity_name
                """), {
                    'cycle_id': cycle_id,
                    'report_id': report_id,
                    'phase_name': phase_name,
                    'activity_name': activity_name
                }).scalar()
                
                if activity_id:
                    conn.execute(text("""
                        INSERT INTO workflow_activity_history (
                            activity_id, cycle_id, report_id, phase_name, activity_name,
                            from_status, to_status, changed_by, changed_at, change_reason
                        ) VALUES (
                            :activity_id, :cycle_id, :report_id, :phase_name, :activity_name,
                            'not_started', 'completed', :changed_by, :changed_at, 'Migrated from phase_data'
                        )
                    """), {
                        'activity_id': activity_id,
                        'cycle_id': cycle_id,
                        'report_id': report_id,
                        'phase_name': phase_name,
                        'activity_name': activity_name,
                        'changed_by': activity_data.get('completed_by', started_by),
                        'changed_at': completed_at
                    })
    
    # Update workflow_activities to ensure proper can_start/can_complete flags based on dependencies
    conn.execute(text("""
        WITH activity_deps AS (
            SELECT 
                wa.activity_id,
                wa.cycle_id,
                wa.report_id,
                wa.phase_name,
                wa.activity_name,
                wa.status,
                dep.depends_on_activity,
                dep_wa.status as dep_status
            FROM workflow_activities wa
            LEFT JOIN workflow_activity_dependencies dep 
                ON wa.phase_name = dep.phase_name 
                AND wa.activity_name = dep.activity_name
                AND dep.is_active = true
            LEFT JOIN workflow_activities dep_wa
                ON wa.cycle_id = dep_wa.cycle_id
                AND wa.report_id = dep_wa.report_id
                AND wa.phase_name = dep_wa.phase_name
                AND dep.depends_on_activity = dep_wa.activity_name
        )
        UPDATE workflow_activities wa
        SET 
            can_start = CASE 
                WHEN wa.status != 'not_started' THEN false
                WHEN NOT EXISTS (
                    SELECT 1 FROM activity_deps ad 
                    WHERE ad.activity_id = wa.activity_id 
                    AND ad.dep_status != 'completed'
                ) THEN true
                ELSE false
            END,
            can_complete = CASE
                WHEN wa.status = 'in_progress' THEN true
                ELSE false
            END,
            updated_at = NOW()
        WHERE wa.status IN ('not_started', 'in_progress')
    """))


def downgrade():
    # This migration is not easily reversible
    # We would need to reconstruct the phase_data JSON from the workflow_activities table
    pass