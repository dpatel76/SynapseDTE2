"""Create unified test report tables

Revision ID: 2025_07_18_create_unified_test_report_tables
Revises: 2025_07_18_cleanup_legacy_test_execution
Create Date: 2025-07-18 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '2025_07_18_create_unified_test_report_tables'
down_revision = '2025_07_18_cleanup_legacy_test_execution'
branch_labels = None
depends_on = None


def upgrade():
    # Create unified test report sections table
    op.create_table(
        'cycle_report_test_report_sections',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('cycle_id', sa.Integer, sa.ForeignKey('test_cycles.cycle_id'), nullable=False),
        sa.Column('report_id', sa.Integer, sa.ForeignKey('reports.id'), nullable=False),
        
        # Section identification
        sa.Column('section_name', sa.String(100), nullable=False),
        sa.Column('section_title', sa.String(255), nullable=False),
        sa.Column('section_order', sa.Integer, nullable=False),
        
        # Section content (unified storage)
        sa.Column('section_content', postgresql.JSONB, nullable=False),
        
        # Section metadata
        sa.Column('data_sources', postgresql.JSONB, nullable=True),
        sa.Column('last_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requires_refresh', sa.Boolean, default=False, nullable=False),
        
        # Section status
        sa.Column('status', sa.String(50), default='draft', nullable=False),
        
        # Approval workflow (built-in)
        sa.Column('tester_approved', sa.Boolean, default=False, nullable=False),
        sa.Column('tester_approved_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('tester_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tester_notes', sa.Text, nullable=True),
        
        sa.Column('report_owner_approved', sa.Boolean, default=False, nullable=False),
        sa.Column('report_owner_approved_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('report_owner_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('report_owner_notes', sa.Text, nullable=True),
        
        sa.Column('executive_approved', sa.Boolean, default=False, nullable=False),
        sa.Column('executive_approved_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('executive_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executive_notes', sa.Text, nullable=True),
        
        # Final output formats
        sa.Column('markdown_content', sa.Text, nullable=True),
        sa.Column('html_content', sa.Text, nullable=True),
        sa.Column('pdf_path', sa.String(500), nullable=True),
        
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        
        # Constraints
        sa.UniqueConstraint('phase_id', 'section_name', name='uq_test_report_section_phase'),
        sa.UniqueConstraint('cycle_id', 'report_id', 'section_name', name='uq_test_report_section_report'),
    )
    
    # Create report generation metadata table
    op.create_table(
        'cycle_report_test_report_generation',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('cycle_id', sa.Integer, sa.ForeignKey('test_cycles.cycle_id'), nullable=False),
        sa.Column('report_id', sa.Integer, sa.ForeignKey('reports.id'), nullable=False),
        
        # Generation metadata
        sa.Column('generation_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_duration_ms', sa.Integer, nullable=True),
        
        # Data collection summary
        sa.Column('phase_data_collected', postgresql.JSONB, nullable=True),
        
        # Generation status
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        
        # Output summary
        sa.Column('total_sections', sa.Integer, nullable=True),
        sa.Column('sections_completed', sa.Integer, nullable=True),
        sa.Column('output_formats_generated', postgresql.JSONB, nullable=True),
        
        # Phase completion tracking
        sa.Column('all_approvals_received', sa.Boolean, default=False, nullable=False),
        sa.Column('phase_completion_ready', sa.Boolean, default=False, nullable=False),
        
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('generated_by', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        
        # Constraints
        sa.UniqueConstraint('phase_id', name='uq_test_report_generation_phase'),
    )
    
    # Create indexes for performance
    op.create_index('idx_test_report_sections_phase', 'cycle_report_test_report_sections', ['phase_id'])
    op.create_index('idx_test_report_sections_cycle_report', 'cycle_report_test_report_sections', ['cycle_id', 'report_id'])
    op.create_index('idx_test_report_sections_status', 'cycle_report_test_report_sections', ['status'])
    op.create_index('idx_test_report_sections_approvals', 'cycle_report_test_report_sections', ['tester_approved', 'report_owner_approved', 'executive_approved'])
    
    op.create_index('idx_test_report_generation_phase', 'cycle_report_test_report_generation', ['phase_id'])
    op.create_index('idx_test_report_generation_cycle_report', 'cycle_report_test_report_generation', ['cycle_id', 'report_id'])
    op.create_index('idx_test_report_generation_status', 'cycle_report_test_report_generation', ['status'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_test_report_generation_status', table_name='cycle_report_test_report_generation')
    op.drop_index('idx_test_report_generation_cycle_report', table_name='cycle_report_test_report_generation')
    op.drop_index('idx_test_report_generation_phase', table_name='cycle_report_test_report_generation')
    
    op.drop_index('idx_test_report_sections_approvals', table_name='cycle_report_test_report_sections')
    op.drop_index('idx_test_report_sections_status', table_name='cycle_report_test_report_sections')
    op.drop_index('idx_test_report_sections_cycle_report', table_name='cycle_report_test_report_sections')
    op.drop_index('idx_test_report_sections_phase', table_name='cycle_report_test_report_sections')
    
    # Drop tables
    op.drop_table('cycle_report_test_report_generation')
    op.drop_table('cycle_report_test_report_sections')