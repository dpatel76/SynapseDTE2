"""Create data owner LOB assignment tables

Revision ID: 2025_07_18_data_owner_lob_tables
Revises: 
Create Date: 2025-07-18 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_07_18_data_owner_lob_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create the new data owner LOB assignment tables"""
    
    # Table 1: Data Owner LOB Assignment Version Management
    op.create_table(
        'cycle_report_data_owner_lob_attribute_versions',
        sa.Column('version_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        
        # Phase Integration
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('workflow_activity_id', sa.Integer, sa.ForeignKey('workflow_activities.activity_id'), nullable=True),
        
        # Version Management
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('version_status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cycle_report_data_owner_lob_attribute_versions.version_id'), nullable=True),
        
        # Temporal Workflow Context
        sa.Column('workflow_execution_id', sa.String(255), nullable=True),
        sa.Column('workflow_run_id', sa.String(255), nullable=True),
        
        # Assignment Summary
        sa.Column('total_lob_attributes', sa.Integer, nullable=False, server_default='0'),
        sa.Column('assigned_lob_attributes', sa.Integer, nullable=False, server_default='0'),
        sa.Column('unassigned_lob_attributes', sa.Integer, nullable=False, server_default='0'),
        
        # Data Executive Information
        sa.Column('data_executive_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('assignment_batch_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('assignment_notes', sa.Text, nullable=True),
        
        # Audit Fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('created_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        
        # Constraints
        sa.UniqueConstraint('phase_id', 'version_number', name='uq_data_owner_version_phase_number'),
        sa.CheckConstraint("version_status IN ('draft', 'active', 'superseded')", name='ck_data_owner_version_status')
    )
    
    # Table 2: Individual Data Owner LOB Attribute Assignments
    op.create_table(
        'cycle_report_data_owner_lob_attribute_assignments',
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        
        # Version Reference
        sa.Column('version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cycle_report_data_owner_lob_attribute_versions.version_id', ondelete='CASCADE'), nullable=False),
        
        # Core Business Keys
        sa.Column('phase_id', sa.Integer, sa.ForeignKey('workflow_phases.phase_id'), nullable=False),
        sa.Column('sample_id', sa.Integer, sa.ForeignKey('cycle_report_sample_selection_samples.sample_id'), nullable=False),
        sa.Column('attribute_id', sa.Integer, sa.ForeignKey('cycle_report_planning_attributes.attribute_id'), nullable=False),
        sa.Column('lob_id', sa.Integer, sa.ForeignKey('lobs.lob_id'), nullable=False),
        
        # Data Owner Assignment
        sa.Column('data_owner_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),  # Can be NULL if unassigned
        
        # Data Executive Assignment Information
        sa.Column('data_executive_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('assigned_by_data_executive_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('assignment_rationale', sa.Text, nullable=True),
        
        # Change Tracking
        sa.Column('previous_data_owner_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        
        # Status
        sa.Column('assignment_status', sa.String(50), nullable=False, server_default='assigned'),
        
        # Data Owner Response
        sa.Column('data_owner_acknowledged', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('data_owner_acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_owner_response_notes', sa.Text, nullable=True),
        
        # Audit Fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('created_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_by_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        
        # Constraints
        sa.UniqueConstraint('version_id', 'phase_id', 'sample_id', 'attribute_id', 'lob_id', 
                          name='uq_data_owner_assignment_version_phase_sample_attr_lob'),
        sa.CheckConstraint("assignment_status IN ('assigned', 'unassigned', 'changed', 'confirmed')", 
                          name='ck_data_owner_assignment_status')
    )
    
    # Indexes for Performance
    
    # Version table indexes
    op.create_index('idx_cycle_report_data_owner_lob_attribute_versions_phase', 
                    'cycle_report_data_owner_lob_attribute_versions', ['phase_id'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_versions_status', 
                    'cycle_report_data_owner_lob_attribute_versions', ['version_status'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_versions_data_executive', 
                    'cycle_report_data_owner_lob_attribute_versions', ['data_executive_id'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_versions_workflow_activity', 
                    'cycle_report_data_owner_lob_attribute_versions', ['workflow_activity_id'])
    
    # Assignment table indexes
    op.create_index('idx_cycle_report_data_owner_lob_attribute_assignments_version', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['version_id'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_assignments_phase', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['phase_id'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_assignments_sample', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['sample_id'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_assignments_attribute', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['attribute_id'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_assignments_lob', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['lob_id'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_assignments_data_owner', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['data_owner_id'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_assignments_data_executive', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['data_executive_id'])
    op.create_index('idx_cycle_report_data_owner_lob_attribute_assignments_status', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['assignment_status'])
    
    # Composite indexes for common queries
    op.create_index('idx_data_owner_assignments_lob_attribute', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['lob_id', 'attribute_id'])
    op.create_index('idx_data_owner_assignments_phase_lob', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['phase_id', 'lob_id'])
    op.create_index('idx_data_owner_assignments_data_owner_status', 
                    'cycle_report_data_owner_lob_attribute_assignments', ['data_owner_id', 'assignment_status'])


def downgrade():
    """Drop the data owner LOB assignment tables"""
    
    # Drop indexes first
    op.drop_index('idx_data_owner_assignments_data_owner_status')
    op.drop_index('idx_data_owner_assignments_phase_lob')
    op.drop_index('idx_data_owner_assignments_lob_attribute')
    
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_assignments_status')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_assignments_data_executive')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_assignments_data_owner')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_assignments_lob')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_assignments_attribute')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_assignments_sample')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_assignments_phase')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_assignments_version')
    
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_versions_workflow_activity')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_versions_data_executive')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_versions_status')
    op.drop_index('idx_cycle_report_data_owner_lob_attribute_versions_phase')
    
    # Drop tables
    op.drop_table('cycle_report_data_owner_lob_attribute_assignments')
    op.drop_table('cycle_report_data_owner_lob_attribute_versions')