"""Create unified test execution architecture

Revision ID: 2025_07_18_unified_test_execution_architecture
Revises: 2025_07_11_redesign_migration
Create Date: 2025-07-18 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '2025_07_18_unified_test_execution_architecture'
down_revision = '2025_07_11_redesign_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Create unified test execution results table
    op.create_table(
        'cycle_report_test_execution_results',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('cycle_id', sa.Integer, sa.ForeignKey('test_cycles.cycle_id'), nullable=False),
        sa.Column('report_id', sa.Integer, sa.ForeignKey('reports.id'), nullable=False),
        sa.Column('test_case_id', sa.String(255), sa.ForeignKey('cycle_report_test_cases.test_case_id'), nullable=False),
        
        # Link to approved evidence from Request for Information
        sa.Column('evidence_id', sa.Integer, sa.ForeignKey('cycle_report_request_info_testcase_source_evidence.id'), nullable=False),
        
        # Execution versioning
        sa.Column('execution_number', sa.Integer, nullable=False),
        sa.Column('is_latest_execution', sa.Boolean, default=False),
        sa.Column('execution_reason', sa.String(100)),  # 'initial', 'retry', 'evidence_updated', 'manual_rerun'
        
        # Test execution configuration
        sa.Column('test_type', sa.String(50), nullable=False),  # 'document_analysis', 'database_test', 'manual_test', 'hybrid'
        sa.Column('analysis_method', sa.String(50), nullable=False),  # 'llm_analysis', 'database_query', 'manual_review'
        
        # Core test data
        sa.Column('sample_value', sa.Text),
        sa.Column('extracted_value', sa.Text),
        sa.Column('expected_value', sa.Text),
        
        # Test results
        sa.Column('test_result', sa.String(50)),  # 'pass', 'fail', 'inconclusive', 'pending_review'
        sa.Column('comparison_result', sa.Boolean),
        sa.Column('variance_details', postgresql.JSONB),
        
        # LLM Analysis Results
        sa.Column('llm_confidence_score', sa.Float),
        sa.Column('llm_analysis_rationale', sa.Text),
        sa.Column('llm_model_used', sa.String(100)),
        sa.Column('llm_tokens_used', sa.Integer),
        sa.Column('llm_response_raw', postgresql.JSONB),
        sa.Column('llm_processing_time_ms', sa.Integer),
        
        # Database Test Results
        sa.Column('database_query_executed', sa.Text),
        sa.Column('database_result_count', sa.Integer),
        sa.Column('database_execution_time_ms', sa.Integer),
        sa.Column('database_result_sample', postgresql.JSONB),
        
        # Execution status and timing
        sa.Column('execution_status', sa.String(50), default='pending'),  # 'pending', 'running', 'completed', 'failed', 'cancelled'
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('processing_time_ms', sa.Integer),
        
        # Error handling
        sa.Column('error_message', sa.Text),
        sa.Column('error_details', postgresql.JSONB),
        sa.Column('retry_count', sa.Integer, default=0),
        
        # Comprehensive analysis results
        sa.Column('analysis_results', postgresql.JSONB, nullable=False),
        
        # Evidence context
        sa.Column('evidence_validation_status', sa.String(50)),
        sa.Column('evidence_version_number', sa.Integer),
        
        # Test execution summary
        sa.Column('execution_summary', sa.Text),
        sa.Column('processing_notes', sa.Text),
        
        # Execution metadata
        sa.Column('executed_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('execution_method', sa.String(50), nullable=False),  # 'automatic', 'manual', 'scheduled'
        
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
    )
    
    # Create unique constraints
    op.create_unique_constraint(
        'uq_test_execution_results_test_case_execution',
        'cycle_report_test_execution_results',
        ['test_case_id', 'execution_number']
    )
    
    # Create conditional unique constraint for latest execution
    op.execute("""
        CREATE UNIQUE INDEX uq_test_execution_results_latest_execution
        ON cycle_report_test_execution_results(test_case_id, is_latest_execution)
        WHERE is_latest_execution = TRUE
    """)
    
    # Create check constraint for evidence validation
    op.create_check_constraint(
        'ck_test_execution_evidence_approved',
        'cycle_report_test_execution_results',
        "evidence_validation_status IN ('valid', 'approved')"
    )
    
    # Create test execution reviews table
    op.create_table(
        'cycle_report_test_execution_reviews',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('execution_id', sa.Integer, sa.ForeignKey('cycle_report_test_execution_results.id'), nullable=False),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        
        # Review details
        sa.Column('review_status', sa.String(50), nullable=False),  # 'approved', 'rejected', 'requires_revision'
        sa.Column('review_notes', sa.Text),
        sa.Column('reviewer_comments', sa.Text),
        sa.Column('recommended_action', sa.String(100)),  # 'approve', 'retest', 'escalate', 'manual_review'
        
        # Quality assessment
        sa.Column('accuracy_score', sa.Float),
        sa.Column('completeness_score', sa.Float),
        sa.Column('consistency_score', sa.Float),
        sa.Column('overall_score', sa.Float),
        
        # Review criteria
        sa.Column('review_criteria_used', postgresql.JSONB),
        
        # Follow-up actions
        sa.Column('requires_retest', sa.Boolean, default=False),
        sa.Column('retest_reason', sa.Text),
        sa.Column('escalation_required', sa.Boolean, default=False),
        sa.Column('escalation_reason', sa.Text),
        
        # Approval workflow
        sa.Column('reviewed_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create unique constraint for reviews
    op.create_unique_constraint(
        'uq_test_execution_reviews_execution_reviewer',
        'cycle_report_test_execution_reviews',
        ['execution_id', 'reviewed_by']
    )
    
    # Create test execution audit table
    op.create_table(
        'cycle_report_test_execution_audit',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('execution_id', sa.Integer, sa.ForeignKey('cycle_report_test_execution_results.id'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),  # 'started', 'completed', 'failed', 'reviewed', 'approved', 'rejected'
        sa.Column('action_details', postgresql.JSONB),
        sa.Column('performed_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('performed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Context information
        sa.Column('previous_status', sa.String(50)),
        sa.Column('new_status', sa.String(50)),
        sa.Column('change_reason', sa.Text),
        sa.Column('system_info', postgresql.JSONB),
    )
    
    # Create indexes for performance
    op.create_index('idx_test_execution_results_phase_id', 'cycle_report_test_execution_results', ['phase_id'])
    op.create_index('idx_test_execution_results_cycle_report', 'cycle_report_test_execution_results', ['cycle_id', 'report_id'])
    op.create_index('idx_test_execution_results_test_case_id', 'cycle_report_test_execution_results', ['test_case_id'])
    op.create_index('idx_test_execution_results_evidence_id', 'cycle_report_test_execution_results', ['evidence_id'])
    op.create_index('idx_test_execution_results_execution_status', 'cycle_report_test_execution_results', ['execution_status'])
    op.create_index('idx_test_execution_results_executed_by', 'cycle_report_test_execution_results', ['executed_by'])
    op.create_index('idx_test_execution_results_created_at', 'cycle_report_test_execution_results', ['created_at'])
    
    op.create_index('idx_test_execution_reviews_execution_id', 'cycle_report_test_execution_reviews', ['execution_id'])
    op.create_index('idx_test_execution_reviews_phase_id', 'cycle_report_test_execution_reviews', ['phase_id'])
    op.create_index('idx_test_execution_reviews_status', 'cycle_report_test_execution_reviews', ['review_status'])
    op.create_index('idx_test_execution_reviews_reviewed_by', 'cycle_report_test_execution_reviews', ['reviewed_by'])
    
    op.create_index('idx_test_execution_audit_execution_id', 'cycle_report_test_execution_audit', ['execution_id'])
    op.create_index('idx_test_execution_audit_performed_by', 'cycle_report_test_execution_audit', ['performed_by'])
    op.create_index('idx_test_execution_audit_performed_at', 'cycle_report_test_execution_audit', ['performed_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_test_execution_audit_performed_at', table_name='cycle_report_test_execution_audit')
    op.drop_index('idx_test_execution_audit_performed_by', table_name='cycle_report_test_execution_audit')
    op.drop_index('idx_test_execution_audit_execution_id', table_name='cycle_report_test_execution_audit')
    
    op.drop_index('idx_test_execution_reviews_reviewed_by', table_name='cycle_report_test_execution_reviews')
    op.drop_index('idx_test_execution_reviews_status', table_name='cycle_report_test_execution_reviews')
    op.drop_index('idx_test_execution_reviews_phase_id', table_name='cycle_report_test_execution_reviews')
    op.drop_index('idx_test_execution_reviews_execution_id', table_name='cycle_report_test_execution_reviews')
    
    op.drop_index('idx_test_execution_results_created_at', table_name='cycle_report_test_execution_results')
    op.drop_index('idx_test_execution_results_executed_by', table_name='cycle_report_test_execution_results')
    op.drop_index('idx_test_execution_results_execution_status', table_name='cycle_report_test_execution_results')
    op.drop_index('idx_test_execution_results_evidence_id', table_name='cycle_report_test_execution_results')
    op.drop_index('idx_test_execution_results_test_case_id', table_name='cycle_report_test_execution_results')
    op.drop_index('idx_test_execution_results_cycle_report', table_name='cycle_report_test_execution_results')
    op.drop_index('idx_test_execution_results_phase_id', table_name='cycle_report_test_execution_results')
    
    # Drop conditional unique index
    op.execute("DROP INDEX IF EXISTS uq_test_execution_results_latest_execution")
    
    # Drop tables
    op.drop_table('cycle_report_test_execution_audit')
    op.drop_table('cycle_report_test_execution_reviews')
    op.drop_table('cycle_report_test_execution_results')