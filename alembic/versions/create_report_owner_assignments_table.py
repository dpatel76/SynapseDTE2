"""Create report owner assignments tables

Revision ID: create_report_owner_assignments
Revises: create_phase_metrics_table
Create Date: 2024-01-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_report_owner_assignments'
down_revision = '011_add_individual_sample_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUMs first
    assignment_status_enum = postgresql.ENUM(
        'Assigned', 'In Progress', 'Completed', 'Overdue', 'Cancelled',
        name='assignment_status_enum'
    )
    assignment_status_enum.create(op.get_bind())
    
    assignment_priority_enum = postgresql.ENUM(
        'Low', 'Medium', 'High', 'Critical',
        name='assignment_priority_enum'
    )
    assignment_priority_enum.create(op.get_bind())
    
    assignment_type_enum = postgresql.ENUM(
        'Data Upload Request', 'File Review', 'Documentation Review',
        'Approval Required', 'Information Request', 'Phase Review',
        name='assignment_type_enum'
    )
    assignment_type_enum.create(op.get_bind())
    
    # Create report_owner_assignments table
    op.create_table(
        'report_owner_assignments',
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(length=50), nullable=False),
        sa.Column('assignment_type', assignment_type_enum, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', assignment_status_enum, nullable=False, server_default='Assigned'),
        sa.Column('priority', assignment_priority_enum, nullable=False, server_default='Medium'),
        sa.Column('completed_by', sa.Integer(), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('completion_attachments', sa.Text(), nullable=True),
        sa.Column('escalated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalation_reason', sa.Text(), nullable=True),
        sa.Column('assignment_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['completed_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
        sa.PrimaryKeyConstraint('assignment_id')
    )
    
    # Create indexes for report_owner_assignments
    op.create_index('idx_ro_assignments_assigned_to', 'report_owner_assignments', ['assigned_to'])
    op.create_index('idx_ro_assignments_cycle_report', 'report_owner_assignments', ['cycle_id', 'report_id'])
    op.create_index('idx_ro_assignments_status', 'report_owner_assignments', ['status'])
    op.create_index('idx_ro_assignments_phase', 'report_owner_assignments', ['phase_name'])
    op.create_index('idx_ro_assignments_due_date', 'report_owner_assignments', ['due_date'])
    op.create_index('idx_ro_assignments_created_at', 'report_owner_assignments', ['created_at'])
    op.create_index('assignment_id', 'report_owner_assignments', ['assignment_id'])
    
    # Create report_owner_assignment_history table
    op.create_table(
        'report_owner_assignment_history',
        sa.Column('history_id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('field_changed', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['report_owner_assignments.assignment_id'], ),
        sa.ForeignKeyConstraint(['changed_by'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('history_id')
    )
    
    # Create indexes for report_owner_assignment_history
    op.create_index('idx_ro_assignment_history_assignment', 'report_owner_assignment_history', ['assignment_id'])
    op.create_index('idx_ro_assignment_history_changed_at', 'report_owner_assignment_history', ['changed_at'])
    op.create_index('history_id', 'report_owner_assignment_history', ['history_id'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_ro_assignment_history_changed_at', table_name='report_owner_assignment_history')
    op.drop_index('idx_ro_assignment_history_assignment', table_name='report_owner_assignment_history')
    op.drop_index('history_id', table_name='report_owner_assignment_history')
    
    op.drop_index('idx_ro_assignments_created_at', table_name='report_owner_assignments')
    op.drop_index('idx_ro_assignments_due_date', table_name='report_owner_assignments')
    op.drop_index('idx_ro_assignments_phase', table_name='report_owner_assignments')
    op.drop_index('idx_ro_assignments_status', table_name='report_owner_assignments')
    op.drop_index('idx_ro_assignments_cycle_report', table_name='report_owner_assignments')
    op.drop_index('idx_ro_assignments_assigned_to', table_name='report_owner_assignments')
    op.drop_index('assignment_id', table_name='report_owner_assignments')
    
    # Drop tables
    op.drop_table('report_owner_assignment_history')
    op.drop_table('report_owner_assignments')
    
    # Drop ENUMs
    assignment_type_enum = postgresql.ENUM(name='assignment_type_enum')
    assignment_type_enum.drop(op.get_bind())
    
    assignment_priority_enum = postgresql.ENUM(name='assignment_priority_enum')
    assignment_priority_enum.drop(op.get_bind())
    
    assignment_status_enum = postgresql.ENUM(name='assignment_status_enum')
    assignment_status_enum.drop(op.get_bind())