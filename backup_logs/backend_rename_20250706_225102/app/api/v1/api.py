"""
Clean Architecture API Router
Maps existing API endpoints to clean architecture implementations
"""

from fastapi import APIRouter

# Import clean architecture endpoint routers
from app.api.v1.endpoints import (
    auth_clean as auth,  # Using clean architecture auth
    users_clean as users,
    lobs,  # Use non-clean version temporarily until model compatibility is resolved
    reports_clean as reports,
    cycle_reports_clean as cycle_reports,
    cycles_clean as cycles,
    planning_clean as planning,  # Using clean architecture planning
    data_profiling_clean as data_profiling,  # Using clean architecture data profiling
    scoping_clean as scoping,  # Using clean architecture scoping
    scoping_submission,  # Scoping submission with versioning
    data_owner_clean as data_owner,
    sample_selection,  # Use non-clean version temporarily until model issues resolved
    request_info_clean as request_info,
    test_execution_clean as test_execution,
    observation_management_clean as observation_management,
    observation_enhanced,  # Keep for now until migrated
    test_report,  # Keep for now until migrated
    admin_sla_clean as admin_sla,
    # admin_rbac_clean as admin_rbac,  # Temporarily disabled due to import issue
    admin_rbac,  # Use non-clean version for now
    test,  # Keep for testing
    data_sources_clean as data_sources,
    sla,  # Keep for now until migrated
    llm_clean as llm,
    metrics_clean as metrics,  # Using clean architecture metrics
    background_jobs,  # Keep for now until migrated
    data_dictionary,  # Keep for now until migrated
    dashboards_clean as dashboards,
    activity_states,  # Activity state management
    versioning,  # Versioning support
    # workflow_management,  # Temporarily disabled due to circular import
    workflow_metrics,
    # workflow_versioning,  # Temporarily disabled due to circular import
    # workflow_compensation,  # Temporarily disabled due to circular import
    temporal_signals,  # Temporal signal endpoints
    workflow_start,  # Workflow start endpoint
    data_profiling_rules,  # Enhanced data profiling rules with individual approval
    universal_assignments,  # Universal assignment system for role-to-role task delegation
    unified_status,  # Unified status system for phases and activities
    unified_metrics  # Unified metrics endpoint for consistent metrics across all phases
)

api_router = APIRouter()

# Include clean architecture routers with original paths (for frontend compatibility)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(lobs.router, prefix="/lobs", tags=["Lines of Business"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(reports.router, prefix="/reports", tags=["Report Management"])
api_router.include_router(cycle_reports.router, prefix="/cycle-reports", tags=["Cycle Report Management"])
api_router.include_router(data_sources.router, prefix="/data-sources", tags=["Data Source Management"])
api_router.include_router(cycles.router, prefix="/cycles", tags=["Test Cycle Management"])
api_router.include_router(planning.router, prefix="/planning", tags=["Planning Phase"])
api_router.include_router(data_profiling.router, prefix="/data-profiling", tags=["Data Profiling Phase"])
api_router.include_router(scoping.router, prefix="/scoping", tags=["Scoping Phase"])
api_router.include_router(scoping_submission.router, prefix="/scoping", tags=["Scoping Submission"])
api_router.include_router(data_owner.router, prefix="/data-owner", tags=["Data Provider ID Phase"])
api_router.include_router(sample_selection.router, prefix="/sample-selection", tags=["Sample Selection"])
api_router.include_router(request_info.router, prefix="/request-info", tags=["Request for Information"])
api_router.include_router(test_execution.router, prefix="/test-execution", tags=["Test Execution"])
api_router.include_router(observation_management.router, prefix="/observation-management", tags=["Observation Management"])
api_router.include_router(observation_enhanced.router, prefix="/observation-enhanced", tags=["Enhanced Observation Management"])
api_router.include_router(test_report.router, prefix="/test-report", tags=["Test Report Phase"])
api_router.include_router(admin_sla.router, prefix="/admin", tags=["Admin SLA"])
api_router.include_router(admin_rbac.router, prefix="/admin/rbac", tags=["Admin RBAC"])
api_router.include_router(test.router, prefix="/test", tags=["Test Endpoints"])

# Service endpoints
api_router.include_router(sla.router, prefix="/sla", tags=["SLA Management"])
api_router.include_router(llm.router, prefix="/llm", tags=["LLM Integration"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics & Analytics"])
api_router.include_router(background_jobs.router, prefix="/jobs", tags=["Background Jobs"])
api_router.include_router(data_dictionary.router, prefix="/data-dictionary", tags=["Regulatory Data Dictionary"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards"])
api_router.include_router(activity_states.router, prefix="/activities", tags=["Activity State Management"])
api_router.include_router(versioning.router, prefix="/versions", tags=["Version Management"])

# Temporal integration endpoints
api_router.include_router(temporal_signals.router, prefix="/temporal", tags=["Temporal Signals"])
api_router.include_router(workflow_start.router, prefix="", tags=["Workflow Start"])

# Enhanced data profiling rules with individual approval
api_router.include_router(data_profiling_rules.router, prefix="/data-profiling", tags=["Data Profiling Rules"])

# Universal assignment system
api_router.include_router(universal_assignments.router, prefix="/universal-assignments", tags=["Universal Assignments"])

# Unified status system - single source of truth for phase and activity status
api_router.include_router(unified_status.router, prefix="/status", tags=["Unified Status System"])

# Unified metrics system - single source of truth for metrics across all phases
api_router.include_router(unified_metrics.router, prefix="/unified-metrics", tags=["Unified Metrics System"])

# Report Owner Assignment endpoints
from app.api.v1.endpoints import report_owner_assignments
api_router.include_router(report_owner_assignments.router, prefix="", tags=["Report Owner Assignments"])

# Universal Assignment Framework endpoints
from app.api.v1.endpoints import universal_assignments, data_profiling_assignments, universal_migration
api_router.include_router(universal_assignments.router, prefix="", tags=["Universal Assignments"])
api_router.include_router(data_profiling_assignments.router, prefix="", tags=["Data Profiling Assignments"])
api_router.include_router(universal_migration.router, prefix="", tags=["Universal Assignment Migration"])

# Workflow endpoints - temporarily disabled due to circular import
# api_router.include_router(workflow_management.router, prefix="/workflow", tags=["Workflow Management"])
api_router.include_router(workflow_metrics.router, prefix="/workflow-metrics", tags=["Workflow Metrics"])
# api_router.include_router(workflow_versioning.router, prefix="/workflow-versions", tags=["Workflow Versioning"])
# api_router.include_router(workflow_compensation.router, prefix="/workflow-compensation", tags=["Workflow Compensation"])

# Health check endpoint
@api_router.get("/health")
async def api_health():
    """API health check"""
    return {
        "status": "healthy", 
        "version": "2.0.0",
        "architecture": "clean"
    }