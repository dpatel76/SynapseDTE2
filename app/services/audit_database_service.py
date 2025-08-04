"""
Separate Audit Database Service
Provides isolated audit logging for compliance requirements with 7-year retention
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Index, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Separate audit database base
AuditBase = declarative_base()


class AuditEventType(Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PASSWORD_CHANGED = "password_changed"
    ROLE_CHANGED = "role_changed"
    
    CYCLE_CREATED = "cycle_created"
    CYCLE_UPDATED = "cycle_updated"
    CYCLE_DELETED = "cycle_deleted"
    CYCLE_STARTED = "cycle_started"
    CYCLE_COMPLETED = "cycle_completed"
    
    PHASE_TRANSITION = "phase_transition"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    
    TEST_EXECUTED = "test_executed"
    OBSERVATION_CREATED = "observation_created"
    OBSERVATION_UPDATED = "observation_updated"
    
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    SECURITY_EVENT = "security_event"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    
    API_ACCESS = "api_access"
    ADMIN_ACTION = "admin_action"


class AuditEvent(AuditBase):
    """Audit event model for separate audit database"""
    __tablename__ = "audit_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)
    event_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # User and session information
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(255), nullable=True, index=True)
    user_role = Column(String(50), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Request information
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_url = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True, index=True)
    
    # Event details
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    action_performed = Column(String(100), nullable=True)
    event_description = Column(Text, nullable=True)
    
    # Additional data
    event_metadata = Column(JSON, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Status and compliance
    status = Column(String(20), nullable=False, default="success")  # success, failure, warning
    compliance_relevant = Column(Boolean, nullable=False, default=True)
    retention_years = Column(Integer, nullable=False, default=7)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_audit_events_user_timestamp', 'user_id', 'event_timestamp'),
        Index('ix_audit_events_type_timestamp', 'event_type', 'event_timestamp'),
        Index('ix_audit_events_compliance_timestamp', 'compliance_relevant', 'event_timestamp'),
        Index('ix_audit_events_resource', 'resource_type', 'resource_id'),
    )


@dataclass
class AuditSummary:
    """Summary of audit events"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_user: Dict[str, int]
    events_by_status: Dict[str, int]
    compliance_events: int
    date_range: Dict[str, str]
    retention_status: Dict[str, int]


class AuditDatabaseService:
    """Service for managing separate audit database"""
    
    def __init__(self):
        # Separate audit database configuration
        self.audit_db_url = getattr(settings, 'audit_database_url', None)
        if not self.audit_db_url:
            # Default to separate audit database
            self.audit_db_url = getattr(settings, 'database_url', '').replace('/synapse', '/synapse_audit')
        
        self.max_connections = getattr(settings, 'audit_db_max_connections', 10)
        self.connection_timeout = getattr(settings, 'audit_db_timeout_seconds', 30)
        self.batch_size = getattr(settings, 'audit_batch_size', 100)
        self.retention_years = getattr(settings, 'audit_retention_years', 7)
        
        self._engine = None
        self._session_factory = None
        self._connected = False
        
        # Event queue for batch processing
        self._event_queue = []
        self._queue_lock = asyncio.Lock()
        
        logger.info("Audit database service initialized")
    
    async def connect(self) -> bool:
        """Connect to audit database"""
        try:
            if self._connected and self._engine:
                return True
            
            # Create audit database engine
            self._engine = create_async_engine(
                self.audit_db_url,
                pool_size=self.max_connections,
                max_overflow=self.max_connections * 2,
                pool_timeout=self.connection_timeout,
                pool_recycle=3600,  # 1 hour
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self._engine.begin() as conn:
                await conn.run_sync(AuditBase.metadata.create_all)
            
            self._connected = True
            logger.info("Successfully connected to audit database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to audit database: {str(e)}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from audit database"""
        try:
            if self._engine:
                await self._engine.dispose()
                self._connected = False
                logger.info("Disconnected from audit database")
        except Exception as e:
            logger.error(f"Error disconnecting from audit database: {str(e)}")
    
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_role: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_url: Optional[str] = None,
        request_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action_performed: Optional[str] = None,
        event_description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        status: str = "success",
        compliance_relevant: bool = True,
        batch: bool = True
    ) -> bool:
        """Log an audit event"""
        try:
            audit_event = {
                "event_type": event_type,
                "event_timestamp": datetime.utcnow(),
                "user_id": user_id,
                "username": username,
                "user_role": user_role,
                "session_id": session_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_method": request_method,
                "request_url": request_url,
                "request_id": request_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action_performed": action_performed,
                "event_description": event_description,
                "event_metadata": metadata,
                "old_values": old_values,
                "new_values": new_values,
                "status": status,
                "compliance_relevant": compliance_relevant,
                "retention_years": self.retention_years
            }
            
            if batch:
                # Add to queue for batch processing
                async with self._queue_lock:
                    self._event_queue.append(audit_event)
                    
                    # Process batch if queue is full
                    if len(self._event_queue) >= self.batch_size:
                        await self._flush_event_queue()
                
                return True
            else:
                # Write immediately
                return await self._write_events([audit_event])
                
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            return False
    
    async def _write_events(self, events: List[Dict[str, Any]]) -> bool:
        """Write events to audit database"""
        if not await self.connect():
            return False
        
        try:
            async with self._session_factory() as session:
                audit_objects = [AuditEvent(**event) for event in events]
                session.add_all(audit_objects)
                await session.commit()
                
                logger.debug(f"Successfully wrote {len(events)} audit events")
                return True
                
        except Exception as e:
            logger.error(f"Failed to write audit events: {str(e)}")
            return False
    
    async def _flush_event_queue(self):
        """Flush the event queue to database"""
        if not self._event_queue:
            return
        
        events_to_write = self._event_queue.copy()
        self._event_queue.clear()
        
        await self._write_events(events_to_write)
    
    async def flush_queue(self):
        """Manually flush the event queue"""
        async with self._queue_lock:
            await self._flush_event_queue()
    
    async def query_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        compliance_only: bool = False,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query audit events with filters"""
        if not await self.connect():
            return []
        
        try:
            async with self._session_factory() as session:
                # Build query
                query = session.query(AuditEvent)
                
                # Apply filters
                if start_date:
                    query = query.filter(AuditEvent.event_timestamp >= start_date)
                if end_date:
                    query = query.filter(AuditEvent.event_timestamp <= end_date)
                if event_types:
                    query = query.filter(AuditEvent.event_type.in_(event_types))
                if user_id:
                    query = query.filter(AuditEvent.user_id == user_id)
                if username:
                    query = query.filter(AuditEvent.username == username)
                if resource_type:
                    query = query.filter(AuditEvent.resource_type == resource_type)
                if resource_id:
                    query = query.filter(AuditEvent.resource_id == resource_id)
                if status:
                    query = query.filter(AuditEvent.status == status)
                if compliance_only:
                    query = query.filter(AuditEvent.compliance_relevant == True)
                
                # Order and paginate
                query = query.order_by(AuditEvent.event_timestamp.desc())
                query = query.offset(offset).limit(limit)
                
                # Execute query
                result = await session.execute(query)
                events = result.scalars().all()
                
                # Convert to dictionaries
                return [
                    {
                        "id": str(event.id),
                        "event_type": event.event_type,
                        "event_timestamp": event.event_timestamp.isoformat(),
                        "user_id": event.user_id,
                        "username": event.username,
                        "user_role": event.user_role,
                        "session_id": event.session_id,
                        "ip_address": event.ip_address,
                        "user_agent": event.user_agent,
                        "request_method": event.request_method,
                        "request_url": event.request_url,
                        "request_id": event.request_id,
                        "resource_type": event.resource_type,
                        "resource_id": event.resource_id,
                        "action_performed": event.action_performed,
                        "event_description": event.event_description,
                        "event_metadata": event.event_metadata,
                        "old_values": event.old_values,
                        "new_values": event.new_values,
                        "status": event.status,
                        "compliance_relevant": event.compliance_relevant,
                        "retention_years": event.retention_years
                    }
                    for event in events
                ]
                
        except Exception as e:
            logger.error(f"Failed to query audit events: {str(e)}")
            return []
    
    async def get_audit_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[AuditSummary]:
        """Get audit summary statistics"""
        if not await self.connect():
            return None
        
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with self._session_factory() as session:
                # Total events
                total_query = session.query(func.count(AuditEvent.id)).filter(
                    AuditEvent.event_timestamp.between(start_date, end_date)
                )
                total_result = await session.execute(total_query)
                total_events = total_result.scalar()
                
                # Events by type
                type_query = session.query(
                    AuditEvent.event_type,
                    func.count(AuditEvent.id)
                ).filter(
                    AuditEvent.event_timestamp.between(start_date, end_date)
                ).group_by(AuditEvent.event_type)
                type_result = await session.execute(type_query)
                events_by_type = dict(type_result.fetchall())
                
                # Events by user
                user_query = session.query(
                    AuditEvent.username,
                    func.count(AuditEvent.id)
                ).filter(
                    AuditEvent.event_timestamp.between(start_date, end_date),
                    AuditEvent.username.is_not(None)
                ).group_by(AuditEvent.username).limit(10)
                user_result = await session.execute(user_query)
                events_by_user = dict(user_result.fetchall())
                
                # Events by status
                status_query = session.query(
                    AuditEvent.status,
                    func.count(AuditEvent.id)
                ).filter(
                    AuditEvent.event_timestamp.between(start_date, end_date)
                ).group_by(AuditEvent.status)
                status_result = await session.execute(status_query)
                events_by_status = dict(status_result.fetchall())
                
                # Compliance events
                compliance_query = session.query(func.count(AuditEvent.id)).filter(
                    AuditEvent.event_timestamp.between(start_date, end_date),
                    AuditEvent.compliance_relevant == True
                )
                compliance_result = await session.execute(compliance_query)
                compliance_events = compliance_result.scalar()
                
                # Retention status
                retention_cutoff = datetime.utcnow() - timedelta(days=365 * self.retention_years)
                old_events_query = session.query(func.count(AuditEvent.id)).filter(
                    AuditEvent.event_timestamp < retention_cutoff
                )
                old_events_result = await session.execute(old_events_query)
                old_events = old_events_result.scalar()
                
                return AuditSummary(
                    total_events=total_events,
                    events_by_type=events_by_type,
                    events_by_user=events_by_user,
                    events_by_status=events_by_status,
                    compliance_events=compliance_events,
                    date_range={
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    retention_status={
                        "total_events": total_events,
                        "events_past_retention": old_events
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to get audit summary: {str(e)}")
            return None
    
    async def cleanup_old_events(self) -> Dict[str, Any]:
        """Clean up events past retention period"""
        if not await self.connect():
            return {"error": "Database connection failed"}
        
        try:
            retention_cutoff = datetime.utcnow() - timedelta(days=365 * self.retention_years)
            
            async with self._session_factory() as session:
                # Count events to be deleted
                count_query = session.query(func.count(AuditEvent.id)).filter(
                    AuditEvent.event_timestamp < retention_cutoff
                )
                count_result = await session.execute(count_query)
                events_to_delete = count_result.scalar()
                
                if events_to_delete == 0:
                    return {
                        "message": "No events past retention period",
                        "events_deleted": 0,
                        "retention_cutoff": retention_cutoff.isoformat()
                    }
                
                # Delete old events in batches
                deleted_total = 0
                batch_size = 1000
                
                while True:
                    delete_query = session.query(AuditEvent).filter(
                        AuditEvent.event_timestamp < retention_cutoff
                    ).limit(batch_size)
                    
                    events_batch = await session.execute(delete_query)
                    events = events_batch.scalars().all()
                    
                    if not events:
                        break
                    
                    for event in events:
                        await session.delete(event)
                    
                    await session.commit()
                    deleted_total += len(events)
                    
                    logger.info(f"Deleted {len(events)} old audit events (total: {deleted_total})")
                
                return {
                    "message": "Old audit events cleaned up successfully",
                    "events_deleted": deleted_total,
                    "retention_cutoff": retention_cutoff.isoformat(),
                    "retention_years": self.retention_years
                }
                
        except Exception as e:
            logger.error(f"Failed to cleanup old audit events: {str(e)}")
            return {"error": str(e)}
    
    async def export_audit_data(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> Optional[str]:
        """Export audit data for compliance reporting"""
        events = await self.query_events(
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Large limit for export
        )
        
        if not events:
            return None
        
        try:
            if format.lower() == "json":
                import json
                return json.dumps(events, indent=2, default=str)
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                if events:
                    writer = csv.DictWriter(output, fieldnames=events[0].keys())
                    writer.writeheader()
                    writer.writerows(events)
                
                return output.getvalue()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to export audit data: {str(e)}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check audit database service health"""
        try:
            if not await self.connect():
                return {
                    "service": "audit_database",
                    "status": "unhealthy",
                    "error": "Unable to connect to audit database"
                }
            
            # Test database operations
            async with self._session_factory() as session:
                # Test simple query
                test_query = session.query(func.count(AuditEvent.id))
                result = await session.execute(test_query)
                total_events = result.scalar()
                
                # Check recent events
                recent_query = session.query(func.count(AuditEvent.id)).filter(
                    AuditEvent.event_timestamp >= datetime.utcnow() - timedelta(hours=24)
                )
                recent_result = await session.execute(recent_query)
                recent_events = recent_result.scalar()
            
            # Queue status
            queue_size = len(self._event_queue)
            
            return {
                "service": "audit_database",
                "status": "healthy",
                "database_connection": "active",
                "configuration": {
                    "retention_years": self.retention_years,
                    "batch_size": self.batch_size,
                    "max_connections": self.max_connections
                },
                "statistics": {
                    "total_events": total_events,
                    "events_last_24h": recent_events,
                    "queue_size": queue_size
                },
                "performance": {
                    "connection_pool_active": True,
                    "batch_processing": "enabled"
                }
            }
            
        except Exception as e:
            logger.error(f"Audit database health check failed: {str(e)}")
            return {
                "service": "audit_database",
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance
audit_db_service = AuditDatabaseService()


def get_audit_database_service() -> AuditDatabaseService:
    """Get the global audit database service instance"""
    return audit_db_service


# Convenience functions for common audit events
async def audit_user_action(
    action: str,
    user_id: int,
    username: str,
    user_role: str,
    details: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Audit a user action"""
    await audit_db_service.log_event(
        event_type=f"user_{action}",
        user_id=user_id,
        username=username,
        user_role=user_role,
        session_id=session_id,
        ip_address=ip_address,
        action_performed=action,
        event_metadata=details
    )


async def audit_data_access(
    resource_type: str,
    resource_id: str,
    action: str,
    user_id: int,
    username: str,
    details: Optional[Dict[str, Any]] = None
):
    """Audit data access events"""
    await audit_db_service.log_event(
        event_type="data_access",
        user_id=user_id,
        username=username,
        resource_type=resource_type,
        resource_id=resource_id,
        action_performed=action,
        event_metadata=details,
        compliance_relevant=True
    )


async def audit_system_event(
    event_type: str,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None
):
    """Audit system-level events"""
    await audit_db_service.log_event(
        event_type=event_type,
        user_id=user_id,
        event_description=description,
        event_metadata=details,
        compliance_relevant=True
    ) 