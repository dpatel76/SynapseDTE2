# Temporal-Integrated Versioning Implementation Plan

## Overview

This plan details how to integrate versioning directly with your Temporal workflow system, making version management an intrinsic part of workflow execution.

## Architecture Principles

1. **Versions are created by Temporal activities** - No direct version creation outside workflows
2. **Approvals happen through workflow signals** - Leverage existing human-in-the-loop pattern
3. **Workflow drives version state** - Version status mirrors workflow state
4. **Single source of truth** - Temporal workflow history is the authoritative record

## Phase 1: Database Schema Updates (Week 1)

### 1.1 Enhance Versioning Tables

```sql
-- Add Temporal context to version_history table
ALTER TABLE version_history 
ADD COLUMN workflow_execution_id VARCHAR(255),
ADD COLUMN workflow_run_id VARCHAR(255),
ADD COLUMN workflow_step_id UUID,
ADD COLUMN activity_name VARCHAR(100),
ADD COLUMN activity_task_token BYTEA,
ADD FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(step_id);

CREATE INDEX idx_version_workflow_execution ON version_history(workflow_execution_id);
CREATE INDEX idx_version_workflow_step ON version_history(workflow_step_id);

-- Add Temporal context to phase-specific version tables
ALTER TABLE planning_phase_versions
ADD COLUMN workflow_execution_id VARCHAR(255),
ADD COLUMN workflow_step_id UUID;

ALTER TABLE sample_selection_versions
ADD COLUMN workflow_execution_id VARCHAR(255),
ADD COLUMN workflow_step_id UUID;

-- Continue for other version tables...
```

### 1.2 Create Version-Workflow Mapping

```sql
-- Track version operations within workflows
CREATE TABLE workflow_version_operations (
    operation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_execution_id VARCHAR(255) NOT NULL,
    workflow_step_id UUID,
    
    -- Operation details
    operation_type VARCHAR(50) NOT NULL, -- 'create', 'approve', 'reject', 'revise'
    phase_name VARCHAR(50) NOT NULL,
    version_id UUID,
    
    -- Timing
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    success BOOLEAN,
    error_message TEXT,
    
    FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(step_id)
);

CREATE INDEX idx_wf_version_ops_execution ON workflow_version_operations(workflow_execution_id);
CREATE INDEX idx_wf_version_ops_version ON workflow_version_operations(version_id);
```

## Phase 2: Temporal Activities for Versioning (Week 2)

### 2.1 Base Versioning Activities

```python
# app/workflows/activities/versioning_activities.py
from temporalio import activity
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from app.services.versioning_service import UnifiedVersioningService
from app.models.workflow_tracking import WorkflowStep
from app.core.database import get_db

class VersioningActivities:
    """Temporal activities for version management"""
    
    @activity.defn
    async def create_version(
        self,
        phase_name: str,
        cycle_id: int,
        report_id: int,
        user_id: int,
        version_data: Dict[str, Any],
        parent_version_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Create a new version for any phase"""
        async with get_db() as db:
            # Get workflow context
            info = activity.info()
            workflow_id = info.workflow_id
            workflow_run_id = info.workflow_run_id
            activity_name = info.activity_type
            
            # Record workflow step
            workflow_step = WorkflowStep(
                workflow_execution_id=workflow_id,
                phase_name=phase_name,
                activity_name=activity_name,
                step_type="activity",
                started_at=datetime.utcnow(),
                input_data={
                    "phase_name": phase_name,
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "user_id": user_id
                }
            )
            db.add(workflow_step)
            await db.flush()
            
            # Create version with workflow context
            service = UnifiedVersioningService(db)
            version_id = await service.create_version(
                phase=phase_name,
                cycle_id=cycle_id,
                report_id=report_id,
                user_id=user_id,
                data=version_data,
                parent_version_id=parent_version_id,
                workflow_context={
                    "workflow_execution_id": workflow_id,
                    "workflow_run_id": workflow_run_id,
                    "workflow_step_id": workflow_step.step_id,
                    "activity_name": activity_name
                }
            )
            
            # Update workflow step
            workflow_step.completed_at = datetime.utcnow()
            workflow_step.output_data = {"version_id": str(version_id)}
            workflow_step.status = "completed"
            
            await db.commit()
            
            return {
                "version_id": str(version_id),
                "workflow_step_id": str(workflow_step.step_id),
                "created_at": datetime.utcnow().isoformat()
            }
    
    @activity.defn
    async def get_current_version(
        self,
        phase_name: str,
        cycle_id: int,
        report_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get the current approved version for a phase"""
        async with get_db() as db:
            service = UnifiedVersioningService(db)
            version = await service.get_current_version(
                phase=phase_name,
                cycle_id=cycle_id,
                report_id=report_id
            )
            
            if version:
                return {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "status": version.version_status,
                    "created_at": version.version_created_at.isoformat()
                }
            return None
    
    @activity.defn
    async def approve_version(
        self,
        phase_name: str,
        version_id: UUID,
        user_id: int,
        approval_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve a version"""
        async with get_db() as db:
            info = activity.info()
            
            service = UnifiedVersioningService(db)
            success = await service.approve_version(
                phase=phase_name,
                version_id=version_id,
                user_id=user_id,
                notes=approval_notes,
                workflow_context={
                    "workflow_execution_id": info.workflow_id,
                    "activity_name": info.activity_type
                }
            )
            
            return {
                "success": success,
                "approved_at": datetime.utcnow().isoformat(),
                "approved_by": user_id
            }
```

### 2.2 Phase-Specific Activities

```python
# app/workflows/activities/sample_selection_activities.py
from app.models.sample_selection import SampleDecision
from app.workflows.activities.versioning_activities import VersioningActivities

class SampleSelectionActivities(VersioningActivities):
    """Sample selection specific activities"""
    
    @activity.defn
    async def create_sample_selection_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        samples: List[Dict[str, Any]],
        selection_criteria: Dict[str, Any],
        parent_version_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Create sample selection version with individual decisions"""
        async with get_db() as db:
            # Create the version
            version_result = await self.create_version(
                phase_name="Sample Selection",
                cycle_id=cycle_id,
                report_id=report_id,
                user_id=user_id,
                version_data={
                    "selection_criteria": selection_criteria,
                    "target_sample_size": len(samples),
                    "generation_methods": ["tester_recommended"]
                },
                parent_version_id=parent_version_id
            )
            
            version_id = UUID(version_result["version_id"])
            
            # Create individual sample decisions
            for idx, sample in enumerate(samples):
                decision = SampleDecision(
                    selection_version_id=version_id,
                    sample_identifier=sample.get("id", f"sample_{idx}"),
                    sample_data=sample.get("data", {}),
                    sample_type=sample.get("type", "population"),
                    recommendation_source="tester",
                    recommended_by_id=user_id,
                    recommendation_timestamp=datetime.utcnow(),
                    decision_status="pending"
                )
                
                # Track lineage if this is a revision
                if parent_version_id and sample.get("carried_from_id"):
                    decision.carried_from_version_id = parent_version_id
                    decision.carried_from_decision_id = sample["carried_from_id"]
                
                db.add(decision)
            
            await db.commit()
            
            return {
                **version_result,
                "sample_count": len(samples),
                "samples_created": True
            }
    
    @activity.defn
    async def process_sample_review(
        self,
        version_id: UUID,
        user_id: int,
        decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process sample review decisions"""
        async with get_db() as db:
            approved_count = 0
            rejected_count = 0
            
            for decision_data in decisions:
                decision = await db.get(
                    SampleDecision, 
                    decision_data["decision_id"]
                )
                
                if decision and decision.selection_version_id == version_id:
                    decision.decision_status = decision_data["status"]
                    decision.decided_by_id = user_id
                    decision.decision_timestamp = datetime.utcnow()
                    decision.decision_notes = decision_data.get("notes")
                    
                    if decision_data["status"] == "approved":
                        approved_count += 1
                    elif decision_data["status"] == "rejected":
                        rejected_count += 1
            
            await db.commit()
            
            return {
                "version_id": str(version_id),
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "review_complete": True
            }
    
    @activity.defn
    async def create_sample_revision(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        parent_version_id: UUID,
        additional_samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a revision carrying forward approved samples"""
        async with get_db() as db:
            # Get approved samples from parent version
            approved_samples = await db.execute(
                select(SampleDecision).where(
                    SampleDecision.selection_version_id == parent_version_id,
                    SampleDecision.decision_status == "approved"
                )
            )
            
            # Prepare samples for new version
            samples_for_revision = []
            
            # Carry forward approved samples
            for decision in approved_samples.scalars():
                samples_for_revision.append({
                    "id": decision.sample_identifier,
                    "data": decision.sample_data,
                    "type": decision.sample_type,
                    "carried_from_id": decision.decision_id
                })
            
            # Add new samples
            samples_for_revision.extend(additional_samples)
            
            # Create new version
            return await self.create_sample_selection_version(
                cycle_id=cycle_id,
                report_id=report_id,
                user_id=user_id,
                samples=samples_for_revision,
                selection_criteria={"revision": True},
                parent_version_id=parent_version_id
            )
```

## Phase 3: Enhanced Workflow with Versioning (Week 3)

### 3.1 Workflow Base Class with Versioning

```python
# app/workflows/versioned_workflow_base.py
from temporalio import workflow
from typing import Dict, Any, Optional
from uuid import UUID

class VersionedWorkflowBase:
    """Base class for workflows with integrated versioning"""
    
    def __init__(self):
        self.phase_versions: Dict[str, UUID] = {}
        self.pending_approvals: Dict[str, Any] = {}
        self.approval_signals: Dict[str, List[Any]] = {}
    
    async def create_phase_version(
        self,
        phase_name: str,
        cycle_id: int,
        report_id: int,
        user_id: int,
        version_data: Dict[str, Any],
        parent_version_id: Optional[UUID] = None
    ) -> UUID:
        """Create a version for a phase"""
        result = await workflow.execute_activity(
            "create_version",
            phase_name,
            cycle_id,
            report_id,
            user_id,
            version_data,
            parent_version_id,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        version_id = UUID(result["version_id"])
        self.phase_versions[phase_name] = version_id
        self.pending_approvals[phase_name] = {
            "version_id": version_id,
            "status": "pending",
            "created_at": result["created_at"]
        }
        
        return version_id
    
    @workflow.signal
    async def submit_version_approval(
        self,
        phase_name: str,
        version_id: str,
        user_id: int,
        approved: bool,
        notes: Optional[str] = None
    ):
        """Signal to approve/reject a version"""
        if phase_name not in self.approval_signals:
            self.approval_signals[phase_name] = []
        
        self.approval_signals[phase_name].append({
            "version_id": version_id,
            "user_id": user_id,
            "approved": approved,
            "notes": notes,
            "timestamp": datetime.utcnow()
        })
    
    async def wait_for_version_approval(
        self,
        phase_name: str,
        timeout: Optional[timedelta] = None
    ) -> bool:
        """Wait for version approval signal"""
        def check_approval():
            if phase_name in self.approval_signals:
                for signal in self.approval_signals[phase_name]:
                    if signal["version_id"] == str(self.phase_versions[phase_name]):
                        return signal["approved"]
            return None
        
        # Wait for approval with optional timeout
        if timeout:
            try:
                await workflow.wait_condition(
                    lambda: check_approval() is not None,
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return False
        else:
            await workflow.wait_condition(
                lambda: check_approval() is not None
            )
        
        # Process the approval
        approved = check_approval()
        if approved:
            # Execute approval activity
            await workflow.execute_activity(
                "approve_version",
                phase_name,
                self.phase_versions[phase_name],
                self.approval_signals[phase_name][-1]["user_id"],
                self.approval_signals[phase_name][-1]["notes"],
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            self.pending_approvals[phase_name]["status"] = "approved"
        else:
            self.pending_approvals[phase_name]["status"] = "rejected"
        
        return approved
```

### 3.2 Enhanced Test Cycle Workflow

```python
# app/workflows/enhanced_test_cycle_workflow_v3.py
from app.workflows.versioned_workflow_base import VersionedWorkflowBase
from app.workflows.activities.sample_selection_activities import SampleSelectionActivities

@workflow.defn
class EnhancedTestCycleWorkflowV3(VersionedWorkflowBase):
    """Test cycle workflow with integrated versioning"""
    
    @workflow.run
    async def run(self, input: TestCycleWorkflowInput) -> TestCycleWorkflowOutput:
        """Run test cycle with versioning"""
        
        # Initialize tracking
        self.cycle_id = input.cycle_id
        self.report_id = input.report_id
        self.current_user_id = input.user_id
        
        # Run phases with versioning
        await self.run_planning_phase()
        await self.run_data_profiling_phase()
        await self.run_scoping_phase()
        await self.run_sample_selection_phase()
        
        # ... continue for other phases
        
        return TestCycleWorkflowOutput(
            cycle_id=self.cycle_id,
            report_id=self.report_id,
            phase_versions=self.phase_versions,
            status="completed"
        )
    
    async def run_sample_selection_phase(self):
        """Run sample selection with versioning"""
        workflow.logger.info("Starting Sample Selection phase")
        
        # Generate initial samples
        samples = await workflow.execute_activity(
            "generate_sample_recommendations",
            self.cycle_id,
            self.report_id,
            start_to_close_timeout=timedelta(minutes=30)
        )
        
        # Create version
        version_result = await workflow.execute_activity(
            SampleSelectionActivities.create_sample_selection_version,
            self.cycle_id,
            self.report_id,
            self.current_user_id,
            samples["recommendations"],
            samples["criteria"],
            None,  # No parent version for initial
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        self.phase_versions["Sample Selection"] = UUID(version_result["version_id"])
        
        # Signal UI that samples are ready for review
        workflow.logger.info(f"Sample Selection version created: {version_result['version_id']}")
        
        # Wait for review signal
        review_complete = False
        revision_count = 0
        max_revisions = 3
        
        while not review_complete and revision_count < max_revisions:
            # Wait for review signal
            await workflow.wait_condition(
                lambda: "sample_review" in self.approval_signals
            )
            
            latest_review = self.approval_signals["sample_review"][-1]
            
            if latest_review["approved"]:
                # Process approval
                await workflow.execute_activity(
                    "approve_version",
                    "Sample Selection",
                    self.phase_versions["Sample Selection"],
                    latest_review["user_id"],
                    latest_review["notes"],
                    start_to_close_timeout=timedelta(minutes=5)
                )
                review_complete = True
                
            elif latest_review.get("needs_revision"):
                # Create revision with additional samples
                revision_result = await workflow.execute_activity(
                    SampleSelectionActivities.create_sample_revision,
                    self.cycle_id,
                    self.report_id,
                    self.current_user_id,
                    self.phase_versions["Sample Selection"],
                    latest_review.get("additional_samples", []),
                    start_to_close_timeout=timedelta(minutes=10)
                )
                
                self.phase_versions["Sample Selection"] = UUID(revision_result["version_id"])
                revision_count += 1
                workflow.logger.info(f"Created revision {revision_count}: {revision_result['version_id']}")
                
                # Clear signals for next review
                self.approval_signals["sample_review"] = []
            
            else:
                # Rejection without revision
                workflow.logger.warning("Sample selection rejected without revision")
                raise workflow.ApplicationError(
                    "Sample selection rejected",
                    type="SampleSelectionRejected"
                )
        
        if not review_complete:
            raise workflow.ApplicationError(
                f"Max revisions ({max_revisions}) exceeded",
                type="MaxRevisionsExceeded"
            )
        
        workflow.logger.info("Sample Selection phase completed")
    
    @workflow.signal
    async def submit_sample_review(
        self,
        review_data: Dict[str, Any]
    ):
        """Handle sample review signal"""
        if "sample_review" not in self.approval_signals:
            self.approval_signals["sample_review"] = []
        
        self.approval_signals["sample_review"].append({
            **review_data,
            "timestamp": workflow.now()
        })
```

## Phase 4: UI Integration (Week 4)

### 4.1 Frontend Service for Workflow Versioning

```typescript
// frontend/src/services/workflowVersioningService.ts
import { TemporalClient } from './temporalClient';

export class WorkflowVersioningService {
  private temporal: TemporalClient;

  async getPhaseVersion(
    workflowId: string,
    phaseName: string
  ): Promise<VersionInfo | null> {
    const workflow = await this.temporal.getWorkflowHandle(workflowId);
    const state = await workflow.query('getPhaseVersions');
    return state.phaseVersions[phaseName] || null;
  }

  async submitApproval(
    workflowId: string,
    phaseName: string,
    versionId: string,
    approved: boolean,
    notes?: string
  ): Promise<void> {
    const workflow = await this.temporal.getWorkflowHandle(workflowId);
    
    await workflow.signal('submitVersionApproval', {
      phaseName,
      versionId,
      userId: getCurrentUserId(),
      approved,
      notes
    });
  }

  async submitSampleReview(
    workflowId: string,
    decisions: SampleDecision[],
    needsRevision: boolean,
    additionalSamples?: Sample[]
  ): Promise<void> {
    const workflow = await this.temporal.getWorkflowHandle(workflowId);
    
    await workflow.signal('submitSampleReview', {
      userId: getCurrentUserId(),
      approved: !needsRevision && decisions.every(d => d.status !== 'rejected'),
      needs_revision: needsRevision,
      decisions,
      additional_samples: additionalSamples
    });
  }
}
```

### 4.2 React Component Example

```typescript
// frontend/src/components/SampleSelectionReview.tsx
import React, { useState, useEffect } from 'react';
import { WorkflowVersioningService } from '../services/workflowVersioningService';

export const SampleSelectionReview: React.FC<Props> = ({ 
  workflowId, 
  cycleId, 
  reportId 
}) => {
  const [version, setVersion] = useState<SampleSelectionVersion | null>(null);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [decisions, setDecisions] = useState<Map<string, SampleDecision>>(new Map());
  
  const versioningService = new WorkflowVersioningService();

  const handleSubmitReview = async () => {
    const allDecisions = Array.from(decisions.values());
    const hasRejections = allDecisions.some(d => d.status === 'rejected');
    
    if (hasRejections && needsMoreSamples) {
      // Request revision with additional samples
      await versioningService.submitSampleReview(
        workflowId,
        allDecisions,
        true,
        additionalSamples
      );
    } else {
      // Submit final review
      await versioningService.submitSampleReview(
        workflowId,
        allDecisions,
        false
      );
    }
  };

  return (
    <div className="sample-selection-review">
      <h2>Sample Selection Review</h2>
      <div className="version-info">
        Version: {version?.versionNumber} 
        (Created: {version?.createdAt})
      </div>
      
      <SampleList 
        samples={samples}
        decisions={decisions}
        onDecisionChange={handleDecisionChange}
      />
      
      <div className="actions">
        <button onClick={handleSubmitReview}>
          Submit Review
        </button>
      </div>
    </div>
  );
};
```

## Phase 5: Migration Strategy (Week 5)

### 5.1 Gradual Migration Approach

1. **Week 1**: Deploy database changes
2. **Week 2**: Deploy Temporal activities
3. **Week 3**: Update workflows one phase at a time
   - Start with Planning (simpler)
   - Then Sample Selection (complex)
   - Continue with other phases
4. **Week 4**: Update UI components
5. **Week 5**: Remove old versioning code

### 5.2 Rollback Strategy

Each phase can be rolled back independently:
- Database changes are backward compatible
- Activities can fall back to direct DB operations
- Workflows can be versioned to support both approaches

## Benefits of This Approach

1. **Unified System**: One system for both workflow and versioning
2. **Consistency**: Version state always matches workflow state
3. **Reliability**: Temporal handles retries, failures, recovery
4. **Auditability**: Complete history in Temporal and database
5. **Simplicity**: No separate orchestration for versions
6. **Scalability**: Temporal scales with your needs

## Next Steps

1. **Review** this implementation plan
2. **Start** with database migrations
3. **Implement** base versioning activities
4. **Test** with Planning phase first
5. **Roll out** to other phases incrementally

This integrated approach will give you a robust, scalable versioning system that leverages all the benefits of Temporal while maintaining data integrity and audit trails.