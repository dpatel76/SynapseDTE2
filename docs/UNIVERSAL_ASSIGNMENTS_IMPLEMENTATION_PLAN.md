# Universal Assignments Implementation Plan

## Executive Summary

This document outlines the plan to implement Universal Assignments consistently across all phase detail pages in the SynapseDTE application. Currently, only 2 out of 9 phase pages utilize Universal Assignments, creating an inconsistent user experience.

## Current State Analysis

### Phase Pages Using Universal Assignments ✅
1. **SampleSelectionPage.tsx**
   - Correctly checks for universal assignments for Report Owners
   - Uses `/universal-assignments/assignments` API with proper filtering
   
2. **DataProfilingEnhanced.tsx**
   - Checks for universal assignments for "Rule Approval" assignment type
   - Properly handles Report Owner assignments

### Phase Pages NOT Using Universal Assignments ❌
1. **SimplifiedPlanningPage.tsx** - No integration
2. **ScopingPage.tsx** - No integration
3. **DataOwnerPage.tsx** - No integration
4. **NewRequestInfoPage.tsx** - No integration
5. **TestExecutionPage.tsx** - No integration
6. **ObservationManagementEnhanced.tsx** - No integration
7. **TestReportPage.tsx** - No integration

### Fixed Issues
1. **MyAssignmentsPage.tsx** - Now properly uses Universal Assignments API
2. **Removed extra left padding** - Fixed with `sx={{ p: 0 }}`

## Universal Assignments Benefits

1. **Unified System**: Single system for all assignments instead of multiple tables
2. **Flexibility**: Can handle any type of assignment without schema changes
3. **Traceability**: Complete audit trail for compliance
4. **Automation**: Integrated with workflow for automatic assignment creation
5. **Context-Aware**: Smart routing based on assignment context
6. **Role-Based**: Works with role hierarchy, not just individual users

## Implementation Plan

### Phase 1: Create Reusable Hook (Week 1)

Create `useUniversalAssignments` hook in `/frontend/src/hooks/useUniversalAssignments.ts`:

```typescript
interface UseUniversalAssignmentsOptions {
  phase: string;
  cycleId: number;
  reportId: number;
  autoNavigate?: boolean;
}

export const useUniversalAssignments = (options: UseUniversalAssignmentsOptions) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // Check for assignments related to this phase
  const { data: assignments, isLoading } = useQuery({
    queryKey: ['universal-assignments', options.phase, options.cycleId, options.reportId],
    queryFn: async () => {
      const response = await apiClient.get('/universal-assignments/assignments', {
        params: {
          user_id: user?.user_id,
          context_type: 'Report',
          context_filter: {
            cycle_id: options.cycleId,
            report_id: options.reportId,
            phase_name: options.phase
          }
        }
      });
      return response.data || [];
    },
    enabled: !!user?.user_id && !!options.cycleId && !!options.reportId
  });
  
  // Extract current assignment if any
  const currentAssignment = assignments?.find(a => 
    a.status !== 'completed' && a.status !== 'approved'
  );
  
  return {
    hasAssignment: !!currentAssignment,
    assignment: currentAssignment,
    isLoading,
    canDirectAccess: !currentAssignment || user?.role === 'Admin'
  };
};
```

### Phase 2: Update Each Phase Page (Weeks 2-3)

For each phase page, add Universal Assignment integration:

#### Example Pattern for SimplifiedPlanningPage.tsx:

```typescript
const SimplifiedPlanningPage: React.FC = () => {
  const { cycleId, reportId } = useParams();
  const { hasAssignment, assignment, canDirectAccess } = useUniversalAssignments({
    phase: 'Planning',
    cycleId: parseInt(cycleId),
    reportId: parseInt(reportId)
  });
  
  // Show assignment context if user came from assignment
  {hasAssignment && (
    <Alert severity="info" sx={{ mb: 2 }}>
      <AlertTitle>Assignment: {assignment.title}</AlertTitle>
      {assignment.description}
      {assignment.due_date && (
        <Typography variant="caption" display="block">
          Due: {format(new Date(assignment.due_date), 'MMM dd, yyyy')}
        </Typography>
      )}
    </Alert>
  )}
  
  // Rest of component...
};
```

### Phase 3: Assignment Type Mapping (Week 4)

Create mapping for automatic assignment creation:

| Phase | Assignment Types |
|-------|-----------------|
| Planning | Attribute Approval, Planning Review |
| Data Profiling | Rule Approval, Profile Review |
| Scoping | Scoping Approval, Scope Review |
| Sample Selection | Sample Approval, LOB Assignment |
| Data Owner | Data Upload Request, Data Review |
| Request Info | Information Request, Test Case Review |
| Test Execution | Test Execution Review, Result Validation |
| Observation Management | Observation Approval, Finding Review |
| Finalize Test Report | Report Approval, Final Review |

### Phase 4: Workflow Integration (Week 5)

Update workflow orchestrator to create assignments automatically:

```python
# In workflow_orchestrator.py
async def advance_phase(self, from_phase: str, to_phase: str):
    # Existing phase advancement logic...
    
    # Create universal assignment for next phase
    assignment_mappings = {
        "Planning": ("Attribute Approval", "Tester", "Test Executive"),
        "Scoping": ("Scoping Approval", "Tester", "Report Owner"),
        "Sample Selection": ("LOB Assignment", "Test Executive", "Data Executive"),
        # ... etc
    }
    
    if to_phase in assignment_mappings:
        assignment_type, from_role, to_role = assignment_mappings[to_phase]
        await self.assignment_service.create_assignment(
            assignment_type=assignment_type,
            from_role=from_role,
            to_role=to_role,
            title=f"{to_phase} Phase Tasks",
            context_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "phase_name": to_phase
            }
        )
```

### Phase 5: Testing & Validation (Week 6)

1. **Unit Tests**: Test the useUniversalAssignments hook
2. **Integration Tests**: Test assignment creation on phase transitions
3. **E2E Tests**: Test complete workflow with assignments
4. **UAT**: Validate with each role type

## Migration Strategy

### Backward Compatibility
- Keep direct access available when no assignments exist
- Maintain existing permissions and role checks
- Phase pages continue to work without assignments

### Data Migration
- No data migration needed - Universal Assignments is additive
- Existing workflows continue to function
- New assignments created going forward

## Success Metrics

1. **Consistency**: All 9 phase pages use Universal Assignments
2. **Traceability**: 100% of phase transitions tracked via assignments
3. **User Satisfaction**: Reduced confusion about task ownership
4. **Compliance**: Complete audit trail for all work items

## Timeline

- **Week 1**: Create reusable hook and utilities
- **Weeks 2-3**: Update all phase pages
- **Week 4**: Configure assignment type mappings
- **Week 5**: Integrate with workflow orchestrator
- **Week 6**: Testing and validation
- **Week 7**: Deployment and monitoring

## Risk Mitigation

1. **Performance**: Use React Query caching to minimize API calls
2. **Complexity**: Start with simple assignment checks, add features incrementally
3. **User Training**: Create documentation and tooltips explaining assignments
4. **Rollback Plan**: Feature flag to disable Universal Assignments if needed

## Next Steps

1. Review and approve this plan
2. Create the useUniversalAssignments hook
3. Start with SimplifiedPlanningPage.tsx as pilot
4. Roll out to remaining pages based on priority

## Appendix: Assignment Context Structure

```typescript
interface AssignmentContext {
  cycle_id: number;
  report_id: number;
  phase_name: string;
  attribute_ids?: number[];
  sample_ids?: number[];
  lob_names?: string[];
  test_case_ids?: number[];
  observation_ids?: number[];
  custom_data?: Record<string, any>;
}
```

This flexible context structure allows assignments to carry all necessary information for users to complete their tasks effectively.