"""reorganize planning attributes - add audit fields and remove scoping fields

Revision ID: fix_planning_attrs_001
Revises: 969b1d7f6b77
Create Date: 2025-08-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_planning_attrs_001'
down_revision = '969b1d7f6b77'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns exist before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('cycle_report_planning_attributes')]
    
    # Add audit and version tracking columns if they don't exist
    if 'version' not in existing_columns:
        op.add_column('cycle_report_planning_attributes', 
                      sa.Column('version', sa.Integer(), nullable=True, server_default='1'))
    if 'created_by' not in existing_columns:
        op.add_column('cycle_report_planning_attributes',
                      sa.Column('created_by', sa.Integer(), nullable=True))
    if 'updated_by' not in existing_columns:
        op.add_column('cycle_report_planning_attributes',
                      sa.Column('updated_by', sa.Integer(), nullable=True))
    
    # Add foreign key constraints for audit columns
    op.create_foreign_key('fk_planning_attrs_created_by', 
                          'cycle_report_planning_attributes', 
                          'users', 
                          ['created_by'], 
                          ['user_id'])
    op.create_foreign_key('fk_planning_attrs_updated_by', 
                          'cycle_report_planning_attributes', 
                          'users', 
                          ['updated_by'], 
                          ['user_id'])
    
    # First, migrate data from columns we're about to drop to scoping attributes
    # This will be done in a separate data migration to preserve data
    
    # Drop columns that belong in scoping (only if they exist)
    if 'llm_rationale' in existing_columns:
        op.drop_column('cycle_report_planning_attributes', 'llm_rationale')
    if 'validation_rules' in existing_columns:
        op.drop_column('cycle_report_planning_attributes', 'validation_rules')
    if 'testing_approach' in existing_columns:
        op.drop_column('cycle_report_planning_attributes', 'testing_approach')
    if 'risk_score' in existing_columns:
        op.drop_column('cycle_report_planning_attributes', 'risk_score')
    if 'typical_source_documents' in existing_columns:
        op.drop_column('cycle_report_planning_attributes', 'typical_source_documents')
    if 'keywords_to_look_for' in existing_columns:
        op.drop_column('cycle_report_planning_attributes', 'keywords_to_look_for')


def downgrade():
    # Re-add dropped columns
    op.add_column('cycle_report_planning_attributes',
                  sa.Column('keywords_to_look_for', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('cycle_report_planning_attributes',
                  sa.Column('typical_source_documents', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('cycle_report_planning_attributes',
                  sa.Column('risk_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('cycle_report_planning_attributes',
                  sa.Column('testing_approach', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('cycle_report_planning_attributes',
                  sa.Column('validation_rules', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('cycle_report_planning_attributes',
                  sa.Column('llm_rationale', sa.TEXT(), autoincrement=False, nullable=True))
    
    # Drop foreign key constraints
    op.drop_constraint('fk_planning_attrs_updated_by', 'cycle_report_planning_attributes', type_='foreignkey')
    op.drop_constraint('fk_planning_attrs_created_by', 'cycle_report_planning_attributes', type_='foreignkey')
    
    # Drop audit columns
    op.drop_column('cycle_report_planning_attributes', 'updated_by')
    op.drop_column('cycle_report_planning_attributes', 'created_by')
    op.drop_column('cycle_report_planning_attributes', 'version')