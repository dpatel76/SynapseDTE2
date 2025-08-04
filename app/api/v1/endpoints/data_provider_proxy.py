"""
Data Provider proxy endpoints to support legacy frontend URLs
This file provides compatibility for frontend expecting /data-provider endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.workflow import WorkflowPhase
from app.models.cycle_report_data_source import CycleReportDataSource
from sqlalchemy import select, and_
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/cycles/{cycle_id}/reports/{report_id}/data-sources")
async def get_data_sources_for_report(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get data sources for a cycle/report from planning phase
    This endpoint provides compatibility for frontend expecting /data-provider/cycles/{cycle_id}/reports/{report_id}/data-sources
    """
    try:
        # Get planning phase which contains the data sources
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
        )
        planning_phase = phase_query.scalar_one_or_none()
        
        if not planning_phase:
            logger.warning(f"No planning phase found for cycle {cycle_id}, report {report_id}")
            return []
        
        # Query data sources from planning phase
        data_sources_query = await db.execute(
            select(CycleReportDataSource).where(
                CycleReportDataSource.phase_id == planning_phase.phase_id
            )
        )
        data_sources = data_sources_query.scalars().all()
        
        # Format response
        result = []
        for ds in data_sources:
            source_data = {
                "id": ds.id,
                "source_name": ds.name,
                "source_type": ds.source_type.value if ds.source_type else None,
                "database_type": ds.source_type.value if ds.source_type else None,
                "connection_config": ds.connection_config or {},
                "is_active": ds.is_active,
                "created_at": ds.created_at.isoformat() if ds.created_at else None,
                "updated_at": ds.updated_at.isoformat() if ds.updated_at else None
            }
            
            # Add table/schema info if available
            if ds.connection_config:
                config = ds.connection_config
                source_data["database_name"] = config.get("database", config.get("database_name"))
                source_data["schema_name"] = config.get("schema", config.get("schema_name", "public"))
                source_data["table_name"] = config.get("table_name", config.get("default_table"))
            
            result.append(source_data)
        
        logger.info(f"Found {len(result)} data sources for cycle {cycle_id}, report {report_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching data sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch data sources: {str(e)}"
        )