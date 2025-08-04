"""Create activity tracking tables

Revision ID: activity_tracking_001
Revises: 
Create Date: 2025-01-11 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'activity_tracking_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create activity_definitions table
    op.create_table('activity_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(length=50), nullable=False),
        sa.Column('activity_name', sa.String(length=100), nullable=False),
        sa.Column('activity_code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('requires_backend_action', sa.Boolean(), nullable=True, default=False),
        sa.Column('backend_endpoint', sa.String(length=200), nullable=True),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('depends_on_activity_codes', sa.JSON(), nullable=True, default=list),
        sa.Column('button_text', sa.String(length=50), nullable=True),
        sa.Column('success_message', sa.String(length=200), nullable=True),
        sa.Column('instructions', sa.String(length=500), nullable=True),
        sa.Column('can_skip', sa.Boolean(), nullable=True, default=False),
        sa.Column('can_reset', sa.Boolean(), nullable=True, default=True),
        sa.Column('auto_complete_on_condition', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('activity_code'),
        sa.UniqueConstraint('phase_name', 'activity_name', name='uq_phase_activity')
    )
    
    # Create indexes for activity_definitions
    op.create_index('idx_activity_phase_sequence', 'activity_definitions', ['phase_name', 'sequence_order'])
    op.create_index('idx_activity_code', 'activity_definitions', ['activity_code'])
    
    # Create activity_states table
    op.create_table('activity_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(length=50), nullable=False),
        sa.Column('activity_definition_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('started_by', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_by', sa.Integer(), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=True, default=False),
        sa.Column('blocking_reason', sa.String(length=500), nullable=True),
        sa.Column('blocked_by_activities', sa.JSON(), nullable=True, default=list),
        sa.Column('completion_data', sa.JSON(), nullable=True),
        sa.Column('completion_notes', sa.String(length=1000), nullable=True),
        sa.Column('reset_count', sa.Integer(), nullable=True, default=0),
        sa.Column('last_reset_at', sa.DateTime(), nullable=True),
        sa.Column('last_reset_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definitions.id'], ),
        sa.ForeignKeyConstraint(['started_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['completed_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['last_reset_by'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cycle_id', 'report_id', 'activity_definition_id', name='uq_activity_state')
    )
    
    # Create indexes for activity_states
    op.create_index('idx_activity_state_context', 'activity_states', ['cycle_id', 'report_id', 'phase_name'])
    op.create_index('idx_activity_state_status', 'activity_states', ['status'])

    # Insert initial activity definitions
    op.execute("""
        INSERT INTO activity_definitions (
            phase_name, activity_name, activity_code, description, 
            activity_type, requires_backend_action, backend_endpoint,
            sequence_order, depends_on_activity_codes, button_text, 
            success_message, instructions, can_skip, can_reset, is_active
        ) VALUES
        -- Planning Phase Activities
        ('Planning', 'Start Planning Phase', 'start_planning', 'Initialize planning phase and set timeline', 
         'phase_start', true, '/planning/cycles/{cycle_id}/reports/{report_id}/start',
         1, '[]', 'Start Phase', 'Planning Phase Started', NULL, false, true, true),
        
        ('Planning', 'Load Attributes', 'load_attributes', 'Load attributes from regulatory data dictionary', 
         'manual', false, NULL,
         2, '["start_planning"]', 'Start', 'Use the Load from Data Dictionary button to load attributes', 
         'Click the "Load from Data Dictionary" button above to import attributes', false, true, true),
        
        ('Planning', 'Review & Approve Attributes', 'review_attributes', 'Review and approve attributes for testing scope', 
         'manual', false, NULL,
         3, '["load_attributes"]', 'Start', 'Review and approve attributes in the table below', 
         'Review each attribute and click the approve button', false, true, true),
        
        ('Planning', 'Complete Planning Phase', 'complete_planning', 'Finalize planning and proceed to scoping', 
         'phase_complete', true, '/planning/cycles/{cycle_id}/reports/{report_id}/complete',
         4, '["review_attributes"]', 'Complete Phase', 'Planning Phase Completed', NULL, false, true, true),
        
        -- Scoping Phase Activities
        ('Scoping', 'Start Scoping Phase', 'start_scoping', 'Initialize scoping phase and load attributes', 
         'phase_start', true, '/scoping/cycles/{cycle_id}/reports/{report_id}/start',
         1, '[]', 'Start Phase', 'Scoping Phase Started', NULL, false, true, true),
        
        ('Scoping', 'Load Attributes', 'load_scoping_attributes', 'Load attributes from planning phase', 
         'automated', false, NULL,
         2, '["start_scoping"]', 'Start', 'Attributes loaded from Planning phase', 
         'Attributes are automatically loaded', false, false, true),
        
        ('Scoping', 'Make Scoping Decisions', 'make_scoping_decisions', 'Decide which attributes to include in testing', 
         'manual', false, NULL,
         3, '["load_scoping_attributes"]', 'Start', 'Use the Include/Exclude buttons to make scoping decisions', 
         'Mark each attribute as included or excluded from testing scope', false, true, true),
        
        ('Scoping', 'Submit for Approval', 'submit_scoping_approval', 'Submit scoping decisions for approval', 
         'manual', false, NULL,
         4, '["make_scoping_decisions"]', 'Start', 'Use the Submit Scoping Decisions button below', 
         'Click "Submit Scoping Decisions" when all decisions are made', false, true, true),
        
        ('Scoping', 'Complete Scoping Phase', 'complete_scoping', 'Finalize scoping and proceed to next phase', 
         'phase_complete', true, '/scoping/cycles/{cycle_id}/reports/{report_id}/complete',
         5, '["submit_scoping_approval"]', 'Complete Phase', 'Scoping Phase Completed', NULL, false, true, true),
        
        -- Sample Selection Phase Activities
        ('Sample Selection', 'Start Sample Selection', 'start_sample_selection', 'Initialize sample selection phase', 
         'phase_start', true, '/sample-selection/cycles/{cycle_id}/reports/{report_id}/start',
         1, '[]', 'Start Phase', 'Sample Selection Phase Started', NULL, false, true, true),
        
        ('Sample Selection', 'Generate Samples', 'generate_samples', 'Generate sample sets for testing', 
         'manual', false, NULL,
         2, '["start_sample_selection"]', 'Start', 'Use the Generate Samples button to create sample sets', 
         'Click "Generate Samples" to create sample sets based on attributes', false, true, true),
        
        ('Sample Selection', 'Review Samples', 'review_samples', 'Review generated sample sets', 
         'manual', false, NULL,
         3, '["generate_samples"]', 'Start', 'Review the generated samples in the table below', 
         'Review each sample set for accuracy and completeness', false, true, true),
        
        ('Sample Selection', 'Approve Samples', 'approve_samples', 'Approve sample sets for testing', 
         'manual', false, NULL,
         4, '["review_samples"]', 'Start', 'Use the Approve button to approve sample sets', 
         'Click the approve button for each sample set', false, true, true),
        
        ('Sample Selection', 'Complete Sample Selection', 'complete_sample_selection', 'Finalize sample selection', 
         'phase_complete', true, '/sample-selection/cycles/{cycle_id}/reports/{report_id}/complete',
         5, '["approve_samples"]', 'Complete Phase', 'Sample Selection Phase Completed', NULL, false, true, true);
    """)


def downgrade():
    op.drop_index('idx_activity_state_status', table_name='activity_states')
    op.drop_index('idx_activity_state_context', table_name='activity_states')
    op.drop_table('activity_states')
    
    op.drop_index('idx_activity_code', table_name='activity_definitions')
    op.drop_index('idx_activity_phase_sequence', table_name='activity_definitions')
    op.drop_table('activity_definitions')