# FR Y-14M Schedule D.1 Test Data - Intentional Anomalies

## Overview
The test dataset (`fr_y14m_schedule_d1_test_data.csv`) contains **269 intentional anomalies** across **1,000 records** (26.9% anomaly rate) designed to test data profiling detection capabilities.

## Anomaly Categories Injected

### 🚨 1. Regulatory Violations (46 anomalies)
**Critical compliance issues that must be detected**

#### Credit Score Range Violations (21 records, 2.1%)
- **Issue**: Credit scores outside valid FICO range (300-850)
- **Examples**: 851, 0, 999
- **Impact**: Regulatory reporting violations, risk model failures
- **Detection Rule**: `CREDIT_SCORE >= 300 AND CREDIT_SCORE <= 850`

#### Excessive APR Violations (17 records, 1.7%) 
- **Issue**: APR above reasonable/legal limits (>40%)
- **Examples**: 79.999%, 45.999%, 99.999%
- **Impact**: Usury law violations, regulatory scrutiny
- **Detection Rule**: `APR <= 36.0 OR (APR > 36.0 AND HIGH_APR_JUSTIFICATION IS NOT NULL)`

#### Negative Credit Limits (8 records, 0.8%)
- **Issue**: Credit limits below zero (mathematically impossible)
- **Examples**: -$2,500, -$1,200
- **Impact**: System calculation errors, balance reconciliation failures
- **Detection Rule**: `CREDIT_LIMIT >= 0`

### 💼 2. Business Logic Violations (168 anomalies)
**Inconsistencies that violate credit card business rules**

#### Severe Over-limit Accounts (56 records, 5.6%)
- **Issue**: Current balance > 200% of credit limit
- **Examples**: $15K balance on $5K limit
- **Impact**: Risk exposure underestimation, collection issues
- **Detection Rule**: `CURRENT_BALANCE <= CREDIT_LIMIT * 1.5 OR OVERLIMIT_FLAG = 'Y'`

#### Minimum Payment Violations (112 records, 11.2%)
- **Issue**: Minimum payment exceeds current balance
- **Examples**: $500 min payment on $200 balance
- **Impact**: CARD Act compliance violations, customer complaints
- **Detection Rule**: `MIN_PAYMENT_DUE <= CURRENT_BALANCE + FEES_AND_INTEREST`

### 📊 3. Data Format Violations (5 anomalies)
**Invalid data formats that break standard conventions**

#### Invalid State Codes (5 records, 0.5%)
- **Issue**: Non-standard US state abbreviations
- **Examples**: 'XX', 'ZZ', '99', null
- **Impact**: Geographic analysis failures, regulatory reporting errors
- **Detection Rule**: `STATE IN (valid_us_state_list)`

### 📈 4. Extreme Outliers (33 anomalies)
**Statistical outliers that indicate data quality issues**

#### Extreme Utilization Rates (29 records, 2.9%)
- **Issue**: Utilization > 400% (extreme over-limit scenarios)
- **Examples**: 561.4%, 710.2%, 779.2%
- **Impact**: Risk model distortion, capital calculation errors
- **Detection Rule**: `UTILIZATION_RATE <= 150.0 OR (UTILIZATION_RATE > 150.0 AND OVERLIMIT_EXPLANATION IS NOT NULL)`

#### Impossibly Old Accounts (4 records, 0.4%)
- **Issue**: Account age > 40 years (older than credit cards existed)
- **Examples**: 600+ months old
- **Impact**: Vintage analysis corruption, historical trend errors
- **Detection Rule**: `ACCOUNT_AGE_MONTHS <= 480` # 40 years max

### ❌ 5. Missing Mandatory Data (9 anomalies)
**Critical fields with null values that violate regulatory requirements**

#### Missing Reference Numbers (8 records, 0.8%)
- **Issue**: Primary key fields with null values
- **Impact**: Record identification failures, audit trail breaks
- **Detection Rule**: `REFERENCE_NUMBER IS NOT NULL AND LENGTH(REFERENCE_NUMBER) > 0`

#### Missing Credit Limits (1 record, 0.1%)
- **Issue**: Active accounts without defined credit limits
- **Impact**: Risk calculation impossible, utilization undefined
- **Detection Rule**: `(ACCOUNT_STATUS = 'ACTIVE' IMPLIES CREDIT_LIMIT IS NOT NULL)`

### 🔄 6. Duplicate Violations (8 anomalies)
**Referential integrity violations**

#### Duplicate Reference Numbers (8 records, 0.8%)
- **Issue**: Non-unique primary key values
- **Impact**: Data integrity violations, aggregation errors
- **Detection Rule**: `COUNT(REFERENCE_NUMBER) = 1 PER REPORTING_PERIOD`

## Data Quality Impact Assessment

### Critical Severity Issues (162 anomalies, 16.2%)
- Regulatory violations (46)
- Missing mandatory data (9) 
- Duplicate violations (8)
- Severe business logic violations (99)

### High Severity Issues (77 anomalies, 7.7%)
- Format violations (5)
- Extreme outliers (33)
- Moderate business logic violations (39)

### Medium Severity Issues (30 anomalies, 3.0%)
- Minor outliers and edge cases

## Expected Detection by Data Profiling

### ✅ Should Be Detected (High Confidence)
1. **Credit score range violations** - Clear min/max validation
2. **Negative credit limits** - Basic range check
3. **Invalid state codes** - Enumeration validation
4. **Missing mandatory fields** - Null checking
5. **Duplicate reference numbers** - Uniqueness validation

### ⚠️ Should Be Detected (Medium Confidence)  
1. **Excessive APR rates** - Requires regulatory knowledge
2. **Extreme utilization rates** - Statistical outlier detection
3. **Over-limit violations** - Cross-field validation
4. **Account age outliers** - Historical context needed

### 🤔 May Be Missed (Low Confidence)
1. **Minimum payment violations** - Complex CARD Act rules
2. **Temporal inconsistencies** - Date relationship logic
3. **Balance component reconciliation** - Multi-field calculations

## Testing Methodology

### Anomaly Injection Strategy
- **Realistic Distribution**: Anomalies follow real-world patterns
- **Severity Levels**: Mix of critical, high, and medium severity issues
- **Category Coverage**: All major data quality dimensions represented
- **Detection Difficulty**: Range from obvious to subtle violations

### Validation Approach
1. **Automated Detection**: Verify anomaly injection successful
2. **LLM Rule Generation**: Test if generated rules catch anomalies
3. **Coverage Assessment**: Measure detection rate by category
4. **False Positive Analysis**: Ensure clean data passes validation

## Success Criteria for Data Profiling

### Minimum Acceptable Performance
- **Critical Issues**: >90% detection rate
- **High Severity**: >70% detection rate  
- **Overall Coverage**: >80% of anomaly categories detected

### Excellent Performance
- **Critical Issues**: >95% detection rate
- **High Severity**: >85% detection rate
- **Overall Coverage**: >90% of anomaly categories detected
- **False Positive Rate**: <5%

## Real-World Relevance

These anomalies represent actual data quality issues encountered in:
- **Regulatory Submissions**: FR Y-14M, CCAR, stress testing
- **Risk Management**: Credit risk models, portfolio analytics  
- **Compliance Monitoring**: CARD Act, fair lending, capital requirements
- **Operational Systems**: Core banking, decision engines, reporting platforms

The data profiling system's ability to detect these anomalies directly correlates to its effectiveness in production regulatory environments.