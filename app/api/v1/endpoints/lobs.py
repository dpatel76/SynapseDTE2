"""
LOB (Lines of Business) management API endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.core.exceptions import ValidationException, NotFoundException
from app.core.logging import audit_logger
from app.core.audit_utils import set_audit_fields_on_create, set_audit_fields_on_update
from app.models.lob import LOB
from app.models.user import User
from app.models.report import Report
from app.models.test_cycle import TestCycle
from app.schemas.lob import (
    LOBCreate,
    LOBUpdate,
    LOBResponse,
    LOBListResponse,
    LOBDetailResponse,
    LOBStatsResponse
)

router = APIRouter()

@router.post("/", response_model=LOBResponse, status_code=status.HTTP_201_CREATED)
@require_permission("lobs", "create")
async def create_lob(
    lob_data: LOBCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LOBResponse:
    """
    Create a new Line of Business (management roles only)
    """
    # Check if LOB name already exists
    existing_lob = await db.execute(
        select(LOB).where(LOB.lob_name == lob_data.lob_name)
    )
    if existing_lob.scalar_one_or_none():
        raise ValidationException("LOB name already exists")

    # Get next lob_id
    max_lob_result = await db.execute(select(LOB.lob_id).order_by(LOB.lob_id.desc()).limit(1))
    max_lob_id = max_lob_result.scalar_one_or_none()
    next_lob_id = (max_lob_id or 0) + 1

    # Create new LOB
    new_lob = LOB(
        lob_id=next_lob_id,
        lob_name=lob_data.lob_name
    )
    
    # Set audit fields
    set_audit_fields_on_create(new_lob, current_user)

    db.add(new_lob)
    await db.commit()
    await db.refresh(new_lob)

    # Log LOB creation
    audit_logger.log_user_action(
        user_id=current_user.user_id,
        action="lob_created",
        resource_type="lob",
        resource_id=new_lob.lob_id,
        details={"lob_name": new_lob.lob_name}
    )

    return LOBResponse.model_validate(new_lob)

@router.get("/", response_model=LOBListResponse)
@require_permission("lobs", "read")
async def get_lobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LOBListResponse:
    """
    Get list of all LOBs with user and report counts
    """
    result = await db.execute(select(LOB).order_by(LOB.lob_name))
    lobs = result.scalars().all()
    
    # Get counts for each LOB using a single query with LEFT JOIN
    lob_stats_query = await db.execute(
        select(
            LOB.lob_id,
            LOB.lob_name,
            LOB.created_at,
            LOB.updated_at,
            func.count(func.distinct(User.user_id)).label('user_count'),
            func.count(func.distinct(Report.report_id)).label('report_count')
        )
        .outerjoin(User, LOB.lob_id == User.lob_id)
        .outerjoin(Report, LOB.lob_id == Report.lob_id)
        .group_by(LOB.lob_id, LOB.lob_name, LOB.created_at, LOB.updated_at)
        .order_by(LOB.lob_name)
    )
    
    lob_stats = lob_stats_query.all()
    
    lob_details = []
    for row in lob_stats:
        lob_details.append(LOBDetailResponse(
            lob_id=row.lob_id,
            lob_name=row.lob_name,
            created_at=row.created_at,
            updated_at=row.updated_at,
            user_count=row.user_count or 0,
            report_count=row.report_count or 0,
            active_cycles=0  # Placeholder
        ))

    return LOBListResponse(
        lobs=lob_details,
        total=len(lobs)
    )

@router.get("/active", response_model=List[LOBResponse])
@require_permission("lobs", "read")
async def get_active_lobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[LOBResponse]:
    """
    Get list of all active LOBs (for dropdowns and selection)
    """
    result = await db.execute(select(LOB).order_by(LOB.lob_name))
    lobs = result.scalars().all()

    return [LOBResponse.model_validate(lob) for lob in lobs]

@router.get("/{lob_id}", response_model=LOBDetailResponse)
@require_permission("lobs", "read")
async def get_lob(
    lob_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LOBDetailResponse:
    """
    Get LOB details by ID
    """
    # Get LOB
    lob_result = await db.execute(select(LOB).where(LOB.lob_id == lob_id))
    lob = lob_result.scalar_one_or_none()

    if not lob:
        raise NotFoundException(f"LOB with ID {lob_id} not found")

    # Get user count
    user_count_result = await db.execute(
        select(func.count(User.user_id)).where(User.lob_id == lob_id)
    )
    user_count = user_count_result.scalar() or 0

    # Get report count
    report_count_result = await db.execute(
        select(func.count(Report.report_id)).where(Report.lob_id == lob_id)
    )
    report_count = report_count_result.scalar() or 0

    # Get active cycles count (simplified - would need proper join in real implementation)
    active_cycles = 0  # Placeholder

    return LOBDetailResponse(
        lob_id=lob.lob_id,
        lob_name=lob.lob_name,
        created_at=lob.created_at,
        updated_at=lob.updated_at,
        user_count=user_count,
        report_count=report_count,
        active_cycles=active_cycles
    )

@router.put("/{lob_id}", response_model=LOBResponse)
@require_permission("lobs", "update", resource_id_param="lob_id")
async def update_lob(
    lob_id: int,
    lob_data: LOBUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LOBResponse:
    """
    Update LOB information (management roles only)
    """
    # Get existing LOB
    lob_result = await db.execute(select(LOB).where(LOB.lob_id == lob_id))
    lob = lob_result.scalar_one_or_none()

    if not lob:
        raise NotFoundException(f"LOB with ID {lob_id} not found")

    # Check if new name already exists (if changing name)
    if lob_data.lob_name and lob_data.lob_name != lob.lob_name:
        existing_lob = await db.execute(
            select(LOB).where(LOB.lob_name == lob_data.lob_name)
        )
        if existing_lob.scalar_one_or_none():
            raise ValidationException("LOB name already exists")

    # Update LOB
    old_values = {"lob_name": lob.lob_name}

    if lob_data.lob_name is not None:
        lob.lob_name = lob_data.lob_name
    
    # Set audit fields
    set_audit_fields_on_update(lob, current_user)

    await db.commit()
    await db.refresh(lob)

    # Log LOB update
    audit_logger.log_user_action(
        user_id=current_user.user_id,
        action="lob_updated",
        resource_type="lob",
        resource_id=lob.lob_id,
        details={
            "old_values": old_values,
            "new_values": {"lob_name": lob.lob_name}
        }
    )

    return LOBResponse.model_validate(lob)

@router.delete("/{lob_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("lobs", "delete", resource_id_param="lob_id")
async def delete_lob(
    lob_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete LOB (management roles only)
    """
    # Get existing LOB
    lob_result = await db.execute(select(LOB).where(LOB.lob_id == lob_id))
    lob = lob_result.scalar_one_or_none()

    if not lob:
        raise NotFoundException(f"LOB with ID {lob_id} not found")

    # Check if LOB has associated users
    user_count_result = await db.execute(
        select(func.count(User.user_id)).where(User.lob_id == lob_id)
    )
    user_count = user_count_result.scalar() or 0

    if user_count > 0:
        raise ValidationException(f"Cannot delete LOB with {user_count} associated users")

    # Check if LOB has associated reports
    report_count_result = await db.execute(
        select(func.count(Report.report_id)).where(Report.lob_id == lob_id)
    )
    report_count = report_count_result.scalar() or 0

    if report_count > 0:
        raise ValidationException(f"Cannot delete LOB with {report_count} associated reports")

    # Delete LOB
    await db.delete(lob)
    await db.commit()

    # Log LOB deletion
    audit_logger.log_user_action(
        user_id=current_user.user_id,
        action="lob_deleted",
        resource_type="lob",
        resource_id=lob_id,
        details={"lob_name": lob.lob_name}
    )

@router.get("/stats/overview", response_model=LOBStatsResponse)
@require_permission("lobs", "read")
async def get_lob_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LOBStatsResponse:
    """
    Get LOB statistics overview (management roles only)
    """
    # Get total LOBs
    total_lobs_result = await db.execute(select(func.count(LOB.lob_id)))
    total_lobs = total_lobs_result.scalar() or 0

    # Get users by LOB
    users_by_lob_result = await db.execute(
        select(LOB.lob_name, func.count(User.user_id))
        .outerjoin(User, LOB.lob_id == User.lob_id)
        .group_by(LOB.lob_id, LOB.lob_name)
    )
    users_by_lob = {row[0]: row[1] for row in users_by_lob_result.all()}

    # Get reports by LOB
    reports_by_lob_result = await db.execute(
        select(LOB.lob_name, func.count(Report.report_id))
        .outerjoin(Report, LOB.lob_id == Report.lob_id)
        .group_by(LOB.lob_id, LOB.lob_name)
    )
    reports_by_lob = {row[0]: row[1] for row in reports_by_lob_result.all()}

    # Active cycles by LOB (placeholder)
    active_cycles_by_lob = {}

    return LOBStatsResponse(
        total_lobs=total_lobs,
        users_by_lob=users_by_lob,
        reports_by_lob=reports_by_lob,
        active_cycles_by_lob=active_cycles_by_lob
    )
