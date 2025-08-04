# Sample Selection Phase Name Fix Summary

## Issue
The workflow phase enum inconsistency between "Sampling" (database) and "Sample Selection" (API endpoints) was causing the sample selection endpoints to fail.

## Root Cause
- Database enum definition in `app/models/workflow.py` uses `'Sampling'`
- Sample selection API endpoints were looking for `'Sample Selection'` in the database
- This mismatch prevented the endpoints from finding the correct workflow phase

## Fix Applied
Updated `app/api/v1/endpoints/sample_selection.py` to use the correct phase name from the database enum:
- Changed all occurrences of `WorkflowPhase.phase_name == 'Sample Selection'` to `WorkflowPhase.phase_name == 'Sampling'`
- Changed `phase_name='Sample Selection'` to `phase_name='Sampling'` when creating workflow phases

## Architecture Notes
The system intentionally uses different names in different contexts:
1. **Database Phase Name**: `'Sampling'` (defined in workflow_phase_enum)
2. **Frontend Route**: `/sample-selection` (for URL consistency)
3. **UI Display**: "Sample Selection" (for user-friendly display)

This is handled by the phase route mapping in `frontend/src/components/WorkflowProgress.tsx`:
```javascript
const phaseRoutes: Record<string, string> = {
  'Sampling': 'sample-selection',  // Maps database name to route
  // ... other phases
};
```

## Files Modified
1. `/Users/dineshpatel/code/projects/SynapseDT/app/api/v1/endpoints/sample_selection.py`
   - Updated 4 occurrences of phase name references

## Testing Recommendations
1. Test sample selection phase initialization
2. Test sample selection phase status updates
3. Verify workflow progression through the sample selection phase
4. Check that the frontend correctly navigates to sample selection pages

## No Further Changes Needed
- Frontend routing is correctly configured
- UI display names can remain as "Sample Selection" for user clarity
- The phase mapping in WorkflowProgress.tsx correctly handles the conversion