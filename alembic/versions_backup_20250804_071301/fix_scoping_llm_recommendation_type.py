"""Fix scoping LLM recommendation column type

Revision ID: fix_scoping_llm_recommendation_type
Revises: 
Create Date: 2025-07-22 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_scoping_llm_recommendation_type'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Change llm_recommendation from VARCHAR(50) to JSONB
    op.alter_column('cycle_report_scoping_attributes', 'llm_recommendation',
                    existing_type=sa.VARCHAR(length=50),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=True,
                    postgresql_using='llm_recommendation::jsonb')


def downgrade():
    # Change back to VARCHAR(50) - this will likely fail if data exists
    op.alter_column('cycle_report_scoping_attributes', 'llm_recommendation',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=sa.VARCHAR(length=50),
                    existing_nullable=True)