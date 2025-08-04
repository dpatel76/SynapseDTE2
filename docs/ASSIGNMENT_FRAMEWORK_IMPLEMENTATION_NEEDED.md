# Assignment Framework Implementation Needed

## Issue
Report Owners do not see data upload assignments in their dashboard when Testers request data for profiling. This is because the standardized assignment framework is not implemented for the data profiling phase.

## Current State
- **Frontend**: Properly implements assignment creation API calls but gets 404 errors
- **Backend**: Missing assignment endpoints for data profiling
- **Fallback**: Uses simple `requestData` which only updates timestamps, doesn't create trackable assignments
- **Dashboard**: Report Owner dashboard doesn't query for data profiling assignments

## Required Backend Implementation

### 1. Create Report Owner Assignment Model
```sql
-- New table for Report Owner assignments
CREATE TABLE report_owner_assignments (
    assignment_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(report_id),
    phase_name VARCHAR(50) NOT NULL, -- 'Data Profiling', 'Request Info', etc.
    assignment_type VARCHAR(50) NOT NULL, -- 'Data Upload', 'File Review', etc.
    assigned_to INTEGER NOT NULL REFERENCES users(user_id), -- Report Owner
    assigned_by INTEGER NOT NULL REFERENCES users(user_id), -- Tester who created request
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    due_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'Assigned', -- 'Assigned', 'In Progress', 'Completed', 'Overdue'
    description TEXT,
    priority VARCHAR(20) NOT NULL DEFAULT 'Medium', -- 'High', 'Medium', 'Low'
    completed_at TIMESTAMP WITH TIME ZONE,
    completed_by INTEGER REFERENCES users(user_id),
    completion_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_report_owner_assignments_assigned_to ON report_owner_assignments(assigned_to);
CREATE INDEX idx_report_owner_assignments_cycle_report ON report_owner_assignments(cycle_id, report_id);
CREATE INDEX idx_report_owner_assignments_status ON report_owner_assignments(status);
```

### 2. Implement Missing Backend Endpoints

#### A. Create Assignment Endpoint
```python
# File: app/api/v1/endpoints/data_profiling_clean.py

@router.post("/cycles/{cycle_id}/reports/{report_id}/assign-report-owner")
@require_permission("data_profiling", "assign")
async def create_report_owner_assignment(
    cycle_id: int,
    report_id: int,
    assignment_details: ReportOwnerAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a data upload assignment for the Report Owner"""
    
    # Get report to find report owner
    report = await get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.report_owner_id:
        raise HTTPException(status_code=400, detail="No Report Owner assigned to this report")
    
    # Create assignment
    assignment = ReportOwnerAssignment(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name="Data Profiling",
        assignment_type=assignment_details.request_type,
        assigned_to=report.report_owner_id,
        assigned_by=current_user.user_id,
        description=assignment_details.description,
        priority=assignment_details.priority,
        due_date=assignment_details.due_date
    )
    
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    
    # Send notification
    await send_assignment_notification(assignment, db)
    
    # Create audit log
    await create_audit_log(
        db=db,
        user_id=current_user.user_id,
        action="ASSIGNMENT_CREATED",
        entity_type="ReportOwnerAssignment",
        entity_id=assignment.assignment_id,
        details=f"Created data upload assignment for Report Owner"
    )
    
    return {"success": True, "assignment_id": assignment.assignment_id}
```

#### B. Get Assignments Endpoint
```python
@router.get("/cycles/{cycle_id}/reports/{report_id}/report-owner-assignments")
async def get_report_owner_assignments(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all assignments for a specific report"""
    
    assignments = await db.execute(
        select(ReportOwnerAssignment)
        .where(
            ReportOwnerAssignment.cycle_id == cycle_id,
            ReportOwnerAssignment.report_id == report_id
        )
        .order_by(ReportOwnerAssignment.created_at.desc())
    )
    
    return assignments.scalars().all()
```

#### C. Dashboard Assignments Endpoint
```python
# File: app/api/v1/endpoints/assignments.py (new file)

@router.get("/report-owner-assignments/pending")
async def get_pending_report_owner_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending assignments for current Report Owner"""
    
    assignments = await db.execute(
        select(ReportOwnerAssignment)
        .join(Report, ReportOwnerAssignment.report_id == Report.report_id)
        .join(TestCycle, ReportOwnerAssignment.cycle_id == TestCycle.cycle_id)
        .where(
            ReportOwnerAssignment.assigned_to == current_user.user_id,
            ReportOwnerAssignment.status.in_(['Assigned', 'In Progress'])
        )
        .order_by(ReportOwnerAssignment.due_date.asc())
    )
    
    return assignments.scalars().all()
```

### 3. Update RequestData Endpoint
```python
# Modify existing requestData endpoint to create assignment
@router.post("/cycles/{cycle_id}/reports/{report_id}/request-data")
async def request_data_from_report_owner(
    cycle_id: int,
    report_id: int,
    request: DataRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request data from Report Owner and create assignment"""
    
    # Update existing logic...
    phase.data_requested_at = datetime.utcnow()
    phase.data_requested_by = current_user.user_id
    
    # NEW: Create assignment
    report = await get_report_by_id(db, report_id)
    if report and report.report_owner_id:
        assignment = ReportOwnerAssignment(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name="Data Profiling",
            assignment_type="Data Upload Request",
            assigned_to=report.report_owner_id,
            assigned_by=current_user.user_id,
            description=request.message or "Data files are required for profiling analysis",
            priority="High",
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        db.add(assignment)
    
    await db.commit()
    return {"success": True}
```

### 4. Update Report Owner Dashboard

#### Frontend Changes Needed:
```typescript
// File: frontend/src/pages/dashboards/ReportOwnerDashboard.tsx

// Add new API call
const { data: dataProfilingAssignments } = useQuery({
  queryKey: ['report-owner-assignments', 'pending'],
  queryFn: () => api.get('/report-owner-assignments/pending').then(res => res.data)
});

// Add new section to dashboard
<Card>
  <CardHeader title="Data Profiling Assignments" />
  <CardContent>
    {dataProfilingAssignments?.map(assignment => (
      <AssignmentCard
        key={assignment.assignment_id}
        title={assignment.assignment_type}
        description={assignment.description}
        dueDate={assignment.due_date}
        priority={assignment.priority}
        status={assignment.status}
        actionUrl={`/cycles/${assignment.cycle_id}/reports/${assignment.report_id}/data-profiling`}
        actionText="Upload Data Files"
      />
    ))}
  </CardContent>
</Card>
```

## Testing Plan

1. **Create Assignment**: Tester requests data → Assignment appears in Report Owner dashboard
2. **Dashboard Visibility**: Report Owner can see assignment with due date and priority
3. **Assignment Completion**: Report Owner uploads files → Assignment marked complete
4. **Notification**: Report Owner receives email/notification about new assignment
5. **SLA Tracking**: Overdue assignments are properly flagged

## Benefits After Implementation

- ✅ Report Owners see data requests in their dashboard
- ✅ Trackable assignments with SLA management
- ✅ Proper audit trail for all data requests
- ✅ Email notifications for assignment creation
- ✅ Consistent assignment patterns across all phases
- ✅ Integration with existing dashboard and notification systems

## Files to Modify

**Backend:**
- `app/models/assignment.py` (create new model)
- `app/api/v1/endpoints/data_profiling_clean.py` (add assignment endpoints)
- `app/api/v1/endpoints/assignments.py` (new file for cross-phase assignments)
- `app/schemas/assignment.py` (create assignment schemas)
- `alembic/versions/` (new migration for assignment table)

**Frontend:**
- `frontend/src/pages/dashboards/ReportOwnerDashboard.tsx` (add assignment display)
- `frontend/src/api/assignments.ts` (new assignment API client)

This implementation will provide the missing assignment framework integration and ensure Report Owners can properly track and respond to data upload requests.