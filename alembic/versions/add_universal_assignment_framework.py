"""Add universal assignment framework

Revision ID: add_universal_assignment_framework
Revises: create_version_history_table
Create Date: 2025-01-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_universal_assignment_framework'
down_revision = 'create_version_history'
branch_labels = None
depends_on = None


def upgrade():
    # Create universal assignment type enum
    assignment_type_enum = postgresql.ENUM(
        'Data Upload Request',
        'File Review', 
        'File Approval',
        'Document Review',
        'Data Validation',
        'Scoping Approval',
        'Sample Selection Approval', 
        'Rule Approval',
        'Observation Approval',
        'Report Approval',
        'Version Approval',
        'Phase Review',
        'Phase Approval',
        'Phase Completion',
        'Workflow Progression',
        'LOB Assignment',
        'Test Execution Review',
        'Quality Review',
        'Compliance Review',
        'Risk Assessment',
        'Information Request',
        'Clarification Required',
        'Additional Data Required',
        'Role Assignment',
        'Permission Grant',
        'System Configuration',
        name='universal_assignment_type_enum'
    )
    assignment_type_enum.create(op.get_bind())

    # Create universal assignment status enum
    assignment_status_enum = postgresql.ENUM(
        'Assigned',
        'Acknowledged',
        'In Progress',
        'Completed',
        'Approved',
        'Rejected',
        'Cancelled',
        'Overdue',
        'Escalated',
        'On Hold',
        'Delegated',
        name='universal_assignment_status_enum'
    )
    assignment_status_enum.create(op.get_bind())

    # Create assignment priority enum
    assignment_priority_enum = postgresql.ENUM(
        'Low',
        'Medium', 
        'High',
        'Critical',
        'Urgent',
        name='universal_assignment_priority_enum'
    )
    assignment_priority_enum.create(op.get_bind())

    # Create context type enum
    context_type_enum = postgresql.ENUM(
        'Test Cycle',
        'Report',
        'Phase',
        'Attribute',
        'Sample',
        'Rule',
        'Observation',
        'File',
        'System',
        'User',
        name='universal_context_type_enum'
    )
    context_type_enum.create(op.get_bind())

    # Create universal_assignments table
    op.create_table('universal_assignments',
        sa.Column('assignment_id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('assignment_type', assignment_type_enum, nullable=False),
        
        # Role Information
        sa.Column('from_role', sa.String(50), nullable=False),
        sa.Column('to_role', sa.String(50), nullable=False),
        sa.Column('from_user_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('to_user_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        
        # Assignment Details
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('task_instructions', sa.Text, nullable=True),
        
        # Context Information
        sa.Column('context_type', context_type_enum, nullable=False),
        sa.Column('context_data', postgresql.JSONB, nullable=True),
        
        # Status & Priority
        sa.Column('status', assignment_status_enum, default='Assigned', nullable=False),
        sa.Column('priority', assignment_priority_enum, default='Medium', nullable=False),
        
        # Timing
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Completion Information
        sa.Column('completed_by_user_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('completion_notes', sa.Text, nullable=True),
        sa.Column('completion_data', postgresql.JSONB, nullable=True),
        sa.Column('completion_attachments', postgresql.JSONB, nullable=True),
        
        # Approval Workflow
        sa.Column('requires_approval', sa.Boolean, default=False, nullable=False),
        sa.Column('approval_role', sa.String(50), nullable=True),
        sa.Column('approved_by_user_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_notes', sa.Text, nullable=True),
        
        # Escalation & Delegation
        sa.Column('escalated', sa.Boolean, default=False, nullable=False),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated_to_user_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('escalation_reason', sa.Text, nullable=True),
        
        sa.Column('delegated_to_user_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('delegated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delegation_reason', sa.Text, nullable=True),
        
        # System Fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        
        # Metadata
        sa.Column('assignment_metadata', postgresql.JSONB, nullable=True),
        sa.Column('workflow_step', sa.String(100), nullable=True),
        sa.Column('parent_assignment_id', sa.String(36), sa.ForeignKey('universal_assignments.assignment_id'), nullable=True),
    )

    # Create indexes
    op.create_index('ix_universal_assignments_assignment_id', 'universal_assignments', ['assignment_id'])
    op.create_index('ix_universal_assignments_assignment_type', 'universal_assignments', ['assignment_type'])
    op.create_index('ix_universal_assignments_from_role', 'universal_assignments', ['from_role'])
    op.create_index('ix_universal_assignments_to_role', 'universal_assignments', ['to_role'])
    op.create_index('ix_universal_assignments_context_type', 'universal_assignments', ['context_type'])
    op.create_index('ix_universal_assignments_status', 'universal_assignments', ['status'])
    op.create_index('ix_universal_assignments_due_date', 'universal_assignments', ['due_date'])

    # Create universal_assignment_history table
    op.create_table('universal_assignment_history',
        sa.Column('history_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('assignment_id', sa.String(36), sa.ForeignKey('universal_assignments.assignment_id'), nullable=False),
        sa.Column('changed_by_user_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        
        # Change Details
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('field_changed', sa.String(100), nullable=True),
        sa.Column('old_value', sa.Text, nullable=True),
        sa.Column('new_value', sa.Text, nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('change_metadata', postgresql.JSONB, nullable=True),
    )

    op.create_index('ix_universal_assignment_history_history_id', 'universal_assignment_history', ['history_id'])

    # Create assignment_templates table
    op.create_table('assignment_templates',
        sa.Column('template_id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('template_name', sa.String(255), nullable=False),
        sa.Column('assignment_type', assignment_type_enum, nullable=False),
        sa.Column('from_role', sa.String(50), nullable=False),
        sa.Column('to_role', sa.String(50), nullable=False),
        
        # Template Content
        sa.Column('title_template', sa.String(255), nullable=False),
        sa.Column('description_template', sa.Text, nullable=True),
        sa.Column('task_instructions_template', sa.Text, nullable=True),
        
        # Default Settings
        sa.Column('default_priority', assignment_priority_enum, default='Medium', nullable=False),
        sa.Column('default_due_days', sa.Integer, nullable=True),
        sa.Column('requires_approval', sa.Boolean, default=False, nullable=False),
        sa.Column('approval_role', sa.String(50), nullable=True),
        
        # Template Metadata
        sa.Column('context_type', context_type_enum, nullable=False),
        sa.Column('workflow_step', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
    )

    op.create_index('ix_assignment_templates_template_id', 'assignment_templates', ['template_id'])


def downgrade():
    # Drop tables
    op.drop_table('assignment_templates')
    op.drop_table('universal_assignment_history')
    op.drop_table('universal_assignments')
    
    # Drop enums
    op.execute('DROP TYPE universal_context_type_enum')
    op.execute('DROP TYPE universal_assignment_priority_enum')
    op.execute('DROP TYPE universal_assignment_status_enum')
    op.execute('DROP TYPE universal_assignment_type_enum')