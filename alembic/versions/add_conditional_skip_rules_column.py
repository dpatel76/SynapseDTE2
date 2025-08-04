"""Add conditional_skip_rules column to activity_definitions

Revision ID: add_conditional_skip_rules
Revises: 
Create Date: 2025-07-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_conditional_skip_rules'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add conditional_skip_rules column to activity_definitions table
    op.add_column('activity_definitions', 
        sa.Column('conditional_skip_rules', postgresql.JSON, nullable=True)
    )


def downgrade():
    # Remove conditional_skip_rules column
    op.drop_column('activity_definitions', 'conditional_skip_rules')