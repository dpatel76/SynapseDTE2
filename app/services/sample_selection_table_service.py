"""
Sample Selection Service - Uses Version Tables
This consolidates all sample selection logic and uses proper database tables
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
import uuid
import json

from app.models.sample_selection import (
    SampleSelectionVersion, SampleSelectionSample,
    VersionStatus, SampleCategory, SampleDecision, SampleSource
)
from app.models.workflow import WorkflowPhase
from app.models.lob import LOB
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


def _serialize_for_json(obj):
    """Convert non-serializable types for JSON storage"""
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    return obj


class SampleSelectionTableService:
    """Consolidated service for sample selection using version tables"""
    
    @staticmethod
    async def get_current_version(
        db: AsyncSession,
        phase_id: int
    ) -> Optional[SampleSelectionVersion]:
        """Get the current active version for a phase"""
        
        # First try to get an approved version
        result = await db.execute(
            select(SampleSelectionVersion)
            .where(
                and_(
                    SampleSelectionVersion.phase_id == phase_id,
                    SampleSelectionVersion.version_status == VersionStatus.APPROVED
                )
            )
            .order_by(SampleSelectionVersion.version_number.desc())
            .limit(1)
        )
        version = result.scalar_one_or_none()
        
        if version:
            return version
            
        # Otherwise get the latest version
        result = await db.execute(
            select(SampleSelectionVersion)
            .where(SampleSelectionVersion.phase_id == phase_id)
            .order_by(SampleSelectionVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_or_create_version(
        db: AsyncSession,
        phase_id: int,
        user_id: int
    ) -> SampleSelectionVersion:
        """Get current version or create initial one"""
        
        version = await SampleSelectionTableService.get_current_version(db, phase_id)
        if version:
            return version
            
        # Create initial version
        version = SampleSelectionVersion(
            phase_id=phase_id,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            workflow_execution_id="initial",
            workflow_run_id="initial",
            activity_name="Initial Version",
            selection_criteria={},
            target_sample_size=0,
            actual_sample_size=0,
            created_by_id=user_id,
            updated_by_id=user_id,
            metadata={}
        )
        
        db.add(version)
        await db.flush()
        
        logger.info(f"Created initial version for phase {phase_id}")
        return version
    
    @staticmethod
    async def get_samples_for_display(
        db: AsyncSession,
        phase_id: int,
        version_number: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[SampleSelectionVersion]]:
        """Get samples formatted for frontend display"""
        
        # Get the appropriate version
        if version_number:
            result = await db.execute(
                select(SampleSelectionVersion)
                .where(
                    and_(
                        SampleSelectionVersion.phase_id == phase_id,
                        SampleSelectionVersion.version_number == version_number
                    )
                )
            )
            version = result.scalar_one_or_none()
        else:
            version = await SampleSelectionTableService.get_current_version(db, phase_id)
            
        if not version:
            return [], None
            
        # Get samples with optional LOB information
        result = await db.execute(
            select(SampleSelectionSample, LOB)
            .join(LOB, SampleSelectionSample.lob_id == LOB.lob_id, isouter=True)
            .where(SampleSelectionSample.version_id == version.version_id)
            .order_by(SampleSelectionSample.created_at)
        )
        
        samples_with_lobs = result.all()
        
        # Format for frontend
        formatted_samples = []
        for sample, lob in samples_with_lobs:
            # Get sample category value and convert to uppercase for frontend
            category_value = sample.sample_category.value if hasattr(sample.sample_category, 'value') else sample.sample_category
            if category_value:
                category_value = str(category_value).upper()
            
            formatted_sample = {
                "sample_id": str(sample.sample_id),
                "version_number": version.version_number,
                "line_of_business": lob.lob_name if lob else None,
                "lob_id": lob.lob_id if lob else None,
                "lob_assignment": lob.lob_name if lob else None,  # Add lob_assignment for frontend compatibility
                "primary_attribute_value": sample.sample_identifier,
                "sample_data": sample.sample_data,
                "sample_category": category_value,
                "sample_source": sample.sample_source.value if hasattr(sample.sample_source, 'value') else sample.sample_source,
                "risk_score": sample.risk_score,
                "confidence_score": sample.confidence_score,
                # Tester fields
                "tester_decision": sample.tester_decision.value if sample.tester_decision and hasattr(sample.tester_decision, 'value') else sample.tester_decision,
                "tester_feedback": sample.tester_decision_notes,
                "tester_decision_date": sample.tester_decision_at.isoformat() if sample.tester_decision_at else None,
                # Report Owner fields
                "report_owner_decision": sample.report_owner_decision.value if sample.report_owner_decision and hasattr(sample.report_owner_decision, 'value') else sample.report_owner_decision,
                "report_owner_feedback": sample.report_owner_decision_notes,
                "report_owner_decision_date": sample.report_owner_decision_at.isoformat() if sample.report_owner_decision_at else None,
                # Metadata
                "created_at": sample.created_at.isoformat(),
                "created_by_id": sample.created_by_id,
                "updated_at": sample.updated_at.isoformat() if sample.updated_at else None,
                "updated_by_id": sample.updated_by_id
            }
            
            # Add attribute focus - get from version's selection criteria or intelligent sampling config
            attribute_focus = None
            if version.intelligent_sampling_config:
                attribute_focus = version.intelligent_sampling_config.get("target_attribute")
            if not attribute_focus and version.selection_criteria:
                attribute_focus = version.selection_criteria.get("target_attribute")
            if not attribute_focus and sample.generation_metadata:
                attribute_focus = sample.generation_metadata.get("target_attribute")
            
            # If still not found, look for a non-PK attribute in scoped attributes
            if not attribute_focus and version.selection_criteria:
                scoped_attrs = version.selection_criteria.get("scoped_attributes", [])
                # Find first non-PK attribute, preferring numeric types
                non_pk_attrs = [attr for attr in scoped_attrs if not attr.get("is_primary_key")]
                
                if non_pk_attrs:
                    # Prefer numeric attributes for intelligent sampling
                    numeric_attrs = [attr for attr in non_pk_attrs 
                                   if attr.get('data_type', '').lower() in ['numeric', 'integer', 'decimal', 'float', 'double', 'bigint', 'int']]
                    
                    if numeric_attrs:
                        attribute_focus = numeric_attrs[0].get("attribute_name")
                    else:
                        attribute_focus = non_pk_attrs[0].get("attribute_name")
            
            formatted_sample["attribute_focus"] = attribute_focus or "Unknown"
            
            # Add rationale from generation metadata
            if sample.generation_metadata:
                formatted_sample["generation_metadata"] = sample.generation_metadata
                # Extract rationale if available
                formatted_sample["rationale"] = sample.generation_metadata.get("rationale", 
                    sample.generation_metadata.get("reason",
                    f"Sample selected as {category_value} case"))
                # Add generation fields for view dialog
                formatted_sample["generation_method"] = sample.generation_metadata.get("generation_method", "Data Source")
                formatted_sample["generated_at"] = sample.generation_metadata.get("generated_at", sample.created_at.isoformat())
                formatted_sample["generated_by"] = sample.generation_metadata.get("generated_by", "System")
            else:
                formatted_sample["rationale"] = f"Sample selected as {category_value} case"
                formatted_sample["generation_method"] = "Data Source"
                formatted_sample["generated_at"] = sample.created_at.isoformat()
                formatted_sample["generated_by"] = "System"
                
            formatted_samples.append(formatted_sample)
            
        return formatted_samples, version
    
    @staticmethod
    async def create_samples_from_generation(
        db: AsyncSession,
        version_id: uuid.UUID,
        generated_samples: List[Dict[str, Any]],
        user_id: int
    ) -> List[SampleSelectionSample]:
        """Create sample records from generated data"""
        
        # Get version to update count
        result = await db.execute(
            select(SampleSelectionVersion).where(
                SampleSelectionVersion.version_id == version_id
            )
        )
        version = result.scalar_one()
        
        created_samples = []
        
        for sample_data in generated_samples:
            # LOB assignment is now optional - tester will assign it
            lob_id = None
            if 'line_of_business' in sample_data:
                # Only assign LOB if explicitly provided
                lob_result = await db.execute(
                    select(LOB).where(LOB.lob_name == sample_data['line_of_business'])
                )
                lob = lob_result.scalar_one_or_none()
                if lob:
                    lob_id = lob.lob_id
                else:
                    logger.warning(f"LOB not found: {sample_data['line_of_business']}")
                
            sample = SampleSelectionSample(
                version_id=version_id,
                phase_id=version.phase_id,
                lob_id=lob_id,  # Can be None - tester will assign later
                sample_identifier=sample_data.get('primary_attribute_value', ''),
                sample_data=_serialize_for_json(sample_data.get('data_row_snapshot', {})),
                sample_category=SampleCategory(sample_data.get('sample_category', 'clean')),
                sample_source=SampleSource(sample_data.get('sample_source', 'tester')),
                risk_score=sample_data.get('risk_score'),
                confidence_score=sample_data.get('confidence_score'),
                generation_metadata=_serialize_for_json(sample_data.get('metadata', {})),
                created_by_id=user_id,
                updated_by_id=user_id
            )
            
            db.add(sample)
            created_samples.append(sample)
            
        # Update version sample count
        version.actual_sample_size += len(created_samples)
        version.updated_at = datetime.utcnow()
        version.updated_by_id = user_id
        
        await db.flush()
        
        logger.info(f"Created {len(created_samples)} samples for version {version.version_number}")
        return created_samples
    
    @staticmethod
    async def update_sample_decision(
        db: AsyncSession,
        sample_id: uuid.UUID,
        decision: str,
        notes: Optional[str],
        user_id: int,
        user_role: str
    ) -> SampleSelectionSample:
        """Update sample decision based on user role"""
        
        # Get sample
        result = await db.execute(
            select(SampleSelectionSample).where(
                SampleSelectionSample.sample_id == sample_id
            )
        )
        sample = result.scalar_one()
        
        decision_enum = SampleDecision(decision)
        
        # Update based on role
        if user_role in ["Report Owner", "Report Owner Executive"]:
            sample.report_owner_decision = decision_enum
            sample.report_owner_decision_at = datetime.utcnow()
            sample.report_owner_decision_by_id = user_id
            sample.report_owner_decision_notes = notes
        else:  # Tester or admin
            sample.tester_decision = decision_enum
            sample.tester_decision_at = datetime.utcnow()
            sample.tester_decision_by_id = user_id
            sample.tester_decision_notes = notes
            
        sample.updated_at = datetime.utcnow()
        sample.updated_by_id = user_id
        
        await db.flush()
        
        logger.info(f"Updated decision for sample {sample_id}")
        return sample
    
    @staticmethod
    async def submit_version_for_approval(
        db: AsyncSession,
        version_id: uuid.UUID,
        user_id: int,
        notes: Optional[str] = None
    ) -> SampleSelectionVersion:
        """Submit version for approval"""
        
        # Get version
        result = await db.execute(
            select(SampleSelectionVersion).where(
                SampleSelectionVersion.version_id == version_id
            )
        )
        version = result.scalar_one()
        
        if version.version_status != VersionStatus.DRAFT:
            raise ValueError(f"Cannot submit version in {version.version_status} status")
            
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.submission_notes = notes
        version.submitted_by_id = user_id
        version.submitted_at = datetime.utcnow()
        version.updated_at = datetime.utcnow()
        version.updated_by_id = user_id
        
        # Update distribution metrics to track submission
        if not version.distribution_metrics:
            version.distribution_metrics = {}
        version.distribution_metrics['submission_timestamp'] = datetime.utcnow().isoformat()
        
        await db.flush()
        
        logger.info(f"Submitted version {version.version_number} for approval")
        return version
    
    @staticmethod
    async def create_new_version_from_feedback(
        db: AsyncSession,
        phase_id: int,
        parent_version_id: uuid.UUID,
        user_id: int,
        change_reason: str = "Incorporating feedback"
    ) -> SampleSelectionVersion:
        """Create new version based on feedback"""
        
        # Get parent version
        parent_result = await db.execute(
            select(SampleSelectionVersion).where(
                SampleSelectionVersion.version_id == parent_version_id
            )
        )
        parent_version = parent_result.scalar_one()
        
        # Get next version number
        max_version_result = await db.execute(
            select(func.max(SampleSelectionVersion.version_number))
            .where(SampleSelectionVersion.phase_id == phase_id)
        )
        max_version = max_version_result.scalar() or 0
        
        # Create new version
        new_version = SampleSelectionVersion(
            phase_id=phase_id,
            version_number=max_version + 1,
            version_status=VersionStatus.DRAFT,
            parent_version_id=parent_version_id,
            workflow_execution_id=f"v{max_version + 1}",
            workflow_run_id=f"run-{uuid.uuid4()}",
            activity_name="Version from Feedback",
            selection_criteria=parent_version.selection_criteria,
            target_sample_size=parent_version.target_sample_size,
            actual_sample_size=0,
            created_by_id=user_id,
            updated_by_id=user_id,
            metadata={
                "created_from": f"version_{parent_version.version_number}",
                "change_reason": change_reason,
                "parent_version_id": str(parent_version_id)
            }
        )
        
        db.add(new_version)
        await db.flush()
        
        # Copy approved samples from parent
        parent_samples_result = await db.execute(
            select(SampleSelectionSample).where(
                and_(
                    SampleSelectionSample.version_id == parent_version_id,
                    SampleSelectionSample.tester_decision == SampleDecision.APPROVED
                )
            )
        )
        parent_samples = parent_samples_result.scalars().all()
        
        for sample in parent_samples:
            new_sample = SampleSelectionSample(
                version_id=new_version.version_id,
                phase_id=phase_id,
                lob_id=sample.lob_id,
                sample_identifier=sample.sample_identifier,
                sample_data=sample.sample_data,
                sample_category=sample.sample_category,
                sample_source=SampleSource.CARRIED_FORWARD,
                risk_score=sample.risk_score,
                confidence_score=sample.confidence_score,
                generation_metadata=sample.generation_metadata,
                validation_results=sample.validation_results,
                # Preserve decisions
                tester_decision=sample.tester_decision,
                tester_decision_notes=sample.tester_decision_notes,
                tester_decision_at=sample.tester_decision_at,
                tester_decision_by_id=sample.tester_decision_by_id,
                report_owner_decision=sample.report_owner_decision,
                report_owner_decision_notes=sample.report_owner_decision_notes,
                report_owner_decision_at=sample.report_owner_decision_at,
                report_owner_decision_by_id=sample.report_owner_decision_by_id,
                # Track carry-forward
                carried_from_version_id=parent_version_id,
                carried_from_sample_id=sample.sample_id,
                carry_forward_reason=change_reason,
                created_by_id=user_id,
                updated_by_id=user_id
            )
            db.add(new_sample)
            
        new_version.actual_sample_size = len(parent_samples)
        
        await db.flush()
        
        logger.info(f"Created version {new_version.version_number} from parent version {parent_version.version_number}")
        return new_version
    
    @staticmethod
    async def create_version(
        db: AsyncSession,
        phase_id: int,
        user_id: int,
        generation_method: Optional[str] = None,
        change_reason: Optional[str] = None,
        carry_forward_approved: bool = False
    ) -> SampleSelectionVersion:
        """Create a new empty version for sample selection"""
        
        # Get the latest version number
        latest_version = await SampleSelectionTableService.get_current_version(db, phase_id)
        next_version_number = 1
        if latest_version:
            next_version_number = latest_version.version_number + 1
        
        # Create new version
        new_version = SampleSelectionVersion(
            phase_id=phase_id,
            version_number=next_version_number,
            version_status=VersionStatus.DRAFT,
            workflow_execution_id=f"v{next_version_number}",
            workflow_run_id=f"run-{uuid.uuid4()}",
            activity_name="Manual Version Creation",
            selection_criteria={},
            target_sample_size=0,
            actual_sample_size=0,
            created_by_id=user_id,
            updated_by_id=user_id,
            metadata={
                "generation_method": generation_method or "manual",
                "change_reason": change_reason or "Created new version"
            }
        )
        db.add(new_version)
        
        # If carry_forward_approved is True and there's a previous version, copy approved samples
        if carry_forward_approved and latest_version:
            # Get approved samples from latest version
            samples_result = await db.execute(
                select(SampleSelectionSample)
                .where(
                    and_(
                        SampleSelectionSample.version_id == latest_version.version_id,
                        SampleSelectionSample.tester_decision == SampleDecision.APPROVED
                    )
                )
            )
            approved_samples = samples_result.scalars().all()
            
            # Copy approved samples to new version
            for sample in approved_samples:
                new_sample = SampleSelectionSample(
                    version_id=new_version.version_id,
                    sample_identifier=sample.sample_identifier,
                    sample_data=sample.sample_data,
                    sample_category=sample.sample_category,
                    data_quality_passed=sample.data_quality_passed,
                    generation_metadata=sample.generation_metadata,
                    # Reset decisions for new version
                    tester_decision=SampleDecision.PENDING,
                    lob_id=sample.lob_id,
                    created_by_id=user_id,
                    updated_by_id=user_id
                )
                db.add(new_sample)
        
        await db.flush()
        
        logger.info(f"Created new version {new_version.version_number} for phase {phase_id}")
        return new_version
    
    @staticmethod
    async def create_version_from_feedback(
        db: AsyncSession,
        phase_id: int,
        user_id: int,
        feedback_version_id: Optional[str] = None
    ) -> SampleSelectionVersion:
        """Create new version preserving report owner feedback (Make Changes workflow)"""
        
        # Get the latest version
        latest_version = await SampleSelectionTableService.get_current_version(db, phase_id)
        if not latest_version:
            raise ValueError("No existing version found")
            
        # Check current version status - only block if pending approval
        # Allow changes for approved versions (after Report Owner review)
        if latest_version.version_status == VersionStatus.PENDING_APPROVAL:
            raise ValueError("Cannot make changes while version is pending Report Owner approval")
        
        # Find the version with report owner feedback
        if feedback_version_id:
            # Use specific version if provided
            feedback_version_result = await db.execute(
                select(SampleSelectionVersion)
                .where(SampleSelectionVersion.version_id == feedback_version_id)
            )
            feedback_version = feedback_version_result.scalar_one_or_none()
        else:
            # Find the latest submitted version with RO feedback
            versions_result = await db.execute(
                select(SampleSelectionVersion)
                .where(SampleSelectionVersion.phase_id == phase_id)
                .order_by(SampleSelectionVersion.version_number.desc())
            )
            versions = versions_result.scalars().all()
            
            feedback_version = None
            for version in versions:
                # Check if this version has RO feedback
                samples_result = await db.execute(
                    select(SampleSelectionSample)
                    .where(
                        and_(
                            SampleSelectionSample.version_id == version.version_id,
                            SampleSelectionSample.report_owner_decision.isnot(None)
                        )
                    )
                    .limit(1)
                )
                if samples_result.scalar_one_or_none():
                    feedback_version = version
                    break
        
        if not feedback_version:
            raise ValueError("No version found with Report Owner feedback")
        
        # Get samples from feedback version
        samples_result = await db.execute(
            select(SampleSelectionSample)
            .where(SampleSelectionSample.version_id == feedback_version.version_id)
        )
        feedback_samples = samples_result.scalars().all()
        
        if not feedback_samples:
            raise ValueError("No samples found in feedback version")
        
        # Check if there's already a draft version created from this feedback version
        existing_draft_result = await db.execute(
            select(SampleSelectionVersion)
            .where(
                and_(
                    SampleSelectionVersion.phase_id == phase_id,
                    SampleSelectionVersion.version_status == VersionStatus.DRAFT,
                    SampleSelectionVersion.parent_version_id == feedback_version.version_id
                )
            )
            .limit(1)
        )
        existing_draft = existing_draft_result.scalar_one_or_none()
        
        if existing_draft:
            logger.info(f"Draft version {existing_draft.version_number} already exists from feedback version {feedback_version.version_number}, returning it")
            return existing_draft
        
        # Get the highest version number to determine the next version
        max_version_result = await db.execute(
            select(func.max(SampleSelectionVersion.version_number))
            .where(SampleSelectionVersion.phase_id == phase_id)
        )
        max_version_number = max_version_result.scalar() or 0
        
        # Create new version with next number
        new_version_number = max_version_number + 1
        new_version = SampleSelectionVersion(
            phase_id=phase_id,
            version_number=new_version_number,
            version_status=VersionStatus.DRAFT,
            workflow_execution_id=feedback_version.workflow_execution_id,
            workflow_run_id=f"make_changes_{new_version_number}",
            activity_name="Make Changes from Feedback",
            selection_criteria=feedback_version.selection_criteria,
            target_sample_size=feedback_version.target_sample_size,
            actual_sample_size=0,
            parent_version_id=feedback_version.version_id,
            created_by_id=user_id,
            updated_by_id=user_id,
            version_metadata={
                "created_from_feedback": True,
                "feedback_version_number": feedback_version.version_number,
                "change_reason": f"Created from report owner feedback on version {feedback_version.version_number}"
            }
        )
        db.add(new_version)
        await db.flush()
        
        # Copy samples, preserving report owner decisions
        for sample in feedback_samples:
            new_sample = SampleSelectionSample(
                version_id=new_version.version_id,
                phase_id=sample.phase_id,
                lob_id=sample.lob_id,
                sample_identifier=sample.sample_identifier,
                sample_data=sample.sample_data,
                sample_category=sample.sample_category,
                sample_source=sample.sample_source,
                # Preserve report owner decisions
                report_owner_decision=sample.report_owner_decision,
                report_owner_decision_notes=sample.report_owner_decision_notes,
                report_owner_decision_at=sample.report_owner_decision_at,
                report_owner_decision_by_id=sample.report_owner_decision_by_id,
                # Reset tester decision if sample was rejected by RO
                tester_decision=None if sample.report_owner_decision == SampleDecision.REJECTED else sample.tester_decision,
                tester_decision_notes=None if sample.report_owner_decision == SampleDecision.REJECTED else sample.tester_decision_notes,
                tester_decision_at=None if sample.report_owner_decision == SampleDecision.REJECTED else sample.tester_decision_at,
                tester_decision_by_id=None if sample.report_owner_decision == SampleDecision.REJECTED else sample.tester_decision_by_id,
                # Other fields
                risk_score=sample.risk_score,
                confidence_score=sample.confidence_score,
                generation_metadata=sample.generation_metadata,
                validation_results=sample.validation_results,
                carry_forward_reason=f"Make changes from version {feedback_version.version_number}",
                created_by_id=user_id,
                updated_by_id=user_id
            )
            db.add(new_sample)
        
        new_version.actual_sample_size = len(feedback_samples)
        
        await db.flush()
        
        logger.info(f"Created version {new_version.version_number} from feedback version {feedback_version.version_number} with {len(feedback_samples)} samples")
        return new_version
    
    @staticmethod
    async def migrate_from_phase_data(
        db: AsyncSession,
        phase: WorkflowPhase,
        user_id: int
    ) -> int:
        """One-time migration from phase_data to version tables"""
        
        phase_data = phase.phase_data or {}
        
        # Check if already migrated
        existing_versions = await db.execute(
            select(func.count(SampleSelectionVersion.version_id))
            .where(SampleSelectionVersion.phase_id == phase.phase_id)
        )
        if existing_versions.scalar() > 0:
            logger.info(f"Phase {phase.phase_id} already migrated")
            return 0
            
        versions_data = phase_data.get('versions', [])
        samples_data = phase_data.get('cycle_report_sample_selection_samples', [])
        
        if not versions_data and not samples_data:
            return 0
            
        # Create version 1 if no versions exist
        if not versions_data:
            versions_data = [{
                'version_number': 1,
                'version_status': 'draft',
                'created_at': datetime.utcnow().isoformat(),
                'created_by': user_id
            }]
            
        version_map = {}
        
        # Migrate versions
        for v_data in versions_data:
            version = SampleSelectionVersion(
                phase_id=phase.phase_id,
                version_number=v_data.get('version_number', 1),
                version_status=VersionStatus.DRAFT,
                workflow_execution_id='migrated',
                workflow_run_id='migrated',
                activity_name='Migrated Version',
                selection_criteria={},
                target_sample_size=0,
                actual_sample_size=v_data.get('total_samples', 0),
                created_at=datetime.fromisoformat(v_data['created_at']) if 'created_at' in v_data else datetime.utcnow(),
                created_by_id=v_data.get('created_by', user_id),
                updated_by_id=user_id,
                metadata=v_data.get('metadata', {})
            )
            
            db.add(version)
            await db.flush()
            
            version_map[version.version_number] = version.version_id
            
        # Migrate samples
        for s_data in samples_data:
            version_num = s_data.get('version_number', 1)
            version_id = version_map.get(version_num, list(version_map.values())[0])
            
            # Get LOB
            lob_result = await db.execute(
                select(LOB).where(LOB.lob_name == s_data.get('line_of_business', ''))
            )
            lob = lob_result.scalar_one_or_none()
            
            if not lob:
                continue
                
            sample = SampleSelectionSample(
                version_id=version_id,
                phase_id=phase.phase_id,
                lob_id=lob.lob_id,
                sample_identifier=s_data.get('primary_attribute_value', ''),
                sample_data=s_data.get('data_row_snapshot', {}),
                sample_category=SampleCategory.CLEAN,
                sample_source=SampleSource.TESTER,
                created_at=datetime.fromisoformat(s_data['created_at']) if 'created_at' in s_data else datetime.utcnow(),
                created_by_id=s_data.get('created_by_id', user_id),
                updated_by_id=user_id
            )
            
            # Migrate decisions
            if s_data.get('tester_decision'):
                sample.tester_decision = SampleDecision(s_data['tester_decision'])
                sample.tester_decision_notes = s_data.get('tester_feedback')
                
            if s_data.get('report_owner_decision'):
                sample.report_owner_decision = SampleDecision(s_data['report_owner_decision'])
                sample.report_owner_decision_notes = s_data.get('report_owner_feedback')
                
            db.add(sample)
            
        await db.flush()
        
        logger.info(f"Migrated {len(version_map)} versions and {len(samples_data)} samples for phase {phase.phase_id}")
        return len(samples_data)