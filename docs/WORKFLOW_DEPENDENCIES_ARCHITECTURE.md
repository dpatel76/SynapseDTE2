# Workflow Dependencies and Parallel Execution Architecture

## Accurate Workflow Structure

The testing workflow is NOT linear - it has parallel execution paths with specific dependencies:

### Phase Dependencies

```
Sequential Phases:
1. Planning → Data Profiling → Scoping → Sample Selection
2. Sample Selection → Data Owner ID (can only start after samples are selected)
3. Observation Management → Finalize Report (report can only start after ALL observations are complete)

Parallel Execution:
- As each data owner is identified → Request Info can begin for that owner
- As each document is uploaded → Testing can begin for those test cases
- As each test case is executed → Observation Management can begin for that test
```

## Visual Workflow Representation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Testing Workflow with Dependencies                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Sequential Foundation:                                                     │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌────────────┐│
│  │  Planning   │───▶│Data Profiling│───▶│   Scoping   │───▶│   Sample   ││
│  │   (Full)    │    │    (Full)    │    │   (Full)    │    │ Selection  ││
│  └─────────────┘    └──────────────┘    └─────────────┘    │   (Full)   ││
│                                                              └──────┬─────┘│
│                                                                     │       │
│  Parallel Execution Streams:                                        ▼       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          Data Owner ID (Audit)                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ Owner 1  │  │ Owner 2  │  │ Owner 3  │  │ Owner N  │          │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │   │
│  └───────┼─────────────┼─────────────┼─────────────┼─────────────────┘   │
│          │             │             │             │                       │
│          ▼             ▼             ▼             ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Request Info (Audit)                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │  Docs 1  │  │  Docs 2  │  │  Docs 3  │  │  Docs N  │          │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │   │
│  └───────┼─────────────┼─────────────┼─────────────┼─────────────────┘   │
│          │             │             │             │                       │
│          ▼             ▼             ▼             ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Test Execution (Audit)                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ Tests 1  │  │ Tests 2  │  │ Tests 3  │  │ Tests N  │          │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │   │
│  └───────┼─────────────┼─────────────┼─────────────┼─────────────────┘   │
│          │             │             │             │                       │
│          ▼             ▼             ▼             ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   Observation Management (Full)                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │  Obs 1   │  │  Obs 2   │  │  Obs 3   │  │  Obs N   │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    │                                       │
│                                    ▼                                       │
│                          ┌─────────────────┐                              │
│                          │ Finalize Report │ (Starts only after          │
│                          │     (Full)      │  ALL observations           │
│                          │  Tester→Exec    │  are complete)              │
│                          └─────────────────┘                              │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Workflow Rules

### 1. Sequential Dependencies
- **Planning → Data Profiling → Scoping → Sample Selection** must be completed in order
- **Sample Selection MUST be complete** before Data Owner ID can begin
- **ALL Observations MUST be complete** before Finalize Report can begin

### 2. Parallel Execution Rules

#### Data Owner ID → Request Info
```
For each data owner identified:
  - Request Info phase can begin immediately for that owner
  - Other data owners don't need to be identified first
  - Each owner's request info process is independent
```

#### Request Info → Test Execution
```
For each document uploaded:
  - Testing can begin immediately for test cases using that document
  - Don't need to wait for all documents
  - Each document enables its associated test cases
```

#### Test Execution → Observation Management
```
For each test case executed:
  - Observations can be created immediately
  - Don't need to wait for all tests to complete
  - Each test result can generate observations in real-time
```

## Database Design Implications

### 1. Phase Dependency Tracking

```sql
CREATE TABLE phase_dependencies (
    dependency_id UUID PRIMARY KEY,
    cycle_id UUID NOT NULL,
    report_id UUID NOT NULL,
    
    -- Phase relationship
    predecessor_phase VARCHAR(50) NOT NULL,
    successor_phase VARCHAR(50) NOT NULL,
    dependency_type VARCHAR(20) NOT NULL, -- 'sequential', 'parallel'
    
    -- Dependency status
    predecessor_status VARCHAR(20),
    can_start BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    UNIQUE(cycle_id, report_id, predecessor_phase, successor_phase)
);
```

### 2. Parallel Execution Tracking

```sql
CREATE TABLE parallel_phase_instances (
    instance_id UUID PRIMARY KEY,
    cycle_id UUID NOT NULL,
    report_id UUID NOT NULL,
    phase_name VARCHAR(50) NOT NULL,
    
    -- Instance context (what this instance is for)
    context_type VARCHAR(50), -- 'data_owner', 'document', 'test_case'
    context_id UUID NOT NULL, -- ID of the owner/document/test
    
    -- Parent instance (what triggered this)
    parent_instance_id UUID,
    parent_phase VARCHAR(50),
    
    -- Status tracking
    instance_status VARCHAR(20),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Ensure uniqueness
    UNIQUE(cycle_id, report_id, phase_name, context_type, context_id)
);
```

### 3. Enhanced Versioning for Parallel Phases

```python
class ParallelPhaseVersion(EnhancedVersionedMixin):
    """Base class for phases that execute in parallel"""
    
    __abstract__ = True
    
    # Instance tracking
    instance_id = Column(UUID, nullable=False)
    context_type = Column(String(50), nullable=False)
    context_id = Column(UUID, nullable=False)
    
    # Parent tracking
    parent_instance_id = Column(UUID)
    parent_phase = Column(String(50))
    
    @property
    def can_start(self):
        """Check if this instance can start based on dependencies"""
        if self.phase_name == "Data Owner ID":
            # Can only start if sample selection is complete
            return self._is_sample_selection_complete()
        elif self.phase_name == "Request Info":
            # Can start if parent data owner is identified
            return self._is_data_owner_identified()
        elif self.phase_name == "Test Execution":
            # Can start if required documents are uploaded
            return self._are_required_documents_available()
        elif self.phase_name == "Observation Management":
            # Can start if parent test is executed
            return self._is_test_executed()
        elif self.phase_name == "Finalize Report":
            # Can only start if ALL observations are complete
            return self._are_all_observations_complete()
        return True
```

## Workflow Orchestration Updates

```python
class EnhancedWorkflowOrchestrator:
    """Orchestrator that handles parallel execution"""
    
    async def check_and_start_dependent_phases(
        self, 
        cycle_id: UUID, 
        report_id: UUID,
        completed_phase: str,
        context: Dict[str, Any]
    ):
        """Start dependent phases when prerequisites are met"""
        
        if completed_phase == "Sample Selection":
            # Start Data Owner ID phase (single instance)
            await self.start_data_owner_id_phase(cycle_id, report_id)
            
        elif completed_phase == "Data Owner ID" and context.get("owner_identified"):
            # Start Request Info for this specific owner
            await self.start_request_info_instance(
                cycle_id, report_id, 
                owner_id=context["owner_id"]
            )
            
        elif completed_phase == "Request Info" and context.get("document_uploaded"):
            # Start Test Execution for test cases using this document
            test_cases = await self.get_test_cases_for_document(
                context["document_id"]
            )
            for test_case in test_cases:
                await self.start_test_execution_instance(
                    cycle_id, report_id,
                    test_case_id=test_case.id,
                    document_id=context["document_id"]
                )
                
        elif completed_phase == "Test Execution" and context.get("test_completed"):
            # Start Observation Management for this test
            await self.start_observation_instance(
                cycle_id, report_id,
                test_execution_id=context["test_execution_id"]
            )
            
        elif completed_phase == "Observation Management":
            # Check if ALL observations are complete
            if await self.are_all_observations_complete(cycle_id, report_id):
                await self.start_finalize_report_phase(cycle_id, report_id)
    
    async def get_phase_progress(
        self, 
        cycle_id: UUID, 
        report_id: UUID, 
        phase_name: str
    ) -> float:
        """Calculate progress for phases with parallel instances"""
        
        if phase_name in ["Data Owner ID", "Request Info", "Test Execution", "Observation Management"]:
            # Calculate based on completed instances
            total_instances = await self.get_total_instances(cycle_id, report_id, phase_name)
            completed_instances = await self.get_completed_instances(cycle_id, report_id, phase_name)
            
            if total_instances == 0:
                return 0.0
            return (completed_instances / total_instances) * 100
        else:
            # Sequential phases use traditional progress calculation
            return await self.get_sequential_phase_progress(cycle_id, report_id, phase_name)
```

## Benefits of This Architecture

1. **Accurate Workflow Modeling**: Reflects the actual parallel nature of the testing process
2. **Efficiency**: Work can begin as soon as prerequisites are met, not waiting for entire phases
3. **Better Progress Tracking**: Can track progress at instance level, not just phase level
4. **Flexibility**: Easy to add new parallel paths or modify dependencies
5. **Clear Dependencies**: Explicit tracking of what can start when

## Implementation Considerations

1. **UI Updates**: Need to show parallel progress streams in the UI
2. **Progress Calculation**: More complex but more accurate
3. **Dependency Validation**: Must validate dependencies before allowing phase transitions
4. **Instance Management**: Need to track and manage multiple instances per phase
5. **Completion Detection**: Must detect when all instances are complete to trigger next phase

This architecture provides a much more accurate representation of your actual workflow and enables the parallel execution that makes the testing process efficient.