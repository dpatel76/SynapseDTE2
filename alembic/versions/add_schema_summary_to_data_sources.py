"""Add schema_summary to cycle_report_planning_data_sources

Revision ID: add_schema_summary
Revises: 
Create Date: 2025-07-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_schema_summary'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add schema_summary column to cycle_report_planning_data_sources table
    op.add_column('cycle_report_planning_data_sources', 
        sa.Column('schema_summary', sa.Text(), nullable=True)
    )
    
    # Add some example schema for existing data sources (optional)
    # You can customize this based on your actual data sources
    op.execute("""
        UPDATE cycle_report_planning_data_sources 
        SET schema_summary = 
        CASE 
            WHEN source_type = 'DATABASE' AND name LIKE '%Credit Card%' THEN 
                'Tables available:
                - credit_card_accounts: account_number, customer_id, credit_limit, balance, apr, open_date, status
                - credit_card_transactions: transaction_id, account_number, transaction_date, amount, merchant, category
                - credit_card_payments: payment_id, account_number, payment_date, payment_amount, payment_method
                - credit_card_customers: customer_id, first_name, last_name, ssn, fico_score, income, address'
            WHEN source_type = 'DATABASE' THEN 
                'Schema not loaded. Please update with actual table and column information.'
            WHEN source_type = 'FILE' THEN 
                'File columns not specified. Please update with column names from the file.'
            ELSE 
                'Schema information not available.'
        END
        WHERE schema_summary IS NULL
    """)


def downgrade():
    # Remove schema_summary column
    op.drop_column('cycle_report_planning_data_sources', 'schema_summary')