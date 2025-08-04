"""Planning Phase Activities for Temporal Workflow

Standard structure:
1. Start Planning Phase (Tester initiated)
2. Planning-specific activities
3. Complete Planning Phase (Tester initiated)
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

logger = logging.getLogger(__name__)


@activity.defn
async def start_planning_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> ActivityResult:
    """Start Planning Phase - Initiated by Tester
    
    This is the standard entry point for the Planning phase.
    Validates user permissions and initializes phase.
    """
    try:
        async with get_db() as db:
            # Verify user has permission to start phase
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to start Planning phase"
                )
            
            # Get or create workflow phase record
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                # Create phase record
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Planning",
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
            
            logger.info(f"Started Planning phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "started_at": phase.actual_start_date.isoformat(),
                    "started_by": user_id
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to start Planning phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def review_regulatory_requirements_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Review regulatory requirements for the report
    
    Planning-specific activity that analyzes regulatory context
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
            
            # Simulate regulatory review (in production, might call LLM service)
            regulatory_context = {
                "regulation": report.regulation or "General Compliance",
                "frequency": report.frequency or "Quarterly",
                "key_requirements": [
                    "Data accuracy and completeness",
                    "Timely submission",
                    "Audit trail maintenance",
                    "Executive attestation"
                ],
                "compliance_areas": [
                    "Financial reporting",
                    "Risk management",
                    "Data governance"
                ]
            }
            
            # Store review results
            cycle_report = await db.execute(
                select(CycleReport).where(
                    CycleReport.cycle_id == cycle_id,
                    CycleReport.report_id == report_id
                )
            )
            cycle_report = cycle_report.scalar_one_or_none()
            
            if cycle_report:
                # Update metadata with regulatory review
                if not cycle_report.metadata:
                    cycle_report.metadata = {}
                cycle_report.metadata["regulatory_review"] = regulatory_context
                await db.commit()
            
            logger.info(f"Completed regulatory requirements review for report {report_id}")
            return ActivityResult(
                success=True,
                data=regulatory_context
            )
            
    except Exception as e:
        logger.error(f"Failed to review regulatory requirements: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def identify_initial_attributes_activity(
    cycle_id: int,
    report_id: int,
    regulatory_context: Dict[str, Any]
) -> ActivityResult:
    """Identify initial test attributes based on regulatory requirements
    
    Planning-specific activity that creates initial attribute list
    """
    try:
        async with get_db() as db:
            # Check if attributes already exist
            existing = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.report_id == report_id
                )
            )
            existing_attributes = existing.scalars().all()
            
            if existing_attributes:
                # Return existing attributes
                return ActivityResult(
                    success=True,
                    data={
                        "attributes_count": len(existing_attributes),
                        "attributes": [
                            {
                                "attribute_id": attr.attribute_id,
                                "attribute_name": attr.attribute_name,
                                "description": attr.description,
                                "is_critical": attr.is_critical
                            }
                            for attr in existing_attributes[:10]  # Limit for response
                        ],
                        "source": "existing"
                    }
                )
            
            # Create initial attributes based on regulatory context
            initial_attributes = [
                {
                    "name": "Customer ID",
                    "description": "Unique identifier for customer",
                    "is_critical": True
                },
                {
                    "name": "Account Number",
                    "description": "Primary account number",
                    "is_critical": True
                },
                {
                    "name": "Balance",
                    "description": "Current account balance",
                    "is_critical": True
                },
                {
                    "name": "Transaction Date",
                    "description": "Date of transaction",
                    "is_critical": False
                },
                {
                    "name": "Risk Rating",
                    "description": "Customer risk rating",
                    "is_critical": True
                }
            ]
            
            # Create attribute records
            created_attributes = []
            for attr_data in initial_attributes:
                attribute = ReportAttribute(
                    report_id=report_id,
                    attribute_name=attr_data["name"],
                    description=attr_data["description"],
                    is_critical=attr_data["is_critical"],
                    created_by=1  # System user
                )
                db.add(attribute)
                created_attributes.append(attribute)
            
            await db.commit()
            
            logger.info(f"Created {len(created_attributes)} initial attributes for report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "attributes_count": len(created_attributes),
                    "attributes": [
                        {
                            "attribute_id": attr.attribute_id,
                            "attribute_name": attr.attribute_name,
                            "description": attr.description,
                            "is_critical": attr.is_critical
                        }
                        for attr in created_attributes
                    ],
                    "source": "generated"
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to identify initial attributes: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def create_test_plan_activity(
    cycle_id: int,
    report_id: int,
    attributes_data: Dict[str, Any]
) -> ActivityResult:
    """Create test plan document
    
    Planning-specific activity that generates test plan
    """
    try:
        async with get_db() as db:
            # Get cycle and report details
            cycle = await db.get(TestCycle, cycle_id)
            report = await db.get(Report, report_id)
            
            if not cycle or not report:
                return ActivityResult(
                    success=False,
                    error="Cycle or report not found"
                )
            
            # Create test plan
            test_plan = {
                "cycle_name": cycle.cycle_name,
                "report_name": report.report_name,
                "planned_start": cycle.start_date.isoformat() if cycle.start_date else None,
                "planned_end": cycle.end_date.isoformat() if cycle.end_date else None,
                "total_attributes": attributes_data.get("attributes_count", 0),
                "critical_attributes": len([
                    a for a in attributes_data.get("attributes", [])
                    if a.get("is_critical")
                ]),
                "phases": [
                    {
                        "phase": "Planning",
                        "duration_days": 2,
                        "activities": ["Review requirements", "Identify attributes", "Create test plan"]
                    },
                    {
                        "phase": "Scoping",
                        "duration_days": 2,
                        "activities": ["Enhance attributes", "Determine testing approach", "Get approvals"]
                    },
                    {
                        "phase": "Sample Selection",
                        "duration_days": 1,
                        "activities": ["Generate samples", "Validate samples", "Approve samples"]
                    },
                    {
                        "phase": "Data Provider ID",
                        "duration_days": 1,
                        "activities": ["Identify data providers", "Assign attributes", "Notify providers"]
                    },
                    {
                        "phase": "Request Info",
                        "duration_days": 3,
                        "activities": ["Send requests", "Collect responses", "Validate data"]
                    },
                    {
                        "phase": "Test Execution",
                        "duration_days": 2,
                        "activities": ["Execute tests", "Document results", "Generate evidence"]
                    },
                    {
                        "phase": "Observation Management",
                        "duration_days": 1,
                        "activities": ["Document findings", "Categorize issues", "Create observations"]
                    },
                    {
                        "phase": "Finalize Test Report",
                        "duration_days": 1,
                        "activities": ["Consolidate results", "Generate final report", "Get executive approval"]
                    }
                ],
                "success_criteria": [
                    "All critical attributes tested",
                    "95% test coverage achieved",
                    "All findings documented",
                    "Executive sign-off obtained"
                ]
            }
            
            # Store test plan in cycle report metadata
            cycle_report = await db.execute(
                select(CycleReport).where(
                    CycleReport.cycle_id == cycle_id,
                    CycleReport.report_id == report_id
                )
            )
            cycle_report = cycle_report.scalar_one_or_none()
            
            if cycle_report:
                if not cycle_report.metadata:
                    cycle_report.metadata = {}
                cycle_report.metadata["test_plan"] = test_plan
                await db.commit()
            
            logger.info(f"Created test plan for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data=test_plan
            )
            
    except Exception as e:
        logger.error(f"Failed to create test plan: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def complete_planning_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    completion_notes: Optional[str] = None
) -> ActivityResult:
    """Complete Planning Phase - Initiated by Tester
    
    This is the standard exit point for the Planning phase.
    Validates completion criteria and marks phase as complete.
    """
    try:
        async with get_db() as db:
            # Verify user has permission
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to complete Planning phase"
                )
            
            # Get workflow phase
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                return ActivityResult(
                    success=False,
                    error="Planning phase not found"
                )
            
            # Verify completion criteria
            # 1. Check if attributes exist
            attributes = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.report_id == report_id
                )
            )
            attributes_count = len(attributes.scalars().all())
            
            if attributes_count == 0:
                return ActivityResult(
                    success=False,
                    error="Cannot complete Planning phase: No attributes identified"
                )
            
            # 2. Check if test plan exists
            cycle_report = await db.execute(
                select(CycleReport).where(
                    CycleReport.cycle_id == cycle_id,
                    CycleReport.report_id == report_id
                )
            )
            cycle_report = cycle_report.scalar_one_or_none()
            
            if not cycle_report or not cycle_report.metadata or "test_plan" not in cycle_report.metadata:
                return ActivityResult(
                    success=False,
                    error="Cannot complete Planning phase: Test plan not created"
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
            
            logger.info(f"Completed Planning phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "completed_at": phase.actual_end_date.isoformat(),
                    "completed_by": user_id,
                    "duration_days": (phase.actual_end_date - phase.actual_start_date).days if phase.actual_start_date else 0,
                    "status": phase.status
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to complete Planning phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def execute_planning_activities(
    cycle_id: int,
    report_id: int,
    metadata: Dict[str, Any]
) -> ActivityResult:
    """Execute all Planning phase activities in sequence
    
    This orchestrates the planning-specific activities between
    start and complete.
    """
    try:
        results = {}
        
        # 1. Review regulatory requirements
        regulatory_result = await review_regulatory_requirements_activity(
            cycle_id, report_id
        )
        if not regulatory_result.success:
            return regulatory_result
        results["regulatory_review"] = regulatory_result.data
        
        # 2. Identify initial attributes
        attributes_result = await identify_initial_attributes_activity(
            cycle_id, report_id, regulatory_result.data
        )
        if not attributes_result.success:
            return attributes_result
        results["attributes"] = attributes_result.data
        
        # 3. Create test plan
        test_plan_result = await create_test_plan_activity(
            cycle_id, report_id, attributes_result.data
        )
        if not test_plan_result.success:
            return test_plan_result
        results["test_plan"] = test_plan_result.data
        
        return ActivityResult(
            success=True,
            data={
                "phase": "Planning",
                "activities_completed": 3,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to execute planning activities: {str(e)}")
        return ActivityResult(success=False, error=str(e))