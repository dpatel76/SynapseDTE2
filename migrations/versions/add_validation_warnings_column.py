"""Add validation warnings column to RFI query validation table

Revision ID: add_validation_warnings
Revises: 
Create Date: 2025-01-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_validation_warnings'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add validation_warnings column if it doesn't exist
    op.add_column('cycle_report_rfi_query_validations', 
                  sa.Column('validation_warnings', postgresql.JSONB(), nullable=True))


def downgrade():
    # Remove validation_warnings column
    op.drop_column('cycle_report_rfi_query_validations', 'validation_warnings')