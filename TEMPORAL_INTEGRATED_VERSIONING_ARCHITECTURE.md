# Temporal-Integrated Versioning Architecture

## Executive Summary

After analyzing the Temporal workflow implementation, I've identified that the system now has:
1. **Temporal Workflows** orchestrating all 9 phases
2. **Workflow tracking tables** (workflow_executions, workflow_steps, workflow_transitions)
3. **Workflow versioning** (V1.0.0, V1.1.0, V1.2.0, V2.0.0)
4. **Human-in-the-loop signals** for approvals

The versioning architecture needs to integrate with, not duplicate, these capabilities.

## Key Integration Points

### 1. Temporal as the Orchestrator

Since Temporal now orchestrates all phase transitions, versioning should be **triggered by Temporal activities** rather than standalone:

```python
# Instead of direct versioning calls
await create_version(data)

# Version creation through Temporal activities
@activity.defn
async def create_planning_version_activity(
    input: PlanningVersionInput
) -> PlanningVersionOutput:
    """Temporal activity that creates a new planning version"""
    async with get_db_session() as db:
        service = UnifiedVersioningService(db)
        version_id = await service.create_version(
            phase="Planning",
            cycle_id=input.cycle_id,
            report_id=input.report_id,
            user_id=input.user_id,
            data=input.planning_data,
            workflow_execution_id=workflow.info().workflow_execution.workflow_id
        )
        return PlanningVersionOutput(version_id=version_id)
```

### 2. Link Versions to Workflow Executions

Enhance the versioning system to track workflow context:

```python
class EnhancedVersionedMixin(VersionedMixin):
    """Enhanced versioning mixin with Temporal integration"""
    
    # Existing versioning fields...
    
    # Temporal integration
    workflow_execution_id = Column(String(255), ForeignKey('workflow_executions.workflow_id'))
    workflow_step_id = Column(UUID, ForeignKey('workflow_steps.step_id'))
    workflow_activity_name = Column(String(100))
    
    # Relationships
    workflow_execution = relationship("WorkflowExecution", back_populates="versions")
    workflow_step = relationship("WorkflowStep", back_populates="versions")
```

### 3. Version-Aware Workflow Activities

Create activities that handle versioning for each phase:

```python
# activities/versioning_activities.py
from temporalio import activity
from app.services.versioning_service import UnifiedVersioningService

class VersioningActivities:
    """Temporal activities for version management"""
    
    @activity.defn
    async def create_sample_selection_version(
        self, input: SampleSelectionVersionInput
    ) -> SampleSelectionVersionOutput:
        """Create new sample selection version with individual decisions"""
        async with get_db_session() as db:
            service = UnifiedVersioningService(db)
            
            # Create version
            version_id = await service.create_version(
                phase="Sample Selection",
                cycle_id=input.cycle_id,
                report_id=input.report_id,
                user_id=input.user_id,
                data={
                    "selection_criteria": input.selection_criteria,
                    "workflow_execution_id": activity.info().workflow_id
                }
            )
            
            # Create individual sample decisions
            for sample in input.samples:
                await service.create_sample_decision(
                    version_id=version_id,
                    sample_data=sample.data,
                    recommendation_source=sample.source,
                    recommended_by=input.user_id
                )
            
            return SampleSelectionVersionOutput(
                version_id=version_id,
                sample_count=len(input.samples)
            )
    
    @activity.defn
    async def approve_version(
        self, input: ApproveVersionInput
    ) -> ApproveVersionOutput:
        """Approve a version through Temporal"""
        async with get_db_session() as db:
            service = UnifiedVersioningService(db)
            
            success = await service.approve_version(
                phase=input.phase_name,
                version_id=input.version_id,
                user_id=input.approver_id,
                notes=input.approval_notes,
                workflow_context={
                    "workflow_id": activity.info().workflow_id,
                    "activity_name": activity.info().activity_type
                }
            )
            
            return ApproveVersionOutput(
                success=success,
                approved_at=datetime.utcnow()
            )
```

### 4. Workflow-Driven Version State Transitions

Integrate version approvals with Temporal signals:

```python
# Enhanced workflow with versioning
class EnhancedTestCycleWorkflowV3:
    """Test cycle workflow with integrated versioning"""
    
    def __init__(self):
        self.current_versions = {}  # Track current version per phase
        self.pending_approvals = {}  # Track pending approvals
    
    @workflow.signal
    async def submit_version_approval(self, approval: VersionApprovalSignal):
        """Handle version approval through workflow signal"""
        phase = approval.phase_name
        
        # Store approval
        if phase not in self.pending_approvals:
            self.pending_approvals[phase] = []
        self.pending_approvals[phase].append(approval)
        
        # Check if approval requirements met
        if self._check_approval_requirements(phase):
            # Execute approval activity
            await workflow.execute_activity(
                approve_version,
                ApproveVersionInput(
                    phase_name=phase,
                    version_id=self.current_versions[phase],
                    approver_id=approval.user_id,
                    approval_notes=approval.notes
                ),
                start_to_close_timeout=timedelta(minutes=5)
            )
    
    async def run_sample_selection_phase(self, input: PhaseInput):
        """Run sample selection with versioning"""
        # Create new version
        result = await workflow.execute_activity(
            create_sample_selection_version,
            SampleSelectionVersionInput(
                cycle_id=input.cycle_id,
                report_id=input.report_id,
                user_id=input.user_id,
                samples=input.samples,
                selection_criteria=input.criteria
            ),
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        self.current_versions["Sample Selection"] = result.version_id
        
        # Wait for approval
        await workflow.wait_condition(
            lambda: self._is_phase_approved("Sample Selection")
        )
```

### 5. Unified Progress Tracking

Combine workflow progress with version status:

```python
class UnifiedProgressService:
    """Service combining workflow and version progress"""
    
    async def get_phase_progress(
        self, cycle_id: int, report_id: int, phase_name: str
    ) -> PhaseProgress:
        """Get comprehensive phase progress"""
        
        # Get workflow progress
        workflow_progress = await self.get_workflow_progress(
            cycle_id, report_id, phase_name
        )
        
        # Get version progress
        version_progress = await self.get_version_progress(
            cycle_id, report_id, phase_name
        )
        
        return PhaseProgress(
            workflow_status=workflow_progress.status,
            workflow_progress=workflow_progress.percentage,
            current_version=version_progress.current_version,
            version_status=version_progress.status,
            pending_approvals=version_progress.pending_approvals,
            approval_history=version_progress.approval_history
        )
```

### 6. Database Schema Updates

Add Temporal context to versioning tables:

```sql
-- Add to version history table
ALTER TABLE version_history ADD COLUMN workflow_execution_id VARCHAR(255);
ALTER TABLE version_history ADD COLUMN workflow_step_id UUID;
ALTER TABLE version_history ADD COLUMN workflow_activity_name VARCHAR(100);

-- Add foreign keys
ALTER TABLE version_history 
ADD CONSTRAINT fk_version_workflow_execution 
FOREIGN KEY (workflow_execution_id) REFERENCES workflow_executions(workflow_id);

ALTER TABLE version_history 
ADD CONSTRAINT fk_version_workflow_step 
FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(step_id);

-- Add indexes
CREATE INDEX idx_version_workflow ON version_history(workflow_execution_id);
CREATE INDEX idx_version_workflow_step ON version_history(workflow_step_id);
```

### 7. Migration Strategy

#### Phase 1: Add Temporal Context (Week 1)
1. Update versioning tables with workflow fields
2. Create version-aware activities
3. Add workflow context to versioning service

#### Phase 2: Integrate Existing Phases (Weeks 2-3)
1. Update Planning phase to use versioning activities
2. Update Data Profiling to use versioning activities
3. Update Scoping to use versioning activities
4. Update Sample Selection with new decision model

#### Phase 3: Parallel Phase Integration (Weeks 4-5)
1. Implement instance-based versioning for parallel phases
2. Add version tracking to Data Owner ID changes
3. Add document versioning to Request Info
4. Add test execution audit versioning

#### Phase 4: Approval Workflow (Week 6)
1. Implement version approval signals
2. Update UI to use workflow signals
3. Add approval dashboard

## Benefits of Temporal Integration

### 1. **Single Source of Truth**
- Temporal workflows drive all version state changes
- No conflicting state between workflow and versioning

### 2. **Automatic Retry and Recovery**
- Failed version operations automatically retried by Temporal
- Workflow can recover from partial failures

### 3. **Better Observability**
- Temporal UI shows version creation/approval flow
- Complete audit trail in workflow history

### 4. **Simplified Code**
- No need for separate approval state machines
- Temporal handles all async operations

### 5. **Scalability**
- Temporal handles distributed execution
- Version operations can scale independently

## Implementation Example

Here's how sample selection would work with integrated versioning:

```python
# Workflow execution
async def run_sample_selection(self, input: WorkflowInput):
    # 1. Create version with samples
    version_result = await workflow.execute_activity(
        create_sample_selection_version,
        SampleSelectionVersionInput(
            cycle_id=input.cycle_id,
            report_id=input.report_id,
            user_id=input.current_user_id,
            samples=await self.generate_samples(input),
            selection_criteria=input.selection_criteria
        )
    )
    
    # 2. Signal for human review
    self.pending_reviews["sample_selection"] = version_result.version_id
    
    # 3. Wait for approval signal
    await workflow.wait_condition(
        lambda: "sample_selection" in self.completed_reviews
    )
    
    # 4. If changes requested, create new version
    if self.review_results["sample_selection"].needs_changes:
        new_version = await workflow.execute_activity(
            create_sample_selection_revision,
            SampleRevisionInput(
                parent_version_id=version_result.version_id,
                additional_samples=self.review_results["sample_selection"].additional_samples,
                rejected_samples=self.review_results["sample_selection"].rejected_samples
            )
        )
```

## Conclusion

By integrating versioning with Temporal workflows:
1. **Eliminate duplicate orchestration** - Temporal drives everything
2. **Maintain version integrity** - All changes tracked through workflows
3. **Simplify implementation** - Less custom code needed
4. **Improve reliability** - Temporal's guarantees apply to versioning
5. **Enable better monitoring** - Single view of workflow and version state

This approach leverages your existing Temporal investment while providing comprehensive versioning capabilities.