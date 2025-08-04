# Manual Debugging Steps for Report Owner Feedback Tab Issue

## Current Situation
- ✅ Automated tests consistently show the "Report Owner Feedback" tab is present
- ✅ Backend has 7 samples with Report Owner decisions
- ✅ Frontend code changes are in place
- ✅ Debug logs show `hasReportOwnerFeedback` is set to `true`
- ❌ User cannot see the tab manually in any browser

## Step-by-Step Manual Debugging

### Step 1: Check Browser Developer Tools
1. Open browser and go to: `http://localhost:3000/cycles/55/reports/156/sample-selection`
2. Login as: `tester@example.com` / `password123`
3. Press `F12` to open Developer Tools
4. Go to **Console** tab
5. Look for these messages:
   ```
   Setting hasReportOwnerFeedback to: true
   Samples with report_owner_decision: 7 out of 12
   ```
6. **Question**: Do you see these debug messages?

### Step 2: Check React Components in DevTools
1. In Developer Tools, go to **Elements** tab
2. Use Ctrl+F (or Cmd+F) to search for: `Report Owner Feedback`
3. **Question**: Do you find this text in the HTML?

### Step 3: Check Network Requests
1. In Developer Tools, go to **Network** tab
2. Refresh the page
3. Look for request to: `/sample-selection/cycles/55/reports/156/samples`
4. Click on the request and check the **Response** tab
5. **Question**: Do you see samples with `"report_owner_decision"` fields?

### Step 4: Check React State
1. If you have React Developer Tools extension:
   - Look for the `SampleSelectionPage` component
   - Check the `hasReportOwnerFeedback` state
2. **Question**: What is the value of `hasReportOwnerFeedback`?

### Step 5: Manual JavaScript Check
1. In the Console tab, run this JavaScript:
   ```javascript
   document.querySelectorAll('button[role="tab"]').forEach((tab, i) => {
     console.log(`Tab ${i+1}: ${tab.textContent.trim()}`);
   });
   ```
2. **Question**: What tabs does this show?

### Step 6: Check for CSS Issues
1. In Elements tab, look for tabs container
2. Check if any CSS is hiding the tab:
   ```javascript
   document.querySelector('button:contains("Report Owner Feedback")')?.style
   ```
3. **Question**: Is there any `display: none` or `visibility: hidden`?

## Possible Root Causes

1. **Browser Extension Interference**: Ad blockers or other extensions
2. **Local Storage/Session Storage**: Cached user preferences
3. **CSS Override**: Some CSS rule hiding the tab
4. **React Hot Reload Issues**: Frontend not updating properly
5. **Build Process Issues**: Different code being served

## Emergency Workaround
If you need to see the Report Owner feedback immediately, you can:
1. Go to Sample Review tab
2. Look at the "Report Owner Decision" column in the table
3. You should see the decisions there even if the tab is hidden

## Next Steps
Please go through Steps 1-5 above and report back what you find. This will help us identify the root cause.