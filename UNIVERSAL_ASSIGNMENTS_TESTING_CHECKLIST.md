# Universal Assignments Testing Checklist

## Backend API Testing

### 1. Assignment Creation
- [ ] Create assignment via API with all required fields
- [ ] Verify assignment appears in database
- [ ] Check audit log entry is created
- [ ] Verify email notification is sent (if configured)

### 2. Assignment Lifecycle
- [ ] Acknowledge assignment (status: Assigned → Acknowledged)
- [ ] Start assignment (status: Acknowledged → In Progress)
- [ ] Complete assignment (status: In Progress → Completed)
- [ ] Verify timestamps are recorded correctly

### 3. Assignment Querying
- [ ] Filter by user (to_user_id)
- [ ] Filter by status (Assigned, Acknowledged, In Progress, etc.)
- [ ] Filter by context (cycle_id, report_id, phase_name)
- [ ] Verify pagination works correctly

### 4. Metrics & Reporting
- [ ] Get user metrics (total, completed, in progress, completion rate)
- [ ] Get phase-level metrics
- [ ] Verify overdue assignments are flagged correctly

## Frontend Testing

### 1. Test Page (`/test-universal-assignments`)
- [ ] Navigate to test page
- [ ] Click "Create Test Assignment"
- [ ] Verify assignment appears in list
- [ ] Click "Fetch Metrics" and verify response
- [ ] Test acknowledge, start, complete buttons

### 2. Phase Page Integration (Test each of 9 phases)

#### Planning Phase (`/cycles/{id}/reports/{id}/planning`)
- [ ] Verify assignments appear at top of page
- [ ] Test assignment actions work
- [ ] Verify page still loads if no assignments

#### Data Profiling Phase (`/cycles/{id}/reports/{id}/data-profiling`)
- [ ] Verify assignments appear at top of page
- [ ] Test both Report Owner and Tester views
- [ ] Verify assignment actions work

#### Scoping Phase (`/cycles/{id}/reports/{id}/scoping`)
- [ ] Verify assignments appear at top of page
- [ ] Test assignment actions work
- [ ] Verify scoping functionality still works

#### Sample Selection Phase (`/cycles/{id}/reports/{id}/sample-selection`)
- [ ] Verify assignments appear at top of page
- [ ] Test assignment actions work
- [ ] Verify sample selection functionality still works

#### Data Provider ID Phase (`/cycles/{id}/reports/{id}/data-owner`)
- [ ] Verify assignments appear at top of page
- [ ] Test assignment actions work
- [ ] Verify data owner functionality still works

#### Request Info Phase (`/cycles/{id}/reports/{id}/request-info`)
- [ ] Verify assignments appear at top of page
- [ ] Test assignment actions work
- [ ] Verify request info functionality still works

#### Test Execution Phase (`/cycles/{id}/reports/{id}/test-execution`)
- [ ] Verify assignments appear at top of page
- [ ] Test assignment actions work
- [ ] Verify test execution functionality still works

#### Observations Phase (`/cycles/{id}/reports/{id}/observation-management`)
- [ ] Verify assignments appear at top of page
- [ ] Test assignment actions work
- [ ] Verify observation management functionality still works

#### Finalize Test Report Phase (`/cycles/{id}/reports/{id}/finalize-report`)
- [ ] Verify assignments appear at top of page
- [ ] Test assignment actions work
- [ ] Verify report finalization functionality still works

### 3. Assignment Component Testing
- [ ] Alert shows correct priority color (Critical=red, High=warning, etc.)
- [ ] Overdue assignments show warning indicator
- [ ] Due date displays correctly
- [ ] Status badge shows correct status
- [ ] Actions buttons appear based on status:
  - Assigned → Show "Acknowledge" button
  - Acknowledged → Show "Start Task" button
  - In Progress → Show "Mark Complete" button

### 4. Role-Based Testing
- [ ] Test as Tester role
- [ ] Test as Test Manager role
- [ ] Test as Report Owner role
- [ ] Test as Data Provider role
- [ ] Verify assignments are filtered by user

### 5. Error Handling
- [ ] Test with network disconnected
- [ ] Test with invalid assignment IDs
- [ ] Test with unauthorized user
- [ ] Verify error toasts appear

### 6. Performance Testing
- [ ] Page load time with many assignments
- [ ] Assignment action response time
- [ ] Auto-refresh functionality (30 second interval)

## Integration Testing

### 1. Workflow Integration
- [ ] Create assignment when phase is submitted for approval
- [ ] Verify assignment blocks phase progression if critical
- [ ] Test assignment completion triggers next phase

### 2. Notification Testing
- [ ] Real-time toast notifications appear
- [ ] Assignment count updates in navigation
- [ ] Email notifications sent (if configured)

### 3. Data Consistency
- [ ] Assignment data consistent between API and UI
- [ ] Status changes reflect immediately
- [ ] Audit trail captures all changes

## Regression Testing
- [ ] All existing phase functionality still works
- [ ] No TypeScript compilation errors
- [ ] No console errors in browser
- [ ] No performance degradation
- [ ] All existing tests still pass

## Security Testing
- [ ] Users can only see their assignments
- [ ] Users can only act on their assignments
- [ ] API validates user permissions
- [ ] No sensitive data exposed