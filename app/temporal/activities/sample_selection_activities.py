"""Sample Selection Phase Activities for Temporal Workflow

Standard structure:
1. Start Sample Selection Phase (Tester initiated)
2. Sample Selection-specific activities
3. Complete Sample Selection Phase (Tester initiated)
"""

from temporalio import activity
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import random
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    WorkflowPhase, TestCycle, Report, CycleReport,
    ReportAttribute, User, Sample
)
from app.models.lob import LOB
from app.temporal.shared import ActivityResult

logger = logging.getLogger(__name__)


@activity.defn
async def start_sample_selection_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> ActivityResult:
    """Start Sample Selection Phase - Initiated by Tester
    
    This is the standard entry point for the Sample Selection phase.
    Validates user permissions and initializes phase.
    """
    try:
        async with get_db() as db:
            # Verify user has permission to start phase
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to start Sample Selection phase"
                )
            
            # Get or create workflow phase record
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                # Create phase record
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Sample Selection",
                    state="In Progress",
                    status="On Schedule",
                    actual_start_date=datetime.utcnow(),
                    started_by=user_id
                )
                db.add(phase)
            else:
                # Update existing phase
                phase.state = "In Progress"
                phase.actual_start_date = datetime.utcnow()
                phase.started_by = user_id
            
            await db.commit()
            
            logger.info(f"Started Sample Selection phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "started_at": phase.actual_start_date.isoformat(),
                    "started_by": user_id
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to start Sample Selection phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def define_selection_criteria_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Define criteria for sample selection
    
    Sample Selection-specific activity that establishes selection rules
    """
    try:
        async with get_db() as db:
            # Get report details
            report = await db.get(Report, report_id)
            if not report:
                return ActivityResult(
                    success=False,
                    error="Report not found"
                )
            
            # Check if criteria already exist
            result = await db.execute(
                select(SampleSelectionCriteria).where(
                    SampleSelectionCriteria.cycle_id == cycle_id,
                    SampleSelectionCriteria.report_id == report_id
                )
            )
            existing_criteria = result.scalar_one_or_none()
            
            if not existing_criteria:
                # Create new selection criteria
                criteria = SampleSelectionCriteria(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    criteria_name=f"{report.report_name} Sample Criteria",
                    criteria_type="stratified",  # stratified, random, targeted
                    sample_size_percentage=10.0,  # 10% sample
                    minimum_samples=100,
                    maximum_samples=1000,
                    selection_rules={
                        "include_critical": True,
                        "balance_by_lob": True,
                        "risk_based_selection": True,
                        "time_period": "last_quarter"
                    },
                    created_by=1  # System user
                )
                db.add(criteria)
                await db.commit()
                
                criteria_data = {
                    "criteria_id": criteria.criteria_id,
                    "criteria_type": criteria.criteria_type,
                    "sample_size_percentage": criteria.sample_size_percentage,
                    "selection_rules": criteria.selection_rules
                }
            else:
                criteria_data = {
                    "criteria_id": existing_criteria.criteria_id,
                    "criteria_type": existing_criteria.criteria_type,
                    "sample_size_percentage": existing_criteria.sample_size_percentage,
                    "selection_rules": existing_criteria.selection_rules
                }
            
            logger.info(f"Defined selection criteria for report {report_id}")
            return ActivityResult(
                success=True,
                data=criteria_data
            )
            
    except Exception as e:
        logger.error(f"Failed to define selection criteria: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def generate_samples_activity(
    cycle_id: int,
    report_id: int,
    criteria_data: Dict[str, Any]
) -> ActivityResult:
    """Generate samples based on criteria
    
    Sample Selection-specific activity that creates sample records
    """
    try:
        async with get_db() as db:
            # Get LOBs for tagging samples
            lobs = await db.execute(select(LineOfBusiness))
            lob_list = lobs.scalars().all()
            
            if not lob_list:
                return ActivityResult(
                    success=False,
                    error="No Lines of Business found for sample tagging"
                )
            
            # Generate samples (simplified for demo)
            samples_created = []
            sample_size = int(criteria_data.get("sample_size_percentage", 10) * 10)  # Simplified calculation
            
            for i in range(min(sample_size, 100)):  # Limit to 100 for demo
                # Randomly assign LOB for each sample
                selected_lob = random.choice(lob_list)
                
                sample = Sample(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    sample_identifier=f"SAMPLE-{cycle_id}-{report_id}-{i+1:04d}",
                    sample_type="customer",
                    lob_id=selected_lob.lob_id,  # Tag sample to LOB
                    selection_criteria_id=criteria_data.get("criteria_id"),
                    sample_data={
                        "customer_id": f"CUST{random.randint(10000, 99999)}",
                        "account_number": f"ACC{random.randint(100000, 999999)}",
                        "risk_rating": random.choice(["Low", "Medium", "High"]),
                        "balance": round(random.uniform(1000, 100000), 2),
                        "lob_name": selected_lob.lob_name
                    },
                    is_critical=random.random() < 0.2,  # 20% critical samples
                    created_by=1  # System user
                )
                db.add(sample)
                samples_created.append({
                    "sample_id": sample.sample_identifier,
                    "lob": selected_lob.lob_name,
                    "is_critical": sample.is_critical
                })
            
            await db.commit()
            
            # Count samples by LOB
            lob_distribution = {}
            for sample in samples_created:
                lob = sample["lob"]
                lob_distribution[lob] = lob_distribution.get(lob, 0) + 1
            
            logger.info(f"Generated {len(samples_created)} samples for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "total_samples": len(samples_created),
                    "critical_samples": len([s for s in samples_created if s["is_critical"]]),
                    "lob_distribution": lob_distribution,
                    "sample_examples": samples_created[:5]  # First 5 samples
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to generate samples: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def validate_sample_coverage_activity(
    cycle_id: int,
    report_id: int,
    sample_data: Dict[str, Any]
) -> ActivityResult:
    """Validate that samples meet coverage requirements
    
    Sample Selection-specific activity that ensures adequate coverage
    """
    try:
        async with get_db() as db:
            # Get attributes that need testing
            attributes = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.report_id == report_id
                )
            )
            attribute_list = attributes.scalars().all()
            
            # Validate coverage
            validation_results = {
                "total_attributes": len(attribute_list),
                "critical_attributes": len([a for a in attribute_list if a.is_critical]),
                "total_samples": sample_data.get("total_samples", 0),
                "critical_samples": sample_data.get("critical_samples", 0),
                "lob_coverage": len(sample_data.get("lob_distribution", {})),
                "validation_passed": True,
                "validation_messages": []
            }
            
            # Check minimum sample size
            if validation_results["total_samples"] < 50:
                validation_results["validation_passed"] = False
                validation_results["validation_messages"].append(
                    f"Insufficient samples: {validation_results['total_samples']} < 50 minimum"
                )
            
            # Check critical attribute coverage
            if validation_results["critical_attributes"] > 0 and validation_results["critical_samples"] == 0:
                validation_results["validation_passed"] = False
                validation_results["validation_messages"].append(
                    "No critical samples selected for critical attributes"
                )
            
            # Check LOB distribution
            if validation_results["lob_coverage"] < 2:
                validation_results["validation_messages"].append(
                    f"Limited LOB coverage: only {validation_results['lob_coverage']} LOBs represented"
                )
            
            logger.info(f"Validated sample coverage: {validation_results['validation_passed']}")
            return ActivityResult(
                success=True,
                data=validation_results
            )
            
    except Exception as e:
        logger.error(f"Failed to validate sample coverage: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def complete_sample_selection_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    completion_notes: Optional[str] = None
) -> ActivityResult:
    """Complete Sample Selection Phase - Initiated by Tester
    
    This is the standard exit point for the Sample Selection phase.
    Validates completion criteria and marks phase as complete.
    """
    try:
        async with get_db() as db:
            # Verify user has permission
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to complete Sample Selection phase"
                )
            
            # Get workflow phase
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                return ActivityResult(
                    success=False,
                    error="Sample Selection phase not found"
                )
            
            # Verify completion criteria
            # 1. Check if samples exist
            samples = await db.execute(
                select(func.count(Sample.sample_id)).where(
                    Sample.cycle_id == cycle_id,
                    Sample.report_id == report_id
                )
            )
            sample_count = samples.scalar()
            
            if sample_count == 0:
                return ActivityResult(
                    success=False,
                    error="Cannot complete Sample Selection phase: No samples generated"
                )
            
            # 2. Check if samples are tagged to LOBs
            untagged_samples = await db.execute(
                select(func.count(Sample.sample_id)).where(
                    Sample.cycle_id == cycle_id,
                    Sample.report_id == report_id,
                    Sample.lob_id.is_(None)
                )
            )
            untagged_count = untagged_samples.scalar()
            
            if untagged_count > 0:
                return ActivityResult(
                    success=False,
                    error=f"Cannot complete Sample Selection phase: {untagged_count} samples not tagged to LOB"
                )
            
            # Mark phase as complete
            phase.state = "Completed"
            phase.actual_end_date = datetime.utcnow()
            phase.completed_by = user_id
            if completion_notes:
                phase.notes = completion_notes
            
            # Calculate if on schedule
            if phase.planned_end_date and phase.actual_end_date > phase.planned_end_date:
                phase.status = "Behind Schedule"
            else:
                phase.status = "Complete"
            
            # Get LOB distribution for summary
            lob_stats = await db.execute(
                select(
                    LineOfBusiness.lob_name,
                    func.count(Sample.sample_id).label("sample_count")
                ).join(
                    Sample, Sample.lob_id == LineOfBusiness.lob_id
                ).where(
                    Sample.cycle_id == cycle_id,
                    Sample.report_id == report_id
                ).group_by(LineOfBusiness.lob_name)
            )
            
            lob_distribution = {row.lob_name: row.sample_count for row in lob_stats}
            
            await db.commit()
            
            logger.info(f"Completed Sample Selection phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "completed_at": phase.actual_end_date.isoformat(),
                    "completed_by": user_id,
                    "duration_days": (phase.actual_end_date - phase.actual_start_date).days if phase.actual_start_date else 0,
                    "status": phase.status,
                    "total_samples": sample_count,
                    "lob_distribution": lob_distribution
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to complete Sample Selection phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def execute_sample_selection_activities(
    cycle_id: int,
    report_id: int,
    metadata: Dict[str, Any]
) -> ActivityResult:
    """Execute all Sample Selection phase activities in sequence
    
    This orchestrates the sample selection-specific activities between
    start and complete.
    """
    try:
        results = {}
        
        # 1. Define selection criteria
        criteria_result = await define_selection_criteria_activity(
            cycle_id, report_id
        )
        if not criteria_result.success:
            return criteria_result
        results["selection_criteria"] = criteria_result.data
        
        # 2. Generate samples with LOB tagging
        samples_result = await generate_samples_activity(
            cycle_id, report_id, criteria_result.data
        )
        if not samples_result.success:
            return samples_result
        results["sample_generation"] = samples_result.data
        
        # 3. Validate sample coverage
        validation_result = await validate_sample_coverage_activity(
            cycle_id, report_id, samples_result.data
        )
        if not validation_result.success:
            return validation_result
        results["coverage_validation"] = validation_result.data
        
        return ActivityResult(
            success=True,
            data={
                "phase": "Sample Selection",
                "activities_completed": 3,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to execute sample selection activities: {str(e)}")
        return ActivityResult(success=False, error=str(e))