# Intelligent Sampling V2 Implementation

## Overview

This document describes the enhanced intelligent sampling implementation that addresses the requirements:
1. Uses background jobs for handling large datasets (30-40M records)
2. Applies 30/50/20 distribution per non-PK attribute
3. Documents clear rationale and category for each sample

## Key Features

### 1. Background Job Processing
- Handles large datasets without blocking the API
- Provides real-time progress updates
- Follows all async patterns learned from planning phase issues

### 2. Per-Attribute Distribution
- 30% Clean samples per attribute
- 50% Anomaly samples per attribute  
- 20% Boundary samples per attribute
- Each non-PK attribute gets its own distribution

### 3. Sample Documentation
Each sample includes:
- **Category**: CLEAN, ANOMALY, or BOUNDARY
- **Rationale**: Clear explanation of why the sample was selected
- **Attribute Focus**: Which attribute triggered the selection
- **Risk Score**: 0.0-1.0 indicating risk level
- **Confidence Score**: How confident the system is in the categorization

## Architecture

### Components

1. **API Endpoint**: `/api/v1/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/generate-intelligent`
   - Returns job ID immediately
   - Processing happens in background

2. **Background Task**: `execute_intelligent_sampling_task`
   - Properly manages database sessions
   - Updates job progress throughout
   - Handles errors gracefully

3. **V2 Service**: `IntelligentSamplingV2Service`
   - Implements per-attribute sampling logic
   - Generates samples with proper categorization
   - Provides detailed rationale for each sample

## Usage

### 1. Start Intelligent Sampling Job

```bash
curl -X POST "http://localhost:8000/api/v1/sample-selection/cycles/1/reports/1/samples/generate-intelligent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_sample_size": 100,
    "use_data_source": true
  }'
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Intelligent sampling job started",
  "status_url": "/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000/status"
}
```

### 2. Monitor Job Progress

```bash
curl "http://localhost:8000/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000/status" \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "job_type": "intelligent_sampling",
  "status": "running",
  "progress_percentage": 45,
  "current_step": "Analyzing attribute: balance",
  "message": ""
}
```

### 3. Get Results

Once completed, retrieve the samples:

```bash
curl "http://localhost:8000/api/v1/sample-selection/cycles/1/reports/1/samples" \
  -H "Authorization: Bearer $TOKEN"
```

## Sample Structure

Each generated sample includes:

```json
{
  "sample_id": "C01_R01_S001",
  "primary_key_value": "MOCK_ANOMALY_balance_1",
  "sample_data": {
    "account_id": "MOCK_ANOMALY_balance_1",
    "balance": -999999
  },
  "generation_method": "Intelligent Sampling",
  "sample_category": "ANOMALY",
  "attribute_focus": "balance",
  "rationale": "Statistical outlier - 3+ standard deviations from mean for attribute 'balance'",
  "risk_score": 0.8,
  "confidence_score": 0.85,
  "anomaly_type": "extreme_outlier"
}
```

## Rationale Examples

### Clean Samples
- "Normal value within expected range for balance"
- "Typical value for transaction_count"
- "Mock clean sample - typical value for customer_segment"

### Anomaly Samples
- "Contains null/missing value for attribute 'account_status'"
- "Statistical outlier - 3+ standard deviations from mean for attribute 'balance'"
- "Violates expected pattern/format for attribute 'phone_number'"
- "Violates business rule constraint for attribute 'credit_limit'"
- "Data quality issue detected for attribute 'date_opened'"

### Boundary Samples
- "Minimum boundary value for balance"
- "Maximum boundary value for transaction_count"
- "Zero/empty value for description"
- "Value near system limit for credit_limit"

## Progress Tracking

The background job provides detailed progress updates:

1. **0-5%**: Initializing
2. **5-10%**: Loading phase data
3. **10-20%**: Loading data source configuration
4. **20-30%**: Loading scoped attributes
5. **30-85%**: Processing attributes (distributed across all attributes)
6. **85-95%**: Saving generated samples
7. **95-100%**: Finalizing and creating audit log

## Error Handling

The system handles various error scenarios:

1. **Missing Data Sources**: Clear message to complete planning phase
2. **No Scoped Attributes**: Prompts to complete scoping first
3. **Database Connection Issues**: Graceful failure with error details
4. **Large Dataset Timeouts**: Configurable timeouts with progress preservation

## Performance Considerations

### For Large Datasets (30-40M records)

1. **Sampling Strategy**: 
   - Doesn't load all records into memory
   - Uses database queries with LIMIT/OFFSET
   - Implements statistical sampling techniques

2. **Progress Updates**:
   - Updates every 1000 records processed
   - Provides ETA based on current speed
   - Allows monitoring through job status API

3. **Resource Management**:
   - Releases database connections properly
   - Implements connection pooling
   - Garbage collects processed batches

## UI Integration

The frontend should display:

1. **Sample Category** - Visual indicator (color/icon)
2. **Rationale** - Clear explanation text
3. **Risk Score** - Progress bar or percentage
4. **Attribute Focus** - Which attribute triggered selection

Example UI components:
- Category badges with colors (Green=Clean, Yellow=Boundary, Red=Anomaly)
- Expandable rationale text
- Risk score heat map
- Attribute grouping/filtering

## Testing

Run the comprehensive test suite:

```bash
python test_intelligent_sampling.py
```

This tests:
- Background job creation and monitoring
- Per-attribute distribution accuracy
- Rationale generation
- Error scenarios
- Large dataset simulation

## Future Enhancements

1. **Profiling Integration**: Use actual profiling results to identify anomalies
2. **ML-Based Selection**: Machine learning to improve sample selection
3. **Custom Rules**: Allow users to define custom selection criteria
4. **Batch Processing**: Process multiple reports in parallel
5. **Sample Caching**: Cache computation-heavy selections