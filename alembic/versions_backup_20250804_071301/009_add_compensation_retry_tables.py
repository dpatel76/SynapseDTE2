"""Add compensation and retry tracking tables

Revision ID: 009
Revises: 008
Create Date: 2024-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Create workflow_compensation_log table
    op.create_table('workflow_compensation_log',
        sa.Column('log_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(255), nullable=False),
        sa.Column('execution_id', sa.String(255), nullable=True),
        sa.Column('phase', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),  # ROLLBACK, NOTIFY, SKIP, etc.
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, default=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('rollback_phases', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('notifications_sent', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('manual_intervention_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('log_id')
    )
    
    # Add indexes
    op.create_index('idx_compensation_workflow_id', 'workflow_compensation_log', ['workflow_id'])
    op.create_index('idx_compensation_phase', 'workflow_compensation_log', ['phase'])
    op.create_index('idx_compensation_timestamp', 'workflow_compensation_log', ['timestamp'])
    
    # Create workflow_activity_retry_log table
    op.create_table('workflow_activity_retry_log',
        sa.Column('retry_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(255), nullable=False),
        sa.Column('activity_id', sa.String(255), nullable=False),
        sa.Column('phase', sa.String(100), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),  # data_fetch, llm_request, etc.
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('retry_after_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('retry_id')
    )
    
    # Add indexes
    op.create_index('idx_retry_workflow_id', 'workflow_activity_retry_log', ['workflow_id'])
    op.create_index('idx_retry_activity_type', 'workflow_activity_retry_log', ['activity_type'])
    op.create_index('idx_retry_phase', 'workflow_activity_retry_log', ['phase'])
    op.create_index('idx_retry_timestamp', 'workflow_activity_retry_log', ['timestamp'])
    
    # Create workflow_retry_policy_config table
    op.create_table('workflow_retry_policy_config',
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False, unique=True),
        sa.Column('max_attempts', sa.Integer(), nullable=True),
        sa.Column('initial_interval_seconds', sa.Integer(), nullable=True),
        sa.Column('backoff_coefficient', sa.Float(), nullable=True),
        sa.Column('max_interval_seconds', sa.Integer(), nullable=True),
        sa.Column('non_retryable_errors', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('config_id'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], ondelete='SET NULL')
    )
    
    # Insert default retry policies
    op.execute("""
        INSERT INTO workflow_retry_policy_config (activity_type, max_attempts, initial_interval_seconds, backoff_coefficient, max_interval_seconds)
        VALUES 
        ('data_fetch', 5, 2, 2.0, 600),
        ('llm_request', 3, 5, 3.0, 300),
        ('database_operation', 3, 1, 2.0, 30),
        ('email_notification', 3, 10, 2.0, 120),
        ('phase_transition', 2, 5, 1.0, 5)
    """)
    
    # Add compensation_log column to workflow_execution
    op.add_column('workflow_execution',
        sa.Column('compensation_log', postgresql.JSONB(), nullable=True)
    )
    
    # Add retry_statistics column to workflow_execution
    op.add_column('workflow_execution',
        sa.Column('retry_statistics', postgresql.JSONB(), nullable=True)
    )


def downgrade():
    op.drop_column('workflow_execution', 'retry_statistics')
    op.drop_column('workflow_execution', 'compensation_log')
    
    op.drop_index('idx_retry_timestamp', table_name='workflow_activity_retry_log')
    op.drop_index('idx_retry_phase', table_name='workflow_activity_retry_log')
    op.drop_index('idx_retry_activity_type', table_name='workflow_activity_retry_log')
    op.drop_index('idx_retry_workflow_id', table_name='workflow_activity_retry_log')
    op.drop_table('workflow_activity_retry_log')
    
    op.drop_index('idx_compensation_timestamp', table_name='workflow_compensation_log')
    op.drop_index('idx_compensation_phase', table_name='workflow_compensation_log')
    op.drop_index('idx_compensation_workflow_id', table_name='workflow_compensation_log')
    op.drop_table('workflow_compensation_log')
    
    op.drop_table('workflow_retry_policy_config')