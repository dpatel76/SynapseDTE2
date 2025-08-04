"""
Sample Selection use cases for clean architecture
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload
import uuid
import random
import math

from app.application.use_cases.base import UseCase
from app.application.dtos.sample_selection import (
    SampleSelectionPhaseStartDTO,
    SampleSelectionVersionCreateDTO,
    SampleSelectionSampleCreateDTO,
    SampleSelectionVersionResponseDTO,
    SampleSelectionSampleResponseDTO,
    # SampleSelectionVersionWithRecordsDTO,  # Temporarily disabled
    SampleSelectionPhaseStatusDTO,
    SampleApprovalRequestDTO,
    SampleStatisticsDTO,
    AutoSampleSelectionRequestDTO,
    BulkSampleApprovalRequestDTO,
    SampleSelectionSummaryDTO,
    PhaseCompletionRequestDTO,
    SampleTypeEnum,
    SampleStatusEnum,
    SelectionMethodEnum
)
from app.models import (
    # WorkflowPhase,  # DEPRECATED: Use WorkflowPhase
    SampleSelectionVersion,
    SampleSelectionSample,
    ReportAttribute,
    WorkflowPhase,
    Report,
    # SampleUploadHistory,  # Temporarily disabled - model not found
    # SampleApprovalHistory  # Temporarily disabled - model not found
)
from app.services.workflow_orchestrator import get_workflow_orchestrator


class StartSampleSelectionPhaseUseCase(UseCase):
    """Start sample selection phase"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        start_data: SampleSelectionPhaseStartDTO,
        user_id: int,
        db: AsyncSession
    ) -> SampleSelectionPhaseStatusDTO:
        """Start the phase"""
        
        # Check if phase already exists
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id, WorkflowPhase.report_id == report_id, WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if phase:
            if phase.phase_status != 'Not Started':
                raise ValueError("Sample Selection phase has already been started")
        else:
            # Create new phase
            phase = WorkflowPhase(
                phase_id=str(uuid.uuid4()),
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started',
                phase_notes=start_data.phase_notes,
                default_sample_size=start_data.default_sample_size,
                selection_criteria=start_data.selection_criteria
            )
            db.add(phase)
        
        # Update phase
        phase.phase_status = 'In Progress'
        phase.started_by = user_id
        phase.started_at = datetime.utcnow()
        
        await db.commit()
        
        # Return status
        return await self._get_phase_status(phase, db)
    
    async def _get_phase_status(
        self,
        phase: WorkflowPhase,
        db: AsyncSession
    ) -> SampleSelectionPhaseStatusDTO:
        """Get phase status"""
        # Get total attributes
        attr_count = await db.execute(
            select(func.count(ReportAttribute.attribute_id))
            .where(
                and_(
                    ReportAttribute.cycle_id == phase.cycle_id,
                    ReportAttribute.report_id == phase.report_id,
                    ReportAttribute.is_primary_key == False
                )
            )
        )
        total_attributes = attr_count.scalar() or 0
        
        # Get sample set statistics
        stats = await db.execute(
            select(
                func.count(func.distinct(SampleSelectionVersion.attribute_id)).label('attrs_with_samples'),
                func.count(SampleSelectionVersion.sample_set_id).label('total_sets'),
                func.sum(func.cast(SampleSelectionVersion.status == SampleStatusEnum.APPROVED, int)).label('approved'),
                func.sum(func.cast(SampleSelectionVersion.status.in_([SampleStatusEnum.DRAFT, SampleStatusEnum.SELECTED]), int)).label('pending')
            ).where(
                and_(
                    SampleSelectionVersion.cycle_id == phase.cycle_id,
                    SampleSelectionVersion.report_id == phase.report_id
                )
            )
        )
        stats_row = stats.first()
        
        # Get total samples count
        sample_count = await db.execute(
            select(func.count(SampleSelectionSample.sample_id))
            .join(SampleSelectionVersion)
            .where(
                and_(
                    SampleSelectionVersion.cycle_id == phase.cycle_id,
                    SampleSelectionVersion.report_id == phase.report_id,
                    SampleSelectionSample.is_selected == True
                )
            )
        )
        total_samples = sample_count.scalar() or 0
        
        # Determine if phase can be completed
        can_complete = (
            total_attributes > 0 and
            stats_row.attrs_with_samples == total_attributes and
            stats_row.pending == 0
        )
        
        completion_requirements = []
        missing_attrs = total_attributes - (stats_row.attrs_with_samples or 0)
        if missing_attrs > 0:
            completion_requirements.append(f"Create sample sets for {missing_attrs} attributes")
        if stats_row.pending > 0:
            completion_requirements.append(f"Get approval for {stats_row.pending} sample sets")
        
        if not completion_requirements:
            completion_requirements.append("All requirements met - ready to complete phase")
        
        return SampleSelectionPhaseStatusDTO(
            phase_id=phase.phase_id,
            cycle_id=phase.cycle_id,
            report_id=phase.report_id,
            phase_status=phase.phase_status,
            total_attributes=total_attributes,
            attributes_with_samples=stats_row.attrs_with_samples or 0,
            total_sample_sets=stats_row.total_sets or 0,
            approved_sample_sets=stats_row.approved or 0,
            pending_approval=stats_row.pending or 0,
            total_samples_selected=total_samples,
            can_complete=can_complete,
            completion_requirements=completion_requirements
        )


class CreateSampleSelectionVersionUseCase(UseCase):
    """Create a sample set for an attribute"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        sample_set_data: SampleSelectionVersionCreateDTO,
        user_id: int,
        db: AsyncSession
    ) -> SampleSelectionVersionResponseDTO:
        """Create sample set"""
        
        # Get or create phase
        phase = await self._get_or_create_phase(cycle_id, report_id, db)
        
        # Get attribute details
        attr_result = await db.execute(
            select(ReportAttribute).where(
                and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.attribute_id == sample_set_data.attribute_id
                )
            )
        )
        attribute = attr_result.scalar_one_or_none()
        
        if not attribute:
            raise ValueError(f"Attribute {sample_set_data.attribute_id} not found")
        
        # Create sample set
        sample_set = SampleSelectionVersion(
            sample_set_id=str(uuid.uuid4()),
            phase_id=phase.phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            attribute_id=sample_set_data.attribute_id,
            attribute_name=attribute.attribute_name,
            sample_type=sample_set_data.sample_type,
            selection_method=sample_set_data.selection_method,
            target_sample_size=sample_set_data.target_sample_size,
            actual_sample_size=0,
            status=SampleStatusEnum.DRAFT,
            selection_criteria=sample_set_data.selection_criteria,
            risk_factors=sample_set_data.risk_factors,
            notes=sample_set_data.notes,
            created_by=user_id
        )
        
        db.add(sample_set)
        await db.commit()
        await db.refresh(sample_set)
        
        return self._to_response_dto(sample_set)
    
    async def _get_or_create_phase(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> WorkflowPhase:
        """Get or create sample selection phase"""
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id, WorkflowPhase.report_id == report_id, WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            phase = WorkflowPhase(
                phase_id=str(uuid.uuid4()),
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started'
            )
            db.add(phase)
            await db.commit()
        
        return phase
    
    def _to_response_dto(self, sample_set: SampleSelectionVersion) -> SampleSelectionVersionResponseDTO:
        """Convert sample set to response DTO"""
        return SampleSelectionVersionResponseDTO(
            sample_set_id=sample_set.sample_set_id,
            phase_id=sample_set.phase_id,
            cycle_id=sample_set.cycle_id,
            report_id=sample_set.report_id,
            attribute_id=sample_set.attribute_id,
            attribute_name=sample_set.attribute_name,
            sample_type=sample_set.sample_type,
            selection_method=sample_set.selection_method,
            target_sample_size=sample_set.target_sample_size,
            actual_sample_size=sample_set.actual_sample_size,
            status=sample_set.status,
            selection_criteria=sample_set.selection_criteria,
            risk_factors=sample_set.risk_factors,
            notes=sample_set.notes,
            created_by=sample_set.created_by,
            created_at=sample_set.created_at,
            approved_by=sample_set.approved_by,
            approved_at=sample_set.approved_at,
            rejection_reason=sample_set.rejection_reason
        )


class AddSampleSelectionSamplesUseCase(UseCase):
    """Add sample records to a sample set"""
    
    async def execute(
        self,
        sample_set_id: str,
        sample_records: List[SampleSelectionSampleCreateDTO],
        user_id: int,
        db: AsyncSession
    ) -> SampleSelectionVersionResponseDTO:
        """Add sample records"""
        
        # Get sample set
        result = await db.execute(
            select(SampleSelectionVersion).where(SampleSelectionVersion.sample_set_id == sample_set_id)
        )
        sample_set = result.scalar_one_or_none()
        
        if not sample_set:
            raise ValueError(f"Sample set {sample_set_id} not found")
        
        if sample_set.status != SampleStatusEnum.DRAFT:
            raise ValueError("Can only add samples to draft sample sets")
        
        # Add sample records
        created_records = []
        for record_data in sample_records:
            sample_record = SampleSelectionSample(
                sample_id=str(uuid.uuid4()),
                sample_set_id=sample_set_id,
                sample_identifier=record_data.sample_identifier,
                primary_key_values=record_data.primary_key_values,
                risk_score=record_data.risk_score,
                selection_reason=record_data.selection_reason,
                metadata=record_data.metadata,
                is_selected=True
            )
            db.add(sample_record)
            created_records.append(sample_record)
        
        # Update actual sample size
        sample_set.actual_sample_size = len(sample_records)
        sample_set.status = SampleStatusEnum.SELECTED
        
        await db.commit()
        
        # Refresh all records
        for record in created_records:
            await db.refresh(record)
        await db.refresh(sample_set)
        
        # Return sample set with records
        return SampleSelectionVersionResponseDTO(
            sample_set_id=sample_set.sample_set_id,
            phase_id=sample_set.phase_id,
            cycle_id=sample_set.cycle_id,
            report_id=sample_set.report_id,
            attribute_id=sample_set.attribute_id,
            attribute_name=sample_set.attribute_name,
            sample_type=sample_set.sample_type,
            selection_method=sample_set.selection_method,
            target_sample_size=sample_set.target_sample_size,
            actual_sample_size=sample_set.actual_sample_size,
            status=sample_set.status,
            selection_criteria=sample_set.selection_criteria,
            risk_factors=sample_set.risk_factors,
            notes=sample_set.notes,
            created_by=sample_set.created_by,
            created_at=sample_set.created_at,
            approved_by=sample_set.approved_by,
            approved_at=sample_set.approved_at,
            rejection_reason=sample_set.rejection_reason,
            sample_records=[self._record_to_dto(r) for r in created_records]
        )
    
    def _record_to_dto(self, record: SampleSelectionSample) -> SampleSelectionSampleResponseDTO:
        """Convert sample record to DTO"""
        return SampleSelectionSampleResponseDTO(
            sample_id=record.sample_id,
            sample_set_id=record.sample_set_id,
            sample_identifier=record.sample_identifier,
            primary_key_values=record.primary_key_values,
            risk_score=record.risk_score,
            selection_reason=record.selection_reason,
            metadata=record.metadata,
            is_selected=record.is_selected,
            created_at=record.created_at
        )


class AutoSelectSamplesUseCase(UseCase):
    """Automatically select samples for attributes"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        request_data: AutoSampleSelectionRequestDTO,
        user_id: int,
        db: AsyncSession
    ) -> List[SampleSelectionVersionResponseDTO]:
        """Auto-select samples"""
        
        # Get or create phase
        phase = await self._get_or_create_phase(cycle_id, report_id, db)
        
        created_sample_sets = []
        
        for attr_id in request_data.attributes:
            # Get attribute details
            attr_result = await db.execute(
                select(ReportAttribute).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.attribute_id == attr_id
                    )
                )
            )
            attribute = attr_result.scalar_one_or_none()
            
            if not attribute:
                continue
            
            # Create sample set
            sample_set = SampleSelectionVersion(
                sample_set_id=str(uuid.uuid4()),
                phase_id=phase.phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                attribute_id=attr_id,
                attribute_name=attribute.attribute_name,
                sample_type=SampleTypeEnum.RANDOM,
                selection_method=request_data.selection_method,
                target_sample_size=request_data.default_sample_size,
                actual_sample_size=0,
                status=SampleStatusEnum.DRAFT,
                selection_criteria={
                    "auto_selected": True,
                    "confidence_level": request_data.confidence_level
                },
                created_by=user_id
            )
            
            db.add(sample_set)
            
            # Auto-generate sample records (simplified for demo)
            sample_size = min(request_data.default_sample_size, 100)  # Cap at 100 for demo
            for i in range(sample_size):
                sample_record = SampleSelectionSample(
                    sample_id=str(uuid.uuid4()),
                    sample_set_id=sample_set.sample_set_id,
                    sample_identifier=f"AUTO-{attr_id}-{i+1:04d}",
                    primary_key_values={"auto_id": i+1, "attribute": attribute.attribute_name},
                    risk_score=random.uniform(0, 1) if request_data.apply_risk_factors else None,
                    selection_reason="Auto-selected based on configured criteria",
                    is_selected=True
                )
                db.add(sample_record)
            
            sample_set.actual_sample_size = sample_size
            sample_set.status = SampleStatusEnum.SELECTED
            
            created_sample_sets.append(sample_set)
        
        await db.commit()
        
        # Refresh all sample sets
        for ss in created_sample_sets:
            await db.refresh(ss)
        
        return [self._to_response_dto(ss) for ss in created_sample_sets]
    
    async def _get_or_create_phase(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> WorkflowPhase:
        """Get or create sample selection phase"""
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id, WorkflowPhase.report_id == report_id, WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            phase = WorkflowPhase(
                phase_id=str(uuid.uuid4()),
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started'
            )
            db.add(phase)
            await db.commit()
        
        return phase
    
    def _to_response_dto(self, sample_set: SampleSelectionVersion) -> SampleSelectionVersionResponseDTO:
        """Convert sample set to response DTO"""
        return SampleSelectionVersionResponseDTO(
            sample_set_id=sample_set.sample_set_id,
            phase_id=sample_set.phase_id,
            cycle_id=sample_set.cycle_id,
            report_id=sample_set.report_id,
            attribute_id=sample_set.attribute_id,
            attribute_name=sample_set.attribute_name,
            sample_type=sample_set.sample_type,
            selection_method=sample_set.selection_method,
            target_sample_size=sample_set.target_sample_size,
            actual_sample_size=sample_set.actual_sample_size,
            status=sample_set.status,
            selection_criteria=sample_set.selection_criteria,
            risk_factors=sample_set.risk_factors,
            notes=sample_set.notes,
            created_by=sample_set.created_by,
            created_at=sample_set.created_at,
            approved_by=sample_set.approved_by,
            approved_at=sample_set.approved_at,
            rejection_reason=sample_set.rejection_reason
        )


class ReviewSampleSelectionVersionUseCase(UseCase):
    """Review and approve/reject sample set"""
    
    async def execute(
        self,
        sample_set_id: str,
        review_data: SampleApprovalRequestDTO,
        user_id: int,
        db: AsyncSession
    ) -> SampleSelectionVersionResponseDTO:
        """Review sample set"""
        
        # Get sample set
        result = await db.execute(
            select(SampleSelectionVersion).where(SampleSelectionVersion.sample_set_id == sample_set_id)
        )
        sample_set = result.scalar_one_or_none()
        
        if not sample_set:
            raise ValueError(f"Sample set {sample_set_id} not found")
        
        if sample_set.status not in [SampleStatusEnum.SELECTED, SampleStatusEnum.DRAFT]:
            raise ValueError("Sample set must be in SELECTED or DRAFT status for review")
        
        # Update sample set
        if review_data.action == "approve":
            sample_set.status = SampleStatusEnum.APPROVED
            sample_set.approved_by = user_id
            sample_set.approved_at = datetime.utcnow()
        else:
            sample_set.status = SampleStatusEnum.REJECTED
            sample_set.rejection_reason = review_data.rejection_reason or "No reason provided"
        
        sample_set.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(sample_set)
        
        return self._to_response_dto(sample_set)
    
    def _to_response_dto(self, sample_set: SampleSelectionVersion) -> SampleSelectionVersionResponseDTO:
        """Convert sample set to response DTO"""
        return SampleSelectionVersionResponseDTO(
            sample_set_id=sample_set.sample_set_id,
            phase_id=sample_set.phase_id,
            cycle_id=sample_set.cycle_id,
            report_id=sample_set.report_id,
            attribute_id=sample_set.attribute_id,
            attribute_name=sample_set.attribute_name,
            sample_type=sample_set.sample_type,
            selection_method=sample_set.selection_method,
            target_sample_size=sample_set.target_sample_size,
            actual_sample_size=sample_set.actual_sample_size,
            status=sample_set.status,
            selection_criteria=sample_set.selection_criteria,
            risk_factors=sample_set.risk_factors,
            notes=sample_set.notes,
            created_by=sample_set.created_by,
            created_at=sample_set.created_at,
            approved_by=sample_set.approved_by,
            approved_at=sample_set.approved_at,
            rejection_reason=sample_set.rejection_reason
        )


class BulkReviewSampleSelectionVersionsUseCase(UseCase):
    """Bulk review multiple sample sets"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        bulk_data: BulkSampleApprovalRequestDTO,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Bulk review sample sets"""
        
        results = {
            "successful": [],
            "failed": []
        }
        
        for sample_set_id in bulk_data.sample_set_ids:
            try:
                # Get sample set
                result = await db.execute(
                    select(SampleSelectionVersion).where(
                        and_(
                            SampleSelectionVersion.sample_set_id == sample_set_id,
                            SampleSelectionVersion.cycle_id == cycle_id,
                            SampleSelectionVersion.report_id == report_id
                        )
                    )
                )
                sample_set = result.scalar_one_or_none()
                
                if not sample_set:
                    results["failed"].append({
                        "sample_set_id": sample_set_id,
                        "error": "Sample set not found"
                    })
                    continue
                
                if sample_set.status not in [SampleStatusEnum.SELECTED, SampleStatusEnum.DRAFT]:
                    results["failed"].append({
                        "sample_set_id": sample_set_id,
                        "error": f"Invalid status: {sample_set.status}"
                    })
                    continue
                
                # Update sample set
                if bulk_data.action == "approve":
                    sample_set.status = SampleStatusEnum.APPROVED
                    sample_set.approved_by = user_id
                    sample_set.approved_at = datetime.utcnow()
                else:
                    sample_set.status = SampleStatusEnum.REJECTED
                    sample_set.rejection_reason = bulk_data.review_notes or "Bulk rejection"
                
                sample_set.updated_at = datetime.utcnow()
                
                results["successful"].append({
                    "sample_set_id": sample_set_id,
                    "new_status": sample_set.status
                })
                
            except Exception as e:
                results["failed"].append({
                    "sample_set_id": sample_set_id,
                    "error": str(e)
                })
        
        await db.commit()
        
        return {
            "total_processed": len(bulk_data.sample_set_ids),
            "successful_count": len(results["successful"]),
            "failed_count": len(results["failed"]),
            "results": results
        }


class GetSampleSelectionPhaseStatusUseCase(UseCase):
    """Get sample selection phase status"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> SampleSelectionPhaseStatusDTO:
        """Get phase status"""
        
        # Get phase
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id, WorkflowPhase.report_id == report_id, WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            # Return default status
            return SampleSelectionPhaseStatusDTO(
                phase_id="",
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status="Not Started",
                total_attributes=0,
                attributes_with_samples=0,
                total_sample_sets=0,
                approved_sample_sets=0,
                pending_approval=0,
                total_samples_selected=0,
                can_complete=False,
                completion_requirements=["Phase not started"]
            )
        
        # Get total attributes
        attr_count = await db.execute(
            select(func.count(ReportAttribute.attribute_id))
            .where(
                and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_primary_key == False
                )
            )
        )
        total_attributes = attr_count.scalar() or 0
        
        # Get sample set statistics
        stats = await db.execute(
            select(
                func.count(func.distinct(SampleSelectionVersion.attribute_id)).label('attrs_with_samples'),
                func.count(SampleSelectionVersion.sample_set_id).label('total_sets'),
                func.sum(func.cast(SampleSelectionVersion.status == SampleStatusEnum.APPROVED, int)).label('approved'),
                func.sum(func.cast(SampleSelectionVersion.status.in_([SampleStatusEnum.DRAFT, SampleStatusEnum.SELECTED]), int)).label('pending')
            ).where(
                and_(
                    SampleSelectionVersion.cycle_id == cycle_id,
                    SampleSelectionVersion.report_id == report_id
                )
            )
        )
        stats_row = stats.first()
        
        # Get total samples count
        sample_count = await db.execute(
            select(func.count(SampleSelectionSample.sample_id))
            .join(SampleSelectionVersion)
            .where(
                and_(
                    SampleSelectionVersion.cycle_id == cycle_id,
                    SampleSelectionVersion.report_id == report_id,
                    SampleSelectionSample.is_selected == True
                )
            )
        )
        total_samples = sample_count.scalar() or 0
        
        # Determine if phase can be completed
        can_complete = (
            total_attributes > 0 and
            stats_row.attrs_with_samples == total_attributes and
            stats_row.pending == 0
        )
        
        completion_requirements = []
        missing_attrs = total_attributes - (stats_row.attrs_with_samples or 0)
        if missing_attrs > 0:
            completion_requirements.append(f"Create sample sets for {missing_attrs} attributes")
        if stats_row.pending > 0:
            completion_requirements.append(f"Get approval for {stats_row.pending} sample sets")
        
        if not completion_requirements:
            completion_requirements.append("All requirements met - ready to complete phase")
        
        return SampleSelectionPhaseStatusDTO(
            phase_id=phase.phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase.phase_status,
            total_attributes=total_attributes,
            attributes_with_samples=stats_row.attrs_with_samples or 0,
            total_sample_sets=stats_row.total_sets or 0,
            approved_sample_sets=stats_row.approved or 0,
            pending_approval=stats_row.pending or 0,
            total_samples_selected=total_samples,
            can_complete=can_complete,
            completion_requirements=completion_requirements
        )


class CompleteSampleSelectionPhaseUseCase(UseCase):
    """Complete sample selection phase"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        completion_data: PhaseCompletionRequestDTO,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Complete phase"""
        
        # Get phase
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id, WorkflowPhase.report_id == report_id, WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise ValueError("Sample Selection phase not found")
        
        if phase.phase_status == "Complete":
            raise ValueError("Phase is already complete")
        
        # Check completion requirements
        if not completion_data.override_checks:
            status_use_case = GetSampleSelectionPhaseStatusUseCase()
            status = await status_use_case.execute(cycle_id, report_id, db)
            
            if not status.can_complete:
                raise ValueError(
                    f"Cannot complete phase: {', '.join(status.completion_requirements)}"
                )
        
        # Update phase status
        phase.phase_status = "Complete"
        phase.completed_by = user_id
        phase.completed_at = datetime.utcnow()
        
        # Update workflow phase
        workflow_orchestrator = get_workflow_orchestrator()
        await workflow_orchestrator.complete_phase(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name="Sample Selection",
            db=db
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Sample Selection phase completed successfully",
            "phase_id": phase.phase_id,
            "completed_at": phase.completed_at
        }


class GetSampleStatisticsUseCase(UseCase):
    """Get sample statistics for an attribute"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        attribute_id: int,
        db: AsyncSession
    ) -> SampleStatisticsDTO:
        """Get statistics"""
        
        # Get total population (simplified - would need actual data source)
        total_population = 10000  # Placeholder
        
        # Get sample sets for attribute
        result = await db.execute(
            select(SampleSelectionVersion)
            .where(
                and_(
                    SampleSelectionVersion.cycle_id == cycle_id,
                    SampleSelectionVersion.report_id == report_id,
                    SampleSelectionVersion.attribute_id == attribute_id,
                    SampleSelectionVersion.status == SampleStatusEnum.APPROVED
                )
            )
        )
        sample_sets = result.scalars().all()
        
        total_samples = sum(ss.actual_sample_size for ss in sample_sets)
        coverage_percentage = (total_samples / total_population * 100) if total_population > 0 else 0
        
        # Calculate confidence level and margin of error (simplified)
        confidence_level = 0.95 if total_samples >= 30 else 0.90
        margin_of_error = 1.96 * math.sqrt((0.5 * 0.5) / total_samples) if total_samples > 0 else None
        
        # Risk coverage (placeholder)
        risk_coverage = {
            "high_risk": 0.85,
            "medium_risk": 0.70,
            "low_risk": 0.50
        }
        
        return SampleStatisticsDTO(
            total_population=total_population,
            sample_size=total_samples,
            coverage_percentage=coverage_percentage,
            confidence_level=confidence_level,
            margin_of_error=margin_of_error,
            risk_coverage=risk_coverage
        )


class GetSampleSelectionSummaryUseCase(UseCase):
    """Get sample selection summary for all attributes"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> List[SampleSelectionSummaryDTO]:
        """Get summary"""
        
        # Get all attributes with sample sets
        result = await db.execute(
            select(
                ReportAttribute.attribute_id,
                ReportAttribute.attribute_name,
                func.count(SampleSelectionVersion.sample_set_id).label('set_count'),
                func.sum(SampleSelectionVersion.actual_sample_size).label('total_samples'),
                func.max(SampleSelectionVersion.updated_at).label('last_updated')
            )
            .outerjoin(
                SampleSelectionVersion,
                and_(
                    SampleSelectionVersion.attribute_id == ReportAttribute.attribute_id,
                    SampleSelectionVersion.cycle_id == ReportAttribute.cycle_id,
                    SampleSelectionVersion.report_id == ReportAttribute.report_id
                )
            )
            .where(
                and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_primary_key == False
                )
            )
            .group_by(
                ReportAttribute.attribute_id,
                ReportAttribute.attribute_name
            )
        )
        
        summaries = []
        total_population = 10000  # Placeholder
        
        for row in result:
            # Determine status
            if row.set_count == 0:
                status = "No Samples"
            else:
                # Check if all approved
                approved_count = await db.execute(
                    select(func.count(SampleSelectionVersion.sample_set_id))
                    .where(
                        and_(
                            SampleSelectionVersion.cycle_id == cycle_id,
                            SampleSelectionVersion.report_id == report_id,
                            SampleSelectionVersion.attribute_id == row.attribute_id,
                            SampleSelectionVersion.status == SampleStatusEnum.APPROVED
                        )
                    )
                )
                approved = approved_count.scalar() or 0
                
                if approved == row.set_count:
                    status = "Approved"
                else:
                    status = "Pending Review"
            
            coverage = (row.total_samples / total_population * 100) if row.total_samples and total_population > 0 else 0
            
            summaries.append(SampleSelectionSummaryDTO(
                attribute_id=row.attribute_id,
                attribute_name=row.attribute_name,
                total_population=total_population,
                sample_sets_count=row.set_count or 0,
                total_samples=row.total_samples or 0,
                coverage_percentage=coverage,
                status=status,
                last_updated=row.last_updated or datetime.utcnow()
            ))
        
        return summaries


# Missing use cases for clean architecture compatibility

class GenerateSampleSelectionUseCase(UseCase):
    """Generate sample selection using LLM or manual process"""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    async def execute(self, cycle_id: int, report_id: int, request_data: Dict[str, Any], 
                     user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Generate sample selection with LLM support"""
        
        use_llm = request_data.get('use_llm', False)
        
        if use_llm and self.llm_service:
            # Get report details for context
            report_result = await db.execute(
                select(Report).where(Report.report_id == report_id)
            )
            report = report_result.scalar_one_or_none()
            
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            # Get scoped attributes
            attrs_result = await db.execute(
                select(ReportAttribute).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_scoped == True
                    )
                )
            )
            scoped_attributes = attrs_result.scalars().all()
            
            # Generate samples using LLM
            llm_response = await self.llm_service.generate_samples(
                report_id=report_id,
                sample_count=request_data.get('sample_count', 25),
                criteria={
                    "regulatory_context": report.regulation or 'General',
                    "attributes": [
                        {
                            "attribute_name": attr.attribute_name,
                            "data_type": attr.data_type,
                            "is_primary_key": attr.is_primary_key
                        }
                        for attr in scoped_attributes
                    ],
                    "risk_focus_areas": request_data.get('risk_focus_areas', []),
                    "sample_type": request_data.get('sample_type', 'Population Sample')
                }
            )
            
            # Create sample set with LLM-generated samples
            phase = await self._get_or_create_phase(cycle_id, report_id, db)
            
            sample_set = SampleSelectionVersion(
                set_id=str(uuid.uuid4()),
                cycle_id=cycle_id,
                report_id=report_id,
                set_name=f"LLM Generated - {report.regulation}",
                description=f"LLM-generated samples for {report.regulation}",
                generation_method='LLM Generated',
                sample_type=request_data.get('sample_type', 'Population Sample'),
                status='Draft',
                target_sample_size=request_data.get('sample_count', 25),
                actual_sample_size=len(llm_response),
                created_by=user_id,
                created_at=datetime.utcnow(),
                generation_rationale="Generated using LLM analysis",
                selection_criteria=request_data.get('selection_criteria', {}),
                quality_score=0.85,
                version_number=1,
                is_latest_version=True,
                is_active=True,
                version_created_at=datetime.utcnow(),
                version_created_by=user_id
            )
            
            db.add(sample_set)
            
            # Add sample records
            for i, sample_data in enumerate(llm_response):
                sample_record = SampleSelectionSample(
                    record_id=str(uuid.uuid4()),
                    set_id=sample_set.set_id,
                    sample_identifier=sample_data.get('sample_id', f"SAMPLE_{i+1:04d}"),
                    primary_key_value=str(sample_data.get('primary_key_value', i+1)),
                    sample_data=sample_data.get('sample_data', {}),
                    risk_score=sample_data.get('risk_score', 0.5),
                    validation_status='Needs Review',
                    selection_rationale=sample_data.get('testing_rationale', 'LLM-generated'),
                    created_at=datetime.utcnow(),
                    approval_status='Pending'
                )
                db.add(sample_record)
            
            await db.commit()
            await db.refresh(sample_set)
            
            return {
                'sample_sets': [{
                    'sample_set_id': sample_set.set_id,
                    'sample_count': len(llm_response),
                    'status': sample_set.status
                }],
                'status': 'Generated',
                'message': 'LLM sample generation completed successfully'
            }
        
        else:
            # Use AutoSelectSamplesUseCase for manual generation
            auto_select = AutoSelectSamplesUseCase()
            
            # Convert request format
            auto_request = AutoSampleSelectionRequestDTO(
                attributes=request_data.get('attribute_ids', []),
                default_sample_size=request_data.get('sample_count', 30),
                selection_method=SelectionMethodEnum.RANDOM,
                apply_risk_factors=request_data.get('apply_risk_factors', False),
                confidence_level=0.95
            )
            
            result = await auto_select.execute(cycle_id, report_id, auto_request, user_id, db)
            
            return {
                'sample_sets': [ss.dict() for ss in result],
                'status': 'Generated',
                'message': 'Sample selection generated successfully'
            }
    
    async def _get_or_create_phase(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> WorkflowPhase:
        """Get or create sample selection phase"""
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id, WorkflowPhase.report_id == report_id, WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            phase = WorkflowPhase(
                phase_id=str(uuid.uuid4()),
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='In Progress'
            )
            db.add(phase)
            await db.commit()
        
        return phase


class ApproveSampleSelectionUseCase(UseCase):
    """Approve sample selection"""
    
    async def execute(self, sample_set_id: str, request_data: Dict[str, Any], 
                     user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Approve sample selection - wrapper for ReviewSampleSelectionVersionUseCase"""
        # Use the existing ReviewSampleSelectionVersionUseCase
        review = ReviewSampleSelectionVersionUseCase()
        
        # Convert request format
        review_request = SampleApprovalRequestDTO(
            action='approve' if request_data.get('approved') else 'reject',
            review_notes=request_data.get('comments'),
            rejection_reason=request_data.get('comments') if not request_data.get('approved') else None
        )
        
        result = await review.execute(sample_set_id, review_request, user_id, db)
        
        return {
            'sample_set_id': sample_set_id,
            'status': 'Approved' if request_data.get('approved') else 'Rejected',
            'reviewed_by': user_id,
            'reviewed_at': datetime.utcnow()
        }


class UploadSampleDataUseCase(UseCase):
    """Upload sample data from file"""
    
    async def execute(self, cycle_id: int, report_id: int, file_data: Any, 
                     user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Process uploaded sample data from CSV/Excel file"""
        
        import pandas as pd
        import io
        
        # Extract file parameters
        file_content = file_data.get('content')
        filename = file_data.get('filename', 'uploaded_file.csv')
        primary_key_column = file_data.get('primary_key_column', 'transaction_id')
        sample_type = file_data.get('sample_type', 'Population Sample')
        
        # Validate file type
        if not filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise ValueError("Only CSV and Excel files are supported")
        
        # Parse file content
        try:
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(io.StringIO(file_content))
            else:
                df = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            raise ValueError(f"Failed to parse file: {str(e)}")
        
        total_rows = len(df)
        if total_rows == 0:
            raise ValueError("No data found in uploaded file")
        
        # Validate primary key column exists
        if primary_key_column not in df.columns:
            raise ValueError(f"Primary key column '{primary_key_column}' not found in file")
        
        # Data validation
        valid_rows = 0
        invalid_rows = 0
        validation_issues = []
        
        # Check for duplicate primary keys
        duplicates = df[df.duplicated(subset=[primary_key_column], keep=False)]
        if not duplicates.empty:
            validation_issues.append({
                "type": "Duplicate Primary Keys",
                "count": len(duplicates),
                "severity": "Error"
            })
            invalid_rows += len(duplicates)
        
        # Check for missing primary key values
        missing_pk = df[df[primary_key_column].isna()]
        if not missing_pk.empty:
            validation_issues.append({
                "type": "Missing Primary Key",
                "count": len(missing_pk),
                "severity": "Error"
            })
            invalid_rows += len(missing_pk)
        
        # Remove invalid rows
        df_valid = df.drop_duplicates(subset=[primary_key_column], keep='first')
        df_valid = df_valid.dropna(subset=[primary_key_column])
        valid_rows = len(df_valid)
        
        # Calculate data quality score
        data_quality_score = valid_rows / total_rows if total_rows > 0 else 0
        
        # Get or create phase
        phase_result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id, WorkflowPhase.report_id == report_id, WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            phase = WorkflowPhase(
                phase_id=str(uuid.uuid4()),
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='In Progress'
            )
            db.add(phase)
        
        # Create sample set
        sample_set = SampleSelectionVersion(
            set_id=str(uuid.uuid4()),
            cycle_id=cycle_id,
            report_id=report_id,
            set_name=f"Manual Upload - {filename}",
            description=f"Samples uploaded from {filename}",
            generation_method='Manual Upload',
            sample_type=sample_type,
            status='Draft',
            target_sample_size=valid_rows,
            actual_sample_size=valid_rows,
            created_by=user_id,
            created_at=datetime.utcnow(),
            generation_rationale=f"Manual upload from {filename}",
            quality_score=data_quality_score,
            sample_metadata={
                "upload_filename": filename,
                "primary_key_column": primary_key_column,
                "total_rows": total_rows,
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows,
                "validation_issues": validation_issues
            },
            version_number=1,
            is_latest_version=True,
            is_active=True,
            version_created_at=datetime.utcnow(),
            version_created_by=user_id
        )
        
        db.add(sample_set)
        
        # Create upload history record
        upload_history = SampleUploadHistory(
            upload_id=str(uuid.uuid4()),
            set_id=sample_set.set_id,
            upload_method='CSV' if filename.lower().endswith('.csv') else 'Excel',
            original_filename=filename,
            file_size_bytes=len(file_content.encode('utf-8')) if isinstance(file_content, str) else len(file_content),
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            primary_key_column=primary_key_column,
            data_mapping={
                "columns": list(df.columns),
                "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
            },
            validation_rules_applied={
                "unique_primary_key": True,
                "non_null_primary_key": True
            },
            data_quality_score=data_quality_score,
            upload_summary={
                "total_columns": len(df.columns),
                "validation_issues": validation_issues
            },
            processing_time_ms=0,  # Would be calculated in real implementation
            uploaded_by=user_id,
            uploaded_at=datetime.utcnow()
        )
        
        db.add(upload_history)
        
        # Create sample records
        for idx, row in df_valid.iterrows():
            sample_data = row.to_dict()
            primary_key_value = str(sample_data[primary_key_column])
            
            sample_record = SampleSelectionSample(
                record_id=str(uuid.uuid4()),
                set_id=sample_set.set_id,
                sample_identifier=f"UPLOAD_{idx+1:04d}",
                primary_key_value=primary_key_value,
                sample_data=sample_data,
                risk_score=None,  # Can be calculated later
                validation_status='Valid',
                validation_score=1.0,
                selection_rationale='Uploaded from file',
                data_source_info={
                    "source": "manual_upload",
                    "filename": filename,
                    "row_number": idx + 1
                },
                created_at=datetime.utcnow(),
                approval_status='Pending'
            )
            db.add(sample_record)
        
        await db.commit()
        await db.refresh(sample_set)
        
        return {
            'message': 'Sample data uploaded successfully',
            'status': 'Success',
            'samples_uploaded': valid_rows,
            'errors': validation_issues,
            'sample_set_id': sample_set.set_id,
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'invalid_rows': invalid_rows,
            'data_quality_score': data_quality_score
        }