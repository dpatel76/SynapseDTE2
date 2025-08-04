"""Database redesign migration - adds new tables alongside existing

Revision ID: 2025_07_11_redesign
Revises: 2025_06_07_1230_initial_schema
Create Date: 2025-07-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2025_07_11_redesign'
down_revision: Union[str, None] = '2025_06_07_1230_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new redesigned tables alongside existing ones"""
    
    # Create new enums if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE report_status_enum AS ENUM ('Active', 'Inactive', 'Under Review', 'Archived');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE cycle_status_enum AS ENUM ('Draft', 'Planning', 'In Progress', 'Review', 'Completed', 'Cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE security_classification_enum AS ENUM ('Public', 'Internal', 'Confidential', 'Restricted', 'HRCI');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE assignment_type_enum AS ENUM ('report_owner', 'tester', 'data_owner', 'reviewer', 'approver', 'observer', 'data_provider');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE assignment_status_enum AS ENUM ('pending', 'accepted', 'declined', 'completed', 'reassigned', 'expired');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create report_inventory table (new name for reports)
    op.create_table('report_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_number', sa.String(length=50), nullable=False),
        sa.Column('report_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('frequency', sa.String(length=50), nullable=True),
        sa.Column('business_unit', sa.String(length=100), nullable=True),
        sa.Column('regulatory_requirement', sa.Boolean(), server_default='false'),
        sa.Column('status', postgresql.ENUM('Active', 'Inactive', 'Under Review', 'Archived', name='report_status_enum', create_type=False), server_default='Active'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_number')
    )
    
    # Create new phase tables with cycle_report_* naming
    op.create_table('cycle_report_attributes_planning',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cycle_report_id', sa.Integer(), nullable=False),
        sa.Column('attribute_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data_type', postgresql.ENUM('Text', 'Number', 'Date', 'Boolean', 'Currency', 'Percentage', 'JSON', name='data_type_enum', create_type=False), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), server_default='false'),
        sa.Column('is_cde', sa.Boolean(), server_default='false'),
        sa.Column('has_issues', sa.Boolean(), server_default='false'),
        sa.Column('is_primary_key', sa.Boolean(), server_default='false'),
        sa.Column('information_security_classification', postgresql.ENUM('Public', 'Internal', 'Confidential', 'Restricted', 'HRCI', name='security_classification_enum', create_type=False), server_default='Internal'),
        sa.Column('data_source_id', sa.Integer(), nullable=True),
        sa.Column('source_table', sa.String(length=255), nullable=True),
        sa.Column('source_column', sa.String(length=255), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('status', postgresql.ENUM('Not Started', 'In Progress', 'Pending Approval', 'Approved', 'Rejected', 'Completed', name='phase_status_enum', create_type=False), server_default='Not Started'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cycle_report_id'], ['cycle_reports.id'], ),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cycle_report_id', 'attribute_name', 'version')
    )
    
    # Version history table
    op.create_table('cycle_report_attributes_planning_version_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('planning_attribute_id', sa.Integer(), nullable=False),
        sa.Column('cycle_report_id', sa.Integer(), nullable=False),
        sa.Column('attribute_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data_type', postgresql.ENUM('Text', 'Number', 'Date', 'Boolean', 'Currency', 'Percentage', 'JSON', name='data_type_enum', create_type=False), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), nullable=True),
        sa.Column('is_cde', sa.Boolean(), nullable=True),
        sa.Column('has_issues', sa.Boolean(), nullable=True),
        sa.Column('is_primary_key', sa.Boolean(), nullable=True),
        sa.Column('information_security_classification', postgresql.ENUM('Public', 'Internal', 'Confidential', 'Restricted', 'HRCI', name='security_classification_enum', create_type=False), nullable=True),
        sa.Column('data_source_id', sa.Integer(), nullable=True),
        sa.Column('source_table', sa.String(length=255), nullable=True),
        sa.Column('source_column', sa.String(length=255), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Universal assignments table
    op.create_table('universal_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('assignee_id', sa.Integer(), nullable=False),
        sa.Column('assignment_type', postgresql.ENUM('report_owner', 'tester', 'data_owner', 'reviewer', 'approver', 'observer', 'data_provider', name='assignment_type_enum', create_type=False), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=True),
        sa.Column('phase', sa.String(length=50), nullable=True),
        sa.Column('assignment_reason', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('priority', sa.String(length=20), server_default='normal'),
        sa.Column('status', postgresql.ENUM('pending', 'accepted', 'declined', 'completed', 'reassigned', 'expired', name='assignment_status_enum', create_type=False), server_default='pending'),
        sa.Column('accepted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entity_type', 'entity_id', 'assignee_id', 'assignment_type', 'status')
    )
    
    # Add indexes
    op.create_index('idx_report_inventory_number', 'report_inventory', ['report_number'])
    op.create_index('idx_planning_cycle_report', 'cycle_report_attributes_planning', ['cycle_report_id'])
    op.create_index('idx_planning_status', 'cycle_report_attributes_planning', ['status'])
    op.create_index('idx_universal_assignments_entity', 'universal_assignments', ['entity_type', 'entity_id'])
    op.create_index('idx_universal_assignments_assignee', 'universal_assignments', ['assignee_id'])
    op.create_index('idx_universal_assignments_status', 'universal_assignments', ['status'])


def downgrade() -> None:
    """Remove redesigned tables"""
    op.drop_index('idx_universal_assignments_status')
    op.drop_index('idx_universal_assignments_assignee')
    op.drop_index('idx_universal_assignments_entity')
    op.drop_index('idx_planning_status')
    op.drop_index('idx_planning_cycle_report')
    op.drop_index('idx_report_inventory_number')
    
    op.drop_table('universal_assignments')
    op.drop_table('cycle_report_attributes_planning_version_history')
    op.drop_table('cycle_report_attributes_planning')
    op.drop_table('report_inventory')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS assignment_status_enum')
    op.execute('DROP TYPE IF EXISTS assignment_type_enum')
    op.execute('DROP TYPE IF EXISTS security_classification_enum')
    op.execute('DROP TYPE IF EXISTS cycle_status_enum')
    op.execute('DROP TYPE IF EXISTS report_status_enum')