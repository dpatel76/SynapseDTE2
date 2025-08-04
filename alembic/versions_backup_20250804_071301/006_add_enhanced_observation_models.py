"""add enhanced observation models

Revision ID: 006_add_enhanced_observation
Revises: 005_add_data_owner_id
Create Date: 2025-06-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '006_add_enhanced_observation'
down_revision = '005_add_data_owner_id'
branch_labels = None
depends_on = None


def upgrade():
    # Create document_revisions table
    op.create_table('document_revisions',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('revision_id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('revision_reason', sa.Text(), nullable=False),
        sa.Column('requested_by', sa.Integer(), nullable=False),
        sa.Column('requested_at', sa.DateTime(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('upload_notes', sa.Text(), nullable=True),
        sa.Column('previous_document_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ),
        sa.ForeignKeyConstraint(['previous_document_id'], ['documents.document_id'], ),
        sa.ForeignKeyConstraint(['requested_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.test_case_id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('revision_id')
    )
    op.create_index(op.f('ix_document_revisions_revision_id'), 'document_revisions', ['revision_id'], unique=False)
    
    # Skip enum creation - use String columns instead due to conflicts
    
    # Create observation_groups table
    op.create_table('observation_groups',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('issue_type', sa.String(), nullable=False),
        sa.Column('first_detected_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=True),
        sa.Column('total_test_cases', sa.Integer(), nullable=True),
        sa.Column('total_samples', sa.Integer(), nullable=True),
        sa.Column('rating', sa.String(20), nullable=True),
        sa.Column('approval_status', sa.String(50), nullable=True),
        sa.Column('report_owner_approved', sa.Boolean(), nullable=True),
        sa.Column('report_owner_approved_by', sa.Integer(), nullable=True),
        sa.Column('report_owner_approved_at', sa.DateTime(), nullable=True),
        sa.Column('report_owner_comments', sa.Text(), nullable=True),
        sa.Column('data_executive_approved', sa.Boolean(), nullable=True),
        sa.Column('data_executive_approved_by', sa.Integer(), nullable=True),
        sa.Column('data_executive_approved_at', sa.DateTime(), nullable=True),
        sa.Column('data_executive_comments', sa.Text(), nullable=True),
        sa.Column('finalized', sa.Boolean(), nullable=True),
        sa.Column('finalized_by', sa.Integer(), nullable=True),
        sa.Column('finalized_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['attribute_id'], ['report_attributes.attribute_id'], ),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['data_executive_approved_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['finalized_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.ForeignKeyConstraint(['report_owner_approved_by'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('group_id'),
        sa.UniqueConstraint('cycle_id', 'report_id', 'attribute_id', 'issue_type', name='_observation_group_uc')
    )
    op.create_index(op.f('ix_observation_groups_group_id'), 'observation_groups', ['group_id'], unique=False)
    
    # Create observations table
    op.create_table('observations',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('test_execution_id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.String(36), nullable=False),
        sa.Column('sample_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_files', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['observation_groups.group_id'], ),
        sa.ForeignKeyConstraint(['sample_id'], ['sample_selections.sample_id'], ),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.test_case_id'], ),
        sa.ForeignKeyConstraint(['test_execution_id'], ['test_executions.execution_id'], ),
        sa.PrimaryKeyConstraint('observation_id')
    )
    op.create_index(op.f('ix_observations_observation_id'), 'observations', ['observation_id'], unique=False)
    
    # Create observation_clarifications table
    op.create_table('observation_clarifications',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('clarification_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('clarification_text', sa.Text(), nullable=False),
        sa.Column('supporting_documents', sa.JSON(), nullable=True),
        sa.Column('requested_by_role', sa.String(), nullable=False),
        sa.Column('requested_by_user_id', sa.Integer(), nullable=False),
        sa.Column('requested_at', sa.DateTime(), nullable=True),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('response_documents', sa.JSON(), nullable=True),
        sa.Column('responded_by', sa.Integer(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['observation_groups.group_id'], ),
        sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['responded_by'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('clarification_id')
    )
    op.create_index(op.f('ix_observation_clarifications_clarification_id'), 'observation_clarifications', ['clarification_id'], unique=False)
    
    # Create test_report_phases table
    op.create_table('test_report_phases',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('phase_id', sa.String(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('include_executive_summary', sa.Boolean(), nullable=True),
        sa.Column('include_phase_artifacts', sa.Boolean(), nullable=True),
        sa.Column('include_detailed_observations', sa.Boolean(), nullable=True),
        sa.Column('include_metrics_dashboard', sa.Boolean(), nullable=True),
        sa.Column('report_title', sa.String(), nullable=True),
        sa.Column('report_period', sa.String(), nullable=True),
        sa.Column('regulatory_references', sa.JSON(), nullable=True),
        sa.Column('final_report_document_id', sa.Integer(), nullable=True),
        sa.Column('report_generated_at', sa.DateTime(), nullable=True),
        sa.Column('report_approved_by', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['final_report_document_id'], ['documents.document_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.PrimaryKeyConstraint('phase_id')
    )
    
    # Create test_report_sections table
    op.create_table('test_report_sections',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('section_id', sa.Integer(), nullable=False),
        sa.Column('phase_id', sa.String(), nullable=False),
        sa.Column('section_name', sa.String(), nullable=False),
        sa.Column('section_order', sa.Integer(), nullable=False),
        sa.Column('section_type', sa.String(), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('content_data', sa.JSON(), nullable=True),
        sa.Column('artifacts', sa.JSON(), nullable=True),
        sa.Column('metrics_summary', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['phase_id'], ['test_report_phases.phase_id'], ),
        sa.PrimaryKeyConstraint('section_id')
    )
    op.create_index(op.f('ix_test_report_sections_section_id'), 'test_report_sections', ['section_id'], unique=False)
    
    # Add "Preparing Test Report" to workflow phases
    op.execute("""
        UPDATE workflow_phases 
        SET phase_dependencies = '{"Planning": [], "Scoping": ["Planning"], "Sample Selection": ["Scoping"], 
                                  "Data Provider ID": ["Sample Selection"], "Request Info": ["Data Provider ID"], 
                                  "Testing": ["Request Info"], "Observations": ["Testing"], 
                                  "Preparing Test Report": ["Observations"]}'
        WHERE phase_dependencies IS NOT NULL
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_test_report_sections_section_id'), table_name='test_report_sections')
    op.drop_table('test_report_sections')
    op.drop_table('test_report_phases')
    op.drop_index(op.f('ix_observation_clarifications_clarification_id'), table_name='observation_clarifications')
    op.drop_table('observation_clarifications')
    op.drop_index(op.f('ix_observations_observation_id'), table_name='observations')
    op.drop_table('observations')
    op.drop_index(op.f('ix_observation_groups_group_id'), table_name='observation_groups')
    op.drop_table('observation_groups')
    op.drop_index(op.f('ix_document_revisions_revision_id'), table_name='document_revisions')
    op.drop_table('document_revisions')