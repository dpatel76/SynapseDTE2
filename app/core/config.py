"""
Application configuration using Pydantic settings
"""

from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "SynapseDT - End-to-End Data Testing System"
    app_version: str = "3.2.0"
    debug: bool = False
    api_v1_str: str = "/api/v1"
    
    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5433/synapse_dt"
    database_host: str = "localhost"
    database_port: int = 5433
    database_name: str = "synapse_dt"
    database_user: str = "synapse_user"
    database_password: str = "synapse_password"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    
    # File Storage
    upload_dir: str = "./uploads"
    max_file_size: int = 20971520  # 20MB in bytes
    allowed_file_types: List[str] = ["pdf", "png", "jpg", "jpeg", "csv", "xlsx", "xls"]
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "your-email@gmail.com"
    smtp_password: str = "your-password"
    smtp_from_email: str = "noreply@synapsedt.com"
    smtp_from_name: str = "SynapseDT System"
    
    # Temporal
    TEMPORAL_HOST: Optional[str] = None
    TEMPORAL_NAMESPACE: Optional[str] = None
    
    # Redis/Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # LLM Configuration
    anthropic_api_key: Optional[str] = None
    claude_model: str = "claude-3-5-sonnet-20241022"
    claude_max_tokens: int = 4000
    
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_max_tokens: int = 4000
    
    default_llm_provider: str = "claude"
    
    # Advanced LLM Configuration - Enhanced from reference implementation
    # Temperature and token settings
    llm_temperature: float = 0.0
    llm_max_tokens: int = 32000
    llm_max_retries: int = 3
    llm_retry_delay: float = 1.0
    
    # Batch Configuration for Token Limit Optimization
    gemini_batch_size: int = 50
    claude_batch_size: int = 15
    claude_smart_batch_size: int = 8
    
    # Hybrid Analysis Configuration
    enable_hybrid_analysis: bool = True
    extraction_model: str = "gemini-2.0-flash"  # Fast extraction
    analysis_model: str = "claude-3-5-sonnet"  # Deep analysis
    min_confidence_for_gemini: float = 7.0
    critical_attributes_use_claude: bool = True
    
    # Claude-specific Optimization Settings
    claude_comprehensive_temperature: float = 0.1
    claude_comprehensive_max_tokens: int = 8192
    claude_anti_truncation_mode: bool = True
    claude_priority_batching: bool = True
    
    # Document Processing Optimization
    max_chunk_size: int = 3000
    chunk_overlap: int = 300
    max_chunks_per_batch: int = 20
    api_delay: float = 0.1
    max_concurrent_calls: int = 5
    
    # LLM Audit and Monitoring
    llm_audit_enabled: bool = True
    llm_performance_tracking: bool = True
    llm_cost_tracking: bool = True
    
    # SLA Configuration (in hours)
    default_sla_hours: int = 24
    cdo_assignment_sla: int = 24
    report_owner_approval_sla: int = 24
    data_owner_submission_sla: int = 24
    
    # Audit Configuration
    audit_log_retention_days: int = 2555  # 7 years
    llm_audit_retention_days: int = 1095  # 3 years
    
    # Security Configuration
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    
    # RBAC Configuration
    use_rbac: bool = True  # Feature flag for RBAC system
    rbac_fallback_to_roles: bool = True  # Fallback to role-based checks if RBAC fails
    rbac_cache_ttl: int = 300  # Cache TTL in seconds for permission checks
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Performance
    max_concurrent_users: int = 100
    api_rate_limit: int = 1000  # requests per minute
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Backup
    backup_enabled: bool = True
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    backup_retention_days: int = 30
    
    # Temporal Configuration
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "synapse-workflow-queue"
    temporal_worker_enabled: bool = True  # Set to True to enable worker
    temporal_activity_timeout: int = 300  # 5 minutes
    temporal_workflow_timeout: int = 86400  # 24 hours
    
    # Dynamic Workflow Configuration
    use_dynamic_workflows: bool = True  # Enable dynamic workflow system
    workflow_version: str = "v2"  # Use v2 for dynamic workflows, v1 for legacy
    dynamic_activity_retry_enabled: bool = True  # Enable retry policies from DB
    dynamic_activity_timeout_enabled: bool = True  # Enable timeout from DB
    parallel_activity_max_concurrent: int = 10  # Max concurrent parallel activities
    workflow_activity_signal_timeout: int = 300  # 5 min timeout for signals
    
    # Activity Handler Configuration
    activity_handler_package: str = "app.temporal.activities.handlers"
    fallback_handler: str = "AutomatedActivityHandler"
    manual_activity_handler: str = "ManualActivityHandler"
    
    # Workflow Feature Flags
    enable_activity_dependencies: bool = True  # Check dependencies before execution
    enable_conditional_activities: bool = True  # Support conditional expressions
    enable_activity_compensation: bool = True  # Enable compensation on failure
    track_activity_metrics: bool = True  # Track execution metrics
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("allowed_methods", mode="before")
    @classmethod
    def assemble_cors_methods(cls, v):
        """Parse CORS methods from string or list"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("allowed_headers", mode="before")
    @classmethod
    def assemble_cors_headers(cls, v):
        """Parse CORS headers from string or list"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def assemble_file_types(cls, v):
        """Parse allowed file types from string or list"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("upload_dir")
    @classmethod
    def create_upload_dir(cls, v):
        """Ensure upload directory exists"""
        os.makedirs(v, exist_ok=True)
        return v
    
    @field_validator("default_llm_provider")
    @classmethod
    def validate_llm_provider(cls, v):
        """Validate LLM provider"""
        if v not in ["claude", "gemini"]:
            raise ValueError("default_llm_provider must be 'claude' or 'gemini'")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings() 