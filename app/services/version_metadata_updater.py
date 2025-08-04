"""
Version Metadata Updater Service
Updates version metadata when assignments are completed
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.sample_selection import SampleSelectionVersion
from app.models.scoping import ScopingVersion
from app.models.data_profiling import DataProfilingVersion
from app.models.universal_assignment import UniversalAssignment
from app.core.logging import get_logger
from sqlalchemy.sql import func

logger = get_logger(__name__)


class VersionMetadataUpdater:
    """Service to update version metadata when assignments are completed"""
    
    @staticmethod
    async def update_sample_selection_version(
        db: AsyncSession,
        assignment: UniversalAssignment
    ) -> None:
        """Update Sample Selection version metadata when Report Owner completes assignment"""
        
        context_data = assignment.context_data or {}
        version_id = context_data.get('version_id')
        
        if not version_id:
            logger.warning(f"No version_id in assignment {assignment.assignment_id} context")
            return
            
        # Get the version
        version_query = await db.execute(
            select(SampleSelectionVersion).where(
                SampleSelectionVersion.version_id == version_id
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            logger.warning(f"Version {version_id} not found")
            return
            
        completion_data = assignment.completion_data or {}
        decision = completion_data.get('decision')
        
        # Update version metadata based on decision
        if decision == 'approved':
            version.version_status = 'approved'
            version.approved_by_id = assignment.completed_by_user_id
            version.approved_at = assignment.completed_at
            
            # Store report owner decision in proper columns
            version.report_owner_decision = 'approved'
            version.report_owner_feedback = completion_data.get('feedback', '')
            version.report_owner_reviewed_at = assignment.completed_at
            version.report_owner_reviewed_by_id = assignment.completed_by_user_id
            
        elif decision == 'rejected':
            version.version_status = 'rejected'
            
            # Store report owner decision in proper columns
            version.report_owner_decision = 'rejected'
            version.report_owner_feedback = completion_data.get('feedback', '')
            version.report_owner_reviewed_at = assignment.completed_at
            version.report_owner_reviewed_by_id = assignment.completed_by_user_id
            
        elif decision == 'revision_required':
            # Keep as rejected status (not draft) so feedback is visible
            version.version_status = 'rejected'
            
            # Store report owner decision in proper columns
            version.report_owner_decision = 'revision_required'
            version.report_owner_feedback = completion_data.get('feedback', '')
            version.report_owner_reviewed_at = assignment.completed_at
            version.report_owner_reviewed_by_id = assignment.completed_by_user_id
        
        # No need to flag modified since we're using regular columns now
        
        version.updated_at = datetime.utcnow()
        version.updated_by_id = assignment.completed_by_user_id
        
        await db.commit()
        
        logger.info(
            f"Updated Sample Selection version {version_id} metadata: "
            f"reviewed_by_report_owner=True, decision={decision}"
        )
    
    @staticmethod
    async def update_scoping_version(
        db: AsyncSession,
        assignment: UniversalAssignment
    ) -> None:
        """Update Scoping version metadata when Report Owner completes assignment"""
        
        context_data = assignment.context_data or {}
        version_id = context_data.get('version_id')
        
        if not version_id:
            logger.warning(f"No version_id in assignment {assignment.assignment_id} context")
            return
            
        # Get the version
        version_query = await db.execute(
            select(ScopingVersion).where(
                ScopingVersion.version_id == version_id
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            logger.warning(f"Version {version_id} not found")
            return
            
        completion_data = assignment.completion_data or {}
        decision = completion_data.get('decision')
        
        # Update version metadata
        if decision == 'approved':
            version.version_status = 'approved'
            version.approved_by_id = assignment.completed_by_user_id
            version.approved_at = assignment.completed_at
            
            # Mark as reviewed by Report Owner
            version.metadata = version.metadata or {}
            version.metadata['reviewed_by_report_owner'] = True
            version.metadata['report_owner_id'] = assignment.completed_by_user_id
            version.metadata['report_owner_review_date'] = assignment.completed_at.isoformat()
            version.metadata['report_owner_decision'] = 'approved'
            
        elif decision in ['rejected', 'revision_required']:
            version.metadata = version.metadata or {}
            version.metadata['reviewed_by_report_owner'] = True
            version.metadata['report_owner_id'] = assignment.completed_by_user_id
            version.metadata['report_owner_review_date'] = assignment.completed_at.isoformat()
            version.metadata['report_owner_decision'] = decision
            version.metadata['feedback'] = completion_data.get('feedback', '')
        
        # No need to flag modified since we're using regular columns now
        
        version.updated_at = datetime.utcnow()
        version.updated_by_id = assignment.completed_by_user_id
        
        await db.commit()
        
        logger.info(
            f"Updated Scoping version {version_id} metadata: "
            f"reviewed_by_report_owner=True, decision={decision}"
        )
    
    @staticmethod
    async def update_data_profiling_version(
        db: AsyncSession,
        assignment: UniversalAssignment
    ) -> None:
        """Update Data Profiling version metadata when Report Owner completes assignment"""
        
        context_data = assignment.context_data or {}
        version_id = context_data.get('version_id')
        
        if not version_id:
            logger.warning(f"No version_id in assignment {assignment.assignment_id} context")
            return
            
        # Get the version
        version_query = await db.execute(
            select(DataProfilingVersion).where(
                DataProfilingVersion.version_id == version_id
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            logger.warning(f"Version {version_id} not found")
            return
            
        completion_data = assignment.completion_data or {}
        decision = completion_data.get('decision')
        
        # Update version metadata
        if decision == 'approved':
            version.version_status = 'approved'
            version.approved_by_id = assignment.completed_by_user_id
            version.approved_at = assignment.completed_at
            
            # Mark as reviewed by Report Owner
            version.metadata = version.metadata or {}
            version.metadata['reviewed_by_report_owner'] = True
            version.metadata['report_owner_id'] = assignment.completed_by_user_id
            version.metadata['report_owner_review_date'] = assignment.completed_at.isoformat()
            version.metadata['report_owner_decision'] = 'approved'
            
        elif decision in ['rejected', 'revision_required']:
            version.metadata = version.metadata or {}
            version.metadata['reviewed_by_report_owner'] = True
            version.metadata['report_owner_id'] = assignment.completed_by_user_id
            version.metadata['report_owner_review_date'] = assignment.completed_at.isoformat()
            version.metadata['report_owner_decision'] = decision
            version.metadata['feedback'] = completion_data.get('feedback', '')
        
        # No need to flag modified since we're using regular columns now
        
        version.updated_at = datetime.utcnow()
        version.updated_by_id = assignment.completed_by_user_id
        
        await db.commit()
        
        logger.info(
            f"Updated Data Profiling version {version_id} metadata: "
            f"reviewed_by_report_owner=True, decision={decision}"
        )
    
    @staticmethod
    async def mark_final_version(
        db: AsyncSession,
        phase_id: int,
        version_id: str,
        phase_type: str
    ) -> None:
        """
        Mark a version as final when approved by both Tester and Report Owner
        
        Args:
            db: Database session
            phase_id: Phase ID
            version_id: Version ID to mark as final
            phase_type: Type of phase ('sample_selection', 'scoping', 'data_profiling')
        """
        
        # Get the appropriate model based on phase type
        if phase_type == 'sample_selection':
            model = SampleSelectionVersion
        elif phase_type == 'scoping':
            model = ScopingVersion
        elif phase_type == 'data_profiling':
            model = DataProfilingVersion
        else:
            logger.error(f"Unknown phase type: {phase_type}")
            return
            
        # Get the version
        version_query = await db.execute(
            select(model).where(
                model.version_id == version_id
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            logger.warning(f"Version {version_id} not found")
            return
            
        # Check if both approvals exist
        metadata = version.metadata or {}
        reviewed_by_ro = metadata.get('reviewed_by_report_owner', False)
        ro_decision = metadata.get('report_owner_decision')
        approved_by_tester = metadata.get('approved_by_tester', False)
        
        if reviewed_by_ro and ro_decision == 'approved' and approved_by_tester:
            # Mark as final version
            metadata['is_final_version'] = True
            metadata['final_version_date'] = datetime.utcnow().isoformat()
            
            # Update all other versions for this phase to not be final
            await db.execute(
                update(model)
                .where(
                    and_(
                        model.phase_id == phase_id,
                        model.version_id != version_id
                    )
                )
                .values(
                    metadata=func.jsonb_set(
                        model.metadata,
                        '{is_final_version}',
                        'false'
                    )
                )
            )
            
            # Flag metadata as modified
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(version, 'metadata')
            
            version.updated_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(
                f"Marked {phase_type} version {version_id} as final version"
            )
    
    @staticmethod
    async def handle_assignment_completion(
        db: AsyncSession,
        assignment: UniversalAssignment
    ) -> None:
        """Main entry point to handle version metadata updates on assignment completion"""
        
        # Determine the assignment type and call appropriate handler
        if assignment.assignment_type == "Sample Selection Approval":
            await VersionMetadataUpdater.update_sample_selection_version(db, assignment)
            
            # Check if we should mark as final
            context_data = assignment.context_data or {}
            version_id = context_data.get('version_id')
            phase_id = context_data.get('phase_id')
            if version_id and phase_id:
                await VersionMetadataUpdater.mark_final_version(
                    db, phase_id, version_id, 'sample_selection'
                )
                
        elif assignment.assignment_type == "Scoping Approval":
            await VersionMetadataUpdater.update_scoping_version(db, assignment)
            
            # Check if we should mark as final
            context_data = assignment.context_data or {}
            version_id = context_data.get('version_id')
            phase_id = context_data.get('phase_id')
            if version_id and phase_id:
                await VersionMetadataUpdater.mark_final_version(
                    db, phase_id, version_id, 'scoping'
                )
                
        elif assignment.assignment_type == "Rule Approval":
            await VersionMetadataUpdater.update_data_profiling_version(db, assignment)
            
            # Check if we should mark as final
            context_data = assignment.context_data or {}
            version_id = context_data.get('version_id')
            phase_id = context_data.get('phase_id')
            if version_id and phase_id:
                await VersionMetadataUpdater.mark_final_version(
                    db, phase_id, version_id, 'data_profiling'
                )