"""
Clean Architecture Dashboard API endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.core.auth import UserRoles
from app.models.user import User
from app.application.dtos.dashboard import (
    DashboardTimeFilter,
    ExecutiveDashboardDTO,
    DataOwnerDashboardDTO,
    DataExecutiveDashboardDTO,
    BoardReportSummaryDTO,
    DashboardHealthDTO,
    DashboardSummaryDTO
)
from app.application.use_cases.dashboard import (
    GetExecutiveDashboardUseCase,
    GetDataOwnerDashboardUseCase,
    GetDataExecutiveDashboardUseCase,
    GetBoardReportSummaryUseCase
)

router = APIRouter()


@router.get("/executive", response_model=ExecutiveDashboardDTO)
async def get_executive_dashboard(
    time_filter: str = Query("current_quarter", description="Time filter: current_quarter, current_year, last_30_days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Report Owner Executive dashboard with strategic KPIs and portfolio analytics"""
    
    # Check if user has executive role
    if current_user.role not in [UserRoles.ADMIN, UserRoles.REPORT_OWNER_EXECUTIVE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Executive dashboard access requires Report Owner Executive role"
        )
    
    try:
        use_case = GetExecutiveDashboardUseCase()
        dashboard_filter = DashboardTimeFilter(filter_type=time_filter)
        
        dashboard_data = await use_case.execute(
            user_id=current_user.user_id,
            time_filter=dashboard_filter,
            db=db
        )
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load executive dashboard: {str(e)}"
        )


@router.get("/executive/board-report", response_model=BoardReportSummaryDTO)
async def get_board_report_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get board-level report summary for executive presentation"""
    
    # Check if user has executive role
    if current_user.role not in [UserRoles.ADMIN, UserRoles.REPORT_OWNER_EXECUTIVE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Board report access requires Report Owner Executive role"
        )
    
    try:
        use_case = GetBoardReportSummaryUseCase()
        
        board_report = await use_case.execute(
            user_id=current_user.user_id,
            db=db
        )
        
        return board_report
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate board report: {str(e)}"
        )


@router.get("/data-owner", response_model=DataOwnerDashboardDTO)
async def get_data_owner_dashboard(
    time_filter: str = Query("last_30_days", description="Time filter: last_7_days, last_30_days, last_90_days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Data Owner dashboard with performance metrics and assignment tracking"""
    
    # Check if user has data owner role
    if current_user.role not in [UserRoles.ADMIN, UserRoles.DATA_OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data Owner dashboard access requires Data Owner role"
        )
    
    try:
        use_case = GetDataOwnerDashboardUseCase()
        dashboard_filter = DashboardTimeFilter(filter_type=time_filter)
        
        dashboard_data = await use_case.execute(
            user_id=current_user.user_id,
            time_filter=dashboard_filter,
            db=db
        )
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load data owner dashboard: {str(e)}"
        )


@router.get("/cdo", response_model=DataExecutiveDashboardDTO)
async def get_cdo_dashboard(
    time_filter: str = Query("last_30_days", description="Time filter: last_7_days, last_30_days, last_90_days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Data Executive dashboard with LOB-wide analytics and team performance metrics"""
    
    # Check if user has Data Executive role
    if current_user.role not in [UserRoles.ADMIN, UserRoles.DATA_EXECUTIVE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data Executive dashboard access requires Data Executive role"
        )
    
    try:
        use_case = GetDataExecutiveDashboardUseCase()
        dashboard_filter = DashboardTimeFilter(filter_type=time_filter)
        
        dashboard_data = await use_case.execute(
            user_id=current_user.user_id,
            time_filter=dashboard_filter,
            db=db
        )
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load Data Executive dashboard: {str(e)}"
        )


@router.get("/health", response_model=DashboardHealthDTO)
async def get_dashboard_services_health(
    current_user: User = Depends(get_current_user)
):
    """Get health status of all dashboard services (Admin only)"""
    
    # Check admin privileges
    if current_user.role != UserRoles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        return DashboardHealthDTO(
            dashboard_services_status="healthy",
            services={
                "executive_dashboard": {
                    "status": "healthy",
                    "features": ["Strategic KPIs", "Portfolio Analytics", "Board Reports"]
                },
                "data_owner_dashboard": {
                    "status": "healthy",
                    "features": ["Performance Metrics", "Assignment Tracking", "Quality Metrics"]
                },
                "cdo_dashboard": {
                    "status": "healthy",
                    "features": ["LOB Analytics", "Team Performance", "Escalation Management"]
                }
            },
            capabilities={
                "total_dashboard_types": 3,
                "role_coverage": ["Executive", "Data Owner", "Data Executive"],
                "analytics_features": ["Strategic KPIs", "Performance Tracking", "Trend Analysis", "Action Items"]
            }
        )
        
    except Exception as e:
        return DashboardHealthDTO(
            dashboard_services_status="unhealthy",
            services={},
            capabilities={}
        )


@router.get("/summary", response_model=DashboardSummaryDTO)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user)
):
    """Get summary of available dashboards for current user"""
    
    try:
        available_dashboards = []
        
        # Check user role and add available dashboards
        if current_user.role in [UserRoles.ADMIN, UserRoles.REPORT_OWNER_EXECUTIVE]:
            available_dashboards.append({
                "type": "executive",
                "name": "Executive Dashboard",
                "description": "Strategic KPIs and portfolio analytics",
                "features": ["Portfolio Compliance Rate", "Operational Efficiency", "Risk Management", "Financial Metrics"],
                "endpoint": "/api/v1/dashboards/executive"
            })
        
        if current_user.role in [UserRoles.ADMIN, UserRoles.DATA_OWNER]:
            available_dashboards.append({
                "type": "data_owner",
                "name": "Data Owner Dashboard",
                "description": "Performance metrics and assignment tracking",
                "features": ["Assignment Overview", "Performance Metrics", "Quality Scores", "Workload Analysis"],
                "endpoint": "/api/v1/dashboards/data-owner"
            })
        
        if current_user.role in [UserRoles.ADMIN, UserRoles.DATA_EXECUTIVE]:
            available_dashboards.append({
                "type": "cdo",
                "name": "Data Executive Dashboard",
                "description": "LOB-wide analytics and team performance",
                "features": ["LOB Overview", "Team Performance", "Assignment Analytics", "Escalation Management"],
                "endpoint": "/api/v1/dashboards/cdo"
            })
        
        return DashboardSummaryDTO(
            user_role=current_user.role,
            available_dashboards=available_dashboards,
            total_available=len(available_dashboards),
            dashboard_capabilities={
                "time_filtering": True,
                "real_time_data": True,
                "export_capabilities": True,
                "customizable_views": True
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard summary: {str(e)}"
        )


# Role-specific dashboard endpoints for backwards compatibility
@router.get("/admin", response_model=Dict[str, Any])
async def get_admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard (redirects to executive dashboard)"""
    if current_user.role != UserRoles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # For admin, return a combined view
    return {
        "message": "Use /executive endpoint for detailed dashboard",
        "available_dashboards": [
            "/api/v1/dashboards/executive",
            "/api/v1/dashboards/data-owner", 
            "/api/v1/dashboards/cdo"
        ],
        "admin_stats": {
            "total_users": 45,
            "active_sessions": 12,
            "system_health": "healthy"
        }
    }


@router.get("/test-executive", response_model=Dict[str, Any])
async def get_test_executive_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get test executive dashboard"""
    if current_user.role not in [UserRoles.ADMIN, UserRoles.TEST_EXECUTIVE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test Executive access required"
        )
    
    # Test executive specific metrics
    return {
        "test_cycles": {
            "active": 5,
            "completed": 12,
            "upcoming": 3
        },
        "team_performance": {
            "testers_assigned": 8,
            "average_completion_time": "14.5 days",
            "quality_score": "92%"
        },
        "workflow_status": {
            "planning": 3,
            "scoping": 5,
            "execution": 7,
            "reporting": 2
        }
    }


@router.get("/tester", response_model=Dict[str, Any])
async def get_tester_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tester dashboard"""
    if current_user.role not in [UserRoles.ADMIN, UserRoles.TESTER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tester access required"
        )
    
    # Tester specific metrics
    return {
        "my_assignments": {
            "planning": 2,
            "scoping": 3,
            "testing": 5,
            "observations": 1
        },
        "performance": {
            "completed_this_week": 8,
            "average_time": "2.3 days",
            "quality_score": "A"
        },
        "upcoming_deadlines": [
            {"task": "Complete testing for Report A", "due": "2023-12-15"},
            {"task": "Submit observations for Report B", "due": "2023-12-18"}
        ]
    }


@router.get("/report-owner", response_model=Dict[str, Any])
async def get_report_owner_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get report owner dashboard"""
    if current_user.role not in [UserRoles.ADMIN, UserRoles.REPORT_OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report Owner access required"
        )
    
    # Report owner specific metrics
    return {
        "my_reports": {
            "total": 8,
            "in_progress": 5,
            "completed": 3
        },
        "pending_reviews": {
            "scoping": 2,
            "cycle_report_sample_selection_samples": 1,
            "observations": 3
        },
        "compliance_status": {
            "on_track": 6,
            "at_risk": 1,
            "overdue": 1
        }
    }


@router.get("/report-executive", response_model=Dict[str, Any])
async def get_report_executive_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get report owner executive dashboard (redirects to executive dashboard)"""
    if current_user.role not in [UserRoles.ADMIN, UserRoles.REPORT_OWNER_EXECUTIVE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report Owner Executive access required"
        )
    
    # Redirect to executive dashboard
    return {
        "message": "Use /executive endpoint for detailed dashboard",
        "endpoint": "/api/v1/dashboards/executive"
    }