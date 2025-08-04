# SynapseDTE Implementation Plan: Metrics, Status Handling, Versioning & LLM Integration

## Executive Summary

Based on comprehensive analysis of the SynapseDTE codebase, this document presents a detailed implementation plan addressing four critical areas: Metrics, Status Handling, Versioning, and LLM Integration. The plan prioritizes quality, completeness, and maintainability while avoiding disruption to working code.

## 1. Metrics System Enhancement

### Current State
- Comprehensive metrics infrastructure exists with role-based dashboards
- Currently using mock data - needs real database integration
- Good foundation with MetricsService and role-specific endpoints

### Implementation Plan

#### Phase 1: Core Metrics Implementation (Week 1-2)
1. **Create Base Metrics Calculation Engine**
   ```python
   # app/services/metrics/base_metrics_calculator.py
   class BaseMetricsCalculator:
       - aggregate_report_metrics()
       - calculate_phase_metrics()
       - calculate_sla_compliance()
       - calculate_error_rates()
   ```

2. **Implement Role-Specific Calculators**
   - TesterMetricsCalculator
   - TestExecutiveMetricsCalculator
   - ReportOwnerMetricsCalculator
   - DataProviderMetricsCalculator
   - DataExecutiveMetricsCalculator

3. **Phase-Level Metrics Tables**
   ```sql
   CREATE TABLE phase_metrics (
       id UUID PRIMARY KEY,
       cycle_id UUID,
       report_id UUID,
       phase_name VARCHAR(50),
       total_attributes INTEGER,
       approved_attributes INTEGER,
       completion_time_minutes INTEGER,
       on_time_completion BOOLEAN,
       submissions_for_approval INTEGER,
       created_at TIMESTAMP
   );
   ```

#### Phase 2: Execution Metrics (Week 3)
1. **Leverage Temporal Workflow Metrics**
   - Integrate WorkflowMetrics model
   - Track start/completion times per activity
   - Calculate phase durations automatically

2. **Create Metrics Aggregation Service**
   ```python
   # app/services/metrics/aggregation_service.py
   - aggregate_by_lob()
   - aggregate_by_report()
   - aggregate_by_test_cycle()
   - calculate_trend_data()
   ```

#### Phase 3: Dashboard Integration (Week 4)
1. **Update MetricsService to use real data**
   - Replace mock data with database queries
   - Implement caching for performance
   - Add real-time metrics updates

2. **Frontend Enhancements**
   - Add drill-down capabilities
   - Implement export functionality
   - Create interactive charts

### Key Metrics by Role

#### Tester Metrics
```yaml
Aggregate:
  - reports_assigned
  - reports_completed
  - observations_confirmed
  
Phase-Specific:
  Planning:
    - total_attributes
    - approved_attributes
    - completion_time
    - on_time_status
  
  Data_Profiling:
    - approved_rules
    - attributes_no_issues
    - attributes_with_anomalies
    
  # ... similar for other phases
```

#### Data Executive (CDO) Metrics
```yaml
LOB-Level:
  - total_assignments
  - sla_breaches
  - resubmission_rate
  
Data_Provider_Performance:
  - response_time
  - quality_score
  - error_rate
```

## 2. Standardized Status Handling Framework

### Current State
- Well-implemented dual state/status tracking
- Some inconsistencies in activity naming and state transitions
- Mix of manual and automated status updates

### Implementation Plan

#### Phase 1: Activity Standardization (Week 1)

1. **Create Activity State Enum**
   ```python
   class ActivityState(str, Enum):
       NOT_STARTED = "Not Started"
       IN_PROGRESS = "In Progress"
       COMPLETED = "Completed"
       REVISION_REQUESTED = "Revision Requested"
   ```

2. **Standardize Activity Names**
   ```yaml
   Planning:
     - activity_start: "Start Planning Phase"
     - activity_review: "Tester Review"
     - activity_approval: "Report Owner Approval"
     - activity_complete: "Complete Planning Phase"
   
   # Repeat for all phases with consistent naming
   ```

3. **Create Activity Transition Rules**
   ```python
   ACTIVITY_TRANSITIONS = {
       "Start Phase": {
           "manual": True,
           "allowed_roles": ["Tester"],
           "next_activity": "auto",
           "updates_phase_state": "In Progress"
       },
       "Tester Review": {
           "manual": False,
           "trigger": "submission",
           "auto_complete": True
       },
       # ... more rules
   }
   ```

#### Phase 2: Automation Framework (Week 2)

1. **Create Activity State Manager**
   ```python
   class ActivityStateManager:
       async def transition_activity(
           self,
           activity_name: str,
           from_state: ActivityState,
           to_state: ActivityState,
           trigger_event: str,
           user_id: Optional[str] = None
       ):
           # Validate transition
           # Update state
           # Trigger next activity if automated
           # Update phase state if needed
   ```

2. **Implement Event-Driven Transitions**
   - Create event listeners for submission, approval, rejection
   - Auto-advance activities based on rules
   - Maintain audit trail

#### Phase 3: Integration (Week 3)

1. **Update WorkflowOrchestrator**
   - Use ActivityStateManager for all transitions
   - Ensure consistent state updates
   - Add validation for manual operations

2. **Frontend Updates**
   - Show activity states clearly
   - Disable/enable actions based on state
   - Real-time status updates

### Activity Automation Rules

```python
AUTOMATION_RULES = {
    "Tester Review": {
        "trigger": "form_submission",
        "auto_complete": True,
        "next_state": "Completed"
    },
    "Report Owner Approval": {
        "trigger": "approval_decision",
        "auto_complete": True,
        "next_state": "Completed"
    },
    "Data Executive Assignment": {
        "trigger": "all_assignments_complete",
        "auto_complete": True,
        "validation": "check_all_lobs_assigned"
    }
}
```

## 3. Consistent Versioning System

### Current State
- Strong implementation for Planning (attributes) and Sample Selection
- Missing versioning in Data Profiling, Testing, and Observations
- Inconsistent approaches across phases

### Implementation Plan

#### Phase 1: Versioning Framework (Week 1)

1. **Create Versioning Mixin**
   ```python
   class VersionedMixin:
       version_number = Column(Integer, default=1)
       is_latest_version = Column(Boolean, default=True)
       version_created_at = Column(DateTime, default=func.now())
       version_created_by = Column(String)
       version_notes = Column(Text)
       change_reason = Column(String)
       parent_version_id = Column(UUID)
       
       def create_new_version(self, reason: str, user_id: str):
           # Logic to create new version
   ```

2. **Create Version History Table**
   ```sql
   CREATE TABLE version_history (
       id UUID PRIMARY KEY,
       entity_type VARCHAR(50),
       entity_id UUID,
       version_number INTEGER,
       change_type VARCHAR(50),
       change_reason TEXT,
       changed_by VARCHAR(255),
       changed_at TIMESTAMP,
       change_details JSONB
   );
   ```

#### Phase 2: Phase-Specific Implementation (Week 2-3)

1. **Data Profiling Versioning**
   ```python
   class DataProfilingRuleVersion(Base, VersionedMixin):
       rule_version_id = Column(UUID, primary_key=True)
       rule_id = Column(UUID)
       attribute_id = Column(UUID)
       rule_definition = Column(JSONB)
       approval_status = Column(String)
   ```

2. **Testing Execution Versioning**
   ```python
   class TestExecutionVersion(Base, VersionedMixin):
       execution_version_id = Column(UUID, primary_key=True)
       execution_id = Column(UUID)
       test_results = Column(JSONB)
       document_results = Column(JSONB)
       database_results = Column(JSONB)
   ```

3. **Observation Versioning**
   ```python
   class ObservationVersion(Base, VersionedMixin):
       observation_version_id = Column(UUID, primary_key=True)
       observation_id = Column(UUID)
       severity = Column(String)
       description = Column(Text)
       resolution = Column(Text)
   ```

#### Phase 3: Version Management Service (Week 4)

1. **Create Unified Version Service**
   ```python
   class VersionManagementService:
       async def create_version(entity_type, entity_id, reason, user_id)
       async def get_version_history(entity_type, entity_id)
       async def compare_versions(version1_id, version2_id)
       async def revert_to_version(entity_type, entity_id, version_number)
   ```

2. **Frontend Version Viewer**
   - Version history dropdown
   - Side-by-side comparison
   - Revert capability (with permissions)
   - Change highlighting

### Versioning Workflow

```yaml
Initial_Creation: v1
User_Makes_Changes: Working on v1
User_Submits: v1 submitted
Reviewer_Requests_Changes: v1 revision requested
User_Resubmits: Creates v2
Reviewer_Approves: v2 marked as approved
Future_Changes: Start from v2, create v3
```

## 4. LLM Integration Optimization

### Current State
- Robust hybrid LLM service with failover
- Good regulation-to-prompt mapping
- Batch sizes hardcoded instead of using configuration
- Missing some batch processing optimizations

### Implementation Plan

#### Phase 1: Configuration Management (Week 1)

1. **Fix Batch Size Configuration**
   ```python
   # app/core/llm_config.py
   class LLMBatchConfig:
       CLAUDE_BATCH_SIZES = {
           "attribute_discovery": 15,
           "attribute_details": 25,
           "scoping": 20,
           "testing": 30
       }
       GEMINI_BATCH_SIZES = {
           "attribute_discovery": 50,
           "attribute_extraction": 100,
           "scoping": 75
       }
   ```

2. **Create Regulation Mapping Config**
   ```python
   REGULATION_PROMPT_MAPPING = {
       "FR Y-14M": {
           "schedules": ["A.1", "A.2", "B.1", "B.2", "C.1", "D.1", "D.2"],
           "prompt_dir": "fr_y_14m",
           "special_handling": {
               "Schedule D.1": "use_enhanced_extraction"
           }
       },
       "CCAR": {
           "schedules": ["1A", "1B", "2A"],
           "prompt_dir": "ccar"
       }
   }
   ```

#### Phase 2: Batch Processing Enhancement (Week 2)

1. **Create Batch Processing Utilities**
   ```python
   class BatchProcessor:
       def __init__(self, provider: str, operation: str):
           self.batch_size = self._get_batch_size(provider, operation)
       
       async def process_in_batches(
           self,
           items: List[Any],
           process_func: Callable,
           progress_callback: Optional[Callable] = None
       ):
           # Smart batching with progress tracking
           # Error handling and retry logic
           # Result aggregation
   ```

2. **Implement Dynamic Batch Sizing**
   ```python
   class DynamicBatchOptimizer:
       def calculate_optimal_batch_size(
           self,
           provider: str,
           prompt_length: int,
           response_complexity: str
       ) -> int:
           # Adjust batch size based on:
           # - Prompt token count
           # - Expected response size
           # - Provider limits
           # - Historical performance
   ```

#### Phase 3: Regulation Support Enhancement (Week 3)

1. **Expand Regulation Support**
   ```python
   # Add support for additional regulations
   SUPPORTED_REGULATIONS = [
       "FR Y-14M",
       "FR Y-14Q",
       "CCAR",
       "DFAST",
       "Basel III",
       "FR Y-9C"
   ]
   ```

2. **Create Prompt Template System**
   ```python
   class PromptTemplateManager:
       def get_regulation_prompt(
           self,
           regulation: str,
           schedule: str,
           operation: str,
           context: Dict[str, Any]
       ) -> str:
           # Load regulation-specific template
           # Apply context variables
           # Handle fallbacks
   ```

### LLM Integration Best Practices

```python
# Example of optimized LLM call
async def process_attributes_with_llm(attributes: List[ReportAttribute]):
    llm_service = get_llm_service()
    batch_processor = BatchProcessor("claude", "attribute_analysis")
    
    results = await batch_processor.process_in_batches(
        items=attributes,
        process_func=llm_service.analyze_attribute,
        progress_callback=update_job_progress
    )
    
    # Store results with versioning
    for result in results:
        await create_attribute_version(result, reason="LLM Enhancement")
```

## Implementation Timeline

### Month 1: Foundation
- Week 1-2: Metrics calculation engine and role-specific calculators
- Week 3-4: Status handling standardization and automation rules

### Month 2: Core Features
- Week 1-2: Versioning framework and phase implementations
- Week 3-4: LLM configuration fixes and batch optimization

### Month 3: Integration & Polish
- Week 1-2: Frontend updates for all features
- Week 3-4: Testing, documentation, and deployment

## Risk Mitigation

1. **Backward Compatibility**
   - Maintain existing APIs during transition
   - Use feature flags for gradual rollout
   - Keep legacy fields until migration complete

2. **Performance Impact**
   - Implement caching for metrics calculations
   - Use async operations throughout
   - Add database indexes for new queries

3. **Data Migration**
   - Create migration scripts for versioning
   - Backfill historical versions where possible
   - Maintain audit trail during migration

## Success Metrics

1. **Metrics System**
   - Real-time dashboard updates < 2 seconds
   - All role-specific metrics implemented
   - Historical trend data available

2. **Status Handling**
   - 90% of transitions automated
   - Consistent naming across all phases
   - Clear activity state visibility

3. **Versioning**
   - All phases support versioning
   - Version history accessible in < 1 second
   - Approval workflows create versions

4. **LLM Integration**
   - Batch sizes configurable per operation
   - Support for 6+ regulations
   - 30% reduction in processing time

## Common Mistakes to Avoid

1. **Metrics**
   - Don't calculate on every request - use caching
   - Avoid N+1 queries - use eager loading
   - Don't mix mock and real data

2. **Status Handling**
   - Don't allow invalid state transitions
   - Always maintain audit trail
   - Avoid race conditions in parallel phases

3. **Versioning**
   - Don't delete old versions
   - Always track who made changes
   - Avoid version number gaps

4. **LLM Integration**
   - Don't hardcode batch sizes
   - Always have fallback prompts
   - Monitor API rate limits

## Conclusion

This implementation plan provides a structured approach to enhancing SynapseDTE's metrics, status handling, versioning, and LLM integration. By following this plan and avoiding common pitfalls, we can achieve a robust, scalable system that meets all requirements while maintaining code quality and system stability.