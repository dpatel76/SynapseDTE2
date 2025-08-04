"""
Notification Adapter Service
Provides parallel writes to both legacy notification tables and universal assignments
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# from app.models.data_owner import CDONotification  # Deprecated - using universal assignments
from app.models.request_info import DataProviderNotification
from app.models.universal_assignment import UniversalAssignment
from app.core.logging import get_logger

logger = get_logger(__name__)

class NotificationAdapter:
    """Adapter to write notifications to both legacy and universal systems"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_cdo_notification(
        self,
        cycle_id: int,
        report_id: int,
        lob_id: int,
        cdo_user_id: int,
        created_by: int,
        notification_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UniversalAssignment:
        """Create notification in both systems"""
        
        # 1. Legacy system deprecated - only using universal assignments
        # CDONotification has been deprecated
        
        # 2. Create in universal system (new)
        universal_assignment = UniversalAssignment(
            assignment_type="LOB Assignment",
            cycle_id=cycle_id,
            report_id=report_id,
            from_user_id=created_by,
            to_user_id=cdo_user_id,
            from_role="Data Executive",
            to_role="Data Executive",  # Updated from CDO
            title=f"LOB Assignment Review Required",
            description=notification_text,
            priority="High",
            status="Assigned",
            due_date=datetime.utcnow().date(),  # Add SLA logic here
            assignment_metadata={
                "lob_id": lob_id,
                "notification_type": "cdo_notification",
                "legacy_table": "cdo_notifications",
                **(metadata or {})
            },
            created_at=datetime.utcnow(),
            created_by=created_by
        )
        self.db.add(universal_assignment)
        
        await self.db.flush()  # Get IDs
        
        logger.info(
            f"Created universal assignment: {universal_assignment.assignment_id}"
        )
        
        return universal_assignment
    
    async def create_data_owner_notification(
        self,
        cycle_id: int,
        report_id: int,
        data_owner_id: int,
        created_by: int,
        notification_text: str,
        test_case_ids: Optional[list[int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[DataProviderNotification, UniversalAssignment]:
        """Create data owner notification in both systems"""
        
        # 1. Create in legacy system
        data_notification = DataProviderNotification(
            cycle_id=cycle_id,
            report_id=report_id,
            data_provider_id=data_owner_id,
            notification_text=notification_text,
            status="sent",
            created_at=datetime.utcnow(),
            created_by=created_by,
            test_case_ids=test_case_ids
        )
        self.db.add(data_notification)
        
        # 2. Create in universal system
        universal_assignment = UniversalAssignment(
            assignment_type="Information Request",
            cycle_id=cycle_id,
            report_id=report_id,
            from_user_id=created_by,
            to_user_id=data_owner_id,
            from_role="Test Manager",
            to_role="Data Owner",
            title="Information Request",
            description=custom_instructions or "Please provide data for the assigned attributes",
            priority="Medium",
            status="Assigned",
            due_date=datetime.utcnow().date(),  # Add SLA logic
            assignment_metadata={
                "phase_id": phase_id,
                "assigned_attributes": assigned_attributes,
                "sample_count": sample_count,
                "portal_access_url": portal_access_url,
                "notification_type": "data_owner_notification",
                "legacy_table": "data_owner_notifications",
                **(metadata or {})
            },
            created_at=datetime.utcnow(),
            created_by=created_by
        )
        self.db.add(universal_assignment)
        
        await self.db.flush()
        
        # Link them
        universal_assignment.assignment_metadata["legacy_notification_id"] = data_notification.notification_id
        data_notification.metadata = {"universal_assignment_id": universal_assignment.assignment_id}
        
        logger.info(
            f"Created parallel notifications - Data Owner: {data_notification.notification_id}, "
            f"Universal: {universal_assignment.assignment_id}"
        )
        
        return data_notification, universal_assignment
    
    async def update_cdo_notification_status(
        self,
        notification_id: int,
        new_status: str,
        updated_by: int
    ):
        """Update status in both systems"""
        
        # Get the CDO notification
        result = await self.db.execute(
            select(CDONotification).where(CDONotification.notification_id == notification_id)
        )
        cdo_notification = result.scalar_one_or_none()
        
        if not cdo_notification:
            return
        
        # Update legacy
        cdo_notification.status = new_status
        cdo_notification.updated_at = datetime.utcnow()
        
        if new_status == "acknowledged":
            cdo_notification.acknowledged_at = datetime.utcnow()
        elif new_status == "complete":
            cdo_notification.completed_at = datetime.utcnow()
        
        # Update universal if linked
        if cdo_notification.metadata and "universal_assignment_id" in cdo_notification.metadata:
            universal_id = cdo_notification.metadata["universal_assignment_id"]
            
            result = await self.db.execute(
                select(UniversalAssignment).where(
                    UniversalAssignment.assignment_id == universal_id
                )
            )
            universal_assignment = result.scalar_one_or_none()
            
            if universal_assignment:
                # Map status
                status_map = {
                    "sent": "Assigned",
                    "acknowledged": "Acknowledged", 
                    "in_progress": "In Progress",
                    "complete": "Completed",
                    "cancelled": "Cancelled"
                }
                
                universal_assignment.status = status_map.get(new_status, new_status)
                universal_assignment.updated_at = datetime.utcnow()
                universal_assignment.updated_by = updated_by
                
                if new_status == "acknowledged":
                    universal_assignment.acknowledged_at = datetime.utcnow()
                    universal_assignment.acknowledged_by = updated_by
                elif new_status == "complete":
                    universal_assignment.completed_at = datetime.utcnow()
                    universal_assignment.completed_by = updated_by
        
        logger.info(f"Updated notification status to {new_status} in both systems")
    
    async def migrate_historical_notifications(self):
        """One-time migration of historical data"""
        
        migrated_count = 0
        
        # Migrate CDO notifications
        result = await self.db.execute(
            select(CDONotification).where(
                CDONotification.metadata.is_(None) |
                ~CDONotification.metadata.has_key("universal_assignment_id")
            )
        )
        cdo_notifications = result.scalars().all()
        
        for notification in cdo_notifications:
            universal_assignment = UniversalAssignment(
                assignment_type="LOB Assignment",
                cycle_id=notification.cycle_id,
                report_id=notification.report_id,
                from_user_id=notification.created_by,
                to_user_id=notification.cdo_user_id,
                from_role="Data Executive",
                to_role="Data Executive",  # Updated from CDO
                title="LOB Assignment Review Required",
                description=notification.notification_text,
                priority="High",
                status=self._map_legacy_status(notification.status),
                created_at=notification.created_at,
                created_by=notification.created_by,
                acknowledged_at=notification.acknowledged_at,
                completed_at=notification.completed_at,
                assignment_metadata={
                    "lob_id": notification.lob_id,
                    "migrated_from": "cdo_notifications",
                    "original_id": notification.notification_id,
                    "migration_date": datetime.utcnow().isoformat()
                }
            )
            self.db.add(universal_assignment)
            migrated_count += 1
        
        # Migrate data owner notifications
        result = await self.db.execute(
            select(DataProviderNotification).where(
                DataProviderNotification.metadata.is_(None) |
                ~DataProviderNotification.metadata.has_key("universal_assignment_id")
            )
        )
        data_notifications = result.scalars().all()
        
        for notification in data_notifications:
            universal_assignment = UniversalAssignment(
                assignment_type="Information Request",
                cycle_id=notification.cycle_id,
                report_id=notification.report_id,
                from_user_id=notification.created_by,
                to_user_id=notification.data_provider_id,
                from_role="Test Manager",
                to_role="Data Owner",
                title="Information Request",
                description=notification.notification_text,
                priority="Medium",
                status=self._map_legacy_status(notification.status),
                created_at=notification.created_at,
                created_by=notification.created_by,
                acknowledged_at=notification.acknowledged_at,
                completed_at=notification.completed_at,
                assignment_metadata={
                    "test_case_ids": notification.test_case_ids,
                    "migrated_from": "data_owner_notifications",
                    "original_id": notification.notification_id,
                    "migration_date": datetime.utcnow().isoformat()
                }
            )
            self.db.add(universal_assignment)
            migrated_count += 1
        
        await self.db.commit()
        
        logger.info(f"Migrated {migrated_count} historical notifications")
        return migrated_count
    
    def _map_legacy_status(self, legacy_status: str) -> str:
        """Map legacy status to universal status"""
        status_map = {
            "sent": "Assigned",
            "acknowledged": "Acknowledged",
            "in_progress": "In Progress",
            "complete": "Completed",
            "completed": "Completed",
            "cancelled": "Cancelled"
        }
        return status_map.get(legacy_status, "Assigned")