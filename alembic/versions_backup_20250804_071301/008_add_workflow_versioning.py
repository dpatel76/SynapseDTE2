"""Add workflow versioning support

Revision ID: 008
Revises: 007
Create Date: 2024-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007_add_test_report_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add version column to workflow_execution table
    op.add_column('workflow_execution', 
        sa.Column('workflow_version', sa.String(20), nullable=True)
    )
    
    # Add migration_history table for tracking workflow migrations
    op.create_table('workflow_migration_history',
        sa.Column('migration_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(255), nullable=False),
        sa.Column('execution_id', sa.String(255), nullable=True),
        sa.Column('from_version', sa.String(20), nullable=False),
        sa.Column('to_version', sa.String(20), nullable=False),
        sa.Column('migration_status', sa.String(50), nullable=False),
        sa.Column('migration_started_at', sa.DateTime(), nullable=False),
        sa.Column('migration_completed_at', sa.DateTime(), nullable=True),
        sa.Column('migration_notes', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('migration_id'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.user_id'], ondelete='SET NULL')
    )
    
    # Add index for workflow lookups
    op.create_index('idx_workflow_migration_workflow_id', 'workflow_migration_history', ['workflow_id'])
    
    # Add workflow_version_config table for version management
    op.create_table('workflow_version_config',
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.String(20), nullable=False, unique=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_deprecated', sa.Boolean(), nullable=False, default=False),
        sa.Column('release_date', sa.Date(), nullable=False),
        sa.Column('deprecation_date', sa.Date(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('breaking_changes', postgresql.JSONB(), nullable=True),
        sa.Column('features', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('version_id')
    )
    
    # Insert initial version data
    op.execute("""
        INSERT INTO workflow_version_config (version_number, is_current, is_deprecated, release_date, description, features)
        VALUES 
        ('1.0.0', false, false, '2024-01-01', 'Initial 8-phase workflow implementation', 
         '{"phases": 8, "parallel_execution": false, "timing_instrumentation": false}'::jsonb),
        ('1.1.0', false, false, '2024-01-15', 'Added phase timing instrumentation', 
         '{"phases": 8, "parallel_execution": false, "timing_instrumentation": true}'::jsonb),
        ('1.2.0', true, false, '2024-02-01', 'Added parallel phase execution support', 
         '{"phases": 8, "parallel_execution": true, "timing_instrumentation": true, "phase_skipping": true}'::jsonb)
    """)
    
    # Update existing workflow executions to have version
    op.execute("""
        UPDATE workflow_execution 
        SET workflow_version = '1.2.0' 
        WHERE workflow_version IS NULL
    """)
    
    # Make version column non-nullable after backfill
    op.alter_column('workflow_execution', 'workflow_version',
        existing_type=sa.String(20),
        nullable=False
    )


def downgrade():
    op.drop_index('idx_workflow_migration_workflow_id', table_name='workflow_migration_history')
    op.drop_table('workflow_migration_history')
    op.drop_table('workflow_version_config')
    op.drop_column('workflow_execution', 'workflow_version')