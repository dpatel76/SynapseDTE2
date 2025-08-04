"""
Universal Metrics API endpoints
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.universal_metrics_service import (
    get_universal_metrics_service, 
    MetricsContext,
    UniversalMetrics
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/universal-metrics/{cycle_id}/{report_id}")
async def get_universal_metrics(
    cycle_id: int,
    report_id: int,
    phase_name: Optional[str] = Query(None, description="Optional phase name for phase-specific metrics"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get universal metrics for a specific cycle and report.
    
    Returns consistent metrics across all phases including:
    - Total attributes (approved in planning)
    - DQ rules (all and approved)
    - Scoped attributes (PK and Non-PK)
    - Approved samples and their LOBs
    - Data providers
    - Test cases (total, passed, failed, pending)
    """
    try:
        logger.info(f"Getting universal metrics for cycle {cycle_id}, report {report_id}, phase {phase_name}")
        
        # Create metrics context
        context = MetricsContext(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=current_user.user_id,
            user_role=current_user.role,
            lob_id=current_user.lob_id,
            phase_name=phase_name
        )
        
        # Get metrics service
        metrics_service = get_universal_metrics_service(db)
        
        # Get universal metrics
        metrics = await metrics_service.get_metrics(context)
        
        # Convert to dict for response
        response = {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "metrics": {
                # Core metrics
                "total_attributes": metrics.total_attributes,
                "all_dq_rules": metrics.all_dq_rules,
                "approved_dq_rules": metrics.approved_dq_rules,
                "scoped_attributes": {
                    "primary_key": metrics.scoped_attributes_pk,
                    "non_primary_key": metrics.scoped_attributes_non_pk,
                    "total": metrics.scoped_attributes_total
                },
                "approved_samples": metrics.approved_samples,
                "lobs_count": metrics.lobs_count,
                "data_providers_count": metrics.data_providers_count,
                "test_cases": {
                    "total": metrics.test_cases_total,
                    "passed": metrics.test_cases_passed,
                    "failed": metrics.test_cases_failed,
                    "pending": metrics.test_cases_pending
                },
                # Computed metrics
                "rates": {
                    "dq_rules_approval": round(metrics.dq_rules_approval_rate, 2),
                    "test_execution": round(metrics.test_execution_rate, 2),
                    "test_pass": round(metrics.test_pass_rate, 2)
                }
            },
            "calculated_at": metrics.calculated_at.isoformat(),
            "context": {
                "user_id": context.user_id,
                "user_role": context.user_role,
                "phase_name": context.phase_name
            }
        }
        
        # Add phase-specific metrics if requested
        if phase_name:
            phase_metrics = await metrics_service.get_phase_specific_metrics(context)
            response["phase_specific_metrics"] = phase_metrics
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting universal metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get universal metrics: {str(e)}"
        )


@router.get("/universal-metrics/summary")
async def get_metrics_summary(
    cycle_id: int = Query(..., description="Cycle ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a summary of universal metrics across all reports in a cycle.
    """
    try:
        logger.info(f"Getting metrics summary for cycle {cycle_id}")
        
        # This would aggregate metrics across all reports
        # For now, return a placeholder
        return {
            "cycle_id": cycle_id,
            "message": "Summary endpoint to be implemented",
            "total_reports": 0
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics summary: {str(e)}"
        )