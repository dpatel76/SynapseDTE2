# SynapseDT - Enhanced LLM Integration Guide

## Overview

SynapseDT now features a sophisticated hybrid LLM integration system that optimizes between Claude (Anthropic) and Gemini (Google) based on task requirements, token limits, and performance characteristics.

## Key Features

### 🔄 Hybrid Model Strategy
- **Gemini for Fast Extraction**: Leverages larger token limits (32k) and faster processing for initial attribute extraction
- **Claude for Deep Analysis**: Uses superior reasoning capabilities for comprehensive analysis and critical attribute evaluation
- **Intelligent Model Selection**: Automatically chooses the optimal model based on task type, document size, and criticality

### 📊 Token Limit Optimizations
- **Smart Batching**: Processes attributes in optimized batches to avoid token limits
  - Claude: 8 attributes per batch (conservative for accuracy)
  - Gemini: 50 attributes per batch (leverages larger context window)
- **Document Chunking**: Automatically splits large documents with intelligent overlap
- **Anti-Truncation Mode**: Prevents incomplete responses through careful prompt engineering

### 🎯 Performance Features
- **Cost Tracking**: Real-time monitoring of API costs per model
- **Latency Monitoring**: Performance metrics for optimization
- **Rate Limit Handling**: Exponential backoff and intelligent retry logic
- **Memory Management**: Optimized garbage collection for large document processing

## Configuration

### Environment Variables

```env
# Claude API Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key-here
CLAUDE_MODEL=claude-3-sonnet-20240229
CLAUDE_COMPREHENSIVE_TEMPERATURE=0.1
CLAUDE_COMPREHENSIVE_MAX_TOKENS=8192

# Gemini API Configuration
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=gemini-2.0-flash
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=32000

# Hybrid Analysis Configuration
ENABLE_HYBRID_ANALYSIS=True
EXTRACTION_MODEL=gemini-2.0-flash
ANALYSIS_MODEL=claude-3-5-sonnet
MIN_CONFIDENCE_FOR_GEMINI=7.0
CRITICAL_ATTRIBUTES_USE_CLAUDE=True

# Batch Processing Optimization
GEMINI_BATCH_SIZE=50
CLAUDE_BATCH_SIZE=15
CLAUDE_SMART_BATCH_SIZE=8

# Document Processing
MAX_CHUNK_SIZE=3000
CHUNK_OVERLAP=300
MAX_CHUNKS_PER_BATCH=20
API_DELAY=0.1
MAX_CONCURRENT_CALLS=5

# Performance and Monitoring
LLM_AUDIT_ENABLED=True
LLM_PERFORMANCE_TRACKING=True
LLM_COST_TRACKING=True
```

### Advanced Configuration Options

#### Model Selection Strategy
```python
# Automatic model selection based on task
- Attribute Extraction: Gemini (fast, large context)
- Critical Analysis: Claude (accurate, better reasoning)
- Document Processing: Gemini for large docs, Claude for complex extraction
- Batch Analysis: Based on attribute criticality
```

#### Batching Strategy
```python
# Claude Batching (Conservative for Accuracy)
CLAUDE_SMART_BATCH_SIZE=8  # Optimal for detailed analysis
CLAUDE_BATCH_SIZE=15       # Maximum for simple tasks

# Gemini Batching (Aggressive for Speed)
GEMINI_BATCH_SIZE=50       # Leverages large context window
```

## Usage Examples

### 1. Attribute Generation with Hybrid Analysis

```python
from app.services.llm_service import llm_service

# Generate attribute list using fast extraction
attributes = await llm_service.generate_attribute_list(
    regulatory_specification="FR Y-14M Schedule D.1...",
    document_context="Credit card reporting requirements...",
    use_fast_extraction=True  # Uses Gemini
)

# Analyze attributes with hybrid approach
analyzed_attributes = await llm_service.analyze_attributes_in_batches(
    attributes=attributes,
    regulatory_context={
        "regulation": "FR Y-14M Schedule D.1",
        "specification_context": "Credit card data reporting"
    },
    document_context="Additional context..."
)
```

### 2. Document Data Extraction

```python
# Extract specific attributes from large documents
extraction_result = await llm_service.extract_document_data(
    document_text=large_document_text,
    target_attributes=["loan_id", "borrower_ssn", "loan_amount"],
    document_type="loan_application"
)

# Results include confidence scores and evidence
print(f"Extracted values: {extraction_result['extracted_values']}")
print(f"Confidence scores: {extraction_result['confidence_scores']}")
print(f"Evidence: {extraction_result['evidence']}")
```

### 3. Performance Monitoring

```python
# Get comprehensive performance metrics
metrics = llm_service.get_performance_metrics()

print(f"Claude metrics: {metrics.get('claude', {})}")
print(f"Gemini metrics: {metrics.get('gemini', {})}")
print(f"Hybrid service status: {metrics['hybrid_service']}")
```

## Optimization Strategies

### Token Limit Management

1. **Document Chunking**
   - Automatically splits documents larger than `MAX_CHUNK_SIZE`
   - Intelligent overlap to maintain context
   - Consolidates results from multiple chunks

2. **Batch Processing**
   - Processes attributes in optimal batch sizes
   - Respects model-specific token limits
   - Includes rate limiting between batches

3. **Prompt Optimization**
   - Concise system prompts for efficiency
   - JSON-only responses to reduce tokens
   - Model-specific prompt engineering

### Cost Optimization

1. **Model Selection**
   ```python
   # Cost-effective model routing
   - Gemini: ~$0.50 per million tokens
   - Claude: ~$3-15 per million tokens
   - Use Gemini for bulk processing, Claude for critical analysis
   ```

2. **Batch Size Optimization**
   ```python
   # Optimal batch sizes to minimize API calls
   Claude: 8 attributes per call (accuracy-focused)
   Gemini: 50 attributes per call (efficiency-focused)
   ```

3. **Real-time Cost Tracking**
   ```python
   # Monitor costs in real-time
   Total cost per request
   Cost breakdown by model
   Usage analytics and trends
   ```

### Performance Optimization

1. **Async Processing**
   - Full async/await implementation
   - Concurrent processing where possible
   - Non-blocking API calls

2. **Memory Management**
   - Automatic garbage collection
   - Memory usage monitoring
   - Chunked processing for large documents

3. **Rate Limit Handling**
   - Exponential backoff for retries
   - Intelligent wait times
   - Model-specific rate limiting

## Error Handling and Fallbacks

### Robust Error Recovery
```python
# Multi-level fallback strategy
1. Retry with exponential backoff
2. Switch to alternative model if available
3. Graceful degradation with partial results
4. Comprehensive error logging and monitoring
```

### Model Availability Handling
```python
# Dynamic model availability
- Auto-detect available models based on API keys
- Graceful fallback if preferred model unavailable
- Clear error messages for configuration issues
```

## Integration Points

### Planning Phase
- **Attribute Generation**: Uses hybrid approach for comprehensive attribute discovery
- **Regulatory Analysis**: Deep analysis of specifications using Claude for accuracy

### Scoping Phase
- **Batch Analysis**: Processes large attribute lists efficiently
- **Priority Scoring**: Uses Claude for critical attribute importance scoring

### Sample Selection Phase
- **Sample Generation**: Leverages Gemini's large context for complex sampling strategies
- **Validation**: Uses Claude for sample validation and quality checks

### Testing Execution Phase
- **Document Extraction**: Hybrid approach based on document size and complexity
- **Comparison Analysis**: Uses Claude for detailed discrepancy analysis

## Monitoring and Analytics

### Performance Metrics
```json
{
  "claude": {
    "model": "claude-3-5-sonnet",
    "metrics": {
      "total_requests": 150,
      "successful_requests": 148,
      "failed_requests": 2,
      "average_latency": 2.3,
      "total_tokens": 45000,
      "total_cost": 0.675
    }
  },
  "gemini": {
    "model": "gemini-2.0-flash",
    "metrics": {
      "total_requests": 300,
      "successful_requests": 295,
      "failed_requests": 5,
      "average_latency": 1.1,
      "total_tokens": 120000,
      "total_cost": 0.060
    }
  }
}
```

### Cost Analytics
- Real-time cost tracking per model
- Usage trends and optimization recommendations
- Budget alerts and cost projections

### Performance Analytics
- Latency trends by model and task type
- Success rates and error analysis
- Token usage efficiency metrics

## Best Practices

### 1. Model Selection
- Use **Gemini** for initial extraction and bulk processing
- Use **Claude** for critical analysis and complex reasoning
- Enable hybrid analysis for optimal results

### 2. Batch Size Configuration
- Start with recommended batch sizes
- Monitor performance and adjust based on your use case
- Consider rate limits and cost implications

### 3. Error Handling
- Always handle `LLMError` exceptions
- Implement fallback strategies for critical operations
- Monitor error rates and adjust retry logic

### 4. Cost Management
- Enable cost tracking for budget monitoring
- Use appropriate models for each task
- Monitor usage patterns and optimize batch sizes

### 5. Performance Optimization
- Enable async processing for better performance
- Use document chunking for large documents
- Monitor memory usage for optimization opportunities

## Troubleshooting

### Common Issues

1. **API Key Configuration**
   ```bash
   # Verify API keys are set correctly
   echo $ANTHROPIC_API_KEY
   echo $GOOGLE_API_KEY
   ```

2. **Rate Limiting**
   ```python
   # Adjust retry settings if hitting rate limits frequently
   LLM_MAX_RETRIES=5
   LLM_RETRY_DELAY=2.0
   ```

3. **Token Limits**
   ```python
   # Reduce batch sizes if hitting token limits
   CLAUDE_SMART_BATCH_SIZE=5
   GEMINI_BATCH_SIZE=30
   ```

4. **Memory Issues**
   ```python
   # Reduce chunk sizes for memory optimization
   MAX_CHUNK_SIZE=2000
   MAX_CHUNKS_PER_BATCH=10
   ```

### Debug Logging
```python
# Enable detailed logging for troubleshooting
import logging
logging.getLogger('app.services.llm_service').setLevel(logging.DEBUG)
```

## Conclusion

The enhanced LLM integration in SynapseDT provides a robust, cost-effective, and performant solution for document analysis and attribute extraction. By leveraging the strengths of both Claude and Gemini, the system delivers optimal results while managing costs and maintaining high availability.

For additional support or questions, please refer to the API documentation or contact the development team. 