"""Create version history table

Revision ID: create_version_history
Revises: create_phase_metrics
Create Date: 2024-12-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_version_history'
down_revision = 'create_phase_metrics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create version_history table
    op.create_table(
        'version_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Entity identification
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_name', sa.String(255), nullable=True),
        
        # Version information
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('change_type', sa.String(50), nullable=False),
        sa.Column('change_reason', sa.Text, nullable=True),
        
        # Change tracking
        sa.Column('changed_by', sa.String(255), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Change details
        sa.Column('change_details', postgresql.JSONB, nullable=True),
        
        # Context
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('phase_name', sa.String(50), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    
    # Create indexes
    op.create_index('idx_version_history_entity', 'version_history', ['entity_type', 'entity_id'])
    op.create_index('idx_version_history_cycle_report', 'version_history', ['cycle_id', 'report_id'])
    op.create_index('idx_version_history_changed_by', 'version_history', ['changed_by'])
    op.create_index('idx_version_history_changed_at', 'version_history', ['changed_at'])
    op.create_index('idx_version_history_change_type', 'version_history', ['change_type'])
    
    # Add versioning columns to existing tables that need versioning
    
    # Add to report_attributes table
    op.add_column('report_attributes', sa.Column('version_number', sa.Integer, nullable=False, server_default='1'))
    op.add_column('report_attributes', sa.Column('is_latest_version', sa.Boolean, nullable=False, server_default='true'))
    op.add_column('report_attributes', sa.Column('version_created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.add_column('report_attributes', sa.Column('version_created_by', sa.String(255), nullable=True))
    op.add_column('report_attributes', sa.Column('version_notes', sa.Text, nullable=True))
    op.add_column('report_attributes', sa.Column('change_reason', sa.String(500), nullable=True))
    op.add_column('report_attributes', sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('report_attributes', sa.Column('version_status', sa.String(50), nullable=False, server_default='approved'))
    op.add_column('report_attributes', sa.Column('approved_version_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('report_attributes', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('report_attributes', sa.Column('approved_by', sa.String(255), nullable=True))
    
    # Add to sample_sets table (already has some versioning)
    op.add_column('sample_sets', sa.Column('version_status', sa.String(50), nullable=False, server_default='draft'))
    op.add_column('sample_sets', sa.Column('approved_version_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('sample_sets', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('sample_sets', sa.Column('approved_by', sa.String(255), nullable=True))
    op.add_column('sample_sets', sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create indexes for versioning columns
    op.create_index('idx_report_attributes_version', 'report_attributes', ['version_number', 'is_latest_version'])
    op.create_index('idx_sample_sets_version', 'sample_sets', ['version_number', 'is_latest_version'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_sample_sets_version', 'sample_sets')
    op.drop_index('idx_report_attributes_version', 'report_attributes')
    
    # Remove versioning columns from existing tables
    versioning_columns = [
        'version_number', 'is_latest_version', 'version_created_at',
        'version_created_by', 'version_notes', 'change_reason',
        'parent_version_id', 'version_status', 'approved_version_id',
        'approved_at', 'approved_by'
    ]
    
    # Remove from report_attributes
    for col in versioning_columns:
        try:
            op.drop_column('report_attributes', col)
        except:
            pass  # Column might not exist
    
    # Remove from sample_sets (only the new ones)
    new_sample_set_columns = [
        'version_status', 'approved_version_id', 
        'approved_at', 'approved_by', 'parent_version_id'
    ]
    for col in new_sample_set_columns:
        try:
            op.drop_column('sample_sets', col)
        except:
            pass
    
    # Drop version history indexes
    op.drop_index('idx_version_history_change_type', 'version_history')
    op.drop_index('idx_version_history_changed_at', 'version_history')
    op.drop_index('idx_version_history_changed_by', 'version_history')
    op.drop_index('idx_version_history_cycle_report', 'version_history')
    op.drop_index('idx_version_history_entity', 'version_history')
    
    # Drop version history table
    op.drop_table('version_history')