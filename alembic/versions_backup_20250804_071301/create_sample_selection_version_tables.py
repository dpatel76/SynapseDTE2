"""Create new simplified sample selection version tables

Revision ID: sample_selection_v2_001
Revises: 
Create Date: 2024-07-18 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'sample_selection_v2_001'
down_revision = 'unify_scoping_decisions'
branch_labels = None
depends_on = None

def upgrade():
    """Create new simplified sample selection version tables"""
    
    # Create enums for sample selection
    op.execute("""
        CREATE TYPE sample_category_enum AS ENUM (
            'clean', 'anomaly', 'boundary'
        );
    """)
    
    op.execute("""
        CREATE TYPE sample_decision_enum AS ENUM (
            'include', 'exclude', 'pending'
        );
    """)
    
    op.execute("""
        CREATE TYPE sample_source_enum AS ENUM (
            'tester', 'llm', 'manual', 'carried_forward'
        );
    """)
    
    # 1. Create cycle_report_sample_selection_versions table
    op.create_table(
        'cycle_report_sample_selection_versions',
        sa.Column('version_id', postgresql.UUID(), nullable=False, primary_key=True),
        sa.Column('phase_id', sa.Integer(), sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', sa.Enum('draft', 'pending_approval', 'approved', 'rejected', 'superseded', name='version_status'), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        
        # Temporal workflow context
        sa.Column('workflow_execution_id', sa.String(255), nullable=False),
        sa.Column('workflow_run_id', sa.String(255), nullable=False),
        sa.Column('activity_name', sa.String(100), nullable=False),
        
        # Metadata
        sa.Column('selection_criteria', postgresql.JSONB(), nullable=False),
        sa.Column('target_sample_size', sa.Integer(), nullable=False),
        sa.Column('actual_sample_size', sa.Integer(), nullable=False, default=0),
        sa.Column('intelligent_sampling_config', postgresql.JSONB(), nullable=True),
        sa.Column('distribution_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('data_source_config', postgresql.JSONB(), nullable=True),
        sa.Column('submission_notes', sa.Text(), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        
        # Timestamps and tracking
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['parent_version_id'], ['cycle_report_sample_selection_versions.version_id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id']),
        
        # Unique constraints
        sa.UniqueConstraint('phase_id', 'version_number', name='uq_sample_selection_version'),
    )
    
    # 2. Create cycle_report_sample_selection_samples table
    op.create_table(
        'cycle_report_sample_selection_samples',
        sa.Column('sample_id', postgresql.UUID(), nullable=False, primary_key=True),
        sa.Column('version_id', postgresql.UUID(), sa.ForeignKey('cycle_report_sample_selection_versions.version_id'), nullable=False),
        sa.Column('phase_id', sa.Integer(), sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('lob_id', sa.Integer(), sa.ForeignKey('lobs.lob_id'), nullable=False),
        
        # Sample identification
        sa.Column('sample_identifier', sa.String(255), nullable=False),
        sa.Column('sample_data', postgresql.JSONB(), nullable=False),
        sa.Column('sample_category', sa.Enum('clean', 'anomaly', 'boundary', name='sample_category_enum'), nullable=False),
        sa.Column('sample_source', sa.Enum('tester', 'llm', 'manual', 'carried_forward', name='sample_source_enum'), nullable=False),
        
        # Decision tracking
        sa.Column('tester_decision', sa.Enum('include', 'exclude', 'pending', name='sample_decision_enum'), nullable=False, default='pending'),
        sa.Column('tester_decision_notes', sa.Text(), nullable=True),
        sa.Column('tester_decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tester_decision_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        
        sa.Column('report_owner_decision', sa.Enum('include', 'exclude', 'pending', name='sample_decision_enum'), nullable=False, default='pending'),
        sa.Column('report_owner_decision_notes', sa.Text(), nullable=True),
        sa.Column('report_owner_decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('report_owner_decision_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        
        # Metadata
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('generation_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('validation_results', postgresql.JSONB(), nullable=True),
        
        # Carry-forward tracking
        sa.Column('carried_from_version_id', postgresql.UUID(), nullable=True),
        sa.Column('carried_from_sample_id', postgresql.UUID(), nullable=True),
        sa.Column('carry_forward_reason', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['version_id'], ['cycle_report_sample_selection_versions.version_id']),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id']),
        sa.ForeignKeyConstraint(['lob_id'], ['lobs.lob_id']),
        sa.ForeignKeyConstraint(['tester_decision_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['report_owner_decision_by_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['carried_from_version_id'], ['cycle_report_sample_selection_versions.version_id']),
        sa.ForeignKeyConstraint(['carried_from_sample_id'], ['cycle_report_sample_selection_samples.sample_id']),
    )
    
    # Create indexes
    op.create_index('idx_sample_selection_versions_phase', 'cycle_report_sample_selection_versions', ['phase_id'])
    op.create_index('idx_sample_selection_versions_status', 'cycle_report_sample_selection_versions', ['version_status'])
    op.create_index('idx_sample_selection_versions_workflow', 'cycle_report_sample_selection_versions', ['workflow_execution_id'])
    op.create_index('idx_sample_selection_versions_created_at', 'cycle_report_sample_selection_versions', ['created_at'])
    op.create_index('idx_sample_selection_versions_current', 'cycle_report_sample_selection_versions', ['phase_id', 'version_status'])
    
    op.create_index('idx_sample_selection_samples_version', 'cycle_report_sample_selection_samples', ['version_id'])
    op.create_index('idx_sample_selection_samples_phase', 'cycle_report_sample_selection_samples', ['phase_id'])
    op.create_index('idx_sample_selection_samples_lob', 'cycle_report_sample_selection_samples', ['lob_id'])
    op.create_index('idx_sample_selection_samples_category', 'cycle_report_sample_selection_samples', ['sample_category'])
    op.create_index('idx_sample_selection_samples_source', 'cycle_report_sample_selection_samples', ['sample_source'])
    op.create_index('idx_sample_selection_samples_tester_decision', 'cycle_report_sample_selection_samples', ['tester_decision'])
    op.create_index('idx_sample_selection_samples_owner_decision', 'cycle_report_sample_selection_samples', ['report_owner_decision'])
    op.create_index('idx_sample_selection_samples_identifier', 'cycle_report_sample_selection_samples', ['sample_identifier'])
    op.create_index('idx_sample_selection_samples_created_at', 'cycle_report_sample_selection_samples', ['created_at'])
    
    # Composite indexes for common queries
    op.create_index('idx_sample_selection_samples_version_category', 'cycle_report_sample_selection_samples', ['version_id', 'sample_category'])
    op.create_index('idx_sample_selection_samples_version_decisions', 'cycle_report_sample_selection_samples', ['version_id', 'tester_decision', 'report_owner_decision'])
    op.create_index('idx_sample_selection_samples_phase_lob', 'cycle_report_sample_selection_samples', ['phase_id', 'lob_id'])
    
    # Create trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_sample_selection_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_sample_selection_versions_updated_at
            BEFORE UPDATE ON cycle_report_sample_selection_versions
            FOR EACH ROW
            EXECUTE FUNCTION update_sample_selection_updated_at_column();
        
        CREATE TRIGGER update_sample_selection_samples_updated_at
            BEFORE UPDATE ON cycle_report_sample_selection_samples
            FOR EACH ROW
            EXECUTE FUNCTION update_sample_selection_updated_at_column();
    """)


def downgrade():
    """Drop the new sample selection version tables"""
    
    # Drop triggers
    op.execute("""
        DROP TRIGGER IF EXISTS update_sample_selection_versions_updated_at ON cycle_report_sample_selection_versions;
        DROP TRIGGER IF EXISTS update_sample_selection_samples_updated_at ON cycle_report_sample_selection_samples;
        DROP FUNCTION IF EXISTS update_sample_selection_updated_at_column();
    """)
    
    # Drop indexes
    op.drop_index('idx_sample_selection_samples_phase_lob', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_version_decisions', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_version_category', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_created_at', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_identifier', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_owner_decision', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_tester_decision', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_source', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_category', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_lob', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_phase', 'cycle_report_sample_selection_samples')
    op.drop_index('idx_sample_selection_samples_version', 'cycle_report_sample_selection_samples')
    
    op.drop_index('idx_sample_selection_versions_current', 'cycle_report_sample_selection_versions')
    op.drop_index('idx_sample_selection_versions_created_at', 'cycle_report_sample_selection_versions')
    op.drop_index('idx_sample_selection_versions_workflow', 'cycle_report_sample_selection_versions')
    op.drop_index('idx_sample_selection_versions_status', 'cycle_report_sample_selection_versions')
    op.drop_index('idx_sample_selection_versions_phase', 'cycle_report_sample_selection_versions')
    
    # Drop tables
    op.drop_table('cycle_report_sample_selection_samples')
    op.drop_table('cycle_report_sample_selection_versions')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS sample_decision_enum;")
    op.execute("DROP TYPE IF EXISTS sample_source_enum;")
    op.execute("DROP TYPE IF EXISTS sample_category_enum;")