# Sample Selection Workflow - Correct Implementation

## Workflow Steps

### 1. Tester Submits Version
- Tester completes sample selection and submits to Report Owner
- **Version metadata updated**: `version_status = "pending_approval"`
- **Assignment created** for Report Owner with version info
- Version cannot be modified while `pending_approval`

### 2. Report Owner Reviews
- Report Owner reviews samples and provides feedback
- **Version metadata updated**: `reviewed_by_report_owner = true`
- Samples updated with `report_owner_decision` and `report_owner_feedback`

### 3. Tester Views Feedback
- **Report Owner Feedback tab** shows the **LATEST version** with RO feedback
- Not the earliest, but the most recent version reviewed by RO
- Uses version metadata to determine which version to show

### 4. Make Changes (if needed)
- **Only allowed when**: Current version status is NOT `pending_approval` or `approved`
- **Creates new version from**: Latest version that has Report Owner feedback
- **Copies**:
  - All samples from the feedback version
  - LOB assignments
  - Tester decisions (reset if RO rejected)
  - Report Owner decisions and feedback

### 5. Resubmission
- Tester makes changes and submits again
- New version status: `pending_approval`
- New assignment created for Report Owner

### 6. Approval
- Report Owner approves the version
- **Version metadata updated**: `version_status = "approved"`
- Cannot make changes once approved

### 7. Phase Completion
- Tester can complete the phase once version is `approved`

## Key Implementation Details

### Version Metadata Structure
```json
{
  "version_id": "uuid",
  "version_number": 2,
  "version_status": "pending_approval", // draft, pending_approval, approved, rejected
  "metadata": {
    "reviewed_by_report_owner": true,
    "report_owner_id": 123,
    "report_owner_review_date": "2024-01-25T10:00:00Z",
    "report_owner_decision": "approved"
  }
}
```

### Finding Correct Version
1. For **Report Owner Feedback**: Find LATEST version with `reviewed_by_report_owner = true`
2. For **Make Changes**: Use same LATEST version with RO feedback
3. Check version status before allowing changes

### Status Transitions
- `draft` → `pending_approval` (on submit)
- `pending_approval` → `draft` (if rejected with changes needed)
- `pending_approval` → `approved` (if approved by RO)

## Fixed Issues

1. **Wrong Version Selection**: Was using earliest version (v1) instead of latest reviewed (v2)
2. **Make Changes Logic**: Now finds latest version with RO feedback, not earliest
3. **Status Checking**: Added validation to prevent changes when `pending_approval` or `approved`
4. **Version Display**: Report Owner Feedback tab now shows correct version number

## Testing Checklist

- [ ] Submit version creates `pending_approval` status
- [ ] Cannot make changes when `pending_approval`
- [ ] RO feedback updates version metadata
- [ ] RO Feedback tab shows latest reviewed version
- [ ] Make Changes uses latest feedback version
- [ ] All decisions and LOBs are copied correctly
- [ ] Cannot make changes when `approved`