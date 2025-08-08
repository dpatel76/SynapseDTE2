# Scoping Attribute ID Refactoring Plan

## Current State
- ScopingAttribute has its own UUID (`attribute_id`) as primary key
- Also stores `planning_attribute_id` as a foreign key to planning phase
- This creates unnecessary indirection and complexity

## Problems with Current Approach
1. **Inconsistent References**: Same attribute has different IDs in different phases
2. **Complex Queries**: Need joins to connect scoping decisions back to planning attributes
3. **API Complexity**: Frontend needs to track multiple IDs for the same logical attribute
4. **Data Duplication**: Each version creates new UUIDs for the same attributes

## Proposed Solution
Use a composite key approach where ScopingAttribute is uniquely identified by:
- `version_id` (UUID) - The scoping version
- `planning_attribute_id` (Integer) - The planning attribute ID

## Benefits
1. **Consistent Identity**: Attributes maintain same ID across all phases
2. **Simpler Queries**: Direct reference to planning attributes
3. **Clear Relationships**: Obvious connection between planning and scoping
4. **Efficient Storage**: No unnecessary UUID generation

## Migration Strategy

### Phase 1: Add Constraints (Safe)
1. Add unique constraint on (version_id, planning_attribute_id)
2. Add indexes for performance
3. Keep existing attribute_id column for rollback safety

### Phase 2: Update Code (This PR)
1. Update model to use composite identification
2. Change API endpoints to accept planning_attribute_id
3. Update service methods to query by planning_attribute_id
4. Update frontend to use planning_attribute_id

### Phase 3: Cleanup (Future PR)
1. Drop the attribute_id column
2. Update primary key to composite
3. Clean up any remaining references

## API Changes

### Before:
```
POST /scoping/attributes/{attribute_id}/tester-decision
GET /scoping/attributes/{attribute_id}/history
```

### After:
```
POST /scoping/versions/{version_id}/attributes/{planning_attribute_id}/tester-decision
GET /scoping/phases/{phase_id}/attributes/{planning_attribute_id}/history
```

## Code Changes Required

1. **Model Updates**
   - Remove attribute_id as primary key
   - Add composite unique constraint
   - Update relationships

2. **Service Updates**
   - Change queries to use planning_attribute_id
   - Update create/update methods
   - Fix attribute lookups

3. **API Updates**
   - Change endpoints to use planning_attribute_id
   - Update response DTOs
   - Fix validation

4. **Frontend Updates**
   - Use planning_attribute_id consistently
   - Update API calls
   - Fix attribute references

## Rollback Plan
If issues arise:
1. Keep attribute_id column initially
2. Can revert to using attribute_id
3. Remove constraints in downgrade migration