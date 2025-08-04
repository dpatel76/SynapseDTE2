"""Report Inventory API endpoints"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import Report as ReportInventory, User
from app.schemas.base import Message
from pydantic import BaseModel, Field
from datetime import datetime


router = APIRouter()


# Pydantic schemas
class ReportInventoryBase(BaseModel):
    report_number: str = Field(..., max_length=50)
    report_name: str = Field(..., max_length=255)
    description: Optional[str] = None
    frequency: Optional[str] = Field(None, max_length=50)
    business_unit: Optional[str] = Field(None, max_length=100)
    regulatory_requirement: bool = False
    status: str = "Active"


class ReportInventoryCreate(ReportInventoryBase):
    pass


class ReportInventoryUpdate(BaseModel):
    report_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    frequency: Optional[str] = Field(None, max_length=50)
    business_unit: Optional[str] = Field(None, max_length=100)
    regulatory_requirement: Optional[bool] = None
    status: Optional[str] = None


class ReportInventoryResponse(ReportInventoryBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    created_by: Optional[int]
    updated_by: Optional[int]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ReportInventoryResponse])
async def get_report_inventory(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all reports from inventory"""
    query = select(ReportInventory)
    
    if status:
        query = query.where(ReportInventory.status == status)
    
    query = query.offset(skip).limit(limit)
    reports = db.scalars(query).all()
    
    return reports


@router.get("/{report_id}", response_model=ReportInventoryResponse)
def get_report_by_id(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report by ID"""
    report = db.get(ReportInventory, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    return report


@router.post("/", response_model=ReportInventoryResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    report_data: ReportInventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report in inventory"""
    # Check if report number already exists
    existing = db.scalar(
        select(ReportInventory).where(
            ReportInventory.report_number == report_data.report_number
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report number {report_data.report_number} already exists"
        )
    
    report = ReportInventory(
        **report_data.dict(),
        created_by_id=current_user.user_id,
        updated_by_id=current_user.user_id
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report


@router.put("/{report_id}", response_model=ReportInventoryResponse)
def update_report(
    report_id: int,
    report_data: ReportInventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a report in inventory"""
    report = db.get(ReportInventory, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    update_data = report_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)
    
    report.updated_by_id = current_user.user_id
    
    db.commit()
    db.refresh(report)
    
    return report


@router.delete("/{report_id}", response_model=Message)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a report from inventory (soft delete by setting status to Archived)"""
    report = db.get(ReportInventory, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    report.status = "Archived"
    report.updated_by_id = current_user.user_id
    
    db.commit()
    
    return Message(message=f"Report {report.report_number} has been archived")