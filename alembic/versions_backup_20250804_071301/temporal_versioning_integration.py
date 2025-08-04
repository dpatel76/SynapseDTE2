"""Add Temporal integration to versioning system

Revision ID: temporal_versioning_001
Revises: 
Create Date: 2024-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'temporal_versioning_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add Temporal context to versioning tables"""
    
    # Add Temporal fields to version_history table
    op.add_column('version_history', 
        sa.Column('workflow_execution_id', sa.String(255), nullable=True))
    op.add_column('version_history', 
        sa.Column('workflow_run_id', sa.String(255), nullable=True))
    op.add_column('version_history', 
        sa.Column('workflow_step_id', postgresql.UUID(), nullable=True))
    op.add_column('version_history', 
        sa.Column('activity_name', sa.String(100), nullable=True))
    op.add_column('version_history', 
        sa.Column('activity_task_token', sa.LargeBinary(), nullable=True))
    
    # Add foreign key to workflow_steps
    op.create_foreign_key(
        'fk_version_history_workflow_step',
        'version_history', 'workflow_steps',
        ['workflow_step_id'], ['step_id']
    )
    
    # Add indexes
    op.create_index('idx_version_workflow_execution', 
                    'version_history', ['workflow_execution_id'])
    op.create_index('idx_version_workflow_step', 
                    'version_history', ['workflow_step_id'])
    
    # Create workflow version operations tracking table
    op.create_table('workflow_version_operations',
        sa.Column('operation_id', postgresql.UUID(), 
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('workflow_step_id', postgresql.UUID(), nullable=True),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('version_id', postgresql.UUID(), nullable=True),
        sa.Column('initiated_at', sa.TIMESTAMP(timezone=True), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('operation_id'),
        sa.ForeignKeyConstraint(['workflow_step_id'], ['workflow_steps.step_id'])
    )
    
    op.create_index('idx_wf_version_ops_execution', 
                    'workflow_version_operations', ['workflow_execution_id'])
    op.create_index('idx_wf_version_ops_version', 
                    'workflow_version_operations', ['version_id'])
    
    # Add Temporal fields to phase-specific version tables
    
    # Planning phase versions
    if table_exists('planning_phase_versions'):
        op.add_column('planning_phase_versions',
            sa.Column('workflow_execution_id', sa.String(255), nullable=True))
        op.add_column('planning_phase_versions',
            sa.Column('workflow_step_id', postgresql.UUID(), nullable=True))
        op.create_index('idx_planning_workflow_execution',
                       'planning_phase_versions', ['workflow_execution_id'])
    
    # Sample selection versions
    if table_exists('sample_selection_versions'):
        op.add_column('sample_selection_versions',
            sa.Column('workflow_execution_id', sa.String(255), nullable=True))
        op.add_column('sample_selection_versions',
            sa.Column('workflow_step_id', postgresql.UUID(), nullable=True))
        op.create_index('idx_sample_selection_workflow_execution',
                       'sample_selection_versions', ['workflow_execution_id'])
    
    # Data profiling versions
    if table_exists('data_profiling_versions'):
        op.add_column('data_profiling_versions',
            sa.Column('workflow_execution_id', sa.String(255), nullable=True))
        op.add_column('data_profiling_versions',
            sa.Column('workflow_step_id', postgresql.UUID(), nullable=True))
        op.create_index('idx_data_profiling_workflow_execution',
                       'data_profiling_versions', ['workflow_execution_id'])
    
    # Scoping versions
    if table_exists('scoping_versions'):
        op.add_column('scoping_versions',
            sa.Column('workflow_execution_id', sa.String(255), nullable=True))
        op.add_column('scoping_versions',
            sa.Column('workflow_step_id', postgresql.UUID(), nullable=True))
        op.create_index('idx_scoping_workflow_execution',
                       'scoping_versions', ['workflow_execution_id'])
    
    # Observation versions
    if table_exists('observation_versions'):
        op.add_column('observation_versions',
            sa.Column('workflow_execution_id', sa.String(255), nullable=True))
        op.add_column('observation_versions',
            sa.Column('workflow_step_id', postgresql.UUID(), nullable=True))
        op.create_index('idx_observation_workflow_execution',
                       'observation_versions', ['workflow_execution_id'])
    
    # Test report versions
    if table_exists('test_report_versions'):
        op.add_column('test_report_versions',
            sa.Column('workflow_execution_id', sa.String(255), nullable=True))
        op.add_column('test_report_versions',
            sa.Column('workflow_step_id', postgresql.UUID(), nullable=True))
        op.create_index('idx_test_report_workflow_execution',
                       'test_report_versions', ['workflow_execution_id'])
    
    # Add workflow context to existing versioning tables if they exist
    tables_to_update = [
        'report_attributes',
        'sample_sets',
        'profiling_rules',
        'scoping_decisions'
    ]
    
    for table_name in tables_to_update:
        if table_exists(table_name) and has_version_fields(table_name):
            op.add_column(table_name,
                sa.Column('workflow_execution_id', sa.String(255), nullable=True))
            op.add_column(table_name,
                sa.Column('workflow_step_id', postgresql.UUID(), nullable=True))
            op.create_index(f'idx_{table_name}_workflow_execution',
                           table_name, ['workflow_execution_id'])


def downgrade():
    """Remove Temporal integration from versioning system"""
    
    # Drop workflow version operations table
    op.drop_table('workflow_version_operations')
    
    # Remove from version_history
    op.drop_index('idx_version_workflow_execution', 'version_history')
    op.drop_index('idx_version_workflow_step', 'version_history')
    op.drop_constraint('fk_version_history_workflow_step', 'version_history')
    op.drop_column('version_history', 'workflow_execution_id')
    op.drop_column('version_history', 'workflow_run_id')
    op.drop_column('version_history', 'workflow_step_id')
    op.drop_column('version_history', 'activity_name')
    op.drop_column('version_history', 'activity_task_token')
    
    # Remove from phase-specific version tables
    phase_tables = [
        'planning_phase_versions',
        'sample_selection_versions',
        'data_profiling_versions',
        'scoping_versions',
        'observation_versions',
        'test_report_versions'
    ]
    
    for table_name in phase_tables:
        if table_exists(table_name):
            op.drop_index(f'idx_{table_name.replace("_versions", "")}_workflow_execution', 
                         table_name)
            op.drop_column(table_name, 'workflow_execution_id')
            op.drop_column(table_name, 'workflow_step_id')
    
    # Remove from other tables
    tables_to_update = [
        'report_attributes',
        'sample_sets',
        'profiling_rules',
        'scoping_decisions'
    ]
    
    for table_name in tables_to_update:
        if table_exists(table_name) and column_exists(table_name, 'workflow_execution_id'):
            op.drop_index(f'idx_{table_name}_workflow_execution', table_name)
            op.drop_column(table_name, 'workflow_execution_id')
            op.drop_column(table_name, 'workflow_step_id')


def table_exists(table_name):
    """Check if table exists in database"""
    from sqlalchemy import inspect
    from alembic import context
    
    bind = context.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def has_version_fields(table_name):
    """Check if table has versioning fields"""
    from sqlalchemy import inspect
    from alembic import context
    
    bind = context.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return 'version_number' in columns or 'version_id' in columns


def column_exists(table_name, column_name):
    """Check if column exists in table"""
    from sqlalchemy import inspect
    from alembic import context
    
    bind = context.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns