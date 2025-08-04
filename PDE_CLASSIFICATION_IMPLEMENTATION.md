# PDE Classification Implementation - Single & Batch Processing

## Overview

This document outlines the comprehensive PDE (Prudential Data Element) classification system that supports both single and batch processing approaches, following the established patterns used throughout the SynapseDTE system.

## 🎯 Key Features

### ✅ Consistent Processing Approach
- **Single Classification**: Individual PDE mapping classification with immediate response
- **Batch Classification**: Background job processing for multiple PDE mappings
- **Unified LLM Service**: Same core classification logic for both approaches
- **Background Job Integration**: Follows established job management patterns

### ✅ Comprehensive Classification Analysis
- **Risk Assessment**: Critical, High, Medium, Low risk levels
- **Information Security Classification**: HRCI, Confidential, Proprietary, Public
- **Regulatory Analysis**: Automatic identification of applicable regulations
- **PII Detection**: Automatic flagging of personally identifiable information
- **Evidence Collection**: Structured evidence and rationale for classifications

### ✅ Performance & Reliability
- **Smart Batching**: Optimal batch sizes (8 mappings per batch)
- **Fallback Mechanisms**: Individual processing if batch fails
- **Progress Tracking**: Real-time progress updates for batch operations
- **Error Handling**: Comprehensive error recovery and fallback classifications

## 🔧 Technical Implementation

### 1. LLM Service Methods

#### Single Classification
```python
async def generate_pde_classification_suggestion(
    self,
    pde_mapping,
    attribute,
    cycle_id: int,
    report_id: int
) -> Dict[str, Any]
```

#### Batch Classification
```python
async def generate_pde_classification_suggestions_batch(
    self,
    pde_mappings: List,
    cycle_id: int,
    report_id: int,
    job_id: Optional[str] = None
) -> List[Dict[str, Any]]
```

### 2. API Endpoints

#### Single Classification Endpoint
```
POST /planning/cycles/{cycle_id}/reports/{report_id}/pde-classifications/suggest?pde_mapping_id=127
```

**Response Format:**
```json
{
    "pde_mapping_id": 127,
    "pde_name": "Credit Card Balance",
    "llm_suggested_criticality": "High",
    "llm_suggested_risk_level": "High",
    "llm_suggested_information_security_classification": "Confidential",
    "llm_regulatory_references": ["FR Y-14M", "Basel III"],
    "llm_classification_rationale": "Detailed explanation...",
    "regulatory_flag": true,
    "pii_flag": false,
    "evidence": {
        "data_sensitivity_indicators": ["Financial data", "Customer account information"],
        "regulatory_scope": ["Banking regulations", "Capital requirements"],
        "business_impact": "High impact on regulatory compliance"
    },
    "security_controls": {
        "required_controls": ["Access logging", "Data encryption"],
        "access_restrictions": "Restricted to authorized personnel"
    }
}
```

#### Batch Classification Endpoint
```
POST /planning/cycles/{cycle_id}/reports/{report_id}/pde-classifications/suggest-batch
```

**Optional Parameters:**
- `pde_mapping_ids`: Array of specific mapping IDs (if empty, processes all mappings)

**Response Format:**
```json
{
    "job_id": "uuid-string",
    "message": "Batch PDE classification started",
    "mappings_to_process": 25,
    "cycle_id": 54,
    "report_id": 156
}
```

### 3. Background Job Processing

#### Job Management
- **Job Creation**: Automatic job ID generation and tracking
- **Progress Updates**: Real-time progress from 5% to 100%
- **Result Storage**: Automatic saving of suggestions to database
- **Error Recovery**: Comprehensive error handling with fallbacks

#### Processing Steps
1. **Initialization** (5%): Setup and validation
2. **Batch Processing** (10-90%): LLM analysis in optimal batches
3. **Database Updates** (90-95%): Saving results to PDE mappings
4. **Completion** (100%): Final status and metrics

## 🎯 Classification Schema

### Criticality Levels
- **Critical**: Essential for regulatory compliance, business operations
- **High**: Important for compliance, significant business impact
- **Medium**: Moderate importance, some business impact
- **Low**: Minimal impact, optional for some processes

### Information Security Classifications
- **HRCI**: Highly Restricted Confidential Information
- **Confidential**: Internal use only, requires protection
- **Proprietary**: Company proprietary information
- **Public**: Can be shared externally

### Evidence Structure
```json
{
    "evidence": {
        "data_sensitivity_indicators": [
            "Customer information",
            "Financial data",
            "Regulatory reporting"
        ],
        "regulatory_scope": [
            "FR Y-14M Schedule D.1",
            "Basel III Capital Requirements"
        ],
        "business_impact": "Description of business impact"
    },
    "security_controls": {
        "required_controls": [
            "Access logging",
            "Data encryption",
            "Regular audits"
        ],
        "access_restrictions": "Role-based access requirements"
    }
}
```

## 🚀 Usage Examples

### Frontend Integration

#### Single Classification
```javascript
const response = await apiClient.post(
    `/planning/cycles/${cycleId}/reports/${reportId}/pde-classifications/suggest?pde_mapping_id=${mappingId}`
);
```

#### Batch Classification
```javascript
// Start batch job
const jobResponse = await apiClient.post(
    `/planning/cycles/${cycleId}/reports/${reportId}/pde-classifications/suggest-batch`,
    { pde_mapping_ids: [127, 128, 129] } // Optional - if empty, processes all
);

// Monitor progress
const jobId = jobResponse.data.job_id;
const progress = await apiClient.get(`/jobs/${jobId}/status`);
```

### Backend Usage

#### Direct LLM Service Usage
```python
from app.services.llm_service import get_llm_service

llm_service = get_llm_service()

# Single classification
suggestion = await llm_service.generate_pde_classification_suggestion(
    pde_mapping=mapping,
    attribute=mapping.attribute,
    cycle_id=54,
    report_id=156
)

# Batch classification
suggestions = await llm_service.generate_pde_classification_suggestions_batch(
    pde_mappings=mappings,
    cycle_id=54,
    report_id=156,
    job_id="optional-job-id"
)
```

## 🔄 Integration with Existing Systems

### Database Integration
- **Automatic Updates**: Classifications saved to PDE mapping records
- **Historical Tracking**: Maintains LLM rationale and references
- **Flag Management**: Automatic setting of regulatory and PII flags

### Activity Management
- **Workflow Integration**: Compatible with existing activity completion patterns
- **Status Tracking**: Integrates with phase status management
- **Audit Trail**: Full audit logging of classification changes

### Background Job System
- **Consistent Patterns**: Uses same job manager as scoping and profiling
- **Progress Tracking**: Real-time updates via established job status API
- **Error Handling**: Follows established error recovery patterns

## 📊 Performance Characteristics

### Batch Processing Efficiency
- **Optimal Batch Size**: 8 mappings per batch for best quality/speed balance
- **Processing Speed**: ~15-30 seconds per batch depending on complexity
- **Fallback Performance**: Individual processing if batch fails
- **Rate Limiting**: Built-in delays to avoid API limits

### Scalability
- **Memory Efficient**: Processes in small batches to manage memory
- **Database Optimized**: Efficient querying with proper relationship loading
- **Parallel Safe**: Can handle multiple concurrent classification jobs

## 🛡️ Error Handling & Reliability

### Fallback Strategies
1. **Batch Failure**: Falls back to individual processing
2. **Individual Failure**: Uses default medium-risk classification
3. **LLM Unavailable**: Provides structured fallback with rationale
4. **Database Errors**: Comprehensive error logging and recovery

### Quality Assurance
- **JSON Validation**: Strict parsing with fallback mechanisms
- **Response Verification**: Validates expected number of classifications
- **Rationale Requirements**: Ensures all classifications have explanations
- **Audit Logging**: Complete logging of all classification activities

## 🔧 Configuration

### Batch Settings
```python
BATCH_SIZE = 8  # Optimal for Claude analysis
RATE_LIMIT_DELAY = 1  # Seconds between batches
MAX_RETRIES = 3  # Retry attempts for failed batches
```

### Classification Defaults
```python
DEFAULT_CRITICALITY = "Medium"
DEFAULT_RISK_LEVEL = "Medium"
DEFAULT_SECURITY_CLASS = "Confidential"
DEFAULT_REGULATORY_FLAG = True
DEFAULT_PII_FLAG = False
```

## 📈 Monitoring & Metrics

### Job Metrics
- **Processing Time**: Total time for batch completion
- **Success Rate**: Percentage of successful classifications
- **Fallback Usage**: Frequency of fallback mechanisms
- **Error Patterns**: Common failure modes and recovery

### Quality Metrics
- **Classification Distribution**: Spread across risk levels
- **Regulatory Coverage**: Percentage with regulatory references
- **PII Detection Rate**: Accuracy of PII flagging
- **User Acceptance**: Manual override frequency

This implementation provides a robust, scalable, and consistent approach to PDE classification that integrates seamlessly with the existing SynapseDTE architecture while following established patterns for background processing and error handling. 