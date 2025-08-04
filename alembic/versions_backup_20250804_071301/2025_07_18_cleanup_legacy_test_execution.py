"""Cleanup legacy test execution tables and models

Revision ID: 2025_07_18_cleanup_legacy_test_execution
Revises: 2025_07_18_unified_test_execution_architecture
Create Date: 2025-07-18 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '2025_07_18_cleanup_legacy_test_execution'
down_revision = '2025_07_18_unified_test_execution_architecture'
branch_labels = None
depends_on = None

def upgrade():
    # Drop legacy test execution tables in the correct order (dependencies first)
    
    # Drop audit log table
    op.drop_table('test_execution_audit_logs')
    
    # Drop comparison table
    op.drop_table('test_comparisons')
    
    # Drop bulk execution table
    op.drop_table('bulk_test_executions')
    
    # Drop review table
    op.drop_table('test_result_reviews')
    
    # Drop database test table
    op.drop_table('cycle_report_test_execution_database_tests')
    
    # Drop document analysis table
    op.drop_table('cycle_report_test_execution_document_analyses')
    
    # Drop main test execution table
    op.drop_table('cycle_report_test_executions')
    
    # Drop legacy ENUMs
    op.execute('DROP TYPE IF EXISTS test_type_enum')
    op.execute('DROP TYPE IF EXISTS test_status_enum')
    op.execute('DROP TYPE IF EXISTS test_result_enum')
    op.execute('DROP TYPE IF EXISTS analysis_method_enum')
    op.execute('DROP TYPE IF EXISTS review_status_enum')
    
    # Note: We're not dropping the deprecated test_execution_phases table
    # as it was commented out in the original model


def downgrade():
    # Recreate legacy ENUM types
    op.execute("""
        CREATE TYPE test_type_enum AS ENUM (
            'Document Based',
            'Database Based',
            'Hybrid'
        )
    """)
    
    op.execute("""
        CREATE TYPE test_status_enum AS ENUM (
            'Pending',
            'Running',
            'Completed',
            'Failed',
            'Cancelled',
            'Requires Review'
        )
    """)
    
    op.execute("""
        CREATE TYPE test_result_enum AS ENUM (
            'Pass',
            'Fail',
            'Inconclusive',
            'Pending Review'
        )
    """)
    
    op.execute("""
        CREATE TYPE analysis_method_enum AS ENUM (
            'LLM Analysis',
            'Database Query',
            'Manual Review',
            'Automated Comparison'
        )
    """)
    
    op.execute("""
        CREATE TYPE review_status_enum AS ENUM (
            'Pending',
            'In Review',
            'Approved',
            'Rejected',
            'Requires Revision'
        )
    """)
    
    # Recreate legacy tables in reverse order
    
    # Recreate main test execution table
    op.create_table(
        'cycle_report_test_executions',
        sa.Column('execution_id', sa.Integer, primary_key=True),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('cycle_id', sa.Integer, sa.ForeignKey('test_cycles.cycle_id'), nullable=False),
        sa.Column('report_id', sa.Integer, sa.ForeignKey('reports.id'), nullable=False),
        sa.Column('sample_record_id', sa.String(100), nullable=False),
        sa.Column('attribute_id', sa.Integer, sa.ForeignKey("cycle_report_planning_attributes.id"), nullable=False),
        sa.Column('test_type', postgresql.ENUM('Document Based', 'Database Based', 'Hybrid', name='test_type_enum'), nullable=False),
        sa.Column('analysis_method', postgresql.ENUM('LLM Analysis', 'Database Query', 'Manual Review', 'Automated Comparison', name='analysis_method_enum'), nullable=False),
        sa.Column('priority', sa.String(20), default='Normal', nullable=False),
        sa.Column('custom_instructions', sa.Text, nullable=True),
        sa.Column('status', postgresql.ENUM('Pending', 'Running', 'Completed', 'Failed', 'Cancelled', 'Requires Review', name='test_status_enum'), default='Pending', nullable=False),
        sa.Column('result', postgresql.ENUM('Pass', 'Fail', 'Inconclusive', 'Pending Review', name='test_result_enum'), nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('execution_summary', sa.Text, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('document_analysis_id', sa.Integer, sa.ForeignKey("cycle_report_test_execution_document_analyses.analysis_id"), nullable=True),
        sa.Column('database_test_id', sa.Integer, sa.ForeignKey("cycle_report_test_execution_database_tests.test_id"), nullable=True),
        sa.Column('data_source_id', postgresql.UUID, sa.ForeignKey('data_sources_v2.data_source_id'), nullable=True),
        sa.Column('sample_id', sa.Integer, sa.ForeignKey("cycle_report_sample_selection_samples.sample_id"), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('executed_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Recreate document analysis table
    op.create_table(
        'cycle_report_test_execution_document_analyses',
        sa.Column('analysis_id', sa.Integer, primary_key=True),
        sa.Column('submission_document_id', sa.String(36), sa.ForeignKey('document_submissions.submission_id'), nullable=False),
        sa.Column('sample_record_id', sa.String(100), nullable=False),
        sa.Column('attribute_id', sa.Integer, sa.ForeignKey("cycle_report_planning_attributes.id"), nullable=False),
        sa.Column('analysis_prompt', sa.Text, nullable=True),
        sa.Column('expected_value', sa.String(500), nullable=True),
        sa.Column('confidence_threshold', sa.Float, default=0.8, nullable=False),
        sa.Column('extracted_value', sa.Text, nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('analysis_rationale', sa.Text, nullable=False),
        sa.Column('matches_expected', sa.Boolean, nullable=True),
        sa.Column('validation_notes', postgresql.JSONB, nullable=True),
        sa.Column('llm_model_used', sa.String(100), nullable=True),
        sa.Column('llm_tokens_used', sa.Integer, nullable=True),
        sa.Column('llm_response_raw', sa.Text, nullable=True),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('analysis_duration_ms', sa.Integer, nullable=False),
        sa.Column('analyzed_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
    )
    
    # Recreate database test table
    op.create_table(
        'cycle_report_test_execution_database_tests',
        sa.Column('test_id', sa.Integer, primary_key=True),
        sa.Column('database_submission_id', sa.String(36), nullable=True),
        sa.Column('sample_record_id', sa.String(100), nullable=False),
        sa.Column('attribute_id', sa.Integer, sa.ForeignKey("cycle_report_planning_attributes.id"), nullable=False),
        sa.Column('test_query', sa.Text, nullable=True),
        sa.Column('connection_timeout', sa.Integer, default=30, nullable=False),
        sa.Column('query_timeout', sa.Integer, default=60, nullable=False),
        sa.Column('connection_successful', sa.Boolean, nullable=False),
        sa.Column('query_successful', sa.Boolean, nullable=False),
        sa.Column('retrieved_value', sa.Text, nullable=True),
        sa.Column('record_count', sa.Integer, nullable=True),
        sa.Column('execution_time_ms', sa.Integer, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('connection_string_hash', sa.String(64), nullable=True),
        sa.Column('database_version', sa.String(100), nullable=True),
        sa.Column('actual_query_executed', sa.Text, nullable=True),
        sa.Column('query_plan', sa.Text, nullable=True),
        sa.Column('tested_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('tested_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
    )
    
    # Recreate review table
    op.create_table(
        'test_result_reviews',
        sa.Column('review_id', sa.Integer, primary_key=True),
        sa.Column('execution_id', sa.Integer, sa.ForeignKey('cycle_report_test_executions.execution_id'), nullable=False),
        sa.Column('reviewer_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('review_result', postgresql.ENUM('Pending', 'In Review', 'Approved', 'Rejected', 'Requires Revision', name='review_status_enum'), nullable=False),
        sa.Column('reviewer_comments', sa.Text, nullable=False),
        sa.Column('recommended_action', sa.String(200), nullable=True),
        sa.Column('requires_retest', sa.Boolean, default=False, nullable=False),
        sa.Column('accuracy_score', sa.Float, nullable=True),
        sa.Column('completeness_score', sa.Float, nullable=True),
        sa.Column('consistency_score', sa.Float, nullable=True),
        sa.Column('overall_score', sa.Float, nullable=True),
        sa.Column('review_criteria_used', postgresql.JSONB, nullable=True),
        sa.Column('supporting_evidence', sa.Text, nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('review_duration_ms', sa.Integer, nullable=True),
    )
    
    # Recreate bulk execution table
    op.create_table(
        'bulk_test_executions',
        sa.Column('bulk_execution_id', sa.Integer, primary_key=True),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('execution_mode', sa.String(20), default='Parallel', nullable=False),
        sa.Column('max_concurrent_tests', sa.Integer, default=5, nullable=False),
        sa.Column('total_tests', sa.Integer, nullable=False),
        sa.Column('tests_started', sa.Integer, default=0, nullable=False),
        sa.Column('tests_completed', sa.Integer, default=0, nullable=False),
        sa.Column('tests_failed', sa.Integer, default=0, nullable=False),
        sa.Column('execution_ids', postgresql.JSONB, nullable=False),
        sa.Column('status', sa.String(50), default='Pending', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('initiated_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Recreate comparison table
    op.create_table(
        'test_comparisons',
        sa.Column('comparison_id', sa.Integer, primary_key=True),
        sa.Column('execution_ids', postgresql.JSONB, nullable=False),
        sa.Column('comparison_criteria', postgresql.JSONB, nullable=False),
        sa.Column('comparison_results', postgresql.JSONB, nullable=False),
        sa.Column('consistency_score', sa.Float, nullable=False),
        sa.Column('differences_found', postgresql.JSONB, nullable=True),
        sa.Column('recommendations', postgresql.JSONB, nullable=True),
        sa.Column('analysis_method_used', sa.String(100), nullable=True),
        sa.Column('statistical_metrics', postgresql.JSONB, nullable=True),
        sa.Column('compared_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('comparison_duration_ms', sa.Integer, nullable=False),
        sa.Column('compared_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
    )
    
    # Recreate audit log table
    op.create_table(
        'test_execution_audit_logs',
        sa.Column('log_id', sa.Integer, primary_key=True),
        sa.Column('cycle_id', sa.Integer, sa.ForeignKey('test_cycles.cycle_id'), nullable=False),
        sa.Column('report_id', sa.Integer, sa.ForeignKey('reports.id'), nullable=False),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=True),
        sa.Column('performed_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('performed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('old_values', postgresql.JSONB, nullable=True),
        sa.Column('new_values', postgresql.JSONB, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('execution_time_ms', sa.Integer, nullable=True),
    )