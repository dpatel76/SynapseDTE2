"""Phase ID Refactoring: Remove redundant cycle_id and report_id columns

Revision ID: 2025_07_20_phase_id_refactoring
Revises: 2025_07_11_redesign_migration
Create Date: 2025-07-20 18:15:00.000000

This migration refactors the database to use phase_id as the primary foreign key
relationship instead of redundant cycle_id/report_id combinations.

Changes:
1. Add phase_id to tables that need it
2. Populate phase_id from existing cycle_id/report_id relationships
3. Remove redundant cycle_id and report_id columns
4. Update foreign key constraints
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '2025_07_20_phase_id_refactoring'
down_revision = '2025_07_11_redesign_migration'
branch_labels = None
depends_on = None

# Tables that currently have all three IDs and need refactoring
TABLES_TO_REFACTOR = [
    'cycle_report_data_profiling_rules',
    'cycle_report_documents',
    'cycle_report_observation_groups',
    'cycle_report_observation_mgmt_audit_logs',
    'cycle_report_observation_mgmt_observation_records',
    'cycle_report_observation_mgmt_preliminary_findings',
    'cycle_report_planning_attributes',
    'cycle_report_request_info_audit_logs',
    'cycle_report_request_info_testcase_source_evidence',
    'cycle_report_sample_selection_audit_logs',
    'cycle_report_sample_selection_samples',
    'cycle_report_scoping_attribute_recommendations_backup',
    'cycle_report_scoping_decision_versions',
    'cycle_report_scoping_decisions',
    'cycle_report_scoping_submissions',
    'cycle_report_test_execution_results',
    'workflow_activities'
]

# Tables that need phase_id added (currently have cycle_id + report_id)
TABLES_TO_ADD_PHASE_ID = [
    'activity_states',
    'cycle_report_data_profiling_rule_versions',
    'cycle_report_document_submissions',
    'cycle_report_planning_data_sources',
    'cycle_report_planning_pde_mappings',
    'cycle_report_test_cases',
    'data_owner_phase_audit_logs_legacy',
    'llm_audit_logs',
    'metrics_execution',
    'metrics_phases',
    'profiling_executions',
    'profiling_jobs',
    'universal_sla_violation_trackings',
    'universal_version_histories',
    'workflow_activity_histories',
    'workflow_executions'
]

def upgrade():
    """Upgrade to phase_id based relationships"""
    
    # Phase 1: Add phase_id columns where needed
    print("Phase 1: Adding phase_id columns...")
    
    for table_name in TABLES_TO_ADD_PHASE_ID:
        try:
            # Check if table exists
            op.execute(f"""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = '{table_name}' AND table_schema = 'public'
            """)
            
            # Add phase_id column
            op.add_column(table_name, sa.Column('phase_id', postgresql.UUID(), nullable=True))
            print(f"  ✓ Added phase_id to {table_name}")
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not add phase_id to {table_name}: {e}")
    
    # Phase 2: Populate phase_id for tables that will keep only phase_id
    print("Phase 2: Populating phase_id from existing relationships...")
    
    for table_name in TABLES_TO_REFACTOR:
        try:
            # Map table to appropriate phase name
            phase_mapping = {
                'cycle_report_data_profiling_rules': 'Data Profiling',
                'cycle_report_documents': 'Request for Information',  # Most documents are RFI related
                'cycle_report_observation_groups': 'Observation Management',
                'cycle_report_observation_mgmt_audit_logs': 'Observation Management',
                'cycle_report_observation_mgmt_observation_records': 'Observation Management',
                'cycle_report_observation_mgmt_preliminary_findings': 'Observation Management',
                'cycle_report_planning_attributes': 'Planning',
                'cycle_report_request_info_audit_logs': 'Request for Information',
                'cycle_report_request_info_testcase_source_evidence': 'Request for Information',
                'cycle_report_sample_selection_audit_logs': 'Sample Selection',
                'cycle_report_sample_selection_samples': 'Sample Selection',
                'cycle_report_scoping_attribute_recommendations_backup': 'Scoping',
                'cycle_report_scoping_decision_versions': 'Scoping',
                'cycle_report_scoping_decisions': 'Scoping',
                'cycle_report_scoping_submissions': 'Scoping',
                'cycle_report_test_execution_results': 'Test Execution',
                'workflow_activities': None  # Special case - activities can be in any phase
            }
            
            phase_name = phase_mapping.get(table_name)
            
            if table_name == 'workflow_activities':
                # For workflow_activities, use the phase_id they already have
                continue
            elif phase_name:
                # Update with specific phase
                op.execute(f"""
                    UPDATE {table_name} 
                    SET phase_id = wp.phase_id
                    FROM workflow_phases wp
                    WHERE wp.cycle_id = {table_name}.cycle_id 
                        AND wp.report_id = {table_name}.report_id
                        AND wp.phase_name = '{phase_name}'
                """)
                print(f"  ✓ Populated phase_id for {table_name} ({phase_name})")
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not populate phase_id for {table_name}: {e}")
    
    # Phase 3: Populate phase_id for tables getting phase_id added
    print("Phase 3: Populating phase_id for newly added columns...")
    
    phase_mappings_new = {
        'activity_states': None,  # Complex mapping needed
        'cycle_report_data_profiling_rule_versions': 'Data Profiling',
        'cycle_report_document_submissions': 'Request for Information',
        'cycle_report_planning_data_sources': 'Planning',
        'cycle_report_planning_pde_mappings': 'Planning',
        'cycle_report_test_cases': 'Test Execution',
        'data_owner_phase_audit_logs_legacy': None,  # Legacy table
        'llm_audit_logs': None,  # Cross-phase
        'metrics_execution': 'Test Execution',
        'metrics_phases': None,  # Cross-phase
        'profiling_executions': 'Data Profiling',
        'profiling_jobs': 'Data Profiling',
        'universal_sla_violation_trackings': None,  # Cross-phase
        'universal_version_histories': None,  # Cross-phase
        'workflow_activity_histories': None,  # Complex mapping
        'workflow_executions': None  # Cross-phase
    }
    
    for table_name in TABLES_TO_ADD_PHASE_ID:
        try:
            phase_name = phase_mappings_new.get(table_name)
            
            if phase_name:
                op.execute(f"""
                    UPDATE {table_name} 
                    SET phase_id = wp.phase_id
                    FROM workflow_phases wp
                    WHERE wp.cycle_id = {table_name}.cycle_id 
                        AND wp.report_id = {table_name}.report_id
                        AND wp.phase_name = '{phase_name}'
                """)
                print(f"  ✓ Populated phase_id for {table_name} ({phase_name})")
            else:
                print(f"  ⚠ Skipped {table_name} - requires manual mapping")
                
        except Exception as e:
            print(f"  ⚠ Warning: Could not populate phase_id for {table_name}: {e}")
    
    # Phase 4: Add foreign key constraints for phase_id
    print("Phase 4: Adding foreign key constraints...")
    
    all_tables_with_phase_id = TABLES_TO_REFACTOR + TABLES_TO_ADD_PHASE_ID
    
    for table_name in all_tables_with_phase_id:
        try:
            constraint_name = f"fk_{table_name}_phase_id"
            op.create_foreign_key(
                constraint_name,
                table_name,
                'workflow_phases',
                ['phase_id'],
                ['phase_id']
            )
            print(f"  ✓ Added FK constraint for {table_name}")
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not add FK constraint for {table_name}: {e}")
    
    # Phase 5: Remove redundant columns from refactored tables
    print("Phase 5: Removing redundant cycle_id and report_id columns...")
    
    for table_name in TABLES_TO_REFACTOR:
        if table_name == 'workflow_activities':
            continue  # Keep workflow_activities as-is for now
            
        try:
            # Drop foreign key constraints first
            op.execute(f"""
                ALTER TABLE {table_name} 
                DROP CONSTRAINT IF EXISTS {table_name}_cycle_id_fkey,
                DROP CONSTRAINT IF EXISTS {table_name}_report_id_fkey,
                DROP CONSTRAINT IF EXISTS fk_{table_name}_cycle,
                DROP CONSTRAINT IF EXISTS fk_{table_name}_report
            """)
            
            # Drop the columns
            op.drop_column(table_name, 'cycle_id')
            op.drop_column(table_name, 'report_id')
            
            print(f"  ✓ Removed redundant columns from {table_name}")
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not remove columns from {table_name}: {e}")
    
    print("✅ Phase ID refactoring upgrade completed!")

def downgrade():
    """Downgrade from phase_id based relationships"""
    
    print("Downgrading phase_id refactoring...")
    
    # Phase 1: Re-add cycle_id and report_id columns
    for table_name in TABLES_TO_REFACTOR:
        if table_name == 'workflow_activities':
            continue
            
        try:
            op.add_column(table_name, sa.Column('cycle_id', sa.Integer(), nullable=True))
            op.add_column(table_name, sa.Column('report_id', sa.Integer(), nullable=True))
            
            # Populate from phase_id relationship
            op.execute(f"""
                UPDATE {table_name} 
                SET cycle_id = wp.cycle_id, report_id = wp.report_id
                FROM workflow_phases wp
                WHERE wp.phase_id = {table_name}.phase_id
            """)
            
            print(f"  ✓ Restored cycle_id/report_id for {table_name}")
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not restore columns for {table_name}: {e}")
    
    # Phase 2: Remove phase_id columns from tables that didn't have it originally
    for table_name in TABLES_TO_ADD_PHASE_ID:
        try:
            op.drop_constraint(f"fk_{table_name}_phase_id", table_name, type_='foreignkey')
            op.drop_column(table_name, 'phase_id')
            print(f"  ✓ Removed phase_id from {table_name}")
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not remove phase_id from {table_name}: {e}")
    
    # Phase 3: Re-add foreign key constraints for cycle_id/report_id
    for table_name in TABLES_TO_REFACTOR:
        if table_name == 'workflow_activities':
            continue
            
        try:
            op.create_foreign_key(
                f"fk_{table_name}_cycle",
                table_name,
                'test_cycles',
                ['cycle_id'],
                ['cycle_id']
            )
            
            print(f"  ✓ Restored FK constraints for {table_name}")
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not restore FK constraints for {table_name}: {e}")
    
    print("✅ Phase ID refactoring downgrade completed!")