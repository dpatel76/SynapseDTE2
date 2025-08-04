"""Add workflow state column

Revision ID: d1f70826c2d2
Revises: 7c8e6011c207
Create Date: 2025-06-07 14:07:38.425043

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd1f70826c2d2'
down_revision: Union[str, None] = '7c8e6011c207'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add essential workflow tracking columns to workflow_phases table."""
    # Create the ENUM types first
    workflow_phase_state_enum = postgresql.ENUM(
        'Not Started', 'In Progress', 'Complete', 
        name='workflow_phase_state_enum'
    )
    workflow_phase_status_enum = postgresql.ENUM(
        'On Track', 'At Risk', 'Past Due', 
        name='workflow_phase_status_enum'
    )
    
    # Create the ENUMs if they don't exist
    workflow_phase_state_enum.create(op.get_bind(), checkfirst=True)
    workflow_phase_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Update workflow_phase_enum to use 'Sample Selection' instead of 'Sampling'
    op.execute("ALTER TYPE workflow_phase_enum RENAME VALUE 'Sampling' TO 'Sample Selection'")
    
    # Add the essential columns
    op.add_column('workflow_phases', sa.Column('state', workflow_phase_state_enum, nullable=False, server_default='Not Started'))
    op.add_column('workflow_phases', sa.Column('schedule_status', workflow_phase_status_enum, nullable=False, server_default='On Track'))
    
    # Add the other tracking columns that are referenced in the model
    op.add_column('workflow_phases', sa.Column('state_override', workflow_phase_state_enum, nullable=True))
    op.add_column('workflow_phases', sa.Column('status_override', workflow_phase_status_enum, nullable=True))
    op.add_column('workflow_phases', sa.Column('override_reason', sa.Text(), nullable=True))
    op.add_column('workflow_phases', sa.Column('override_by', sa.Integer(), nullable=True))
    op.add_column('workflow_phases', sa.Column('override_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('workflow_phases', sa.Column('started_by', sa.Integer(), nullable=True))
    op.add_column('workflow_phases', sa.Column('completed_by', sa.Integer(), nullable=True))
    op.add_column('workflow_phases', sa.Column('notes', sa.Text(), nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key('fk_workflow_phases_override_by', 'workflow_phases', 'users', ['override_by'], ['user_id'])
    op.create_foreign_key('fk_workflow_phases_started_by', 'workflow_phases', 'users', ['started_by'], ['user_id'])
    op.create_foreign_key('fk_workflow_phases_completed_by', 'workflow_phases', 'users', ['completed_by'], ['user_id'])


def downgrade() -> None:
    """Remove workflow tracking columns."""
    # Drop foreign keys first
    op.drop_constraint('fk_workflow_phases_completed_by', 'workflow_phases', type_='foreignkey')
    op.drop_constraint('fk_workflow_phases_started_by', 'workflow_phases', type_='foreignkey')
    op.drop_constraint('fk_workflow_phases_override_by', 'workflow_phases', type_='foreignkey')
    
    # Drop columns
    op.drop_column('workflow_phases', 'notes')
    op.drop_column('workflow_phases', 'completed_by')
    op.drop_column('workflow_phases', 'started_by')
    op.drop_column('workflow_phases', 'override_at')
    op.drop_column('workflow_phases', 'override_by')
    op.drop_column('workflow_phases', 'override_reason')
    op.drop_column('workflow_phases', 'status_override')
    op.drop_column('workflow_phases', 'state_override')
    op.drop_column('workflow_phases', 'schedule_status')
    op.drop_column('workflow_phases', 'state')
    
    # Drop ENUMs (only if not used elsewhere)
    postgresql.ENUM(name='workflow_phase_status_enum').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='workflow_phase_state_enum').drop(op.get_bind(), checkfirst=True)
