"""Add workflow activity enhancements for dynamic execution

Revision ID: add_workflow_activity_enhancements
Revises: populate_activity_templates
Create Date: 2025-07-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_workflow_activity_enhancements'
down_revision = 'populate_activity_templates'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to workflow_activity_templates
    op.add_column('workflow_activity_templates', 
        sa.Column('handler_name', sa.String(255), nullable=True))
    op.add_column('workflow_activity_templates', 
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='300'))
    op.add_column('workflow_activity_templates', 
        sa.Column('retry_policy', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('workflow_activity_templates', 
        sa.Column('conditional_expression', sa.Text(), nullable=True))
    op.add_column('workflow_activity_templates', 
        sa.Column('execution_mode', sa.String(50), nullable=False, server_default='sequential'))
    
    # Add new columns to workflow_activities
    op.add_column('workflow_activities', 
        sa.Column('instance_id', sa.String(255), nullable=True))
    op.add_column('workflow_activities', 
        sa.Column('parent_activity_id', sa.Integer(), nullable=True))
    op.add_column('workflow_activities', 
        sa.Column('execution_mode', sa.String(50), nullable=True))
    op.add_column('workflow_activities', 
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('workflow_activities', 
        sa.Column('last_error', sa.Text(), nullable=True))
    
    # Add foreign key for parent activity
    op.create_foreign_key(
        'fk_workflow_activities_parent',
        'workflow_activities', 
        'workflow_activities',
        ['parent_activity_id'], 
        ['activity_id'],
        ondelete='SET NULL'
    )
    
    # Create index for instance_id
    op.create_index(
        'ix_workflow_activities_instance_id',
        'workflow_activities',
        ['cycle_id', 'report_id', 'instance_id']
    )
    
    # Update existing templates with handler names
    op.execute("""
        UPDATE workflow_activity_templates 
        SET handler_name = CASE
            WHEN activity_name = 'Generate Attributes' THEN 'GenerateAttributesHandler'
            WHEN activity_name = 'Execute Scoping' THEN 'ExecuteScopingHandler'
            WHEN activity_name = 'Generate Samples' THEN 'GenerateSamplesHandler'
            WHEN activity_name = 'Send Data Request' THEN 'SendDataRequestHandler'
            WHEN activity_name = 'Execute Tests' THEN 'ExecuteTestsHandler'
            WHEN activity_type = 'manual' THEN 'ManualActivityHandler'
            ELSE 'AutomatedActivityHandler'
        END
    """)
    
    # Set execution modes for parallel phases
    op.execute("""
        UPDATE workflow_activity_templates
        SET execution_mode = 'parallel'
        WHERE phase_name IN ('Request for Information', 'Test Execution', 'Observation Management')
        AND activity_type = 'task'
    """)
    
    # Set retry policies for critical activities
    op.execute("""
        UPDATE workflow_activity_templates
        SET retry_policy = '{"max_attempts": 3, "initial_interval": 2, "max_interval": 60, "backoff": 2}'::json
        WHERE activity_type IN ('task', 'automated')
    """)


def downgrade():
    # Remove indexes
    op.drop_index('ix_workflow_activities_instance_id', table_name='workflow_activities')
    
    # Remove foreign key
    op.drop_constraint('fk_workflow_activities_parent', 'workflow_activities', type_='foreignkey')
    
    # Remove columns from workflow_activities
    op.drop_column('workflow_activities', 'last_error')
    op.drop_column('workflow_activities', 'retry_count')
    op.drop_column('workflow_activities', 'execution_mode')
    op.drop_column('workflow_activities', 'parent_activity_id')
    op.drop_column('workflow_activities', 'instance_id')
    
    # Remove columns from workflow_activity_templates
    op.drop_column('workflow_activity_templates', 'execution_mode')
    op.drop_column('workflow_activity_templates', 'conditional_expression')
    op.drop_column('workflow_activity_templates', 'retry_policy')
    op.drop_column('workflow_activity_templates', 'timeout_seconds')
    op.drop_column('workflow_activity_templates', 'handler_name')