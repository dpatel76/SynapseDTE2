"""Implement universal phase tracking

Revision ID: implement_universal_phase_tracking
Revises: drop_deprecated_phase_tables
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'implement_universal_phase_tracking'
down_revision = 'drop_deprecated_phase_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add workflow tracking columns to tables that had phase_id
    
    # Data profiling tables
    op.add_column('cycle_report_data_profiling_files', 
        sa.Column('workflow_activity_id', sa.Integer(), 
        sa.ForeignKey('workflow_activities.activity_id'), nullable=True))
    
    op.add_column('cycle_report_data_profiling_rules', 
        sa.Column('workflow_activity_id', sa.Integer(), 
        sa.ForeignKey('workflow_activities.activity_id'), nullable=True))
    
    op.add_column('cycle_report_data_profiling_results', 
        sa.Column('workflow_activity_id', sa.Integer(), 
        sa.ForeignKey('workflow_activities.activity_id'), nullable=True))
    
    op.add_column('cycle_report_data_profiling_attribute_scores', 
        sa.Column('workflow_activity_id', sa.Integer(), 
        sa.ForeignKey('workflow_activities.activity_id'), nullable=True))
    
    # Now drop the deprecated phase_id columns
    op.drop_column('cycle_report_data_profiling_files', 'phase_id')
    op.drop_column('cycle_report_data_profiling_rules', 'phase_id')
    op.drop_column('cycle_report_data_profiling_results', 'phase_id')
    op.drop_column('cycle_report_data_profiling_attribute_scores', 'phase_id')
    
    # Create indexes for better performance
    op.create_index('idx_profiling_files_workflow', 'cycle_report_data_profiling_files', ['workflow_activity_id'])
    op.create_index('idx_profiling_rules_workflow', 'cycle_report_data_profiling_rules', ['workflow_activity_id'])
    op.create_index('idx_profiling_results_workflow', 'cycle_report_data_profiling_results', ['workflow_activity_id'])
    op.create_index('idx_profiling_scores_workflow', 'cycle_report_data_profiling_attribute_scores', ['workflow_activity_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_profiling_files_workflow', table_name='cycle_report_data_profiling_files')
    op.drop_index('idx_profiling_rules_workflow', table_name='cycle_report_data_profiling_rules')
    op.drop_index('idx_profiling_results_workflow', table_name='cycle_report_data_profiling_results')
    op.drop_index('idx_profiling_scores_workflow', table_name='cycle_report_data_profiling_attribute_scores')
    
    # Add back phase_id columns
    op.add_column('cycle_report_data_profiling_files', sa.Column('phase_id', sa.Integer(), nullable=True))
    op.add_column('cycle_report_data_profiling_rules', sa.Column('phase_id', sa.Integer(), nullable=True))
    op.add_column('cycle_report_data_profiling_results', sa.Column('phase_id', sa.Integer(), nullable=True))
    op.add_column('cycle_report_data_profiling_attribute_scores', sa.Column('phase_id', sa.Integer(), nullable=True))
    
    # Drop workflow_activity_id columns
    op.drop_column('cycle_report_data_profiling_files', 'workflow_activity_id')
    op.drop_column('cycle_report_data_profiling_rules', 'workflow_activity_id')
    op.drop_column('cycle_report_data_profiling_results', 'workflow_activity_id')
    op.drop_column('cycle_report_data_profiling_attribute_scores', 'workflow_activity_id')