"""add test report tables

Revision ID: 007_add_test_report_tables
Revises: 006_add_enhanced_observation
Create Date: 2025-06-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '007_add_test_report_tables'
down_revision = '006_add_enhanced_observation'
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_test_report_sections_section_id'), table_name='test_report_sections')
    op.drop_table('test_report_sections')
    op.drop_table('test_report_phases')