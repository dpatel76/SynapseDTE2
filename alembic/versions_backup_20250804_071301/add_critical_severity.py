"""add critical severity value to enum

Revision ID: add_critical_severity
Revises: fix_scoping_llm_recommendation_type
Create Date: 2025-07-23 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_critical_severity'
down_revision = 'fix_scoping_llm_recommendation_type'
branch_labels = None
depends_on = None


def upgrade():
    # Add 'critical' to severity_enum
    op.execute("ALTER TYPE severity_enum ADD VALUE 'critical'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values
    # This would require recreating the enum type and all dependent columns
    pass