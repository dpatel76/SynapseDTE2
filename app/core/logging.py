"""
Structured logging configuration using structlog
"""

import structlog
import logging
import sys
from typing import Any, Dict
from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


class AuditLogger:
    """Audit logger for tracking business operations"""
    
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log_user_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int = None,
        details: Dict[str, Any] = None
    ) -> None:
        """Log user actions for audit trail"""
        self.logger.info(
            "User action",
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {}
        )
    
    def log_workflow_transition(
        self,
        cycle_id: int,
        report_id: int,
        phase: str,
        from_status: str,
        to_status: str,
        user_id: int,
        details: Dict[str, Any] = None
    ) -> None:
        """Log workflow phase transitions"""
        self.logger.info(
            "Workflow transition",
            cycle_id=cycle_id,
            report_id=report_id,
            phase=phase,
            from_status=from_status,
            to_status=to_status,
            user_id=user_id,
            details=details or {}
        )
    
    def log_llm_operation(
        self,
        provider: str,
        operation: str,
        user_id: int,
        cycle_id: int = None,
        report_id: int = None,
        tokens_used: int = None,
        execution_time_ms: int = None,
        success: bool = True,
        error: str = None
    ) -> None:
        """Log LLM operations"""
        self.logger.info(
            "LLM operation",
            provider=provider,
            operation=operation,
            user_id=user_id,
            cycle_id=cycle_id,
            report_id=report_id,
            tokens_used=tokens_used,
            execution_time_ms=execution_time_ms,
            success=success,
            error=error
        )
    
    def log_file_operation(
        self,
        user_id: int,
        operation: str,
        filename: str,
        file_size: int = None,
        file_type: str = None,
        cycle_id: int = None,
        report_id: int = None,
        success: bool = True,
        error: str = None
    ) -> None:
        """Log file operations"""
        self.logger.info(
            "File operation",
            user_id=user_id,
            operation=operation,
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            cycle_id=cycle_id,
            report_id=report_id,
            success=success,
            error=error
        )
    
    def log_sla_event(
        self,
        event_type: str,
        cycle_id: int,
        report_id: int,
        phase: str,
        assigned_user_id: int,
        sla_hours: int,
        hours_elapsed: float,
        is_breach: bool = False
    ) -> None:
        """Log SLA events"""
        self.logger.warning(
            "SLA event",
            event_type=event_type,
            cycle_id=cycle_id,
            report_id=report_id,
            phase=phase,
            assigned_user_id=assigned_user_id,
            sla_hours=sla_hours,
            hours_elapsed=hours_elapsed,
            is_breach=is_breach
        )


# Global audit logger instance
audit_logger = AuditLogger() 