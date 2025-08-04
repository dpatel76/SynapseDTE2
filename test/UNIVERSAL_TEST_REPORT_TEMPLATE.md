# Universal Test Report Template for SynapseDTE

## Design Principles

This template is designed to work for ALL reports regardless of:
- Testing coverage (from <1% to 100%)
- Number of attributes (from dozens to hundreds)
- Testing approach (minimal investigation vs comprehensive testing)
- Phase completion status (partial vs complete)
- Issue severity (no issues to critical failures)

## Dynamic Report Structure

### 1. Executive Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                   EXECUTIVE SUMMARY                              │
│                                                                 │
│              [Report Name] Testing Report                        │
│              Cycle [X] - [Period] Results                        │
└─────────────────────────────────────────────────────────────────┘
```

**Executive Overview**
```
This report summarizes the testing performed on [Report Name] for [Period].

Report Purpose: [Plain English description of what this report does and why it matters]

Testing Approach: [Brief description - e.g., "Comprehensive risk-based testing" or 
"Targeted investigation of specific attributes" or "Pilot testing of new methodology"]
```

### 2. Report Context and Stakeholders

```
Report Information:
• Report Name: [Full regulatory name]
• Report ID: [System ID]
• Frequency: [Monthly/Quarterly/Annual]
• Regulatory Body: [Fed/OCC/FDIC/etc]
• Business Impact: [Why this report matters]

Key Stakeholders:
• Report Owner: [Name, Title]
• Report Owner Executive: [Name, Title]
• Lead Tester: [Name]
• Test Executive: [Name, Title]
• Data Owners: [List by LOB]
• Data Executive: [Name, Title]
```

### 3. Testing Summary Dashboard

**Dynamic Coverage Analysis**
```
Testing Coverage:
• Total Attributes: [X]
• Testable Attributes (Non-PK): [Y]
• Attributes Selected: [Z] ([Z/Y]%)
• Attributes Tested: [A] ([A/Z]% of selected, [A/Y]% of testable)

[CONDITIONAL MESSAGING BASED ON COVERAGE:]
- If coverage < 5%: "⚠️ MINIMAL COVERAGE: This represents targeted testing only"
- If coverage 5-25%: "⚠️ LIMITED COVERAGE: Focused on highest risk areas"
- If coverage 25-50%: "MODERATE COVERAGE: Risk-based selection applied"
- If coverage 50-75%: "GOOD COVERAGE: Majority of key attributes tested"
- If coverage > 75%: "✓ COMPREHENSIVE COVERAGE: Thorough testing performed"
```

**Quality Results**
```
Test Execution Summary:
• Samples Selected: [X] [Add context: "minimal" if <5, "limited" if <30, "adequate" if 30-100, "comprehensive" if >100]
• Test Cases Designed: [Y]
• Test Cases Executed: [Z] ([Z/Y]%)
• Pass Rate: [P]%
• Issues Identified: [I]
  - High Severity: [H]
  - Medium Severity: [M]
  - Low Severity: [L]

[CONDITIONAL STATUS:]
- If no testing done: "Status: NOT STARTED"
- If testing < 100%: "Status: IN PROGRESS ([X]% complete)"
- If testing = 100%: "Status: COMPLETE"
```

### 4. Phase-by-Phase Analysis

#### Planning Phase
```
What We Did:
[Dynamic description based on data]
- If all attributes catalogued: "Completed comprehensive attribute inventory"
- If CDE identified: "Identified [X] Critical Data Elements requiring focused testing"
- If issues noted: "Documented [X] attributes with known historical issues"

Results:
• Attributes Identified: [Total]
• Critical Data Elements: [X] ([X/Total]%)
• Primary Keys: [Y] (excluded from value testing)
• Known Issues: [Z]
• Approval Status: [Approved/Pending/Rejected]

[INSIGHT BOX - Conditional based on CDE percentage:]
- If CDE < 5%: "This report is primarily informational with few critical calculations"
- If CDE 5-15%: "Moderate number of critical elements requiring focused attention"
- If CDE > 15%: "High concentration of critical elements indicates calculation-intensive report"
```

#### Data Profiling Phase
```
Profiling Approach:
[Dynamic based on approval rate]
- If <10% approved: "Highly selective profiling focused on critical checks only"
- If 10-50% approved: "Targeted profiling of key data quality dimensions"
- If >50% approved: "Comprehensive profiling across multiple quality dimensions"

Results:
• Rules Generated: [X]
• Rules Approved: [Y] ([Y/X]%)
• Rules Executed: [Z]
• Anomalies Found: [A] affecting [B] attributes

[QUALITY SCORE BOX:]
- If anomalies = 0: "✓ Data Quality Score: 100% - No issues detected"
- If anomalies < 5%: "Data Quality Score: [X]% - Minor issues identified"
- If anomalies > 5%: "⚠️ Data Quality Score: [X]% - Significant issues require attention"
```

#### Scoping Phase
```
Selection Strategy:
[Dynamic based on selection percentage]
- If <5%: "MINIMAL SELECTION: [Explain why - pilot, investigation, etc.]"
- If 5-25%: "FOCUSED SELECTION: Concentrated on highest risk attributes"
- If 25-50%: "BALANCED SELECTION: Risk-based approach with good coverage"
- If >50%: "COMPREHENSIVE SELECTION: Broad coverage across report"

Results:
• Testable Attributes: [X]
• Selected for Testing: [Y] ([Y/X]%)
• Risk Distribution:
  - High Risk: [H]
  - Medium Risk: [M]
  - Low Risk: [L]

[COVERAGE WARNING BOX - If <25%:]
⚠️ Testing [Y] of [X] attributes means [X-Y] attributes ([%]) receive no testing.
Management must formally accept this risk.
```

#### Sample Selection Phase
```
Sampling Methodology:
[Dynamic based on sample count]
- If <5 samples: "Minimal sampling - spot check only"
- If 5-30: "Limited sampling - basic coverage"
- If 30-100: "Adequate sampling - statistical validity"
- If >100: "Comprehensive sampling - high confidence"

Results:
• Total Samples: [X]
• Samples per Attribute: [Avg]
• Time Period Coverage: [Dates]
• Business Line Coverage: [List]

[STATISTICAL VALIDITY BOX:]
- If <30: "⚠️ Insufficient samples for statistical confidence"
- If 30-100: "Adequate samples for moderate confidence (±[X]% margin)"
- If >100: "✓ Strong statistical validity achieved"
```

#### Test Execution Phase
```
Testing Progress:
[Dynamic status based on completion]
- If 0%: "NOT STARTED"
- If 1-99%: "IN PROGRESS: [X] of [Y] attributes tested ([Z]%)"
- If 100%: "COMPLETE: All selected attributes tested"

Results:
• Attributes Tested: [X] of [Y] selected
• Test Cases Executed: [Z]
• Pass Rate: [P]%
• Failed Tests: [F] affecting [A] attributes

[RESULTS INTERPRETATION BOX:]
- If pass rate = 100%: "All tests passed - no issues identified"
- If pass rate > 90%: "High pass rate with limited issues"
- If pass rate 75-90%: "Moderate issues requiring attention"
- If pass rate < 75%: "⚠️ Significant issues detected"
```

#### Observation Management Phase
```
Issue Summary:
• Total Observations: [X]
• Severity Distribution:
  - High: [H] ([H/X]%)
  - Medium: [M] ([M/X]%)
  - Low: [L] ([L/X]%)

Resolution Status:
• Approved by Management: [A]
• Pending Approval: [P]
• Remediation Plans Developed: [R]

[If no observations: "✓ No issues identified during testing"]
[If observations exist: Include top 3 high severity issues with summaries]
```

### 5. Critical Analysis Section

**Dynamic Risk Assessment**
```
Testing Adequacy Assessment:
[Based on coverage percentage and results]

[CONDITIONAL ASSESSMENTS:]

For <5% coverage:
┌─────────────────────────────────────────────────────────────────┐
│                    ⚠️ CRITICAL WARNING                           │
├─────────────────────────────────────────────────────────────────┤
│ Testing coverage of [X]% provides minimal assurance about       │
│ report accuracy. This approach:                                 │
│ • Leaves [Y]% of attributes untested                           │
│ • Cannot detect systematic issues                               │
│ • May not meet regulatory expectations                         │
│ • Requires documented risk acceptance                          │
└─────────────────────────────────────────────────────────────────┘

For 5-25% coverage:
┌─────────────────────────────────────────────────────────────────┐
│                    ⚠️ LIMITED ASSURANCE                          │
├─────────────────────────────────────────────────────────────────┤
│ Testing coverage of [X]% provides limited assurance. Consider:  │
│ • Expanding coverage to include all high-risk attributes       │
│ • Documenting rationale for exclusions                         │
│ • Implementing compensating controls                           │
└─────────────────────────────────────────────────────────────────┘

For >50% coverage with no issues:
┌─────────────────────────────────────────────────────────────────┐
│                    ✓ POSITIVE RESULTS                           │
├─────────────────────────────────────────────────────────────────┤
│ Testing coverage of [X]% with [Y]% pass rate indicates:        │
│ • Good data quality in tested areas                            │
│ • Effective controls are in place                              │
│ • Low risk of material misstatement                           │
└─────────────────────────────────────────────────────────────────┘
```

### 6. Recommendations Section

**Dynamic Recommendations Based on Results**

```
[CONDITIONAL RECOMMENDATIONS:]

If coverage < 25%:
IMMEDIATE ACTIONS REQUIRED:
1. Expand testing coverage to minimum 25-30% of attributes
2. Ensure all CDEs and known issue attributes are included
3. Obtain executive sign-off on risk acceptance for untested areas

If high severity issues found:
CRITICAL REMEDIATIONS:
1. [List each high severity issue with deadline]
2. Implement controls to prevent recurrence
3. Consider restatement if material

If pass rate < 90%:
QUALITY IMPROVEMENTS NEEDED:
1. Root cause analysis for systematic failures
2. Enhanced controls at data source
3. Additional training for data providers

If all good:
MAINTAIN CURRENT STATE:
1. Continue current testing approach
2. Consider automation opportunities
3. Share best practices across teams
```

### 7. Executive Sign-Off Section

```
[DYNAMIC BASED ON RESULTS:]

For minimal coverage:
┌─────────────────────────────────────────────────────────────────┐
│                  RISK ACCEPTANCE REQUIRED                        │
├─────────────────────────────────────────────────────────────────┤
│ By testing only [X]% of attributes, management accepts:        │
│ • Potential undetected errors in [Y] untested attributes       │
│ • Regulatory criticism risk                                     │
│ • Reliance on other controls                                    │
│                                                                 │
│ ________________________          ________________________     │
│ Report Owner                      Executive Sponsor             │
│ Date: __________________          Date: __________________     │
└─────────────────────────────────────────────────────────────────┘

For comprehensive testing:
┌─────────────────────────────────────────────────────────────────┐
│                  MANAGEMENT ATTESTATION                          │
├─────────────────────────────────────────────────────────────────┤
│ We have reviewed the comprehensive testing results and:         │
│ • Acknowledge the findings                                      │
│ • Approve the remediation plans                                 │
│ • Commit to addressing identified issues                        │
│                                                                 │
│ ________________________          ________________________     │
│ Report Owner                      Executive Sponsor             │
│ Date: __________________          Date: __________________     │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Guidelines

### 1. Data Requirements
To generate this report, the system needs:
- Report metadata (name, frequency, purpose)
- Stakeholder assignments
- Phase completion data
- Attribute counts and classifications
- Test execution results
- Observation details
- Approval statuses

### 2. Conditional Logic Rules
- Coverage thresholds: <5%, 5-25%, 25-50%, 50-75%, >75%
- Sample adequacy: <5, 5-30, 30-100, >100
- Pass rate categories: 100%, >90%, 75-90%, <75%
- CDE concentration: <5%, 5-15%, >15%

### 3. Dynamic Sections
- Show/hide sections based on phase completion
- Adjust language based on coverage levels
- Include warnings for inadequate testing
- Highlight achievements for good results

### 4. Flexibility Features
- Works for reports with 10 to 1000+ attributes
- Handles partial or complete testing
- Adapts messaging for different audiences
- Scales details based on complexity

## Benefits of This Universal Template

1. **Consistency**: All reports follow same structure
2. **Flexibility**: Adapts to any testing scenario
3. **Transparency**: Clear about limitations
4. **Risk-Focused**: Highlights gaps and issues
5. **Actionable**: Provides specific recommendations
6. **Audit-Ready**: Complete documentation
7. **Scalable**: Works for simple or complex reports

This template ensures that whether testing 1 attribute or 100, the report accurately reflects the testing performed and clearly communicates both achievements and limitations.