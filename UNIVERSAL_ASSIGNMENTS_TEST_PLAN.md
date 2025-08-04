# Universal Assignments Testing & Validation Plan

## Overview
This document outlines the comprehensive testing strategy for the Universal Assignments implementation across the SynapseDTE application.

## Test Scenarios

### 1. Component Integration Tests

#### 1.1 Hook Functionality
- **Test**: Verify `useUniversalAssignments` hook correctly fetches assignments
- **Steps**:
  1. Navigate to any phase detail page
  2. Check that assignments are loaded based on user role and phase
  3. Verify assignment filtering by status, priority, and due date
- **Expected**: Hook returns relevant assignments for the current context

#### 1.2 Assignment Alert Display
- **Test**: Verify `UniversalAssignmentAlert` component displays correctly
- **Steps**:
  1. Create a test assignment for a user
  2. Navigate to the relevant phase page
  3. Verify alert appears at top of page with correct information
- **Expected**: Alert shows title, description, priority, due date, and actions

#### 1.3 Assignment Actions
- **Test**: Verify acknowledge, start, and complete actions work
- **Steps**:
  1. Click "Acknowledge" on an assignment
  2. Verify status updates to "acknowledged"
  3. Click "Start Task" and verify status updates to "in_progress"
  4. Click "Mark Complete" and verify status updates to "completed"
- **Expected**: Each action updates assignment status correctly

### 2. Workflow Integration Tests

#### 2.1 Phase Start Assignment Creation
- **Test**: Verify assignments are created when starting a phase
- **Steps**:
  1. Navigate to Planning phase as Tester
  2. Click "Start Phase"
  3. Check that review assignment is created for Test Manager
- **Expected**: Appropriate assignments created based on configuration

#### 2.2 Submission Flow
- **Test**: Verify submission creates review assignments
- **Steps**:
  1. Complete Scoping decisions as Tester
  2. Submit for approval
  3. Verify Test Manager receives review assignment
  4. Verify Report Owner receives approval assignment
- **Expected**: Chain of assignments created for approval workflow

#### 2.3 Assignment Dependencies
- **Test**: Verify dependent assignments are created
- **Steps**:
  1. Complete a documentation request as Data Provider
  2. Verify Tester receives review notification
- **Expected**: Auto-assignments created based on completion

### 3. Role-Based Testing

#### 3.1 Tester Role
- **Assignments to verify**:
  - Can create planning review assignments
  - Can create scoping submission assignments
  - Can create documentation requests
  - Receives revision assignments from Test Manager

#### 3.2 Test Manager Role
- **Assignments to verify**:
  - Receives planning review assignments
  - Receives scoping review assignments
  - Can create revision requests
  - Can escalate to Report Owner

#### 3.3 Data Provider Role
- **Assignments to verify**:
  - Receives documentation requests
  - Receives data owner assignments from CDO
  - Can submit clarification responses

#### 3.4 Report Owner Role
- **Assignments to verify**:
  - Receives approval requests
  - Receives observation ratings
  - Can escalate to Executive

#### 3.5 CDO Role
- **Assignments to verify**:
  - Receives LOB assignment requests
  - Can assign data owners

#### 3.6 Report Owner Executive Role
- **Assignments to verify**:
  - Receives critical escalations
  - Receives final approvals

### 4. SLA and Priority Testing

#### 4.1 SLA Calculation
- **Test**: Verify due dates are calculated correctly
- **Steps**:
  1. Create assignments with different SLA hours
  2. Verify due dates match configuration
- **Expected**: Due dates = creation time + SLA hours

#### 4.2 Overdue Handling
- **Test**: Verify overdue assignments are highlighted
- **Steps**:
  1. Create assignment with past due date
  2. Verify "Overdue" chip appears
  3. Verify warning color in alert
- **Expected**: Visual indicators for overdue assignments

#### 4.3 Priority Display
- **Test**: Verify priority colors and ordering
- **Steps**:
  1. Create assignments with different priorities
  2. Verify color coding matches configuration
- **Expected**: Critical=red, Urgent=red, High=orange, Medium=blue, Low=green

### 5. Error Handling Tests

#### 5.1 API Failures
- **Test**: Verify graceful handling of API errors
- **Steps**:
  1. Simulate API failure for assignment fetch
  2. Verify error message displayed
  3. Verify retry functionality
- **Expected**: User-friendly error messages and recovery options

#### 5.2 Permission Errors
- **Test**: Verify handling of unauthorized actions
- **Steps**:
  1. Attempt to complete assignment for wrong user
  2. Verify error message
- **Expected**: Clear permission error messages

### 6. Performance Tests

#### 6.1 Load Testing
- **Test**: Verify performance with many assignments
- **Steps**:
  1. Create 100+ assignments for a user
  2. Measure page load time
  3. Verify pagination/filtering works
- **Expected**: Page loads within 2 seconds

#### 6.2 Real-time Updates
- **Test**: Verify assignment updates reflect quickly
- **Steps**:
  1. Open same phase in two browser tabs
  2. Complete assignment in one tab
  3. Verify update appears in other tab within 5 seconds
- **Expected**: Near real-time updates via React Query

### 7. Integration Testing Checklist

For each phase page, verify:
- [ ] UniversalAssignmentAlert appears when assignments exist
- [ ] Assignment actions (acknowledge, start, complete) work
- [ ] Phase-specific workflows create correct assignments
- [ ] Assignment completion triggers follow-up assignments
- [ ] Error states handled gracefully
- [ ] Performance is acceptable

### 8. Manual Test Script

1. **Setup**:
   - Create test cycle and report
   - Create test users for each role
   - Navigate to cycle/report workflow

2. **Planning Phase**:
   - Start phase as Tester
   - Verify Test Manager gets review assignment
   - Complete planning phase

3. **Scoping Phase**:
   - Make scoping decisions as Tester
   - Submit for approval
   - Verify approval chain (Test Manager → Report Owner)

4. **Data Owner Phase**:
   - Verify CDO gets LOB assignment
   - Assign data owners
   - Verify data owners get notifications

5. **Request Info Phase**:
   - Start phase as Tester
   - Verify data owners get documentation requests
   - Submit documentation
   - Request revisions

6. **Test Execution Phase**:
   - Execute tests
   - Request clarifications
   - Complete test cases

7. **Observation Management**:
   - Create observations
   - Request ratings
   - Get approvals

8. **Finalize Report**:
   - Generate report
   - Submit for approval
   - Get executive sign-off

## Automated Testing

### Unit Tests
```typescript
// Example test for useUniversalAssignments hook
describe('useUniversalAssignments', () => {
  it('should fetch assignments for current phase', async () => {
    const { result } = renderHook(() => 
      useUniversalAssignments({
        phase: 'Planning',
        cycleId: 1,
        reportId: 1
      })
    );
    
    await waitFor(() => {
      expect(result.current.assignments).toHaveLength(1);
      expect(result.current.assignments[0].assignment_type).toBe('planning_review');
    });
  });
});
```

### Integration Tests
```typescript
// Example test for workflow integration
describe('Workflow Integration', () => {
  it('should create assignment on phase submission', async () => {
    // Setup
    const user = userEvent.setup();
    render(<ScopingPage />);
    
    // Make decisions and submit
    await user.click(screen.getByText('Submit Decisions'));
    
    // Verify assignment created
    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/universal-assignments/assignments',
        expect.objectContaining({
          assignment_type: 'scoping_submission'
        })
      );
    });
  });
});
```

## Success Criteria

1. All phase pages display Universal Assignments alerts
2. Assignment lifecycle (create → acknowledge → start → complete) works
3. Role-based assignment routing functions correctly
4. SLA and priority features work as configured
5. Workflow integrations create appropriate assignments
6. Performance meets requirements (< 2s load time)
7. Error handling provides good user experience
8. All manual test scenarios pass
9. Automated tests provide > 80% coverage

## Rollback Plan

If issues are discovered:
1. Disable Universal Assignments feature flag
2. Remove UniversalAssignmentAlert components from pages
3. Revert workflow integration changes
4. Restore previous assignment mechanisms

## Post-Deployment Monitoring

1. Monitor API error rates for /universal-assignments endpoints
2. Track assignment completion rates
3. Monitor page load performance
4. Collect user feedback on new assignment system
5. Track SLA compliance rates