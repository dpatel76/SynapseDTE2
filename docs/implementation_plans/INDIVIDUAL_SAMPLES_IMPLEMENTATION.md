# Individual Samples Implementation

## Overview
This implementation removes all references to sample sets and implements a new individual sample management system for the Sample Selection phase.

## Database Changes

### New Tables Created
1. **samples** - Individual sample records
   - Tracks each sample independently
   - Includes tester decision fields (Include/Exclude/Review Required)
   - Status tracking (Draft/Submitted/Approved/Rejected/Revision Required)
   - Risk scoring and metadata

2. **sample_submissions** - Groups samples for approval
   - Tracks submission status and approval workflow
   - Links to multiple samples via association table

3. **sample_submission_items** - Association table
   - Links samples to submissions
   - Tracks inclusion status

4. **sample_feedback** - Report owner feedback
   - Can be at submission or individual sample level
   - Tracks blocking issues and resolution status

5. **sample_audit_logs** - Comprehensive audit trail
   - Tracks all operations on samples and submissions

### Migration
- Created migration script: `alembic/versions/010_add_individual_sample_tables.py`
- Run with: `alembic upgrade head`

## API Endpoints

### New endpoints in `/sample-selection/{cycle_id}/reports/{report_id}/`:

1. **GET /samples**
   - List all samples with filtering options
   - Query params: include_excluded, sample_type, tester_decision

2. **POST /samples/generate**
   - Generate new samples using LLM
   - Body: target_sample_size, sample_type, selection_criteria, etc.

3. **PUT /samples/{sample_id}/decision**
   - Update tester decision for a sample
   - Body: tester_decision, tester_decision_rationale

4. **POST /samples/submit**
   - Submit samples for approval
   - Body: submission_name, submission_notes, sample_ids

5. **GET /samples/feedback**
   - Get report owner feedback
   - Query params: submission_id, unresolved_only

6. **POST /samples/feedback**
   - Create feedback (Report Owner only)
   - Body: feedback_type, feedback_text, requested_changes, is_blocking

7. **GET /samples/analytics**
   - Get analytics and statistics

8. **PUT /samples/bulk-decision**
   - Bulk update tester decisions
   - Body: sample_ids, tester_decision

## Frontend Changes

### New Component
- `SampleSelectionIndividual.tsx` - Complete rewrite of sample selection UI
  - Individual sample management
  - Tester decision tracking (Include/Exclude/Review Required)
  - Bulk operations support
  - Real-time analytics
  - Feedback management with blocking issue indicators
  - Submission workflow

### Features
- Generate samples with LLM
- Individual decision tracking per sample
- Bulk decision updates
- Sample submission workflow
- Feedback viewing with unresolved count badges
- Analytics dashboard
- Filtering and search capabilities

## Key Improvements

1. **Granular Control** - Each sample has its own decision and status
2. **Better Workflow** - Clear submission and approval process
3. **Feedback Management** - Detailed feedback at sample or submission level
4. **Audit Trail** - Complete tracking of all operations
5. **Analytics** - Real-time statistics and insights

## Usage

### For Testers
1. Generate or upload samples
2. Review each sample and mark as Include/Exclude/Review Required
3. Use bulk actions for efficiency
4. Submit selected samples for approval
5. Address any feedback from Report Owners

### For Report Owners
1. Review submitted samples
2. Provide feedback at submission or individual sample level
3. Mark feedback as blocking if changes are required
4. Approve or reject submissions

## Configuration
No additional configuration required. The system uses existing authentication and permissions.

## Testing
Test the new endpoints with:
```bash
# List samples
curl -X GET "http://localhost:8000/api/v1/sample-selection/1/reports/1/samples" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Generate samples
curl -X POST "http://localhost:8000/api/v1/sample-selection/1/reports/1/samples/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_sample_size": 10,
    "sample_type": "Population Sample",
    "include_edge_cases": true
  }'
```

## Notes
- The old sample set endpoints remain available for backward compatibility
- Both systems can coexist during transition
- Individual samples provide more flexibility and better tracking
- Feedback system enables better collaboration between Testers and Report Owners