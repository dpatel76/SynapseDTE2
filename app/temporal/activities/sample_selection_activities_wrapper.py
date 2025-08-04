"""Sample Selection Phase Activities - Wrappers for existing use cases

These activities call the existing sample selection implementation
from the clean architecture use cases.
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
from app.infrastructure.container import get_container
from app.application.use_cases.sample_selection import (
    StartSampleSelectionPhaseUseCase,
    CreateSampleSetUseCase,
    AutoSelectSamplesUseCase,
    ApproveSampleSetUseCase,
    CompleteSampleSelectionPhaseUseCase
)
from app.application.dtos.sample_selection import (
    SampleSelectionPhaseStartDTO,
    CreateSampleSetDTO,
    AutoSampleSelectionRequestDTO,
    SampleSelectionPhaseCompleteDTO
)

logger = logging.getLogger(__name__)


@activity.defn
async def start_sample_selection_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Start sample selection phase using existing use case"""
    try:
        async with get_container() as container:
            db = await container.get_db()
            
            # Get the existing use case
            use_case = StartSampleSelectionPhaseUseCase()
            
            # Create DTO with default values
            start_dto = SampleSelectionPhaseStartDTO(
                phase_notes="Started via Temporal workflow",
                default_sample_size=25,
                selection_criteria={
                    "risk_based": True,
                    "coverage_target": 80
                }
            )
            
            # Execute existing use case
            result = await use_case.execute(
                cycle_id=cycle_id,
                report_id=report_id,
                start_data=start_dto,
                user_id=user_id,
                db=db
            )
            
            logger.info(f"Started sample selection phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "phase_id": result.phase_id,
                "data": {
                    "phase_status": result.phase_status,
                    "sample_size": result.default_sample_size
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start sample selection phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def execute_sample_selection_activities(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Execute sample selection using existing auto-selection use case"""
    try:
        async with get_container() as container:
            db = await container.get_db()
            
            # Get report attributes for this report
            from app.models import ReportAttribute
            from sqlalchemy import select
            
            result = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_active == True
                )
            )
            attributes = result.scalars().all()
            attribute_ids = [attr.attribute_id for attr in attributes]
            
            # Use auto-selection use case
            auto_select_use_case = AutoSelectSamplesUseCase()
            
            # Create request DTO
            request_dto = AutoSampleSelectionRequestDTO(
                attribute_ids=attribute_ids,
                use_llm=True,  # Use LLM for intelligent selection
                selection_strategy="risk_based",
                target_count=25
            )
            
            # Execute existing use case
            sample_sets = await auto_select_use_case.execute(
                cycle_id=cycle_id,
                report_id=report_id,
                request_data=request_dto,
                user_id=user_id,
                db=db
            )
            
            # Auto-approve the sample sets
            approve_use_case = ApproveSampleSetUseCase()
            for sample_set in sample_sets:
                await approve_use_case.execute(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    sample_set_id=sample_set.sample_set_id,
                    approval_notes="Auto-approved via workflow",
                    user_id=user_id,
                    db=db
                )
            
            logger.info(f"Created {len(sample_sets)} sample sets for report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "sample_sets_created": len(sample_sets),
                    "total_samples": sum(len(ss.samples) for ss in sample_sets),
                    "sample_set_ids": [ss.sample_set_id for ss in sample_sets]
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to execute sample selection: {str(e)}")
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
    """Complete sample selection phase using existing use case"""
    try:
        async with get_container() as container:
            db = await container.get_db()
            
            # Complete phase using existing use case
            complete_use_case = CompleteSampleSelectionPhaseUseCase()
            
            complete_dto = SampleSelectionPhaseCompleteDTO(
                completion_notes=f"Completed via workflow. Created {phase_data.get('sample_sets_created', 0)} sample sets",
                final_sample_count=phase_data.get('total_samples', 0)
            )
            
            result = await complete_use_case.execute(
                cycle_id=cycle_id,
                report_id=report_id,
                complete_data=complete_dto,
                user_id=user_id,
                db=db
            )
            
            # Advance workflow using orchestrator
            async for db2 in get_db():
                orchestrator = get_workflow_orchestrator(db2)
                await orchestrator.advance_phase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    from_phase="Sample Selection",
                    to_phase="Data Owner Identification",
                    user_id=user_id
                )
            
            logger.info(f"Completed sample selection phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_status": result.phase_status,
                    "completion_timestamp": result.completion_timestamp.isoformat(),
                    "next_phase": "Data Owner Identification"
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete sample selection phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }