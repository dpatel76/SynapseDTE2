"""
Clean Architecture API Router
"""

from fastapi import APIRouter

# Import clean endpoint routers
try:
    from app.api.v1.endpoints import auth_clean as auth
except ImportError:
    from app.api.v1.endpoints import auth

try:
    from app.api.v1.endpoints import reports_clean as reports
except ImportError:
    from app.api.v1.endpoints import reports

try:
    from app.api.v1.endpoints import cycles_clean as cycles
except ImportError:
    from app.api.v1.endpoints import cycles

try:
    from app.api.v1.endpoints import users_clean as users
except ImportError:
    from app.api.v1.endpoints import users

try:
    from app.api.v1.endpoints import lobs_clean as lobs
except ImportError:
    from app.api.v1.endpoints import lobs

from app.api.v1.endpoints import (
    planning_clean as planning,
    scoping_clean as scoping,
    test_execution_clean as test_execution,
    workflow_clean as workflow,
    dashboards_clean as dashboards,
    observation_management_clean as observation_management,
    request_info_clean as request_info,
    sample_selection_clean as sample_selection,
    data_owner_clean as data_owner,
    metrics_clean as metrics,
    # Use existing endpoints for now
    sla,
    admin_rbac,
    admin_sla
)

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Core Management
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(lobs.router, prefix="/lobs", tags=["Lines of Business"])
api_router.include_router(reports.router, prefix="/reports", tags=["Report Management"])
api_router.include_router(cycles.router, prefix="/cycles", tags=["Test Cycle Management"])

# Workflow Phases - Clean Architecture
api_router.include_router(planning.router, prefix="/planning", tags=["Planning Phase"])
api_router.include_router(scoping.router, prefix="/scoping", tags=["Scoping Phase"])
api_router.include_router(test_execution.router, prefix="/test-execution", tags=["Test Execution"])

# Workflow Phases - Traditional (for now)
api_router.include_router(data_owner.router, prefix="/data-owner", tags=["Data Owner Phase"])
api_router.include_router(sample_selection.router, prefix="/sample-selection", tags=["CycleReportSampleSelectionSamples Selection"])
api_router.include_router(request_info.router, prefix="/request-info", tags=["Request for Information"])
api_router.include_router(observation_management.router, prefix="/observation-management", tags=["Observation Management"])

# Services
api_router.include_router(workflow.router, prefix="/workflow", tags=["Workflow Management"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics & Analytics"])
api_router.include_router(sla.router, prefix="/sla", tags=["SLA Management"])

# Admin
api_router.include_router(admin_rbac.router, prefix="/admin/rbac", tags=["Admin RBAC"])
api_router.include_router(admin_sla.router, prefix="/admin/sla", tags=["Admin SLA"])

# Health check
@api_router.get("/health")
async def health_check():
    """API health check"""
    return {"status": "healthy", "architecture": "clean", "version": "2.0.0"}
