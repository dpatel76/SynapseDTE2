# Intelligent Sampling Implementation

## Overview

This document describes the implementation of intelligent sampling functionality with 30/50/20 distribution based on lessons learned from planning phase issues.

## What Was Implemented

### 1. Intelligent Sampling Service (Already Existed)
- **File**: `/app/services/sample_selection_intelligent_service.py`
- **Distribution**: 30% clean, 50% anomaly, 20% boundary samples
- Supports both database and file-based sampling
- Provides mock sample generation when no data source is available

### 2. New Intelligent Sampling Endpoint
- **Endpoint**: `POST /api/v1/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/generate-intelligent`
- **File**: `/app/api/v1/endpoints/sample_selection.py`

#### Features:
1. **Data Source Integration**
   - Connects to planning phase data sources
   - Queries `CycleReportDataSource` from planning phase
   - Falls back to mock generation if no data source

2. **File Upload Support**
   - Can include previously uploaded samples in the intelligent distribution
   - Respects the 30/50/20 ratio when combining sources

3. **Error Handling**
   - Validates data sources exist when `use_data_source=true`
   - Provides clear error messages for missing prerequisites
   - Proper transaction handling with rollback on errors

4. **Audit Trail**
   - Creates LLMAuditLog entries for all generations
   - Tracks distribution achieved vs requested
   - Records user, timestamp, and metadata

### 3. Request Model
```python
class IntelligentSamplingRequest(BaseModel):
    target_sample_size: int
    use_data_source: bool = True  # Use actual data or mock
    distribution: Optional[Dict[str, float]] = None  # Custom distribution
    include_file_samples: bool = False  # Include uploaded samples
```

### 4. Response Format
```json
{
    "samples_generated": 100,
    "distribution_achieved": {
        "clean": {"count": 30, "percentage": 30.0, "target_percentage": 30.0},
        "anomaly": {"count": 50, "percentage": 50.0, "target_percentage": 50.0},
        "boundary": {"count": 20, "percentage": 20.0, "target_percentage": 20.0}
    },
    "generation_summary": {
        "total_requested": 100,
        "total_generated": 100,
        "generation_quality": 0.95,
        "data_source_config": {...}
    },
    "message": "Successfully generated 100 samples using intelligent sampling"
}
```

## Lessons Applied from Planning Phase

### 1. **No Background Jobs**
- Intelligent sampling runs synchronously in the request handler
- Avoids all SQLAlchemy session management issues from planning phase
- Simpler error handling and immediate feedback

### 2. **Proper JSONB Updates**
- Uses `flag_modified(phase, 'phase_data')` consistently
- Updates timestamps and user IDs on all modifications
- Stores comprehensive metadata for audit trail

### 3. **Data Source Connection**
- Properly queries planning phase for data sources
- Handles missing data sources gracefully
- Clear error messages guide users

### 4. **Error Handling**
- Comprehensive try-catch with proper rollback
- Detailed logging at each step
- User-friendly error messages

### 5. **Phase Management**
- Correctly queries WorkflowPhase by cycle_id and report_id
- Never constructs phase_id manually
- Handles missing phases appropriately

## Usage Examples

### 1. Generate with Mock Data
```bash
curl -X POST "http://localhost:8000/api/v1/sample-selection/cycles/1/reports/1/samples/generate-intelligent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_sample_size": 100,
    "use_data_source": false
  }'
```

### 2. Generate with Data Source
```bash
curl -X POST "http://localhost:8000/api/v1/sample-selection/cycles/1/reports/1/samples/generate-intelligent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_sample_size": 100,
    "use_data_source": true
  }'
```

### 3. Generate with Custom Distribution
```bash
curl -X POST "http://localhost:8000/api/v1/sample-selection/cycles/1/reports/1/samples/generate-intelligent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_sample_size": 100,
    "use_data_source": false,
    "distribution": {
      "clean": 0.4,
      "anomaly": 0.4,
      "boundary": 0.2
    }
  }'
```

### 4. Include Uploaded File Samples
```bash
curl -X POST "http://localhost:8000/api/v1/sample-selection/cycles/1/reports/1/samples/generate-intelligent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_sample_size": 100,
    "use_data_source": false,
    "include_file_samples": true
  }'
```

## Testing

A comprehensive test script is provided at `/test_intelligent_sampling.py`:

```bash
# Set auth token
export AUTH_TOKEN="your-token-here"

# Run all tests
python test_intelligent_sampling.py
```

The test script covers:
1. Mock data generation
2. Custom distribution
3. File sample inclusion
4. Data source integration
5. Result verification

## Integration with Frontend

The frontend component `IntelligentSamplingPanel.tsx` already exists but currently uses mock API calls. To integrate:

1. Update the API endpoint from mock to real:
   ```typescript
   // Change from mock
   api.createSamplingJob(config)
   
   // To real endpoint
   api.post('/sample-selection/cycles/{cycleId}/reports/{reportId}/samples/generate-intelligent', {
     target_sample_size: config.target_sample_size,
     use_data_source: true,
     distribution: {
       clean: config.normal_percentage / 100,
       anomaly: config.anomaly_percentage / 100,
       boundary: config.boundary_percentage / 100
     }
   })
   ```

2. The frontend already supports:
   - Custom distribution sliders
   - Multiple sampling strategies
   - Real-time progress tracking
   - Sample preview and export

## Benefits

1. **Consistent Sample Quality**: 30/50/20 distribution ensures comprehensive testing coverage
2. **Flexibility**: Supports multiple data sources and custom distributions
3. **Auditability**: Complete audit trail of all sample generations
4. **Error Prevention**: Applies all lessons learned from planning phase issues
5. **User Guidance**: Clear error messages help users understand prerequisites

## Future Enhancements

1. **Profiling Integration**: Connect to data profiling results for smarter anomaly detection
2. **Background Processing**: Add optional async processing for large sample sets
3. **Sample Caching**: Cache generated samples for reuse across versions
4. **Advanced Strategies**: Add more sophisticated sampling algorithms
5. **Export Formats**: Support multiple export formats (CSV, JSON, Excel)