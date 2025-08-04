"""Sample Selection Phase Activities - Reconciled with all existing steps

These activities match the pre-Temporal workflow exactly:
1. Start Sample Selection Phase
2. Define Selection Criteria
3. Generate/Upload Sample Sets
4. Review & Approve Samples
5. Complete Sample Selection Phase
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
from app.models import SampleSelectionPhase, SampleSet, Report, SampleRecord
from app.application.use_cases.sample_selection import (
    StartSampleSelectionPhaseUseCase,
    AutoSelectSamplesUseCase,
    ApproveSampleSelectionUseCase,
    CompleteSampleSelectionPhaseUseCase
)

logger = logging.getLogger(__name__)


@activity.defn
async def start_sample_selection_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 1: Start sample selection phase"""
    try:
        async for db in get_db():
            # Use existing use case
            use_case = StartSampleSelectionPhaseUseCase()
            result = await use_case.execute(
                cycle_id=cycle_id,
                report_id=report_id,
                request_data={
                    "target_sample_size": 25,  # Default
                    "sampling_methodology": "Risk-based sampling",
                    "instructions": "Please select samples based on risk criteria"
                },
                user_id=user_id,
                db=db
            )
            
            if not result.success:
                raise Exception(result.error)
            
            logger.info(f"Started sample selection phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_id": result.data.get('phase_id'),
                    "phase_name": "Sample Selection",
                    "state": "In Progress",
                    "started_at": datetime.utcnow().isoformat(),
                    "target_sample_size": 25,
                    "sampling_methodology": "Risk-based sampling"
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start sample selection phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def define_selection_criteria_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    criteria_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 2: Define selection criteria
    
    Human-in-the-loop activity for defining sample selection criteria.
    """
    try:
        async for db in get_db():
            if criteria_data:
                # Process selection criteria
                criteria = {
                    "selection_method": criteria_data.get('selection_method', 'risk_based'),
                    "target_sample_size": criteria_data.get('target_sample_size', 25),
                    "risk_factors": criteria_data.get('risk_factors', []),
                    "exclusion_criteria": criteria_data.get('exclusion_criteria', []),
                    "inclusion_criteria": criteria_data.get('inclusion_criteria', []),
                    "stratification": criteria_data.get('stratification', {}),
                    "custom_rules": criteria_data.get('custom_rules', [])
                }
                
                # Store criteria in phase data
                # This would typically be stored in the SampleSelectionPhase model
                
                return {
                    "success": True,
                    "data": {
                        "criteria_defined": True,
                        "selection_method": criteria['selection_method'],
                        "target_sample_size": criteria['target_sample_size'],
                        "ready_for_generation": True,
                        "criteria": criteria
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_criteria_definition",
                        "message": "Waiting for selection criteria to be defined"
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in criteria definition: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def generate_sample_sets_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    generation_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 3: Generate or upload sample sets
    
    This activity handles both:
    - LLM-based sample generation
    - Manual sample upload
    """
    try:
        async for db in get_db():
            if generation_data:
                if generation_data.get('use_llm_generation'):
                    # Use existing auto-select use case
                    use_case = AutoSelectSamplesUseCase()
                    result = await use_case.execute(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        request_data={
                            "target_sample_size": generation_data.get('target_sample_size', 25),
                            "selection_criteria": generation_data.get('criteria', {}),
                            "use_llm": True
                        },
                        user_id=user_id,
                        db=db
                    )
                    
                    if not result.success:
                        raise Exception(result.error)
                    
                    sample_sets = result.data.get('sample_sets', [])
                    
                    return {
                        "success": True,
                        "data": {
                            "generation_method": "llm",
                            "sample_sets_created": len(sample_sets),
                            "total_samples": sum(len(s.get('samples', [])) for s in sample_sets),
                            "sample_sets": sample_sets,
                            "ready_for_review": True
                        }
                    }
                    
                elif generation_data.get('manual_samples'):
                    # Handle manual sample upload
                    manual_samples = generation_data['manual_samples']
                    
                    # Create sample set
                    sample_set = SampleSet(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        set_name=f"Manual Sample Set - {datetime.utcnow().strftime('%Y%m%d')}",
                        version_number=1,
                        generation_method='manual',
                        status='draft',
                        created_by=user_id
                    )
                    db.add(sample_set)
                    await db.flush()
                    
                    # Add samples
                    for sample_data in manual_samples:
                        sample = SampleSelection(
                            cycle_id=cycle_id,
                            report_id=report_id,
                            set_id=sample_set.set_id,
                            **sample_data,
                            created_by=user_id
                        )
                        db.add(sample)
                    
                    await db.commit()
                    
                    return {
                        "success": True,
                        "data": {
                            "generation_method": "manual",
                            "sample_sets_created": 1,
                            "total_samples": len(manual_samples),
                            "ready_for_review": True
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "No generation method specified"
                    }
            else:
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_sample_generation",
                        "message": "Waiting for samples to be generated or uploaded"
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in sample generation: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def review_approve_samples_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    approval_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 4: Review and approve sample sets
    
    Human-in-the-loop activity for sample review and approval.
    """
    try:
        async for db in get_db():
            if approval_data and approval_data.get('set_approvals'):
                # Process sample set approvals
                approved_sets = []
                rejected_sets = []
                
                for set_approval in approval_data['set_approvals']:
                    set_id = set_approval['set_id']
                    action = set_approval['action']  # 'approve', 'reject', 'request_changes'
                    
                    if action == 'approve':
                        # Use existing approve use case
                        use_case = ApproveSampleSetUseCase()
                        result = await use_case.execute(
                            cycle_id=cycle_id,
                            report_id=report_id,
                            set_id=set_id,
                            approval_data={
                                "approval_notes": set_approval.get('notes', ''),
                                "individual_sample_decisions": set_approval.get('sample_decisions', [])
                            },
                            user_id=user_id,
                            db=db
                        )
                        
                        if result.success:
                            approved_sets.append(set_id)
                        else:
                            logger.error(f"Failed to approve set {set_id}: {result.error}")
                            
                    elif action == 'reject':
                        # Update sample set status to rejected
                        await db.execute(
                            update(SampleSet)
                            .where(SampleSet.set_id == set_id)
                            .values(
                                status='rejected',
                                approval_notes=set_approval.get('notes', ''),
                                approved_by=user_id,
                                approved_at=datetime.utcnow()
                            )
                        )
                        rejected_sets.append(set_id)
                
                await db.commit()
                
                # Check if we have enough approved samples
                approved_sample_count = await db.execute(
                    select(func.count(SampleSelection.sample_id))
                    .join(SampleSet)
                    .where(
                        and_(
                            SampleSelection.cycle_id == cycle_id,
                            SampleSelection.report_id == report_id,
                            SampleSet.status == 'approved'
                        )
                    )
                )
                total_approved = approved_sample_count.scalar()
                
                return {
                    "success": True,
                    "data": {
                        "sets_approved": len(approved_sets),
                        "sets_rejected": len(rejected_sets),
                        "total_approved_samples": total_approved,
                        "meets_target_size": total_approved >= 25,  # Default target
                        "ready_to_complete": total_approved >= 25
                    }
                }
            else:
                # Check current approval status
                result = await db.execute(
                    select(SampleSet).where(
                        and_(
                            SampleSet.cycle_id == cycle_id,
                            SampleSet.report_id == report_id
                        )
                    )
                )
                sample_sets = result.scalars().all()
                
                pending_sets = [s for s in sample_sets if s.status == 'draft']
                approved_sets = [s for s in sample_sets if s.status == 'approved']
                
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_review",
                        "message": "Waiting for sample sets to be reviewed and approved",
                        "pending_review_count": len(pending_sets),
                        "approved_count": len(approved_sets)
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in sample approval: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def complete_sample_selection_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    phase_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Step 5: Complete sample selection phase"""
    try:
        async for db in get_db():
            # Verify we have approved samples
            if not phase_data.get('ready_to_complete'):
                raise ValueError("Cannot complete sample selection - insufficient approved samples")
            
            # Use existing complete use case
            use_case = CompleteSampleSelectionPhaseUseCase()
            result = await use_case.execute(
                cycle_id=cycle_id,
                report_id=report_id,
                completion_data={
                    "completion_notes": f"Completed with {phase_data.get('total_approved_samples', 0)} approved samples"
                },
                user_id=user_id,
                db=db
            )
            
            if not result.success:
                raise Exception(result.error)
            
            # Since Sample Selection and Data Provider ID run in parallel,
            # we don't advance to next phase here - that's handled by the workflow
            
            logger.info(f"Completed sample selection phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_name": "Sample Selection",
                    "approved_samples": phase_data.get('total_approved_samples', 0),
                    "completed_at": datetime.utcnow().isoformat(),
                    "parallel_phase": "Data Provider ID"  # Runs in parallel
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete sample selection phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }