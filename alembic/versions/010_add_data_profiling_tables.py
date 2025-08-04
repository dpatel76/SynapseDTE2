"""Add data profiling tables

Revision ID: 010_add_data_profiling_tables
Revises: 009_add_compensation_retry_tables
Create Date: 2025-01-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '010_add_data_profiling_tables'
down_revision = '009'
branch_labels = None
depends_on = None

def upgrade():
    # Create enums
    op.execute("CREATE TYPE profilingrulestatus AS ENUM ('pending', 'approved', 'rejected')")
    op.execute("CREATE TYPE profilingruletype AS ENUM ('completeness', 'validity', 'accuracy', 'consistency', 'uniqueness', 'timeliness', 'regulatory')")
    
    # Create data_profiling_phases table
    op.create_table('data_profiling_phases',
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Not Started'),
        sa.Column('data_requested_at', sa.DateTime(), nullable=True),
        sa.Column('data_received_at', sa.DateTime(), nullable=True),
        sa.Column('rules_generated_at', sa.DateTime(), nullable=True),
        sa.Column('profiling_executed_at', sa.DateTime(), nullable=True),
        sa.Column('phase_completed_at', sa.DateTime(), nullable=True),
        sa.Column('started_by', sa.Integer(), nullable=True),
        sa.Column('data_requested_by', sa.Integer(), nullable=True),
        sa.Column('completed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['completed_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['data_requested_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.ForeignKeyConstraint(['started_by'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('phase_id')
    )
    op.create_index(op.f('ix_data_profiling_phases_phase_id'), 'data_profiling_phases', ['phase_id'], unique=False)
    
    # Create data_profiling_files table
    op.create_table('data_profiling_files',
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_format', sa.String(length=50), nullable=False),
        sa.Column('delimiter', sa.String(length=10), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('columns_metadata', sa.JSON(), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('validation_errors', sa.JSON(), nullable=True),
        sa.Column('missing_attributes', sa.JSON(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['phase_id'], ['data_profiling_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('file_id')
    )
    op.create_index(op.f('ix_data_profiling_files_file_id'), 'data_profiling_files', ['file_id'], unique=False)
    
    # Create profiling_rules table
    op.create_table('profiling_rules',
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=255), nullable=False),
        sa.Column('rule_type', postgresql.ENUM('completeness', 'validity', 'accuracy', 'consistency', 'uniqueness', 'timeliness', 'regulatory', name='profilingruletype'), nullable=False),
        sa.Column('rule_description', sa.Text(), nullable=True),
        sa.Column('rule_code', sa.Text(), nullable=False),
        sa.Column('rule_parameters', sa.JSON(), nullable=True),
        sa.Column('llm_provider', sa.String(length=50), nullable=True),
        sa.Column('llm_rationale', sa.Text(), nullable=True),
        sa.Column('regulatory_reference', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', name='profilingrulestatus'), nullable=False, server_default='pending'),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('is_executable', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('execution_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['attribute_id'], ['report_attributes.attribute_id'], ),
        sa.ForeignKeyConstraint(['phase_id'], ['data_profiling_phases.phase_id'], ),
        sa.PrimaryKeyConstraint('rule_id')
    )
    op.create_index(op.f('ix_profiling_rules_rule_id'), 'profiling_rules', ['rule_id'], unique=False)
    
    # Create profiling_results table
    op.create_table('profiling_results',
        sa.Column('result_id', sa.Integer(), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('execution_status', sa.String(length=50), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('passed_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('pass_rate', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('result_summary', sa.JSON(), nullable=True),
        sa.Column('failed_records', sa.JSON(), nullable=True),
        sa.Column('result_details', sa.Text(), nullable=True),
        sa.Column('quality_impact', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('severity', sa.String(length=50), nullable=True, server_default='medium'),
        sa.Column('has_anomaly', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('anomaly_description', sa.Text(), nullable=True),
        sa.Column('anomaly_marked_by', sa.Integer(), nullable=True),
        sa.Column('anomaly_marked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['anomaly_marked_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['attribute_id'], ['report_attributes.attribute_id'], ),
        sa.ForeignKeyConstraint(['phase_id'], ['data_profiling_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['profiling_rules.rule_id'], ),
        sa.PrimaryKeyConstraint('result_id')
    )
    op.create_index(op.f('ix_profiling_results_result_id'), 'profiling_results', ['result_id'], unique=False)
    
    # Create attribute_profiling_scores table
    op.create_table('attribute_profiling_scores',
        sa.Column('score_id', sa.Integer(), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('overall_quality_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('completeness_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('validity_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('accuracy_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('consistency_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('uniqueness_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_rules_executed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('rules_passed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('rules_failed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_values', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('null_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('unique_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('data_type_detected', sa.String(length=50), nullable=True),
        sa.Column('pattern_detected', sa.String(length=255), nullable=True),
        sa.Column('distribution_type', sa.String(length=50), nullable=True),
        sa.Column('has_anomalies', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('anomaly_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('anomaly_types', sa.JSON(), nullable=True),
        sa.Column('testing_recommendation', sa.Text(), nullable=True),
        sa.Column('risk_assessment', sa.Text(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['attribute_id'], ['report_attributes.attribute_id'], ),
        sa.ForeignKeyConstraint(['phase_id'], ['data_profiling_phases.phase_id'], ),
        sa.PrimaryKeyConstraint('score_id')
    )
    op.create_index(op.f('ix_attribute_profiling_scores_score_id'), 'attribute_profiling_scores', ['score_id'], unique=False)
    
    # Create indexes for foreign keys
    op.create_index('idx_data_profiling_phases_cycle_report', 'data_profiling_phases', ['cycle_id', 'report_id'])
    op.create_index('idx_data_profiling_files_phase', 'data_profiling_files', ['phase_id'])
    op.create_index('idx_profiling_rules_phase', 'profiling_rules', ['phase_id'])
    op.create_index('idx_profiling_rules_attribute', 'profiling_rules', ['attribute_id'])
    op.create_index('idx_profiling_results_phase', 'profiling_results', ['phase_id'])
    op.create_index('idx_profiling_results_rule', 'profiling_results', ['rule_id'])
    op.create_index('idx_profiling_results_attribute', 'profiling_results', ['attribute_id'])
    op.create_index('idx_attribute_profiling_scores_phase', 'attribute_profiling_scores', ['phase_id'])
    op.create_index('idx_attribute_profiling_scores_attribute', 'attribute_profiling_scores', ['attribute_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_attribute_profiling_scores_attribute', table_name='attribute_profiling_scores')
    op.drop_index('idx_attribute_profiling_scores_phase', table_name='attribute_profiling_scores')
    op.drop_index('idx_profiling_results_attribute', table_name='profiling_results')
    op.drop_index('idx_profiling_results_rule', table_name='profiling_results')
    op.drop_index('idx_profiling_results_phase', table_name='profiling_results')
    op.drop_index('idx_profiling_rules_attribute', table_name='profiling_rules')
    op.drop_index('idx_profiling_rules_phase', table_name='profiling_rules')
    op.drop_index('idx_data_profiling_files_phase', table_name='data_profiling_files')
    op.drop_index('idx_data_profiling_phases_cycle_report', table_name='data_profiling_phases')
    
    # Drop tables
    op.drop_index(op.f('ix_attribute_profiling_scores_score_id'), table_name='attribute_profiling_scores')
    op.drop_table('attribute_profiling_scores')
    op.drop_index(op.f('ix_profiling_results_result_id'), table_name='profiling_results')
    op.drop_table('profiling_results')
    op.drop_index(op.f('ix_profiling_rules_rule_id'), table_name='profiling_rules')
    op.drop_table('profiling_rules')
    op.drop_index(op.f('ix_data_profiling_files_file_id'), table_name='data_profiling_files')
    op.drop_table('data_profiling_files')
    op.drop_index(op.f('ix_data_profiling_phases_phase_id'), table_name='data_profiling_phases')
    op.drop_table('data_profiling_phases')
    
    # Drop enums
    op.execute('DROP TYPE profilingruletype')
    op.execute('DROP TYPE profilingrulestatus')