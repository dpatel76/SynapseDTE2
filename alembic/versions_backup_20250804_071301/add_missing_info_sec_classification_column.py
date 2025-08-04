"""Add missing information_security_classification column

Revision ID: add_info_sec_class_001
Revises: 
Create Date: 2025-01-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_info_sec_class_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add information_security_classification column to cycle_report_planning_pde_mappings if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'cycle_report_planning_pde_mappings' 
                AND column_name = 'information_security_classification'
            ) THEN
                ALTER TABLE cycle_report_planning_pde_mappings 
                ADD COLUMN information_security_classification VARCHAR(50);
            END IF;
        END $$;
    """)


def downgrade():
    # Remove the column if it exists
    op.execute("""
        ALTER TABLE cycle_report_planning_pde_mappings 
        DROP COLUMN IF EXISTS information_security_classification;
    """)