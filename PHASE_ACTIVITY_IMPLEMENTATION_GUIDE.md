# Phase Activity Implementation Guide

## Key Learnings from Planning Phase Implementation

### 1. Activity Status Management
- Activities are displayed using the unified status service (`usePhaseStatus` hook)
- Activity statuses must be properly sequenced - later activities can't start until earlier ones complete
- The backend `unified_status_service.py` controls activity status logic

### 2. Button Text Logic
- "Start Phase" button text for activities that start a phase (e.g., "Start Planning Phase")
- "Complete Phase" button text for activities that complete a phase (e.g., "Complete Planning Phase")
- Regular "Start"/"Complete" for other activities

### 3. API Integration Pattern
- Phase-level activities (Start/Complete Phase) should use phase-specific endpoints:
  - `/planning/cycles/{cycle_id}/reports/{report_id}/start`
  - `/planning/cycles/{cycle_id}/reports/{report_id}/complete`
- Other activities may use custom handlers or show informational messages
- No generic activity transition endpoints exist - each phase handles its own logic

### 4. Backend Phase Status Updates
- When starting a phase, must check if WorkflowPhase record exists
- If exists with "Not Started" status, update to "In Progress"
- If doesn't exist, create new record with "In Progress" status
- Must update both `status` and `state` fields, plus timestamps

### 5. Frontend Refresh Pattern
```typescript
// After any activity action, refresh both status systems
await refetchStatus();      // Unified status
await loadPhaseStatus();    // Phase-specific status
```

### 6. Error Handling
- Pydantic schemas require all fields - check schema definitions
- Use appropriate toast notifications (success, warning, error)
- Handle specific activity types with custom logic

## Implementation Checklist for Other Phases

### For Each Phase Page:
1. **Update handleActivityAction**
   - Map phase start/complete activities to correct endpoints
   - Add custom handlers for phase-specific activities
   - Use informational messages for manual activities

2. **Fix Button Text**
   - Ensure DynamicActivityCards shows correct text based on activity type
   - "Start Phase" for phase start activities
   - "Complete Phase" for phase complete activities

3. **Update Backend Endpoints**
   - Ensure start endpoint updates existing "Not Started" phases
   - Return all required fields for response schemas
   - Handle phase state transitions properly

4. **Verify Activity Sequencing**
   - Check unified_status_service.py for correct dependencies
   - Ensure `can_start` logic enforces proper sequence
   - Activities should only be startable when prerequisites are met

## Phases to Update:
1. ✅ Planning - Complete
2. ⏳ Scoping
3. ⏳ Data Profiling  
4. ⏳ Sample Selection
5. ⏳ Data Provider ID
6. ⏳ Request Info
7. ⏳ Test Execution
8. ⏳ Observations
9. ⏳ Finalize Test Report