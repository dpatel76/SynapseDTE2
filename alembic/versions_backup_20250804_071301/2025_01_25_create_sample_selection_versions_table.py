"""create sample selection versions table

Revision ID: create_sample_selection_versions
Revises: 
Create Date: 2025-01-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_sample_selection_versions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sample_selection_version_status_enum AS ENUM (
                'draft', 'pending_approval', 'approved', 'rejected', 'superseded'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sample_category_enum AS ENUM (
                'clean', 'anomaly', 'boundary'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sample_decision_enum AS ENUM (
                'approved', 'rejected', 'pending'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sample_source_enum AS ENUM (
                'tester', 'llm', 'manual', 'carried_forward'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create the cycle_report_sample_selection_versions table
    op.create_table('cycle_report_sample_selection_versions',
        sa.Column('version_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('workflow_activity_id', sa.Integer(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', postgresql.ENUM('draft', 'pending_approval', 'approved', 'rejected', 'superseded', name='sample_selection_version_status_enum'), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('workflow_execution_id', sa.String(length=255), nullable=False),
        sa.Column('workflow_run_id', sa.String(length=255), nullable=False),
        sa.Column('activity_name', sa.String(length=100), nullable=False),
        sa.Column('selection_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('target_sample_size', sa.Integer(), nullable=False),
        sa.Column('actual_sample_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('intelligent_sampling_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('distribution_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_source_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('submission_notes', sa.Text(), nullable=True),
        sa.Column('submitted_by_id', sa.Integer(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['parent_version_id'], ['cycle_report_sample_selection_versions.version_id'], ),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['workflow_activity_id'], ['workflow_activities.activity_id'], ),
        sa.PrimaryKeyConstraint('version_id')
    )
    
    # Create indexes
    op.create_index('idx_sample_selection_versions_phase_id', 'cycle_report_sample_selection_versions', ['phase_id'], unique=False)
    op.create_index('idx_sample_selection_versions_phase_version', 'cycle_report_sample_selection_versions', ['phase_id', 'version_number'], unique=True)
    op.create_index('idx_sample_selection_versions_status', 'cycle_report_sample_selection_versions', ['version_status'], unique=False)
    op.create_index('idx_sample_selection_versions_workflow_execution', 'cycle_report_sample_selection_versions', ['workflow_execution_id'], unique=False)

    # Create the cycle_report_sample_selection_samples table
    op.create_table('cycle_report_sample_selection_samples',
        sa.Column('sample_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('workflow_activity_id', sa.Integer(), nullable=True),
        sa.Column('line_of_business', sa.String(length=100), nullable=False),
        sa.Column('primary_attribute_value', sa.String(length=255), nullable=False),
        sa.Column('sample_category', postgresql.ENUM('clean', 'anomaly', 'boundary', name='sample_category_enum'), nullable=False),
        sa.Column('sample_source', postgresql.ENUM('tester', 'llm', 'manual', 'carried_forward', name='sample_source_enum'), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('included_in_version', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('exclusion_reason', sa.Text(), nullable=True),
        sa.Column('data_row_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('attribute_values', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tester_decision', postgresql.ENUM('approved', 'rejected', 'pending', name='sample_decision_enum'), nullable=True),
        sa.Column('tester_decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tester_decision_by_id', sa.Integer(), nullable=True),
        sa.Column('tester_notes', sa.Text(), nullable=True),
        sa.Column('report_owner_decision', postgresql.ENUM('approved', 'rejected', 'pending', name='sample_decision_enum'), nullable=True),
        sa.Column('report_owner_decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('report_owner_decision_by_id', sa.Integer(), nullable=True),
        sa.Column('report_owner_notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['report_owner_decision_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['tester_decision_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['cycle_report_sample_selection_versions.version_id'], ),
        sa.ForeignKeyConstraint(['workflow_activity_id'], ['workflow_activities.activity_id'], ),
        sa.PrimaryKeyConstraint('sample_id')
    )
    
    # Create indexes for samples table
    op.create_index('idx_sample_selection_samples_version_id', 'cycle_report_sample_selection_samples', ['version_id'], unique=False)
    op.create_index('idx_sample_selection_samples_phase_id', 'cycle_report_sample_selection_samples', ['phase_id'], unique=False)
    op.create_index('idx_sample_selection_samples_lob', 'cycle_report_sample_selection_samples', ['line_of_business'], unique=False)
    op.create_index('idx_sample_selection_samples_primary_attr', 'cycle_report_sample_selection_samples', ['primary_attribute_value'], unique=False)
    op.create_index('idx_sample_selection_samples_category', 'cycle_report_sample_selection_samples', ['sample_category'], unique=False)

    # Create trigger to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_cycle_report_sample_selection_versions_updated_at 
        BEFORE UPDATE ON cycle_report_sample_selection_versions 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_cycle_report_sample_selection_samples_updated_at 
        BEFORE UPDATE ON cycle_report_sample_selection_samples 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_cycle_report_sample_selection_samples_updated_at ON cycle_report_sample_selection_samples")
    op.execute("DROP TRIGGER IF EXISTS update_cycle_report_sample_selection_versions_updated_at ON cycle_report_sample_selection_versions")
    
    # Drop tables
    op.drop_table('cycle_report_sample_selection_samples')
    op.drop_table('cycle_report_sample_selection_versions')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS sample_source_enum")
    op.execute("DROP TYPE IF EXISTS sample_decision_enum")
    op.execute("DROP TYPE IF EXISTS sample_category_enum")
    op.execute("DROP TYPE IF EXISTS sample_selection_version_status_enum")