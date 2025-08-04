"""SQLAlchemy implementation of SampleSelectionRepository"""
from typing import Any, Optional, List, Dict
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import uuid

from app.application.interfaces.repositories import ISampleSelectionRepository
from app.models.sample_selection import (
    SampleSet, SampleRecord, SampleValidationResult, SampleValidationIssue,
    SampleApprovalHistory, LLMSampleGeneration, SampleUploadHistory,
    SampleSelectionAuditLog
)
from app.models.sample_selection_phase import SampleSelectionPhase


class SQLAlchemySampleSelectionRepository(ISampleSelectionRepository):
    """SQLAlchemy implementation of the sample selection repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_sample_set(self, cycle_id: int, report_id: int, created_by: int, 
                               generation_method: str, sample_count: int) -> Any:
        """Create a new sample set"""
        # Get or create phase
        phase_result = await self.session.execute(
            select(SampleSelectionPhase).where(
                and_(
                    SampleSelectionPhase.cycle_id == cycle_id,
                    SampleSelectionPhase.report_id == report_id
                )
            )
        )
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            phase = SampleSelectionPhase(
                phase_id=str(uuid.uuid4()),
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='In Progress',
                started_by=created_by,
                started_at=datetime.utcnow()
            )
            self.session.add(phase)
        
        # Create sample set
        sample_set = SampleSet(
            sample_set_id=str(uuid.uuid4()),
            cycle_id=cycle_id,
            report_id=report_id,
            set_name=f"{generation_method} Sample Set",
            description=f"Sample set created via {generation_method}",
            generation_method=generation_method,
            sample_type='Population Sample',
            status='Draft',
            target_sample_size=sample_count,
            actual_sample_size=0,
            created_by=created_by,
            created_at=datetime.utcnow(),
            selection_criteria={},
            version_number=1,
            is_latest_version=True,
            is_active=True,
            version_created_at=datetime.utcnow(),
            version_created_by=created_by
        )
        
        self.session.add(sample_set)
        await self.session.commit()
        await self.session.refresh(sample_set)
        
        return sample_set
    
    async def get_sample_set(self, sample_set_id: str) -> Any:
        """Get sample set by ID"""
        result = await self.session.execute(
            select(SampleSet)
            .where(SampleSet.sample_set_id == sample_set_id)
            .options(
                selectinload(SampleSet.sample_records),
                selectinload(SampleSet.validation_results),
                selectinload(SampleSet.approval_history)
            )
        )
        return result.scalar_one_or_none()
    
    async def add_sample_record(self, sample_set_id: str, **kwargs) -> Any:
        """Add sample record to set"""
        # Get sample set
        sample_set = await self.get_sample_set(sample_set_id)
        if not sample_set:
            raise ValueError(f"Sample set {sample_set_id} not found")
        
        # Create sample record
        sample_record = SampleRecord(
            record_id=str(uuid.uuid4()),
            set_id=sample_set_id,
            sample_identifier=kwargs.get('sample_identifier', f"SAMPLE_{uuid.uuid4().hex[:8]}"),
            primary_key_value=kwargs.get('primary_key_value', ''),
            sample_data=kwargs.get('sample_data', {}),
            risk_score=kwargs.get('risk_score'),
            validation_status=kwargs.get('validation_status', 'Needs Review'),
            validation_score=kwargs.get('validation_score'),
            selection_rationale=kwargs.get('selection_rationale', ''),
            data_source_info=kwargs.get('data_source_info', {}),
            created_at=datetime.utcnow(),
            approval_status='Pending'
        )
        
        self.session.add(sample_record)
        
        # Update sample set actual size
        sample_set.actual_sample_size += 1
        
        await self.session.commit()
        await self.session.refresh(sample_record)
        
        return sample_record
    
    async def update_sample_set_status(self, sample_set_id: str, status: str, 
                                      reviewed_by: int, review_comments: Optional[str] = None) -> Any:
        """Update sample set status"""
        # Get sample set
        sample_set = await self.get_sample_set(sample_set_id)
        if not sample_set:
            raise ValueError(f"Sample set {sample_set_id} not found")
        
        # Update status
        previous_status = sample_set.status
        sample_set.status = status
        
        if status == 'Approved':
            sample_set.approved_by = reviewed_by
            sample_set.approved_at = datetime.utcnow()
            sample_set.approval_notes = review_comments
        elif status == 'Rejected':
            sample_set.rejection_reason = review_comments or 'No reason provided'
        
        # Create approval history
        approval_history = SampleApprovalHistory(
            approval_id=str(uuid.uuid4()),
            set_id=sample_set_id,
            approval_step='Review',
            decision=status,
            approved_by=reviewed_by,
            approved_at=datetime.utcnow(),
            feedback=review_comments,
            previous_status=previous_status,
            new_status=status
        )
        
        self.session.add(approval_history)
        
        await self.session.commit()
        await self.session.refresh(sample_set)
        
        return sample_set
    
    async def check_all_samples_approved(self, cycle_id: int, report_id: int) -> bool:
        """Check if all samples are approved for a cycle/report"""
        # Count total sample sets
        total_result = await self.session.execute(
            select(func.count(SampleSet.sample_set_id))
            .where(
                and_(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id,
                    SampleSet.is_active == True
                )
            )
        )
        total_count = total_result.scalar() or 0
        
        if total_count == 0:
            return False  # No samples exist
        
        # Count approved sample sets
        approved_result = await self.session.execute(
            select(func.count(SampleSet.sample_set_id))
            .where(
                and_(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id,
                    SampleSet.is_active == True,
                    SampleSet.status == 'Approved'
                )
            )
        )
        approved_count = approved_result.scalar() or 0
        
        return approved_count == total_count
    
    async def get_sample_sets_by_cycle_report(self, cycle_id: int, report_id: int) -> List[Any]:
        """Get all sample sets for a cycle/report"""
        result = await self.session.execute(
            select(SampleSet)
            .where(
                and_(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id,
                    SampleSet.is_active == True
                )
            )
            .order_by(SampleSet.created_at.desc())
        )
        return result.scalars().all()
    
    async def create_sample_validation_result(self, sample_set_id: str, validation_data: Dict[str, Any]) -> Any:
        """Create validation result for a sample set"""
        validation_result = SampleValidationResult(
            validation_id=str(uuid.uuid4()),
            set_id=sample_set_id,
            validation_type=validation_data.get('validation_type', 'Manual'),
            validation_rules=validation_data.get('validation_rules', {}),
            overall_status=validation_data.get('overall_status', 'Valid'),
            total_samples=validation_data.get('total_samples', 0),
            valid_samples=validation_data.get('valid_samples', 0),
            invalid_samples=validation_data.get('invalid_samples', 0),
            warning_samples=validation_data.get('warning_samples', 0),
            overall_quality_score=validation_data.get('overall_quality_score', 1.0),
            validation_summary=validation_data.get('validation_summary', {}),
            recommendations=validation_data.get('recommendations', []),
            validated_by=validation_data.get('validated_by'),
            validated_at=datetime.utcnow()
        )
        
        self.session.add(validation_result)
        await self.session.commit()
        await self.session.refresh(validation_result)
        
        return validation_result
    
    async def create_llm_generation_record(self, generation_data: Dict[str, Any]) -> Any:
        """Create LLM generation tracking record"""
        llm_generation = LLMSampleGeneration(
            generation_id=str(uuid.uuid4()),
            set_id=generation_data.get('set_id'),
            cycle_id=generation_data.get('cycle_id'),
            report_id=generation_data.get('report_id'),
            requested_sample_size=generation_data.get('requested_sample_size', 0),
            actual_samples_generated=generation_data.get('actual_samples_generated', 0),
            generation_prompt=generation_data.get('generation_prompt'),
            selection_criteria=generation_data.get('selection_criteria', {}),
            risk_focus_areas=generation_data.get('risk_focus_areas', []),
            exclude_criteria=generation_data.get('exclude_criteria', {}),
            include_edge_cases=generation_data.get('include_edge_cases', True),
            randomization_seed=generation_data.get('randomization_seed'),
            llm_model_used=generation_data.get('llm_model_used', 'Claude-3.5'),
            generation_rationale=generation_data.get('generation_rationale', ''),
            confidence_score=generation_data.get('confidence_score', 0.85),
            risk_coverage=generation_data.get('risk_coverage', {}),
            estimated_testing_time=generation_data.get('estimated_testing_time', 0),
            llm_metadata=generation_data.get('llm_metadata', {}),
            generated_by=generation_data.get('generated_by'),
            generated_at=datetime.utcnow()
        )
        
        self.session.add(llm_generation)
        await self.session.commit()
        await self.session.refresh(llm_generation)
        
        return llm_generation
    
    async def create_audit_log(self, cycle_id: int, report_id: int, action: str, 
                              entity_type: str, entity_id: str, user_id: int, 
                              old_values: Optional[Dict] = None, new_values: Optional[Dict] = None,
                              notes: Optional[str] = None) -> Any:
        """Create audit log entry"""
        audit_log = SampleSelectionAuditLog(
            audit_id=str(uuid.uuid4()),
            cycle_id=cycle_id,
            report_id=report_id,
            set_id=entity_id if entity_type == 'SampleSet' else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=user_id,
            performed_at=datetime.utcnow(),
            old_values=old_values,
            new_values=new_values,
            notes=notes
        )
        
        self.session.add(audit_log)
        await self.session.commit()
        
        return audit_log