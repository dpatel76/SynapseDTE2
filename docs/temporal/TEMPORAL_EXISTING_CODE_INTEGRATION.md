# Temporal Integration with Existing Code

## Overview

The Temporal workflow integration is designed to **wrap and orchestrate** the existing, tested code rather than replacing it. This document shows exactly how each workflow phase calls the existing functions.

## Architecture Pattern

```
┌─────────────────────┐
│  Temporal Workflow  │
└──────────┬──────────┘
           │ Orchestrates
           ▼
┌─────────────────────┐
│ Temporal Activities │ (Thin wrappers)
└──────────┬──────────┘
           │ Calls
           ▼
┌─────────────────────┐
│ Existing Use Cases  │ (No changes)
│ & Services          │
└──────────┬──────────┘
           │ Uses
           ▼
┌─────────────────────┐
│ Database/Business   │ (Unchanged)
│ Logic               │
└─────────────────────┘
```

## Phase-by-Phase Integration

### 1. Planning Phase

**Workflow Activity**: `planning_activities_wrapper.py`

```python
@activity.defn
async def start_planning_phase_activity(cycle_id, report_id, user_id):
    # Calls existing WorkflowOrchestrator
    orchestrator = get_workflow_orchestrator(db)
    
    # This is the SAME method used by the planning endpoint
    phase = await orchestrator.start_planning_phase(
        cycle_id=cycle_id,
        report_id=report_id,
        notes=request.notes,
        user_id=user.user_id
    )
```

**Existing Code Called**:
- `WorkflowOrchestrator.start_planning_phase()` - app/services/workflow_orchestrator.py
- `WorkflowOrchestrator.get_planning_checklist()` - app/services/workflow_orchestrator.py
- `WorkflowOrchestrator.update_planning_item()` - app/services/workflow_orchestrator.py
- `WorkflowOrchestrator.complete_planning_phase()` - app/services/workflow_orchestrator.py

### 2. Scoping Phase (LLM Attribute Generation)

**Workflow Activity**: `scoping_activities_wrapper.py`

```python
@activity.defn
async def execute_scoping_activities(cycle_id, report_id, user_id):
    # Get the SAME LLM service used by scoping endpoint
    llm_service = get_llm_service()
    
    # Call existing LLM service
    result = await llm_service.generate_test_attributes(
        regulatory_context=report.regulatory_citation,
        report_type=report.report_type,
        business_rules=report.business_rules,
        sample_size=25,
        cycle_id=cycle_id,
        report_id=report_id,
        preferred_provider="claude"
    )
```

**Existing Code Called**:
- `HybridLLMService.generate_test_attributes()` - app/services/llm_service.py
- `WorkflowOrchestrator.create_report_attribute()` - app/services/workflow_orchestrator.py
- `WorkflowOrchestrator.approve_all_attributes()` - app/services/workflow_orchestrator.py

### 3. Sample Selection Phase

**Workflow Activity**: `sample_selection_activities_wrapper.py`

```python
@activity.defn
async def execute_sample_selection_activities(cycle_id, report_id, user_id):
    # Use existing clean architecture use case
    auto_select_use_case = AutoSelectSamplesUseCase()
    
    # Execute with same parameters as UI would
    sample_sets = await auto_select_use_case.execute(
        cycle_id=cycle_id,
        report_id=report_id,
        request_data=request_dto,
        user_id=user_id,
        db=db
    )
```

**Existing Code Called**:
- `StartSampleSelectionPhaseUseCase.execute()` - app/application/use_cases/sample_selection.py
- `AutoSelectSamplesUseCase.execute()` - app/application/use_cases/sample_selection.py
- `ApproveSampleSetUseCase.execute()` - app/application/use_cases/sample_selection.py
- `CompleteSampleSelectionPhaseUseCase.execute()` - app/application/use_cases/sample_selection.py

### 4. Data Owner Identification Phase

**Workflow Activity**: Uses existing endpoints

**Existing Code Called**:
- `assign_data_owners()` - app/api/v1/endpoints/data_owner_clean.py
- `CDOService.auto_assign_data_owners()` - app/services/cdo_service.py
- `NotificationService.notify_data_owners()` - app/services/notification_service.py

### 5. Request for Information Phase

**Workflow Activity**: Uses existing endpoints

**Existing Code Called**:
- `create_information_request()` - app/api/v1/endpoints/request_info_clean.py
- `EmailService.send_rfi_email()` - app/services/email_service.py
- `WorkflowOrchestrator.track_rfi_status()` - app/services/workflow_orchestrator.py

### 6. Test Execution Phase

**Workflow Activity**: Uses existing endpoints

**Existing Code Called**:
- `TestExecutionService.create_test_cases()` - app/services/test_execution_service.py
- `TestExecutionService.execute_tests()` - app/services/test_execution_service.py
- `LLMService.analyze_test_results()` - app/services/llm_service.py

### 7. Observation Management Phase

**Workflow Activity**: Uses existing endpoints

**Existing Code Called**:
- `ObservationService.create_observation()` - app/services/observation_service.py
- `ObservationService.group_observations()` - app/services/observation_service.py
- `WorkflowOrchestrator.review_observations()` - app/services/workflow_orchestrator.py

### 8. Finalize Test Report Phase

**Workflow Activity**: Uses existing endpoints

**Existing Code Called**:
- `ReportGenerationService.generate_final_report()` - app/services/report_generation_service.py
- `LLMService.generate_executive_summary()` - app/services/llm_service.py
- `WorkflowOrchestrator.complete_test_cycle()` - app/services/workflow_orchestrator.py

## Key Benefits

### 1. **Zero Code Duplication**
- All business logic remains in existing services
- Temporal activities are thin wrappers only

### 2. **Preserves All Features**
- Audit trails continue to work
- Notifications are sent as before
- Permissions and RBAC are enforced
- Database transactions are handled correctly

### 3. **Maintains Testing**
- Existing unit tests for services remain valid
- Integration tests continue to pass
- Only need to add tests for the wrapper activities

### 4. **Easy Rollback**
- Can disable Temporal and revert to manual process
- No changes to core business logic
- UI can work with or without Temporal

## Example: How LLM Service is Called

**Original Scoping Endpoint** (app/api/v1/endpoints/scoping_clean.py):
```python
@router.post("/generate-attributes")
async def generate_test_attributes(request: GenerateAttributesRequest):
    llm_service = get_llm_service()
    result = await llm_service.generate_test_attributes(...)
    return result
```

**Temporal Activity Wrapper** (app/temporal/activities/scoping_activities_wrapper.py):
```python
@activity.defn
async def execute_scoping_activities(...):
    # SAME service, SAME method
    llm_service = get_llm_service()
    result = await llm_service.generate_test_attributes(...)
    return result
```

## Verification Checklist

✅ **WorkflowOrchestrator** - All phase state management preserved
✅ **HybridLLMService** - LLM calls unchanged
✅ **Clean Architecture Use Cases** - Called directly
✅ **Database Models** - No changes required
✅ **Audit Logging** - Continues to work
✅ **Email Notifications** - Sent as before
✅ **RBAC/Permissions** - Enforced at service level
✅ **Error Handling** - Existing try/catch blocks active

## Migration Path

1. **Phase 1**: Temporal wraps existing code (current)
2. **Phase 2**: Monitor and validate behavior
3. **Phase 3**: Optimize where needed (optional)
4. **Phase 4**: Add advanced features (retries, compensation)

The key principle: **Temporal orchestrates, existing code executes**.