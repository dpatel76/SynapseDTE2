# LLM Integration Configuration Analysis for SynapseDTE

## Executive Summary

This document provides a comprehensive analysis of the LLM integration configuration in SynapseDTE, focusing on:
1. How regulation fields in reports map to prompt directories
2. Batch size configurations for different LLM operations
3. Hardcoded batching parameters that should be moved to configuration
4. Regulation-specific prompt loading logic
5. Prompt directory structure and mapping mechanisms

The analysis reveals several inconsistencies between configured and hardcoded batch sizes, as well as opportunities to improve the centralization of LLM operations.

## 1. Regulation Field Mapping to Prompt Directories

### 1.1 How Regulation Mapping Works

The regulation field in reports maps to prompt directories through the `PromptManager` class in `app/core/prompt_manager.py`.

#### Directory Structure:
```
prompts/
├── regulatory/
│   ├── fr_y_14m/
│   │   ├── common/
│   │   ├── schedule_a_1/
│   │   ├── schedule_a_2/
│   │   ├── schedule_b_1/
│   │   ├── schedule_b_2/
│   │   ├── schedule_c_1/
│   │   ├── schedule_d_1/
│   │   └── schedule_d_2/
│   └── [other_regulations]/
├── claude/
├── gemini/
└── [generic prompts]
```

#### Mapping Process:
1. **Normalization**: Regulation names are normalized (e.g., "FR Y-14M" → "fr_y_14m")
2. **Schedule Handling**: Dots in schedules are replaced with underscores (e.g., "Schedule D.1" → "schedule_d_1")
3. **Path Resolution Priority**:
   - First tries: `regulatory/{regulation}/{schedule}/{template_name}.txt`
   - Falls back to: `regulatory/{regulation}/common/{template_name}.txt`
   - Final fallback: `prompts/{template_name}.txt`

#### Key Code from `prompt_manager.py`:
```python
def _get_template_path(self, template_name: str, regulatory_report: Optional[str] = None,
                      schedule: Optional[str] = None) -> Optional[Path]:
    # Normalize regulatory report name (e.g., "FR Y-14M" -> "fr_y_14m")
    report_dir = regulatory_report.lower().replace(' ', '_').replace('-', '_')
    
    if schedule:
        # Handle dots in schedule names (e.g., "Schedule D.1" -> "schedule_d_1")
        schedule_dir = schedule.lower().replace(' ', '_').replace('.', '_')
        specific_path = self.prompts_dir / "regulatory" / report_dir / schedule_dir / f"{template_name}.txt"
```

### 1.2 Regulation Detection in LLM Service

The `llm_service.py` detects regulations from context using regex patterns:

```python
def _extract_regulatory_info(self, regulatory_context: str, report_type: str) -> tuple[Optional[str], Optional[str]]:
    # Common regulatory report patterns
    report_patterns = [
        (r'FR\s*Y-?14M', 'FR Y-14M'),
        (r'FR\s*Y-?14Q', 'FR Y-14Q'),
        (r'FR\s*Y-?9C', 'FR Y-9C'),
        (r'Call\s*Report', 'Call Report'),
        (r'FFIEC\s*\d+', 'FFIEC'),
        (r'CCAR', 'CCAR'),
        (r'DFAST', 'DFAST')
    ]
    
    # Schedule patterns for FR Y-14M - correct sub-schedules
    schedule_patterns = [
        (r'Schedule\s*A\.1\b', 'schedule_a_1'),
        (r'Schedule\s*D\.1\b', 'schedule_d_1'),
        # ... more patterns
    ]
```

## 2. Batch Size Configurations

### 2.1 Configuration Locations

**In `app/core/config.py`:**
```python
# Batch Configuration for Token Limit Optimization
gemini_batch_size: int = 50
claude_batch_size: int = 15
claude_smart_batch_size: int = 8

# Document Processing Optimization
max_chunk_size: int = 3000
chunk_overlap: int = 300
max_chunks_per_batch: int = 20
```

**In `app/services/llm_service.py` (lines 705-709):**
```python
# Provider-specific batch sizes optimized for context windows
batch_sizes = {
    'gemini': 50,    # Large context window - can handle more attributes
    'claude': 25     # Increased batch size for better completeness while staying within limits
}
batch_size = batch_sizes.get(details_provider_name, 25)
```

**In `app/api/v1/endpoints/scoping.py` (line 666):**
```python
# Process attributes in batches of 20 (reduced from 30)
batch_size = 20
```

**In `app/services/audit_database_service.py` (line 139):**
```python
self.batch_size = getattr(settings, 'audit_batch_size', 100)
```

### 2.2 Inconsistencies Found

1. **Claude Batch Size Mismatch**: 
   - Config defines `claude_batch_size: 15`
   - LLM service hardcodes `'claude': 25`
   - Config also has unused `claude_smart_batch_size: 8`

2. **Hardcoded vs Configurable**:
   - Scoping endpoint hardcodes batch size of 20
   - LLM service hardcodes provider-specific sizes
   - Audit service uses configurable batch size (but `audit_batch_size` not defined in config)

3. **Unused Configuration**:
   - `claude_smart_batch_size` is defined but never used
   - Document processing configs (`max_chunk_size`, `chunk_overlap`, `max_chunks_per_batch`) appear unused

## 3. Hardcoded Batching Parameters

### 3.1 Identified Hardcoded Values

1. **`app/services/llm_service.py`** (lines 706-710):
   - Hardcoded batch sizes in dictionary
   - `gemini`: 50 (matches config value)
   - `claude`: 25 (doesn't match config value of 15)
   - Default: 25

2. **`app/api/v1/endpoints/scoping.py`** (line 666):
   - `batch_size = 20` (hardcoded, no config reference)

3. **`app/api/v1/endpoints/planning.py`**:
   - No batch processing found (processes all attributes at once)

4. **`app/services/audit_database_service.py`** (line 139):
   - Uses configurable value but `audit_batch_size` not defined in config

### 3.2 Configuration Values Not Being Used

From `app/core/config.py`:
- `claude_batch_size: int = 15` - Not used, hardcoded as 25
- `claude_smart_batch_size: int = 8` - Never referenced
- `max_chunks_per_batch: int = 20` - Not found in usage

## 4. Regulation-Specific Prompt Loading

### 4.1 Prompt Types and Their Uses

1. **`attribute_discovery`**: Phase 1 of attribute generation - discovers attribute names
2. **`attribute_batch_details`**: Phase 2 of attribute generation - gets detailed info
3. **`scoping_recommendations`**: Generates test recommendations for attributes
4. **`document_extraction`**: Extracts values from documents
5. **`sample_generation`**: Generates sample data for testing

### 4.2 Prompt Loading Flow

1. **Detection**: `_extract_regulatory_info()` uses regex to detect regulation/schedule
2. **Path Building**: `_get_template_path()` builds path based on regulation/schedule
3. **Loading**: `load_prompt_template()` loads template with caching
4. **Formatting**: `format_prompt()` substitutes variables using Template.safe_substitute()

### 4.3 Example Prompt Structure

From `prompts/regulatory/fr_y_14m/schedule_d_1/attribute_discovery.txt`:
```
CRITICAL INSTRUCTION: Return ONLY a JSON array...

Generate all FR Y-14M Schedule D.1 credit card loan level attributes.

Context: ${report_name} - ${regulatory_context}

Your response must be EXACTLY in this format:
["attribute_1", "attribute_2", "attribute_3", ...]
```

## 5. Prompt Directory Mapping

### 5.1 Current Supported Mappings

From analysis of the codebase, the following regulations are supported:

**FR Y-14M Schedules:**
- Schedule A.1, A.2 (First Lien Mortgages)
- Schedule B.1, B.2 (Home Equity)
- Schedule C.1 (Credit Card)
- Schedule D.1, D.2 (Other Consumer)

**Mapping Examples:**
- "FR Y-14M Schedule D.1" → `prompts/regulatory/fr_y_14m/schedule_d_1/`
- "FR Y-14M" (no schedule) → `prompts/regulatory/fr_y_14m/common/`
- Unknown regulation → `prompts/` (generic prompts)

### 5.2 Scoping Endpoint Regulation Mapping

The scoping endpoint has its own mapping logic in `get_regulation_prompt_path()`:

```python
prompt_mappings = {
    # FR Y-14M mappings
    ("FR Y-14M", "D.1"): "fr_y_14m/schedule_d_1/scoping_recommendations.txt",
    ("FR Y-14M", "D.2"): "fr_y_14m/schedule_d_2/scoping_recommendations.txt",
    # FR Y-14A mappings  
    ("FR Y-14A", "A"): "fr_y_14a/schedule_a/scoping_recommendations.txt",
    # CCAR mappings
    ("CCAR", ""): "ccar/general/scoping_recommendations.txt",
}
```

## 6. Key Findings and Recommendations

### 6.1 Key Findings

1. **Batch Size Inconsistencies**:
   - Configuration defines batch sizes that aren't used
   - Hardcoded values don't match configuration
   - Different endpoints use different hardcoded batch sizes

2. **Regulation Mapping Works Well**:
   - Automatic detection from context
   - Proper fallback hierarchy
   - Support for schedule-specific prompts

3. **Missing Centralization**:
   - Scoping endpoint implements own batch logic
   - No shared batch processing utilities
   - Duplicate prompt loading in different endpoints

### 6.2 Immediate Recommendations

1. **Fix Batch Size Configuration**:
   ```python
   # In llm_service.py, use config values:
   from app.core.config import get_settings
   settings = get_settings()
   
   batch_sizes = {
       'gemini': settings.gemini_batch_size,
       'claude': settings.claude_batch_size
   }
   ```

2. **Add Missing Config Values**:
   ```python
   # In config.py:
   scoping_batch_size: int = 20
   audit_batch_size: int = 100
   ```

3. **Remove Unused Configurations**:
   - Remove `claude_smart_batch_size`
   - Document or implement document chunking configs

### 6.3 Long-term Improvements

1. **Centralize Batch Processing**:
   - Create shared batch processing utilities
   - Move scoping batch logic to LLM service
   - Standardize error handling across batches

2. **Dynamic Batch Sizing**:
   - Adjust batch sizes based on token usage
   - Monitor API rate limits
   - Optimize for cost vs performance

3. **Enhanced Regulation Support**:
   - Add more regulatory reports (FR Y-14Q, FR Y-9C)
   - Support version-specific prompts
   - Auto-update prompts from regulatory specs
## 7. Summary

The SynapseDTE LLM integration has a sophisticated prompt management system with good support for regulation-specific prompts. However, there are several areas for improvement:

1. **Configuration Management**: Batch sizes are defined in config but not consistently used
2. **Code Duplication**: Multiple endpoints implement similar batch processing logic
3. **Hardcoded Values**: Several batch sizes and parameters are hardcoded instead of configurable

The regulation mapping system works well and provides good flexibility for adding new regulatory reports and schedules. The main improvements needed are in centralizing batch processing logic and ensuring configuration values are actually used throughout the codebase.