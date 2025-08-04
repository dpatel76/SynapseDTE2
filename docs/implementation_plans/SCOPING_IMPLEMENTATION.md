# Scoping Implementation Guide

## **🎯 Complete Scoping Workflow**

### **1. Report-to-Prompt Mapping System**

```python
def get_regulation_prompt_path(report) -> Path:
    """
    Maps specific reports to their regulation-specific prompts
    
    MAPPING STRATEGY:
    1. Primary: report.regulation + report.schedule 
    2. Fallback: report.regulation only
    3. Default: FR Y-14M Schedule D.1
    """
```

**Supported Mappings:**
```
📋 FR Y-14M Schedule D.1 → prompts/regulatory/fr_y_14m/schedule_d_1/scoping_recommendations.txt
📋 FR Y-14M Schedule D.2 → prompts/regulatory/fr_y_14m/schedule_d_2/scoping_recommendations.txt
📋 FR Y-14A Schedule A → prompts/regulatory/fr_y_14a/schedule_a/scoping_recommendations.txt
📋 CCAR → prompts/regulatory/ccar/general/scoping_recommendations.txt
📋 DFAST → prompts/regulatory/dfast/general/scoping_recommendations.txt
```

**Example Mapping Process:**
```
Report ID: 156
Report Name: "Domestic Credit Card Data Collection"
Regulation: "FR Y-14M"
Schedule: "D.1"

MAPPING RESULT:
✅ EXACT MATCH: ('FR Y-14M', 'D.1') → fr_y_14m/schedule_d_1/scoping_recommendations.txt
✅ PROMPT FILE EXISTS: /prompts/regulatory/fr_y_14m/schedule_d_1/scoping_recommendations.txt
```

### **2. Local Risk Scoring Methodology (0-100 Scale)**

```python
def calculate_local_risk_score(attr, cde_attributes, historical_issue_attributes) -> float:
    """
    SCORING BREAKDOWN:
    - Base Score: 20 points (inherent risk)
    - Regulatory Criticality: 0-30 points
    - Data Complexity: 0-20 points  
    - Historical Issues: 0-15 points
    - CDE Status: 0-10 points
    - Mandatory Flag: 0-5 points
    
    Total: 0-100 points
    """
```

**Risk Categorization:**
```
🔴 HIGH RISK (70-100): Critical regulatory fields
   - balance fields (stress testing): 30 pts
   - APR fields (consumer protection): 26 pts
   - credit scores (risk assessment): 24 pts
   
🟡 MEDIUM RISK (50-69): Important operational fields
   - credit limits: 15 pts
   - payment fields: 12 pts
   - rates and fees: 10 pts
   
🟢 LOW RISK (0-49): Administrative fields
   - identifiers: 5 pts
   - geographic data: 3 pts
```

**Example Risk Calculation:**
```
Attribute: "cycle_ending_balance"
- Base Score: 20
- Regulatory (balance field): 30
- Complexity (Decimal): 15
- Historical Issues: 0
- CDE Status: 10
- Mandatory: 5
TOTAL: 80/100 → HIGH RISK → TEST
```

### **3. Modified Prompt Format Integration**

**Your Updated Prompt Expects:**
```json
[
  {
    "attribute_name": "exact_name_from_list",
    "description": "Clear description of the field",
    "risk_score": "Generated from 1-100 range",
    "rationale": "Specific rationale citing FR Y-14M requirements",
    "validation_rules": "Format requirements, valid values, constraints",
    "typical_source_documents": "Credit card system, loan servicing platform",
    "keywords_to_look_for": "Account #, Card Number, Customer ID"
  }
]
```

**Code Processing:**
```python
# Extract from Claude response
risk_score = float(rec_data.get("risk_score", 50.0))
description = rec_data.get("description", f"Credit card data attribute: {attr_name}")
rationale = rec_data.get("rationale", f"Risk assessment for {attr_name}")
validation_rules = rec_data.get("validation_rules", f"Data type: {attr.data_type}")
source_docs = rec_data.get("typical_source_documents", "Credit card system")
keywords = rec_data.get("keywords_to_look_for", f"Account #, {attr_name}")

# Convert 0-100 score to TEST/SKIP
recommendation = "TEST" if risk_score >= 50 else "SKIP"

# Map to priority levels
if risk_score >= 80: priority = "High"
elif risk_score >= 60: priority = "Medium" 
else: priority = "Low"
```

### **4. Complete Workflow Example**

```
🚀 STARTING REAL LLM SCOPING RECOMMENDATIONS GENERATION
================================================================================
📊 STEP 1: DATA ANALYSIS
   Total attributes: 118
   CDE attributes: 23
   Historical issue attributes: 8

📋 STEP 2: REPORT MAPPING
🗺️  REPORT-TO-PROMPT MAPPING:
   📋 Report ID: 156
   📋 Report Name: Domestic Credit Card Data Collection
   📋 Regulation: FR Y-14M
   🏷️  Normalized Regulation: 'FR Y-14M'
   🏷️  Normalized Schedule: 'D.1'
   ✅ EXACT MATCH: ('FR Y-14M', 'D.1') → fr_y_14m/schedule_d_1/scoping_recommendations.txt
   ✅ PROMPT FILE EXISTS: /prompts/regulatory/fr_y_14m/schedule_d_1/scoping_recommendations.txt

🤖 STEP 3: LLM PROCESSING
   Provider: Claude-3.5-Sonnet
   Batch size: 25
   Total batches: 5

📦 Processing batch 1/5 (25 attributes)
================================================================================
📤 SENDING REAL PROMPT TO CLAUDE (Batch 1)
================================================================================
📏 Prompt length: 2847 characters
📝 Prompt preview (first 500 chars):
You are a Federal Reserve FR Y-14M Schedule D - Domestic Credit Card Data Collection...

🔄 Making Claude API call for batch 1...
✅ Claude API call completed in 3.42s
💰 Batch cost: $0.0234, Total cost so far: $0.0234
📄 Claude response length: 4567 characters
✅ Parsed 25 recommendations from Claude

🔢 STEP 4: RISK SCORING
   Scale: 0-100 points
   Threshold: ≥50 = TEST, <50 = SKIP

✅ Batch 1 completed: 25 recommendations processed
...

🎉 REAL LLM SCOPING RECOMMENDATIONS COMPLETED
📊 Total time: 18.42s
💰 Total cost: $0.1156
✅ Recommended for testing: 97
❌ Recommended to skip: 21
================================================================================
```

### **5. Fallback Strategy**

**If LLM Call Fails:**
```python
# Fallback: Use local risk scoring methodology
logger.info("🔄 Using local risk scoring methodology as fallback")
for attr in batch_attributes:
    local_score = calculate_local_risk_score(attr, cde_attributes, historical_issue_attributes)
    batch_recommendations.append({
        "attribute_name": attr.attribute_name,
        "description": attr.description or f"Credit card data attribute: {attr.attribute_name}",
        "risk_score": local_score,
        "rationale": f"Local risk assessment. Score: {local_score}/100 based on regulatory factors.",
        "validation_rules": f"Data type: {attr.data_type}, Mandatory: {attr.mandatory_flag}",
        "typical_source_documents": "Credit card system, loan servicing platform",
        "keywords_to_look_for": f"Account #, {attr.attribute_name}, Customer ID"
    })
```

### **6. Key Benefits**

✅ **Regulation-Specific**: Automatically selects correct prompt based on report metadata
✅ **Robust Fallback**: Local risk scoring if LLM unavailable  
✅ **0-100 Scale**: Consistent risk scoring across all methods
✅ **Real LLM Integration**: Actual Claude API calls with cost tracking
✅ **Comprehensive Logging**: Full visibility into decision process
✅ **Extensible Mapping**: Easy to add new regulations/schedules

### **7. Adding New Regulations**

**Step 1: Create Prompt File**
```
prompts/regulatory/new_regulation/schedule_x/scoping_recommendations.txt
```

**Step 2: Add Mapping**
```python
prompt_mappings = {
    # Add new mapping
    ("NEW REGULATION", "SCHEDULE X"): "new_regulation/schedule_x/scoping_recommendations.txt",
    # ... existing mappings
}
```

**Step 3: Test**
```python
# Report with new regulation will automatically use new prompt
report.regulation = "NEW REGULATION"
report.schedule = "SCHEDULE X"
# System automatically maps to correct prompt
``` 