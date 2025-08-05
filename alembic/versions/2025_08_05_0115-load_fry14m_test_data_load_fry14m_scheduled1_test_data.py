"""load_fry14m_scheduled1_test_data

Revision ID: load_fry14m_test_data
Revises: create_fry14m_test_data
Create Date: 2025-08-05 01:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from datetime import datetime, date

# revision identifiers, used by Alembic.
revision = 'load_fry14m_test_data'
down_revision = 'create_fry14m_test_data'
branch_labels = None
depends_on = None


def upgrade():
    """
    Load sample test data for fry14m_scheduled1_data table.
    This creates a representative sample of credit card account data for testing purposes.
    """
    conn = op.get_bind()
    
    # Generate sample test data
    # We'll create 100 sample records with varied data to represent different scenarios
    sample_data = []
    
    # Base date for calculations
    base_date = date(2024, 1, 1)
    states = ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'MI', 'GA', 'NC']
    
    for i in range(1, 101):  # Create 100 test records
        # Generate varied but realistic test data
        customer_id = f"CUST{i:06d}"
        reference_number = f"REF{i:08d}"
        bank_id = f"BANK{(i % 5) + 1:03d}"
        period_id = "202401"
        corporate_id = f"CORP{(i % 10) + 1:04d}"
        state = states[i % len(states)]
        zip_code = f"{(i % 90000) + 10000}"
        
        # Financial data with some variation
        credit_limit = 5000 + (i * 100)
        balance = credit_limit * (0.1 + (i % 10) * 0.08)  # 10% to 90% utilization
        
        # Credit scores
        credit_score = 600 + (i % 200)
        
        # Dates
        origination_date = base_date.replace(year=2020 + (i % 4))
        
        # Insert data
        insert_query = text("""
            INSERT INTO fry14m_scheduled1_data (
                reference_number, customer_id, bank_id, period_id, corporate_id,
                state, zip_code, credit_card_type, product_type, lending_type,
                revolve_feature, network_id, secured_credit_type, loan_source_channel,
                cycle_ending_balance, promotional_balance_mix, cash_balance_mix,
                average_daily_balance, month_ending_balance, total_reward_cash,
                reward_type, account_cycle_date, account_origination_date,
                multiple_banking_relationships, multiple_credit_card_relationships,
                joint_account, authorized_users, flagged_as_securitized,
                borrower_income_at_origination, income_source_at_origination,
                origination_credit_bureau_score_primary, refreshed_credit_bureau_score,
                behavioral_score, original_credit_limit, current_credit_limit,
                current_cash_advance_limit, line_frozen_flag, line_increase_decrease_flag,
                minimum_payment_due, total_payment_due, actual_payment_amount,
                total_past_due, days_past_due, apr_at_cycle_end,
                month_end_account_status_active_closed, bankruptcy_flag,
                utilization_rate, account_age_months, available_credit,
                created_at, updated_at, created_by, updated_by
            ) VALUES (
                :reference_number, :customer_id, :bank_id, :period_id, :corporate_id,
                :state, :zip_code, :credit_card_type, :product_type, :lending_type,
                :revolve_feature, :network_id, :secured_credit_type, :loan_source_channel,
                :cycle_ending_balance, :promotional_balance_mix, :cash_balance_mix,
                :average_daily_balance, :month_ending_balance, :total_reward_cash,
                :reward_type, :account_cycle_date, :account_origination_date,
                :multiple_banking_relationships, :multiple_credit_card_relationships,
                :joint_account, :authorized_users, :flagged_as_securitized,
                :borrower_income_at_origination, :income_source_at_origination,
                :origination_credit_bureau_score_primary, :refreshed_credit_bureau_score,
                :behavioral_score, :original_credit_limit, :current_credit_limit,
                :current_cash_advance_limit, :line_frozen_flag, :line_increase_decrease_flag,
                :minimum_payment_due, :total_payment_due, :actual_payment_amount,
                :total_past_due, :days_past_due, :apr_at_cycle_end,
                :month_end_account_status_active_closed, :bankruptcy_flag,
                :utilization_rate, :account_age_months, :available_credit,
                NOW(), NOW(), 'system', 'system'
            )
        """)
        
        conn.execute(insert_query, {
            'reference_number': reference_number,
            'customer_id': customer_id,
            'bank_id': bank_id,
            'period_id': period_id,
            'corporate_id': corporate_id,
            'state': state,
            'zip_code': zip_code,
            'credit_card_type': (i % 4) + 1,  # 1-4
            'product_type': (i % 3) + 1,  # 1-3
            'lending_type': 1,  # Credit card
            'revolve_feature': 1,  # Revolving
            'network_id': (i % 4) + 1,  # 1-4 (Visa, MC, Amex, Discover)
            'secured_credit_type': 0 if i % 10 != 0 else 1,  # 10% secured
            'loan_source_channel': (i % 5) + 1,  # 1-5
            'cycle_ending_balance': round(balance, 2),
            'promotional_balance_mix': round(balance * 0.1, 2) if i % 5 == 0 else 0,
            'cash_balance_mix': round(balance * 0.05, 2) if i % 7 == 0 else 0,
            'average_daily_balance': round(balance * 0.9, 2),
            'month_ending_balance': round(balance, 2),
            'total_reward_cash': round(balance * 0.01, 2) if i % 3 == 0 else 0,
            'reward_type': 1 if i % 3 == 0 else 0,
            'account_cycle_date': base_date,
            'account_origination_date': origination_date,
            'multiple_banking_relationships': 1 if i % 3 == 0 else 0,
            'multiple_credit_card_relationships': 1 if i % 4 == 0 else 0,
            'joint_account': 1 if i % 20 == 0 else 0,
            'authorized_users': i % 3,  # 0-2 authorized users
            'flagged_as_securitized': 1 if i % 15 == 0 else 0,
            'borrower_income_at_origination': 40000 + (i * 500),
            'income_source_at_origination': (i % 4) + 1,
            'origination_credit_bureau_score_primary': credit_score,
            'refreshed_credit_bureau_score': credit_score + (i % 20) - 10,
            'behavioral_score': round(0.5 + (i % 50) * 0.01, 6),
            'original_credit_limit': credit_limit,
            'current_credit_limit': credit_limit,
            'current_cash_advance_limit': credit_limit * 0.5,
            'line_frozen_flag': 1 if i % 50 == 0 else 0,
            'line_increase_decrease_flag': 1 if (i % 30) == 0 else 0,
            'minimum_payment_due': round(balance * 0.02, 2) if balance > 0 else 0,
            'total_payment_due': round(balance, 2),
            'actual_payment_amount': round(balance * 0.02, 2) if balance > 0 else 0,
            'total_past_due': round(balance * 0.1, 2) if i % 20 == 0 else 0,
            'days_past_due': 30 if i % 20 == 0 else 0,
            'apr_at_cycle_end': 15.99 + (i % 10) * 0.5,
            'month_end_account_status_active_closed': 1,  # Active
            'bankruptcy_flag': 1 if i % 100 == 0 else 0,
            'utilization_rate': round((balance / credit_limit) * 100, 3),
            'account_age_months': (i % 60) + 12,
            'available_credit': credit_limit - balance
        })
    
    # Add a few edge case records for testing
    # 1. Closed account
    conn.execute(insert_query, {
        'reference_number': 'REF99999999',
        'customer_id': 'CUST999999',
        'bank_id': 'BANK001',
        'period_id': '202401',
        'corporate_id': 'CORP0001',
        'state': 'CA',
        'zip_code': '90210',
        'credit_card_type': 1,
        'product_type': 1,
        'lending_type': 1,
        'revolve_feature': 1,
        'network_id': 1,
        'secured_credit_type': 0,
        'loan_source_channel': 1,
        'cycle_ending_balance': 0,
        'promotional_balance_mix': 0,
        'cash_balance_mix': 0,
        'average_daily_balance': 0,
        'month_ending_balance': 0,
        'total_reward_cash': 0,
        'reward_type': 0,
        'account_cycle_date': base_date,
        'account_origination_date': date(2020, 1, 1),
        'multiple_banking_relationships': 0,
        'multiple_credit_card_relationships': 0,
        'joint_account': 0,
        'authorized_users': 0,
        'flagged_as_securitized': 0,
        'borrower_income_at_origination': 50000,
        'income_source_at_origination': 1,
        'origination_credit_bureau_score_primary': 700,
        'refreshed_credit_bureau_score': 700,
        'behavioral_score': 0.7,
        'original_credit_limit': 10000,
        'current_credit_limit': 0,  # Closed
        'current_cash_advance_limit': 0,
        'line_frozen_flag': 0,
        'line_increase_decrease_flag': 0,
        'minimum_payment_due': 0,
        'total_payment_due': 0,
        'actual_payment_amount': 0,
        'total_past_due': 0,
        'days_past_due': 0,
        'apr_at_cycle_end': 0,
        'month_end_account_status_active_closed': 0,  # Closed
        'bankruptcy_flag': 0,
        'utilization_rate': 0,
        'account_age_months': 48,
        'available_credit': 0
    })
    
    print(f"Loaded test data into fry14m_scheduled1_data table")


def downgrade():
    # Remove the test data
    conn = op.get_bind()
    conn.execute("TRUNCATE TABLE fry14m_scheduled1_data RESTART IDENTITY")