# Risk Score Enhancement Implementation

## Summary

Enhanced the SynapseDT platform to incorporate LLM-provided risk scores into the attribute generation and scoping recommendation process.

## Key Changes

### 1. Database Schema Enhancement
- Added `risk_score` field (Float, 0-10) to `report_attributes` table
- Added `llm_risk_rationale` field (Text) to store LLM's reasoning
- Created migration: `2025_06_06_risk_score_enhancement.py`

### 2. Prompt Updates
- Updated all FR Y-14M `attribute_batch_details.txt` prompts (7 files)
- Changed from 8 fields to 10 fields per attribute
- Added risk scoring guidelines:
  - 9-10: Critical stress testing inputs
  - 7-8: Important risk metrics and identifiers
  - 5-6: Supporting data elements
  - 3-4: Optional enrichment fields
  - 1-2: Low priority descriptive fields

### 3. Backend Implementation
- **Planning Endpoint** (`app/api/v1/endpoints/planning.py`):
  - Updated to capture and store `risk_score` and `llm_risk_rationale` from LLM responses
  - Both synchronous and asynchronous endpoints updated

- **Scoping Endpoint** (`app/api/v1/endpoints/scoping.py`):
  - Enhanced scoring logic to use LLM risk scores when available
  - If LLM risk score exists: Uses it as base score with reduced modifiers for CDE (+1.5) and historical issues (+1.0)
  - If no LLM risk score: Falls back to original local scoring logic
  - Updated rationale to indicate whether LLM risk score was used

### 4. Data Flow

1. **Planning Phase**: 
   - CDE matching happens during attribute generation
   - Historical issue matching happens during attribute generation
   - LLM provides `mandatory_flag`, `risk_score`, and `llm_risk_rationale`
   - All flags and scores are saved to database

2. **Scoping Phase**:
   - Reads attributes with their LLM risk scores
   - Applies hybrid scoring:
     - Primary: LLM risk score (if available)
     - Secondary: Local modifiers based on CDE/historical flags
   - Generates TEST/SKIP recommendations based on final score

### 5. Answers to Original Questions

1. **CDE and historical issue matching DOES happen in planning phase** ✓
   - Matching logic in `/planning/{cycle_id}/reports/{report_id}/generate-attributes-llm`
   - Flags are saved to database

2. **CDE and historical flags ARE passed to scoping, but scoring is hybrid** ✓
   - LLM provides initial risk scores during attribute generation
   - Scoping uses LLM scores when available, with additional local modifiers
   - Falls back to pure local scoring if no LLM risk score

3. **Mandatory flag IS coming from LLM** ✓
   - LLM returns `mandatory_flag` as part of attribute details
   - Values: Mandatory, Conditional, Optional

## Testing Recommendations

1. Run database migration: `alembic upgrade head`
2. Test attribute generation with FR Y-14M schedules
3. Verify risk scores are being captured and displayed
4. Test scoping recommendations with both LLM and non-LLM attributes
5. Validate that CDE and historical matching still works correctly

## Future Enhancements

1. Add risk score visualization in frontend
2. Allow manual override of LLM risk scores
3. Add risk score trend analysis
4. Create risk score calibration based on historical testing results