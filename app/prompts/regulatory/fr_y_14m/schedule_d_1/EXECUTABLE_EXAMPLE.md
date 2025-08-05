# FR Y-14M Schedule D.1 Executable Data Profiling Rules - Complete Example

This example demonstrates the enhanced executable prompt that generates validation rules using exact column names and Python pandas logic.

## Input Example:

**Column Names from Uploaded File:**
```python
column_names = [
    'LOAN_ID', 'OUTSTANDING_BALANCE', 'PRINCIPAL_BALANCE', 'ACCRUED_INTEREST', 
    'ORIGINATION_DATE', 'MATURITY_DATE', 'DELINQ_STATUS', 'DAYS_PAST_DUE',
    'LOAN_PURPOSE', 'COLLATERAL_VALUE', 'LOAN_TO_VALUE', 'FICO_SCORE',
    'PAYMENT_AMOUNT', 'INTEREST_RATE', 'MONTHLY_PAYMENT', 'VIN_NUMBER'
]
```

**Attributes Batch (10 attributes max for token management):**
```python
attributes_batch = [
    "LOAN_ID (String): Unique identifier for the loan [Mandatory]",
    "OUTSTANDING_BALANCE (Decimal): Current outstanding principal balance [Mandatory]", 
    "DELINQ_STATUS (String): Current delinquency bucket [Mandatory]",
    "DAYS_PAST_DUE (Integer): Number of days past due [Optional]",
    "LOAN_PURPOSE (String): Purpose of the loan [Mandatory]"
]
```

## Enhanced Prompt Output:

```json
[
  {
    "attribute_id": "LOAN_ID",
    "rule_name": "LOAN_ID Uniqueness and Format Validation",
    "rule_type": "regulatory",
    "rule_category": "single_field",
    "required_columns": ["LOAN_ID"],
    "executable_logic": "(df['LOAN_ID'].notna()) & (df['LOAN_ID'].str.len().between(5, 50)) & (df['LOAN_ID'].str.match(r'^[A-Za-z0-9_-]+$')) & (~df['LOAN_ID'].duplicated(keep=False))",
    "expected_result": "PASS when loan ID is unique, 5-50 characters, alphanumeric with underscore/hyphen only",
    "null_handling": "NULL values fail validation - loan ID is mandatory",
    "edge_cases": ["Duplicate IDs", "Special characters", "Length violations", "NULL values"],
    "batch_dependency": "none",
    "severity": "critical",
    "regulatory_requirement": "FR Y-14M Schedule D.1 Unique Identification",
    "business_impact": "Duplicate loan IDs compromise data integrity and stress testing accuracy"
  },
  {
    "attribute_id": "OUTSTANDING_BALANCE",
    "rule_name": "Outstanding Balance Range and Component Reconciliation",
    "rule_type": "business_logic",
    "rule_category": "multi_field",
    "required_columns": ["OUTSTANDING_BALANCE", "PRINCIPAL_BALANCE", "ACCRUED_INTEREST"],
    "executable_logic": "(df['OUTSTANDING_BALANCE'].notna()) & (df['OUTSTANDING_BALANCE'] >= 0) & (df['OUTSTANDING_BALANCE'] <= 50000000) & (abs(df['OUTSTANDING_BALANCE'] - (df['PRINCIPAL_BALANCE'].fillna(0) + df['ACCRUED_INTEREST'].fillna(0))) <= 0.01)",
    "expected_result": "PASS when balance is positive, within $50M limit, and equals principal + interest within $0.01",
    "null_handling": "NULL outstanding balance fails validation, NULL components treated as zero",
    "edge_cases": ["Zero balances", "Very large amounts", "Penny rounding differences", "Component reconciliation"],
    "batch_dependency": "none",
    "severity": "critical",
    "regulatory_requirement": "FR Y-14M Schedule D.1 Balance Integrity",
    "business_impact": "Balance errors cascade to all EAD calculations and stress testing models"
  },
  {
    "attribute_id": "DELINQ_STATUS",
    "rule_name": "Delinquency Status and Days Past Due Alignment",
    "rule_type": "relationship",
    "rule_category": "multi_field",
    "required_columns": ["DELINQ_STATUS", "DAYS_PAST_DUE"],
    "executable_logic": "((df['DELINQ_STATUS'] == 'CURRENT') & (df['DAYS_PAST_DUE'].fillna(0) <= 29)) | ((df['DELINQ_STATUS'] == '30-59') & (df['DAYS_PAST_DUE'].between(30, 59, inclusive='both'))) | ((df['DELINQ_STATUS'] == '60-89') & (df['DAYS_PAST_DUE'].between(60, 89, inclusive='both'))) | ((df['DELINQ_STATUS'] == '90+') & (df['DAYS_PAST_DUE'] >= 90)) | ((df['DELINQ_STATUS'] == 'CHARGEOFF') & (df['DAYS_PAST_DUE'] >= 180))",
    "expected_result": "PASS when delinquency status aligns with days past due buckets per regulatory definitions",
    "null_handling": "NULL days_past_due treated as 0 for CURRENT status validation",
    "edge_cases": ["Boundary values (29/30, 59/60, 89/90)", "Charge-off timing", "NULL handling"],
    "batch_dependency": "none",
    "severity": "critical",
    "regulatory_requirement": "FR Y-14M Schedule D.1 Delinquency Classification",
    "business_impact": "Incorrect delinquency affects PD model calibration and loss forecasting"
  },
  {
    "attribute_id": "LOAN_PURPOSE",
    "rule_name": "Loan Purpose Code Validation and Schedule Exclusion",
    "rule_type": "regulatory",
    "rule_category": "single_field",
    "required_columns": ["LOAN_PURPOSE"],
    "executable_logic": "df['LOAN_PURPOSE'].isin(['AUTO', 'PERSONAL', 'STUDENT', 'BOAT_RV', 'OTHER_SECURED', 'LINE_OF_CREDIT']) & (~df['LOAN_PURPOSE'].isin(['MORTGAGE', 'HOME_EQUITY', 'CREDIT_CARD']))",
    "expected_result": "PASS when purpose is valid D.1 consumer loan type and excludes other schedules",
    "null_handling": "NULL purpose codes fail validation",
    "edge_cases": ["Invalid purpose codes", "Cross-schedule contamination", "Case sensitivity"],
    "batch_dependency": "none",
    "severity": "high",
    "regulatory_requirement": "FR Y-14M Schedule D.1 Purpose Classification",
    "business_impact": "Incorrect purpose affects portfolio segmentation and regulatory reporting accuracy"
  },
  {
    "attribute_id": "VIN_NUMBER",
    "rule_name": "VIN Completeness and Format for Auto Loans",
    "rule_type": "completeness",
    "rule_category": "multi_field",
    "required_columns": ["VIN_NUMBER", "LOAN_PURPOSE"],
    "executable_logic": "((df['LOAN_PURPOSE'] == 'AUTO') & (df['VIN_NUMBER'].notna()) & (df['VIN_NUMBER'].str.len() == 17) & (df['VIN_NUMBER'].str.match(r'^[A-HJ-NPR-Z0-9]{17}$'))) | (df['LOAN_PURPOSE'] != 'AUTO')",
    "expected_result": "PASS when auto loans have valid 17-character VIN excluding I,O,Q, non-auto loans exempt",
    "null_handling": "NULL VIN fails validation only for auto loans",
    "edge_cases": ["Non-auto loans exempt", "Invalid VIN characters", "Wrong length", "Check digit validation"],
    "batch_dependency": "none",
    "severity": "high",
    "regulatory_requirement": "FR Y-14M Schedule D.1 Auto Loan Collateral Identification",
    "business_impact": "VIN validation ensures proper collateral tracking and recovery assessment"
  }
]
```

## Python Execution Framework:

```python
import pandas as pd
import numpy as np
from typing import Dict, List, Any

def execute_data_profiling_rules(df: pd.DataFrame, rules: List[Dict]) -> Dict[str, Any]:
    """Execute all profiling rules against dataframe"""
    results = {
        'total_rules': len(rules),
        'passed_rules': 0,
        'failed_rules': 0,
        'rule_results': [],
        'summary': {}
    }
    
    for rule in rules:
        try:
            # Check if all required columns exist
            missing_cols = [col for col in rule['required_columns'] if col not in df.columns]
            if missing_cols:
                result = {
                    'rule_name': rule['rule_name'],
                    'attribute_id': rule['attribute_id'],
                    'status': 'FAILED',
                    'error': f"Missing columns: {missing_cols}",
                    'pass_rate': 0.0,
                    'severity': rule['severity']
                }
            else:
                # Execute the validation logic
                validation_result = eval(rule['executable_logic'])
                pass_count = validation_result.sum()
                total_count = len(df)
                pass_rate = (pass_count / total_count) * 100 if total_count > 0 else 0
                
                result = {
                    'rule_name': rule['rule_name'],
                    'attribute_id': rule['attribute_id'],
                    'status': 'PASSED' if pass_rate >= 95.0 else 'FAILED',
                    'pass_rate': round(pass_rate, 2),
                    'pass_count': int(pass_count),
                    'total_count': int(total_count),
                    'failed_count': int(total_count - pass_count),
                    'severity': rule['severity'],
                    'business_impact': rule['business_impact']
                }
                
            results['rule_results'].append(result)
            
            if result['status'] == 'PASSED':
                results['passed_rules'] += 1
            else:
                results['failed_rules'] += 1
                
        except Exception as e:
            result = {
                'rule_name': rule['rule_name'],
                'attribute_id': rule['attribute_id'],
                'status': 'ERROR',
                'error': str(e),
                'severity': rule['severity']
            }
            results['rule_results'].append(result)
            results['failed_rules'] += 1
    
    # Generate summary
    results['summary'] = {
        'overall_pass_rate': round((results['passed_rules'] / results['total_rules']) * 100, 2),
        'critical_failures': len([r for r in results['rule_results'] if r['severity'] == 'critical' and r['status'] != 'PASSED']),
        'high_failures': len([r for r in results['rule_results'] if r['severity'] == 'high' and r['status'] != 'PASSED']),
        'regulatory_compliance': 'PASS' if results['passed_rules'] == results['total_rules'] else 'FAIL'
    }
    
    return results

# Example usage:
# df = pd.read_csv('fr_y14m_d1_data.csv')
# rules = load_profiling_rules()  # Load from LLM response
# validation_results = execute_data_profiling_rules(df, rules)
# print(f"Overall compliance: {validation_results['summary']['regulatory_compliance']}")
```

## Key Enhancements in Executable Prompt:

### 1. **Exact Column Name Usage**
- Uses only columns from `${column_names}` provided from uploaded files
- No assumption or creation of column names
- Direct mapping to FR Y-14M technical specifications

### 2. **Executable Logic**
- Pandas operations that can run directly: `df['COLUMN'].method()`
- SQL-like conditions using pandas syntax
- Vectorized operations for performance

### 3. **Comprehensive Edge Case Handling**
- Division by zero: `(denominator != 0) & (calculation)` 
- NULL handling: `.fillna()`, `.notna()`, `.isna()`
- Boundary testing: `.between(lower, upper, inclusive='both')`
- Format validation: `.str.match()`, `.str.len()`

### 4. **Batching Support**
- Token-aware batching (max 10 attributes per batch)
- Cross-attribute dependency tracking
- Deferred execution for rules requiring additional columns

### 5. **Regulatory Precision**
- FR Y-14M Schedule D.1 specific validations
- Consumer loan focus (auto, student, personal, etc.)
- Proper exclusion of other schedules (mortgage, credit card)

This executable approach transforms LLM-generated rules into production-ready validation code that can run directly against FR Y-14M data files with exact column matching and comprehensive regulatory compliance validation.