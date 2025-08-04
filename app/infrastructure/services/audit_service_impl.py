"""Implementation of AuditService"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.application.interfaces.services import AuditService
from app.models import AuditLog


class AuditServiceImpl(AuditService):
    """Implementation of audit service using database"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log an audit action"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        
        self.session.add(audit_log)
        await self.session.commit()
    
    async def log_data_change(
        self,
        user_id: int,
        entity_type: str,
        entity_id: int,
        operation: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a data change"""
        details = {
            "operation": operation,
            "old_values": old_values or {},
            "new_values": new_values or {}
        }
        
        await self.log_action(
            user_id=user_id,
            action=f"DATA_CHANGE_{operation.upper()}",
            resource_type=entity_type,
            resource_id=entity_id,
            details=details
        )
    
    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log a security event"""
        security_details = {
            "event_type": event_type,
            "severity": severity,
            **(details or {})
        }
        
        audit_log = AuditLog(
            user_id=user_id,
            action=f"SECURITY_{event_type.upper()}",
            resource_type="security",
            details=security_details,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        
        self.session.add(audit_log)
        await self.session.commit()
    
    async def get_audit_trail(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail with filters"""
        query = select(AuditLog)
        
        # Build filters
        filters = []
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        if start_date:
            filters.append(AuditLog.timestamp >= start_date)
        if end_date:
            filters.append(AuditLog.timestamp <= end_date)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Order by timestamp descending and limit
        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)
        
        result = await self.session.execute(query)
        audit_logs = result.scalars().all()
        
        return [self._to_dict(log) for log in audit_logs]
    
    def _to_dict(self, audit_log: AuditLog) -> Dict[str, Any]:
        """Convert audit log to dictionary"""
        return {
            "audit_id": audit_log.audit_id,
            "user_id": audit_log.user_id,
            "action": audit_log.action,
            "resource_type": audit_log.resource_type,
            "resource_id": audit_log.resource_id,
            "details": audit_log.details,
            "ip_address": audit_log.ip_address,
            "timestamp": audit_log.timestamp
        }