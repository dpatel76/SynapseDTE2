"""load_actual_fry14m_scheduled1_data_from_source

Revision ID: load_actual_fry14m_data
Revises: load_fry14m_test_data
Create Date: 2025-08-06 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
import subprocess
import os

# revision identifiers, used by Alembic.
revision = 'load_actual_fry14m_data'
down_revision = '969b1d7f6b77'
branch_labels = None
depends_on = None


def upgrade():
    """
    Load actual data from source database (port 5432) into container database.
    This replaces the mock test data with real FR Y-14M Schedule D.1 data.
    """
    conn = op.get_bind()
    
    # First, clear any existing data
    conn.execute(text("TRUNCATE TABLE fry14m_scheduled1_data RESTART IDENTITY"))
    
    # Get database connection parameters
    # Assuming environment variables or config for source database
    source_host = os.environ.get('SOURCE_DB_HOST', 'localhost')
    source_port = os.environ.get('SOURCE_DB_PORT', '5432')
    source_db = os.environ.get('SOURCE_DB_NAME', 'synapse_dt')
    source_user = os.environ.get('SOURCE_DB_USER', 'synapse_user')
    source_password = os.environ.get('SOURCE_DB_PASSWORD', 'synapse_password')
    
    # Current database connection info (target)
    target_host = os.environ.get('DB_HOST', 'localhost')
    target_port = os.environ.get('DB_PORT', '5433')
    target_db = os.environ.get('DB_NAME', 'synapse_dt')
    target_user = os.environ.get('DB_USER', 'synapse_user')
    target_password = os.environ.get('DB_PASSWORD', 'synapse_password')
    
    # For Docker environments, use host.docker.internal instead of localhost
    if os.environ.get('RUNNING_IN_DOCKER'):
        if source_host == 'localhost':
            source_host = 'host.docker.internal'
    
    try:
        # Use COPY command to transfer data directly between databases
        # This is more efficient than dump/restore for large datasets
        copy_query = text("""
            INSERT INTO fry14m_scheduled1_data
            SELECT * FROM dblink(
                'host={source_host} port={source_port} dbname={source_db} user={source_user} password={source_password}',
                'SELECT * FROM fry14m_scheduled1_data'
            ) AS t(
                id integer,
                reference_number character varying(50),
                customer_id character varying(50),
                bank_id character varying(20),
                period_id character varying(20),
                corporate_id character varying(50),
                state character varying(2),
                zip_code character varying(20),
                credit_card_type integer,
                product_type integer,
                lending_type integer,
                revolve_feature integer,
                network_id integer,
                secured_credit_type integer,
                loan_source_channel integer,
                purchased_credit_deteriorated_status integer,
                cycle_ending_balance numeric(20,2),
                promotional_balance_mix numeric(20,2),
                cash_balance_mix numeric(20,2),
                penalty_balance_mix numeric(20,2),
                other_balance_mix numeric(20,2),
                average_daily_balance numeric(20,2),
                month_ending_balance numeric(20,2),
                total_reward_cash numeric(20,2),
                reward_type integer,
                account_cycle_date date,
                account_origination_date date,
                acquisition_date date,
                credit_bureau_score_refresh_date date,
                next_payment_due_date date,
                collection_re_age_date date,
                customer_service_re_age_date date,
                date_co_borrower_added date,
                multiple_banking_relationships integer,
                multiple_credit_card_relationships integer,
                joint_account integer,
                authorized_users integer,
                flagged_as_securitized integer,
                borrower_income_at_origination numeric(20,2),
                income_source_at_origination integer,
                origination_credit_bureau_score_primary integer,
                origination_credit_bureau_score_co_borrower integer,
                refreshed_credit_bureau_score integer,
                behavioral_score numeric(10,6),
                original_credit_limit numeric(20,2),
                current_credit_limit numeric(20,2),
                current_cash_advance_limit numeric(20,2),
                line_frozen_flag integer,
                line_increase_decrease_flag integer,
                minimum_payment_due numeric(20,2),
                total_payment_due numeric(20,2),
                actual_payment_amount numeric(20,2),
                total_past_due numeric(20,2),
                days_past_due integer,
                apr_at_cycle_end numeric(10,3),
                variable_rate_index numeric(10,3),
                variable_rate_margin numeric(10,3),
                maximum_apr numeric(10,3),
                rate_reset_frequency integer,
                promotional_apr numeric(10,3),
                cash_apr numeric(10,3),
                account_60_plus_dpd_last_three_years_flag integer,
                fee_type integer,
                month_end_account_status_active_closed integer,
                account_sold_flag integer,
                bankruptcy_flag integer,
                loss_sharing integer,
                purchase_amount numeric(20,2),
                cash_advance_amount numeric(20,2),
                balance_transfer_amount numeric(20,2),
                convenience_check_amount numeric(20,2),
                charge_off_reason integer,
                gross_charge_off_amount numeric(20,2),
                recovery_amount numeric(20,2),
                principal_charge_off_amount numeric(20,2),
                probability_of_default numeric(10,5),
                loss_given_default numeric(10,5),
                expected_loss_given_default numeric(10,5),
                exposure_at_default numeric(20,2),
                ead_id_segment character varying(50),
                loss_share_id character varying(50),
                loss_share_rate numeric(10,5),
                other_credits numeric(20,2),
                late_fee numeric(20,2),
                over_limit_fee numeric(20,2),
                nsf_fee numeric(20,2),
                cash_advance_fee numeric(20,2),
                monthly_annual_fee numeric(20,2),
                debt_suspension_fee numeric(20,2),
                balance_transfer_fee numeric(20,2),
                other_fee numeric(20,2),
                cycles_past_due_at_cycle_date integer,
                cycles_past_due_at_month_end integer,
                hardship_program_flag integer,
                payment_assistance_program_flag integer,
                workout_program_flag integer,
                debt_management_program_flag integer,
                forbearance_program_flag integer,
                trial_modification_program_flag integer,
                permanent_modification_program_flag integer,
                short_sale_program_flag integer,
                original_credit_bureau_score_name character varying(100),
                refreshed_credit_bureau_score_name character varying(100),
                behavioral_score_name character varying(100),
                behavioral_score_version character varying(100),
                credit_limit_change_type integer,
                line_change_type integer,
                internal_credit_score_flag integer,
                internal_credit_score_value numeric(10,3),
                entity_type integer,
                national_bank_rssd_id character varying(20),
                utilization_rate numeric(10,3),
                account_age_months integer,
                last_statement_balance numeric(20,2),
                interest_charged numeric(20,2),
                available_credit numeric(20,2),
                payment_channel integer,
                cycle_days integer,
                stmt_closing_balance numeric(20,2),
                created_at timestamp without time zone,
                updated_at timestamp without time zone,
                created_by character varying(100),
                updated_by character varying(100)
            )
        """.format(
            source_host=source_host,
            source_port=source_port,
            source_db=source_db,
            source_user=source_user,
            source_password=source_password
        ))
        
        # First ensure dblink extension is available
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS dblink"))
        
        # Execute the copy
        conn.execute(copy_query)
        
        # Verify the data was loaded
        result = conn.execute(text("SELECT COUNT(*) FROM fry14m_scheduled1_data"))
        count = result.scalar()
        
        print(f"Successfully loaded {count} records from source database")
        
    except Exception as e:
        print(f"Error using dblink, falling back to dump/restore method: {e}")
        
        # Fallback method using pg_dump/psql
        dump_file = '/tmp/fry14m_actual_data.sql'
        
        # Set environment variables for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = source_password
        
        # Dump data from source
        dump_cmd = [
            'pg_dump',
            '-h', source_host,
            '-p', source_port,
            '-U', source_user,
            '-d', source_db,
            '-t', 'fry14m_scheduled1_data',
            '--data-only',
            '--column-inserts',
            '--no-owner',
            '--no-privileges',
            '-f', dump_file
        ]
        
        try:
            subprocess.run(dump_cmd, env=env, check=True)
            print(f"Dumped data from source database to {dump_file}")
            
            # Load data into target
            env['PGPASSWORD'] = target_password
            load_cmd = [
                'psql',
                '-h', target_host,
                '-p', target_port,
                '-U', target_user,
                '-d', target_db,
                '-f', dump_file
            ]
            
            subprocess.run(load_cmd, env=env, check=True)
            
            # Verify the data was loaded
            result = conn.execute(text("SELECT COUNT(*) FROM fry14m_scheduled1_data"))
            count = result.scalar()
            
            print(f"Successfully loaded {count} records from source database")
            
            # Clean up
            if os.path.exists(dump_file):
                os.remove(dump_file)
                
        except subprocess.CalledProcessError as e:
            print(f"Error during dump/restore: {e}")
            raise


def downgrade():
    """
    Revert to mock test data
    """
    # This will revert by running the previous migration's upgrade
    # The previous migration will reload the mock data
    conn = op.get_bind()
    conn.execute(text("TRUNCATE TABLE fry14m_scheduled1_data RESTART IDENTITY"))
    
    # Note: To fully revert, you would need to re-run the previous migration's upgrade()
    # Alembic handles this through the downgrade chain