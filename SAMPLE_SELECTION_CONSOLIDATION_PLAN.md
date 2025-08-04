# Sample Selection Endpoint Consolidation Plan

## Overview
This plan outlines how to safely consolidate redundant endpoints in the sample selection module without breaking existing functionality.

## Current State Analysis

### 1. Submit/Approval Flow Redundancy
Currently we have:
- **Legacy submission system**: Uses "submissions" array in phase_data
- **New version system**: Uses "versions" array in phase_data
- Both are storing similar data in different formats

### 2. Multiple Review Endpoints
- `/samples/review` - Reviews all samples globally
- `/submissions/{submission_id}/review` - Reviews specific submission
- `/versions/{version_id}/approve` - Approves version

### 3. Three Generation Strategies as Separate Endpoints
- Basic generation
- Intelligent generation  
- Enhanced generation

## Consolidation Strategy

### Phase 1: Deprecate but Don't Remove (Safe Transition)

1. **Mark Legacy Endpoints as Deprecated**
   - Add deprecation warnings to response headers
   - Log usage of deprecated endpoints
   - Update documentation

2. **Redirect Legacy Calls to New Endpoints**
   ```python
   # Example: Legacy submit endpoint redirects to version submit
   @router.post("/cycles/{cycle_id}/reports/{report_id}/samples/submit")
   async def submit_samples_legacy(...):
       # Log deprecation warning
       logger.warning("Using deprecated submit endpoint")
       
       # Create version if needed
       version = await create_or_get_current_version(...)
       
       # Redirect to new endpoint
       return await submit_version_for_approval(version.version_id, ...)
   ```

### Phase 2: Unify Generation Endpoints

**Current**: 3 separate endpoints
**Target**: 1 endpoint with strategy parameter

```python
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/generate")
async def generate_samples(
    cycle_id: int,
    report_id: int,
    request: SampleGenerationRequest,  # includes strategy field
    ...
):
    if request.strategy == "basic":
        return await _generate_basic_samples(...)
    elif request.strategy == "intelligent":
        return await _generate_intelligent_samples(...)
    elif request.strategy == "enhanced":
        return await _generate_enhanced_samples(...)
```

### Phase 3: Consolidate Approval Flow

**Target State**:
1. One primary approval endpoint: `/versions/{version_id}/approve`
2. Remove submission-based review endpoints
3. Keep individual sample decisions for granular control

### Phase 4: Simplify Bulk Operations

**Current**: 4 different bulk endpoints
**Target**: 1 bulk operation endpoint

```python
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/bulk-operation")
async def bulk_sample_operation(
    cycle_id: int,
    report_id: int,
    request: BulkOperationRequest,  # includes action: approve/reject/decide
    ...
):
    # Handle all bulk operations in one endpoint
```

## Migration Path

### Step 1: Add Version Support to Legacy Endpoints (Complete)
✓ Already added version creation and management

### Step 2: Create Adapter Functions
Create internal functions that adapt legacy calls to new version-based system:

```python
async def _adapt_legacy_submission_to_version(phase_data, submission_id):
    """Convert legacy submission to version format"""
    # Find submission
    # Create or update version
    # Return version_id
```

### Step 3: Implement Deprecation Warnings
```python
def deprecated_endpoint(alternative: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Add deprecation header
            response = await func(*args, **kwargs)
            response.headers["X-Deprecated"] = "true"
            response.headers["X-Alternative-Endpoint"] = alternative
            return response
        return wrapper
    return decorator
```

### Step 4: Update Frontend Gradually
1. Update frontend to use new endpoints
2. Keep legacy endpoints working during transition
3. Monitor usage of deprecated endpoints
4. Remove legacy endpoints after frontend migration

## Endpoints to Keep vs Remove

### Keep (Primary Endpoints):
1. `/versions` - Get all versions
2. `/cycles/{cycle_id}/reports/{report_id}/versions` - Create version
3. `/versions/{version_id}/submit` - Submit for approval
4. `/versions/{version_id}/approve` - Approve/reject version
5. `/cycles/{cycle_id}/reports/{report_id}/resubmit-after-feedback` - Make changes
6. `/cycles/{cycle_id}/reports/{report_id}/samples` - Get samples
7. `/cycles/{cycle_id}/reports/{report_id}/samples/generate` - Generate samples (unified)
8. `/cycles/{cycle_id}/reports/{report_id}/samples/{sample_id}/decide` - Individual decision
9. `/cycles/{cycle_id}/reports/{report_id}/samples/bulk-operation` - Bulk operations (unified)

### Deprecate (Redundant Endpoints):
1. `/cycles/{cycle_id}/reports/{report_id}/samples/submit` - Use version submit
2. `/cycles/{cycle_id}/reports/{report_id}/samples/review` - Use version approve
3. `/cycles/{cycle_id}/reports/{report_id}/submissions/{submission_id}/review` - Use version approve
4. `/cycles/{cycle_id}/reports/{report_id}/samples/intelligent` - Use generate with strategy
5. `/cycles/{cycle_id}/reports/{report_id}/samples/generate-enhanced` - Use generate with strategy
6. `/cycles/{cycle_id}/reports/{report_id}/samples/bulk-approve` - Use bulk-operation
7. `/cycles/{cycle_id}/reports/{report_id}/samples/bulk-reject` - Use bulk-operation
8. `/cycles/{cycle_id}/reports/{report_id}/samples/bulk-decision` - Use bulk-operation

## Benefits

1. **Reduced Confusion**: One clear way to do each operation
2. **Easier Maintenance**: Less code duplication
3. **Consistent Patterns**: All phases follow same versioning pattern
4. **Better API Design**: RESTful, predictable endpoints
5. **Safer Migration**: Gradual transition without breaking changes

## Risks and Mitigation

1. **Risk**: Breaking existing frontend
   **Mitigation**: Keep legacy endpoints with adapters during transition

2. **Risk**: Data inconsistency between submissions and versions
   **Mitigation**: Sync data during transition period

3. **Risk**: Performance impact from adapters
   **Mitigation**: Monitor and optimize adapter functions

## Timeline

1. Week 1: Implement adapter functions and deprecation framework
2. Week 2: Add deprecation warnings to all legacy endpoints
3. Week 3-4: Update frontend to use new endpoints
4. Week 5: Monitor usage and fix any issues
5. Week 6+: Remove deprecated endpoints after confirming no usage