"""Create phase metrics table

Revision ID: create_phase_metrics
Revises: 
Create Date: 2024-12-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_phase_metrics'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create phase_metrics table
    op.create_table(
        'phase_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('lob_name', sa.String(100), nullable=True),
        
        # Metric fields
        sa.Column('total_attributes', sa.Integer, default=0),
        sa.Column('approved_attributes', sa.Integer, default=0),
        sa.Column('attributes_with_issues', sa.Integer, default=0),
        sa.Column('primary_keys', sa.Integer, default=0),
        sa.Column('non_pk_attributes', sa.Integer, default=0),
        
        sa.Column('total_samples', sa.Integer, default=0),
        sa.Column('approved_samples', sa.Integer, default=0),
        sa.Column('failed_samples', sa.Integer, default=0),
        
        sa.Column('total_test_cases', sa.Integer, default=0),
        sa.Column('completed_test_cases', sa.Integer, default=0),
        sa.Column('passed_test_cases', sa.Integer, default=0),
        sa.Column('failed_test_cases', sa.Integer, default=0),
        
        sa.Column('total_observations', sa.Integer, default=0),
        sa.Column('approved_observations', sa.Integer, default=0),
        
        sa.Column('completion_time_minutes', sa.Float, nullable=True),
        sa.Column('on_time_completion', sa.Boolean, nullable=True),
        sa.Column('submissions_for_approval', sa.Integer, default=0),
        
        sa.Column('data_providers_assigned', sa.Integer, default=0),
        sa.Column('changes_to_data_providers', sa.Integer, default=0),
        
        sa.Column('rfi_sent', sa.Integer, default=0),
        sa.Column('rfi_completed', sa.Integer, default=0),
        sa.Column('rfi_pending', sa.Integer, default=0),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], name='fk_phase_metrics_cycle'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], name='fk_phase_metrics_report'),
    )
    
    # Create indexes
    op.create_index('idx_phase_metrics_cycle_report', 'phase_metrics', ['cycle_id', 'report_id'])
    op.create_index('idx_phase_metrics_phase', 'phase_metrics', ['phase_name'])
    op.create_index('idx_phase_metrics_lob', 'phase_metrics', ['lob_name'])
    op.create_index('idx_phase_metrics_created', 'phase_metrics', ['created_at'])
    
    # Create execution_metrics table for tracking workflow execution times
    op.create_table(
        'execution_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('activity_name', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=True),
        
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Float, nullable=True),
        sa.Column('status', sa.String(50), nullable=False),  # started, completed, failed
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], name='fk_execution_metrics_cycle'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], name='fk_execution_metrics_report'),
    )
    
    # Create indexes for execution metrics
    op.create_index('idx_execution_metrics_cycle_report', 'execution_metrics', ['cycle_id', 'report_id'])
    op.create_index('idx_execution_metrics_user', 'execution_metrics', ['user_id'])
    op.create_index('idx_execution_metrics_start', 'execution_metrics', ['start_time'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_execution_metrics_start', 'execution_metrics')
    op.drop_index('idx_execution_metrics_user', 'execution_metrics')
    op.drop_index('idx_execution_metrics_cycle_report', 'execution_metrics')
    
    op.drop_index('idx_phase_metrics_created', 'phase_metrics')
    op.drop_index('idx_phase_metrics_lob', 'phase_metrics')
    op.drop_index('idx_phase_metrics_phase', 'phase_metrics')
    op.drop_index('idx_phase_metrics_cycle_report', 'phase_metrics')
    
    # Drop tables
    op.drop_table('execution_metrics')
    op.drop_table('phase_metrics')