"""Add FR Y-14M Schedule D.1 data table

Revision ID: add_fry14m_scheduled1_data
Revises: 
Create Date: 2025-01-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_fry14m_scheduled1_data'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create fry14m_scheduled1_data table with 118 columns"""
    
    op.create_table('fry14m_scheduled1_data',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        
        # Reference and identification columns
        sa.Column('reference_number', sa.String(50), nullable=True),
        sa.Column('customer_id', sa.String(50), nullable=True),
        sa.Column('bank_id', sa.String(50), nullable=True),
        sa.Column('period_id', sa.String(10), nullable=True),
        sa.Column('corporate_id', sa.String(50), nullable=True),
        
        # Location columns
        sa.Column('state', sa.String(2), nullable=True),
        sa.Column('zip_code', sa.String(10), nullable=True),
        
        # Product type columns
        sa.Column('credit_card_type', sa.Integer(), nullable=True),
        sa.Column('product_type', sa.Integer(), nullable=True),
        sa.Column('lending_type', sa.Integer(), nullable=True),
        sa.Column('revolve_feature', sa.Integer(), nullable=True),
        sa.Column('network_id', sa.Integer(), nullable=True),
        sa.Column('secured_credit_type', sa.Integer(), nullable=True),
        sa.Column('loan_source_channel', sa.Integer(), nullable=True),
        sa.Column('purchased_credit_deteriorated_status', sa.Integer(), nullable=True),
        
        # Balance columns
        sa.Column('cycle_ending_balance', sa.Numeric(20, 2), nullable=True),
        sa.Column('promotional_balance_mix', sa.Numeric(20, 2), nullable=True),
        sa.Column('cash_balance_mix', sa.Numeric(20, 2), nullable=True),
        sa.Column('penalty_balance_mix', sa.Numeric(20, 2), nullable=True),
        sa.Column('other_balance_mix', sa.Numeric(20, 2), nullable=True),
        sa.Column('average_daily_balance', sa.Numeric(20, 2), nullable=True),
        sa.Column('month_ending_balance', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_reward_cash', sa.Numeric(20, 2), nullable=True),
        
        # Reward and dates
        sa.Column('reward_type', sa.Integer(), nullable=True),
        sa.Column('account_cycle_date', sa.Date(), nullable=True),
        sa.Column('account_origination_date', sa.Date(), nullable=True),
        sa.Column('acquisition_date', sa.Date(), nullable=True),
        sa.Column('credit_bureau_score_refresh_date', sa.Date(), nullable=True),
        sa.Column('next_payment_due_date', sa.Date(), nullable=True),
        sa.Column('collection_re_age_date', sa.Date(), nullable=True),
        sa.Column('customer_service_re_age_date', sa.Date(), nullable=True),
        sa.Column('date_co_borrower_added', sa.Date(), nullable=True),
        
        # Relationship flags
        sa.Column('multiple_banking_relationships', sa.Integer(), nullable=True),
        sa.Column('multiple_credit_card_relationships', sa.Integer(), nullable=True),
        sa.Column('joint_account', sa.Integer(), nullable=True),
        sa.Column('authorized_users', sa.Integer(), nullable=True),
        sa.Column('flagged_as_securitized', sa.Integer(), nullable=True),
        
        # Income and credit scores
        sa.Column('borrower_income_at_origination', sa.Numeric(20, 2), nullable=True),
        sa.Column('income_source_at_origination', sa.Integer(), nullable=True),
        sa.Column('origination_credit_bureau_score_primary', sa.Integer(), nullable=True),
        sa.Column('origination_credit_bureau_score_co_borrower', sa.Integer(), nullable=True),
        sa.Column('refreshed_credit_bureau_score', sa.Integer(), nullable=True),
        sa.Column('behavioral_score', sa.Numeric(10, 6), nullable=True),
        
        # Credit limits
        sa.Column('original_credit_limit', sa.Numeric(20, 2), nullable=True),
        sa.Column('current_credit_limit', sa.Numeric(20, 2), nullable=True),
        sa.Column('current_cash_advance_limit', sa.Numeric(20, 2), nullable=True),
        
        # Flags
        sa.Column('line_frozen_flag', sa.Integer(), nullable=True),
        sa.Column('line_increase_decrease_flag', sa.Integer(), nullable=True),
        
        # Payment information
        sa.Column('minimum_payment_due', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_payment_due', sa.Numeric(20, 2), nullable=True),
        sa.Column('actual_payment_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_past_due', sa.Numeric(20, 2), nullable=True),
        sa.Column('days_past_due', sa.Integer(), nullable=True),
        
        # APR and rates
        sa.Column('apr_at_cycle_end', sa.Numeric(10, 3), nullable=True),
        sa.Column('variable_rate_index', sa.Numeric(10, 3), nullable=True),
        sa.Column('variable_rate_margin', sa.Numeric(10, 3), nullable=True),
        sa.Column('maximum_apr', sa.Numeric(10, 3), nullable=True),
        sa.Column('rate_reset_frequency', sa.Integer(), nullable=True),
        sa.Column('promotional_apr', sa.Numeric(10, 3), nullable=True),
        sa.Column('cash_apr', sa.Numeric(10, 3), nullable=True),
        
        # Account status flags
        sa.Column('account_60_plus_dpd_last_three_years_flag', sa.Integer(), nullable=True),
        sa.Column('fee_type', sa.Integer(), nullable=True),
        sa.Column('month_end_account_status_active_closed', sa.Integer(), nullable=True),
        sa.Column('account_sold_flag', sa.Integer(), nullable=True),
        sa.Column('bankruptcy_flag', sa.Integer(), nullable=True),
        sa.Column('loss_sharing', sa.Integer(), nullable=True),
        
        # Transaction amounts
        sa.Column('purchase_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('cash_advance_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('balance_transfer_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('convenience_check_amount', sa.Numeric(20, 2), nullable=True),
        
        # Charge-off and recovery
        sa.Column('charge_off_reason', sa.Integer(), nullable=True),
        sa.Column('gross_charge_off_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('recovery_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('principal_charge_off_amount', sa.Numeric(20, 2), nullable=True),
        
        # Risk metrics
        sa.Column('probability_of_default', sa.Numeric(10, 5), nullable=True),
        sa.Column('loss_given_default', sa.Numeric(10, 5), nullable=True),
        sa.Column('expected_loss_given_default', sa.Numeric(10, 5), nullable=True),
        sa.Column('exposure_at_default', sa.Numeric(20, 2), nullable=True),
        sa.Column('ead_id_segment', sa.String(50), nullable=True),
        sa.Column('loss_share_id', sa.String(50), nullable=True),
        sa.Column('loss_share_rate', sa.Numeric(10, 5), nullable=True),
        
        # Fee columns
        sa.Column('other_credits', sa.Numeric(20, 2), nullable=True),
        sa.Column('late_fee', sa.Numeric(20, 2), nullable=True),
        sa.Column('over_limit_fee', sa.Numeric(20, 2), nullable=True),
        sa.Column('nsf_fee', sa.Numeric(20, 2), nullable=True),
        sa.Column('cash_advance_fee', sa.Numeric(20, 2), nullable=True),
        sa.Column('monthly_annual_fee', sa.Numeric(20, 2), nullable=True),
        sa.Column('debt_suspension_fee', sa.Numeric(20, 2), nullable=True),
        sa.Column('balance_transfer_fee', sa.Numeric(20, 2), nullable=True),
        sa.Column('other_fee', sa.Numeric(20, 2), nullable=True),
        
        # Past due cycles
        sa.Column('cycles_past_due_at_cycle_date', sa.Integer(), nullable=True),
        sa.Column('cycles_past_due_at_month_end', sa.Integer(), nullable=True),
        
        # Program flags
        sa.Column('hardship_program_flag', sa.Integer(), nullable=True),
        sa.Column('payment_assistance_program_flag', sa.Integer(), nullable=True),
        sa.Column('workout_program_flag', sa.Integer(), nullable=True),
        sa.Column('debt_management_program_flag', sa.Integer(), nullable=True),
        sa.Column('forbearance_program_flag', sa.Integer(), nullable=True),
        sa.Column('trial_modification_program_flag', sa.Integer(), nullable=True),
        sa.Column('permanent_modification_program_flag', sa.Integer(), nullable=True),
        sa.Column('short_sale_program_flag', sa.Integer(), nullable=True),
        
        # Score names and identifiers
        sa.Column('original_credit_bureau_score_name', sa.String(100), nullable=True),
        sa.Column('refreshed_credit_bureau_score_name', sa.String(100), nullable=True),
        sa.Column('behavioral_score_name', sa.String(100), nullable=True),
        sa.Column('behavioral_score_version', sa.String(100), nullable=True),
        
        # Line change types
        sa.Column('credit_limit_change_type', sa.Integer(), nullable=True),
        sa.Column('line_change_type', sa.Integer(), nullable=True),
        
        # Internal score
        sa.Column('internal_credit_score_flag', sa.Integer(), nullable=True),
        sa.Column('internal_credit_score_value', sa.Numeric(10, 3), nullable=True),
        
        # Entity information
        sa.Column('entity_type', sa.Integer(), nullable=True),
        sa.Column('national_bank_rssd_id', sa.String(50), nullable=True),
        
        # Additional metrics
        sa.Column('utilization_rate', sa.Numeric(10, 3), nullable=True),
        sa.Column('account_age_months', sa.Integer(), nullable=True),
        sa.Column('last_statement_balance', sa.Numeric(20, 2), nullable=True),
        sa.Column('interest_charged', sa.Numeric(20, 2), nullable=True),
        sa.Column('available_credit', sa.Numeric(20, 2), nullable=True),
        sa.Column('payment_channel', sa.Integer(), nullable=True),
        sa.Column('cycle_days', sa.Integer(), nullable=True),
        sa.Column('stmt_closing_balance', sa.Numeric(20, 2), nullable=True),
        
        # Audit columns
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('updated_by', sa.String(100), nullable=True),
        
        # Indexes
        sa.Index('idx_fry14m_reference_number', 'reference_number'),
        sa.Index('idx_fry14m_customer_id', 'customer_id'),
        sa.Index('idx_fry14m_period_id', 'period_id'),
        sa.Index('idx_fry14m_account_origination_date', 'account_origination_date'),
        sa.Index('idx_fry14m_state', 'state'),
    )


def downgrade():
    """Drop fry14m_scheduled1_data table"""
    op.drop_table('fry14m_scheduled1_data')