# Scoping UI and Backend Improvements

## Current State Analysis

### Database Design Assessment
The database already has excellent versioning support:
- `report_attributes`: Has version tracking (version_number, is_latest_version, master_attribute_id)
- `scoping_submissions`: Has versioning (version, previous_version_id, changes_from_previous)
- `report_owner_scoping_reviews`: Handles approval workflow
- `scoping_audit_log`: Tracks all changes

### UI Gap
The current UI only has checkboxes for selection but lacks explicit Include/Exclude functionality.

## Proposed UI Improvements

### 1. Replace Checkbox with Include/Exclude Toggle

```typescript
// Add to each table row in Scoping Status column
<TableCell>
  {attr.is_primary_key ? (
    <Chip 
      label="Included (PK)" 
      color="primary" 
      size="small"
      icon={<LockIcon />}
    />
  ) : (
    <ToggleButtonGroup
      value={getScopingDecision(attr.attribute_id)}
      exclusive
      onChange={(e, value) => handleScopingDecision(attr.attribute_id, value)}
      size="small"
    >
      <ToggleButton value="include" color="success">
        <CheckCircleIcon sx={{ mr: 0.5 }} />
        Include
      </ToggleButton>
      <ToggleButton value="exclude" color="error">
        <CancelIcon sx={{ mr: 0.5 }} />
        Exclude
      </ToggleButton>
    </ToggleButtonGroup>
  )}
</TableCell>
```

### 2. Add Decision Summary Panel

```typescript
// Add above the table
<Card sx={{ mb: 2 }}>
  <CardContent>
    <Typography variant="h6">Scoping Decision Summary</Typography>
    <Grid container spacing={2}>
      <Grid item xs={3}>
        <Typography variant="body2" color="text.secondary">Total Attributes</Typography>
        <Typography variant="h4">{attributes.length}</Typography>
      </Grid>
      <Grid item xs={3}>
        <Typography variant="body2" color="text.secondary">Included</Typography>
        <Typography variant="h4" color="success.main">
          {getIncludedCount()}
        </Typography>
      </Grid>
      <Grid item xs={3}>
        <Typography variant="body2" color="text.secondary">Excluded</Typography>
        <Typography variant="h4" color="error.main">
          {getExcludedCount()}
        </Typography>
      </Grid>
      <Grid item xs={3}>
        <Typography variant="body2" color="text.secondary">Pending</Typography>
        <Typography variant="h4" color="warning.main">
          {getPendingCount()}
        </Typography>
      </Grid>
    </Grid>
  </CardContent>
</Card>
```

### 3. Add Bulk Actions

```typescript
// Add bulk action buttons
<Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
  <Button
    variant="outlined"
    startIcon={<CheckCircleIcon />}
    onClick={() => handleBulkAction('include')}
    disabled={bulkSelectedAttributes.length === 0}
  >
    Include Selected ({bulkSelectedAttributes.length})
  </Button>
  <Button
    variant="outlined"
    color="error"
    startIcon={<CancelIcon />}
    onClick={() => handleBulkAction('exclude')}
    disabled={bulkSelectedAttributes.length === 0}
  >
    Exclude Selected ({bulkSelectedAttributes.length})
  </Button>
  <Button
    variant="outlined"
    startIcon={<FilterListIcon />}
    onClick={() => setShowFilters(!showFilters)}
  >
    Filter by Risk Score
  </Button>
</Box>
```

### 4. Add Submission with Comments

```typescript
// Replace simple submit button with dialog
<Button
  variant="contained"
  color="primary"
  startIcon={<SendIcon />}
  onClick={() => setSubmitDialogOpen(true)}
  disabled={!canSubmit()}
>
  Submit Scoping Decisions
</Button>

// Submission Dialog
<Dialog open={submitDialogOpen} onClose={() => setSubmitDialogOpen(false)}>
  <DialogTitle>Submit Scoping Decisions for Approval</DialogTitle>
  <DialogContent>
    <Typography variant="body2" gutterBottom>
      You are submitting {getIncludedCount()} attributes for testing 
      and excluding {getExcludedCount()} attributes.
    </Typography>
    <TextField
      fullWidth
      multiline
      rows={4}
      label="Submission Notes (Optional)"
      placeholder="Provide any context or rationale for your scoping decisions..."
      value={submissionNotes}
      onChange={(e) => setSubmissionNotes(e.target.value)}
      sx={{ mt: 2 }}
    />
  </DialogContent>
  <DialogActions>
    <Button onClick={() => setSubmitDialogOpen(false)}>Cancel</Button>
    <Button onClick={handleSubmitScoping} variant="contained" color="primary">
      Submit for Approval
    </Button>
  </DialogActions>
</Dialog>
```

## Backend API Improvements

### 1. Enhanced Scoping Decision Endpoint

```python
@router.post("/cycles/{cycle_id}/reports/{report_id}/scoping-submission")
async def create_scoping_submission(
    cycle_id: int,
    report_id: int,
    submission_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Create a new scoping submission with versioning"""
    
    # Get previous submission if exists
    prev_submission = await db.execute(
        select(ScopingSubmission)
        .where(
            and_(
                ScopingSubmission.cycle_id == cycle_id,
                ScopingSubmission.report_id == report_id,
                ScopingSubmission.is_latest == True
            )
        )
    )
    previous = prev_submission.scalar_one_or_none()
    
    # Create new submission
    new_submission = ScopingSubmission(
        cycle_id=cycle_id,
        report_id=report_id,
        submitted_by=current_user.user_id,
        version=previous.version + 1 if previous else 1,
        previous_version_id=previous.submission_id if previous else None,
        total_attributes=submission_data["total_attributes"],
        scoped_attributes=submission_data["included_count"],
        skipped_attributes=submission_data["excluded_count"],
        submission_notes=submission_data.get("notes", ""),
        is_latest=True
    )
    
    # Mark previous as not latest
    if previous:
        previous.is_latest = False
        
        # Calculate changes
        changes = calculate_changes(previous_decisions, current_decisions)
        new_submission.changes_from_previous = changes
    
    db.add(new_submission)
    
    # Create individual decisions
    for decision in submission_data["decisions"]:
        scoping_decision = TesterScopingDecision(
            cycle_id=cycle_id,
            report_id=report_id,
            attribute_id=decision["attribute_id"],
            submission_id=new_submission.submission_id,
            decision="Accept" if decision["include"] else "Decline",
            final_scoping=decision["include"],
            tester_rationale=decision.get("rationale", ""),
            decided_by=current_user.user_id
        )
        db.add(scoping_decision)
    
    await db.commit()
    
    return {
        "submission_id": new_submission.submission_id,
        "version": new_submission.version,
        "status": "submitted_for_approval"
    }
```

### 2. View Submission History

```python
@router.get("/cycles/{cycle_id}/reports/{report_id}/scoping-history")
async def get_scoping_submission_history(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """Get all scoping submission versions"""
    
    submissions = await db.execute(
        select(ScopingSubmission)
        .where(
            and_(
                ScopingSubmission.cycle_id == cycle_id,
                ScopingSubmission.report_id == report_id
            )
        )
        .order_by(ScopingSubmission.version.desc())
    )
    
    return [
        {
            "submission_id": sub.submission_id,
            "version": sub.version,
            "submitted_at": sub.submitted_at,
            "submitted_by": sub.submitter.full_name,
            "total_attributes": sub.total_attributes,
            "included": sub.scoped_attributes,
            "excluded": sub.skipped_attributes,
            "status": sub.approval_status,
            "changes_from_previous": sub.changes_from_previous,
            "review_comments": sub.review_comments
        }
        for sub in submissions.scalars().all()
    ]
```

## Key Benefits

1. **Clear UI**: Explicit Include/Exclude toggles instead of ambiguous checkboxes
2. **Versioning**: Every submission creates a new version with change tracking
3. **Audit Trail**: Complete history of what changed between versions
4. **Approval Workflow**: Report owners can review and request changes
5. **Reusable Pattern**: Same design can be used for sampling phase

## Implementation Priority

1. **Phase 1**: Add Include/Exclude UI components
2. **Phase 2**: Implement versioned submission endpoint
3. **Phase 3**: Add submission history view
4. **Phase 4**: Enhance with comparison view between versions