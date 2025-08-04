"""
Test endpoints for E2E testing
These endpoints are only available in test/development environments
"""

import os
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, delete
from pydantic import BaseModel

from app.core.database import get_db
from app.models import (
    User, LOB, Report, TestCycle, CycleReport,
    SLAConfiguration, SLAEscalationRule
)
from app.models.sla import SLAType
from app.core.auth import get_password_hash

router = APIRouter()

# Only enable test endpoints in development/test environments
def check_test_environment():
    """Ensure test endpoints are only available in test environments"""
    env = os.getenv("ENVIRONMENT", "development")
    if env not in ["development", "test"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test endpoints are only available in development/test environments"
        )

# Pydantic models for test data
class TestUser(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role: str
    lob_id: int

class TestLOB(BaseModel):
    name: str
    description: str
    is_active: bool = True

class TestReport(BaseModel):
    report_name: str
    regulation: str = None
    description: str = None
    frequency: str = None
    report_owner_id: int
    lob_id: int
    is_active: bool = True

class TestDataSource(BaseModel):
    name: str
    description: str
    source_type: str
    connection_string: str
    is_active: bool = True

class DatabaseSeedRequest(BaseModel):
    environment: str
    clearExisting: bool = True

@router.post("/seed-database")
async def seed_database(
    request: DatabaseSeedRequest,
    session: AsyncSession = Depends(get_db)
):
    """Seed the database with test data"""
    check_test_environment()
    
    try:
        if request.clearExisting:
            # Clear existing test data
            await session.execute(delete(SLAEscalationRule))
            await session.execute(delete(SLAConfiguration))
            await session.execute(delete(CycleReport))
            await session.execute(delete(TestCycle))
            await session.execute(delete(Report))
            await session.execute(delete(User))
            await session.execute(delete(LOB))
            await session.commit()
        
        # Create default LOBs
        default_lobs = [
            LOB(lob_name="Retail Banking"),
            LOB(lob_name="Commercial Banking"),
            LOB(lob_name="Investment Banking")
        ]
        
        for lob in default_lobs:
            session.add(lob)
        
        await session.commit()
        
        # Create default SLA configurations
        default_sla_configs = [
            SLAConfiguration(
                sla_type=SLAType.DATA_PROVIDER_IDENTIFICATION,
                sla_hours=48,
                warning_hours=8,
                escalation_enabled=True,
                is_active=True,
                business_hours_only=True,
                weekend_excluded=True,
                auto_escalate_on_breach=True,
                escalation_interval_hours=24
            ),
            SLAConfiguration(
                sla_type=SLAType.DATA_PROVIDER_RESPONSE,
                sla_hours=72,
                warning_hours=12,
                escalation_enabled=True,
                is_active=True,
                business_hours_only=True,
                weekend_excluded=True,
                auto_escalate_on_breach=True,
                escalation_interval_hours=24
            ),
            SLAConfiguration(
                sla_type=SLAType.TESTING_COMPLETION,
                sla_hours=120,
                warning_hours=24,
                escalation_enabled=True,
                is_active=True,
                business_hours_only=True,
                weekend_excluded=True,
                auto_escalate_on_breach=True,
                escalation_interval_hours=24
            )
        ]
        
        for config in default_sla_configs:
            session.add(config)
        
        await session.commit()
        
        return {"status": "success", "message": "Database seeded successfully"}
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database seeding failed: {str(e)}"
        )

@router.post("/create-user")
async def create_test_user(
    user_data: TestUser,
    session: AsyncSession = Depends(get_db)
):
    """Create a test user"""
    check_test_environment()
    
    try:
        # Check if user already exists
        existing_user = await session.execute(
            text("SELECT user_id FROM users WHERE email = :email"),
            {"email": user_data.email}
        )
        if existing_user.first():
            return {"status": "exists", "message": f"User {user_data.email} already exists"}
        
        # Get next user_id
        max_user_result = await session.execute(text("SELECT COALESCE(MAX(user_id), 0) FROM users"))
        max_user_id = max_user_result.scalar()
        next_user_id = (max_user_id or 0) + 1
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            user_id=next_user_id,  # Explicitly set the user_id
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role,
            lob_id=user_data.lob_id,
            is_active=True
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)  # Refresh to get the complete user object
        
        return {"status": "success", "message": f"User {user_data.email} created successfully", "user_id": user.user_id}
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}"
        )

@router.post("/create-lob")
async def create_test_lob(
    lob_data: TestLOB,
    session: AsyncSession = Depends(get_db)
):
    """Create a test LOB"""
    check_test_environment()
    
    try:
        lob = LOB(lob_name=lob_data.name)
        
        session.add(lob)
        await session.commit()
        
        return {"status": "success", "message": f"LOB {lob_data.name} created successfully"}
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LOB creation failed: {str(e)}"
        )

@router.post("/create-report")
async def create_test_report(
    report_data: TestReport,
    session: AsyncSession = Depends(get_db)
):
    """Create a test report"""
    check_test_environment()
    
    try:
        report = Report(
            report_name=report_data.report_name,
            regulation=report_data.regulation,
            description=report_data.description,
            frequency=report_data.frequency,
            report_owner_id=report_data.report_owner_id,
            lob_id=report_data.lob_id,
            is_active=report_data.is_active
        )
        
        session.add(report)
        await session.commit()
        
        return {"status": "success", "message": f"Report {report_data.report_name} created successfully"}
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report creation failed: {str(e)}"
        )

@router.post("/create-data-source")
async def create_test_data_source(
    data_source: TestDataSource,
    session: AsyncSession = Depends(get_db)
):
    """Create a test data source"""
    check_test_environment()
    
    try:
        # For now, just return success since we don't have a DataSource model yet
        return {"status": "success", "message": f"Data source {data_source.name} created successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data source creation failed: {str(e)}"
        )

@router.delete("/cleanup-database")
async def cleanup_test_database(
    session: AsyncSession = Depends(get_db)
):
    """Clean up test database"""
    check_test_environment()
    
    try:
        # Clean up test data in reverse dependency order
        await session.execute(delete(SLAEscalationRule))
        await session.execute(delete(SLAConfiguration))
        await session.execute(delete(CycleReport))
        await session.execute(delete(TestCycle))
        await session.execute(delete(Report))
        await session.execute(delete(User))
        await session.execute(delete(LOB))
        await session.commit()
        
        return {"status": "success", "message": "Test database cleaned up successfully"}
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database cleanup failed: {str(e)}"
        )

@router.delete("/cleanup-files")
async def cleanup_test_files():
    """Clean up test files"""
    check_test_environment()
    
    try:
        # For now, just return success since we don't have file management yet
        return {"status": "success", "message": "Test files cleaned up successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File cleanup failed: {str(e)}"
        )

@router.post("/reset-sla")
async def reset_sla_configurations(
    session: AsyncSession = Depends(get_db)
):
    """Reset SLA configurations to default state"""
    check_test_environment()
    
    try:
        # Clear existing SLA data
        await session.execute(delete(SLAEscalationRule))
        await session.execute(delete(SLAConfiguration))
        await session.commit()
        
        return {"status": "success", "message": "SLA configurations reset successfully"}
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SLA reset failed: {str(e)}"
        )

@router.get("/health")
async def test_health():
    """Test endpoints health check"""
    check_test_environment()
    return {"status": "healthy", "environment": os.getenv("ENVIRONMENT", "development")}

@router.get("/get-lobs")
async def get_lobs(session: AsyncSession = Depends(get_db)):
    """Get all LOBs for test setup"""
    check_test_environment()
    
    try:
        result = await session.execute(text("SELECT lob_id, lob_name FROM lobs ORDER BY lob_id"))
        lobs = [{"lob_id": row[0], "lob_name": row[1]} for row in result.fetchall()]
        return lobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch LOBs: {str(e)}")

@router.get("/get-users")
async def get_users(session: AsyncSession = Depends(get_db)):
    """Get all users for test setup"""
    check_test_environment()
    
    try:
        result = await session.execute(text("SELECT user_id, email, role, first_name, last_name FROM users ORDER BY user_id"))
        users = [
            {
                "user_id": row[0], 
                "email": row[1], 
                "role": row[2],
                "first_name": row[3],
                "last_name": row[4]
            } 
            for row in result.fetchall()
        ]
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}") 