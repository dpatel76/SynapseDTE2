# Sample Selection Feedback Debug Enhancements

## Summary of Changes

I've enhanced the Sample Selection page to better handle and display feedback for Testers when Report Owners send samples back for revision. The key changes include:

### 1. Enhanced Logging
- Added comprehensive console.log statements to track feedback loading process
- Logs show when feedback is being loaded, what sample sets have potential feedback, and the final feedback map
- This helps debug why feedback alerts might not be showing

### 2. Added Revision Required Tracking
- Added `revision_required_sets` field to the `SampleSelectionPhaseStatus` interface
- This field is calculated on the frontend from the sample sets data
- Updates automatically when sample sets change status

### 3. Improved Workflow Step Display
- The "Report Owner Review & Approval" step now shows "Revision Required" status when applicable
- Added error color (red) for revision_required status
- Step description now includes count of sets needing revision

### 4. Fixed React Dependencies
- Converted `loadFeedbackForSampleSets` to useCallback to prevent unnecessary re-renders
- Added proper dependencies to useEffect hooks
- Separated revision count calculation to avoid circular dependencies

## How to Debug Feedback Issues

1. **Check Console Logs**: Open browser console and look for:
   - 🔍 "Loading feedback for sample sets..." - Shows which sets are being checked
   - ✅ "Feedback loaded for {set_id}" - Confirms feedback was retrieved
   - ℹ️ "No feedback exists for {set_id} (404)" - Normal for sets without feedback
   - ❌ "Error loading feedback" - Indicates API errors
   - 🚨 "Feedback alert check" - Shows if alert conditions are met

2. **Verify Sample Set Status**: The feedback alert only shows for:
   - Sample sets with status = 'Revision Required'
   - AND feedback exists (has_feedback = true)
   - AND user role = 'Tester'

3. **Check Workflow Steps**: Look at the progress indicator:
   - "Report Owner Review & Approval" should show "Revision Required" in red
   - Description should include count of sets needing revision

## API Expectations

The feedback API endpoint returns:
```json
{
  "sample_set_id": "string",
  "has_feedback": true,
  "needs_revision": true,
  "feedback": {
    "decision": "Revision Required",
    "feedback": "Specific feedback text",
    "requested_changes": ["change1", "change2"],
    "approved_by": "Report Owner Name",
    "approved_at": "2024-01-20T..."
  },
  "individual_sample_decisions": {}
}
```

## Common Issues

1. **Feedback not showing**: Check if:
   - Sample set status is exactly 'Revision Required' (not 'Needs Changes')
   - Feedback API is returning data (check Network tab)
   - User role is 'Tester' (not 'Test Manager' or other)

2. **Workflow step shows "In Progress" instead of "Revision Required"**:
   - This is now fixed - the step will show "Revision Required" when any sets need revision

3. **Performance issues**:
   - Feedback is loaded for all eligible sample sets in parallel
   - 404 errors are expected and handled gracefully
   - Only loads feedback for sets that might have it