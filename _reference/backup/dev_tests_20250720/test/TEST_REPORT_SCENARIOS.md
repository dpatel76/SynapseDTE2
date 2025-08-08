# Test Report Template - Scenario Examples

This document shows how the universal template adapts to different testing scenarios.

## Scenario 1: Minimal Testing (Like Report 156)

**Context**: 118 attributes, 1 tested (0.88% coverage), 2 samples, 100% pass rate

**Executive Summary Output**:
```
Testing Approach: Targeted investigation of specific attribute

Testing Coverage:
• Total Attributes: 118
• Testable Attributes (Non-PK): 114
• Attributes Selected: 1 (0.88%)
• Attributes Tested: 1 (100% of selected, 0.88% of testable)

⚠️ MINIMAL COVERAGE: This represents targeted testing only
```

**Risk Assessment Output**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    ⚠️ CRITICAL WARNING                           │
├─────────────────────────────────────────────────────────────────┤
│ Testing coverage of 0.88% provides minimal assurance about      │
│ report accuracy. This approach:                                 │
│ • Leaves 99.12% of attributes untested                         │
│ • Cannot detect systematic issues                               │
│ • May not meet regulatory expectations                         │
│ • Requires documented risk acceptance                          │
└─────────────────────────────────────────────────────────────────┘
```

## Scenario 2: Moderate Risk-Based Testing

**Context**: 200 attributes, 60 tested (30% coverage), 180 samples, 92% pass rate, 5 medium issues

**Executive Summary Output**:
```
Testing Approach: Risk-based selection focusing on critical data elements

Testing Coverage:
• Total Attributes: 200
• Testable Attributes (Non-PK): 190
• Attributes Selected: 60 (31.6%)
• Attributes Tested: 60 (100% of selected, 31.6% of testable)

MODERATE COVERAGE: Risk-based selection applied
```

**Quality Results Output**:
```
Test Execution Summary:
• Samples Selected: 180 (adequate)
• Test Cases Designed: 180
• Test Cases Executed: 180 (100%)
• Pass Rate: 92%
• Issues Identified: 5
  - High Severity: 0
  - Medium Severity: 5
  - Low Severity: 0

Status: COMPLETE
```

## Scenario 3: Comprehensive Testing

**Context**: 85 attributes, 75 tested (88% coverage), 450 samples, 87% pass rate, 2 high, 8 medium issues

**Executive Summary Output**:
```
Testing Approach: Comprehensive risk-based testing

Testing Coverage:
• Total Attributes: 85
• Testable Attributes (Non-PK): 80
• Attributes Selected: 75 (93.8%)
• Attributes Tested: 75 (100% of selected, 93.8% of testable)

✓ COMPREHENSIVE COVERAGE: Thorough testing performed
```

**Observation Output**:
```
Issue Summary:
• Total Observations: 10
• Severity Distribution:
  - High: 2 (20%)
  - Medium: 8 (80%)
  - Low: 0 (0%)

HIGH SEVERITY ISSUES:
1. Total Assets Reconciliation - $2.5M variance requires immediate correction
2. Loan Loss Reserve Calculation - Formula error understating reserves
```

## Scenario 4: In-Progress Testing

**Context**: 150 attributes, 40 selected, 25 tested (62.5% of selected), 3 high issues found so far

**Executive Summary Output**:
```
Testing Coverage:
• Total Attributes: 150
• Testable Attributes (Non-PK): 145
• Attributes Selected: 40 (27.6%)
• Attributes Tested: 25 (62.5% of selected, 17.2% of testable)

LIMITED COVERAGE: Focused on highest risk areas
Status: IN PROGRESS (62.5% complete)
```

## Scenario 5: Perfect Results

**Context**: 50 attributes, 45 tested (90% coverage), 300 samples, 100% pass rate, 0 issues

**Executive Summary Output**:
```
✓ COMPREHENSIVE COVERAGE: Thorough testing performed

Test Execution Summary:
• Samples Selected: 300 (comprehensive)
• Test Cases Executed: 135
• Pass Rate: 100%
• Issues Identified: 0

Status: COMPLETE
```

**Risk Assessment Output**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    ✓ POSITIVE RESULTS                           │
├─────────────────────────────────────────────────────────────────┤
│ Testing coverage of 90% with 100% pass rate indicates:         │
│ • Excellent data quality in tested areas                       │
│ • Effective controls are in place                              │
│ • Low risk of material misstatement                           │
│ • Strong compliance with regulatory requirements               │
└─────────────────────────────────────────────────────────────────┘
```

## Dynamic Elements Examples

### Coverage-Based Messaging

```python
if coverage_percentage < 5:
    message = "⚠️ MINIMAL COVERAGE: This represents targeted testing only"
    risk_level = "CRITICAL"
elif coverage_percentage < 25:
    message = "⚠️ LIMITED COVERAGE: Focused on highest risk areas"
    risk_level = "HIGH"
elif coverage_percentage < 50:
    message = "MODERATE COVERAGE: Risk-based selection applied"
    risk_level = "MEDIUM"
elif coverage_percentage < 75:
    message = "GOOD COVERAGE: Majority of key attributes tested"
    risk_level = "LOW"
else:
    message = "✓ COMPREHENSIVE COVERAGE: Thorough testing performed"
    risk_level = "MINIMAL"
```

### Sample Adequacy Assessment

```python
if total_samples < 5:
    sample_assessment = "minimal"
    statistical_note = "⚠️ Insufficient samples for statistical confidence"
elif total_samples < 30:
    sample_assessment = "limited"
    statistical_note = "⚠️ Limited statistical validity"
elif total_samples < 100:
    sample_assessment = "adequate"
    statistical_note = f"Adequate samples for moderate confidence (±{margin}% margin)"
else:
    sample_assessment = "comprehensive"
    statistical_note = "✓ Strong statistical validity achieved"
```

### Recommendations Based on Results

```python
recommendations = []

# Coverage-based recommendations
if coverage_percentage < 25:
    recommendations.append({
        "priority": "IMMEDIATE",
        "action": "Expand testing coverage to minimum 25-30% of attributes",
        "deadline": "Next testing cycle"
    })

# Issue-based recommendations
if high_severity_count > 0:
    recommendations.append({
        "priority": "CRITICAL",
        "action": f"Address {high_severity_count} high severity issues",
        "deadline": "Before report submission"
    })

# Pass rate recommendations
if pass_rate < 90:
    recommendations.append({
        "priority": "HIGH",
        "action": "Perform root cause analysis on test failures",
        "deadline": "Within 2 weeks"
    })
```

## Benefits of Dynamic Approach

1. **Accurate Representation**: Never overstates or understates the testing performed
2. **Risk Transparency**: Clearly communicates limitations when testing is minimal
3. **Positive Recognition**: Highlights good results when achieved
4. **Actionable Guidance**: Recommendations match the specific situation
5. **Regulatory Defensible**: Honest about gaps while showing risk awareness
6. **Scalable**: Works equally well for small focused tests or large comprehensive reviews

This template ensures consistent, professional reporting regardless of testing scope while maintaining complete transparency about coverage and limitations.