"""
DTOs for Admin API endpoints
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Security Management DTOs
class KeyRotationResultDTO(BaseModel):
    """Result of encryption key rotation operation"""
    status: str
    keys_rotated: int
    timestamp: datetime
    details: Dict[str, Any]


class SecurityStatusDTO(BaseModel):
    """Security service status information"""
    service: str
    status: str
    encryption_enabled: bool
    key_rotation_enabled: bool
    last_key_rotation: Optional[datetime]
    metrics: Dict[str, Any]


class PasswordValidationRequestDTO(BaseModel):
    """Request for password validation"""
    password: str
    user_id: Optional[int] = None


class PasswordValidationResultDTO(BaseModel):
    """Result of password validation"""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    strength: str
    requirements_met: Dict[str, bool]


class SecurityReportDTO(BaseModel):
    """Security metrics report"""
    time_period_days: int
    report_date: datetime
    metrics: Dict[str, Any]
    recommendations: List[str]
    issues_found: int


# Backup Management DTOs
class CreateBackupRequestDTO(BaseModel):
    """Request to create a backup"""
    category: str = Field(default="all", description="Backup category: all, files, security, config, logs")
    backup_name: Optional[str] = None


class BackupOperationResponseDTO(BaseModel):
    """Response for backup operations"""
    message: str
    status: str
    category: Optional[str] = None
    backup_name: Optional[str] = None
    operation: Optional[str] = None


class BackupInfoDTO(BaseModel):
    """Information about a single backup"""
    backup_name: str
    created_at: datetime
    size_mb: float
    category: str
    status: str
    path: str


class BackupListResponseDTO(BaseModel):
    """Response containing list of backups"""
    backups: List[BackupInfoDTO]
    total_count: int
    total_size_mb: float


class RestoreBackupRequestDTO(BaseModel):
    """Request to restore from a backup"""
    backup_name: str
    categories: Optional[List[str]] = None
    target_path: Optional[str] = None


class BackupStatusDTO(BaseModel):
    """Backup service status"""
    service: str
    status: str
    backup_enabled: bool
    last_backup: Optional[datetime]
    next_scheduled_backup: Optional[datetime]
    storage_used_mb: float
    storage_available_mb: float


# System Health DTOs
class ServiceHealthDTO(BaseModel):
    """Health status of a single service"""
    service: str
    status: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SystemHealthDTO(BaseModel):
    """Comprehensive system health status"""
    system: Dict[str, Any]
    services: Dict[str, ServiceHealthDTO]
    recommendations: List[str]


class StorageInfoDTO(BaseModel):
    """Storage information for a path"""
    path: str
    total_gb: Optional[float] = None
    used_gb: Optional[float] = None
    free_gb: Optional[float] = None
    usage_percent: Optional[float] = None
    status: str


class StorageHealthDTO(BaseModel):
    """Storage health metrics"""
    storage_overview: Dict[str, StorageInfoDTO]
    recommendations: List[str]


# Cache Management DTOs
class CacheHealthDTO(BaseModel):
    """Cache service health status"""
    service: str
    status: str
    connected: bool
    version: Optional[str] = None
    uptime_seconds: Optional[int] = None
    memory_used_mb: Optional[float] = None
    memory_max_mb: Optional[float] = None


class CacheMetricsDTO(BaseModel):
    """Cache performance metrics"""
    total_keys: int
    memory_used_mb: float
    hit_rate: float
    miss_rate: float
    eviction_rate: float
    operations_per_second: float
    categories: Dict[str, Dict[str, Any]]


class ClearCacheRequestDTO(BaseModel):
    """Request to clear cache"""
    category: Optional[str] = None
    pattern: Optional[str] = None


class ClearCacheResponseDTO(BaseModel):
    """Response from cache clearing operation"""
    success: bool
    keys_cleared: int
    operation: str
    timestamp: datetime


class CacheKeyDTO(BaseModel):
    """Information about a cache key"""
    key: str
    ttl_seconds: Optional[int] = None
    type: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


class ListCacheKeysResponseDTO(BaseModel):
    """Response containing list of cache keys"""
    category: str
    pattern: str
    total_found: int
    limit_applied: int
    keys: List[CacheKeyDTO]


# Comprehensive System Health DTOs
class ServiceHealthSummaryDTO(BaseModel):
    """Summary of service health across all services"""
    total_services: int
    healthy_services: int
    unhealthy_services: int
    health_percentage: float


class ComprehensiveSystemHealthDTO(BaseModel):
    """Comprehensive system health including all services"""
    overall_status: str
    timestamp: datetime
    services: Dict[str, ServiceHealthDTO]
    summary: ServiceHealthSummaryDTO
    error: Optional[str] = None


# Audit Database Management DTOs
class AuditEventQueryDTO(BaseModel):
    """Query parameters for audit events"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[str]] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    resource_type: Optional[str] = None
    compliance_only: bool = False
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditEventDTO(BaseModel):
    """Audit event information"""
    event_id: str
    timestamp: datetime
    event_type: str
    user_id: Optional[int]
    username: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    result: str
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    compliance_relevant: bool


class AuditEventsResponseDTO(BaseModel):
    """Response containing audit events"""
    events: List[AuditEventDTO]
    total_returned: int
    filters_applied: Dict[str, Any]
    pagination: Dict[str, int]


class AuditSummaryDTO(BaseModel):
    """Summary statistics for audit events"""
    start_date: datetime
    end_date: datetime
    total_events: int
    unique_users: int
    event_types: Dict[str, int]
    resource_types: Dict[str, int]
    compliance_events: int
    failed_operations: int
    security_events: int
    top_users: List[Dict[str, Any]]
    hourly_distribution: Dict[str, int]


class ExportAuditDataRequestDTO(BaseModel):
    """Request to export audit data"""
    start_date: datetime
    end_date: datetime
    format: str = Field(default="json", pattern="^(json|csv)$")


class ExportAuditDataResponseDTO(BaseModel):
    """Response from audit data export"""
    message: str
    start_date: datetime
    end_date: datetime
    format: str
    data_size_chars: int
    export_timestamp: datetime
    sample_data: Optional[str] = None


class AuditCleanupResponseDTO(BaseModel):
    """Response from audit cleanup operation"""
    message: str
    status: str
    retention_years: int


class FlushAuditQueueResponseDTO(BaseModel):
    """Response from flushing audit queue"""
    message: str
    timestamp: datetime


class AuditDatabaseHealthDTO(BaseModel):
    """Audit database health status"""
    service: str
    status: str
    queue_size: int
    database_connected: bool
    last_flush: Optional[datetime]
    error: Optional[str] = None