"""reorganize scoping attributes - remove duplicates and add missing fields

Revision ID: fix_scoping_attrs_001
Revises: fix_planning_attrs_001
Create Date: 2025-08-07 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_scoping_attrs_001'
down_revision = 'fix_planning_attrs_001'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns exist before trying to add them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('cycle_report_scoping_attributes')]
    
    # Add fields from planning that belong in scoping
    if 'validation_rules' not in existing_columns:
        op.add_column('cycle_report_scoping_attributes',
                      sa.Column('validation_rules', sa.Text(), nullable=True))
    
    if 'testing_approach' not in existing_columns:
        op.add_column('cycle_report_scoping_attributes',
                      sa.Column('testing_approach', sa.Text(), nullable=True))
    
    # Note: expected_source_documents and search_keywords already exist
    # They map to typical_source_documents and keywords_to_look_for from planning
    
    # Remove duplicate fields that should only exist in planning
    if 'is_cde' in existing_columns:
        op.drop_column('cycle_report_scoping_attributes', 'is_cde')
    
    if 'has_historical_issues' in existing_columns:
        op.drop_column('cycle_report_scoping_attributes', 'has_historical_issues')
    
    if 'is_primary_key' in existing_columns:
        op.drop_column('cycle_report_scoping_attributes', 'is_primary_key')
    
    # Populate llm_request_payload for existing records with NULL values
    op.execute("""
        UPDATE cycle_report_scoping_attributes
        SET llm_request_payload = '{"model": "claude-3-5-sonnet", "temperature": 0.3, "max_tokens": 2000}'::jsonb
        WHERE llm_request_payload IS NULL OR llm_request_payload::text = 'null'
    """)


def downgrade():
    # Re-add removed columns
    op.add_column('cycle_report_scoping_attributes',
                  sa.Column('is_primary_key', sa.BOOLEAN(), autoincrement=False, nullable=False, server_default='false'))
    op.add_column('cycle_report_scoping_attributes',
                  sa.Column('has_historical_issues', sa.BOOLEAN(), autoincrement=False, nullable=False, server_default='false'))
    op.add_column('cycle_report_scoping_attributes',
                  sa.Column('is_cde', sa.BOOLEAN(), autoincrement=False, nullable=False, server_default='false'))
    
    # Remove added columns
    op.drop_column('cycle_report_scoping_attributes', 'testing_approach')
    op.drop_column('cycle_report_scoping_attributes', 'validation_rules')