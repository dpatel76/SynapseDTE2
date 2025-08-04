"""unified_data_profiling_architecture

Revision ID: unified_data_profiling_001
Revises: 
Create Date: 2025-07-18 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'unified_data_profiling_001'
down_revision = 'scoping_consolidation_001'
branch_labels = None
depends_on = None


def upgrade():
    """Create unified data profiling architecture following exact same pattern as sample selection/scoping"""
    
    # Create ENUM types for data profiling
    version_status_enum = sa.Enum('draft', 'pending_approval', 'approved', 'rejected', 'superseded', name='version_status_enum')
    rule_type_enum = sa.Enum('completeness', 'validity', 'accuracy', 'consistency', 'uniqueness', name='rule_type_enum')
    severity_enum = sa.Enum('low', 'medium', 'high', name='severity_enum')
    decision_enum = sa.Enum('approve', 'reject', 'request_changes', name='decision_enum')
    rule_status_enum = sa.Enum('pending', 'submitted', 'approved', 'rejected', name='rule_status_enum')
    data_source_type_enum = sa.Enum('file_upload', 'database_source', name='data_source_type_enum')
    
    # Create ENUMs if they don't exist
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'version_status_enum') THEN
                CREATE TYPE version_status_enum AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'superseded');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rule_type_enum') THEN
                CREATE TYPE rule_type_enum AS ENUM ('completeness', 'validity', 'accuracy', 'consistency', 'uniqueness');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'severity_enum') THEN
                CREATE TYPE severity_enum AS ENUM ('low', 'medium', 'high');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'decision_enum') THEN
                CREATE TYPE decision_enum AS ENUM ('approve', 'reject', 'request_changes');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rule_status_enum') THEN
                CREATE TYPE rule_status_enum AS ENUM ('pending', 'submitted', 'approved', 'rejected');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'data_source_type_enum') THEN
                CREATE TYPE data_source_type_enum AS ENUM ('file_upload', 'database_source');
            END IF;
        END $$;
    """)
    
    # Table 1: Rule Version Management (exact same pattern as sample selection/scoping)
    op.create_table(
        'cycle_report_data_profiling_rule_versions',
        sa.Column('version_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Phase Integration (only phase_id needed)
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('workflow_activity_id', sa.Integer, sa.ForeignKey('workflow_activities.activity_id'), nullable=True),
        
        # Version Management (exact same as sample selection/scoping)
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('version_status', version_status_enum, nullable=False, server_default='draft'),
        sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cycle_report_data_profiling_rule_versions.version_id'), nullable=True),
        
        # Temporal Workflow Context
        sa.Column('workflow_execution_id', sa.String(255), nullable=True),
        sa.Column('workflow_run_id', sa.String(255), nullable=True),
        
        # Rule Set Summary
        sa.Column('total_rules', sa.Integer, nullable=False, server_default='0'),
        sa.Column('approved_rules', sa.Integer, nullable=False, server_default='0'),
        sa.Column('rejected_rules', sa.Integer, nullable=False, server_default='0'),
        
        # Data Source Reference (from planning phase)
        sa.Column('data_source_type', data_source_type_enum, nullable=True),
        sa.Column('planning_data_source_id', sa.Integer, nullable=True),
        sa.Column('source_table_name', sa.String(255), nullable=True),
        sa.Column('source_file_path', sa.String(500), nullable=True),
        
        # Execution Summary
        sa.Column('total_records_processed', sa.Integer, nullable=True),
        sa.Column('overall_quality_score', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('execution_job_id', sa.String(255), nullable=True),
        
        # Approval Workflow
        sa.Column('submitted_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        
        # Audit Fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        
        # Constraints
        sa.UniqueConstraint('phase_id', 'version_number', name='uq_data_profiling_version_per_phase')
    )
    
    # Table 2: Individual Rules (NO execution results stored here)
    op.create_table(
        'cycle_report_data_profiling_rules',
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Version Reference
        sa.Column('version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cycle_report_data_profiling_rule_versions.version_id', ondelete='CASCADE'), nullable=False),
        
        # Phase Integration
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        
        # Attribute Reference
        sa.Column('attribute_id', sa.Integer, sa.ForeignKey('cycle_report_planning_attributes.id'), nullable=False),
        
        # Rule Definition (NO execution results here)
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('rule_type', rule_type_enum, nullable=False),
        sa.Column('rule_description', sa.Text, nullable=True),
        sa.Column('rule_code', sa.Text, nullable=False),
        sa.Column('rule_parameters', postgresql.JSONB, nullable=True),
        
        # LLM Metadata
        sa.Column('llm_provider', sa.String(50), nullable=True),
        sa.Column('llm_rationale', sa.Text, nullable=True),
        sa.Column('llm_confidence_score', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('regulatory_reference', sa.Text, nullable=True),
        
        # Rule Configuration
        sa.Column('is_executable', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('execution_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('severity', severity_enum, nullable=False, server_default='medium'),
        
        # Dual Decision Model (same as scoping)
        sa.Column('tester_decision', decision_enum, nullable=True),
        sa.Column('tester_decided_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('tester_decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tester_notes', sa.Text, nullable=True),
        
        sa.Column('report_owner_decision', decision_enum, nullable=True),
        sa.Column('report_owner_decided_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('report_owner_decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('report_owner_notes', sa.Text, nullable=True),
        
        # Status
        sa.Column('status', rule_status_enum, nullable=False, server_default='pending'),
        
        # Audit Fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        
        # Constraints
        sa.UniqueConstraint('version_id', 'attribute_id', 'rule_name', name='uq_data_profiling_rule_per_version_attribute')
    )
    
    # Create indexes for performance
    op.create_index('idx_data_profiling_rule_versions_phase', 'cycle_report_data_profiling_rule_versions', ['phase_id'])
    op.create_index('idx_data_profiling_rule_versions_status', 'cycle_report_data_profiling_rule_versions', ['version_status'])
    op.create_index('idx_data_profiling_rule_versions_parent', 'cycle_report_data_profiling_rule_versions', ['parent_version_id'])
    op.create_index('idx_data_profiling_rule_versions_workflow', 'cycle_report_data_profiling_rule_versions', ['workflow_execution_id'])
    
    op.create_index('idx_data_profiling_rules_version', 'cycle_report_data_profiling_rules', ['version_id'])
    op.create_index('idx_data_profiling_rules_phase', 'cycle_report_data_profiling_rules', ['phase_id'])
    op.create_index('idx_data_profiling_rules_attribute', 'cycle_report_data_profiling_rules', ['attribute_id'])
    op.create_index('idx_data_profiling_rules_status', 'cycle_report_data_profiling_rules', ['status'])
    op.create_index('idx_data_profiling_rules_type', 'cycle_report_data_profiling_rules', ['rule_type'])
    op.create_index('idx_data_profiling_rules_tester_decision', 'cycle_report_data_profiling_rules', ['tester_decision'])
    op.create_index('idx_data_profiling_rules_report_owner_decision', 'cycle_report_data_profiling_rules', ['report_owner_decision'])


def downgrade():
    """Drop unified data profiling architecture"""
    
    # Drop indexes first
    op.drop_index('idx_data_profiling_rules_report_owner_decision', table_name='cycle_report_data_profiling_rules')
    op.drop_index('idx_data_profiling_rules_tester_decision', table_name='cycle_report_data_profiling_rules')
    op.drop_index('idx_data_profiling_rules_type', table_name='cycle_report_data_profiling_rules')
    op.drop_index('idx_data_profiling_rules_status', table_name='cycle_report_data_profiling_rules')
    op.drop_index('idx_data_profiling_rules_attribute', table_name='cycle_report_data_profiling_rules')
    op.drop_index('idx_data_profiling_rules_phase', table_name='cycle_report_data_profiling_rules')
    op.drop_index('idx_data_profiling_rules_version', table_name='cycle_report_data_profiling_rules')
    
    op.drop_index('idx_data_profiling_rule_versions_workflow', table_name='cycle_report_data_profiling_rule_versions')
    op.drop_index('idx_data_profiling_rule_versions_parent', table_name='cycle_report_data_profiling_rule_versions')
    op.drop_index('idx_data_profiling_rule_versions_status', table_name='cycle_report_data_profiling_rule_versions')
    op.drop_index('idx_data_profiling_rule_versions_phase', table_name='cycle_report_data_profiling_rule_versions')
    
    # Drop tables
    op.drop_table('cycle_report_data_profiling_rules')
    op.drop_table('cycle_report_data_profiling_rule_versions')
    
    # Drop ENUMs
    op.execute('DROP TYPE IF EXISTS data_source_type_enum')
    op.execute('DROP TYPE IF EXISTS rule_status_enum')
    op.execute('DROP TYPE IF EXISTS decision_enum')
    op.execute('DROP TYPE IF EXISTS severity_enum')
    op.execute('DROP TYPE IF EXISTS rule_type_enum')
    op.execute('DROP TYPE IF EXISTS version_status_enum')