"""
Attribute Versioning Service

Comprehensive service for managing attribute versions, approvals, comparisons, and audit trails.
Handles the business logic for attribute lifecycle management.
"""

import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text, desc, update
from sqlalchemy.orm import selectinload

from app.models.report_attribute import ReportAttribute
# from app.models.report_attribute import AttributeVersionChangeLog, AttributeVersionComparison  # Temporarily disabled

# Temporary placeholder classes to avoid breaking the system
class AttributeVersionChangeLog:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class AttributeVersionComparison:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
from app.models.user import User
from app.core.logging import get_logger
from app.core.exceptions import ValidationException

logger = get_logger(__name__)


class AttributeVersioningService:
    """Service for managing attribute versions and lifecycle"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_new_version(
        self, 
        attribute_id: int, 
        updated_by_user_id: int, 
        updated_data: Dict[str, Any],
        change_reason: str = None, 
        version_notes: str = None
    ) -> ReportAttribute:
        """
        Create a new version of an attribute with updated data
        
        Args:
            attribute_id: ID of the current attribute version
            updated_by_user_id: User creating the new version  
            updated_data: Dictionary of fields to update
            change_reason: Reason for creating new version
            version_notes: Notes about the changes
            
        Returns:
            New ReportAttribute version
        """
        try:
            # Get current attribute version
            result = await self.db.execute(
                select(ReportAttribute).where(ReportAttribute.attribute_id == attribute_id)
            )
            current_attribute = result.scalar_one_or_none()
            
            if not current_attribute:
                raise ValidationException(f"Attribute {attribute_id} not found")
            
            # Create new version using model method
            new_version = current_attribute.create_new_version(
                updated_by_user_id=updated_by_user_id,
                change_reason=change_reason,
                version_notes=version_notes
            )
            
            # Apply updated data to new version
            for field, value in updated_data.items():
                if hasattr(new_version, field):
                    setattr(new_version, field, value)
            
            # Add to database and flush to get the new attribute ID
            self.db.add(new_version)
            await self.db.flush()  # Get the new attribute ID
            
            # Create change log entry with the new attribute ID
            field_changes = json.dumps({
                field: {"old": getattr(current_attribute, field, None), "new": value}
                for field, value in updated_data.items()
                if hasattr(current_attribute, field)
            })
            
            change_log = AttributeVersionChangeLog(
                attribute_id=new_version.attribute_id,
                change_type='created',
                version_number=new_version.version_number,
                changed_by=updated_by_user_id,
                change_notes=version_notes,
                field_changes=field_changes
            )
            
            self.db.add(change_log)
            await self.db.commit()
            
            logger.info(f"Created new version {new_version.version_number} for attribute {attribute_id}")
            return new_version
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create new version for attribute {attribute_id}: {str(e)}")
            raise
    
    async def approve_version(
        self, 
        attribute_id: int, 
        approved_by_user_id: int, 
        approval_notes: str = None
    ) -> AttributeVersionChangeLog:
        """Approve an attribute version"""
        try:
            # Get attribute version
            result = await self.db.execute(
                select(ReportAttribute).where(ReportAttribute.attribute_id == attribute_id)
            )
            attribute = result.scalar_one_or_none()
            
            if not attribute:
                raise ValidationException(f"Attribute {attribute_id} not found")
            
            if attribute.approval_status == 'approved':
                raise ValidationException(f"Attribute {attribute_id} is already approved")
            
            # Approve the version
            change_log = attribute.approve_version(approved_by_user_id, approval_notes)
            self.db.add(change_log)
            
            await self.db.commit()
            
            logger.info(f"Approved attribute version {attribute_id} v{attribute.version_number}")
            return change_log
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to approve attribute {attribute_id}: {str(e)}")
            raise
    
    async def reject_version(
        self, 
        attribute_id: int, 
        rejected_by_user_id: int, 
        rejection_reason: str = None
    ) -> AttributeVersionChangeLog:
        """Reject an attribute version"""
        try:
            # Get attribute version
            result = await self.db.execute(
                select(ReportAttribute).where(ReportAttribute.attribute_id == attribute_id)
            )
            attribute = result.scalar_one_or_none()
            
            if not attribute:
                raise ValidationException(f"Attribute {attribute_id} not found")
            
            if attribute.approval_status == 'rejected':
                raise ValidationException(f"Attribute {attribute_id} is already rejected")
            
            # Reject the version
            change_log = attribute.reject_version(rejected_by_user_id, rejection_reason)
            self.db.add(change_log)
            
            await self.db.commit()
            
            logger.info(f"Rejected attribute version {attribute_id} v{attribute.version_number}")
            return change_log
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to reject attribute {attribute_id}: {str(e)}")
            raise
    
    async def archive_version(
        self, 
        attribute_id: int, 
        archived_by_user_id: int, 
        archive_reason: str = None
    ) -> AttributeVersionChangeLog:
        """Archive an attribute version"""
        try:
            # Get attribute version
            result = await self.db.execute(
                select(ReportAttribute).where(ReportAttribute.attribute_id == attribute_id)
            )
            attribute = result.scalar_one_or_none()
            
            if not attribute:
                raise ValidationException(f"Attribute {attribute_id} not found")
            
            if not attribute.is_active:
                raise ValidationException(f"Attribute {attribute_id} is already archived")
            
            # Archive the version
            change_log = attribute.archive_version(archived_by_user_id, archive_reason)
            self.db.add(change_log)
            
            await self.db.commit()
            
            logger.info(f"Archived attribute version {attribute_id} v{attribute.version_number}")
            return change_log
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to archive attribute {attribute_id}: {str(e)}")
            raise
    
    async def restore_version(
        self, 
        attribute_id: int, 
        restored_by_user_id: int, 
        restore_reason: str = None
    ) -> AttributeVersionChangeLog:
        """Restore an attribute version as the latest active version"""
        try:
            # Get attribute version
            result = await self.db.execute(
                select(ReportAttribute).where(ReportAttribute.attribute_id == attribute_id)
            )
            attribute = result.scalar_one_or_none()
            
            if not attribute:
                raise ValidationException(f"Attribute {attribute_id} not found")
            
            # Get master attribute ID
            master_id = attribute.master_attribute_id or attribute.attribute_id
            
            # Mark all other versions of this attribute as not latest
            await self.db.execute(
                update(ReportAttribute)
                .where(
                    and_(
                        ReportAttribute.master_attribute_id == master_id,
                        ReportAttribute.attribute_id != attribute_id
                    )
                )
                .values(is_latest_version=False)
            )
            
            # Restore the version
            change_log = attribute.restore_version(restored_by_user_id, restore_reason)
            self.db.add(change_log)
            
            await self.db.commit()
            
            logger.info(f"Restored attribute version {attribute_id} v{attribute.version_number}")
            return change_log
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to restore attribute {attribute_id}: {str(e)}")
            raise
    
    async def get_version_history(self, master_attribute_id: int) -> Dict[str, Any]:
        """Get complete version history for an attribute"""
        try:
            # Get all versions of the attribute
            result = await self.db.execute(
                select(ReportAttribute)
                .options(
                    selectinload(ReportAttribute.version_created_by_user),
                    selectinload(ReportAttribute.approved_by_user),
                    selectinload(ReportAttribute.archived_by_user)
                )
                .where(
                    or_(
                        ReportAttribute.master_attribute_id == master_attribute_id,
                        ReportAttribute.attribute_id == master_attribute_id
                    )
                )
                .order_by(desc(ReportAttribute.version_number))
            )
            versions = result.scalars().all()
            
            if not versions:
                raise ValidationException(f"No versions found for master attribute {master_attribute_id}")
            
            # Get latest and active versions
            latest_version = max(versions, key=lambda v: v.version_number)
            active_versions = [v for v in versions if v.is_active and v.approval_status == 'approved']
            active_version = active_versions[0] if active_versions else None
            
            return {
                "master_attribute_id": master_attribute_id,
                "attribute_name": latest_version.attribute_name,
                "total_versions": len(versions),
                "latest_version": latest_version.version_number,
                "active_version": active_version.version_number if active_version else None,
                "versions": versions
            }
            
        except Exception as e:
            logger.error(f"Failed to get version history for attribute {master_attribute_id}: {str(e)}")
            raise
    
    async def compare_versions(
        self, 
        version_a_id: int, 
        version_b_id: int, 
        compared_by_user_id: int,
        comparison_notes: str = None
    ) -> Dict[str, Any]:
        """Compare two versions of an attribute and store the comparison"""
        try:
            # Get both versions
            result_a = await self.db.execute(
                select(ReportAttribute).where(ReportAttribute.attribute_id == version_a_id)
            )
            version_a = result_a.scalar_one_or_none()
            
            result_b = await self.db.execute(
                select(ReportAttribute).where(ReportAttribute.attribute_id == version_b_id)
            )
            version_b = result_b.scalar_one_or_none()
            
            if not version_a or not version_b:
                raise ValidationException("One or both versions not found")
            
            # Perform comparison using model method
            comparison_result = version_b.get_change_summary(version_a)
            
            # Calculate impact score based on type and number of changes
            impact_score = self._calculate_impact_score(comparison_result["changes"])
            
            # Store comparison in database
            comparison = AttributeVersionComparison(
                version_a_id=version_a_id,
                version_b_id=version_b_id,
                differences_found=len(comparison_result["changes"]),
                comparison_summary=json.dumps(comparison_result),
                impact_score=impact_score,
                compared_by=compared_by_user_id,
                comparison_notes=comparison_notes
            )
            
            self.db.add(comparison)
            await self.db.commit()
            
            # Return enhanced comparison result
            return {
                "comparison_id": comparison.comparison_id,
                "version_a_id": version_a_id,
                "version_b_id": version_b_id,
                "differences_found": len(comparison_result["changes"]),
                "comparison_summary": json.dumps(comparison_result),
                "impact_score": impact_score,
                "compared_at": comparison.compared_at,
                "compared_by": compared_by_user_id,
                "comparison_notes": comparison_notes,
                "changes": comparison_result["changes"],
                "summary": comparison_result["summary"]
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to compare versions {version_a_id} and {version_b_id}: {str(e)}")
            raise
    
    async def get_change_log(self, attribute_id: int) -> List[AttributeVersionChangeLog]:
        """Get change log for an attribute"""
        try:
            result = await self.db.execute(
                select(AttributeVersionChangeLog)
                .options(selectinload(AttributeVersionChangeLog.changed_by_user))
                .where(AttributeVersionChangeLog.attribute_id == attribute_id)
                .order_by(desc(AttributeVersionChangeLog.changed_at))
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get change log for attribute {attribute_id}: {str(e)}")
            raise
    
    async def bulk_approve_versions(
        self, 
        attribute_ids: List[int], 
        approved_by_user_id: int, 
        notes: str = None
    ) -> Dict[str, Any]:
        """Bulk approve multiple attribute versions"""
        results = []
        successful = 0
        failed = 0
        skipped = 0
        
        for attribute_id in attribute_ids:
            try:
                # Check if already approved
                result = await self.db.execute(
                    select(ReportAttribute).where(ReportAttribute.attribute_id == attribute_id)
                )
                attribute = result.scalar_one_or_none()
                
                if not attribute:
                    results.append({
                        "attribute_id": attribute_id,
                        "status": "failed",
                        "reason": "Attribute not found"
                    })
                    failed += 1
                    continue
                
                if attribute.approval_status == 'approved':
                    results.append({
                        "attribute_id": attribute_id, 
                        "status": "skipped",
                        "reason": "Already approved"
                    })
                    skipped += 1
                    continue
                
                # Approve the version
                change_log = await self.approve_version(attribute_id, approved_by_user_id, notes)
                results.append({
                    "attribute_id": attribute_id,
                    "status": "success",
                    "change_log_id": change_log.log_id
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "attribute_id": attribute_id,
                    "status": "failed", 
                    "reason": str(e)
                })
                failed += 1
        
        return {
            "total_requested": len(attribute_ids),
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "results": results,
            "summary": f"Bulk approval: {successful} successful, {failed} failed, {skipped} skipped"
        }
    
    async def get_attributes_by_status(
        self, 
        cycle_id: int, 
        report_id: int, 
        status: str = None,
        version_filter: str = "latest"  # latest, active, all
    ) -> List[ReportAttribute]:
        """Get attributes filtered by approval status and version"""
        try:
            query = select(ReportAttribute).where(
                and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id
                )
            )
            
            # Apply status filter
            if status:
                query = query.where(ReportAttribute.approval_status == status)
            
            # Apply version filter
            if version_filter == "latest":
                query = query.where(ReportAttribute.is_latest_version == True)
            elif version_filter == "active":
                query = query.where(
                    and_(
                        ReportAttribute.is_active == True,
                        ReportAttribute.approval_status == 'approved'
                    )
                )
            
            result = await self.db.execute(query.order_by(ReportAttribute.attribute_name))
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get attributes by status: {str(e)}")
            raise
    
    def _calculate_impact_score(self, changes: List[Dict[str, Any]]) -> float:
        """Calculate impact score for version changes"""
        if not changes:
            return 0.0
        
        # Define impact weights for different fields
        field_weights = {
            'attribute_name': 3.0,
            'data_type': 2.5,
            'mandatory_flag': 2.0,
            'validation_rules': 2.0,
            'risk_score': 1.5,
            'is_primary_key': 2.5,
            'primary_key_order': 1.5,
            'description': 1.0,
            'tester_notes': 0.5,
            'typical_source_documents': 1.0,
            'keywords_to_look_for': 1.0,
            'testing_approach': 1.0
        }
        
        total_impact = 0.0
        for change in changes:
            field = change.get('field', '')
            weight = field_weights.get(field, 1.0)
            total_impact += weight
        
        # Normalize to 0-10 scale
        max_possible_impact = len(changes) * 3.0  # Maximum weight per change
        normalized_score = min(10.0, (total_impact / max_possible_impact) * 10.0)
        
        return round(normalized_score, 2) 