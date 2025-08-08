# Fix for Scoping Version Issue

## Problem
When the Data Owner ID phase starts, it creates 5 assignments instead of 1 because:
1. Multiple scoping versions have `report_owner_decision = 'approved'` for the same attribute
2. When new versions are created from parent versions, they copy the report owner's decision
3. This causes the query to find 5 versions with approved "Current Credit limit" attribute

## Root Cause
In the scoping version creation logic, when creating a new version from a parent:
- Version 27: Originally approved by RO
- Version 29: Created from 27, copied the approved decision  
- Version 30: Created from 29, copied the approved decision
- Version 31: Fresh RO approval (the correct one)
- Version 32: Created from 31, copied the approved decision

## Solution

### Option 1: Fix the Version Creation (Recommended)
When creating new scoping versions, reset the report owner decisions:

```python
# In scoping version creation service
def create_new_version_from_parent(parent_version):
    # Copy attributes from parent
    for attr in parent_attributes:
        new_attr = ScopingAttribute(
            # ... copy other fields ...
            report_owner_decision=None,  # Reset RO decision
            report_owner_notes=None,
            report_owner_decided_by_id=None,
            report_owner_decided_at=None
        )
```

### Option 2: Fix the Query (Current Workaround)
The query already filters by approved version correctly:
```python
# Only get attributes from the approved version
scoped_attrs_query = await db.execute(
    select(ScopingAttribute, PlanningAttribute)
    .join(PlanningAttribute, ScopingAttribute.planning_attribute_id == PlanningAttribute.id)
    .where(and_(
        ScopingAttribute.version_id == approved_version_id,  # This is correct
        ScopingAttribute.is_primary_key == False,
        ScopingAttribute.report_owner_decision == 'approved'
    ))
)
```

## Issue Found
The issue was NOT in the query itself, but in how the phase start was called multiple times or how the workflow was structured. The query returns 1 result correctly when tested.

## Current Status
- Fixed by manually creating the single correct assignment
- 1 assignment created for: Current Credit limit × GBM LOB
- Assigned to Data Executive (user ID 5)

## Next Steps
1. Find where scoping versions are created and ensure RO decisions are reset
2. Clean up the database to remove incorrect RO decisions from non-approved versions
3. Add validation to prevent this issue in the future