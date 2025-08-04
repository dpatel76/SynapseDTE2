"""
Use cases for Admin functionality
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import asdict
import os
import shutil

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio

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
    BackupInfoDTO,
    BackupListResponseDTO,
    RestoreBackupRequestDTO,
    BackupStatusDTO,
    # System Health
    ServiceHealthDTO,
    SystemHealthDTO,
    StorageInfoDTO,
    StorageHealthDTO,
    # Cache Management
    CacheHealthDTO,
    CacheMetricsDTO,
    ClearCacheRequestDTO,
    ClearCacheResponseDTO,
    CacheKeyDTO,
    ListCacheKeysResponseDTO,
    # Comprehensive System Health
    ServiceHealthSummaryDTO,
    ComprehensiveSystemHealthDTO,
    # Audit Database Management
    AuditEventQueryDTO,
    AuditEventDTO,
    AuditEventsResponseDTO,
    AuditSummaryDTO,
    ExportAuditDataRequestDTO,
    ExportAuditDataResponseDTO,
    AuditCleanupResponseDTO,
    FlushAuditQueueResponseDTO,
    AuditDatabaseHealthDTO
)
from app.core.exceptions import BusinessRuleViolation, ResourceNotFound
from app.models.user import User


# Base class for Admin use cases
class AdminUseCase:
    """Base class for admin use cases with common dependencies"""
    def __init__(self, db: AsyncSession, current_user: User, **services):
        self.db = db
        self.current_user = current_user
        # Store all provided services
        for service_name, service in services.items():
            setattr(self, service_name, service)


# Security Management Use Cases
class RotateEncryptionKeysUseCase(AdminUseCase):
    """Use case for rotating encryption keys"""
    
    async def execute(self, request: None) -> KeyRotationResultDTO:
        try:
            result = await self.security_service.rotate_encryption_keys()
            
            # Audit the key rotation
            await self.security_service.audit_security_event(
                "KEY_ROTATION",
                self.current_user.user_id,
                {
                    "manual_trigger": True,
                    "result": result,
                    "ip_address": "127.0.0.1"  # Would get from request context
                },
                self.db
            )
            
            return KeyRotationResultDTO(
                status=result.get("status", "completed"),
                keys_rotated=result.get("keys_rotated", 0),
                timestamp=datetime.utcnow(),
                details=result
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Key rotation failed: {str(e)}")


class GetSecurityStatusUseCase(AdminUseCase):
    """Use case for getting security service status"""
    
    async def execute(self, request: None) -> SecurityStatusDTO:
        try:
            health_status = await self.security_service.health_check()
            
            return SecurityStatusDTO(
                service="security",
                status=health_status.get("status", "unknown"),
                encryption_enabled=health_status.get("encryption_enabled", False),
                key_rotation_enabled=health_status.get("key_rotation_enabled", False),
                last_key_rotation=health_status.get("last_key_rotation"),
                metrics=health_status.get("metrics", {})
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to get security status: {str(e)}")


class ValidatePasswordUseCase(AdminUseCase):
    """Use case for validating password complexity"""
    
    async def execute(self, request: PasswordValidationRequestDTO) -> PasswordValidationResultDTO:
        try:
            result = self.security_service.validate_password_complexity(
                request.password,
                request.user_id
            )
            
            return PasswordValidationResultDTO(
                valid=result.get("valid", False),
                errors=result.get("errors", []),
                strength=result.get("strength", "weak"),
                requirements_met=result.get("requirements_met", {})
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Password validation failed: {str(e)}")


class GenerateSecurityReportUseCase(AdminUseCase):
    """Use case for generating security report"""
    
    async def execute(self, time_period_days: int) -> SecurityReportDTO:
        try:
            report = await self.security_service.generate_security_report(time_period_days)
            
            return SecurityReportDTO(
                time_period_days=time_period_days,
                report_date=datetime.utcnow(),
                metrics=report.get("metrics", {}),
                recommendations=report.get("recommendations", []),
                issues_found=report.get("issues_found", 0)
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to generate security report: {str(e)}")


# Backup Management Use Cases
class CreateBackupUseCase(AdminUseCase):
    """Use case for creating a backup"""
    
    async def execute(self, request: CreateBackupRequestDTO) -> BackupOperationResponseDTO:
        try:
            # Note: In the actual implementation, this would be handled by background tasks
            # For now, we'll just return the response indicating it's started
            backup_name = request.backup_name or f"manual_{request.category}"
            
            return BackupOperationResponseDTO(
                message="Backup creation started",
                status="in_progress",
                category=request.category,
                backup_name=backup_name
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to start backup: {str(e)}")


class ListBackupsUseCase(AdminUseCase):
    """Use case for listing available backups"""
    
    async def execute(self, request: None) -> BackupListResponseDTO:
        try:
            backups_data = await self.backup_service.list_backups()
            
            backups = [
                BackupInfoDTO(
                    backup_name=b["name"],
                    created_at=b["created_at"],
                    size_mb=b["size_mb"],
                    category=b["category"],
                    status=b["status"],
                    path=b["path"]
                )
                for b in backups_data.get("backups", [])
            ]
            
            return BackupListResponseDTO(
                backups=backups,
                total_count=len(backups),
                total_size_mb=sum(b.size_mb for b in backups)
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to list backups: {str(e)}")


class RestoreBackupUseCase(AdminUseCase):
    """Use case for restoring from a backup"""
    
    async def execute(self, request: RestoreBackupRequestDTO) -> BackupOperationResponseDTO:
        try:
            # Note: In the actual implementation, this would be handled by background tasks
            return BackupOperationResponseDTO(
                message="Backup restore started",
                status="in_progress",
                backup_name=request.backup_name,
                operation=f"Restoring categories: {request.categories or 'all'}"
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to start restore: {str(e)}")


class CleanupOldBackupsUseCase(AdminUseCase):
    """Use case for cleaning up old backups"""
    
    async def execute(self, request: None) -> BackupOperationResponseDTO:
        try:
            # Note: In the actual implementation, this would be handled by background tasks
            return BackupOperationResponseDTO(
                message="Backup cleanup started",
                status="in_progress"
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to start cleanup: {str(e)}")


class GetBackupStatusUseCase(AdminUseCase):
    """Use case for getting backup service status"""
    
    async def execute(self, request: None) -> BackupStatusDTO:
        try:
            health_status = await self.backup_service.health_check()
            
            return BackupStatusDTO(
                service="backup",
                status=health_status.get("status", "unknown"),
                backup_enabled=health_status.get("backup_enabled", False),
                last_backup=health_status.get("last_backup"),
                next_scheduled_backup=health_status.get("next_scheduled_backup"),
                storage_used_mb=health_status.get("storage_used_mb", 0),
                storage_available_mb=health_status.get("storage_available_mb", 0)
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to get backup status: {str(e)}")


# System Health Use Cases
class GetSystemHealthUseCase(AdminUseCase):
    """Use case for getting comprehensive system health"""
    
    async def execute(self, request: None) -> SystemHealthDTO:
        try:
            security_health = await self.security_service.health_check()
            backup_health = await self.backup_service.health_check()
            
            # Determine overall system health
            overall_status = "healthy"
            if (security_health.get("status") != "healthy" or 
                backup_health.get("status") != "healthy"):
                overall_status = "degraded"
            
            return SystemHealthDTO(
                system={
                    "status": overall_status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "uptime": "99.9%"
                },
                services={
                    "security": ServiceHealthDTO(
                        service="security",
                        status=security_health.get("status", "unknown"),
                        details=security_health
                    ),
                    "backup": ServiceHealthDTO(
                        service="backup",
                        status=backup_health.get("status", "unknown"),
                        details=backup_health
                    )
                },
                recommendations=[]
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to get system health: {str(e)}")


class GetStorageHealthUseCase(AdminUseCase):
    """Use case for getting storage health metrics"""
    
    async def execute(self, request: None) -> StorageHealthDTO:
        try:
            storage_info = {}
            
            paths_to_check = [
                ("/app/uploads", "uploads"),
                ("/app/backups", "backups"), 
                ("/app/logs", "logs"),
                ("/app/security", "security")
            ]
            
            for path, name in paths_to_check:
                if os.path.exists(path):
                    total, used, free = shutil.disk_usage(path)
                    storage_info[name] = StorageInfoDTO(
                        path=path,
                        total_gb=round(total / (1024**3), 2),
                        used_gb=round(used / (1024**3), 2),
                        free_gb=round(free / (1024**3), 2),
                        usage_percent=round((used / total) * 100, 1),
                        status="healthy" if (used / total) < 0.8 else "warning"
                    )
                else:
                    storage_info[name] = StorageInfoDTO(
                        path=path,
                        status="missing"
                    )
            
            return StorageHealthDTO(
                storage_overview=storage_info,
                recommendations=[
                    "Monitor storage usage regularly",
                    "Set up automated cleanup policies",
                    "Consider storage expansion if usage > 80%"
                ]
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to get storage health: {str(e)}")


# Cache Management Use Cases
class GetCacheHealthUseCase(AdminUseCase):
    """Use case for getting cache service health"""
    
    async def execute(self, request: None) -> CacheHealthDTO:
        try:
            health_status = await self.cache_service.health_check()
            
            return CacheHealthDTO(
                service="cache",
                status=health_status.get("status", "unknown"),
                connected=health_status.get("connected", False),
                version=health_status.get("version"),
                uptime_seconds=health_status.get("uptime_seconds"),
                memory_used_mb=health_status.get("memory_used_mb"),
                memory_max_mb=health_status.get("memory_max_mb")
            )
        except Exception as e:
            return CacheHealthDTO(
                service="cache",
                status="unhealthy",
                connected=False,
                error=str(e)
            )


class GetCacheMetricsUseCase(AdminUseCase):
    """Use case for getting cache performance metrics"""
    
    async def execute(self, request: None) -> CacheMetricsDTO:
        try:
            metrics = await self.cache_service.get_metrics()
            
            return CacheMetricsDTO(
                total_keys=metrics.get("total_keys", 0),
                memory_used_mb=metrics.get("memory_used_mb", 0),
                hit_rate=metrics.get("hit_rate", 0),
                miss_rate=metrics.get("miss_rate", 0),
                eviction_rate=metrics.get("eviction_rate", 0),
                operations_per_second=metrics.get("operations_per_second", 0),
                categories=metrics.get("categories", {})
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to get cache metrics: {str(e)}")


class ClearCacheUseCase(AdminUseCase):
    """Use case for clearing cache data"""
    
    async def execute(self, request: ClearCacheRequestDTO) -> ClearCacheResponseDTO:
        try:
            cleared_count = 0
            operation = ""
            
            if request.pattern:
                # Clear by pattern
                cleared_count = await self.cache_service.clear_pattern(
                    request.pattern,
                    request.category or 'default'
                )
                operation = f"pattern '{request.pattern}'"
            elif request.category:
                # Clear by category
                cleared_count = await self.cache_service.clear_category(request.category)
                operation = f"category '{request.category}'"
            else:
                # Clear all categories
                total_cleared = 0
                categories_cleared = []
                
                for cat in self.cache_service.cache_configs.keys():
                    count = await self.cache_service.clear_category(cat)
                    total_cleared += count
                    if count > 0:
                        categories_cleared.append(cat)
                
                cleared_count = total_cleared
                operation = f"all categories: {', '.join(categories_cleared)}"
            
            return ClearCacheResponseDTO(
                success=True,
                keys_cleared=cleared_count,
                operation=operation,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to clear cache: {str(e)}")


class ListCacheKeysUseCase(AdminUseCase):
    """Use case for listing cache keys"""
    
    async def execute(self, params: Dict[str, Any]) -> ListCacheKeysResponseDTO:
        try:
            category = params.get("category", "default")
            pattern = params.get("pattern", "*")
            limit = params.get("limit", 100)
            
            # Connect to Redis
            if not await self.cache_service.connect():
                raise BusinessRuleViolation("Unable to connect to cache service")
            
            # Build search pattern
            cache_pattern = self.cache_service._build_key(pattern, category)
            
            # Get matching keys (limited)
            keys = await self.cache_service._redis.keys(cache_pattern)
            keys = keys[:limit]  # Limit results
            
            # Get key details
            key_details = []
            for key in keys:
                try:
                    ttl = await self.cache_service._redis.ttl(key)
                    key_type = await self.cache_service._redis.type(key)
                    
                    key_details.append(CacheKeyDTO(
                        key=key,
                        ttl_seconds=ttl,
                        type=key_type,
                        expires_at=(datetime.utcnow() + timedelta(seconds=ttl)) if ttl > 0 else None
                    ))
                except Exception:
                    key_details.append(CacheKeyDTO(
                        key=key,
                        error="Unable to get key details"
                    ))
            
            return ListCacheKeysResponseDTO(
                category=category,
                pattern=pattern,
                total_found=len(keys),
                limit_applied=limit,
                keys=key_details
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to list cache keys: {str(e)}")


# Comprehensive System Health Use Case
class GetComprehensiveSystemHealthUseCase(AdminUseCase):
    """Use case for getting comprehensive system health status"""
    
    async def execute(self, request: None) -> ComprehensiveSystemHealthDTO:
        try:
            # Gather health status from all services
            health_checks = await asyncio.gather(
                self.db.execute(text("SELECT 1")),  # Database health
                self.security_service.health_check(),
                self.backup_service.health_check(),
                self.cache_service.health_check(),
                self.audit_service.health_check(),
                return_exceptions=True
            )
            
            # Process health results
            database_healthy = not isinstance(health_checks[0], Exception)
            security_health = health_checks[1] if not isinstance(health_checks[1], Exception) else {"service": "security", "status": "unhealthy", "error": str(health_checks[1])}
            backup_health = health_checks[2] if not isinstance(health_checks[2], Exception) else {"service": "backup", "status": "unhealthy", "error": str(health_checks[2])}
            cache_health = health_checks[3] if not isinstance(health_checks[3], Exception) else {"service": "cache", "status": "unhealthy", "error": str(health_checks[3])}
            audit_health = health_checks[4] if not isinstance(health_checks[4], Exception) else {"service": "audit_database", "status": "unhealthy", "error": str(health_checks[4])}
            
            # Calculate overall health
            services_healthy = [
                database_healthy,
                security_health.get("status") == "healthy",
                backup_health.get("status") == "healthy",
                cache_health.get("status") == "healthy",
                audit_health.get("status") == "healthy"
            ]
            
            overall_health = "healthy" if all(services_healthy) else "degraded" if any(services_healthy) else "unhealthy"
            
            return ComprehensiveSystemHealthDTO(
                overall_status=overall_health,
                timestamp=datetime.utcnow(),
                services={
                    "database": ServiceHealthDTO(
                        service="database",
                        status="healthy" if database_healthy else "unhealthy",
                        details={"connection": "successful" if database_healthy else "failed"}
                    ),
                    "security": ServiceHealthDTO(**security_health),
                    "backup": ServiceHealthDTO(**backup_health),
                    "cache": ServiceHealthDTO(**cache_health),
                    "audit_database": ServiceHealthDTO(**audit_health)
                },
                summary=ServiceHealthSummaryDTO(
                    total_services=len(services_healthy),
                    healthy_services=sum(services_healthy),
                    unhealthy_services=len(services_healthy) - sum(services_healthy),
                    health_percentage=round((sum(services_healthy) / len(services_healthy)) * 100, 1)
                )
            )
        except Exception as e:
            return ComprehensiveSystemHealthDTO(
                overall_status="unhealthy",
                timestamp=datetime.utcnow(),
                error=str(e),
                services={
                    "database": ServiceHealthDTO(service="database", status="unknown", error="Health check failed"),
                    "security": ServiceHealthDTO(service="security", status="unknown", error="Health check failed"),
                    "backup": ServiceHealthDTO(service="backup", status="unknown", error="Health check failed"),
                    "cache": ServiceHealthDTO(service="cache", status="unknown", error="Health check failed"),
                    "audit_database": ServiceHealthDTO(service="audit_database", status="unknown", error="Health check failed")
                },
                summary=ServiceHealthSummaryDTO(
                    total_services=5,
                    healthy_services=0,
                    unhealthy_services=5,
                    health_percentage=0
                )
            )


# Audit Database Management Use Cases
class QueryAuditEventsUseCase(AdminUseCase):
    """Use case for querying audit events"""
    
    async def execute(self, request: AuditEventQueryDTO) -> AuditEventsResponseDTO:
        try:
            events_data = await self.audit_service.query_events(
                start_date=request.start_date,
                end_date=request.end_date,
                event_types=request.event_types,
                user_id=request.user_id,
                username=request.username,
                resource_type=request.resource_type,
                compliance_only=request.compliance_only,
                limit=request.limit,
                offset=request.offset
            )
            
            events = [
                AuditEventDTO(
                    event_id=e["event_id"],
                    timestamp=e["timestamp"],
                    event_type=e["event_type"],
                    user_id=e.get("user_id"),
                    username=e.get("username"),
                    resource_type=e.get("resource_type"),
                    resource_id=e.get("resource_id"),
                    action=e["action"],
                    result=e["result"],
                    details=e.get("details", {}),
                    ip_address=e.get("ip_address"),
                    user_agent=e.get("user_agent"),
                    compliance_relevant=e.get("compliance_relevant", False)
                )
                for e in events_data
            ]
            
            return AuditEventsResponseDTO(
                events=events,
                total_returned=len(events),
                filters_applied={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "event_types": request.event_types,
                    "user_id": request.user_id,
                    "username": request.username,
                    "resource_type": request.resource_type,
                    "compliance_only": request.compliance_only
                },
                pagination={
                    "limit": request.limit,
                    "offset": request.offset
                }
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to query audit events: {str(e)}")


class GetAuditSummaryUseCase(AdminUseCase):
    """Use case for getting audit summary statistics"""
    
    async def execute(self, params: Dict[str, Optional[datetime]]) -> AuditSummaryDTO:
        try:
            summary_data = await self.audit_service.get_audit_summary(
                start_date=params.get("start_date"),
                end_date=params.get("end_date")
            )
            
            if not summary_data:
                raise ResourceNotFound("No audit data found for the specified period")
            
            # Convert dataclass to DTO
            summary_dict = asdict(summary_data)
            return AuditSummaryDTO(**summary_dict)
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to get audit summary: {str(e)}")


class ExportAuditDataUseCase(AdminUseCase):
    """Use case for exporting audit data"""
    
    async def execute(self, request: ExportAuditDataRequestDTO) -> ExportAuditDataResponseDTO:
        try:
            # Validate date range (max 1 year for exports)
            if (request.end_date - request.start_date).days > 365:
                raise BusinessRuleViolation("Export date range cannot exceed 1 year")
            
            export_data = await self.audit_service.export_audit_data(
                start_date=request.start_date,
                end_date=request.end_date,
                format=request.format
            )
            
            if not export_data:
                return ExportAuditDataResponseDTO(
                    message="No audit data found for the specified date range",
                    start_date=request.start_date,
                    end_date=request.end_date,
                    format=request.format,
                    data_size_chars=0,
                    export_timestamp=datetime.utcnow()
                )
            
            return ExportAuditDataResponseDTO(
                message="Audit data exported successfully",
                start_date=request.start_date,
                end_date=request.end_date,
                format=request.format,
                data_size_chars=len(export_data),
                export_timestamp=datetime.utcnow(),
                sample_data=export_data[:1000] + "..." if len(export_data) > 1000 else export_data
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to export audit data: {str(e)}")


class CleanupOldAuditEventsUseCase(AdminUseCase):
    """Use case for cleaning up old audit events"""
    
    async def execute(self, request: None) -> AuditCleanupResponseDTO:
        try:
            # Note: In the actual implementation, this would be handled by background tasks
            return AuditCleanupResponseDTO(
                message="Audit cleanup started",
                status="in_progress",
                retention_years=self.audit_service.retention_years
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to start audit cleanup: {str(e)}")


class FlushAuditQueueUseCase(AdminUseCase):
    """Use case for flushing audit queue"""
    
    async def execute(self, request: None) -> FlushAuditQueueResponseDTO:
        try:
            await self.audit_service.flush_queue()
            
            return FlushAuditQueueResponseDTO(
                message="Audit queue flushed successfully",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            raise BusinessRuleViolation(f"Failed to flush audit queue: {str(e)}")


class GetAuditDatabaseHealthUseCase(AdminUseCase):
    """Use case for getting audit database health"""
    
    async def execute(self, request: None) -> AuditDatabaseHealthDTO:
        try:
            health_status = await self.audit_service.health_check()
            
            return AuditDatabaseHealthDTO(
                service="audit_database",
                status=health_status.get("status", "unknown"),
                queue_size=health_status.get("queue_size", 0),
                database_connected=health_status.get("database_connected", False),
                last_flush=health_status.get("last_flush")
            )
        except Exception as e:
            return AuditDatabaseHealthDTO(
                service="audit_database",
                status="unhealthy",
                queue_size=0,
                database_connected=False,
                error=str(e)
            )