# FR Y-14M Schedule D.1 Data Loading Guide

This guide explains how to create and populate the `fry14m_scheduled1_data` table with test data.

## Overview

The FR Y-14M Schedule D.1 table contains 118 columns of credit card loan-level data for regulatory reporting purposes.

## Files Created

1. **Migration Script**: `alembic/versions/add_fry14m_scheduled1_data_table.py`
   - Creates the `fry14m_scheduled1_data` table with all 118 columns
   - Includes proper data types based on the data characteristics
   - Adds indexes for common query patterns

2. **Data Loading Script**: `scripts/fry14m_data/load_fry14m_scheduled1_data.py`
   - Reads data from `tests/data/fr_y14m_schedule_d1_test_data_with_anomalies.csv`
   - Handles data type conversions (dates, decimals, integers)
   - Loads data in batches for efficiency
   - Includes comprehensive error handling

3. **Migration Runner**: `scripts/fry14m_data/apply_fry14m_migration.py`
   - Simple script to run the Alembic migration

## Steps to Load Data

### 1. Run the Database Migration

```bash
# Option 1: Using the helper script
python scripts/fry14m_data/apply_fry14m_migration.py

# Option 2: Using Alembic directly
alembic upgrade head
```

### 2. Load the Data

```bash
python scripts/fry14m_data/load_fry14m_scheduled1_data.py
```

## Table Structure

The table includes the following column categories:

- **Identification**: reference_number, customer_id, bank_id, period_id, etc.
- **Product Information**: credit_card_type, product_type, lending_type, etc.
- **Balance Data**: Various balance fields (cycle_ending_balance, promotional_balance_mix, etc.)
- **Date Fields**: Account dates (origination, cycle, payment due dates, etc.)
- **Credit Information**: Credit scores, limits, utilization rates
- **Payment Data**: Payment amounts, past due information
- **Rate Information**: APRs, margins, promotional rates
- **Risk Metrics**: Probability of default, loss given default, etc.
- **Fee Information**: Various fee types and amounts
- **Program Flags**: Various assistance and modification program indicators

## Data Types Used

- **VARCHAR**: For IDs, references, and text fields
- **NUMERIC(20,2)**: For monetary amounts and balances
- **NUMERIC(10,3-6)**: For rates and percentages
- **INTEGER**: For flags, counts, and score values
- **DATE**: For all date fields
- **DATETIME**: For audit fields (created_at, updated_at)

## Verification

After loading, you can verify the data with:

```sql
-- Check record count
SELECT COUNT(*) FROM fry14m_scheduled1_data;

-- Sample first few records
SELECT * FROM fry14m_scheduled1_data LIMIT 5;

-- Check data by period
SELECT period_id, COUNT(*) 
FROM fry14m_scheduled1_data 
GROUP BY period_id;
```

## Notes

- The CSV file contains test data with potential anomalies for testing purposes
- All 118 columns from the FR Y-14M Schedule D.1 specification are included
- Date fields are parsed from YYYYMMDD format
- Numeric fields handle large values with appropriate precision
- The script includes proper error handling and logging