# Data Continuity & Test Data Selection Analysis

## 🎯 **Overview**

This document details how test data selection and continuity is handled across all 9 phases of the SynapseDTE workflow, ensuring realistic data flows and dependencies.

## 📊 **Data Flow Architecture**

### **Core Data Identifiers Tracked:**
```
test_cycle_id ──┐
report_id (156) ├─── Core Workflow Context
cycle_report_id ┘
workflow_id
```

### **Phase-to-Phase Data Dependencies:**
```
Planning ──→ Scoping ──→ Sample Selection ──→ Data Owner Assignment
    │            │              │                     │
    ├─ Test Plan │              │                     │
    └─ Success   ├─ Attributes  │                     │
       Criteria  └─ Decisions   ├─ Sample Set        │
                                └─ Generated Samples  ├─ Assignments
                                                      └─ Mappings
                ┌─────────────────────────────────────┘
                │
                ▼
Request Information ──→ Test Execution ──→ Observation Management
        │                     │                    │
        ├─ Source Info        │                    │
        └─ Documentation      ├─ Test Cases       │
                              ├─ Test Results     ├─ Observations
                              └─ Execution Data   └─ Approvals
                    ┌─────────────────────────────┘
                    │
                    ▼
Generate Test Report ──→ Final Review
        │                      │
        ├─ Report Sections     │
        └─ Report Metadata     ├─ Review Decisions
                               └─ Final Status
```

## 🔗 **Phase-by-Phase Data Continuity**

### **Phase 1: Planning**
**Data Generated:**
- `planning_id` - Unique identifier for the test plan
- `test_plan_data` - Comprehensive planning information
- `target_sample_size` - Used in Sample Selection phase
- `expected_test_count` - Validated in Test Execution phase

**Data Used in Later Phases:**
```json
{
  "target_sample_size": 100,     // → Sample Selection phase
  "expected_test_count": 50,     // → Test Execution validation
  "success_criteria": "...",     // → Final Review phase
  "timeline_estimate": "14 days" // → Overall workflow tracking
}
```

### **Phase 2: Scoping**
**Data Input Dependencies:**
- `planning_id` from Phase 1 (prerequisite validation)
- `report_id` (156) - Gets actual attributes from database

**Data Generated:**
- `scoping_submission_id` - Tracks scoping decisions
- `selected_attributes[]` - Specific attributes chosen for testing
- `scoping_decisions[]` - Detailed decisions per attribute

**Selection Logic:**
```python
# Intelligent attribute selection based on risk
for i, attr in enumerate(available_attributes[:15]):
    risk_level = "high" if i < 5 else "medium" if i < 10 else "low"
    priority = "critical" if i < 3 else "high" if i < 8 else "medium"
    
    decision = {
        "attribute_id": attr["attribute_id"],
        "risk_level": risk_level,
        "testing_priority": priority,
        "sample_size_allocation": target_sample_size // num_attributes_selected
    }
```

**Data Used in Later Phases:**
- `selected_attributes` → Data Owner Assignment (which attributes need owners)
- `scoping_decisions` → Sample Selection (sample allocation per attribute)
- `risk_levels` → Test Execution (test intensity based on risk)

### **Phase 3: Sample Selection**
**Data Input Dependencies:**
- `selected_attributes` from Scoping phase
- `sample_size_allocation` per attribute from scoping decisions
- `target_sample_size` from Planning phase

**Data Generation Process:**
```python
# Uses scoped attributes for targeted sample generation
sample_generation_data = {
    "attribute_ids": [attr["attribute_id"] for attr in selected_attributes],
    "sample_size": total_sample_allocation,
    "sampling_method": "risk_weighted_stratified",
    "criteria": {
        "priority_weighting": {
            "critical": 0.5,  # 50% of samples for critical attributes
            "high": 0.3,      # 30% for high priority
            "medium": 0.2     # 20% for medium priority
        }
    }
}
```

**Data Generated:**
- `sample_set_id` - Identifier for the generated sample set
- `generated_samples[]` - Actual sample records with metadata
- `sample_metadata` - Generation parameters and statistics

**Data Lineage Tracking:**
```python
# Maps samples back to their source attributes
self.data_lineage["samples_generated_to_executed"] = {
    sample_id: {
        "attribute_id": sample.get("attribute_id"),
        "risk_level": sample.get("risk_level"),
        "sample_data": sample
    }
    for sample in generated_samples
}
```

### **Phase 4: Data Owner Assignment**
**Data Input Dependencies:**
- `selected_attributes` from Scoping (what needs data owners)
- `risk_level` and `priority` from scoping decisions

**Assignment Logic:**
```python
# Assigns data owners based on scoped attributes
for attr in selected_attributes:
    assignment = {
        "attribute_id": attr["attribute_id"],
        "data_owner_email": "data.provider@example.com",
        "priority": attr["priority"],  # From scoping decisions
        "risk_level": attr["risk_level"],  # From scoping decisions
        "expected_response_time": "72h" if priority == "critical" else "120h"
    }
```

**Data Generated:**
- `assignment_ids[]` - Tracking assignment records
- `data_owner_mappings{}` - Maps attribute_id → data_owner_email
- `notification_ids[]` - Tracks sent notifications

### **Phase 5: Request Information**
**Data Input Dependencies:**
- `assigned_attributes` from Data Owner Assignment
- `data_owner_mappings` to know who should respond

**Data Generated Per Assignment:**
```python
submission_data = {
    "attribute_ids": [assigned attributes],
    "source_system": "Core Banking System v2.1",
    "data_lineage": "Detailed lineage for assigned attributes",
    "control_framework": "SOX controls specific to these attributes",
    # ... tailored to the specific assigned attributes
}
```

### **Phase 6: Test Execution**
**Data Input Dependencies:**
- `sample_set_id` from Sample Selection (what to test)
- `selected_attributes` from Scoping (what to validate)
- `source_information` from Request Information (how to test)

**Test Case Generation:**
```python
# Generates test cases based on samples and attributes
test_generation_data = {
    "sample_set_id": self.data_tracker.phase_data["sample_selection"]["sample_set_id"],
    "attribute_ids": [attr["attribute_id"] for attr in selected_attributes],
    "test_types": ["completeness", "accuracy", "validity", "consistency"],
    "source_metadata": submission_data_from_phase_5
}
```

**Result Tracking:**
```python
# Maps test results back to original samples and attributes
test_results = [
    {
        "test_case_id": generated_test_case_id,
        "sample_id": original_sample_id,
        "attribute_id": source_attribute_id,
        "result": "pass/fail",
        "details": "Specific validation details"
    }
]
```

### **Phase 7: Observation Management**
**Data Input Dependencies:**
- `test_results` from Test Execution (failures create observations)
- `attribute_metadata` from earlier phases for context

**Observation Creation Logic:**
```python
# Creates observations only for failed test cases
for test_result in test_results:
    if test_result["result"] == "fail":
        observation = {
            "title": f"Issue in {get_attribute_name(test_result['attribute_id'])}",
            "affected_attributes": [test_result["attribute_id"]],
            "sample_ids": [test_result["sample_id"]],
            "test_case_reference": test_result["test_case_id"],
            "severity": determine_severity_from_risk_level(attribute_risk),
            # ... uses data from all previous phases for context
        }
```

## 📈 **Data Validation & Continuity Checks**

### **Prerequisites Validation:**
```python
def validate_data_continuity(self, phase_name: str) -> List[str]:
    issues = []
    
    if phase_name == "scoping":
        if not self.phase_data["planning"]["planning_id"]:
            issues.append("Planning phase data missing")
    
    elif phase_name == "sample_selection":
        if not self.phase_data["scoping"]["selected_attributes"]:
            issues.append("No attributes scoped for sample selection")
    
    elif phase_name == "test_execution":
        if not self.phase_data["sample_selection"]["sample_set_id"]:
            issues.append("No sample set for testing")
        if not self.phase_data["request_information"]["submission_ids"]:
            issues.append("No source information for testing")
    
    return issues
```

### **Cross-Phase Data Lineage:**
```python
self.data_lineage = {
    "attributes_scoped_to_tested": {
        attribute_id: {
            "risk_level": from_scoping,
            "sample_allocation": from_scoping,
            "data_owner": from_assignment,
            "test_results": from_execution
        }
    },
    "samples_generated_to_executed": {
        sample_id: {
            "attribute_id": source_attribute,
            "test_cases": [generated_test_cases],
            "results": [test_outcomes]
        }
    }
}
```

## 🔄 **Real-Time Data Flow Tracking**

### **Flow Logging:**
```python
def log_data_flow(self, from_phase: str, to_phase: str, data_type: str, count: int):
    flow_record = {
        "from_phase": from_phase,
        "to_phase": to_phase,
        "data_type": data_type,
        "count": count,
        "timestamp": datetime.now().isoformat()
    }
    
    # Example: "Scoping → Sample Selection | attributes_selected: 15 items"
```

### **Background Job Tracking:**
```python
# Tracks LLM jobs, sample generation, report generation
self.background_jobs[job_id] = {
    "phase": current_phase,
    "input_data": {
        "attribute_count": len(selected_attributes),
        "sample_count": len(generated_samples)
    },
    "output_data": job_results,
    "duration": execution_time
}
```

## 📊 **Comprehensive Reporting**

### **Data Continuity Report Structure:**
```json
{
  "data_continuity_analysis": {
    "attributes_flow": {
      "total_available": "From Report 156",
      "scoped_for_testing": 15,
      "assigned_data_owners": 15,
      "samples_generated": 150,
      "test_cases_created": 75,
      "observations_created": 3
    },
    "phase_dependencies": {
      "planning_to_scoping": [
        {"data_type": "target_sample_size", "value": 100}
      ],
      "scoping_to_sample_selection": [
        {"data_type": "attributes_selected", "count": 15}
      ]
    }
  }
}
```

## ✅ **Key Improvements in Data Continuity**

### **1. Actual Data Usage:**
- Uses **real Report 156 attributes** instead of hardcoded values
- **Dynamically selects** based on availability and risk
- **Tracks actual IDs** generated by the system

### **2. Intelligent Selection Logic:**
- **Risk-based attribute selection** (high/medium/low)
- **Priority-weighted sampling** (critical/high/medium)
- **Proportional allocation** based on planning targets

### **3. Comprehensive Tracking:**
- **End-to-end lineage** from attributes → samples → tests → observations
- **Cross-phase validation** ensures prerequisites are met
- **Real-time monitoring** of data flows between phases

### **4. Realistic Dependencies:**
- **Sample size** from planning used in sample selection
- **Scoped attributes** drive data owner assignments
- **Test failures** create specific observations with context

### **5. Data Integrity Validation:**
- **Prerequisites checking** before each phase
- **Data consistency** validation across phases
- **Missing data detection** with specific error messages

This enhanced approach ensures that **every piece of data flows logically** from phase to phase, creating a **realistic and traceable** end-to-end workflow that mirrors real-world usage patterns.
