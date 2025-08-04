# Manual Testing Checklist

## Prerequisites
- Backend server running on http://localhost:8000
- Frontend server running on http://localhost:3000
- Test users created (admin@example.com, report_owner@example.com)

## Test 1: Report Owner Feedback Tab (Sample Selection)

### Steps:
1. Login as Admin
2. Navigate to Sample Selection phase
3. Generate samples if needed
4. Submit for Report Owner review
5. Login as Report Owner
6. Complete the review with decisions
7. Login back as Admin
8. Click on "Report Owner Feedback" tab

### Expected Results:
- [ ] Tab shows ONLY the version that Report Owner reviewed (e.g., v2)
- [ ] No data from other versions (v1, v3, v4) appears
- [ ] Version indicator chip shows correct version number
- [ ] All samples from the reviewed version are displayed
- [ ] No duplicate samples appear
- [ ] "Make Changes" functionality works correctly

### Console Check:
- [ ] No 404 errors in browser console
- [ ] No JavaScript errors

## Test 2: Report Owner Feedback (Scoping Phase)

### Steps:
1. Navigate to Scoping phase
2. Click on "Report Owner Feedback" tab

### Expected Results:
- [ ] Shows only the version originally reviewed by Report Owner
- [ ] Version indicator chip displays correctly (e.g., "Version 1")
- [ ] All scoped attributes from that version are shown
- [ ] No data from subsequent versions appears

### Console Check:
- [ ] No 404 errors in browser console
- [ ] No JavaScript errors

## Test 3: Report Owner Feedback (Data Profiling Phase)

### Steps:
1. Navigate to Data Profiling phase
2. Click on "Report Owner Feedback" tab

### Expected Results:
- [ ] Shows only the version originally reviewed by Report Owner
- [ ] Version indicator chip displays correctly
- [ ] All profiled attributes from that version are shown
- [ ] No data from subsequent versions appears

### Console Check:
- [ ] No 404 errors in browser console
- [ ] No JavaScript errors

## Test 4: Version-based Submission

### Steps:
1. Navigate to Sample Selection phase
2. Generate new samples (this creates a new version, e.g., v4)
3. Make some changes to the samples
4. Click "Submit for Review"
5. Check the created assignment

### Expected Results:
- [ ] Assignment is created with the correct version (v4)
- [ ] Assignment details show the correct version number
- [ ] Report Owner sees the correct version when reviewing

## Test 5: 404 Error Check

### Steps:
1. Open browser developer tools (F12)
2. Navigate to Console tab
3. Clear console
4. Navigate through all phases:
   - Sample Selection (all tabs)
   - Scoping (all tabs)
   - Data Profiling (all tabs)

### Expected Results:
- [ ] No 404 errors in console
- [ ] All API calls return successful responses
- [ ] No "Failed to fetch" errors

## Test 6: General Workflow

### Steps:
1. Complete entire workflow from start:
   - Generate samples
   - Review and submit
   - Complete Report Owner review
   - Make changes based on feedback
   - Resubmit
   - Final approval

### Expected Results:
- [ ] All tabs load correctly at each step
- [ ] Version tracking is consistent throughout
- [ ] No errors during transitions
- [ ] Data integrity maintained
- [ ] Feedback tabs show correct historical data

## Browser Console Test

### Steps:
1. Open browser console (F12)
2. Paste and run the frontend_console_test.js script
3. Run `testNavigation()` command
4. Navigate manually through the application
5. Run `testSummary()` command

### Expected Results:
- [ ] No errors reported in summary
- [ ] No 404 network errors
- [ ] No React error boundaries triggered

## Performance Check

### Steps:
1. Monitor page load times
2. Check for any freezing or lag
3. Verify smooth transitions between tabs

### Expected Results:
- [ ] Pages load within 2 seconds
- [ ] No UI freezing
- [ ] Smooth tab transitions

## Edge Cases

### Test empty states:
- [ ] No samples generated yet
- [ ] No Report Owner feedback yet
- [ ] No decisions made yet

### Test error states:
- [ ] Invalid cycle/report IDs
- [ ] Unauthorized access attempts
- [ ] Network disconnection handling

## Summary

Total Tests Passed: _____ / _____

Issues Found:
1. 
2. 
3. 

Notes: