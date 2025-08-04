"""
Unified Metrics API endpoint that provides consistent metrics across all workflow phases
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.dependencies import get_db, get_current_user
from app.core.permissions import require_permission
from app.models.user import User

router = APIRouter()


@router.get("/{cycle_id}/reports/{report_id}")
@require_permission("metrics", "read")
async def get_unified_metrics(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get unified metrics for a cycle/report combination using direct SQL queries"""
    
    try:
        # Use direct SQL queries to avoid model import issues
        
        # Total attributes
        result = await db.execute(
            text("SELECT COUNT(*) FROM report_attributes WHERE cycle_id = :cycle_id AND report_id = :report_id AND is_latest_version = true"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        total_attributes = result.scalar() or 0
        
        # Scoped attributes
        result = await db.execute(
            text("SELECT COUNT(*) FROM report_attributes WHERE cycle_id = :cycle_id AND report_id = :report_id AND is_scoped = true AND is_latest_version = true"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        scoped_attributes = result.scalar() or 0
        
        # Total samples
        result = await db.execute(
            text("SELECT COUNT(DISTINCT sample_id) FROM test_cases WHERE cycle_id = :cycle_id AND report_id = :report_id"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        total_samples = result.scalar() or 0
        
        # Completed test cases
        result = await db.execute(
            text("SELECT COUNT(*) FROM cycle_report_test_execution_test_executions WHERE cycle_id = :cycle_id AND report_id = :report_id AND result IS NOT NULL"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        completed_test_cases = result.scalar() or 0
        
        # Total test cases
        result = await db.execute(
            text("SELECT COUNT(*) FROM cycle_report_test_execution_test_executions WHERE cycle_id = :cycle_id AND report_id = :report_id"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        total_test_cases = result.scalar() or 0
        
        # Finalized observations - check observation_groups table first
        result = await db.execute(
            text("SELECT COUNT(*) FROM observation_groups WHERE cycle_id = :cycle_id AND report_id = :report_id AND approval_status = 'FULLY_APPROVED'"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        finalized_observations = result.scalar() or 0
        
        # Total observations
        result = await db.execute(
            text("SELECT COUNT(*) FROM observation_groups WHERE cycle_id = :cycle_id AND report_id = :report_id"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        total_observations = result.scalar() or 0
        
        # If no observations in observation_groups, try observations table
        if total_observations == 0:
            result = await db.execute(
                text("SELECT COUNT(*) FROM observations WHERE cycle_id = :cycle_id AND report_id = :report_id"),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            total_observations = result.scalar() or 0
        
        return {
            # Core workflow metrics
            "total_attributes": total_attributes,
            "scoped_attributes": scoped_attributes,
            "total_samples": total_samples,
            "completed_test_cases": completed_test_cases,
            "total_test_cases": total_test_cases,
            "finalized_observations": finalized_observations,
            "total_observations": total_observations,
            
            # Meta information
            "cycle_id": cycle_id,
            "report_id": report_id,
            "calculated_at": "now"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating unified metrics: {str(e)}"
        )


@router.get("/{cycle_id}/reports/{report_id}/phase/{phase_name}")
@require_permission("metrics", "read")
async def get_phase_metrics(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get metrics for a specific phase"""
    
    try:
        metrics_calculator = BaseMetricsCalculator(db)
        
        # Route to appropriate phase metrics
        phase_method_map = {
            "planning": metrics_calculator._calculate_planning_metrics,
            "scoping": metrics_calculator._calculate_scoping_metrics,
            "data_profiling": metrics_calculator._calculate_scoping_metrics,  # Alias
            "sample_selection": metrics_calculator._calculate_sample_selection_metrics,
            "data_provider_id": metrics_calculator._calculate_data_provider_id_metrics,
            "request_info": metrics_calculator._calculate_request_info_metrics,
            "testing": metrics_calculator._calculate_testing_metrics,
            "test_execution": metrics_calculator._calculate_testing_metrics,  # Alias
            "observations": metrics_calculator._calculate_observation_metrics,
            "observation_management": metrics_calculator._calculate_observation_metrics,  # Alias
        }
        
        phase_key = phase_name.lower().replace("-", "_")
        if phase_key not in phase_method_map:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown phase: {phase_name}"
            )
        
        metrics = await phase_method_map[phase_key](cycle_id, report_id)
        
        return {
            "phase_name": phase_name,
            "cycle_id": cycle_id,
            "report_id": report_id,
            "metrics": metrics,
            "calculated_at": "now"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating {phase_name} metrics: {str(e)}"
        )