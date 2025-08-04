"""
Observation Versioning Service

Handles version management for observations including:
- Creating new versions
- Submitting for approval
- Managing approval workflow
- Tracking changes between versions
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observation_versioning import (
    ObservationVersion,
    ObservationVersionItem,
    ObservationVersionChangeLog,
    ObservationVersionStatus,
    ObservationApprovalStatus
)
from app.models.observation_management import ObservationRecord
from app.models.workflow import WorkflowPhase
from app.core.exceptions import BusinessError


class ObservationVersioningService:
    """Service for managing observation versions"""
    
    async def create_new_version(
        self,
        db: AsyncSession,
        phase_id: int,
        user_id: int,
        parent_version_id: Optional[str] = None
    ) -> ObservationVersion:
        """Create a new observation version"""
        
        # Get the latest version number
        latest_version_query = select(func.max(ObservationVersion.version_number)).where(
            ObservationVersion.phase_id == phase_id
        )
        latest_version_result = await db.execute(latest_version_query)
        latest_version_number = latest_version_result.scalar() or 0
        
        # Create new version
        new_version = ObservationVersion(
            phase_id=phase_id,
            version_number=latest_version_number + 1,
            version_status=ObservationVersionStatus.DRAFT.value,
            parent_version_id=parent_version_id,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        
        db.add(new_version)
        await db.flush()
        
        # If there's a parent version, copy observations
        if parent_version_id:
            await self._copy_observations_from_parent(db, parent_version_id, new_version.version_id, user_id)
        
        # Create change log entry
        change_log = ObservationVersionChangeLog(
            from_version_id=parent_version_id,
            to_version_id=new_version.version_id,
            change_type='created',
            change_summary=f'Created version {new_version.version_number}',
            changed_by=user_id,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(change_log)
        
        await db.commit()
        return new_version
    
    async def add_observations_to_version(
        self,
        db: AsyncSession,
        version_id: str,
        observation_ids: List[int],
        user_id: int
    ) -> List[ObservationVersionItem]:
        """Add observations to a version"""
        
        # Get the version
        version = await db.get(ObservationVersion, version_id)
        if not version:
            raise BusinessError("Version not found")
        
        if version.version_status != ObservationVersionStatus.DRAFT.value:
            raise BusinessError("Can only add observations to draft versions")
        
        # Create version items
        items = []
        for obs_id in observation_ids:
            # Check if observation exists
            obs = await db.get(ObservationRecord, obs_id)
            if not obs:
                continue
            
            # Determine priority based on severity
            priority = 'medium'
            if obs.severity and obs.severity.value == 'HIGH':
                priority = 'high'
            elif obs.severity and obs.severity.value == 'LOW':
                priority = 'low'
            
            item = ObservationVersionItem(
                version_id=version_id,
                observation_id=obs_id,
                priority=priority,
                created_by_id=user_id,
                updated_by_id=user_id
            )
            db.add(item)
            items.append(item)
        
        # Update version statistics
        await self._update_version_statistics(db, version_id)
        
        await db.commit()
        return items
    
    async def submit_version_for_approval(
        self,
        db: AsyncSession,
        version_id: str,
        user_id: int,
        submission_notes: Optional[str] = None
    ) -> ObservationVersion:
        """Submit version for approval"""
        
        # Get the version with items
        version_query = select(ObservationVersion).options(
            selectinload(ObservationVersion.observation_items)
        ).where(ObservationVersion.version_id == version_id)
        result = await db.execute(version_query)
        version = result.scalar_one_or_none()
        
        if not version:
            raise BusinessError("Version not found")
        
        if version.version_status != ObservationVersionStatus.DRAFT.value:
            raise BusinessError("Can only submit draft versions")
        
        if not version.observation_items:
            raise BusinessError("Cannot submit version with no observations")
        
        # Update version status
        version.version_status = ObservationVersionStatus.PENDING_APPROVAL.value
        version.approval_status = ObservationApprovalStatus.PENDING.value
        version.submitted_at = datetime.utcnow()
        version.submitted_by = user_id
        version.submission_notes = submission_notes
        version.updated_by_id = user_id
        
        # Create change log
        change_log = ObservationVersionChangeLog(
            to_version_id=version_id,
            change_type='submitted',
            change_summary=f'Submitted version {version.version_number} for approval',
            change_details={'submission_notes': submission_notes},
            changed_by=user_id,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(change_log)
        
        await db.commit()
        return version
    
    async def approve_version(
        self,
        db: AsyncSession,
        version_id: str,
        user_id: int,
        approval_level: str,  # 'tester' or 'report_owner'
        comments: Optional[str] = None
    ) -> ObservationVersion:
        """Approve a version"""
        
        version = await db.get(ObservationVersion, version_id)
        if not version:
            raise BusinessError("Version not found")
        
        if version.version_status != ObservationVersionStatus.PENDING_APPROVAL.value:
            raise BusinessError("Version is not pending approval")
        
        if approval_level == 'tester':
            version.tester_approval_at = datetime.utcnow()
            version.tester_approval_by = user_id
            version.tester_approval_comments = comments
            
            # Update approval status
            if version.approval_status == ObservationApprovalStatus.PENDING.value:
                version.approval_status = ObservationApprovalStatus.TESTER_APPROVED.value
        
        elif approval_level == 'report_owner':
            version.report_owner_approval_at = datetime.utcnow()
            version.report_owner_approval_by = user_id
            version.report_owner_approval_comments = comments
            
            # If tester already approved, mark as fully approved
            if version.approval_status == ObservationApprovalStatus.TESTER_APPROVED.value:
                version.approval_status = ObservationApprovalStatus.FULLY_APPROVED.value
                version.version_status = ObservationVersionStatus.APPROVED.value
            else:
                version.approval_status = ObservationApprovalStatus.REPORT_OWNER_APPROVED.value
        
        version.updated_by_id = user_id
        
        # Create change log
        change_log = ObservationVersionChangeLog(
            to_version_id=version_id,
            change_type='approved',
            change_summary=f'{approval_level.title()} approved version {version.version_number}',
            change_details={'approval_level': approval_level, 'comments': comments},
            changed_by=user_id,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(change_log)
        
        await db.commit()
        return version
    
    async def reject_version(
        self,
        db: AsyncSession,
        version_id: str,
        user_id: int,
        rejection_reason: str
    ) -> ObservationVersion:
        """Reject a version"""
        
        version = await db.get(ObservationVersion, version_id)
        if not version:
            raise BusinessError("Version not found")
        
        if version.version_status != ObservationVersionStatus.PENDING_APPROVAL.value:
            raise BusinessError("Version is not pending approval")
        
        version.version_status = ObservationVersionStatus.REJECTED.value
        version.approval_status = ObservationApprovalStatus.REJECTED.value
        version.updated_by_id = user_id
        
        # Create change log
        change_log = ObservationVersionChangeLog(
            to_version_id=version_id,
            change_type='rejected',
            change_summary=f'Rejected version {version.version_number}',
            change_details={'rejection_reason': rejection_reason},
            changed_by=user_id,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(change_log)
        
        await db.commit()
        return version
    
    async def get_current_version(
        self,
        db: AsyncSession,
        phase_id: int
    ) -> Optional[ObservationVersion]:
        """Get the current active version for a phase"""
        
        query = select(ObservationVersion).where(
            and_(
                ObservationVersion.phase_id == phase_id,
                ObservationVersion.version_status == ObservationVersionStatus.APPROVED.value
            )
        ).order_by(ObservationVersion.version_number.desc())
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _copy_observations_from_parent(
        self,
        db: AsyncSession,
        parent_version_id: str,
        new_version_id: str,
        user_id: int
    ):
        """Copy observations from parent version to new version"""
        
        # Get parent version items
        parent_items_query = select(ObservationVersionItem).where(
            ObservationVersionItem.version_id == parent_version_id
        )
        result = await db.execute(parent_items_query)
        parent_items = result.scalars().all()
        
        # Copy items to new version
        for parent_item in parent_items:
            new_item = ObservationVersionItem(
                version_id=new_version_id,
                observation_id=parent_item.observation_id,
                item_status=parent_item.item_status,
                priority=parent_item.priority,
                risk_rating=parent_item.risk_rating,
                group_id=parent_item.group_id,
                group_name=parent_item.group_name,
                created_by_id=user_id,
                updated_by_id=user_id
            )
            db.add(new_item)
    
    async def _update_version_statistics(
        self,
        db: AsyncSession,
        version_id: str
    ):
        """Update version statistics based on observations"""
        
        # Get version with items
        version_query = select(ObservationVersion).options(
            selectinload(ObservationVersion.observation_items).selectinload(
                ObservationVersionItem.observation
            )
        ).where(ObservationVersion.version_id == version_id)
        
        result = await db.execute(version_query)
        version = result.scalar_one_or_none()
        
        if not version:
            return
        
        # Calculate statistics
        total_observations = len(version.observation_items)
        high_priority = sum(1 for item in version.observation_items if item.priority == 'high')
        medium_priority = sum(1 for item in version.observation_items if item.priority == 'medium')
        low_priority = sum(1 for item in version.observation_items if item.priority == 'low')
        
        # Get unique samples and attributes
        unique_samples = set()
        unique_attributes = set()
        
        for item in version.observation_items:
            if item.observation:
                if item.observation.source_sample_record_id:
                    unique_samples.add(item.observation.source_sample_record_id)
                if item.observation.source_attribute_id:
                    unique_attributes.add(item.observation.source_attribute_id)
        
        # Update version
        version.total_observations = total_observations
        version.high_priority_observations = high_priority
        version.medium_priority_observations = medium_priority
        version.low_priority_observations = low_priority
        version.total_samples_impacted = len(unique_samples)
        version.total_attributes_impacted = len(unique_attributes)
        
        # Determine overall risk rating
        if high_priority > 0:
            version.overall_risk_rating = 'high'
        elif medium_priority > 0:
            version.overall_risk_rating = 'medium'
        else:
            version.overall_risk_rating = 'low'