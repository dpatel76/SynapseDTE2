"""
Sample Selection field mappers between models and DTOs
"""

from typing import Dict, Any, Optional
from app.models.sample_selection import SampleSet, SampleRecord
from app.application.dtos.sample_selection import (
    SampleSetResponseDTO,
    SampleRecordResponseDTO,
    SampleStatusEnum,
    SelectionMethodEnum
)


class SampleSelectionMapper:
    """Maps between SampleSet model and DTOs"""
    
    @staticmethod
    def model_to_dto(sample_set: SampleSet, phase_id: Optional[str] = None, 
                     attribute_id: Optional[int] = None, 
                     attribute_name: Optional[str] = None) -> SampleSetResponseDTO:
        """Convert SampleSet model to DTO"""
        # Map generation_method enum values to DTO's SelectionMethodEnum
        method_mapping = {
            'LLM Generated': SelectionMethodEnum.STATISTICAL,
            'Manual Upload': SelectionMethodEnum.MANUAL,
            'Hybrid': SelectionMethodEnum.RISK_BASED
        }
        
        # Map status enum values to DTO's SampleStatusEnum
        status_mapping = {
            'Draft': SampleStatusEnum.DRAFT,
            'Pending Approval': SampleStatusEnum.SELECTED,
            'Approved': SampleStatusEnum.APPROVED,
            'Rejected': SampleStatusEnum.REJECTED,
            'Revision Required': SampleStatusEnum.REJECTED
        }
        
        return SampleSetResponseDTO(
            sample_set_id=sample_set.set_id,
            phase_id=phase_id or "",
            cycle_id=sample_set.cycle_id,
            report_id=sample_set.report_id,
            attribute_id=attribute_id or 0,
            attribute_name=attribute_name or sample_set.set_name,
            sample_type=sample_set.sample_type,
            selection_method=method_mapping.get(sample_set.generation_method, SelectionMethodEnum.MANUAL),
            target_sample_size=sample_set.target_sample_size or 0,
            actual_sample_size=sample_set.actual_sample_size,
            status=status_mapping.get(sample_set.status, SampleStatusEnum.DRAFT),
            selection_criteria=sample_set.selection_criteria,
            risk_factors=None,  # Not available in model
            notes=sample_set.description,
            created_by=sample_set.created_by,
            created_at=sample_set.created_at,
            approved_by=sample_set.approved_by,
            approved_at=sample_set.approved_at,
            rejection_reason=sample_set.approval_notes
        )
    
    @staticmethod
    def record_to_dto(record: SampleRecord) -> SampleRecordResponseDTO:
        """Convert SampleRecord model to DTO"""
        return SampleRecordResponseDTO(
            sample_id=record.record_id,
            sample_set_id=record.set_id,
            sample_identifier=record.sample_identifier,
            primary_key_values={"value": record.primary_key_value},
            risk_score=record.risk_score,
            selection_reason=record.selection_rationale,
            metadata=record.data_source_info,
            is_selected=True,  # All records in DB are selected
            created_at=record.created_at
        )
    
    @staticmethod
    def dto_to_model_fields(dto_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DTO fields to model fields"""
        # Map DTO selection_method to model generation_method
        method_mapping = {
            'Random': 'Manual Upload',
            'Systematic': 'Manual Upload',
            'Risk-Based': 'Hybrid',
            'Statistical': 'LLM Generated',
            'Manual': 'Manual Upload'
        }
        
        model_fields = {
            'set_name': dto_data.get('attribute_name', 'Sample Set'),
            'description': dto_data.get('notes'),
            'generation_method': method_mapping.get(dto_data.get('selection_method'), 'Manual Upload'),
            'sample_type': dto_data.get('sample_type'),
            'target_sample_size': dto_data.get('target_sample_size'),
            'selection_criteria': dto_data.get('selection_criteria'),
            'status': 'Draft'  # Default status for new sets
        }
        
        return model_fields