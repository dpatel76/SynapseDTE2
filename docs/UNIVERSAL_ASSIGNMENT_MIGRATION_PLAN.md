# Universal Assignment Migration Plan

## Overview
Migrate from phase-specific notification tables to the universal assignment system.

## Current State Analysis

### Phase-Specific Notification Tables
1. **cdo_notifications** (Data Owner Phase)
   - Used for notifying CDOs about LOB assignments
   - Simple structure: notification text, status, timestamps
   - Limited lifecycle: sent → acknowledged → complete

2. **data_owner_notifications** (Request Info Phase)
   - Used for notifying data owners about information requests
   - Similar simple structure
   - No delegation or escalation support

### Universal Assignment System
- **universal_assignments** table
- Comprehensive task lifecycle management
- Supports delegation, escalation, approvals
- Rich metadata and context
- Phase-agnostic design

## Migration Strategy

### Phase 1: Parallel Operation (Week 2)
1. **Keep existing tables active**
2. **Create adapters** that write to both systems:
   ```python
   # When creating a CDO notification:
   # 1. Create in cdo_notifications (existing)
   # 2. Also create in universal_assignments (new)
   ```

3. **Map notification types to assignment types:**
   - cdo_notifications → Assignment Type: "LOB Assignment"
   - data_owner_notifications → Assignment Type: "Information Request"

### Phase 2: Data Migration (Week 3)
1. **Historical Data Migration Script**
   ```sql
   -- Migrate CDO notifications
   INSERT INTO universal_assignments (
       assignment_type, cycle_id, report_id, 
       from_user_id, to_user_id, status, 
       created_at, context
   )
   SELECT 
       'LOB Assignment', cycle_id, report_id,
       created_by, cdo_user_id, 
       CASE status 
           WHEN 'sent' THEN 'assigned'
           WHEN 'acknowledged' THEN 'acknowledged'
           WHEN 'complete' THEN 'completed'
       END,
       created_at,
       jsonb_build_object(
           'notification_text', notification_text,
           'lob_id', lob_id,
           'migrated_from', 'cdo_notifications',
           'original_id', notification_id
       )
   FROM cdo_notifications;
   ```

2. **Verification**
   - Count records in both systems
   - Validate data integrity
   - Test queries work correctly

### Phase 3: API Migration (Week 3)
1. **Update API Endpoints**
   ```python
   # Old endpoint
   @router.post("/data-owner/notify-cdo")
   async def notify_cdo_old(...):
       # Create in cdo_notifications
   
   # New endpoint  
   @router.post("/data-owner/notify-cdo")
   async def notify_cdo_new(...):
       # Create in universal_assignments
       assignment = UniversalAssignment(
           assignment_type="LOB Assignment",
           from_role="Data Executive",
           to_role="CDO",
           ...
       )
   ```

2. **Maintain Backward Compatibility**
   - Keep old endpoints working
   - Add deprecation headers
   - Log usage for monitoring

### Phase 4: Frontend Migration (Week 4)
1. **Update Components**
   - Notification components use universal API
   - Update queries to fetch from universal system
   - Maintain UI consistency

2. **Feature Enhancements**
   - Add delegation capability
   - Add escalation rules
   - Show richer task lifecycle

### Phase 5: Deprecation (Month 2)
1. **Monitor Usage**
   - Track calls to old endpoints
   - Ensure no critical dependencies

2. **Final Cutover**
   - Stop writing to old tables
   - Remove old endpoints
   - Archive old tables

## Implementation Details

### 1. Assignment Type Mapping
```python
NOTIFICATION_TO_ASSIGNMENT_MAP = {
    'cdo_notification': {
        'type': 'LOB Assignment',
        'from_role': 'Data Executive',
        'to_role': 'CDO',
        'priority': 'high',
        'sla_hours': 48
    },
    'data_owner_notification': {
        'type': 'Information Request',
        'from_role': 'Test Manager',
        'to_role': 'Data Provider',
        'priority': 'medium',
        'sla_hours': 72
    }
}
```

### 2. Status Mapping
```python
STATUS_MAP = {
    # Old → New
    'sent': 'assigned',
    'acknowledged': 'acknowledged',
    'in_progress': 'in_progress',
    'complete': 'completed',
    'cancelled': 'cancelled'
}
```

### 3. Context Preservation
Store original notification data in context field:
```json
{
    "migrated_from": "cdo_notifications",
    "original_id": 123,
    "notification_text": "Please review LOB assignment",
    "lob_id": 45,
    "migration_timestamp": "2025-01-07T..."
}
```

## Rollback Plan

### Database Rollback
```sql
-- Remove migrated records
DELETE FROM universal_assignments 
WHERE context->>'migrated_from' IN ('cdo_notifications', 'data_owner_notifications');

-- Tables remain intact, can resume using them
```

### Code Rollback
- Revert API endpoints to use old tables
- Revert frontend to use old endpoints
- All changes are feature-flagged

## Success Metrics

1. **Zero Data Loss**
   - All notifications migrated
   - All statuses preserved
   - All relationships maintained

2. **No Service Disruption**
   - Parallel operation ensures continuity
   - Gradual migration reduces risk

3. **Enhanced Functionality**
   - Users can now delegate tasks
   - Automatic escalation works
   - Better visibility into task lifecycle

## Timeline

- Week 2, Day 1-2: Implement parallel writes
- Week 2, Day 3-5: Test parallel operation
- Week 3, Day 1-2: Migrate historical data
- Week 3, Day 3-4: Update APIs
- Week 3, Day 5: Testing
- Week 4: Frontend updates
- Month 2: Monitor and deprecate

## Risk Mitigation

1. **Risk**: Data inconsistency during parallel writes
   - **Mitigation**: Use transactions, add reconciliation job

2. **Risk**: Performance impact
   - **Mitigation**: Batch migrations, run during off-hours

3. **Risk**: User confusion
   - **Mitigation**: Keep UI identical initially, gradual enhancement