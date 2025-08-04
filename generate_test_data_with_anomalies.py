#!/usr/bin/env python3
"""
Generate FR Y-14M Schedule D.1 Credit Card Test Data WITH INTENTIONAL ANOMALIES
Creates realistic data quality issues that data profiling should discover
"""
import csv
import random
import datetime
from pathlib import Path
from typing import Dict, List, Any
import string
import numpy as np

# Import the original attributes definition
from generate_test_data import FR_Y14M_D1_ATTRIBUTES, US_STATES, generate_random_id, generate_random_date

def inject_data_anomalies(records: List[Dict]) -> List[Dict]:
    """Inject realistic data quality anomalies that data profiling should catch"""
    
    print("🔧 Injecting intentional data anomalies for profiling discovery...")
    
    anomaly_count = 0
    
    for i, record in enumerate(records):
        # Inject different types of anomalies across the dataset
        
        # 1. REGULATORY VIOLATIONS (Critical to catch)
        
        # Credit scores outside valid range (300-850)
        if random.random() < 0.02:  # 2% of records
            if 'REFRESHED_CREDIT_BUREAU_SCORE' in record:
                record['REFRESHED_CREDIT_BUREAU_SCORE'] = random.choice([299, 851, 999, 0])
                anomaly_count += 1
        
        # APR above legal/realistic limits 
        if random.random() < 0.015:  # 1.5% of records
            if 'APR_AT_CYCLE_END' in record:
                record['APR_AT_CYCLE_END'] = random.choice([45.999, 79.999, 99.999])
                anomaly_count += 1
        
        # Negative credit limits (impossible)
        if random.random() < 0.008:  # 0.8% of records
            if 'CURRENT_CREDIT_LIMIT' in record:
                record['CURRENT_CREDIT_LIMIT'] = -random.uniform(100, 5000)
                anomaly_count += 1
        
        # 2. BUSINESS LOGIC VIOLATIONS
        
        # Current balance significantly exceeds credit limit (more than 200%)
        if random.random() < 0.025:  # 2.5% of records
            if 'CYCLE_ENDING_BALANCE' in record and 'CURRENT_CREDIT_LIMIT' in record:
                record['CYCLE_ENDING_BALANCE'] = record['CURRENT_CREDIT_LIMIT'] * random.uniform(2.5, 5.0)
                anomaly_count += 1
        
        # Minimum payment greater than total balance (impossible)
        if random.random() < 0.012:  # 1.2% of records
            if 'MINIMUM_PAYMENT_DUE' in record and 'CYCLE_ENDING_BALANCE' in record:
                record['MINIMUM_PAYMENT_DUE'] = record['CYCLE_ENDING_BALANCE'] * random.uniform(1.5, 3.0)
                anomaly_count += 1
        
        # Payment amount exceeds balance by large margin (suspicious)
        if random.random() < 0.018:  # 1.8% of records
            if 'ACTUAL_PAYMENT_AMOUNT' in record and 'CYCLE_ENDING_BALANCE' in record:
                record['ACTUAL_PAYMENT_AMOUNT'] = record['CYCLE_ENDING_BALANCE'] * random.uniform(5.0, 20.0)
                anomaly_count += 1
        
        # 3. TEMPORAL ANOMALIES
        
        # Account origination date in the future
        if random.random() < 0.005:  # 0.5% of records
            if 'ACCOUNT_ORIGINATION_DATE' in record:
                future_date = datetime.datetime.now() + datetime.timedelta(days=random.randint(30, 365))
                record['ACCOUNT_ORIGINATION_DATE'] = future_date.strftime('%Y%m%d')
                anomaly_count += 1
        
        # Payment due date in the past (more than 1 year ago)
        if random.random() < 0.01:  # 1% of records
            if 'NEXT_PAYMENT_DUE_DATE' in record:
                past_date = datetime.datetime.now() - datetime.timedelta(days=random.randint(365, 1000))
                record['NEXT_PAYMENT_DUE_DATE'] = past_date.strftime('%Y%m%d')
                anomaly_count += 1
        
        # 4. CONSISTENCY VIOLATIONS
        
        # Days past due doesn't match delinquency status
        if random.random() < 0.02:  # 2% of records
            if 'DAYS_PAST_DUE' in record:
                record['DAYS_PAST_DUE'] = random.randint(90, 180)
                # But keep past due amount at 0 (inconsistent)
                if 'TOTAL_PAST_DUE' in record:
                    record['TOTAL_PAST_DUE'] = 0.0
                anomaly_count += 1
        
        # Account status "CLOSED" but has current balance
        if random.random() < 0.008:  # 0.8% of records
            if 'MONTH_END_ACCOUNT_STATUS_ACTIVE_CLOSED' in record and 'CYCLE_ENDING_BALANCE' in record:
                record['MONTH_END_ACCOUNT_STATUS_ACTIVE_CLOSED'] = 2  # Closed
                record['CYCLE_ENDING_BALANCE'] = random.uniform(500, 5000)  # But has balance
                anomaly_count += 1
        
        # 5. DATA FORMAT VIOLATIONS
        
        # Invalid state codes
        if random.random() < 0.005:  # 0.5% of records
            if 'STATE' in record:
                record['STATE'] = random.choice(['XX', 'ZZ', '99', 'N/A', ''])
                anomaly_count += 1
        
        # ZIP codes with wrong length/format
        if random.random() < 0.008:  # 0.8% of records
            if 'ZIP_CODE' in record:
                record['ZIP_CODE'] = random.choice(['1234', '123456789012', 'ABCDE', '00000', ''])
                anomaly_count += 1
        
        # 6. OUTLIERS AND EXTREME VALUES
        
        # Extremely high utilization rates (over 500%)
        if random.random() < 0.015:  # 1.5% of records
            if 'UTILIZATION_RATE' in record:
                record['UTILIZATION_RATE'] = random.uniform(500.0, 999.999)
                anomaly_count += 1
        
        # Account age impossibly long (over 50 years)
        if random.random() < 0.003:  # 0.3% of records
            if 'ACCOUNT_AGE_MONTHS' in record:
                record['ACCOUNT_AGE_MONTHS'] = random.randint(600, 1000)
                anomaly_count += 1
        
        # Extremely low income at origination
        if random.random() < 0.01:  # 1% of records
            if 'BORROWER_INCOME_AT_ORIGINATION' in record:
                record['BORROWER_INCOME_AT_ORIGINATION'] = random.randint(1, 5000)  # Unrealistically low
                anomaly_count += 1
        
        # 7. MISSING MANDATORY DATA (NULL violations)
        
        # Missing reference number (critical identifier)
        if random.random() < 0.002:  # 0.2% of records
            if 'REFERENCE_NUMBER' in record:
                record['REFERENCE_NUMBER'] = None
                anomaly_count += 1
        
        # Missing current credit limit for active accounts
        if random.random() < 0.005:  # 0.5% of records
            if 'CURRENT_CREDIT_LIMIT' in record and record.get('MONTH_END_ACCOUNT_STATUS_ACTIVE_CLOSED') == 1:
                record['CURRENT_CREDIT_LIMIT'] = None
                anomaly_count += 1
        
        # 8. CARD ACT VIOLATIONS
        
        # Minimum payment below CARD Act requirements (should be at least 1% of balance + fees)
        if random.random() < 0.02:  # 2% of records
            if 'MINIMUM_PAYMENT_DUE' in record and 'CYCLE_ENDING_BALANCE' in record:
                if record['CYCLE_ENDING_BALANCE'] > 0:
                    # Set minimum payment unrealistically low (violates CARD Act)
                    record['MINIMUM_PAYMENT_DUE'] = random.uniform(1.0, 10.0)
                    anomaly_count += 1
        
        # 9. MATHEMATICAL INCONSISTENCIES
        
        # Balance components don't add up to current balance
        if random.random() < 0.015:  # 1.5% of records
            if all(field in record for field in ['CYCLE_ENDING_BALANCE', 'CASH_BALANCE_MIX', 'PROMOTIONAL_BALANCE_MIX']):
                # Make components not add up to total
                record['CASH_BALANCE_MIX'] = record['CYCLE_ENDING_BALANCE'] * 0.3
                record['PROMOTIONAL_BALANCE_MIX'] = record['CYCLE_ENDING_BALANCE'] * 0.8  # Intentionally wrong
                anomaly_count += 1
        
        # 10. DUPLICATE REFERENCE NUMBERS (should be unique)
        if i > 0 and random.random() < 0.003:  # 0.3% of records
            if 'REFERENCE_NUMBER' in record:
                # Copy reference number from previous record (create duplicate)
                record['REFERENCE_NUMBER'] = records[i-1]['REFERENCE_NUMBER']
                anomaly_count += 1
    
    print(f"✅ Injected {anomaly_count} intentional anomalies across {len(records)} records")
    print(f"   Anomaly rate: {(anomaly_count/len(records)*100):.2f}%")
    
    return records

def generate_batch_data_with_anomalies(batch_attrs: List[str], num_records: int, start_id: int) -> List[Dict]:
    """Generate data for a batch of attributes, then inject anomalies"""
    from generate_test_data import generate_batch_data
    
    # First generate clean data
    records = generate_batch_data(batch_attrs, num_records, start_id)
    
    # Then inject anomalies
    return inject_data_anomalies(records)

def generate_fr_y14m_test_data_with_anomalies():
    """Generate complete FR Y-14M Schedule D.1 test dataset with intentional anomalies"""
    print("🎯 Generating FR Y-14M Schedule D.1 Test Data WITH ANOMALIES")
    print("=" * 60)
    
    # Import the main generation logic but with anomaly injection
    from generate_test_data import create_attribute_batches
    
    # Verify we have exactly 118 attributes
    all_attributes = list(FR_Y14M_D1_ATTRIBUTES.keys())
    print(f"✅ Total attributes defined: {len(all_attributes)}")
    
    if len(all_attributes) != 118:
        print(f"❌ Expected 118 attributes, got {len(all_attributes)}")
        return False
    
    # Create batches for processing
    attribute_batches = create_attribute_batches(all_attributes, batch_size=30)
    print(f"✅ Created {len(attribute_batches)} attribute batches")
    
    # Generate data in batches
    num_records = 1000
    all_records = []
    
    print(f"\n🚀 Generating {num_records} records with intentional anomalies...")
    print("-" * 50)
    
    # Initialize records with empty dictionaries
    for i in range(num_records):
        all_records.append({})
    
    # Process each attribute batch (using clean generation first)
    for batch_idx, batch_attrs in enumerate(attribute_batches):
        print(f"Processing batch {batch_idx + 1}/{len(attribute_batches)}: {len(batch_attrs)} attributes")
        
        from generate_test_data import generate_batch_data
        batch_data = generate_batch_data(batch_attrs, num_records, 1)
        
        # Merge batch data into all records
        for i, record in enumerate(batch_data):
            all_records[i].update(record)
        
        print(f"  ✅ Generated clean data for attributes: {batch_attrs[:5]}{'...' if len(batch_attrs) > 5 else ''}")
    
    # Apply business rules first (from original logic)
    print(f"\n🔧 Applying business rules and consistency checks...")
    
    for record in all_records:
        # Ensure current balance <= credit limit (most cases)
        if record.get('CYCLE_ENDING_BALANCE') and record.get('CURRENT_CREDIT_LIMIT'):
            if random.random() < 0.85:  # 85% of accounts stay under limit
                record['CYCLE_ENDING_BALANCE'] = min(
                    record['CYCLE_ENDING_BALANCE'], 
                    record['CURRENT_CREDIT_LIMIT']
                )
        
        # Ensure minimum payment <= total payment due
        if record.get('MINIMUM_PAYMENT_DUE') and record.get('TOTAL_PAYMENT_DUE'):
            record['TOTAL_PAYMENT_DUE'] = max(
                record['TOTAL_PAYMENT_DUE'], 
                record['MINIMUM_PAYMENT_DUE']
            )
        
        # Calculate utilization rate
        if record.get('CYCLE_ENDING_BALANCE') and record.get('CURRENT_CREDIT_LIMIT'):
            if record['CURRENT_CREDIT_LIMIT'] > 0:
                util_rate = (record['CYCLE_ENDING_BALANCE'] / record['CURRENT_CREDIT_LIMIT']) * 100
                record['UTILIZATION_RATE'] = round(min(util_rate, 999.999), 3)
            else:
                record['UTILIZATION_RATE'] = 999.999  # Special code for zero limit
        
        # Ensure days past due consistency
        if record.get('DAYS_PAST_DUE', 0) > 0:
            record['TOTAL_PAST_DUE'] = max(record.get('TOTAL_PAST_DUE', 0), 
                                         record.get('MINIMUM_PAYMENT_DUE', 0))
    
    # NOW INJECT INTENTIONAL ANOMALIES
    print(f"\n🐛 Injecting intentional data quality anomalies...")
    all_records = inject_data_anomalies(all_records)
    
    # Write to CSV
    output_file = Path("tests/data/fr_y14m_schedule_d1_test_data_with_anomalies.csv")
    print(f"\n💾 Writing data with anomalies to {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = all_attributes
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(all_records)
    
    print(f"✅ Successfully generated {len(all_records)} records with anomalies")
    print(f"✅ File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Generate anomaly summary
    print(f"\n🐛 Anomaly Categories Injected:")
    print("-" * 35)
    print("1. ⚠️  Regulatory Violations:")
    print("   - Credit scores outside 300-850 range")
    print("   - APR above 45% (usury concerns)")
    print("   - Negative credit limits")
    
    print("2. 💼 Business Logic Violations:")
    print("   - Balance > 200% of credit limit")
    print("   - Minimum payment > current balance")
    print("   - Payment amount > 5x balance")
    
    print("3. 📅 Temporal Anomalies:")
    print("   - Future origination dates")
    print("   - Past due dates over 1 year old")
    
    print("4. 🔗 Consistency Violations:")
    print("   - High days past due but $0 past due amount")
    print("   - Closed accounts with current balances")
    
    print("5. 📊 Data Format Violations:")
    print("   - Invalid state codes (XX, ZZ, 99)")
    print("   - Malformed ZIP codes")
    
    print("6. 📈 Outliers and Extremes:")
    print("   - Utilization rates over 500%")
    print("   - Account age over 50 years")
    print("   - Income under $5,000")
    
    print("7. ❌ Missing Mandatory Data:")
    print("   - Null reference numbers")
    print("   - Missing credit limits for active accounts")
    
    print("8. ⚖️  CARD Act Violations:")
    print("   - Minimum payments below 1% requirement")
    
    print("9. 🧮 Mathematical Inconsistencies:")
    print("   - Balance components don't sum to total")
    
    print("10. 🔄 Duplicate Violations:")
    print("    - Duplicate reference numbers")
    
    # Sample data validation
    sample_record = all_records[0]
    print(f"\n📋 Sample Record (first 10 fields):")
    for i, (field, value) in enumerate(sample_record.items()):
        if i < 10:
            print(f"   {field}: {value}")
        else:
            break
    
    print(f"\n🎯 Data Profiling Testing Objectives:")
    print("=" * 45)
    print("The LLM-generated validation rules should detect:")
    print("✓ Regulatory compliance violations")
    print("✓ Business logic inconsistencies") 
    print("✓ Data format and range violations")
    print("✓ Temporal relationship anomalies")
    print("✓ Mathematical calculation errors")
    print("✓ Missing mandatory data")
    print("✓ Duplicate key violations")
    print("✓ Statistical outliers and extremes")
    
    return True

if __name__ == "__main__":
    success = generate_fr_y14m_test_data_with_anomalies()
    exit(0 if success else 1)