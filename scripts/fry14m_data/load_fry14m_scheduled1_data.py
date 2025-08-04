"""Load FR Y-14M Schedule D.1 test data from CSV file into database"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine
from app.core.logging import get_logger
import os
from typing import Dict, Any, Optional

logger = get_logger(__name__)

# Column mappings from CSV headers to database columns
COLUMN_MAPPINGS = {
    'REFERENCE_NUMBER': 'reference_number',
    'CUSTOMER_ID': 'customer_id',
    'BANK_ID': 'bank_id',
    'PERIOD_ID': 'period_id',
    'CORPORATE_ID': 'corporate_id',
    'STATE': 'state',
    'ZIP_CODE': 'zip_code',
    'CREDIT_CARD_TYPE': 'credit_card_type',
    'PRODUCT_TYPE': 'product_type',
    'LENDING_TYPE': 'lending_type',
    'REVOLVE_FEATURE': 'revolve_feature',
    'NETWORK_ID': 'network_id',
    'SECURED_CREDIT_TYPE': 'secured_credit_type',
    'LOAN_SOURCE_CHANNEL': 'loan_source_channel',
    'PURCHASED_CREDIT_DETERIORATED_STATUS': 'purchased_credit_deteriorated_status',
    'CYCLE_ENDING_BALANCE': 'cycle_ending_balance',
    'PROMOTIONAL_BALANCE_MIX': 'promotional_balance_mix',
    'CASH_BALANCE_MIX': 'cash_balance_mix',
    'PENALTY_BALANCE_MIX': 'penalty_balance_mix',
    'OTHER_BALANCE_MIX': 'other_balance_mix',
    'AVERAGE_DAILY_BALANCE': 'average_daily_balance',
    'MONTH_ENDING_BALANCE': 'month_ending_balance',
    'TOTAL_REWARD_CASH': 'total_reward_cash',
    'REWARD_TYPE': 'reward_type',
    'ACCOUNT_CYCLE_DATE': 'account_cycle_date',
    'ACCOUNT_ORIGINATION_DATE': 'account_origination_date',
    'ACQUISITION_DATE': 'acquisition_date',
    'CREDIT_BUREAU_SCORE_REFRESH_DATE': 'credit_bureau_score_refresh_date',
    'NEXT_PAYMENT_DUE_DATE': 'next_payment_due_date',
    'COLLECTION_RE_AGE_DATE': 'collection_re_age_date',
    'CUSTOMER_SERVICE_RE_AGE_DATE': 'customer_service_re_age_date',
    'DATE_CO_BORROWER_ADDED': 'date_co_borrower_added',
    'MULTIPLE_BANKING_RELATIONSHIPS': 'multiple_banking_relationships',
    'MULTIPLE_CREDIT_CARD_RELATIONSHIPS': 'multiple_credit_card_relationships',
    'JOINT_ACCOUNT': 'joint_account',
    'AUTHORIZED_USERS': 'authorized_users',
    'FLAGGED_AS_SECURITIZED': 'flagged_as_securitized',
    'BORROWER_INCOME_AT_ORIGINATION': 'borrower_income_at_origination',
    'INCOME_SOURCE_AT_ORIGINATION': 'income_source_at_origination',
    'ORIGINATION_CREDIT_BUREAU_SCORE_PRIMARY': 'origination_credit_bureau_score_primary',
    'ORIGINATION_CREDIT_BUREAU_SCORE_CO_BORROWER': 'origination_credit_bureau_score_co_borrower',
    'REFRESHED_CREDIT_BUREAU_SCORE': 'refreshed_credit_bureau_score',
    'BEHAVIORAL_SCORE': 'behavioral_score',
    'ORIGINAL_CREDIT_LIMIT': 'original_credit_limit',
    'CURRENT_CREDIT_LIMIT': 'current_credit_limit',
    'CURRENT_CASH_ADVANCE_LIMIT': 'current_cash_advance_limit',
    'LINE_FROZEN_FLAG': 'line_frozen_flag',
    'LINE_INCREASE_DECREASE_FLAG': 'line_increase_decrease_flag',
    'MINIMUM_PAYMENT_DUE': 'minimum_payment_due',
    'TOTAL_PAYMENT_DUE': 'total_payment_due',
    'ACTUAL_PAYMENT_AMOUNT': 'actual_payment_amount',
    'TOTAL_PAST_DUE': 'total_past_due',
    'DAYS_PAST_DUE': 'days_past_due',
    'APR_AT_CYCLE_END': 'apr_at_cycle_end',
    'VARIABLE_RATE_INDEX': 'variable_rate_index',
    'VARIABLE_RATE_MARGIN': 'variable_rate_margin',
    'MAXIMUM_APR': 'maximum_apr',
    'RATE_RESET_FREQUENCY': 'rate_reset_frequency',
    'PROMOTIONAL_APR': 'promotional_apr',
    'CASH_APR': 'cash_apr',
    'ACCOUNT_60_PLUS_DPD_LAST_THREE_YEARS_FLAG': 'account_60_plus_dpd_last_three_years_flag',
    'FEE_TYPE': 'fee_type',
    'MONTH_END_ACCOUNT_STATUS_ACTIVE_CLOSED': 'month_end_account_status_active_closed',
    'ACCOUNT_SOLD_FLAG': 'account_sold_flag',
    'BANKRUPTCY_FLAG': 'bankruptcy_flag',
    'LOSS_SHARING': 'loss_sharing',
    'PURCHASE_AMOUNT': 'purchase_amount',
    'CASH_ADVANCE_AMOUNT': 'cash_advance_amount',
    'BALANCE_TRANSFER_AMOUNT': 'balance_transfer_amount',
    'CONVENIENCE_CHECK_AMOUNT': 'convenience_check_amount',
    'CHARGE_OFF_REASON': 'charge_off_reason',
    'GROSS_CHARGE_OFF_AMOUNT': 'gross_charge_off_amount',
    'RECOVERY_AMOUNT': 'recovery_amount',
    'PRINCIPAL_CHARGE_OFF_AMOUNT': 'principal_charge_off_amount',
    'PROBABILITY_OF_DEFAULT': 'probability_of_default',
    'LOSS_GIVEN_DEFAULT': 'loss_given_default',
    'EXPECTED_LOSS_GIVEN_DEFAULT': 'expected_loss_given_default',
    'EXPOSURE_AT_DEFAULT': 'exposure_at_default',
    'EAD_ID_SEGMENT': 'ead_id_segment',
    'LOSS_SHARE_ID': 'loss_share_id',
    'LOSS_SHARE_RATE': 'loss_share_rate',
    'OTHER_CREDITS': 'other_credits',
    'LATE_FEE': 'late_fee',
    'OVER_LIMIT_FEE': 'over_limit_fee',
    'NSF_FEE': 'nsf_fee',
    'CASH_ADVANCE_FEE': 'cash_advance_fee',
    'MONTHLY_ANNUAL_FEE': 'monthly_annual_fee',
    'DEBT_SUSPENSION_FEE': 'debt_suspension_fee',
    'BALANCE_TRANSFER_FEE': 'balance_transfer_fee',
    'OTHER_FEE': 'other_fee',
    'CYCLES_PAST_DUE_AT_CYCLE_DATE': 'cycles_past_due_at_cycle_date',
    'CYCLES_PAST_DUE_AT_MONTH_END': 'cycles_past_due_at_month_end',
    'HARDSHIP_PROGRAM_FLAG': 'hardship_program_flag',
    'PAYMENT_ASSISTANCE_PROGRAM_FLAG': 'payment_assistance_program_flag',
    'WORKOUT_PROGRAM_FLAG': 'workout_program_flag',
    'DEBT_MANAGEMENT_PROGRAM_FLAG': 'debt_management_program_flag',
    'FORBEARANCE_PROGRAM_FLAG': 'forbearance_program_flag',
    'TRIAL_MODIFICATION_PROGRAM_FLAG': 'trial_modification_program_flag',
    'PERMANENT_MODIFICATION_PROGRAM_FLAG': 'permanent_modification_program_flag',
    'SHORT_SALE_PROGRAM_FLAG': 'short_sale_program_flag',
    'ORIGINAL_CREDIT_BUREAU_SCORE_NAME': 'original_credit_bureau_score_name',
    'REFRESHED_CREDIT_BUREAU_SCORE_NAME': 'refreshed_credit_bureau_score_name',
    'BEHAVIORAL_SCORE_NAME': 'behavioral_score_name',
    'BEHAVIORAL_SCORE_VERSION': 'behavioral_score_version',
    'CREDIT_LIMIT_CHANGE_TYPE': 'credit_limit_change_type',
    'LINE_CHANGE_TYPE': 'line_change_type',
    'INTERNAL_CREDIT_SCORE_FLAG': 'internal_credit_score_flag',
    'INTERNAL_CREDIT_SCORE_VALUE': 'internal_credit_score_value',
    'ENTITY_TYPE': 'entity_type',
    'NATIONAL_BANK_RSSD_ID': 'national_bank_rssd_id',
    'UTILIZATION_RATE': 'utilization_rate',
    'ACCOUNT_AGE_MONTHS': 'account_age_months',
    'LAST_STATEMENT_BALANCE': 'last_statement_balance',
    'INTEREST_CHARGED': 'interest_charged',
    'AVAILABLE_CREDIT': 'available_credit',
    'PAYMENT_CHANNEL': 'payment_channel',
    'CYCLE_DAYS': 'cycle_days',
    'STMT_CLOSING_BALANCE': 'stmt_closing_balance'
}

# Define date columns for proper parsing
DATE_COLUMNS = [
    'ACCOUNT_CYCLE_DATE', 'ACCOUNT_ORIGINATION_DATE', 'ACQUISITION_DATE',
    'CREDIT_BUREAU_SCORE_REFRESH_DATE', 'NEXT_PAYMENT_DUE_DATE',
    'COLLECTION_RE_AGE_DATE', 'CUSTOMER_SERVICE_RE_AGE_DATE',
    'DATE_CO_BORROWER_ADDED'
]

# Define numeric columns
NUMERIC_COLUMNS = [
    'CYCLE_ENDING_BALANCE', 'PROMOTIONAL_BALANCE_MIX', 'CASH_BALANCE_MIX',
    'PENALTY_BALANCE_MIX', 'OTHER_BALANCE_MIX', 'AVERAGE_DAILY_BALANCE',
    'MONTH_ENDING_BALANCE', 'TOTAL_REWARD_CASH', 'BORROWER_INCOME_AT_ORIGINATION',
    'BEHAVIORAL_SCORE', 'ORIGINAL_CREDIT_LIMIT', 'CURRENT_CREDIT_LIMIT',
    'CURRENT_CASH_ADVANCE_LIMIT', 'MINIMUM_PAYMENT_DUE', 'TOTAL_PAYMENT_DUE',
    'ACTUAL_PAYMENT_AMOUNT', 'TOTAL_PAST_DUE', 'APR_AT_CYCLE_END',
    'VARIABLE_RATE_INDEX', 'VARIABLE_RATE_MARGIN', 'MAXIMUM_APR',
    'PROMOTIONAL_APR', 'CASH_APR', 'PURCHASE_AMOUNT', 'CASH_ADVANCE_AMOUNT',
    'BALANCE_TRANSFER_AMOUNT', 'CONVENIENCE_CHECK_AMOUNT',
    'GROSS_CHARGE_OFF_AMOUNT', 'RECOVERY_AMOUNT', 'PRINCIPAL_CHARGE_OFF_AMOUNT',
    'PROBABILITY_OF_DEFAULT', 'LOSS_GIVEN_DEFAULT', 'EXPECTED_LOSS_GIVEN_DEFAULT',
    'EXPOSURE_AT_DEFAULT', 'LOSS_SHARE_RATE', 'OTHER_CREDITS', 'LATE_FEE',
    'OVER_LIMIT_FEE', 'NSF_FEE', 'CASH_ADVANCE_FEE', 'MONTHLY_ANNUAL_FEE',
    'DEBT_SUSPENSION_FEE', 'BALANCE_TRANSFER_FEE', 'OTHER_FEE',
    'INTERNAL_CREDIT_SCORE_VALUE', 'UTILIZATION_RATE', 'LAST_STATEMENT_BALANCE',
    'INTEREST_CHARGED', 'AVAILABLE_CREDIT', 'STMT_CLOSING_BALANCE'
]

# Integer columns
INTEGER_COLUMNS = [
    'CREDIT_CARD_TYPE', 'PRODUCT_TYPE', 'LENDING_TYPE', 'REVOLVE_FEATURE',
    'NETWORK_ID', 'SECURED_CREDIT_TYPE', 'LOAN_SOURCE_CHANNEL',
    'PURCHASED_CREDIT_DETERIORATED_STATUS', 'REWARD_TYPE',
    'MULTIPLE_BANKING_RELATIONSHIPS', 'MULTIPLE_CREDIT_CARD_RELATIONSHIPS',
    'JOINT_ACCOUNT', 'AUTHORIZED_USERS', 'FLAGGED_AS_SECURITIZED',
    'INCOME_SOURCE_AT_ORIGINATION', 'ORIGINATION_CREDIT_BUREAU_SCORE_PRIMARY',
    'ORIGINATION_CREDIT_BUREAU_SCORE_CO_BORROWER', 'REFRESHED_CREDIT_BUREAU_SCORE',
    'LINE_FROZEN_FLAG', 'LINE_INCREASE_DECREASE_FLAG', 'DAYS_PAST_DUE',
    'RATE_RESET_FREQUENCY', 'ACCOUNT_60_PLUS_DPD_LAST_THREE_YEARS_FLAG',
    'FEE_TYPE', 'MONTH_END_ACCOUNT_STATUS_ACTIVE_CLOSED', 'ACCOUNT_SOLD_FLAG',
    'BANKRUPTCY_FLAG', 'LOSS_SHARING', 'CHARGE_OFF_REASON',
    'CYCLES_PAST_DUE_AT_CYCLE_DATE', 'CYCLES_PAST_DUE_AT_MONTH_END',
    'HARDSHIP_PROGRAM_FLAG', 'PAYMENT_ASSISTANCE_PROGRAM_FLAG',
    'WORKOUT_PROGRAM_FLAG', 'DEBT_MANAGEMENT_PROGRAM_FLAG',
    'FORBEARANCE_PROGRAM_FLAG', 'TRIAL_MODIFICATION_PROGRAM_FLAG',
    'PERMANENT_MODIFICATION_PROGRAM_FLAG', 'SHORT_SALE_PROGRAM_FLAG',
    'CREDIT_LIMIT_CHANGE_TYPE', 'LINE_CHANGE_TYPE', 'INTERNAL_CREDIT_SCORE_FLAG',
    'ENTITY_TYPE', 'ACCOUNT_AGE_MONTHS', 'PAYMENT_CHANNEL', 'CYCLE_DAYS'
]


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in YYYYMMDD format"""
    if pd.isna(date_str) or str(date_str).strip() == '':
        return None
    try:
        # Handle YYYYMMDD format
        date_str = str(date_str).strip()
        if len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, '%Y%m%d')
        return None
    except Exception as e:
        logger.warning(f"Failed to parse date: {date_str}, error: {e}")
        return None


def clean_numeric(value: Any) -> Optional[float]:
    """Clean and convert numeric values"""
    if pd.isna(value) or str(value).strip() == '':
        return None
    try:
        return float(str(value).replace(',', ''))
    except Exception:
        return None


def clean_integer(value: Any) -> Optional[int]:
    """Clean and convert integer values"""
    if pd.isna(value) or str(value).strip() == '':
        return None
    try:
        return int(float(str(value).replace(',', '')))
    except Exception:
        return None


async def truncate_table(session: AsyncSession):
    """Truncate the fry14m_scheduled1_data table"""
    logger.info("Truncating existing data from fry14m_scheduled1_data table")
    await session.execute(text("TRUNCATE TABLE fry14m_scheduled1_data RESTART IDENTITY"))
    await session.commit()


async def load_data_batch(session: AsyncSession, batch_data: list):
    """Load a batch of data into the database"""
    try:
        # Build insert statement
        columns = list(batch_data[0].keys())
        placeholders = ', '.join([f':{col}' for col in columns])
        column_names = ', '.join(columns)
        
        insert_query = f"""
            INSERT INTO fry14m_scheduled1_data ({column_names})
            VALUES ({placeholders})
        """
        
        # Execute batch insert
        await session.execute(text(insert_query), batch_data)
        await session.commit()
        logger.info(f"Successfully inserted batch of {len(batch_data)} records")
        
    except Exception as e:
        logger.error(f"Failed to insert batch: {e}")
        await session.rollback()
        raise


async def load_fry14m_data():
    """Main function to load FR Y-14M Schedule D.1 data from CSV"""
    try:
        # Define CSV file path
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'tests', 'data', 'fr_y14m_schedule_d1_test_data_with_anomalies.csv'
        )
        
        logger.info(f"Reading CSV file from: {csv_path}")
        
        # Read CSV file
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns from CSV")
        
        # Process data in batches
        batch_size = 100
        all_records = []
        
        for idx, row in df.iterrows():
            record = {}
            
            # Process each column
            for csv_col, db_col in COLUMN_MAPPINGS.items():
                if csv_col in row:
                    value = row[csv_col]
                    
                    # Handle date columns
                    if csv_col in DATE_COLUMNS:
                        record[db_col] = parse_date(value)
                    
                    # Handle numeric columns
                    elif csv_col in NUMERIC_COLUMNS:
                        cleaned_value = clean_numeric(value)
                        record[db_col] = cleaned_value
                    
                    # Handle integer columns
                    elif csv_col in INTEGER_COLUMNS:
                        record[db_col] = clean_integer(value)
                    
                    # Handle string columns
                    else:
                        if pd.isna(value) or str(value).strip() == '':
                            record[db_col] = None
                        else:
                            record[db_col] = str(value).strip()
            
            # Add audit fields
            record['created_at'] = datetime.utcnow()
            record['updated_at'] = datetime.utcnow()
            record['created_by'] = 'data_load_script'
            record['updated_by'] = 'data_load_script'
            
            all_records.append(record)
            
            # Load batch when size is reached
            if len(all_records) >= batch_size:
                async with AsyncSessionLocal() as session:
                    await load_data_batch(session, all_records)
                all_records = []
        
        # Load remaining records
        if all_records:
            async with AsyncSessionLocal() as session:
                await load_data_batch(session, all_records)
        
        logger.info(f"Successfully loaded all {len(df)} records into fry14m_scheduled1_data table")
        
    except Exception as e:
        logger.error(f"Failed to load FR Y-14M data: {e}")
        raise


async def main():
    """Main entry point"""
    try:
        # First truncate existing data
        async with AsyncSessionLocal() as session:
            await truncate_table(session)
        
        # Load new data
        await load_fry14m_data()
        
        # Verify loaded data
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM fry14m_scheduled1_data")
            )
            count = result.scalar()
            logger.info(f"Total records in fry14m_scheduled1_data table: {count}")
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())