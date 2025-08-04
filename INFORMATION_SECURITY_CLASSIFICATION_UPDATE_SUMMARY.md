# Information Security Classification Update Summary

## Overview
Updated the information security classification functionality to use regulation-specific prompts, making it consistent with the PDE mapping and other LLM implementations.

## Changes Made

### 1. Created Regulation-Specific Information Security Classification Prompt
**File**: `/prompts/regulatory/fr_y_14m/schedule_d_1/information_security_classification.txt`

This prompt includes:
- FR Y-14M Schedule D.1 specific security requirements
- Federal Reserve data quality and retention standards
- Schedule-specific criticality guidelines:
  - HIGH: Account identifiers, credit scores, risk metrics
  - MEDIUM: Transaction data, rates, geographic data
  - LOW: Descriptive fields, system flags
- Regulatory compliance requirements:
  - FR Y-14M submission requirements
  - CCAR validation requirements
  - Privacy regulations (GLBA, FCRA, Reg P)
  - 5-year data retention requirements
- Security control recommendations based on field type

### 2. Created Generic Information Security Classification Prompt
**File**: `/prompts/information_security_classification.txt`

A fallback template for non-regulatory or unrecognized regulatory contexts with general security classification guidelines.

### 3. Updated Planning Activities Endpoint
**File**: `/app/api/v1/endpoints/planning_activities.py`

Changes to `get_llm_classification_suggestions`:
- Modified query to load report relationship through attribute
- Added regulatory context parsing logic
- Integrated PromptManager to load regulation-specific prompts
- Added source_system parameter to prompt
- Included logging to indicate when using regulatory-specific prompts
- Provided fallback prompt for cases where template is not found

## Key Improvements

### 1. **Regulatory Compliance Focus**
- Classification now considers FR Y-14M specific requirements
- Understands impact on stress testing and CCAR submissions
- Includes Federal Reserve examination findings context

### 2. **Schedule-Specific Security Guidelines**
- Credit card specific PII considerations (account numbers, credit scores)
- Proper classification of risk metrics (PD, LGD, EAD)
- Understanding of quasi-identifiers like ZIP codes

### 3. **Enhanced Security Controls**
- Recommends encryption, masking, access control levels
- Considers audit logging requirements
- Aligns with Federal Reserve data quality standards

### 4. **Consistency Across System**
- Follows same pattern as PDE mapping and attribute discovery
- Uses centralized PromptManager
- Supports prompt hierarchy (schedule → report → generic)

## Example Usage

When classifying a PDE for credit limit field in FR Y-14M Schedule D.1:

1. System detects: `regulatory_report = 'fr_y_14m'`, `schedule = 'schedule_d_1'`
2. Loads: `/prompts/regulatory/fr_y_14m/schedule_d_1/information_security_classification.txt`
3. LLM receives FR Y-14M D.1 specific guidance
4. Returns classification with:
   - Criticality: HIGH (critical for stress testing)
   - Risk Level: MEDIUM (confidential financial data)
   - Regulatory Flag: TRUE (required for FR Y-14M)
   - Security Controls: Encryption required, audit logging required

## Benefits

1. **Accuracy**: Classifications align with Federal Reserve requirements
2. **Compliance**: Considers all applicable regulations and standards
3. **Risk Management**: Properly identifies high-risk fields
4. **Audit Ready**: Provides evidence and rationale for classifications

## Next Steps

1. Create information security classification prompts for other FR Y-14M schedules
2. Add prompts for other regulatory reports (FR Y-14Q, FR Y-9C)
3. Consider integration with automated security control implementation
4. Add validation to ensure classifications meet minimum regulatory requirements