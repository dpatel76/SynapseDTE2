# Testing the Fixed Scoping Workflow

## Summary of Changes

1. **Backend API Fixed**: 
   - The `/scoping/status` endpoint now properly queries `ScopingSubmission` and `ReportOwnerScopingReview` tables
   - Returns actual submission and review status instead of deriving from workflow phase

2. **Frontend State Management Fixed**:
   - Removed all session storage dependencies
   - Workflow steps now determined by actual API data
   - Added support for revision status

3. **ScopingDecisionToggle Fixed**:
   - Now properly shows "Not in Scope" for planning-unapproved attributes
   - Shows Include/Exclude toggles for all planning-approved attributes

## How to Test

1. Navigate to the scoping page for a cycle/report
2. Check the workflow cards - they should show:
   - "Start Scoping Phase" (if not started)
   - "Generate LLM Recommendations" (if phase started but no recommendations)
   - "Tester Review & Decisions" (if recommendations exist)
   - "Report Owner Approval" (if submitted)
   - "Complete Scoping Phase" (if approved)

3. For the Include/Exclude toggles:
   - Primary Key attributes should show "Included (PK)" chip
   - Planning-approved attributes should show Include/Exclude toggle buttons
   - Non-approved attributes should show "Not in Scope"

4. The workflow state should persist across page refreshes (no more session storage!)

## Key Differences

- **Planning Approval**: Stored in `ReportAttribute.approval_status` - determines which attributes are in scope
- **Scoping Approval**: Stored in `ReportOwnerScopingReview` - approves the tester's Include/Exclude decisions

The workflow now properly tracks:
- Has the phase started?
- Are there LLM recommendations?
- Has the tester submitted decisions?
- Has the report owner reviewed?
- Is the phase complete?