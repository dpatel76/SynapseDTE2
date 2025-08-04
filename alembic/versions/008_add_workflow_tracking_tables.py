"""Add workflow tracking tables for Temporal integration

Revision ID: 008_workflow_tracking
Revises: 007_add_test_report_tables
Create Date: 2024-12-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '008_workflow_tracking'
down_revision = '007_add_test_report_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create workflow execution status enum
    op.execute("""
        CREATE TYPE workflow_execution_status AS ENUM (
            'pending', 'running', 'completed', 'failed', 'cancelled', 'timed_out'
        )
    """)
    
    # Create step type enum
    op.execute("""
        CREATE TYPE step_type AS ENUM (
            'phase', 'activity', 'transition', 'decision', 'parallel_branch', 'sub_workflow'
        )
    """)
    
    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('execution_id', sa.String(36), primary_key=True),
        sa.Column('workflow_id', sa.String(100), nullable=False),
        sa.Column('workflow_run_id', sa.String(100), nullable=False),
        sa.Column('workflow_type', sa.String(100), nullable=False),
        sa.Column('workflow_version', sa.String(20), server_default='1.0'),
        sa.Column('cycle_id', sa.Integer(), sa.ForeignKey('test_cycles.cycle_id'), nullable=False),
        sa.Column('report_id', sa.Integer(), sa.ForeignKey('reports.report_id')),
        sa.Column('initiated_by', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', 'timed_out', name='workflow_execution_status'), server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Float()),
        sa.Column('input_data', sa.JSON()),
        sa.Column('output_data', sa.JSON()),
        sa.Column('error_details', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create indexes for workflow_executions
    op.create_index('idx_workflow_executions_cycle', 'workflow_executions', ['cycle_id'])
    op.create_index('idx_workflow_executions_status', 'workflow_executions', ['status'])
    op.create_index('idx_workflow_executions_started', 'workflow_executions', ['started_at'])
    
    # Create workflow_steps table
    op.create_table(
        'workflow_steps',
        sa.Column('step_id', sa.String(36), primary_key=True),
        sa.Column('execution_id', sa.String(36), sa.ForeignKey('workflow_executions.execution_id'), nullable=False),
        sa.Column('parent_step_id', sa.String(36), sa.ForeignKey('workflow_steps.step_id')),
        sa.Column('step_name', sa.String(100), nullable=False),
        sa.Column('step_type', postgresql.ENUM('phase', 'activity', 'transition', 'decision', 'parallel_branch', 'sub_workflow', name='step_type'), nullable=False),
        sa.Column('phase_name', sa.String(50)),
        sa.Column('activity_name', sa.String(100)),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', 'timed_out', name='workflow_execution_status'), server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Float()),
        sa.Column('attempt_number', sa.Integer(), server_default='1'),
        sa.Column('max_attempts', sa.Integer(), server_default='3'),
        sa.Column('retry_delay_seconds', sa.Integer()),
        sa.Column('input_data', sa.JSON()),
        sa.Column('output_data', sa.JSON()),
        sa.Column('error_details', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create indexes for workflow_steps
    op.create_index('idx_workflow_steps_execution', 'workflow_steps', ['execution_id'])
    op.create_index('idx_workflow_steps_status', 'workflow_steps', ['status'])
    op.create_index('idx_workflow_steps_phase', 'workflow_steps', ['phase_name'])
    
    # Create workflow_transitions table
    op.create_table(
        'workflow_transitions',
        sa.Column('transition_id', sa.String(36), primary_key=True),
        sa.Column('execution_id', sa.String(36), sa.ForeignKey('workflow_executions.execution_id'), nullable=False),
        sa.Column('from_step_id', sa.String(36), sa.ForeignKey('workflow_steps.step_id')),
        sa.Column('to_step_id', sa.String(36), sa.ForeignKey('workflow_steps.step_id')),
        sa.Column('transition_type', sa.String(50)),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Float()),
        sa.Column('condition_evaluated', sa.String(200)),
        sa.Column('condition_result', sa.Boolean()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create indexes for workflow_transitions
    op.create_index('idx_workflow_transitions_execution', 'workflow_transitions', ['execution_id'])
    op.create_index('idx_workflow_transitions_timing', 'workflow_transitions', ['started_at', 'completed_at'])
    
    # Create workflow_metrics table
    op.create_table(
        'workflow_metrics',
        sa.Column('metric_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('workflow_type', sa.String(100), nullable=False),
        sa.Column('phase_name', sa.String(50)),
        sa.Column('activity_name', sa.String(100)),
        sa.Column('step_type', postgresql.ENUM('phase', 'activity', 'transition', 'decision', 'parallel_branch', 'sub_workflow', name='step_type')),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('execution_count', sa.Integer(), server_default='0'),
        sa.Column('success_count', sa.Integer(), server_default='0'),
        sa.Column('failure_count', sa.Integer(), server_default='0'),
        sa.Column('avg_duration', sa.Float()),
        sa.Column('min_duration', sa.Float()),
        sa.Column('max_duration', sa.Float()),
        sa.Column('p50_duration', sa.Float()),
        sa.Column('p90_duration', sa.Float()),
        sa.Column('p95_duration', sa.Float()),
        sa.Column('p99_duration', sa.Float()),
        sa.Column('avg_retry_count', sa.Float()),
        sa.Column('timeout_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create indexes and constraints for workflow_metrics
    op.create_index('idx_workflow_metrics_type_period', 'workflow_metrics', ['workflow_type', 'period_start'])
    op.create_index('idx_workflow_metrics_phase_period', 'workflow_metrics', ['phase_name', 'period_start'])
    op.create_unique_constraint(
        'uq_workflow_metrics_aggregation',
        'workflow_metrics',
        ['workflow_type', 'phase_name', 'activity_name', 'step_type', 'period_start', 'period_end']
    )
    
    # Create workflow_alerts table
    op.create_table(
        'workflow_alerts',
        sa.Column('alert_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('execution_id', sa.String(36), sa.ForeignKey('workflow_executions.execution_id')),
        sa.Column('workflow_type', sa.String(100)),
        sa.Column('phase_name', sa.String(50)),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('threshold_value', sa.Float()),
        sa.Column('actual_value', sa.Float()),
        sa.Column('alert_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('acknowledged', sa.Boolean(), server_default='false'),
        sa.Column('acknowledged_by', sa.Integer(), sa.ForeignKey('users.user_id')),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True)),
        sa.Column('resolved', sa.Boolean(), server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True))
    )
    
    # Create indexes for workflow_alerts
    op.create_index('idx_workflow_alerts_unresolved', 'workflow_alerts', ['resolved', 'created_at'])
    op.create_index('idx_workflow_alerts_severity', 'workflow_alerts', ['severity', 'created_at'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('workflow_alerts')
    op.drop_table('workflow_metrics')
    op.drop_table('workflow_transitions')
    op.drop_table('workflow_steps')
    op.drop_table('workflow_executions')
    
    # Drop enums
    op.execute('DROP TYPE workflow_execution_status')
    op.execute('DROP TYPE step_type')