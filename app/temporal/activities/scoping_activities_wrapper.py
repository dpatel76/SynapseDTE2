"""Scoping Phase Activities - Wrappers for existing use cases

These activities call the existing scoping phase implementation,
particularly the LLM service for generating test attributes.
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging

from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
from app.services.llm_service import get_llm_service
from app.models import Report, CycleReport

logger = logging.getLogger(__name__)


@activity.defn
async def start_scoping_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Start scoping phase using existing workflow orchestrator"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Start scoping phase
            phase = await orchestrator.start_scoping_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                notes="Started via Temporal workflow",
                user_id=user_id
            )
            
            logger.info(f"Started scoping phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "phase_id": phase.phase_id,
                "data": {
                    "phase_name": phase.phase_name,
                    "state": phase.state,
                    "status": phase.schedule_status
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start scoping phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def execute_scoping_activities(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Execute scoping activities - primarily LLM attribute generation"""
    try:
        async for db in get_db():
            # Get report details
            report = await db.get(Report, report_id)
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            # Get LLM service (existing implementation)
            llm_service = get_llm_service()
            
            # Call existing LLM service to generate attributes
            # This is the SAME service used by the scoping endpoint
            result = await llm_service.generate_test_attributes(
                regulatory_context=report.regulatory_citation or "",
                report_type=report.report_type,
                business_rules=report.business_rules or "",
                sample_size=25,  # Default
                cycle_id=cycle_id,
                report_id=report_id,
                preferred_provider="claude"  # Use Claude for quality
            )
            
            if result['success']:
                attributes = result.get('attributes', [])
                logger.info(f"Generated {len(attributes)} test attributes for report {report_id}")
                
                # Store attributes using existing logic
                orchestrator = get_workflow_orchestrator(db)
                for attr in attributes:
                    await orchestrator.create_report_attribute(
                        report_id=report_id,
                        attribute_data=attr,
                        created_by=user_id
                    )
                
                return {
                    "success": True,
                    "data": {
                        "attributes_generated": len(attributes),
                        "llm_provider": result.get('metadata', {}).get('provider'),
                        "model_used": result.get('metadata', {}).get('model'),
                        "attributes": attributes
                    }
                }
            else:
                raise Exception(f"LLM generation failed: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"Failed to execute scoping activities: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def complete_scoping_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    phase_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Complete scoping phase and advance workflow"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Mark all attributes as approved (for workflow automation)
            attributes = phase_data.get('attributes', [])
            if attributes:
                await orchestrator.approve_all_attributes(
                    report_id=report_id,
                    approved_by=user_id,
                    notes="Auto-approved via workflow"
                )
            
            # Complete scoping phase
            phase = await orchestrator.complete_scoping_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                completion_notes=f"Generated {len(attributes)} attributes",
                user_id=user_id
            )
            
            # Advance to next phase
            await orchestrator.advance_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                from_phase="Scoping",
                to_phase="Sample Selection",
                user_id=user_id
            )
            
            logger.info(f"Completed scoping phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_name": phase.phase_name,
                    "attributes_count": len(attributes),
                    "next_phase": "Sample Selection"
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete scoping phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }