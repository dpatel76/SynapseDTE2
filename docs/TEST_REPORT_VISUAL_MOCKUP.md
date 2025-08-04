# Test Report Visual Mockup & Section Templates

## Executive Summary Page Mockup

```
================================================================================
                              COMPREHENSIVE TEST REPORT
                             FR Y-14M Schedule D.1
                            Commercial Real Estate Loans
                           Test Cycle 2 - DGO Q3 2025
================================================================================

EXECUTIVE SUMMARY

┌─ PLAIN ENGLISH EXPLANATION ──────────────────────────────────────────────────┐
│                                                                              │
│ This report documents the testing of Wells Fargo's FR Y-14M Schedule D.1    │
│ submission to the Federal Reserve. This monthly report provides loan-level  │
│ details for every commercial real estate loan over $1 million. The Fed uses │
│ this data to stress test our portfolio and determine if we have enough      │
│ capital to survive a severe recession.                                       │
│                                                                              │
│ Why This Matters: Errors in this report could lead to incorrect capital     │
│ requirements, regulatory penalties, or restrictions on dividends and share  │
│ buybacks.                                                                    │
└──────────────────────────────────────────────────────────────────────────────┘

KEY STAKEHOLDERS
┌─────────────────────────────┬─────────────────────┬─────────────────────────┐
│ Role                        │ Name                │ Responsibility          │
├─────────────────────────────┼─────────────────────┼─────────────────────────┤
│ Report Owner               │ Mike Johnson        │ Overall report accuracy │
│ Lead Tester                │ Test User           │ Test execution          │
│ Data Provider (GBM)        │ Lisa Chen           │ Source data quality     │
│ Data Executive             │ David Brown         │ Data governance         │
└─────────────────────────────┴─────────────────────┴─────────────────────────┘

┌─ TESTING SCORECARD ───────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────┐│
│   │      118       │  │       1        │  │     0.88%      │  │    HIGH    ││
│   │ Total Attrs    │  │ Attrs Tested   │  │   Coverage     │  │    Risk    ││
│   └────────────────┘  └────────────────┘  └────────────────┘  └────────────┘│
│                                                                              │
│   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────┐│
│   │       4        │  │       2        │  │      100%      │  │     0      ││
│   │ Test Cases     │  │    Passed      │  │   Pass Rate    │  │   Issues   ││
│   └────────────────┘  └────────────────┘  └────────────────┘  └────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘

┌─ ⚠️ CRITICAL RISK ASSESSMENT ─────────────────────────────────────────────────┐
│                                                                              │
│ FINDING: Testing only 0.88% of report attributes provides virtually no       │
│ assurance about report accuracy.                                             │
│                                                                              │
│ RISKS IDENTIFIED:                                                            │
│ • 113 of 114 testable attributes have ZERO testing                         │
│ • Unknown if the 1 Critical Data Element was tested                        │
│ • No statistical validity with only 4 samples from thousands of loans      │
│ • High probability of undetected errors in production reports               │
│                                                                              │
│ REQUIRED ACTIONS:                                                            │
│ 1. Immediately expand testing to cover all CDEs and high-risk attributes   │
│ 2. Increase sample size to achieve statistical confidence                   │
│ 3. Implement automated testing for future cycles                           │
│ 4. Executive review of risk acceptance if minimal testing continues         │
└──────────────────────────────────────────────────────────────────────────────┘

Page 1 of 12                    CONFIDENTIAL - INTERNAL USE ONLY
================================================================================
```

## Planning Phase Page Mockup

```
================================================================================
PLANNING PHASE RESULTS                                                    Page 2

┌─ WHAT ACTUALLY HAPPENED ──────────────────────────────────────────────────────┐
│                                                                              │
│ During the planning phase, we catalogued all 118 data attributes that make  │
│ up the FR Y-14M Schedule D.1 report. This involved:                        │
│                                                                              │
│ • Reviewing the Federal Reserve's technical specifications                   │
│ • Mapping each attribute to source systems and data owners                  │
│ • Identifying which attributes are critical for calculations (CDEs)         │
│ • Flagging attributes with known data quality issues                        │
│                                                                              │
│ KEY INSIGHT: With only 1 CDE out of 118 attributes (0.8%), this report     │
│ is primarily a data collection exercise rather than a calculation-intensive │
│ submission. Most fields simply pass through loan characteristics.           │
└──────────────────────────────────────────────────────────────────────────────┘

PLANNING METRICS
┌─────────────────────────────┬────────────┬─────────────────────────────────┐
│ Metric                      │ Count      │ Percentage of Total             │
├─────────────────────────────┼────────────┼─────────────────────────────────┤
│ Total Attributes           │ 118        │ 100.0%                          │
│ Critical Data Elements     │ 1          │ 0.8%                            │
│ Primary Keys              │ 4          │ 3.4%                            │
│ Attributes with Issues    │ 1          │ 0.8%                            │
│ Standard Attributes       │ 112        │ 94.9%                           │
├─────────────────────────────┼────────────┼─────────────────────────────────┤
│ Approved for Testing      │ 118        │ 100.0%                          │
│ Rejected                  │ 0          │ 0.0%                            │
└─────────────────────────────┴────────────┴─────────────────────────────────┘

ATTRIBUTE INVENTORY (Sorted by Type, then Line Number)
┌──────┬─────────────────────────────────┬──────┬─────┬───────┬─────────────┐
│ Line │ Attribute Name                  │ Type │ PK  │ CDE   │ Status      │
├──────┼─────────────────────────────────┼──────┼─────┼───────┼─────────────┤
│ 1    │ Reference Number                │ Text │ ✓   │       │ Approved    │
│ 3    │ Legal Entity Identifier         │ Text │ ✓   │       │ Approved    │
│ 8    │ Loan ID                        │ Text │ ✓   │       │ Approved    │
│ 24   │ Reporting Date                 │ Date │ ✓   │       │ Approved    │
├──────┼─────────────────────────────────┼──────┼─────┼───────┼─────────────┤
│ 45   │ Current Credit Limit           │ Num  │     │ ✓     │ Approved    │
├──────┼─────────────────────────────────┼──────┼─────┼───────┼─────────────┤
│ 67   │ Past Due Amount               │ Num  │     │       │ Approved ⚠️  │
├──────┼─────────────────────────────────┼──────┼─────┼───────┼─────────────┤
│ 2    │ Obligor Name                   │ Text │     │       │ Approved    │
│ 4    │ Property Type                  │ Code │     │       │ Approved    │
│ 5    │ Property Location              │ Text │     │       │ Approved    │
│ ...  │ [Additional 108 attributes]    │ ...  │     │       │ ...         │
└──────┴─────────────────────────────────┴──────┴─────┴───────┴─────────────┘

VERSION HISTORY
┌────────┬────────────┬──────────────┬──────────┬─────────────┬──────────────┐
│ Version│ Date       │ Submitted By │ Status   │ Approved By │ Comments     │
├────────┼────────────┼──────────────┼──────────┼─────────────┼──────────────┤
│ v1     │ 2025-07-15 │ Test User    │ Approved │ Mike Johnson│ All attrs OK │
└────────┴────────────┴──────────────┴──────────┴─────────────┴──────────────┘

Page 2 of 12                    CONFIDENTIAL - INTERNAL USE ONLY
================================================================================
```

## Data Profiling Phase Page Mockup

```
================================================================================
DATA PROFILING PHASE RESULTS                                              Page 3

┌─ WHAT ACTUALLY HAPPENED ──────────────────────────────────────────────────────┐
│                                                                              │
│ We used AI to generate 385 data quality rules - about 3 rules per attribute.│
│ However, the approval process was extremely selective:                       │
│                                                                              │
│ • Generated: 385 rules (100%)                                               │
│ • Submitted: 385 rules                                                      │
│ • Approved: 21 rules (5.5%)                                                │
│ • Rejected: 364 rules (94.5%)                                              │
│                                                                              │
│ CONCERN: The 94.5% rejection rate suggests either overly restrictive        │
│ approval criteria or a decision to minimize profiling efforts. This leaves  │
│ most attributes without any data quality validation.                        │
└──────────────────────────────────────────────────────────────────────────────┘

DATA PROFILING METRICS
┌───────────────────────────┬─────────┬──────────┬────────────────────────────┐
│ Metric                    │ Count   │ Percent  │ Implication                │
├───────────────────────────┼─────────┼──────────┼────────────────────────────┤
│ Rules Generated          │ 385     │ 100.0%   │ Comprehensive coverage     │
│ Rules Approved           │ 21      │ 5.5%     │ Minimal validation         │
│ Rules Executed           │ 21      │ 100.0%   │ All approved rules ran     │
│ Rules Passed             │ 21      │ 100.0%   │ No data quality issues     │
│ Attributes with Rules    │ 7       │ 5.9%     │ 111 attrs unchecked       │
└───────────────────────────┴─────────┴──────────┴────────────────────────────┘

APPROVED RULES DETAIL
┌────┬──────────────────────┬────────────────────────┬─────────┬────────────┐
│ ID │ Attribute           │ Rule Description       │ Result  │ Records    │
├────┼──────────────────────┼────────────────────────┼─────────┼────────────┤
│ 1  │ Reference Number    │ Not Null Check         │ PASS ✓  │ 1,001/1,001│
│ 2  │ Reference Number    │ Unique Check           │ PASS ✓  │ 1,001/1,001│
│ 3  │ Reference Number    │ Format Check (Regex)   │ PASS ✓  │ 1,001/1,001│
│ 4  │ Current Credit Limit│ Range Check (0-10B)    │ PASS ✓  │ 1,001/1,001│
│ 5  │ Current Credit Limit│ Decimal Precision      │ PASS ✓  │ 1,001/1,001│
│ 6  │ Loan ID            │ Not Null Check         │ PASS ✓  │ 1,001/1,001│
│ 7  │ Loan ID            │ Format Check           │ PASS ✓  │ 1,001/1,001│
│... │ [14 more rules]     │                        │         │            │
└────┴──────────────────────┴────────────────────────┴─────────┴────────────┘

REJECTED RULES SUMMARY (Top Categories)
┌─────────────────────────────┬─────────┬──────────────────────────────────────┐
│ Rejection Reason           │ Count   │ Example Rules                        │
├─────────────────────────────┼─────────┼──────────────────────────────────────┤
│ Too Computationally Expensive│ 89     │ Cross-table validations              │
│ Redundant with Other Rules  │ 76     │ Multiple null checks on same field   │
│ Not Applicable to Data Type │ 65     │ Numeric checks on text fields        │
│ Requires External Data      │ 54     │ Address validation against USPS      │
│ Low Priority               │ 45     │ Format checks on optional fields     │
│ Other                      │ 35     │ Various                              │
└─────────────────────────────┴─────────┴──────────────────────────────────────┘

VERSION HISTORY
┌────────┬────────────┬──────────────┬──────────┬─────────────┬──────────────┐
│ Version│ Date       │ Submitted By │ Status   │ Reviewed By │ Comments     │
├────────┼────────────┼──────────────┼──────────┼─────────────┼──────────────┤
│ v1     │ 2025-07-20 │ Test User    │ Rejected │ Mike Johnson│ Too many rules│
│ v2     │ 2025-07-21 │ Test User    │ Approved │ Mike Johnson│ 21 critical  │
└────────┴────────────┴──────────────┴──────────┴─────────────┴──────────────┘

Page 3 of 12                    CONFIDENTIAL - INTERNAL USE ONLY
================================================================================
```

## Scoping Phase Page Mockup

```
================================================================================
SCOPING PHASE RESULTS                                                     Page 4

┌─ WHAT ACTUALLY HAPPENED ──────────────────────────────────────────────────────┐
│                                                                              │
│ The scoping phase revealed an extremely conservative testing approach:       │
│                                                                              │
│ • Started with: 114 testable attributes (excluding 4 Primary Keys)          │
│ • Selected: 5 attributes (4.4% coverage)                                    │
│ • Approved: 1 attribute (0.88% final coverage)                              │
│                                                                              │
│ CRITICAL ISSUE: The approved attribute may not even be the Critical Data    │
│ Element. With 99.12% of attributes untested, we have virtually no assurance │
│ about data quality or regulatory compliance.                                 │
└──────────────────────────────────────────────────────────────────────────────┘

SCOPING DECISION MATRIX
┌─────────────────────────────┬────────┬──────────┬─────────────────────────┐
│ Scoping Criteria           │ Count  │ Percent  │ Decision Impact         │
├─────────────────────────────┼────────┼──────────┼─────────────────────────┤
│ Total Attributes           │ 118    │ 100.0%   │ Starting universe       │
│ Less: Primary Keys         │ (4)    │ 3.4%     │ Not testable           │
│ Testable Attributes        │ 114    │ 96.6%    │ Available for testing  │
│ Initially Selected         │ 5      │ 4.4%     │ Risk-based selection   │
│ Final Approved             │ 1      │ 0.88%    │ Actual test coverage   │
│ Not Tested                 │ 113    │ 99.12%   │ Coverage gap           │
└─────────────────────────────┴────────┴──────────┴─────────────────────────┘

SELECTED ATTRIBUTES DETAIL
┌──────┬─────────────────────────────┬──────────┬─────────┬─────────────────┐
│ Line │ Attribute Name              │ Type     │ Status  │ Selection Reason│
├──────┼─────────────────────────────┼──────────┼─────────┼─────────────────┤
│ 45   │ Current Credit Limit        │ CDE      │ APPROVED│ Critical element│
│ 67   │ Past Due Amount            │ Issue    │ Rejected│ Known issues    │
│ 23   │ Property Value             │ High Risk│ Rejected│ Material amount │
│ 89   │ Interest Rate              │ High Risk│ Rejected│ Calculation base│
│ 102  │ Maturity Date              │ Required │ Rejected│ Regulatory req  │
└──────┴─────────────────────────────┴──────────┴─────────┴─────────────────┘

REJECTION ANALYSIS
┌─────────────────────────────┬─────────────────────────────────────────────┐
│ Rejected Attribute         │ Rejection Rationale & Risk                  │
├─────────────────────────────┼─────────────────────────────────────────────┤
│ Past Due Amount           │ "Historical issues resolved" - HIGH RISK    │
│ Property Value            │ "Validated at source" - MEDIUM RISK         │
│ Interest Rate             │ "System calculated" - MEDIUM RISK           │
│ Maturity Date             │ "Static data" - LOW RISK                    │
└─────────────────────────────┴─────────────────────────────────────────────┘

ATTRIBUTES NOT SELECTED (Highest Risk)
┌──────┬─────────────────────────────┬──────────┬──────────────────────────┐
│ Line │ Attribute Name              │ Risk     │ Why This Matters         │
├──────┼─────────────────────────────┼──────────┼──────────────────────────┤
│ 34   │ Loan Balance               │ HIGH     │ Direct capital impact    │
│ 56   │ Risk Rating                │ HIGH     │ Drives reserves          │
│ 78   │ Collateral Value           │ HIGH     │ LTV calculations         │
│ 91   │ Payment Status             │ MEDIUM   │ Delinquency reporting    │
│ ...  │ [109 more untested]        │ VARIOUS  │ Multiple impacts         │
└──────┴─────────────────────────────┴──────────┴──────────────────────────┘

VERSION HISTORY
┌────────┬────────────┬──────────────┬──────────┬─────────────┬──────────────┐
│ Version│ Date       │ Submitted By │ Status   │ Reviewed By │ Comments     │
├────────┼────────────┼──────────────┼──────────┼─────────────┼──────────────┤
│ v1     │ 2025-07-22 │ Test User    │ Rejected │ Mike Johnson│ Too many attrs│
│ v2     │ 2025-07-23 │ Test User    │ Partial  │ Mike Johnson│ Approve 1 only│
└────────┴────────────┴──────────────┴──────────┴─────────────┴──────────────┘

Page 4 of 12                    CONFIDENTIAL - INTERNAL USE ONLY
================================================================================
```

## Key Design Elements Demonstrated

### 1. **Clear Visual Hierarchy**
- Section headers are prominent and consistent
- Information flows from high-level to detailed
- Related information is grouped together

### 2. **Professional Data Presentation**
- Tables have clear headers and borders
- Numbers are right-aligned, text is left-aligned
- Consistent use of symbols (✓, ⚠️, etc.)

### 3. **Effective Use of Color/Formatting**
- Commentary boxes with colored headers
- Risk assessments with warning colors
- Metric cards for quick scanning

### 4. **No Text Truncation**
- Full attribute names displayed
- Intelligent abbreviations where needed
- Tables sized appropriately for content

### 5. **Business Context**
- Plain English explanations
- "What Actually Happened" narrative
- Clear implications of findings

### 6. **Actionable Information**
- Specific recommendations
- Risk assessments with required actions
- Clear next steps

This mockup shows how the report should look when properly implemented, with professional formatting, clear information hierarchy, and no truncated text or broken layouts.