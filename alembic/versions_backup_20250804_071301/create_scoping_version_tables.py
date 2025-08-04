"""Consolidate scoping system into unified version management

Revision ID: scoping_consolidation_001  
Revises: migrate_sample_selection_001
Create Date: 2024-07-18 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'scoping_consolidation_001'
down_revision = 'sample_selection_v2_001'
branch_labels = None
depends_on = None

def drop_legacy_tables():
    """Drop legacy scoping tables that are being replaced by consolidated version management"""
    
    # List of legacy tables to drop (in dependency order)
    legacy_tables = [
        # Decision and review tables
        'cycle_report_scoping_decisions',
        'cycle_report_scoping_tester_decisions', 
        'cycle_report_scoping_report_owner_reviews',
        
        # Submission tables
        'cycle_report_scoping_submissions',
        
        # Versioning tables
        'cycle_report_scoping_decision_versions',
        'cycle_report_scoping_attribute_recommendation_versions',
        
        # Recommendation tables
        'cycle_report_scoping_attribute_recommendations',
        
        # Other legacy tables
        'tester_scoping_decisions',
        'report_owner_scoping_reviews',
        'scoping_decision_versions',
        'attribute_scoping_recommendation_versions',
        'scoping_submissions',
        'scoping_versions',
        'scoping_decisions',
        'scoping_audit_log'
    ]
    
    # Drop tables if they exist
    for table in legacy_tables:
        try:
            op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"Dropped legacy table: {table}")
        except Exception as e:
            print(f"Warning: Could not drop {table}: {e}")
    
    # Drop legacy enums if they exist
    legacy_enums = [
        'scoping_decision_enum',
        'scoping_tester_decision_enum', 
        'scoping_report_owner_decision_enum',
        'scoping_attribute_status_enum',
        'scoping_version_status_enum'
    ]
    
    for enum in legacy_enums:
        try:
            op.execute(f"DROP TYPE IF EXISTS {enum} CASCADE")
            print(f"Dropped legacy enum: {enum}")
        except Exception as e:
            print(f"Warning: Could not drop {enum}: {e}")

def upgrade():
    """Consolidate scoping system into unified version management"""
    
    # First, drop legacy scoping tables if they exist
    drop_legacy_tables()
    
    # Create enums for scoping system
    op.execute("""
        CREATE TYPE scoping_version_status_enum AS ENUM (
            'draft', 'pending_approval', 'approved', 'rejected', 'superseded'
        );
    """)
    
    op.execute("""
        CREATE TYPE scoping_tester_decision_enum AS ENUM (
            'accept', 'decline', 'override'
        );
    """)
    
    op.execute("""
        CREATE TYPE scoping_report_owner_decision_enum AS ENUM (
            'approved', 'rejected', 'pending', 'needs_revision'
        );
    """)
    
    op.execute("""
        CREATE TYPE scoping_attribute_status_enum AS ENUM (
            'pending', 'submitted', 'approved', 'rejected', 'needs_revision'
        );
    """)
    
    # 1. Create cycle_report_scoping_versions table
    op.create_table(
        'cycle_report_scoping_versions',
        sa.Column('version_id', postgresql.UUID(), nullable=False, primary_key=True),
        sa.Column('phase_id', sa.Integer(), sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('workflow_activity_id', sa.Integer(), sa.ForeignKey('workflow_activities.activity_id'), nullable=True),
        
        # Version Management (same as sample selection)
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', sa.Enum('draft', 'pending_approval', 'approved', 'rejected', 'superseded', name='scoping_version_status_enum'), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        
        # Temporal Workflow Context
        sa.Column('workflow_execution_id', sa.String(255), nullable=True),
        sa.Column('workflow_run_id', sa.String(255), nullable=True),
        sa.Column('activity_name', sa.String(100), nullable=True),
        
        # Scoping Summary Statistics
        sa.Column('total_attributes', sa.Integer(), nullable=False, default=0),
        sa.Column('scoped_attributes', sa.Integer(), nullable=False, default=0),
        sa.Column('declined_attributes', sa.Integer(), nullable=False, default=0),
        sa.Column('override_count', sa.Integer(), nullable=False, default=0),
        sa.Column('cde_count', sa.Integer(), nullable=False, default=0),
        sa.Column('recommendation_accuracy', sa.Float(), nullable=True),
        
        # Submission and Approval Workflow
        sa.Column('submission_notes', sa.Text(), nullable=True),
        sa.Column('submitted_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('requested_changes', postgresql.JSONB(), nullable=True),
        
        # Risk and Impact Assessment
        sa.Column('resource_impact_assessment', sa.Text(), nullable=True),
        sa.Column('risk_coverage_assessment', sa.Text(), nullable=True),
        
        # Audit Fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=False),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['parent_version_id'], ['cycle_report_scoping_versions.version_id']),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id']),
        sa.ForeignKeyConstraint(['workflow_activity_id'], ['workflow_activities.activity_id']),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id']),
        
        # Unique constraints
        sa.UniqueConstraint('phase_id', 'version_number', name='uq_scoping_version'),
    )
    
    # 2. Create cycle_report_scoping_attributes table
    op.create_table(
        'cycle_report_scoping_attributes',
        sa.Column('attribute_id', postgresql.UUID(), nullable=False, primary_key=True),
        sa.Column('version_id', postgresql.UUID(), sa.ForeignKey('cycle_report_scoping_versions.version_id'), nullable=False),
        sa.Column('phase_id', sa.Integer(), sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('planning_attribute_id', sa.Integer(), sa.ForeignKey('cycle_report_planning_attributes.id'), nullable=False),
        
        # LLM Recommendation (embedded JSON)
        sa.Column('llm_recommendation', postgresql.JSONB(), nullable=False),
        sa.Column('llm_provider', sa.String(50), nullable=True),
        sa.Column('llm_confidence_score', sa.DECIMAL(5,2), nullable=True),
        sa.Column('llm_rationale', sa.Text(), nullable=True),
        sa.Column('llm_processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('llm_request_payload', postgresql.JSONB(), nullable=True),
        sa.Column('llm_response_payload', postgresql.JSONB(), nullable=True),
        
        # Tester Decision
        sa.Column('tester_decision', sa.Enum('accept', 'decline', 'override', name='scoping_tester_decision_enum'), nullable=True),
        sa.Column('final_scoping', sa.Boolean(), nullable=True),
        sa.Column('tester_rationale', sa.Text(), nullable=True),
        sa.Column('tester_decided_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('tester_decided_at', sa.DateTime(timezone=True), nullable=True),
        
        # Report Owner Decision
        sa.Column('report_owner_decision', sa.Enum('approved', 'rejected', 'pending', 'needs_revision', name='scoping_report_owner_decision_enum'), nullable=True),
        sa.Column('report_owner_notes', sa.Text(), nullable=True),
        sa.Column('report_owner_decided_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('report_owner_decided_at', sa.DateTime(timezone=True), nullable=True),
        
        # Special Cases and Metadata
        sa.Column('is_override', sa.Boolean(), nullable=False, default=False),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('is_cde', sa.Boolean(), nullable=False, default=False),
        sa.Column('has_historical_issues', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_primary_key', sa.Boolean(), nullable=False, default=False),
        
        # Data Quality Integration
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        sa.Column('data_quality_issues', postgresql.JSONB(), nullable=True),
        
        # Expected Source Documents
        sa.Column('expected_source_documents', postgresql.JSONB(), nullable=True),
        sa.Column('search_keywords', postgresql.JSONB(), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(), nullable=True),
        
        # Status
        sa.Column('status', sa.Enum('pending', 'submitted', 'approved', 'rejected', 'needs_revision', name='scoping_attribute_status_enum'), nullable=False),
        
        # Audit Fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=False),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['version_id'], ['cycle_report_scoping_versions.version_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id']),
        sa.ForeignKeyConstraint(['planning_attribute_id'], ['cycle_report_planning_attributes.id']),
        sa.ForeignKeyConstraint(['tester_decided_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['report_owner_decided_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id']),
        
        # Unique constraints
        sa.UniqueConstraint('version_id', 'planning_attribute_id', name='uq_scoping_attribute_version'),
    )
    
    # Create indexes for performance
    op.create_index('idx_scoping_versions_phase', 'cycle_report_scoping_versions', ['phase_id'])
    op.create_index('idx_scoping_versions_status', 'cycle_report_scoping_versions', ['version_status'])
    op.create_index('idx_scoping_versions_parent', 'cycle_report_scoping_versions', ['parent_version_id'])
    op.create_index('idx_scoping_versions_workflow', 'cycle_report_scoping_versions', ['workflow_execution_id'])
    op.create_index('idx_scoping_versions_created_at', 'cycle_report_scoping_versions', ['created_at'])
    op.create_index('idx_scoping_versions_submitted_at', 'cycle_report_scoping_versions', ['submitted_at'])
    op.create_index('idx_scoping_versions_approved_at', 'cycle_report_scoping_versions', ['approved_at'])
    op.create_index('idx_scoping_versions_current', 'cycle_report_scoping_versions', ['phase_id', 'version_status'])
    
    op.create_index('idx_scoping_attributes_version', 'cycle_report_scoping_attributes', ['version_id'])
    op.create_index('idx_scoping_attributes_phase', 'cycle_report_scoping_attributes', ['phase_id'])
    op.create_index('idx_scoping_attributes_planning_attr', 'cycle_report_scoping_attributes', ['planning_attribute_id'])
    op.create_index('idx_scoping_attributes_status', 'cycle_report_scoping_attributes', ['status'])
    op.create_index('idx_scoping_attributes_tester_decision', 'cycle_report_scoping_attributes', ['tester_decision'])
    op.create_index('idx_scoping_attributes_owner_decision', 'cycle_report_scoping_attributes', ['report_owner_decision'])
    op.create_index('idx_scoping_attributes_final_scoping', 'cycle_report_scoping_attributes', ['final_scoping'])
    op.create_index('idx_scoping_attributes_is_override', 'cycle_report_scoping_attributes', ['is_override'])
    op.create_index('idx_scoping_attributes_is_cde', 'cycle_report_scoping_attributes', ['is_cde'])
    op.create_index('idx_scoping_attributes_created_at', 'cycle_report_scoping_attributes', ['created_at'])
    op.create_index('idx_scoping_attributes_tester_decided_at', 'cycle_report_scoping_attributes', ['tester_decided_at'])
    op.create_index('idx_scoping_attributes_owner_decided_at', 'cycle_report_scoping_attributes', ['report_owner_decided_at'])
    
    # Composite indexes for common queries
    op.create_index('idx_scoping_attributes_version_status', 'cycle_report_scoping_attributes', ['version_id', 'status'])
    op.create_index('idx_scoping_attributes_version_decisions', 'cycle_report_scoping_attributes', ['version_id', 'tester_decision', 'report_owner_decision'])
    op.create_index('idx_scoping_attributes_phase_status', 'cycle_report_scoping_attributes', ['phase_id', 'status'])
    op.create_index('idx_scoping_attributes_scoping_flags', 'cycle_report_scoping_attributes', ['final_scoping', 'is_override', 'is_cde'])
    
    # Create triggers for updated_at columns
    op.execute("""
        CREATE OR REPLACE FUNCTION update_scoping_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_scoping_versions_updated_at
            BEFORE UPDATE ON cycle_report_scoping_versions
            FOR EACH ROW
            EXECUTE FUNCTION update_scoping_updated_at_column();
        
        CREATE TRIGGER update_scoping_attributes_updated_at
            BEFORE UPDATE ON cycle_report_scoping_attributes
            FOR EACH ROW
            EXECUTE FUNCTION update_scoping_updated_at_column();
    """)
    
    # Create function to update version summaries
    op.execute("""
        CREATE OR REPLACE FUNCTION update_scoping_version_summary()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE cycle_report_scoping_versions
            SET 
                total_attributes = (
                    SELECT COUNT(*) 
                    FROM cycle_report_scoping_attributes 
                    WHERE version_id = NEW.version_id
                ),
                scoped_attributes = (
                    SELECT COUNT(*) 
                    FROM cycle_report_scoping_attributes 
                    WHERE version_id = NEW.version_id AND final_scoping = TRUE
                ),
                declined_attributes = (
                    SELECT COUNT(*) 
                    FROM cycle_report_scoping_attributes 
                    WHERE version_id = NEW.version_id AND final_scoping = FALSE
                ),
                override_count = (
                    SELECT COUNT(*) 
                    FROM cycle_report_scoping_attributes 
                    WHERE version_id = NEW.version_id AND is_override = TRUE
                ),
                cde_count = (
                    SELECT COUNT(*) 
                    FROM cycle_report_scoping_attributes 
                    WHERE version_id = NEW.version_id AND is_cde = TRUE
                ),
                recommendation_accuracy = (
                    SELECT ROUND(
                        AVG(CASE 
                            WHEN (llm_recommendation->>'recommended_action' = 'test' AND final_scoping = TRUE) 
                                OR (llm_recommendation->>'recommended_action' = 'skip' AND final_scoping = FALSE) 
                            THEN 1.0 
                            ELSE 0.0 
                        END), 3
                    )
                    FROM cycle_report_scoping_attributes 
                    WHERE version_id = NEW.version_id AND final_scoping IS NOT NULL
                )
            WHERE version_id = NEW.version_id;
            
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_scoping_version_summary_trigger
            AFTER INSERT OR UPDATE OR DELETE ON cycle_report_scoping_attributes
            FOR EACH ROW
            EXECUTE FUNCTION update_scoping_version_summary();
    """)


def downgrade():
    """Drop the consolidated scoping version tables and restore legacy structure"""
    
    # Drop triggers and functions
    op.execute("""
        DROP TRIGGER IF EXISTS update_scoping_versions_updated_at ON cycle_report_scoping_versions;
        DROP TRIGGER IF EXISTS update_scoping_attributes_updated_at ON cycle_report_scoping_attributes;
        DROP TRIGGER IF EXISTS update_scoping_version_summary_trigger ON cycle_report_scoping_attributes;
        DROP FUNCTION IF EXISTS update_scoping_updated_at_column();
        DROP FUNCTION IF EXISTS update_scoping_version_summary();
    """)
    
    # Drop indexes
    op.drop_index('idx_scoping_attributes_scoping_flags', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_phase_status', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_version_decisions', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_version_status', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_owner_decided_at', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_tester_decided_at', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_created_at', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_is_cde', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_is_override', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_final_scoping', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_owner_decision', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_tester_decision', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_status', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_planning_attr', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_phase', 'cycle_report_scoping_attributes')
    op.drop_index('idx_scoping_attributes_version', 'cycle_report_scoping_attributes')
    
    op.drop_index('idx_scoping_versions_current', 'cycle_report_scoping_versions')
    op.drop_index('idx_scoping_versions_approved_at', 'cycle_report_scoping_versions')
    op.drop_index('idx_scoping_versions_submitted_at', 'cycle_report_scoping_versions')
    op.drop_index('idx_scoping_versions_created_at', 'cycle_report_scoping_versions')
    op.drop_index('idx_scoping_versions_workflow', 'cycle_report_scoping_versions')
    op.drop_index('idx_scoping_versions_parent', 'cycle_report_scoping_versions')
    op.drop_index('idx_scoping_versions_status', 'cycle_report_scoping_versions')
    op.drop_index('idx_scoping_versions_phase', 'cycle_report_scoping_versions')
    
    # Drop tables
    op.drop_table('cycle_report_scoping_attributes')
    op.drop_table('cycle_report_scoping_versions')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS scoping_attribute_status_enum;")
    op.execute("DROP TYPE IF EXISTS scoping_report_owner_decision_enum;")
    op.execute("DROP TYPE IF EXISTS scoping_tester_decision_enum;")
    op.execute("DROP TYPE IF EXISTS scoping_version_status_enum;")