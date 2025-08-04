"""
Clean architecture implementation of Admin API endpoints
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.auth import UserRoles
from app.models.user import User
from app.services.security_service import get_security_service, SecurityService
from app.services.backup_service import get_backup_service, BackupService
from app.services.cache_service import get_cache_service, CacheService
from app.services.audit_database_service import get_audit_database_service, AuditDatabaseService

from app.application.dtos.admin import (
    # Security Management
    KeyRotationResultDTO,
    SecurityStatusDTO,
    PasswordValidationRequestDTO,
    PasswordValidationResultDTO,
    SecurityReportDTO,
    # Backup Management
    CreateBackupRequestDTO,
    BackupOperationResponseDTO,
    BackupListResponseDTO,
    RestoreBackupRequestDTO,
    BackupStatusDTO,
    # System Health
    SystemHealthDTO,
    StorageHealthDTO,
    # Cache Management
    CacheHealthDTO,
    CacheMetricsDTO,
    ClearCacheRequestDTO,
    ClearCacheResponseDTO,
    ListCacheKeysResponseDTO,
    # Comprehensive System Health
    ComprehensiveSystemHealthDTO,
    # Audit Database Management
    AuditEventQueryDTO,
    AuditEventsResponseDTO,
    AuditSummaryDTO,
    ExportAuditDataRequestDTO,
    ExportAuditDataResponseDTO,
    AuditCleanupResponseDTO,
    FlushAuditQueueResponseDTO,
    AuditDatabaseHealthDTO
)

from app.application.use_cases.admin import (
    # Security Management
    RotateEncryptionKeysUseCase,
    GetSecurityStatusUseCase,
    ValidatePasswordUseCase,
    GenerateSecurityReportUseCase,
    # Backup Management
    CreateBackupUseCase,
    ListBackupsUseCase,
    RestoreBackupUseCase,
    CleanupOldBackupsUseCase,
    GetBackupStatusUseCase,
    # System Health
    GetSystemHealthUseCase,
    GetStorageHealthUseCase,
    # Cache Management
    GetCacheHealthUseCase,
    GetCacheMetricsUseCase,
    ClearCacheUseCase,
    ListCacheKeysUseCase,
    # Comprehensive System Health
    GetComprehensiveSystemHealthUseCase,
    # Audit Database Management
    QueryAuditEventsUseCase,
    GetAuditSummaryUseCase,
    ExportAuditDataUseCase,
    CleanupOldAuditEventsUseCase,
    FlushAuditQueueUseCase,
    GetAuditDatabaseHealthUseCase
)

router = APIRouter()


# Security Management Endpoints
@router.post(
    "/security/rotate-keys",
    response_model=KeyRotationResultDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def rotate_encryption_keys(
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger key rotation (Admin only)"""
    use_case = RotateEncryptionKeysUseCase(
        db=db,
        current_user=current_user,
        security_service=security_service
    )
    return await use_case.execute(None)


@router.get(
    "/security/status",
    response_model=SecurityStatusDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_security_status(
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service),
    db: AsyncSession = Depends(get_db)
):
    """Get security service status (Admin only)"""
    use_case = GetSecurityStatusUseCase(
        db=db,
        current_user=current_user,
        security_service=security_service
    )
    return await use_case.execute(None)


@router.post(
    "/security/validate-password",
    response_model=PasswordValidationResultDTO
)
async def validate_password_complexity(
    request: PasswordValidationRequestDTO,
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service),
    db: AsyncSession = Depends(get_db)
):
    """Validate password against complexity rules"""
    # Allow users to validate their own passwords, admins can validate any
    if request.user_id and request.user_id != current_user.user_id and current_user.role != UserRoles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot validate password for other users"
        )
    
    use_case = ValidatePasswordUseCase(
        db=db,
        current_user=current_user,
        security_service=security_service
    )
    return await use_case.execute(request)


@router.get(
    "/security/report",
    response_model=SecurityReportDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_security_report(
    time_period_days: int = Query(30, description="Time period in days"),
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service),
    db: AsyncSession = Depends(get_db)
):
    """Generate security metrics report (Admin only)"""
    use_case = GenerateSecurityReportUseCase(
        db=db,
        current_user=current_user,
        security_service=security_service
    )
    return await use_case.execute(time_period_days)


# Backup Management Endpoints
@router.post(
    "/backup/create",
    response_model=BackupOperationResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def create_backup(
    background_tasks: BackgroundTasks,
    request: CreateBackupRequestDTO = CreateBackupRequestDTO(),
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
    db: AsyncSession = Depends(get_db)
):
    """Create a manual backup (Admin only)"""
    use_case = CreateBackupUseCase(
        db=db,
        current_user=current_user,
        backup_service=backup_service
    )
    
    # Add actual backup task to background
    background_tasks.add_task(
        backup_service.create_backup,
        request.category,
        request.backup_name
    )
    
    return await use_case.execute(request)


@router.get(
    "/backup/list",
    response_model=BackupListResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def list_backups(
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
    db: AsyncSession = Depends(get_db)
):
    """List all available backups (Admin only)"""
    use_case = ListBackupsUseCase(
        db=db,
        current_user=current_user,
        backup_service=backup_service
    )
    return await use_case.execute(None)


@router.post(
    "/backup/restore",
    response_model=BackupOperationResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def restore_backup(
    request: RestoreBackupRequestDTO,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
    db: AsyncSession = Depends(get_db)
):
    """Restore from a backup (Admin only)"""
    use_case = RestoreBackupUseCase(
        db=db,
        current_user=current_user,
        backup_service=backup_service
    )
    
    # Add actual restore task to background
    background_tasks.add_task(
        backup_service.restore_backup,
        request.backup_name,
        request.categories,
        request.target_path
    )
    
    return await use_case.execute(request)


@router.delete(
    "/backup/cleanup",
    response_model=BackupOperationResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def cleanup_old_backups(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
    db: AsyncSession = Depends(get_db)
):
    """Clean up old backups (Admin only)"""
    use_case = CleanupOldBackupsUseCase(
        db=db,
        current_user=current_user,
        backup_service=backup_service
    )
    
    # Add actual cleanup task to background
    background_tasks.add_task(backup_service.cleanup_old_backups)
    
    return await use_case.execute(None)


@router.get(
    "/backup/status",
    response_model=BackupStatusDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_backup_status(
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
    db: AsyncSession = Depends(get_db)
):
    """Get backup service status (Admin only)"""
    use_case = GetBackupStatusUseCase(
        db=db,
        current_user=current_user,
        backup_service=backup_service
    )
    return await use_case.execute(None)


# System Health Endpoints
@router.get(
    "/health/system",
    response_model=SystemHealthDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_system_health(
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service),
    backup_service: BackupService = Depends(get_backup_service),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive system health status (Admin only)"""
    use_case = GetSystemHealthUseCase(
        db=db,
        current_user=current_user,
        security_service=security_service,
        backup_service=backup_service
    )
    return await use_case.execute(None)


@router.get(
    "/health/storage",
    response_model=StorageHealthDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_storage_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get storage health metrics (Admin only)"""
    use_case = GetStorageHealthUseCase(
        db=db,
        current_user=current_user
    )
    return await use_case.execute(None)


@router.get(
    "/health/cache-service",
    response_model=CacheHealthDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_cache_service_health(
    current_user: User = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db)
) -> CacheHealthDTO:
    """Get cache service health status (Admin only)"""
    use_case = GetCacheHealthUseCase(
        db=db,
        current_user=current_user,
        cache_service=cache_service
    )
    return await use_case.execute(None)


@router.get(
    "/cache/metrics",
    response_model=CacheMetricsDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_cache_metrics(
    current_user: User = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db)
) -> CacheMetricsDTO:
    """Get cache performance metrics (Admin only)"""
    use_case = GetCacheMetricsUseCase(
        db=db,
        current_user=current_user,
        cache_service=cache_service
    )
    return await use_case.execute(None)


@router.post(
    "/cache/clear",
    response_model=ClearCacheResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def clear_cache(
    request: ClearCacheRequestDTO = ClearCacheRequestDTO(),
    current_user: User = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db)
) -> ClearCacheResponseDTO:
    """Clear cache data (Admin only)"""
    use_case = ClearCacheUseCase(
        db=db,
        current_user=current_user,
        cache_service=cache_service
    )
    return await use_case.execute(request)


@router.get(
    "/cache/keys",
    response_model=ListCacheKeysResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def list_cache_keys(
    category: Optional[str] = Query("default", description="Cache category"),
    pattern: Optional[str] = Query("*", description="Pattern to match"),
    limit: int = Query(100, description="Maximum number of keys to return"),
    current_user: User = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db)
) -> ListCacheKeysResponseDTO:
    """List cache keys (Admin only)"""
    use_case = ListCacheKeysUseCase(
        db=db,
        current_user=current_user,
        cache_service=cache_service
    )
    return await use_case.execute({
        "category": category,
        "pattern": pattern,
        "limit": limit
    })


@router.get(
    "/system-health/comprehensive",
    response_model=ComprehensiveSystemHealthDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_comprehensive_system_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    security_service: SecurityService = Depends(get_security_service),
    backup_service: BackupService = Depends(get_backup_service),
    cache_service: CacheService = Depends(get_cache_service),
    audit_service: AuditDatabaseService = Depends(get_audit_database_service)
) -> ComprehensiveSystemHealthDTO:
    """Get comprehensive system health status (Admin only)"""
    use_case = GetComprehensiveSystemHealthUseCase(
        db=db,
        current_user=current_user,
        security_service=security_service,
        backup_service=backup_service,
        cache_service=cache_service,
        audit_service=audit_service
    )
    return await use_case.execute(None)


# Audit Database Management Endpoints
@router.get(
    "/audit/events",
    response_model=AuditEventsResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def query_audit_events(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    event_types: Optional[List[str]] = Query(None, description="Event types to filter"),
    user_id: Optional[int] = Query(None, description="User ID to filter"),
    username: Optional[str] = Query(None, description="Username to filter"),
    resource_type: Optional[str] = Query(None, description="Resource type to filter"),
    compliance_only: bool = Query(False, description="Show only compliance-relevant events"),
    limit: int = Query(100, description="Maximum number of events"),
    offset: int = Query(0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    audit_service: AuditDatabaseService = Depends(get_audit_database_service),
    db: AsyncSession = Depends(get_db)
) -> AuditEventsResponseDTO:
    """Query audit events (Admin only)"""
    # Parse dates if provided
    start_datetime = None
    end_datetime = None
    
    if start_date:
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    query_dto = AuditEventQueryDTO(
        start_date=start_datetime,
        end_date=end_datetime,
        event_types=event_types,
        user_id=user_id,
        username=username,
        resource_type=resource_type,
        compliance_only=compliance_only,
        limit=limit,
        offset=offset
    )
    
    use_case = QueryAuditEventsUseCase(
        db=db,
        current_user=current_user,
        audit_service=audit_service
    )
    return await use_case.execute(query_dto)


@router.get(
    "/audit/summary",
    response_model=AuditSummaryDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_audit_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_user),
    audit_service: AuditDatabaseService = Depends(get_audit_database_service),
    db: AsyncSession = Depends(get_db)
) -> AuditSummaryDTO:
    """Get audit summary statistics (Admin only)"""
    # Parse dates if provided
    start_datetime = None
    end_datetime = None
    
    if start_date:
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    use_case = GetAuditSummaryUseCase(
        db=db,
        current_user=current_user,
        audit_service=audit_service
    )
    return await use_case.execute({
        "start_date": start_datetime,
        "end_date": end_datetime
    })


@router.post(
    "/audit/export",
    response_model=ExportAuditDataResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def export_audit_data(
    start_date: str = Query(..., description="Start date (ISO format)"),
    end_date: str = Query(..., description="End date (ISO format)"),
    format: str = Query("json", description="Export format: json, csv"),
    current_user: User = Depends(get_current_user),
    audit_service: AuditDatabaseService = Depends(get_audit_database_service),
    db: AsyncSession = Depends(get_db)
) -> ExportAuditDataResponseDTO:
    """Export audit data for compliance reporting (Admin only)"""
    # Parse dates
    start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    request_dto = ExportAuditDataRequestDTO(
        start_date=start_datetime,
        end_date=end_datetime,
        format=format
    )
    
    use_case = ExportAuditDataUseCase(
        db=db,
        current_user=current_user,
        audit_service=audit_service
    )
    return await use_case.execute(request_dto)


@router.delete(
    "/audit/cleanup",
    response_model=AuditCleanupResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def cleanup_old_audit_events(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    audit_service: AuditDatabaseService = Depends(get_audit_database_service),
    db: AsyncSession = Depends(get_db)
) -> AuditCleanupResponseDTO:
    """Clean up old audit events past retention period (Admin only)"""
    use_case = CleanupOldAuditEventsUseCase(
        db=db,
        current_user=current_user,
        audit_service=audit_service
    )
    
    # Add actual cleanup task to background
    background_tasks.add_task(audit_service.cleanup_old_events)
    
    return await use_case.execute(None)


@router.post(
    "/audit/flush-queue",
    response_model=FlushAuditQueueResponseDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def flush_audit_queue(
    current_user: User = Depends(get_current_user),
    audit_service: AuditDatabaseService = Depends(get_audit_database_service),
    db: AsyncSession = Depends(get_db)
) -> FlushAuditQueueResponseDTO:
    """Manually flush the audit event queue (Admin only)"""
    use_case = FlushAuditQueueUseCase(
        db=db,
        current_user=current_user,
        audit_service=audit_service
    )
    return await use_case.execute(None)


@router.get(
    "/health/audit-database",
    response_model=AuditDatabaseHealthDTO,
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_audit_database_health(
    current_user: User = Depends(get_current_user),
    audit_service: AuditDatabaseService = Depends(get_audit_database_service),
    db: AsyncSession = Depends(get_db)
) -> AuditDatabaseHealthDTO:
    """Get audit database health status (Admin only)"""
    use_case = GetAuditDatabaseHealthUseCase(
        db=db,
        current_user=current_user,
        audit_service=audit_service
    )
    return await use_case.execute(None)


@router.get(
    "/dashboard/metrics",
    dependencies=[Depends(require_roles([UserRoles.ADMIN]))]
)
async def get_admin_dashboard_metrics(
    year: int = Query(None, description="Year for metrics (defaults to current year)"),
    cycle_id: Optional[int] = Query(None, description="Filter by specific cycle ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get admin dashboard metrics"""
    from datetime import datetime
    from sqlalchemy import select, func, and_
    from app.models import TestCycle, Report, CycleReport, WorkflowPhase
    
    # Default to current year if not specified
    if year is None:
        year = datetime.now().year
    
    # Build year filter
    year_start = datetime(year, 1, 1)
    year_end = datetime(year, 12, 31, 23, 59, 59)
    
    # Get active cycles count
    cycles_query = select(func.count(TestCycle.cycle_id)).where(
        and_(
            TestCycle.is_active == True,
            TestCycle.created_at >= year_start,
            TestCycle.created_at <= year_end
        )
    )
    if cycle_id:
        cycles_query = cycles_query.where(TestCycle.cycle_id == cycle_id)
    
    active_cycles_result = await db.execute(cycles_query)
    active_cycles = active_cycles_result.scalar() or 0
    
    # Get reports metrics
    if cycle_id:
        # Filter by specific cycle
        reports_query = select(
            func.count(CycleReport.report_id.distinct()).label("total_reports")
        ).where(CycleReport.cycle_id == cycle_id)
    else:
        # All reports for the year
        reports_query = select(
            func.count(CycleReport.report_id.distinct()).label("total_reports")
        ).join(
            TestCycle, TestCycle.cycle_id == CycleReport.cycle_id
        ).where(
            and_(
                TestCycle.created_at >= year_start,
                TestCycle.created_at <= year_end
            )
        )
    
    reports_result = await db.execute(reports_query)
    total_reports = reports_result.scalar() or 0
    
    # Get workflow phase metrics
    phase_query = select(
        WorkflowPhase.status,
        func.count(WorkflowPhase.phase_id).label("count")
    ).group_by(WorkflowPhase.status)
    
    if cycle_id:
        phase_query = phase_query.where(WorkflowPhase.cycle_id == cycle_id)
    else:
        # Filter by year through test cycles
        phase_query = phase_query.join(
            TestCycle, TestCycle.cycle_id == WorkflowPhase.cycle_id
        ).where(
            and_(
                TestCycle.created_at >= year_start,
                TestCycle.created_at <= year_end
            )
        )
    
    phase_result = await db.execute(phase_query)
    phase_counts = {row.status: row.count for row in phase_result}
    
    # Calculate report statuses based on workflow phases
    active_reports = phase_counts.get("In Progress", 0)
    completed_reports = phase_counts.get("Complete", 0)
    pending_reports = phase_counts.get("Not Started", 0) + phase_counts.get("Pending Approval", 0)
    
    # Get observations count (placeholder - in real implementation, get from observation tables)
    # For now, estimate based on reports
    total_observations = total_reports * 2  # Average 2 observations per report
    
    return {
        "activeCycles": active_cycles,
        "totalReports": total_reports,
        "activeReports": active_reports,
        "completedReports": completed_reports,
        "pendingReports": pending_reports,
        "totalObservations": total_observations,
        "year": year,
        "cycleId": cycle_id
    }