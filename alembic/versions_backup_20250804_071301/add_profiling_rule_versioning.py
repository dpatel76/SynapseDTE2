"""Add versioning and enhanced approval workflow to profiling rules

Revision ID: add_profiling_rule_versioning
Revises: create_phase_metrics_table
Create Date: 2024-06-22 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_profiling_rule_versioning'
down_revision = '010_add_data_profiling_tables'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add versioning columns to profiling_rules table
    op.add_column('profiling_rules', sa.Column('version_number', sa.Integer(), nullable=False, default=1))
    op.add_column('profiling_rules', sa.Column('is_current_version', sa.Boolean(), nullable=False, default=True))
    op.add_column('profiling_rules', sa.Column('business_key', sa.String(255), nullable=True))
    op.add_column('profiling_rules', sa.Column('version_created_at', sa.DateTime(), nullable=True))
    op.add_column('profiling_rules', sa.Column('version_created_by', sa.Integer(), nullable=True))
    op.add_column('profiling_rules', sa.Column('effective_from', sa.DateTime(), nullable=True))
    op.add_column('profiling_rules', sa.Column('effective_to', sa.DateTime(), nullable=True))
    
    # Add enhanced approval workflow columns
    op.add_column('profiling_rules', sa.Column('rejected_by', sa.Integer(), nullable=True))
    op.add_column('profiling_rules', sa.Column('rejected_at', sa.DateTime(), nullable=True))
    op.add_column('profiling_rules', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('profiling_rules', sa.Column('rejection_notes', sa.Text(), nullable=True))
    op.add_column('profiling_rules', sa.Column('revision_notes', sa.Text(), nullable=True))
    
    # Update the status enum to include new statuses
    op.execute("ALTER TYPE profilingrulestatus ADD VALUE 'draft'")
    op.execute("ALTER TYPE profilingrulestatus ADD VALUE 'under_review'")
    op.execute("ALTER TYPE profilingrulestatus ADD VALUE 'needs_revision'")
    op.execute("ALTER TYPE profilingrulestatus ADD VALUE 'resubmitted'")
    
    # Add foreign key constraints for new user references
    op.create_foreign_key(
        'fk_profiling_rules_rejected_by',
        'profiling_rules', 'users',
        ['rejected_by'], ['user_id']
    )
    op.create_foreign_key(
        'fk_profiling_rules_version_created_by',
        'profiling_rules', 'users',
        ['version_created_by'], ['user_id']
    )
    
    # Create indexes for versioning queries
    op.create_index('ix_profiling_rules_business_key', 'profiling_rules', ['business_key'])
    op.create_index('ix_profiling_rules_current_version', 'profiling_rules', ['is_current_version'])
    op.create_index('ix_profiling_rules_version_number', 'profiling_rules', ['version_number'])
    
    # Update existing records to have proper versioning data
    op.execute("""
        UPDATE cycle_report_data_profiling_rules 
        SET 
            business_key = CONCAT('rule_', rule_id),
            version_created_at = created_at,
            version_created_by = created_by,
            effective_from = created_at
        WHERE business_key IS NULL
    """)
    
    # Make business_key non-nullable after populating
    op.alter_column('profiling_rules', 'business_key', nullable=False)

def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_profiling_rules_business_key', 'profiling_rules')
    op.drop_index('ix_profiling_rules_current_version', 'profiling_rules')
    op.drop_index('ix_profiling_rules_version_number', 'profiling_rules')
    
    # Remove foreign key constraints
    op.drop_constraint('fk_profiling_rules_rejected_by', 'profiling_rules', type_='foreignkey')
    op.drop_constraint('fk_profiling_rules_version_created_by', 'profiling_rules', type_='foreignkey')
    
    # Remove versioning columns
    op.drop_column('profiling_rules', 'version_number')
    op.drop_column('profiling_rules', 'is_current_version')
    op.drop_column('profiling_rules', 'business_key')
    op.drop_column('profiling_rules', 'version_created_at')
    op.drop_column('profiling_rules', 'version_created_by')
    op.drop_column('profiling_rules', 'effective_from')
    op.drop_column('profiling_rules', 'effective_to')
    
    # Remove enhanced approval workflow columns
    op.drop_column('profiling_rules', 'rejected_by')
    op.drop_column('profiling_rules', 'rejected_at')
    op.drop_column('profiling_rules', 'rejection_reason')
    op.drop_column('profiling_rules', 'rejection_notes')
    op.drop_column('profiling_rules', 'revision_notes')
    
    # Note: Cannot easily remove enum values in PostgreSQL, they would remain