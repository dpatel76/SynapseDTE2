# RFI Phase Quick Fix Checklist

## 🚨 Critical Issues to Fix

### 1. Mixed Async/Sync Sessions in `request_info.py`

**Lines with Sync Session (MUST FIX):**
- Line 659: `submit_document_evidence` 
- Line 689: `submit_data_source_evidence`
- Line 722: `get_test_case_evidence`
- Line 749: `get_evidence_for_review`
- Line 779: `submit_tester_decision`
- Line 820: `get_evidence_progress`
- Line 844: `get_evidence_validation`
- Line 869: `revalidate_evidence`
- Line 909: `get_data_owner_evidence_portal`

**Fix:**
```python
# Change from:
db: Session = Depends(get_db)
# To:
db: AsyncSession = Depends(get_db)

# And make service calls async:
service = EvidenceCollectionService(db)
result = await service.submit_document_evidence(...)  # Add await
```

### 2. Missing Timestamp Updates in `request_info_service.py`

**Lines Missing updated_at:**
- Line 150-154: Phase status update
- Line 569-571: Notification access tracking  
- Line 695-696: Test case status change
- Line 792-794: Phase completion

**Fix:**
```python
# Add after each modification:
object.field = new_value
object.updated_at = datetime.utcnow()
if hasattr(object, 'updated_by'):
    object.updated_by = user_id
self.db.add(object)  # Ensure tracking
```

### 3. Missing Model Import in `request_info_activities.py`

**Line 130:** References undefined `InformationRequest`

**Fix:**
```python
# Add to imports at top:
from app.models.request_info import InformationRequest, InformationRequestItem
```

## ✅ Quick Validation Script

```bash
# Check for sync sessions in async endpoints
grep -n "db: Session" app/api/v1/endpoints/request_info.py

# Check for missing updated_at
grep -A2 -B2 "\.status = " app/services/request_info_service.py | grep -v "updated_at"

# Run pattern checker
python scripts/check_async_patterns.py app/api/v1/endpoints/request_info.py app/services/request_info_service.py

# Check for undefined models
python -m py_compile app/temporal/activities/request_info_activities.py
```

## 🔧 Fix Priority

1. **HIGH PRIORITY** (Runtime Errors):
   - Mixed async/sync sessions - Can cause connection pool exhaustion
   - Missing imports - Will fail immediately when activity runs

2. **MEDIUM PRIORITY** (Data Integrity):
   - Missing timestamp updates - Audit trail incomplete
   - Session tracking - Changes might not persist

3. **LOW PRIORITY** (Future-proofing):
   - Add job manager infrastructure if needed
   - Implement progress tracking patterns

## 📋 Testing After Fixes

```python
# Test async session usage
async def test_all_endpoints_async():
    """Verify all endpoints use AsyncSession"""
    import ast
    # Parse file and check all Depends(get_db) are AsyncSession

# Test timestamp updates
async def test_timestamp_updates():
    """Verify updated_at is set on all modifications"""
    # Create test case
    # Modify it
    # Assert updated_at changed

# Test temporal activities
async def test_request_info_activities():
    """Verify all activities can be imported and run"""
    from app.temporal.activities import request_info_activities
    # Run each activity with test data
```

## 🚀 Estimated Time to Fix All Issues

- Mixed Sessions: 45 minutes (9 endpoints × 5 min each)
- Timestamp Updates: 20 minutes (4 locations × 5 min each)  
- Missing Imports: 5 minutes
- Testing: 30 minutes

**Total: ~1.5 hours**

## 📝 Commit Message Template

```
fix(rfi): standardize async sessions and add missing timestamps

- Convert all RFI endpoints from sync to async sessions
- Add updated_at timestamp updates to all object modifications
- Fix missing model imports in temporal activities
- Prevent connection pool and session tracking issues

Based on lessons from Planning phase troubleshooting
```