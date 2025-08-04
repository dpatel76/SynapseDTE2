# Universal Phase Status Framework

## Problem Statement
- Multiple status systems causing inconsistencies
- Hardcoded activity cards across all phase pages
- Missing date tracking for some phases
- No single source of truth for phase/activity status

## Root Causes Identified
1. **Dual API Systems**: 
   - Workflow API (`/api/workflow/`) - Used by overview page
   - Universal Status API (`/status/`) - Used by phase detail pages
   - No synchronization between them

2. **Date Tracking Gaps**:
   - `actual_start_date` and `actual_end_date` not consistently set
   - Some phases update dates (Planning, Scoping) others don't
   - Manual process prone to errors

3. **Hardcoded Activities**:
   - All 9 phases have hardcoded `getXXXSteps()` functions
   - Activities array from Universal Status API is ignored
   - Maintenance nightmare

## Proposed Solution

### 1. Single Source of Truth
Use ONLY the Universal Status API for all status information:
- Overview page should use `useAllPhasesStatus()` hook
- Phase pages continue using `usePhaseStatus()` hook
- Remove dependency on Workflow API for status

### 2. Dynamic Activity Cards Component
Create a reusable component that renders activities dynamically:

```typescript
// components/phase/DynamicActivityCards.tsx
interface DynamicActivityCardsProps {
  activities: ActivityStatus[];
  onActivityClick?: (activity: ActivityStatus) => void;
}

export const DynamicActivityCards: React.FC<DynamicActivityCardsProps> = ({
  activities,
  onActivityClick
}) => {
  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
      {activities.map((activity) => (
        <ActivityCard
          key={activity.activity_id}
          activity={activity}
          onClick={() => onActivityClick?.(activity)}
        />
      ))}
    </Box>
  );
};
```

### 3. Automatic Date Tracking
Implement middleware/service to automatically set dates:

```typescript
// services/phaseTracking.ts
export const trackPhaseTransition = async (
  phaseId: string,
  newStatus: PhaseStatusType,
  userId: number
) => {
  const updates: any = {};
  
  // Automatically set start date
  if (newStatus === 'in_progress' && !phase.actual_start_date) {
    updates.actual_start_date = new Date();
    updates.started_by = userId;
  }
  
  // Automatically set end date
  if (newStatus === 'completed' && !phase.actual_end_date) {
    updates.actual_end_date = new Date();
    updates.completed_by = userId;
  }
  
  await updatePhase(phaseId, updates);
};
```

### 4. Migration Plan

#### Phase 1: Update Overview Page (1 day)
- Replace `workflowApi.getWorkflowStatus()` with `useAllPhasesStatus()`
- Map Universal Status data to existing UI components
- Ensure backward compatibility

#### Phase 2: Create Dynamic Components (2 days)
- Build `DynamicActivityCards` component
- Build `ActivityCard` component with status indicators
- Add activity action handlers

#### Phase 3: Update Phase Pages (3 days)
- Replace hardcoded `getXXXSteps()` with `DynamicActivityCards`
- Remove static activity definitions
- Test each phase thoroughly

#### Phase 4: Implement Auto Date Tracking (2 days)
- Add date tracking to status update endpoints
- Ensure all status changes trigger date updates
- Add audit logging

## Benefits
1. **Single Source of Truth**: All status from Universal Status API
2. **Maintainability**: No more hardcoded activities
3. **Consistency**: Same status everywhere
4. **Automatic Tracking**: Dates always populated
5. **Extensibility**: Easy to add new activities

## Implementation Checklist
- [ ] Update ReportTestingPageRedesigned to use useAllPhasesStatus
- [ ] Create DynamicActivityCards component
- [ ] Update SimplifiedPlanningPage
- [ ] Update DataProfilingEnhanced
- [ ] Update ScopingPage
- [ ] Update SampleSelectionPage
- [ ] Update DataOwnerPage
- [ ] Update NewRequestInfoPage
- [ ] Update TestExecutionPage
- [ ] Update ObservationManagementEnhanced
- [ ] Update TestReportPage
- [ ] Implement automatic date tracking
- [ ] Add comprehensive tests
- [ ] Update documentation