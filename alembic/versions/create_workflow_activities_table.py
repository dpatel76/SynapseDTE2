"""Create workflow_activities table for structured activity tracking

Revision ID: create_workflow_activities
Revises: 
Create Date: 2025-06-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_workflow_activities'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create activity status enum
    op.execute("CREATE TYPE activity_status_enum AS ENUM ('not_started', 'in_progress', 'completed', 'revision_requested', 'blocked', 'skipped')")
    
    # Create activity type enum
    op.execute("CREATE TYPE activity_type_enum AS ENUM ('start', 'task', 'review', 'approval', 'complete', 'custom')")
    
    # Create workflow_activities table
    op.create_table('workflow_activities',
        sa.Column('activity_id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.Enum('Planning', 'Data Profiling', 'Scoping', 'Sample Selection', 'Data Provider ID', 'Data Owner ID', 'Request Info', 'Test Execution', 'Observation Management', 'Test Report', name='workflow_phase_enum'), nullable=False),
        sa.Column('activity_name', sa.String(255), nullable=False),
        sa.Column('activity_type', sa.Enum('start', 'task', 'review', 'approval', 'complete', 'custom', name='activity_type_enum'), nullable=False),
        sa.Column('activity_order', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('not_started', 'in_progress', 'completed', 'revision_requested', 'blocked', 'skipped', name='activity_status_enum'), nullable=False, server_default='not_started'),
        sa.Column('can_start', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_optional', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_by', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by', sa.Integer(), nullable=True),
        sa.Column('revision_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revision_requested_by', sa.Integer(), nullable=True),
        sa.Column('revision_reason', sa.Text(), nullable=True),
        sa.Column('blocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('blocked_reason', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('activity_id'),
        sa.ForeignKeyConstraint(['cycle_id', 'report_id'], ['testing_cycles.cycle_id', 'reports.report_id'], ),
        sa.ForeignKeyConstraint(['cycle_id', 'report_id', 'phase_name'], ['workflow_phases.cycle_id', 'workflow_phases.report_id', 'workflow_phases.phase_name'], ),
        sa.ForeignKeyConstraint(['started_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['completed_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['revision_requested_by'], ['users.user_id'], )
    )
    
    # Create indexes for better query performance
    op.create_index('ix_workflow_activities_cycle_report', 'workflow_activities', ['cycle_id', 'report_id'])
    op.create_index('ix_workflow_activities_phase', 'workflow_activities', ['cycle_id', 'report_id', 'phase_name'])
    op.create_index('ix_workflow_activities_status', 'workflow_activities', ['status'])
    op.create_index('ix_workflow_activities_activity_name', 'workflow_activities', ['activity_name'])
    
    # Create unique constraint to prevent duplicate activities
    op.create_unique_constraint('uq_workflow_activities_unique_activity', 'workflow_activities', 
                               ['cycle_id', 'report_id', 'phase_name', 'activity_name'])
    
    # Create workflow_activity_history table for audit trail
    op.create_table('workflow_activity_history',
        sa.Column('history_id', sa.Integer(), nullable=False),
        sa.Column('activity_id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(100), nullable=False),
        sa.Column('activity_name', sa.String(255), nullable=False),
        sa.Column('from_status', sa.String(50), nullable=True),
        sa.Column('to_status', sa.String(50), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('history_id'),
        sa.ForeignKeyConstraint(['activity_id'], ['workflow_activities.activity_id'], ),
        sa.ForeignKeyConstraint(['changed_by'], ['users.user_id'], )
    )
    
    op.create_index('ix_workflow_activity_history_activity', 'workflow_activity_history', ['activity_id'])
    op.create_index('ix_workflow_activity_history_changed_at', 'workflow_activity_history', ['changed_at'])
    
    # Create workflow_activity_dependencies table for defining activity relationships
    op.create_table('workflow_activity_dependencies',
        sa.Column('dependency_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(100), nullable=False),
        sa.Column('activity_name', sa.String(255), nullable=False),
        sa.Column('depends_on_activity', sa.String(255), nullable=False),
        sa.Column('dependency_type', sa.String(50), nullable=False, server_default='completion'),  # completion, approval, any
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('dependency_id')
    )
    
    op.create_unique_constraint('uq_activity_dependencies_unique', 'workflow_activity_dependencies',
                               ['phase_name', 'activity_name', 'depends_on_activity'])
    
    # Create workflow_activity_templates table for defining standard activities per phase
    op.create_table('workflow_activity_templates',
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(100), nullable=False),
        sa.Column('activity_name', sa.String(255), nullable=False),
        sa.Column('activity_type', sa.Enum('start', 'task', 'review', 'approval', 'complete', 'custom', name='activity_type_enum'), nullable=False),
        sa.Column('activity_order', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_optional', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('required_role', sa.String(100), nullable=True),
        sa.Column('auto_complete_on_event', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('template_id')
    )
    
    op.create_unique_constraint('uq_activity_templates_unique', 'workflow_activity_templates',
                               ['phase_name', 'activity_name'])
    op.create_index('ix_workflow_activity_templates_phase', 'workflow_activity_templates', ['phase_name'])


def downgrade():
    op.drop_table('workflow_activity_templates')
    op.drop_table('workflow_activity_dependencies')
    op.drop_table('workflow_activity_history')
    op.drop_table('workflow_activities')
    op.execute('DROP TYPE activity_status_enum')
    op.execute('DROP TYPE activity_type_enum')