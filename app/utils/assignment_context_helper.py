"""
Helper functions for enriching assignment context data with report and cycle names
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.report import Report
from app.models.test_cycle import TestCycle


async def enrich_context_with_names(
    context_data: Dict[str, Any],
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Enrich context_data with report_name and cycle_name based on IDs
    
    Args:
        context_data: The context data dictionary containing report_id and/or cycle_id
        db: Database session
        
    Returns:
        Enriched context_data with report_name and cycle_name added if applicable
    """
    enriched_data = context_data.copy()
    
    # Add report name if report_id is present but report_name is missing
    if 'report_id' in enriched_data and 'report_name' not in enriched_data:
        report_id = enriched_data['report_id']
        if report_id:
            try:
                report_id_int = int(report_id) if isinstance(report_id, str) else report_id
                result = await db.execute(
                    select(Report).where(Report.report_id == report_id_int)
                )
                report = result.scalar_one_or_none()
                if report:
                    enriched_data['report_name'] = report.report_name
            except Exception as e:
                # Log error but don't fail
                print(f"Error fetching report name for ID {report_id}: {e}")
    
    # Add cycle name if cycle_id is present but cycle_name is missing
    if 'cycle_id' in enriched_data and 'cycle_name' not in enriched_data:
        cycle_id = enriched_data['cycle_id']
        if cycle_id:
            try:
                cycle_id_int = int(cycle_id) if isinstance(cycle_id, str) else cycle_id
                result = await db.execute(
                    select(TestCycle).where(TestCycle.cycle_id == cycle_id_int)
                )
                cycle = result.scalar_one_or_none()
                if cycle:
                    enriched_data['cycle_name'] = cycle.cycle_name
            except Exception as e:
                # Log error but don't fail
                print(f"Error fetching cycle name for ID {cycle_id}: {e}")
    
    return enriched_data


def create_base_context(
    cycle_id: Optional[int] = None,
    report_id: Optional[int] = None,
    report_name: Optional[str] = None,
    cycle_name: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a base context_data dictionary with standard fields
    
    Args:
        cycle_id: Test cycle ID
        report_id: Report ID
        report_name: Report name (will be fetched if not provided)
        cycle_name: Cycle name (will be fetched if not provided)
        **kwargs: Additional context fields
        
    Returns:
        Context data dictionary
    """
    context = {}
    
    if cycle_id is not None:
        context['cycle_id'] = cycle_id
    if report_id is not None:
        context['report_id'] = report_id
    if report_name:
        context['report_name'] = report_name
    if cycle_name:
        context['cycle_name'] = cycle_name
        
    # Add any additional fields
    context.update(kwargs)
    
    return context