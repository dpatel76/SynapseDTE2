"""Add LLM payload columns to scoping attributes

Revision ID: add_llm_payload_columns
Revises: 
Create Date: 2025-01-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_llm_payload_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add llm_request_payload column
    op.add_column('cycle_report_scoping_attributes', 
        sa.Column('llm_request_payload', postgresql.JSONB(), nullable=True)
    )
    
    # Add llm_response_payload column
    op.add_column('cycle_report_scoping_attributes',
        sa.Column('llm_response_payload', postgresql.JSONB(), nullable=True)
    )


def downgrade():
    # Remove llm_response_payload column
    op.drop_column('cycle_report_scoping_attributes', 'llm_response_payload')
    
    # Remove llm_request_payload column
    op.drop_column('cycle_report_scoping_attributes', 'llm_request_payload')