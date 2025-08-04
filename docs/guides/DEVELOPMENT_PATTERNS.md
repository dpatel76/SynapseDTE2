# Development Patterns and Common Mistakes

## Common UI/UX Patterns in SynapseDTE

### 1. Phase Start Pattern
Every workflow phase follows this pattern when in "Not Started" status:
- Display a prominent card with "Start [Phase Name] Phase" button
- Button calls `POST /{phase}/cycles/{cycleId}/reports/{reportId}/start`
- Payload includes: `planned_start_date`, `planned_end_date`, `notes`
- After successful start, reload phase status
- Disable phase-specific actions until phase is started

Example endpoints:
- `/planning/cycles/{cycleId}/reports/{reportId}/start`
- `/scoping/cycles/{cycleId}/reports/{reportId}/start`
- `/sample-selection/cycles/{cycleId}/reports/{reportId}/start`

### 2. Phase Workflow Cards
Activity/workflow cards show phase progress:
- Each phase has 4-6 steps displayed as cards
- Status: pending, active, in_progress, completed, revision_required
- Cards are visual indicators, not interactive elements
- Status is derived from phase data, not separate API calls

### 3. Submit/Review Pattern
Most phases follow this flow:
1. Tester performs work (create samples, execute tests, etc.)
2. Tester submits for approval
3. Report Owner reviews and can: Approve, Reject, Request Revision
4. If revision requested, workflow reverts to tester action state

### 4. Individual Items vs Sets Pattern
The codebase is moving from "sets" to "individual items":
- Old: SampleSet → New: IndividualSample
- Old: TestSet → New: IndividualTest
- Always check which pattern is being used in current code

## Common Mistakes to Avoid

### 1. Making Unnecessary Changes
❌ **DON'T**: Modify working code when investigating issues
✅ **DO**: Understand the code first, only change what's explicitly requested

### 2. Not Checking Existing Patterns
❌ **DON'T**: Implement new patterns without checking existing ones
✅ **DO**: Look at similar phases/features for established patterns

### 3. Assuming Endpoints Don't Exist
❌ **DON'T**: Create new endpoints without thorough search
✅ **DO**: Search multiple ways - grep, file names, route definitions

### 4. Breaking Working Features
❌ **DON'T**: "Fix" code that isn't broken
✅ **DO**: Test understanding by explaining what you'll do before doing it

### 5. Incomplete Changes
❌ **DON'T**: Change frontend without checking backend, or vice versa
✅ **DO**: Consider full stack implications of changes

## Search Strategies

### Finding Endpoints
1. `grep -r "endpoint_name" app/api/v1/endpoints/`
2. Check route definitions in endpoint files
3. Look for similar phase endpoints as reference
4. Check the api.py file for route includes

### Finding UI Components
1. Check route definitions in App.tsx
2. Trace from URL to component
3. Look for similar phase pages as reference

### Finding Data Models
1. Check app/models/ directory
2. Look for relationships and foreign keys
3. Check migration files for schema

## Testing Checklist Before Making Changes

1. **Understand Current State**
   - How does it currently work?
   - What specific issue needs fixing?
   - Are there similar working examples?

2. **Validate Assumptions**
   - Does the endpoint exist?
   - Is this the right component?
   - Am I fixing the root cause?

3. **Minimize Impact**
   - What's the smallest change needed?
   - Will this break anything else?
   - Should I ask for clarification first?

## Common API Response Patterns

### Success Response
```json
{
  "message": "Action completed successfully",
  "data": { ... },
  "metadata": {
    "processing_time": 123,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Error Response
```json
{
  "detail": "Human readable error message",
  "status_code": 400,
  "error_code": "SPECIFIC_ERROR_CODE"
}
```

### List Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

## Phase Status Management

### Workflow Phase States
- `state`: Not Started, In Progress, Complete, Blocked, Skipped
- `status`: Pending, Active, Under Review, Approved, On Hold

### Phase Dependencies
- Planning → Scoping → (Sample Selection || Data Provider) → Testing
- Some phases can run in parallel
- Check WorkflowOrchestrator for rules

## Authentication and Permissions

### Role-Based Access
- Frontend: Check user role before showing UI elements
- Backend: Use @require_permission decorators
- Common roles: Tester, Test Manager, Report Owner, Data Owner, CDO

### Permission Pattern
```python
@require_permission("sample_selection", "create")
```

## Remember: When in Doubt

1. **Look for existing examples** in similar phases
2. **Ask for clarification** rather than assuming
3. **Explain your plan** before implementing
4. **Test locally** if possible
5. **Keep changes minimal** and focused