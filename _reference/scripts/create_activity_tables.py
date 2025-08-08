#!/usr/bin/env python3
"""Create activity tracking tables directly"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Create engine
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
engine = create_engine(DATABASE_URL)

# Execute the migration directly
with engine.begin() as connection:
    # Check if tables exist
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'activity_definitions'
        );
    """))
    
    table_exists = result.scalar()
    
    if not table_exists:
        print('Creating activity_definitions and activity_states tables...')
        
        # Create activity_definitions table
        connection.execute(text("""
            CREATE TABLE activity_definitions (
                id SERIAL PRIMARY KEY,
                phase_name VARCHAR(50) NOT NULL,
                activity_name VARCHAR(100) NOT NULL,
                activity_code VARCHAR(50) NOT NULL,
                description VARCHAR(500),
                activity_type VARCHAR(50) NOT NULL,
                requires_backend_action BOOLEAN DEFAULT FALSE,
                backend_endpoint VARCHAR(200),
                sequence_order INTEGER NOT NULL,
                depends_on_activity_codes JSON DEFAULT '[]'::json,
                button_text VARCHAR(50),
                success_message VARCHAR(200),
                instructions VARCHAR(500),
                can_skip BOOLEAN DEFAULT FALSE,
                can_reset BOOLEAN DEFAULT TRUE,
                auto_complete_on_condition JSON,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by_id INTEGER,
                updated_by_id INTEGER,
                CONSTRAINT uq_activity_code UNIQUE (activity_code),
                CONSTRAINT uq_phase_activity UNIQUE (phase_name, activity_name)
            );
        """))
        
        # Create indexes
        connection.execute(text('CREATE INDEX idx_activity_phase_sequence ON activity_definitions (phase_name, sequence_order);'))
        connection.execute(text('CREATE INDEX idx_activity_code ON activity_definitions (activity_code);'))
        
        # Create activity_states table
        connection.execute(text("""
            CREATE TABLE activity_states (
                id SERIAL PRIMARY KEY,
                cycle_id INTEGER NOT NULL,
                report_id INTEGER NOT NULL,
                phase_name VARCHAR(50) NOT NULL,
                activity_definition_id INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                started_at TIMESTAMP,
                started_by INTEGER,
                completed_at TIMESTAMP,
                completed_by INTEGER,
                is_blocked BOOLEAN DEFAULT FALSE,
                blocking_reason VARCHAR(500),
                blocked_by_activities JSON DEFAULT '[]'::json,
                completion_data JSON,
                completion_notes VARCHAR(1000),
                reset_count INTEGER DEFAULT 0,
                last_reset_at TIMESTAMP,
                last_reset_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by_id INTEGER,
                updated_by_id INTEGER,
                CONSTRAINT fk_activity_definition FOREIGN KEY (activity_definition_id) REFERENCES activity_definitions(id),
                CONSTRAINT fk_started_by FOREIGN KEY (started_by) REFERENCES users(user_id),
                CONSTRAINT fk_completed_by FOREIGN KEY (completed_by) REFERENCES users(user_id),
                CONSTRAINT fk_last_reset_by FOREIGN KEY (last_reset_by) REFERENCES users(user_id),
                CONSTRAINT uq_activity_state UNIQUE (cycle_id, report_id, activity_definition_id)
            );
        """))
        
        # Create indexes
        connection.execute(text('CREATE INDEX idx_activity_state_context ON activity_states (cycle_id, report_id, phase_name);'))
        connection.execute(text('CREATE INDEX idx_activity_state_status ON activity_states (status);'))
        
        # Insert initial activity definitions
        connection.execute(text("""
            INSERT INTO activity_definitions (
                phase_name, activity_name, activity_code, description, 
                activity_type, requires_backend_action, backend_endpoint,
                sequence_order, depends_on_activity_codes, button_text, 
                success_message, instructions, can_skip, can_reset, is_active
            ) VALUES
            -- Planning Phase Activities
            ('planning', 'Start Planning Phase', 'start_planning', 'Initialize planning phase and set timeline', 
             'phase_start', true, '/planning/cycles/{cycle_id}/reports/{report_id}/start',
             1, '[]', 'Start Phase', 'Planning Phase Started', NULL, false, true, true),
            
            ('planning', 'Load Attributes', 'load_attributes', 'Load attributes from regulatory data dictionary', 
             'manual', false, NULL,
             2, '["start_planning"]', 'Start', 'Use the Load from Data Dictionary button to load attributes', 
             'Click the "Load from Data Dictionary" button above to import attributes', false, true, true),
            
            ('planning', 'Review & Approve Attributes', 'review_attributes', 'Review and approve attributes for testing scope', 
             'manual', false, NULL,
             3, '["load_attributes"]', 'Start', 'Review and approve attributes in the table below', 
             'Review each attribute and click the approve button', false, true, true),
            
            ('planning', 'Complete Planning Phase', 'complete_planning', 'Finalize planning and proceed to scoping', 
             'phase_complete', true, '/planning/cycles/{cycle_id}/reports/{report_id}/complete',
             4, '["review_attributes"]', 'Complete Phase', 'Planning Phase Completed', NULL, false, true, true),
            
            -- Scoping Phase Activities
            ('scoping', 'Start Scoping Phase', 'start_scoping', 'Initialize scoping phase and load attributes', 
             'phase_start', true, '/scoping/cycles/{cycle_id}/reports/{report_id}/start',
             1, '[]', 'Start Phase', 'Scoping Phase Started', NULL, false, true, true),
            
            ('scoping', 'Load Attributes', 'load_scoping_attributes', 'Load attributes from planning phase', 
             'automated', false, NULL,
             2, '["start_scoping"]', 'Start', 'Attributes loaded from Planning phase', 
             'Attributes are automatically loaded', false, false, true),
            
            ('scoping', 'Make Scoping Decisions', 'make_scoping_decisions', 'Decide which attributes to include in testing', 
             'manual', false, NULL,
             3, '["load_scoping_attributes"]', 'Start', 'Use the Include/Exclude buttons to make scoping decisions', 
             'Mark each attribute as included or excluded from testing scope', false, true, true),
            
            ('scoping', 'Submit for Approval', 'submit_scoping_approval', 'Submit scoping decisions for approval', 
             'manual', false, NULL,
             4, '["make_scoping_decisions"]', 'Start', 'Use the Submit Scoping Decisions button below', 
             'Click "Submit Scoping Decisions" when all decisions are made', false, true, true),
            
            ('scoping', 'Complete Scoping Phase', 'complete_scoping', 'Finalize scoping and proceed to next phase', 
             'phase_complete', true, '/scoping/cycles/{cycle_id}/reports/{report_id}/complete',
             5, '["submit_scoping_approval"]', 'Complete Phase', 'Scoping Phase Completed', NULL, false, true, true),
            
            -- Sample Selection Phase Activities
            ('sample_selection', 'Start Sample Selection', 'start_sample_selection', 'Initialize sample selection phase', 
             'phase_start', true, '/sample-selection/cycles/{cycle_id}/reports/{report_id}/start',
             1, '[]', 'Start Phase', 'Sample Selection Phase Started', NULL, false, true, true),
            
            ('sample_selection', 'Generate Samples', 'generate_samples', 'Generate sample sets for testing', 
             'manual', false, NULL,
             2, '["start_sample_selection"]', 'Start', 'Use the Generate Samples button to create sample sets', 
             'Click "Generate Samples" to create sample sets based on attributes', false, true, true),
            
            ('sample_selection', 'Review Samples', 'review_samples', 'Review generated sample sets', 
             'manual', false, NULL,
             3, '["generate_samples"]', 'Start', 'Review the generated samples in the table below', 
             'Review each sample set for accuracy and completeness', false, true, true),
            
            ('sample_selection', 'Approve Samples', 'approve_samples', 'Approve sample sets for testing', 
             'manual', false, NULL,
             4, '["review_samples"]', 'Start', 'Use the Approve button to approve sample sets', 
             'Click the approve button for each sample set', false, true, true),
            
            ('sample_selection', 'Complete Sample Selection', 'complete_sample_selection', 'Finalize sample selection', 
             'phase_complete', true, '/sample-selection/cycles/{cycle_id}/reports/{report_id}/complete',
             5, '["approve_samples"]', 'Complete Phase', 'Sample Selection Phase Completed', NULL, false, true, true);
        """))
        
        print('Tables created and populated successfully!')
    else:
        print('Tables already exist')
        
        # Check if data exists
        result = connection.execute(text("SELECT COUNT(*) FROM activity_definitions"))
        count = result.scalar()
        print(f"Activity definitions count: {count}")

print("\nVerifying tables...")
with engine.connect() as connection:
    # Check activity_definitions
    result = connection.execute(text("SELECT phase_name, COUNT(*) as count FROM activity_definitions GROUP BY phase_name"))
    print("\nActivity definitions by phase:")
    for row in result:
        print(f"  {row.phase_name}: {row.count} activities")
    
    # Check for any activity states
    result = connection.execute(text("SELECT COUNT(*) FROM activity_states"))
    count = result.scalar()
    print(f"\nActivity states count: {count}")