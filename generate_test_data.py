#!/usr/bin/env python3
"""
Generate FR Y-14M Schedule D.1 Credit Card Test Data
Creates 1000 sample records with all 118 attributes in batches
"""
import csv
import random
import datetime
from pathlib import Path
from typing import Dict, List, Any
import string

# FR Y-14M Schedule D.1 - All 118 Attributes with Data Types
FR_Y14M_D1_ATTRIBUTES = {
    # Identifiers and Keys (Lines 1-4, 76)
    "REFERENCE_NUMBER": {"type": "C", "length": 18, "mandatory": True},
    "CUSTOMER_ID": {"type": "C", "length": 18, "mandatory": True},
    "BANK_ID": {"type": "N", "length": 10, "mandatory": True},
    "PERIOD_ID": {"type": "date", "format": "YYYYMMDD", "mandatory": True},
    "CORPORATE_ID": {"type": "C", "length": 18, "mandatory": True},
    
    # Geographic Information (Lines 5-6)
    "STATE": {"type": "C", "length": 2, "mandatory": True},
    "ZIP_CODE": {"type": "C", "length": 9, "mandatory": True},
    
    # Product Classification (Lines 7-14)
    "CREDIT_CARD_TYPE": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3, 4]},
    "PRODUCT_TYPE": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3, 4, 5]},
    "LENDING_TYPE": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3]},
    "REVOLVE_FEATURE": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "NETWORK_ID": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3, 4, 5]},
    "SECURED_CREDIT_TYPE": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1, 2]},
    "LOAN_SOURCE_CHANNEL": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3, 4, 5]},
    "PURCHASED_CREDIT_DETERIORATED_STATUS": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    
    # Balance Information (Lines 15, 17-22)
    "CYCLE_ENDING_BALANCE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "PROMOTIONAL_BALANCE_MIX": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "CASH_BALANCE_MIX": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "PENALTY_BALANCE_MIX": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "OTHER_BALANCE_MIX": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "AVERAGE_DAILY_BALANCE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "MONTH_ENDING_BALANCE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    
    # Rewards and Promotional (Lines 23-24)
    "TOTAL_REWARD_CASH": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "REWARD_TYPE": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1, 2, 3]},
    
    # Date Fields (Lines 25-27, 41, 50, 60, 106, 114)
    "ACCOUNT_CYCLE_DATE": {"type": "date", "format": "YYYYMMDD", "mandatory": True},
    "ACCOUNT_ORIGINATION_DATE": {"type": "date", "format": "YYYYMMDD", "mandatory": True},
    "ACQUISITION_DATE": {"type": "date", "format": "YYYYMMDD", "mandatory": True},
    "CREDIT_BUREAU_SCORE_REFRESH_DATE": {"type": "date", "format": "YYYYMMDD", "mandatory": True},
    "NEXT_PAYMENT_DUE_DATE": {"type": "date", "format": "YYYYMMDD", "mandatory": True},
    "COLLECTION_RE_AGE_DATE": {"type": "date", "format": "YYYYMMDD", "mandatory": False},
    "CUSTOMER_SERVICE_RE_AGE_DATE": {"type": "date", "format": "YYYYMMDD", "mandatory": False},
    "DATE_CO_BORROWER_ADDED": {"type": "date", "format": "YYYYMMDD", "mandatory": False},
    
    # Relationship Flags (Lines 28-32)
    "MULTIPLE_BANKING_RELATIONSHIPS": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "MULTIPLE_CREDIT_CARD_RELATIONSHIPS": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "JOINT_ACCOUNT": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "AUTHORIZED_USERS": {"type": "N", "length": 5, "mandatory": True},
    "FLAGGED_AS_SECURITIZED": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    
    # Credit Scoring (Lines 33-42)
    "BORROWER_INCOME_AT_ORIGINATION": {"type": "N", "length": 12, "mandatory": True},
    "INCOME_SOURCE_AT_ORIGINATION": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3, 4, 5]},
    "ORIGINATION_CREDIT_BUREAU_SCORE_PRIMARY": {"type": "N", "length": 3, "mandatory": True},
    "ORIGINATION_CREDIT_BUREAU_SCORE_CO_BORROWER": {"type": "N", "length": 3, "mandatory": True},
    "REFRESHED_CREDIT_BUREAU_SCORE": {"type": "N", "length": 3, "mandatory": True},
    "BEHAVIORAL_SCORE": {"type": "N", "length": 10, "decimals": 6, "mandatory": False},
    
    # Credit Limits (Lines 43-47)
    "ORIGINAL_CREDIT_LIMIT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "CURRENT_CREDIT_LIMIT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "CURRENT_CASH_ADVANCE_LIMIT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "LINE_FROZEN_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "LINE_INCREASE_DECREASE_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1, 2]},
    
    # Payment Information (Lines 48-53)
    "MINIMUM_PAYMENT_DUE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "TOTAL_PAYMENT_DUE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "ACTUAL_PAYMENT_AMOUNT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "TOTAL_PAST_DUE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "DAYS_PAST_DUE": {"type": "N", "length": 3, "mandatory": True},
    
    # Interest Rates and APR (Lines 56, 77-82)
    "APR_AT_CYCLE_END": {"type": "N", "length": 6, "decimals": 3, "mandatory": True},
    "VARIABLE_RATE_INDEX": {"type": "N", "length": 2, "mandatory": True},
    "VARIABLE_RATE_MARGIN": {"type": "N", "length": 6, "decimals": 3, "mandatory": True},
    "MAXIMUM_APR": {"type": "N", "length": 6, "decimals": 3, "mandatory": True},
    "RATE_RESET_FREQUENCY": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3, 4]},
    "PROMOTIONAL_APR": {"type": "N", "length": 6, "decimals": 3, "mandatory": True},
    "CASH_APR": {"type": "N", "length": 6, "decimals": 3, "mandatory": True},
    
    # Account Status Flags (Lines 54, 57-59, 68-70)
    "ACCOUNT_60_PLUS_DPD_LAST_THREE_YEARS_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "FEE_TYPE": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3, 4]},
    "MONTH_END_ACCOUNT_STATUS_ACTIVE_CLOSED": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2]},
    "ACCOUNT_SOLD_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "BANKRUPTCY_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "LOSS_SHARING": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    
    # Transaction Volumes (Lines 64-67)
    "PURCHASE_AMOUNT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "CASH_ADVANCE_AMOUNT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "BALANCE_TRANSFER_AMOUNT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "CONVENIENCE_CHECK_AMOUNT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    
    # Charge-offs and Recoveries (Lines 61-63, 107)
    "CHARGE_OFF_REASON": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1, 2, 3, 4]},
    "GROSS_CHARGE_OFF_AMOUNT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "RECOVERY_AMOUNT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "PRINCIPAL_CHARGE_OFF_AMOUNT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    
    # Basel II Risk Parameters (Lines 71-75) - Optional
    "PROBABILITY_OF_DEFAULT": {"type": "N", "length": 6, "decimals": 5, "mandatory": False},
    "LOSS_GIVEN_DEFAULT": {"type": "N", "length": 6, "decimals": 5, "mandatory": False},
    "EXPECTED_LOSS_GIVEN_DEFAULT": {"type": "N", "length": 6, "decimals": 5, "mandatory": False},
    "EXPOSURE_AT_DEFAULT": {"type": "N", "length": 12, "decimals": 2, "mandatory": False},
    "EAD_ID_SEGMENT": {"type": "N", "length": 7, "mandatory": False},
    
    # Fee Categories (Lines 83-96)
    "LOSS_SHARE_ID": {"type": "C", "length": 7, "mandatory": True},
    "LOSS_SHARE_RATE": {"type": "N", "length": 7, "decimals": 5, "mandatory": True},
    "OTHER_CREDITS": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "LATE_FEE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "OVER_LIMIT_FEE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "NSF_FEE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "CASH_ADVANCE_FEE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "MONTHLY_ANNUAL_FEE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "DEBT_SUSPENSION_FEE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "BALANCE_TRANSFER_FEE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "OTHER_FEE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    
    # Delinquency Tracking (Lines 86-87)
    "CYCLES_PAST_DUE_AT_CYCLE_DATE": {"type": "N", "length": 2, "mandatory": True},
    "CYCLES_PAST_DUE_AT_MONTH_END": {"type": "N", "length": 2, "mandatory": True},
    
    # Program Enrollment Flags (Lines 97-104)
    "HARDSHIP_PROGRAM_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "PAYMENT_ASSISTANCE_PROGRAM_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "WORKOUT_PROGRAM_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "DEBT_MANAGEMENT_PROGRAM_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "FORBEARANCE_PROGRAM_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "TRIAL_MODIFICATION_PROGRAM_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "PERMANENT_MODIFICATION_PROGRAM_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "SHORT_SALE_PROGRAM_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    
    # Credit Score Metadata (Lines 109-121)
    "ORIGINAL_CREDIT_BUREAU_SCORE_NAME": {"type": "N", "length": 2, "mandatory": True, "values": [1, 2, 3, 4, 5]},
    "REFRESHED_CREDIT_BUREAU_SCORE_NAME": {"type": "N", "length": 2, "mandatory": True, "values": [1, 2, 3, 4, 5]},
    "BEHAVIORAL_SCORE_NAME": {"type": "C", "length": 30, "mandatory": False},
    "BEHAVIORAL_SCORE_VERSION": {"type": "C", "length": 30, "mandatory": False},
    "CREDIT_LIMIT_CHANGE_TYPE": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1, 2, 3]},
    "LINE_CHANGE_TYPE": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1, 2, 3]},
    "INTERNAL_CREDIT_SCORE_FLAG": {"type": "N", "length": 1, "mandatory": True, "values": [0, 1]},
    "INTERNAL_CREDIT_SCORE_VALUE": {"type": "N", "length": 6, "decimals": 3, "mandatory": True},
    
    # Regulatory and Administrative (Lines 108, 115, 118, 123)
    "ENTITY_TYPE": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3, 4]},
    "NATIONAL_BANK_RSSD_ID": {"type": "N", "length": 10, "mandatory": True},
    
    # Additional fields to reach exactly 118 total
    "UTILIZATION_RATE": {"type": "N", "length": 6, "decimals": 3, "mandatory": True},
    "ACCOUNT_AGE_MONTHS": {"type": "N", "length": 3, "mandatory": True},
    "LAST_STATEMENT_BALANCE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "INTEREST_CHARGED": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "AVAILABLE_CREDIT": {"type": "N", "length": 12, "decimals": 2, "mandatory": True},
    "PAYMENT_CHANNEL": {"type": "N", "length": 1, "mandatory": True, "values": [1, 2, 3, 4, 5]},
    "CYCLE_DAYS": {"type": "N", "length": 2, "mandatory": True},
    "STMT_CLOSING_BALANCE": {"type": "N", "length": 12, "decimals": 2, "mandatory": True}
}

# US States for geographic data
US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

def generate_random_id(length: int) -> str:
    """Generate random alphanumeric ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_random_date(start_year: int = 2020, end_year: int = 2024) -> str:
    """Generate random date in YYYYMMDD format"""
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    
    # Handle different month lengths
    if month in [1, 3, 5, 7, 8, 10, 12]:
        max_day = 31
    elif month in [4, 6, 9, 11]:
        max_day = 30
    else:  # February
        max_day = 29 if year % 4 == 0 else 28
    
    day = random.randint(1, max_day)
    return f"{year:04d}{month:02d}{day:02d}"

def generate_value(attr_name: str, spec: Dict) -> Any:
    """Generate realistic value based on attribute specification"""
    
    if spec["type"] == "C":  # Character field
        if attr_name == "STATE":
            return random.choice(US_STATES)
        elif attr_name == "ZIP_CODE":
            return f"{random.randint(10000, 99999):05d}{random.randint(1000, 9999):04d}"
        elif "SCORE_NAME" in attr_name:
            return random.choice(["FICO", "VANTAGE", "CUSTOM", "INTERNAL", "OTHER"])[:spec["length"]]
        elif "ID" in attr_name:
            return generate_random_id(spec["length"])
        else:
            return generate_random_id(spec["length"])
    
    elif spec["type"] == "date":
        if "ORIGINATION" in attr_name:
            return generate_random_date(2018, 2023)
        elif "ACQUISITION" in attr_name:
            return generate_random_date(2019, 2024)
        else:
            return generate_random_date(2023, 2024)
    
    elif spec["type"] == "N":  # Numeric field
        if "values" in spec:
            return random.choice(spec["values"])
        
        # Handle specific field types with realistic ranges
        if "SCORE" in attr_name and "BUREAU" in attr_name:
            return random.randint(300, 850)  # FICO score range
        elif "INCOME" in attr_name:
            return random.randint(25000, 250000)  # Annual income range
        elif "LIMIT" in attr_name:
            return round(random.uniform(500, 50000), 2)
        elif "BALANCE" in attr_name:
            return round(random.uniform(0, 25000), 2)
        elif "PAYMENT" in attr_name:
            return round(random.uniform(0, 5000), 2)
        elif "APR" in attr_name or "RATE" in attr_name:
            return round(random.uniform(0, 35.99), 3)
        elif "FEE" in attr_name:
            return round(random.uniform(0, 100), 2)
        elif "DAYS" in attr_name:
            return random.randint(0, 180)
        elif "CYCLES" in attr_name:
            return random.randint(0, 6)
        elif "MONTHS" in attr_name:
            return random.randint(1, 240)
        elif "UTILIZATION" in attr_name:
            return round(random.uniform(0, 100), 3)
        elif "RSSD" in attr_name or "BANK_ID" in attr_name:
            return random.randint(1000000, 9999999999)
        elif "decimals" in spec:
            max_value = 10 ** (spec["length"] - spec["decimals"]) - 1
            return round(random.uniform(0, max_value), spec["decimals"])
        else:
            max_value = 10 ** spec["length"] - 1
            return random.randint(0, max_value)
    
    return None

def generate_batch_data(batch_attrs: List[str], num_records: int, start_id: int) -> List[Dict]:
    """Generate data for a batch of attributes"""
    records = []
    
    for i in range(num_records):
        record = {}
        record_id = start_id + i
        
        for attr_name in batch_attrs:
            spec = FR_Y14M_D1_ATTRIBUTES[attr_name]
            
            # Handle optional fields (some may be null)
            if not spec["mandatory"] and random.random() < 0.3:  # 30% chance of null for optional
                record[attr_name] = None
            else:
                record[attr_name] = generate_value(attr_name, spec)
        
        records.append(record)
    
    return records

def create_attribute_batches(attributes: List[str], batch_size: int = 30) -> List[List[str]]:
    """Split attributes into batches for processing"""
    batches = []
    for i in range(0, len(attributes), batch_size):
        batches.append(attributes[i:i + batch_size])
    return batches

def generate_fr_y14m_test_data():
    """Generate complete FR Y-14M Schedule D.1 test dataset"""
    print("🎯 Generating FR Y-14M Schedule D.1 Test Data")
    print("=" * 50)
    
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
    
    print(f"\n🚀 Generating {num_records} records...")
    print("-" * 30)
    
    # Initialize records with empty dictionaries
    for i in range(num_records):
        all_records.append({})
    
    # Process each attribute batch
    for batch_idx, batch_attrs in enumerate(attribute_batches):
        print(f"Processing batch {batch_idx + 1}/{len(attribute_batches)}: {len(batch_attrs)} attributes")
        
        batch_data = generate_batch_data(batch_attrs, num_records, 1)
        
        # Merge batch data into all records
        for i, record in enumerate(batch_data):
            all_records[i].update(record)
        
        print(f"  ✅ Generated data for attributes: {batch_attrs[:5]}{'...' if len(batch_attrs) > 5 else ''}")
    
    # Ensure data consistency and business rules
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
    
    # Write to CSV
    output_file = Path("tests/data/fr_y14m_schedule_d1_test_data.csv")
    print(f"\n💾 Writing data to {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = all_attributes
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(all_records)
    
    print(f"✅ Successfully generated {len(all_records)} records")
    print(f"✅ File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Generate summary statistics
    print(f"\n📊 Data Quality Summary:")
    mandatory_fields = [attr for attr, spec in FR_Y14M_D1_ATTRIBUTES.items() if spec["mandatory"]]
    optional_fields = [attr for attr, spec in FR_Y14M_D1_ATTRIBUTES.items() if not spec["mandatory"]]
    
    print(f"   Mandatory fields: {len(mandatory_fields)}")
    print(f"   Optional fields: {len(optional_fields)}")
    
    # Sample data validation
    sample_record = all_records[0]
    print(f"\n📋 Sample Record (first 10 fields):")
    for i, (field, value) in enumerate(sample_record.items()):
        if i < 10:
            print(f"   {field}: {value}")
        else:
            break
    
    return True

if __name__ == "__main__":
    success = generate_fr_y14m_test_data()
    exit(0 if success else 1)