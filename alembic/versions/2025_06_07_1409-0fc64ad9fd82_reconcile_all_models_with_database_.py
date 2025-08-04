"""Reconcile all models with database schema

Revision ID: 0fc64ad9fd82
Revises: d1f70826c2d2
Create Date: 2025-06-07 14:09:43.382218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0fc64ad9fd82'
down_revision: Union[str, None] = 'd1f70826c2d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns to reconcile models with database schema."""
    
    # Add missing columns to data_sources table
    op.add_column('data_sources', sa.Column('description', sa.Text(), nullable=True))
    
    # Add missing columns to report_attributes table (the main cause of errors)
    op.add_column('report_attributes', sa.Column('validation_rules', sa.Text(), nullable=True))
    op.add_column('report_attributes', sa.Column('typical_source_documents', sa.Text(), nullable=True))
    op.add_column('report_attributes', sa.Column('keywords_to_look_for', sa.Text(), nullable=True))
    op.add_column('report_attributes', sa.Column('testing_approach', sa.Text(), nullable=True))
    op.add_column('report_attributes', sa.Column('risk_score', sa.Float(), nullable=True, comment='LLM-provided risk score (0-10) based on regulatory importance'))
    op.add_column('report_attributes', sa.Column('llm_risk_rationale', sa.Text(), nullable=True, comment='LLM explanation for the assigned risk score'))
    op.add_column('report_attributes', sa.Column('is_primary_key', sa.Boolean(), nullable=False, server_default='false', comment='Whether this attribute is part of the primary key'))
    op.add_column('report_attributes', sa.Column('primary_key_order', sa.Integer(), nullable=True, comment='Order of this attribute in composite primary key (1-based)'))
    op.add_column('report_attributes', sa.Column('approval_status', sa.String(length=20), nullable=False, server_default='pending', comment='Approval status: pending, approved, rejected'))
    op.add_column('report_attributes', sa.Column('master_attribute_id', sa.Integer(), nullable=True))
    op.add_column('report_attributes', sa.Column('version_number', sa.Integer(), nullable=False, server_default='1', comment='Version number of this attribute'))
    op.add_column('report_attributes', sa.Column('is_latest_version', sa.Boolean(), nullable=False, server_default='true', comment='Whether this is the latest version'))
    op.add_column('report_attributes', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether this version is active'))
    op.add_column('report_attributes', sa.Column('version_notes', sa.Text(), nullable=True, comment='Notes about what changed in this version'))
    op.add_column('report_attributes', sa.Column('change_reason', sa.String(length=100), nullable=True, comment='Reason for creating new version'))
    op.add_column('report_attributes', sa.Column('replaced_attribute_id', sa.Integer(), nullable=True))
    op.add_column('report_attributes', sa.Column('version_created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')))
    op.add_column('report_attributes', sa.Column('version_created_by', sa.Integer(), nullable=False, server_default='1'))  # Default to first user
    op.add_column('report_attributes', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('report_attributes', sa.Column('approved_by', sa.Integer(), nullable=True))
    op.add_column('report_attributes', sa.Column('archived_at', sa.DateTime(), nullable=True))
    op.add_column('report_attributes', sa.Column('archived_by', sa.Integer(), nullable=True))
    
    # Add indexes and foreign keys
    op.create_index('ix_report_attributes_master_attribute_id', 'report_attributes', ['master_attribute_id'], unique=False)
    op.create_foreign_key('fk_report_attributes_master_attribute', 'report_attributes', 'report_attributes', ['master_attribute_id'], ['attribute_id'])
    op.create_foreign_key('fk_report_attributes_replaced_attribute', 'report_attributes', 'report_attributes', ['replaced_attribute_id'], ['attribute_id'])
    op.create_foreign_key('fk_report_attributes_approved_by', 'report_attributes', 'users', ['approved_by'], ['user_id'])
    op.create_foreign_key('fk_report_attributes_archived_by', 'report_attributes', 'users', ['archived_by'], ['user_id'])
    op.create_foreign_key('fk_report_attributes_version_created_by', 'report_attributes', 'users', ['version_created_by'], ['user_id'])
    
    # Add missing columns to testing_test_executions table
    op.add_column('testing_test_executions', sa.Column('data_source_id', sa.Integer(), nullable=True))
    op.add_column('testing_test_executions', sa.Column('sample_id', sa.Integer(), nullable=True))
    op.add_column('testing_test_executions', sa.Column('executed_by', sa.Integer(), nullable=True))
    
    # Add foreign keys for new columns
    op.create_foreign_key('fk_testing_test_executions_sample', 'testing_test_executions', 'samples', ['sample_id'], ['sample_id'])
    op.create_foreign_key('fk_testing_test_executions_data_source', 'testing_test_executions', 'data_sources', ['data_source_id'], ['data_source_id'])
    op.create_foreign_key('fk_testing_test_executions_executed_by', 'testing_test_executions', 'users', ['executed_by'], ['user_id'])


def downgrade() -> None:
    """Remove added columns."""
    
    # Drop foreign keys first
    op.drop_constraint('fk_testing_test_executions_executed_by', 'testing_test_executions', type_='foreignkey')
    op.drop_constraint('fk_testing_test_executions_data_source', 'testing_test_executions', type_='foreignkey')
    op.drop_constraint('fk_testing_test_executions_sample', 'testing_test_executions', type_='foreignkey')
    
    # Drop testing_test_executions columns
    op.drop_column('testing_test_executions', 'executed_by')
    op.drop_column('testing_test_executions', 'sample_id')
    op.drop_column('testing_test_executions', 'data_source_id')
    
    # Drop report_attributes foreign keys
    op.drop_constraint('fk_report_attributes_version_created_by', 'report_attributes', type_='foreignkey')
    op.drop_constraint('fk_report_attributes_archived_by', 'report_attributes', type_='foreignkey')
    op.drop_constraint('fk_report_attributes_approved_by', 'report_attributes', type_='foreignkey')
    op.drop_constraint('fk_report_attributes_replaced_attribute', 'report_attributes', type_='foreignkey')
    op.drop_constraint('fk_report_attributes_master_attribute', 'report_attributes', type_='foreignkey')
    op.drop_index('ix_report_attributes_master_attribute_id', table_name='report_attributes')
    
    # Drop report_attributes columns
    op.drop_column('report_attributes', 'archived_by')
    op.drop_column('report_attributes', 'archived_at')
    op.drop_column('report_attributes', 'approved_by')
    op.drop_column('report_attributes', 'approved_at')
    op.drop_column('report_attributes', 'version_created_by')
    op.drop_column('report_attributes', 'version_created_at')
    op.drop_column('report_attributes', 'replaced_attribute_id')
    op.drop_column('report_attributes', 'change_reason')
    op.drop_column('report_attributes', 'version_notes')
    op.drop_column('report_attributes', 'is_active')
    op.drop_column('report_attributes', 'is_latest_version')
    op.drop_column('report_attributes', 'version_number')
    op.drop_column('report_attributes', 'master_attribute_id')
    op.drop_column('report_attributes', 'approval_status')
    op.drop_column('report_attributes', 'primary_key_order')
    op.drop_column('report_attributes', 'is_primary_key')
    op.drop_column('report_attributes', 'llm_risk_rationale')
    op.drop_column('report_attributes', 'risk_score')
    op.drop_column('report_attributes', 'testing_approach')
    op.drop_column('report_attributes', 'keywords_to_look_for')
    op.drop_column('report_attributes', 'typical_source_documents')
    op.drop_column('report_attributes', 'validation_rules')
    
    # Drop data_sources column
    op.drop_column('data_sources', 'description')
