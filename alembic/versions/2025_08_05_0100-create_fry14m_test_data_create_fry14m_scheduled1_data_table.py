"""create_fry14m_scheduled1_data_table

Revision ID: create_fry14m_test_data
Revises: fix_workflow_activities_001
Create Date: 2025-08-05 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'create_fry14m_test_data'
down_revision = 'fix_workflow_activities_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create the fry14m_scheduled1_data table
    op.create_table('fry14m_scheduled1_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reference_number', sa.String(length=50), nullable=True),
        sa.Column('customer_id', sa.String(length=50), nullable=True),
        sa.Column('bank_id', sa.String(length=20), nullable=True),
        sa.Column('period_id', sa.String(length=20), nullable=True),
        sa.Column('corporate_id', sa.String(length=50), nullable=True),
        sa.Column('state', sa.String(length=2), nullable=True),
        sa.Column('zip_code', sa.String(length=20), nullable=True),
        sa.Column('credit_card_type', sa.Integer(), nullable=True),
        sa.Column('product_type', sa.Integer(), nullable=True),
        sa.Column('lending_type', sa.Integer(), nullable=True),
        sa.Column('revolve_feature', sa.Integer(), nullable=True),
        sa.Column('network_id', sa.Integer(), nullable=True),
        sa.Column('secured_credit_type', sa.Integer(), nullable=True),
        sa.Column('loan_source_channel', sa.Integer(), nullable=True),
        sa.Column('purchased_credit_deteriorated_status', sa.Integer(), nullable=True),
        sa.Column('cycle_ending_balance', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('promotional_balance_mix', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('cash_balance_mix', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('penalty_balance_mix', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('other_balance_mix', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('average_daily_balance', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('month_ending_balance', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('total_reward_cash', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('reward_type', sa.Integer(), nullable=True),
        sa.Column('account_cycle_date', sa.Date(), nullable=True),
        sa.Column('account_origination_date', sa.Date(), nullable=True),
        sa.Column('acquisition_date', sa.Date(), nullable=True),
        sa.Column('credit_bureau_score_refresh_date', sa.Date(), nullable=True),
        sa.Column('next_payment_due_date', sa.Date(), nullable=True),
        sa.Column('collection_re_age_date', sa.Date(), nullable=True),
        sa.Column('customer_service_re_age_date', sa.Date(), nullable=True),
        sa.Column('date_co_borrower_added', sa.Date(), nullable=True),
        sa.Column('multiple_banking_relationships', sa.Integer(), nullable=True),
        sa.Column('multiple_credit_card_relationships', sa.Integer(), nullable=True),
        sa.Column('joint_account', sa.Integer(), nullable=True),
        sa.Column('authorized_users', sa.Integer(), nullable=True),
        sa.Column('flagged_as_securitized', sa.Integer(), nullable=True),
        sa.Column('borrower_income_at_origination', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('income_source_at_origination', sa.Integer(), nullable=True),
        sa.Column('origination_credit_bureau_score_primary', sa.Integer(), nullable=True),
        sa.Column('origination_credit_bureau_score_co_borrower', sa.Integer(), nullable=True),
        sa.Column('refreshed_credit_bureau_score', sa.Integer(), nullable=True),
        sa.Column('behavioral_score', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('original_credit_limit', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('current_credit_limit', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('current_cash_advance_limit', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('line_frozen_flag', sa.Integer(), nullable=True),
        sa.Column('line_increase_decrease_flag', sa.Integer(), nullable=True),
        sa.Column('minimum_payment_due', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('total_payment_due', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('actual_payment_amount', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('total_past_due', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('days_past_due', sa.Integer(), nullable=True),
        sa.Column('apr_at_cycle_end', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('variable_rate_index', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('variable_rate_margin', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('maximum_apr', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('rate_reset_frequency', sa.Integer(), nullable=True),
        sa.Column('promotional_apr', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('cash_apr', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('account_60_plus_dpd_last_three_years_flag', sa.Integer(), nullable=True),
        sa.Column('fee_type', sa.Integer(), nullable=True),
        sa.Column('month_end_account_status_active_closed', sa.Integer(), nullable=True),
        sa.Column('account_sold_flag', sa.Integer(), nullable=True),
        sa.Column('bankruptcy_flag', sa.Integer(), nullable=True),
        sa.Column('loss_sharing', sa.Integer(), nullable=True),
        sa.Column('purchase_amount', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('cash_advance_amount', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('balance_transfer_amount', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('convenience_check_amount', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('charge_off_reason', sa.Integer(), nullable=True),
        sa.Column('gross_charge_off_amount', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('recovery_amount', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('principal_charge_off_amount', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('probability_of_default', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('loss_given_default', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('expected_loss_given_default', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('exposure_at_default', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('ead_id_segment', sa.String(length=50), nullable=True),
        sa.Column('loss_share_id', sa.String(length=50), nullable=True),
        sa.Column('loss_share_rate', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('other_credits', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('late_fee', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('over_limit_fee', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('nsf_fee', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('cash_advance_fee', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('monthly_annual_fee', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('debt_suspension_fee', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('balance_transfer_fee', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('other_fee', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('cycles_past_due_at_cycle_date', sa.Integer(), nullable=True),
        sa.Column('cycles_past_due_at_month_end', sa.Integer(), nullable=True),
        sa.Column('hardship_program_flag', sa.Integer(), nullable=True),
        sa.Column('payment_assistance_program_flag', sa.Integer(), nullable=True),
        sa.Column('workout_program_flag', sa.Integer(), nullable=True),
        sa.Column('debt_management_program_flag', sa.Integer(), nullable=True),
        sa.Column('forbearance_program_flag', sa.Integer(), nullable=True),
        sa.Column('trial_modification_program_flag', sa.Integer(), nullable=True),
        sa.Column('permanent_modification_program_flag', sa.Integer(), nullable=True),
        sa.Column('short_sale_program_flag', sa.Integer(), nullable=True),
        sa.Column('original_credit_bureau_score_name', sa.String(length=100), nullable=True),
        sa.Column('refreshed_credit_bureau_score_name', sa.String(length=100), nullable=True),
        sa.Column('behavioral_score_name', sa.String(length=100), nullable=True),
        sa.Column('behavioral_score_version', sa.String(length=100), nullable=True),
        sa.Column('credit_limit_change_type', sa.Integer(), nullable=True),
        sa.Column('line_change_type', sa.Integer(), nullable=True),
        sa.Column('internal_credit_score_flag', sa.Integer(), nullable=True),
        sa.Column('internal_credit_score_value', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('entity_type', sa.Integer(), nullable=True),
        sa.Column('national_bank_rssd_id', sa.String(length=20), nullable=True),
        sa.Column('utilization_rate', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('account_age_months', sa.Integer(), nullable=True),
        sa.Column('last_statement_balance', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('interest_charged', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('available_credit', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('payment_channel', sa.Integer(), nullable=True),
        sa.Column('cycle_days', sa.Integer(), nullable=True),
        sa.Column('stmt_closing_balance', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_fry14m_account_origination_date', 'fry14m_scheduled1_data', ['account_origination_date'], unique=False)
    op.create_index('idx_fry14m_customer_id', 'fry14m_scheduled1_data', ['customer_id'], unique=False)
    op.create_index('idx_fry14m_period_id', 'fry14m_scheduled1_data', ['period_id'], unique=False)
    op.create_index('idx_fry14m_reference_number', 'fry14m_scheduled1_data', ['reference_number'], unique=False)
    op.create_index('idx_fry14m_state', 'fry14m_scheduled1_data', ['state'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('idx_fry14m_state', table_name='fry14m_scheduled1_data')
    op.drop_index('idx_fry14m_reference_number', table_name='fry14m_scheduled1_data')
    op.drop_index('idx_fry14m_period_id', table_name='fry14m_scheduled1_data')
    op.drop_index('idx_fry14m_customer_id', table_name='fry14m_scheduled1_data')
    op.drop_index('idx_fry14m_account_origination_date', table_name='fry14m_scheduled1_data')
    
    # Drop table
    op.drop_table('fry14m_scheduled1_data')