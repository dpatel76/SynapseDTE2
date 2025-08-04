# PDE Mapping Implementation Update Summary

## Overview
Updated the PDE mapping functionality in the planning phase to use regulation-specific prompts, making it consistent with the rest of the LLM implementation.

## Changes Made

### 1. Created Regulation-Specific PDE Mapping Prompt
**File**: `/prompts/regulatory/fr_y_14m/schedule_d_1/pde_mapping.txt`

This prompt includes:
- FR Y-14M Schedule D.1 specific context
- 118 credit card fields guidance
- Exact Federal Reserve field naming conventions
- Schedule-specific mapping guidelines for:
  - Account identifiers (CUSIP_NUM, ACCT_NUM, CUST_ID)
  - Balance fields (CYCL_DT_BAL, PROMO_BAL, etc.)
  - Credit limit fields
  - Rate fields (as decimals, not percentages)
  - Date fields (YYYYMMDD format)
  - Payment/collection fields
  - Risk/score fields
- Data quality checks requirements
- Regulatory-specific transformation rules

### 2. Created Generic PDE Mapping Prompt Template
**File**: `/prompts/pde_mapping.txt`

A fallback template for non-regulatory or unrecognized regulatory contexts.

### 3. Updated Planning Activities Endpoint
**File**: `/app/api/v1/endpoints/planning_activities.py`

Changes:
- Added import for `get_prompt_manager` and `selectinload`
- Modified `get_llm_mapping_suggestions` endpoint to:
  - Load report relationship with attribute
  - Parse regulatory context to identify report type and schedule
  - Use PromptManager to load regulation-specific prompts
  - Pass all required parameters to the prompt template
  - Log when using regulatory-specific vs generic prompts
  - Provide fallback prompt if template not found

## Key Improvements

### 1. **Consistency**
- PDE mapping now follows the same pattern as other LLM operations
- Uses the centralized PromptManager system
- Supports the prompt hierarchy (schedule-specific → report-common → generic)

### 2. **Regulation-Specific Context**
- Automatically detects FR Y-14M and schedule from regulatory context
- Provides schedule-specific field names and validation rules
- Includes proper data type formatting requirements

### 3. **Better Mapping Suggestions**
- LLM receives exact Federal Reserve field names
- Understands schedule-specific requirements
- Can suggest appropriate transformations for regulatory compliance

### 4. **Extensibility**
- Easy to add PDE mapping prompts for other schedules
- Simply create `pde_mapping.txt` in the appropriate regulatory directory
- System will automatically use them based on context

## Usage Example

When a user triggers PDE mapping for an attribute in a report with regulatory context "FR Y-14M Schedule D.1 - Credit Card Portfolio":

1. System detects: `regulatory_report = 'fr_y_14m'`, `schedule = 'schedule_d_1'`
2. Loads: `/prompts/regulatory/fr_y_14m/schedule_d_1/pde_mapping.txt`
3. LLM receives FR Y-14M D.1 specific guidance
4. Returns mapping suggestions with:
   - Correct Federal Reserve field names (e.g., CYCL_DT_BAL)
   - Proper PDE codes (e.g., D1_CYCL_BAL)
   - Schedule-specific transformation rules

## Next Steps

1. Create PDE mapping prompts for other FR Y-14M schedules
2. Add prompts for FR Y-14Q, FR Y-9C, and other regulatory reports
3. Consider adding validation to ensure mapped PDEs comply with regulatory requirements