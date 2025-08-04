# Universal Phase Status Framework V2 - Leveraging Existing Infrastructure

## Discovered Existing Backend Components
1. **ActivityStateTracker** - Complete phase-to-activity mapping in `app/core/activity_states.py`
2. **PHASE_ACTIVITIES** - Database of all activities per phase
3. **ACTIVITY_DEPENDENCIES** - Defines activity order and relationships
4. **ActivityStateManager** - Handles state transitions and date tracking

## Root Problem
UnifiedStatusService is NOT using the ActivityStateTracker system, creating dual sources of truth.

## Enhanced Solution - Integration Approach

### Phase 1: Backend Integration (2 days)

#### 1.1 Update UnifiedStatusService to use ActivityStateTracker
```python
# app/services/unified_status_service.py

from app.core.activity_states import ActivityStateTracker, PHASE_ACTIVITIES
from app.services.activity_state_manager import ActivityStateManager

async def _get_phase_status_generic(self, phase_name: str, cycle_id: int, report_id: int) -> PhaseStatus:
    """Generic phase status using ActivityStateTracker"""
    workflow_phase = await self._get_workflow_phase(phase_name, cycle_id, report_id)
    
    # Load activity tracker
    tracker = ActivityStateTracker(phase_name)
    if workflow_phase and workflow_phase.phase_data:
        # Load saved state
        tracker.activities = workflow_phase.phase_data.get('activities', tracker.activities)
    
    # Convert to unified format
    activities = []
    for activity_name, activity_data in tracker.activities.items():
        activities.append(ActivityStatus(
            activity_id=activity_name.replace(' ', '_').lower(),
            name=activity_name,
            description=f"{activity_name} for {phase_name}",
            status=self._map_activity_state(activity_data['state']),
            can_start=activity_data['state'] == 'Not Started',
            can_complete=activity_data['state'] == 'In Progress',
            completion_percentage=100 if activity_data['state'] == 'Completed' else 0,
            last_updated=activity_data.get('completed_at') or activity_data.get('started_at'),
            metadata={
                'started_by': activity_data.get('started_by'),
                'completed_by': activity_data.get('completed_by')
            }
        ))
    
    # Update workflow phase dates automatically
    if workflow_phase:
        await self._sync_phase_dates(workflow_phase, tracker)
    
    return PhaseStatus(
        phase_name=phase_name,
        cycle_id=cycle_id,
        report_id=report_id,
        phase_status=self._calculate_phase_status(tracker),
        overall_completion_percentage=tracker.get_phase_progress()['completion_percentage'],
        activities=activities,
        can_proceed_to_next=all(a['state'] == 'Completed' for a in tracker.activities.values()),
        blocking_issues=self._get_blocking_issues(tracker),
        last_updated=datetime.utcnow()
    )
```

#### 1.2 Add Automatic Date Syncing
```python
async def _sync_phase_dates(self, workflow_phase: WorkflowPhase, tracker: ActivityStateTracker):
    """Automatically sync phase dates from activity tracker"""
    updates_needed = False
    
    # Find first started activity
    first_started = min(
        (a for a in tracker.activities.values() if a['started_at']),
        key=lambda x: x['started_at'],
        default=None
    )
    
    if first_started and not workflow_phase.actual_start_date:
        workflow_phase.actual_start_date = first_started['started_at']
        workflow_phase.started_by = first_started['started_by']
        updates_needed = True
    
    # Check if all activities completed
    all_completed = all(a['state'] == 'Completed' for a in tracker.activities.values())
    if all_completed and not workflow_phase.actual_end_date:
        last_completed = max(
            (a for a in tracker.activities.values() if a['completed_at']),
            key=lambda x: x['completed_at']
        )
        workflow_phase.actual_end_date = last_completed['completed_at']
        workflow_phase.completed_by = last_completed['completed_by']
        workflow_phase.state = 'Complete'
        updates_needed = True
    
    if updates_needed:
        await self.db.commit()
```

### Phase 2: Frontend Dynamic Activity Component (1 day)

#### 2.1 Create Generic Activity Card Component
```typescript
// components/phase/DynamicActivityCards.tsx
import { ActivityStatus } from '../../hooks/useUnifiedStatus';

interface DynamicActivityCardsProps {
  activities: ActivityStatus[];
  onActivityAction?: (activity: ActivityStatus, action: string) => void;
  variant?: 'stepper' | 'cards' | 'timeline';
}

export const DynamicActivityCards: React.FC<DynamicActivityCardsProps> = ({
  activities,
  onActivityAction,
  variant = 'cards'
}) => {
  const renderCards = () => (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
      {activities.map((activity) => (
        <Card key={activity.activity_id} sx={{ flex: '1 1 250px', minWidth: 250 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <Typography variant="h6" sx={{ fontSize: '0.9rem' }}>
                {activity.name}
              </Typography>
              <Chip 
                label={formatStatusText(activity.status)} 
                color={getStatusColor(activity.status)}
                size="small"
              />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {activity.description}
            </Typography>
            {activity.can_start && (
              <Button 
                size="small" 
                onClick={() => onActivityAction?.(activity, 'start')}
                sx={{ mt: 2 }}
              >
                Start Activity
              </Button>
            )}
            {activity.can_complete && (
              <Button 
                size="small" 
                color="success"
                onClick={() => onActivityAction?.(activity, 'complete')}
                sx={{ mt: 2 }}
              >
                Mark Complete
              </Button>
            )}
          </CardContent>
        </Card>
      ))}
    </Box>
  );
  
  // Support different display variants
  switch (variant) {
    case 'stepper':
      return <ActivityStepper activities={activities} onAction={onActivityAction} />;
    case 'timeline':
      return <ActivityTimeline activities={activities} onAction={onActivityAction} />;
    default:
      return renderCards();
  }
};
```

### Phase 3: Update All Phase Pages (3 days)

#### 3.1 Replace Hardcoded Activities
For each phase page:
```typescript
// Before - Hardcoded
const getPlanningSteps = () => { /* hardcoded steps */ };

// After - Dynamic from API
const { data: phaseStatus } = usePhaseStatus('Planning', cycleId, reportId);

// In render
<DynamicActivityCards 
  activities={phaseStatus?.activities || []}
  onActivityAction={handleActivityAction}
  variant="cards"
/>
```

### Phase 4: Update Overview Page (1 day)

#### 4.1 Use useAllPhasesStatus Hook
```typescript
// ReportTestingPageRedesigned.tsx
const { data: allPhases } = useAllPhasesStatus(cycleId, reportId);

// Convert to phase cards
const phaseCards = Object.entries(allPhases || {}).map(([phaseName, phaseStatus]) => ({
  phase_name: phaseName,
  display_name: phaseDisplayNames[phaseName],
  state: phaseStatus.phase_status === 'completed' ? 'Complete' : 
         phaseStatus.phase_status === 'in_progress' ? 'In Progress' : 'Not Started',
  status: calculateScheduleStatus(phaseStatus), // On Track, At Risk, etc.
  progress: phaseStatus.overall_completion_percentage,
  // Dates will be populated from backend
  actual_start_date: phaseStatus.metadata?.started_at,
  actual_end_date: phaseStatus.metadata?.completed_at,
  route_name: phaseRouteMapping[phaseName]
}));
```

### Phase 5: Other Pages Using Status (1 day)

#### 5.1 Test Cycle Details Page
Check and update `CycleDetailPage.tsx` to use unified status

#### 5.2 Dashboard Pages
Update any dashboard that shows phase status

## Benefits Over Previous Plan
1. **Leverages Existing Backend** - No need to rebuild activity mapping
2. **Automatic Date Tracking** - Dates sync from activity tracker
3. **Database-Driven** - Activities come from PHASE_ACTIVITIES constant
4. **Single Source of Truth** - ActivityStateTracker is the authority
5. **Backwards Compatible** - Existing APIs continue to work

## Implementation Order
1. Backend Integration - UnifiedStatusService uses ActivityStateTracker
2. Create DynamicActivityCards component
3. Update one phase page as proof of concept (SimplifiedPlanningPage)
4. Update overview page to use unified status
5. Roll out to remaining 8 phase pages
6. Update test cycle details and other pages
7. Remove old hardcoded functions

## Testing Strategy
1. Unit tests for ActivityStateTracker integration
2. Component tests for DynamicActivityCards
3. Integration tests for date syncing
4. E2E tests for complete workflow

## Migration Risks & Mitigation
- **Risk**: Breaking existing functionality
- **Mitigation**: Feature flag to toggle between old/new implementation
- **Risk**: Performance impact
- **Mitigation**: Cache activity state in phase_data JSONB field