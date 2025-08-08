# Universal Phase Status Framework V3 - With Activity Reset Feature

## New Requirement: Activity Reset Capability
- Tester can reset a completed activity back to "Active" state
- When an activity is reset, ALL subsequent activities are also reset
- Reset icon appears only on completed activities
- Small icon in the activity card itself

## Enhanced Solution Components

### 1. Backend - Activity Reset Logic

#### 1.1 Add Reset Method to ActivityStateTracker
```python
# app/core/activity_states.py - Add to ActivityStateTracker class

def reset_activity_cascade(self, activity_name: str, user_id: str) -> List[str]:
    """
    Reset an activity and all its dependent activities
    Returns list of reset activity names
    """
    if activity_name not in self.activities:
        return []
    
    activity = self.activities[activity_name]
    if activity["state"] != ActivityState.COMPLETED:
        return []  # Can only reset completed activities
    
    # Find all activities that depend on this one (direct and indirect)
    activities_to_reset = self._get_dependent_activities(activity_name)
    activities_to_reset.insert(0, activity_name)  # Include the activity itself
    
    # Reset each activity in reverse order (dependents first)
    reset_activities = []
    for act_name in reversed(activities_to_reset):
        act = self.activities[act_name]
        if act["state"] == ActivityState.COMPLETED:
            act["state"] = ActivityState.IN_PROGRESS
            act["completed_at"] = None
            act["completed_by"] = None
            # Add reset metadata
            if "reset_history" not in act:
                act["reset_history"] = []
            act["reset_history"].append({
                "reset_at": datetime.utcnow(),
                "reset_by": user_id,
                "previous_completed_at": act.get("completed_at")
            })
            reset_activities.append(act_name)
    
    return reset_activities

def _get_dependent_activities(self, activity_name: str) -> List[str]:
    """Get all activities that depend on the given activity"""
    dependents = []
    dependencies = ACTIVITY_DEPENDENCIES.get(self.phase_name, [])
    
    # Build dependency graph
    dep_map = {name: dep for name, dep in dependencies}
    
    # Find all activities that have this activity in their dependency chain
    for act_name, dep in dep_map.items():
        if self._has_dependency(act_name, activity_name, dep_map):
            dependents.append(act_name)
    
    return dependents

def _has_dependency(self, activity: str, target: str, dep_map: dict) -> bool:
    """Check if activity has target in its dependency chain"""
    current = dep_map.get(activity)
    while current:
        if current == target:
            return True
        current = dep_map.get(current)
    return False
```

#### 1.2 Add Reset Endpoint to Activity State Manager
```python
# app/services/activity_state_manager.py - Add method

async def reset_activity_cascade(
    self,
    cycle_id: str,
    report_id: str,
    phase_name: str,
    activity_name: str,
    user_id: str,
    user_role: str
) -> Dict[str, Any]:
    """Reset an activity and all dependent activities"""
    
    # Check permissions - only Tester and Test Manager can reset
    if user_role not in ["Tester", "Test Manager"]:
        return {
            "success": False,
            "error": "Only Tester or Test Manager can reset activities"
        }
    
    try:
        # Get phase and load tracker
        phase = await self._get_workflow_phase(cycle_id, report_id, phase_name)
        if not phase:
            return {"success": False, "error": "Phase not found"}
        
        tracker = self._load_activity_tracker(phase)
        
        # Perform cascade reset
        reset_activities = tracker.reset_activity_cascade(activity_name, user_id)
        
        if not reset_activities:
            return {
                "success": False,
                "error": "Activity cannot be reset or is not completed"
            }
        
        # Update phase state if needed
        if phase.state == 'Complete':
            phase.state = 'In Progress'
            phase.actual_end_date = None
            phase.completed_by = None
        
        # Save updated tracker
        await self._save_activity_tracker(phase, tracker)
        
        # Log the reset action
        logger.info(
            f"User {user_id} reset {len(reset_activities)} activities "
            f"in phase {phase_name} for cycle {cycle_id}, report {report_id}"
        )
        
        return {
            "success": True,
            "reset_activities": reset_activities,
            "message": f"Reset {len(reset_activities)} activities successfully"
        }
        
    except Exception as e:
        logger.error(f"Error resetting activities: {str(e)}")
        return {"success": False, "error": str(e)}
```

#### 1.3 Add API Endpoint
```python
# app/api/v1/endpoints/activity_states.py

@router.post("/activities/{activity_id}/reset")
async def reset_activity(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset an activity and all dependent activities"""
    
    manager = ActivityStateManager(db)
    result = await manager.reset_activity_cascade(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name=phase_name,
        activity_name=activity_id.replace('_', ' ').title(),
        user_id=current_user.user_id,
        user_role=current_user.role
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
```

### 2. Frontend - Enhanced Activity Card Component

#### 2.1 Update ActivityStatus Interface
```typescript
// hooks/useUnifiedStatus.ts
export interface ActivityStatus {
  activity_id: string;
  name: string;
  description: string;
  status: ActivityStatusType;
  can_start: boolean;
  can_complete: boolean;
  can_reset?: boolean;  // New field
  completion_percentage?: number;
  blocking_reason?: string;
  last_updated?: string;
  metadata?: {
    reset_history?: Array<{
      reset_at: string;
      reset_by: string;
      previous_completed_at?: string;
    }>;
    [key: string]: any;
  };
}
```

#### 2.2 Enhanced Dynamic Activity Card Component
```typescript
// components/phase/DynamicActivityCards.tsx
import { useState } from 'react';
import { 
  Card, CardContent, Box, Typography, Chip, Button, IconButton, 
  Tooltip, CircularProgress, Dialog, DialogTitle, DialogContent, 
  DialogActions, List, ListItem, ListItemText 
} from '@mui/material';
import { 
  RestartAlt as ResetIcon, 
  PlayArrow as StartIcon,
  CheckCircle as CompleteIcon,
  Warning as WarningIcon 
} from '@mui/icons-material';
import { ActivityStatus } from '../../hooks/useUnifiedStatus';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';
import { useNotifications } from '../../contexts/NotificationContext';

interface DynamicActivityCardsProps {
  activities: ActivityStatus[];
  cycleId: number;
  reportId: number;
  phaseName: string;
  onActivityAction?: (activity: ActivityStatus, action: string) => void;
  variant?: 'stepper' | 'cards' | 'timeline';
}

export const DynamicActivityCards: React.FC<DynamicActivityCardsProps> = ({
  activities,
  cycleId,
  reportId,
  phaseName,
  onActivityAction,
  variant = 'cards'
}) => {
  const queryClient = useQueryClient();
  const { showToast } = useNotifications();
  const [resetDialog, setResetDialog] = useState<{
    open: boolean;
    activity: ActivityStatus | null;
    affectedActivities: string[];
  }>({ open: false, activity: null, affectedActivities: [] });

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: async (activityId: string) => {
      const response = await apiClient.post(
        `/activity-states/activities/${activityId}/reset`,
        null,
        {
          params: { cycle_id: cycleId, report_id: reportId, phase_name: phaseName }
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      showToast('success', data.message || 'Activities reset successfully');
      // Invalidate phase status to refresh
      queryClient.invalidateQueries({ 
        queryKey: ['phaseStatus', phaseName, cycleId, reportId] 
      });
      setResetDialog({ open: false, activity: null, affectedActivities: [] });
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to reset activity');
    }
  });

  const handleResetClick = (activity: ActivityStatus) => {
    // Find all subsequent activities that would be affected
    const activityIndex = activities.findIndex(a => a.activity_id === activity.activity_id);
    const affectedActivities = activities
      .slice(activityIndex + 1)
      .filter(a => a.status === 'completed')
      .map(a => a.name);
    
    setResetDialog({
      open: true,
      activity,
      affectedActivities
    });
  };

  const handleResetConfirm = () => {
    if (resetDialog.activity) {
      resetMutation.mutate(resetDialog.activity.activity_id);
    }
  };

  const renderActivityCard = (activity: ActivityStatus) => {
    const canReset = activity.status === 'completed' && activity.can_reset !== false;
    
    return (
      <Card 
        key={activity.activity_id} 
        sx={{ 
          flex: '1 1 250px', 
          minWidth: 250,
          position: 'relative',
          transition: 'all 0.3s',
          '&:hover': {
            boxShadow: 3,
            transform: 'translateY(-2px)'
          }
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontSize: '0.9rem' }}>
                {activity.name}
              </Typography>
              <Chip 
                label={formatStatusText(activity.status)} 
                color={getStatusColor(activity.status)}
                size="small"
                sx={{ mt: 0.5 }}
              />
            </Box>
            {canReset && (
              <Tooltip title="Reset this activity and all subsequent activities">
                <IconButton
                  size="small"
                  onClick={() => handleResetClick(activity)}
                  sx={{ 
                    ml: 1,
                    color: 'warning.main',
                    '&:hover': { backgroundColor: 'warning.light', color: 'warning.dark' }
                  }}
                >
                  <ResetIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {activity.description}
          </Typography>
          
          {/* Show reset history if exists */}
          {activity.metadata?.reset_history && activity.metadata.reset_history.length > 0 && (
            <Typography variant="caption" color="warning.main" sx={{ display: 'block', mt: 1 }}>
              <WarningIcon sx={{ fontSize: 12, verticalAlign: 'middle', mr: 0.5 }} />
              Previously reset {activity.metadata.reset_history.length} time(s)
            </Typography>
          )}
          
          {/* Action buttons */}
          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
            {activity.can_start && (
              <Button 
                size="small" 
                startIcon={<StartIcon />}
                onClick={() => onActivityAction?.(activity, 'start')}
                variant="outlined"
              >
                Start
              </Button>
            )}
            {activity.can_complete && (
              <Button 
                size="small" 
                color="success"
                startIcon={<CompleteIcon />}
                onClick={() => onActivityAction?.(activity, 'complete')}
                variant="contained"
              >
                Complete
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  };

  return (
    <>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        {activities.map(activity => renderActivityCard(activity))}
      </Box>
      
      {/* Reset Confirmation Dialog */}
      <Dialog 
        open={resetDialog.open} 
        onClose={() => setResetDialog({ open: false, activity: null, affectedActivities: [] })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon color="warning" />
            Reset Activity Confirmation
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to reset "{resetDialog.activity?.name}"?
          </Typography>
          
          {resetDialog.affectedActivities.length > 0 && (
            <>
              <Typography variant="body2" color="warning.main" sx={{ mt: 2, mb: 1 }}>
                This will also reset the following completed activities:
              </Typography>
              <List dense sx={{ bgcolor: 'warning.light', borderRadius: 1, p: 1 }}>
                {resetDialog.affectedActivities.map((name, idx) => (
                  <ListItem key={idx}>
                    <ListItemText 
                      primary={name}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          )}
          
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            Note: You will need to complete these activities again to finish the phase.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setResetDialog({ open: false, activity: null, affectedActivities: [] })}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleResetConfirm} 
            color="warning"
            variant="contained"
            disabled={resetMutation.isPending}
            startIcon={resetMutation.isPending ? <CircularProgress size={16} /> : <ResetIcon />}
          >
            Reset Activities
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
```

### 3. Update Backend to Include can_reset Flag

```python
# app/services/unified_status_service.py - Update activity conversion

activities.append(ActivityStatus(
    activity_id=activity_name.replace(' ', '_').lower(),
    name=activity_name,
    description=f"{activity_name} for {phase_name}",
    status=self._map_activity_state(activity_data['state']),
    can_start=activity_data['state'] == 'Not Started',
    can_complete=activity_data['state'] == 'In Progress',
    can_reset=activity_data['state'] == 'Completed',  # Add this
    completion_percentage=100 if activity_data['state'] == 'Completed' else 0,
    last_updated=activity_data.get('completed_at') or activity_data.get('started_at'),
    metadata={
        'started_by': activity_data.get('started_by'),
        'completed_by': activity_data.get('completed_by'),
        'reset_history': activity_data.get('reset_history', [])
    }
))
```

## Benefits of Reset Feature
1. **Flexibility** - Testers can correct mistakes without starting over
2. **Cascade Logic** - Ensures workflow integrity by resetting dependents
3. **Audit Trail** - Reset history tracked for compliance
4. **User-Friendly** - Simple icon click with clear confirmation
5. **Permission Controlled** - Only Tester/Test Manager roles can reset

## Implementation Notes
- Reset only available for completed activities
- Reset cascades to all dependent activities automatically
- Phase state updates if it was previously completed
- Full audit trail maintained
- Real-time UI updates via React Query invalidation

## Testing the Reset Feature
1. Complete several activities in sequence
2. Click reset icon on an earlier activity
3. Verify confirmation dialog shows affected activities
4. Confirm reset and verify all affected activities change to "In Progress"
5. Check that phase status updates appropriately
6. Verify reset history is tracked in activity metadata