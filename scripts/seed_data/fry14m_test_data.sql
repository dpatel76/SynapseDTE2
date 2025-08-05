-- Seed data for fry14m_scheduled1_data table
-- This file contains sample credit card account data for testing purposes
-- It will be automatically loaded when setting up a new system

-- Clear existing data
TRUNCATE TABLE fry14m_scheduled1_data RESTART IDENTITY;

-- Insert sample test data
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
) VALUES
-- Sample records with various credit profiles
('REF00000001', 'CUST000001', 'BANK001', '202401', 'CORP0001', 'CA', '90001', 1, 1, 1, 1, 1, 0, 1, 
 2500.00, 0.00, 0.00, 2250.00, 2500.00, 25.00, 1, '2024-01-01', '2020-01-15',
 0, 0, 0, 0, 0, 65000.00, 1, 720, 725, 0.75, 5000.00, 5000.00, 2500.00, 0, 0,
 50.00, 2500.00, 50.00, 0.00, 0, 18.99, 1, 0, 50.000, 48, 2500.00,
 NOW(), NOW(), 'system', 'system'),

('REF00000002', 'CUST000002', 'BANK002', '202401', 'CORP0002', 'NY', '10001', 2, 2, 1, 1, 2, 0, 2,
 8000.00, 800.00, 0.00, 7200.00, 8000.00, 0.00, 0, '2024-01-01', '2021-03-20',
 1, 1, 0, 1, 0, 85000.00, 2, 680, 690, 0.65, 10000.00, 10000.00, 5000.00, 0, 0,
 160.00, 8000.00, 160.00, 0.00, 0, 21.99, 1, 0, 80.000, 36, 2000.00,
 NOW(), NOW(), 'system', 'system'),

('REF00000003', 'CUST000003', 'BANK003', '202401', 'CORP0003', 'TX', '75001', 3, 1, 1, 1, 3, 0, 3,
 500.00, 0.00, 0.00, 450.00, 500.00, 5.00, 1, '2024-01-01', '2022-06-10',
 0, 0, 0, 0, 0, 45000.00, 1, 650, 655, 0.60, 3000.00, 3000.00, 1500.00, 0, 0,
 25.00, 500.00, 25.00, 0.00, 0, 24.99, 1, 0, 16.667, 18, 2500.00,
 NOW(), NOW(), 'system', 'system'),

-- High utilization account
('REF00000004', 'CUST000004', 'BANK001', '202401', 'CORP0004', 'FL', '33001', 1, 1, 1, 1, 1, 0, 1,
 14500.00, 0.00, 500.00, 14000.00, 14500.00, 0.00, 0, '2024-01-01', '2019-11-05',
 1, 1, 0, 2, 0, 120000.00, 3, 760, 750, 0.72, 15000.00, 15000.00, 7500.00, 0, 0,
 290.00, 14500.00, 290.00, 0.00, 0, 16.99, 1, 0, 96.667, 52, 500.00,
 NOW(), NOW(), 'system', 'system'),

-- Delinquent account
('REF00000005', 'CUST000005', 'BANK002', '202401', 'CORP0005', 'IL', '60001', 2, 1, 1, 1, 2, 0, 2,
 6000.00, 0.00, 0.00, 5800.00, 6000.00, 0.00, 0, '2024-01-01', '2020-08-15',
 0, 1, 0, 0, 0, 55000.00, 1, 620, 600, 0.45, 8000.00, 8000.00, 4000.00, 0, 0,
 120.00, 6000.00, 0.00, 600.00, 30, 29.99, 1, 0, 75.000, 42, 2000.00,
 NOW(), NOW(), 'system', 'system'),

-- Secured card
('REF00000006', 'CUST000006', 'BANK003', '202401', 'CORP0001', 'PA', '19001', 1, 1, 1, 1, 1, 1, 1,
 200.00, 0.00, 0.00, 180.00, 200.00, 0.00, 0, '2024-01-01', '2023-01-10',
 0, 0, 0, 0, 0, 35000.00, 1, 580, 600, 0.55, 500.00, 500.00, 0.00, 0, 0,
 25.00, 200.00, 25.00, 0.00, 0, 22.99, 1, 0, 40.000, 12, 300.00,
 NOW(), NOW(), 'system', 'system'),

-- Premium rewards card
('REF00000007', 'CUST000007', 'BANK001', '202401', 'CORP0002', 'OH', '44001', 4, 3, 1, 1, 4, 0, 4,
 3500.00, 0.00, 0.00, 3200.00, 3500.00, 105.00, 2, '2024-01-01', '2018-05-20',
 1, 1, 1, 1, 0, 150000.00, 4, 800, 810, 0.85, 25000.00, 25000.00, 12500.00, 0, 1,
 70.00, 3500.00, 70.00, 0.00, 0, 14.99, 1, 0, 14.000, 68, 21500.00,
 NOW(), NOW(), 'system', 'system'),

-- Zero balance account
('REF00000008', 'CUST000008', 'BANK002', '202401', 'CORP0003', 'MI', '48001', 2, 1, 1, 1, 2, 0, 2,
 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0, '2024-01-01', '2021-09-01',
 1, 1, 0, 0, 0, 70000.00, 2, 700, 710, 0.78, 7500.00, 7500.00, 3750.00, 0, 0,
 0.00, 0.00, 0.00, 0.00, 0, 17.99, 1, 0, 0.000, 28, 7500.00,
 NOW(), NOW(), 'system', 'system'),

-- Line frozen account
('REF00000009', 'CUST000009', 'BANK003', '202401', 'CORP0004', 'GA', '30001', 3, 2, 1, 1, 3, 0, 3,
 4200.00, 0.00, 200.00, 4000.00, 4200.00, 0.00, 0, '2024-01-01', '2020-12-15',
 0, 0, 0, 0, 0, 60000.00, 1, 640, 630, 0.58, 5000.00, 5000.00, 2500.00, 1, 0,
 84.00, 4200.00, 0.00, 420.00, 60, 27.99, 1, 0, 84.000, 37, 800.00,
 NOW(), NOW(), 'system', 'system'),

-- Closed account
('REF00000010', 'CUST000010', 'BANK001', '202401', 'CORP0005', 'NC', '27001', 1, 1, 1, 1, 1, 0, 1,
 0.00, 0.00, 0.00, 0.00, 0.00, 50.00, 1, '2024-01-01', '2019-02-28',
 0, 1, 0, 0, 0, 50000.00, 1, 690, 700, 0.70, 10000.00, 0.00, 0.00, 0, 0,
 0.00, 0.00, 0.00, 0.00, 0, 0.00, 0, 0, 0.000, 59, 0.00,
 NOW(), NOW(), 'system', 'system');

-- This data represents various credit card account scenarios for testing:
-- 1. Normal utilization accounts
-- 2. High utilization accounts
-- 3. Delinquent accounts
-- 4. Secured cards
-- 5. Premium rewards cards
-- 6. Zero balance accounts
-- 7. Frozen accounts
-- 8. Closed accounts