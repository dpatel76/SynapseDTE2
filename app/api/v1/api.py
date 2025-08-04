"""
Clean Architecture API Router
Maps existing API endpoints to clean architecture implementations
"""

from fastapi import APIRouter

# Import clean architecture endpoint routers
from app.api.v1.endpoints import (
    auth,  # Using clean architecture auth
    users,
    lobs,  # Use non-clean version temporarily until model compatibility is resolved
    reports,
    report_inventory_async as report_inventory,  # New redesigned report inventory
    cycle_reports,
    cycles,
    planning,  # Single unified planning system
    data_profiling,  # Using clean architecture data profiling
    scoping,  # Using clean architecture scoping
    scoping_submission,  # Scoping submission with versioning
    data_owner,
    data_owner_lob_assignment,  # New unified data owner LOB assignment system
    sample_selection,  # Use non-clean version temporarily until model issues resolved
    request_info,  # Re-enabled after model consolidation
    request_info_documents,  # Request info document submissions
    rfi_versions,  # RFI versioning system
    rfi_data_sources,  # RFI data source management
    rfi_test_cases,  # RFI test case management
    rfi_evidence_submission,  # RFI evidence submission
    # test_execution,  # Legacy - removed in favor of unified
    test_execution,  # Unified test execution
    observation_management,
    test_report,  # Keep for now until migrated
    admin_sla,
    # admin_rbac_clean as admin_rbac,  # Temporarily disabled due to import issue
    admin_rbac,  # Use non-clean version for now
    test,  # Keep for testing
    data_sources,
    sla,  # Keep for now until migrated
    llm,
    metrics,  # Using clean architecture metrics
    background_jobs,  # Keep for now until migrated
    data_dictionary,  # Keep for now until migrated
    dashboards,
    activity_states,  # Activity state management
    # versioning_clean as versioning,  # Temporarily disabled - causes duplicate table definitions
    # versioning,  # Temporarily disabled due to table conflicts with unified models
    workflow_management,  # Re-enabled workflow management
    workflow_metrics,
    workflow_versioning,  # Re-enabled workflow versioning
    workflow_compensation,  # Re-enabled workflow compensation
    temporal_signals,  # Temporal signal endpoints
    workflow_start,  # Workflow start endpoint
    data_profiling_rules,  # Enhanced data profiling rules with individual approval
    data_profiling_assignments,  # Data profiling assignments with workflow status
    data_provider_proxy,  # Data provider proxy for legacy frontend compatibility
    data_profiling_resubmit,  # Data profiling resubmission after report owner feedback
    data_profiling_failed_records,  # Data profiling failed records with PK attributes
    universal_assignments,  # Universal assignment system for role-to-role task delegation
    unified_status,  # Unified status system for phases and activities
    unified_metrics,  # Unified metrics endpoint for consistent metrics across all phases
    analytics,  # Analytics endpoint for performance metrics and trends
    activity_management,  # Generic activity state management system
    versioning,  # Re-enabled after fixing table conflicts
    document_management,  # Document management system
    universal_metrics  # Universal metrics service for consistent metrics
)

api_router = APIRouter()

# Include clean architecture routers with original paths (for frontend compatibility)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(lobs.router, prefix="/lobs", tags=["Lines of Business"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(reports.router, prefix="/reports", tags=["Report Management"])
api_router.include_router(report_inventory.router, prefix="/report-inventory", tags=["Report Inventory"])
api_router.include_router(cycle_reports.router, prefix="/cycle-reports", tags=["Cycle Report Management"])
api_router.include_router(data_sources.router, prefix="/data-sources", tags=["Data Source Management"])
api_router.include_router(cycles.router, prefix="/cycles", tags=["Test Cycle Management"])
api_router.include_router(planning.router, prefix="/planning", tags=["Planning Phase"])
api_router.include_router(planning.router, prefix="/planning-unified", tags=["Planning Phase"])  # Same system, different URL for frontend compatibility
api_router.include_router(data_profiling.router, prefix="/data-profiling", tags=["Data Profiling Phase"])  # Re-enabled with full job manager integration
api_router.include_router(scoping.router, prefix="/scoping", tags=["Scoping Phase"])
api_router.include_router(scoping_submission.router, prefix="/scoping", tags=["Scoping Submission"])
api_router.include_router(data_owner.router, prefix="/data-owner", tags=["Data Provider ID Phase"])
api_router.include_router(data_provider_proxy.router, prefix="/data-provider", tags=["Data Provider Proxy"])
api_router.include_router(data_owner_lob_assignment.router, prefix="", tags=["Data Owner LOB Assignment"])
api_router.include_router(sample_selection.router, prefix="/sample-selection", tags=["Sample Selection"])
api_router.include_router(request_info.router, prefix="/request-info", tags=["Request for Information"])  # Re-enabled after consolidation
api_router.include_router(request_info_documents.router, prefix="/request-info", tags=["Request Info Documents"])
api_router.include_router(rfi_versions.router, prefix="", tags=["RFI Versions"])  # RFI versioning system
api_router.include_router(rfi_data_sources.router, prefix="/rfi", tags=["RFI Data Sources"])  # RFI data source management
api_router.include_router(rfi_test_cases.router, prefix="/rfi", tags=["RFI Test Cases"])  # RFI test case management
api_router.include_router(rfi_evidence_submission.router, prefix="/rfi", tags=["RFI Evidence Submission"])  # RFI evidence submission
api_router.include_router(test_execution.router, prefix="/test-execution", tags=["Test Execution"])
api_router.include_router(observation_management.router, prefix="/observation-enhanced", tags=["Observation Management"])
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
api_router.include_router(versioning.router, prefix="/versions", tags=["Version Management"])  # Re-enabled after fixing table conflicts

# Temporal integration endpoints
api_router.include_router(temporal_signals.router, prefix="/temporal", tags=["Temporal Signals"])
api_router.include_router(workflow_start.router, prefix="", tags=["Workflow Start"])

# Enhanced data profiling rules with individual approval
api_router.include_router(data_profiling_rules.router, prefix="/data-profiling", tags=["Data Profiling Rules"])

# Data profiling assignments with workflow status
api_router.include_router(data_profiling_assignments.router, prefix="/data-profiling", tags=["Data Profiling Assignments"])

# Data profiling resubmission after report owner feedback
api_router.include_router(data_profiling_resubmit.router, prefix="/data-profiling", tags=["Data Profiling Resubmit"])

# Data profiling failed records with primary key attributes
api_router.include_router(data_profiling_failed_records.router, prefix="/data-profiling", tags=["Data Profiling Failed Records"])

# Enhanced data profiling with database support - DISABLED: Features consolidated into main data_profiling.py
# from app.api.v1.endpoints import data_profiling_enhanced
# api_router.include_router(data_profiling_enhanced.router, prefix="/data-profiling-enhanced", tags=["Enhanced Data Profiling"])


# Unified status system - single source of truth for phase and activity status
api_router.include_router(unified_status.router, prefix="/status", tags=["Unified Status System"])

# Unified metrics system - single source of truth for metrics across all phases
api_router.include_router(unified_metrics.router, prefix="/unified-metrics", tags=["Unified Metrics System"])

# Analytics endpoints for performance metrics, trends, and activities
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# Generic activity management system - database-driven activity state tracking
api_router.include_router(activity_management.router, prefix="/activity-management", tags=["Activity Management"])


# Document management system
api_router.include_router(document_management.router, prefix="/document-management", tags=["Document Management"])

# Universal Metrics Service - consistent metrics across all pages and phases
api_router.include_router(universal_metrics.router, prefix="/metrics", tags=["Universal Metrics"])

# Universal Assignment Framework endpoints - ONLY universal assignments, no role-specific
from app.api.v1.endpoints import universal_assignments, universal_migration
api_router.include_router(universal_assignments.router, prefix="/universal-assignments", tags=["Universal Assignments"])
api_router.include_router(universal_migration.router, prefix="/universal-migration", tags=["Universal Assignment Migration"])

# Workflow endpoints - re-enabled
api_router.include_router(workflow_management.router, prefix="/workflow", tags=["Workflow Management"])
api_router.include_router(workflow_metrics.router, prefix="/workflow-metrics", tags=["Workflow Metrics"])
api_router.include_router(workflow_versioning.router, prefix="/workflow-versions", tags=["Workflow Versioning"])
api_router.include_router(workflow_compensation.router, prefix="/workflow-compensation", tags=["Workflow Compensation"])

# Health check endpoint
@api_router.get("/health")
async def api_health():
    """API health check"""
    return {
        "status": "healthy", 
        "version": "3.2.0",
        "architecture": "clean"
    }