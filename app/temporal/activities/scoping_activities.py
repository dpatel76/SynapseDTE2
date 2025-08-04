"""Scoping Phase Activities for Temporal Workflow

Standard structure:
1. Start Scoping Phase (Tester initiated)
2. Scoping-specific activities
3. Complete Scoping Phase (Tester initiated)
"""

from temporalio import activity
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    WorkflowPhase, TestCycle, Report, CycleReport,
    ReportAttribute, User
)
from app.temporal.shared import ActivityResult
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


@activity.defn
async def start_scoping_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> ActivityResult:
    """Start Scoping Phase - Initiated by Tester
    
    This is the standard entry point for the Scoping phase.
    Validates user permissions and initializes phase.
    """
    try:
        async with get_db() as db:
            # Verify user has permission to start phase
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to start Scoping phase"
                )
            
            # Get or create workflow phase record
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Scoping"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                # Create phase record
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Scoping",
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
            
            logger.info(f"Started Scoping phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "started_at": phase.actual_start_date.isoformat(),
                    "started_by": user_id
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to start Scoping phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def enhance_attributes_with_llm_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Enhance attributes using LLM analysis
    
    Scoping-specific activity that uses LLM to enhance attribute definitions
    """
    try:
        async with get_db() as db:
            # Get existing attributes
            result = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.report_id == report_id
                )
            )
            attributes = result.scalars().all()
            
            if not attributes:
                return ActivityResult(
                    success=False,
                    error="No attributes found to enhance"
                )
            
            # Get report details for context
            report = await db.get(Report, report_id)
            if not report:
                return ActivityResult(
                    success=False,
                    error="Report not found"
                )
            
            # Use LLM to enhance attributes
            llm_service = get_llm_service()
            enhanced_count = 0
            
            for attribute in attributes[:5]:  # Limit to first 5 for demo
                try:
                    # Generate enhanced description and test recommendations
                    enhancement_result = await llm_service.enhance_attribute(
                        attribute_name=attribute.attribute_name,
                        current_description=attribute.description,
                        report_type=report.report_type,
                        regulation=report.regulation
                    )
                    
                    if enhancement_result.get("success"):
                        # Update attribute with enhanced data
                        attribute.description = enhancement_result.get("enhanced_description", attribute.description)
                        attribute.llm_test_recommendations = enhancement_result.get("test_recommendations", [])
                        attribute.data_type = enhancement_result.get("data_type", "text")
                        attribute.validation_rules = enhancement_result.get("validation_rules", {})
                        enhanced_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to enhance attribute {attribute.attribute_name}: {str(e)}")
                    continue
            
            await db.commit()
            
            logger.info(f"Enhanced {enhanced_count} attributes for report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "total_attributes": len(attributes),
                    "enhanced_count": enhanced_count,
                    "enhancement_method": "llm_analysis"
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to enhance attributes with LLM: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def determine_testing_approach_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Determine testing approach for each attribute
    
    Scoping-specific activity that defines testing methodology
    """
    try:
        async with get_db() as db:
            # Get attributes
            result = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.report_id == report_id
                )
            )
            attributes = result.scalars().all()
            
            # Define testing approaches
            testing_approaches = {
                "critical": {
                    "sample_size": "100%",
                    "test_methods": ["document_review", "database_validation", "manual_verification"],
                    "evidence_required": True,
                    "approval_required": True
                },
                "non_critical": {
                    "sample_size": "10%",
                    "test_methods": ["database_validation"],
                    "evidence_required": False,
                    "approval_required": False
                }
            }
            
            # Assign testing approach to each attribute
            approach_assignments = []
            for attribute in attributes:
                approach = testing_approaches["critical"] if attribute.is_critical else testing_approaches["non_critical"]
                
                # Update attribute metadata
                if not attribute.metadata:
                    attribute.metadata = {}
                attribute.metadata["testing_approach"] = approach
                
                approach_assignments.append({
                    "attribute_id": attribute.attribute_id,
                    "attribute_name": attribute.attribute_name,
                    "is_critical": attribute.is_critical,
                    "testing_approach": approach
                })
            
            await db.commit()
            
            logger.info(f"Determined testing approaches for {len(attributes)} attributes")
            return ActivityResult(
                success=True,
                data={
                    "attributes_count": len(attributes),
                    "critical_attributes": len([a for a in attributes if a.is_critical]),
                    "approach_assignments": approach_assignments[:10]  # Limit response size
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to determine testing approach: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def create_scope_document_activity(
    cycle_id: int,
    report_id: int,
    enhancement_data: Dict[str, Any],
    approach_data: Dict[str, Any]
) -> ActivityResult:
    """Create scope definition document
    
    Scoping-specific activity that generates scope document
    """
    try:
        async with get_db() as db:
            # Get report and cycle details
            report = await db.get(Report, report_id)
            cycle = await db.get(TestCycle, cycle_id)
            
            if not report or not cycle:
                return ActivityResult(
                    success=False,
                    error="Report or cycle not found"
                )
            
            # Check if scope definition already exists
            result = await db.execute(
                select(ScopeDefinition).where(
                    ScopeDefinition.cycle_id == cycle_id,
                    ScopeDefinition.report_id == report_id
                )
            )
            scope_def = result.scalar_one_or_none()
            
            if not scope_def:
                # Create new scope definition
                scope_def = ScopeDefinition(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    scope_name=f"{report.report_name} - {cycle.cycle_name} Scope",
                    description=f"Testing scope for {report.report_name} in {cycle.cycle_name}"
                )
                db.add(scope_def)
            
            # Update scope definition with details
            scope_def.total_attributes = approach_data.get("attributes_count", 0)
            scope_def.critical_attributes = approach_data.get("critical_attributes", 0)
            scope_def.testing_methodology = {
                "enhancement_method": enhancement_data.get("enhancement_method"),
                "enhanced_attributes": enhancement_data.get("enhanced_count"),
                "testing_approaches": {
                    "critical": {
                        "count": approach_data.get("critical_attributes", 0),
                        "approach": "Full testing with evidence"
                    },
                    "non_critical": {
                        "count": approach_data.get("attributes_count", 0) - approach_data.get("critical_attributes", 0),
                        "approach": "Sample testing"
                    }
                }
            }
            scope_def.approval_status = "Pending"
            scope_def.created_by = 1  # System user
            
            await db.commit()
            
            logger.info(f"Created scope document for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "scope_id": scope_def.scope_id,
                    "scope_name": scope_def.scope_name,
                    "total_attributes": scope_def.total_attributes,
                    "critical_attributes": scope_def.critical_attributes,
                    "approval_status": scope_def.approval_status
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to create scope document: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def complete_scoping_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    completion_notes: Optional[str] = None
) -> ActivityResult:
    """Complete Scoping Phase - Initiated by Tester
    
    This is the standard exit point for the Scoping phase.
    Validates completion criteria and marks phase as complete.
    """
    try:
        async with get_db() as db:
            # Verify user has permission
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to complete Scoping phase"
                )
            
            # Get workflow phase
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Scoping"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                return ActivityResult(
                    success=False,
                    error="Scoping phase not found"
                )
            
            # Verify completion criteria
            # 1. Check if scope definition exists
            scope_result = await db.execute(
                select(ScopeDefinition).where(
                    ScopeDefinition.cycle_id == cycle_id,
                    ScopeDefinition.report_id == report_id
                )
            )
            scope_def = scope_result.scalar_one_or_none()
            
            if not scope_def:
                return ActivityResult(
                    success=False,
                    error="Cannot complete Scoping phase: Scope definition not created"
                )
            
            # 2. Check if attributes have been enhanced
            attributes = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.metadata.has_key("testing_approach")
                )
            )
            enhanced_count = len(attributes.scalars().all())
            
            if enhanced_count == 0:
                return ActivityResult(
                    success=False,
                    error="Cannot complete Scoping phase: No attributes have testing approach defined"
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
            
            await db.commit()
            
            logger.info(f"Completed Scoping phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "completed_at": phase.actual_end_date.isoformat(),
                    "completed_by": user_id,
                    "duration_days": (phase.actual_end_date - phase.actual_start_date).days if phase.actual_start_date else 0,
                    "status": phase.status,
                    "scope_id": scope_def.scope_id,
                    "enhanced_attributes": enhanced_count
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to complete Scoping phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def execute_scoping_activities(
    cycle_id: int,
    report_id: int,
    metadata: Dict[str, Any]
) -> ActivityResult:
    """Execute all Scoping phase activities in sequence
    
    This orchestrates the scoping-specific activities between
    start and complete.
    """
    try:
        results = {}
        
        # 1. Enhance attributes with LLM
        enhancement_result = await enhance_attributes_with_llm_activity(
            cycle_id, report_id
        )
        if not enhancement_result.success:
            return enhancement_result
        results["attribute_enhancement"] = enhancement_result.data
        
        # 2. Determine testing approach
        approach_result = await determine_testing_approach_activity(
            cycle_id, report_id
        )
        if not approach_result.success:
            return approach_result
        results["testing_approach"] = approach_result.data
        
        # 3. Create scope document
        scope_result = await create_scope_document_activity(
            cycle_id, report_id,
            enhancement_result.data,
            approach_result.data
        )
        if not scope_result.success:
            return scope_result
        results["scope_document"] = scope_result.data
        
        return ActivityResult(
            success=True,
            data={
                "phase": "Scoping",
                "activities_completed": 3,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to execute scoping activities: {str(e)}")
        return ActivityResult(success=False, error=str(e))