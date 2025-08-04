"""Add missing columns to test execution reviews table

Revision ID: add_test_execution_review_columns
Revises: make_lob_id_nullable_in_sample_selection
Create Date: 2025-08-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_test_execution_review_columns'
down_revision = 'make_lob_id_nullable_in_sample_selection'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to cycle_report_test_execution_reviews table
    # Check if columns exist first to avoid errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('cycle_report_test_execution_reviews')]
    
    # Add retest_reason if it doesn't exist
    if 'retest_reason' not in existing_columns:
        op.add_column('cycle_report_test_execution_reviews', 
                      sa.Column('retest_reason', sa.Text(), nullable=True))
    
    # Add escalation_reason if it doesn't exist
    if 'escalation_reason' not in existing_columns:
        op.add_column('cycle_report_test_execution_reviews', 
                      sa.Column('escalation_reason', sa.Text(), nullable=True))


def downgrade():
    # Remove the columns
    op.drop_column('cycle_report_test_execution_reviews', 'escalation_reason')
    op.drop_column('cycle_report_test_execution_reviews', 'retest_reason')