"""
Observation Management use cases for clean architecture
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
import uuid

from app.application.use_cases.base import UseCase
from app.application.dtos.observation import (
    ObservationCreateDTO,
    ObservationResponseDTO,
    ObservationUpdateDTO,
    ImpactAssessmentCreateDTO,
    ImpactAssessmentResponseDTO,
    ObservationApprovalRequestDTO,
    ObservationApprovalResponseDTO,
    ObservationBatchReviewRequestDTO,
    ResolutionCreateDTO,
    ResolutionResponseDTO,
    ObservationPhaseStartDTO,
    ObservationPhaseStatusDTO,
    ObservationPhaseCompleteDTO,
    ObservationAnalyticsDTO,
    AutoDetectionRequestDTO
)
from app.models.observation_management import (
    ObservationTypeEnum,
    ObservationSeverityEnum,
    ObservationStatusEnum,
    ImpactCategoryEnum,
    ResolutionStatusEnum
)
from app.models import (
    ObservationRecord,
    ObservationImpactAssessment,
    ObservationResolution,
    TestExecution,
    WorkflowPhase
)
from app.models.report_attribute import ReportAttribute
from app.services.workflow_orchestrator import get_workflow_orchestrator


class CreateObservationUseCase(UseCase):
    """Create a new observation"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        observation_data: ObservationCreateDTO,
        user_id: int,
        db: AsyncSession
    ) -> ObservationResponseDTO:
        """Execute observation creation"""
        
        # Get or create observation phase
        phase = await self._get_or_create_phase(cycle_id, report_id, db)
        
        # Check for existing observations with same attribute and observation type
        if observation_data.source_attribute_id and observation_data.test_execution_id:
            existing_observation = await self._find_similar_observation(
                db,
                phase.phase_id,
                observation_data.source_attribute_id,
                observation_data.observation_type,
                observation_data.observation_description
            )
            
            if existing_observation:
                # Link the test execution to the existing observation
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Found existing observation {existing_observation.observation_id} for attribute {observation_data.source_attribute_id}")
                
                # Update the test execution ID if provided
                # Note: We'll store the test execution IDs in the supporting_data field
                if not existing_observation.supporting_data:
                    existing_observation.supporting_data = {}
                    
                if 'linked_test_executions' not in existing_observation.supporting_data:
                    existing_observation.supporting_data['linked_test_executions'] = []
                    
                if observation_data.test_execution_id not in existing_observation.supporting_data['linked_test_executions']:
                    existing_observation.supporting_data['linked_test_executions'].append(observation_data.test_execution_id)
                    
                # Update the grouped count
                if 'grouped_count' not in existing_observation.supporting_data:
                    existing_observation.supporting_data['grouped_count'] = 1
                existing_observation.supporting_data['grouped_count'] += 1
                
                # Update modification timestamps
                existing_observation.updated_at = datetime.utcnow()
                existing_observation.updated_by_id = user_id
                
                db.add(existing_observation)
                await db.commit()
                await db.refresh(existing_observation)
                
                # Load the phase and resolutions relationships
                result = await db.execute(
                    select(ObservationRecord)
                    .options(
                        selectinload(ObservationRecord.phase),
                        selectinload(ObservationRecord.resolutions)
                    )
                    .where(ObservationRecord.observation_id == existing_observation.observation_id)
                )
                existing_observation = result.scalar_one()
                
                return self._to_response_dto(existing_observation)
        
        # Generate observation number
        count_result = await db.execute(
            select(func.count(ObservationRecord.observation_id))
            .where(
                ObservationRecord.phase_id == phase.phase_id
            )
        )
        count = count_result.scalar() or 0
        observation_number = f"OBS-{cycle_id}-{report_id}-{count + 1:04d}"
        
        # Create observation
        try:
            # Convert string values to enum if needed
            obs_type = observation_data.observation_type
            if isinstance(obs_type, str):
                obs_type = ObservationTypeEnum[obs_type.replace(' ', '_').upper()]
            
            severity = observation_data.severity
            if isinstance(severity, str):
                # Map common severity names to expected enum values
                severity_map = {
                    'CRITICAL': 'CRITICAL',
                    'HIGH': 'HIGH', 
                    'MEDIUM': 'MEDIUM',
                    'LOW': 'LOW',
                    'INFORMATIONAL': 'INFORMATIONAL',
                    # Also handle lowercase/mixed case
                    'Critical': 'CRITICAL',
                    'High': 'HIGH',
                    'Medium': 'MEDIUM', 
                    'Low': 'LOW',
                    'Informational': 'INFORMATIONAL'
                }
                mapped_severity = severity_map.get(severity, severity.upper())
                severity = ObservationSeverityEnum[mapped_severity]
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error converting enums: {e}")
            logger.error(f"Observation type: {observation_data.observation_type}, Severity: {observation_data.severity}")
            raise
            
        observation = ObservationRecord(
            phase_id=phase.phase_id,
            observation_title=observation_data.observation_title,
            observation_description=observation_data.observation_description,
            observation_type=obs_type,
            severity=severity,
            status=ObservationStatusEnum.DETECTED,
            source_attribute_id=observation_data.source_attribute_id if observation_data.source_attribute_id else None,
            source_sample_record_id=getattr(observation_data, 'source_sample_id', None),
            source_test_execution_id=getattr(observation_data, 'test_execution_id', None) and int(getattr(observation_data, 'test_execution_id', 0)) or None,
            detection_method=getattr(observation_data, 'detection_method', 'Manual'),
            detection_confidence=getattr(observation_data, 'detection_confidence', None),
            impact_description=getattr(observation_data, 'impact_description', None),
            impact_categories=getattr(observation_data, 'impact_categories', None),
            financial_impact_estimate=getattr(observation_data, 'financial_impact_estimate', None),
            regulatory_risk_level=getattr(observation_data, 'regulatory_risk_level', None),
            affected_processes=getattr(observation_data, 'affected_processes', None),
            affected_systems=getattr(observation_data, 'affected_systems', None),
            evidence_documents=getattr(observation_data, 'evidence_documents', None),
            supporting_data=getattr(observation_data, 'supporting_data', None),
            screenshots=getattr(observation_data, 'screenshots', None),
            related_observations=getattr(observation_data, 'related_observations', None),
            detected_by=user_id,
            assigned_to=getattr(observation_data, 'assigned_to', None),
            created_by_id=user_id,
            updated_by_id=user_id
        )
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Created observation object with phase_id={phase.phase_id}, type={obs_type}, severity={severity}")
        
        try:
            db.add(observation)
            await db.commit()
            await db.refresh(observation)
            
            # Load the phase and resolutions relationships to get cycle_id and report_id
            result = await db.execute(
                select(ObservationRecord)
                .options(
                    selectinload(ObservationRecord.phase),
                    selectinload(ObservationRecord.resolutions)
                )
                .where(ObservationRecord.observation_id == observation.observation_id)
            )
            observation = result.scalar_one()
        except Exception as e:
            logger.error(f"Error saving observation: {e}")
            raise
        
        return self._to_response_dto(observation)
    
    async def _get_or_create_phase(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> WorkflowPhase:
        """Get or create observation management phase"""
        result = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Observations"
            ))
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            phase = WorkflowPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Observations",
                status='Not Started'
            )
            db.add(phase)
            await db.commit()
        
        return phase
    
    async def _find_similar_observation(
        self,
        db: AsyncSession,
        phase_id: int,
        attribute_id: Optional[int],
        observation_type: ObservationTypeEnum,
        description: str
    ) -> Optional[ObservationRecord]:
        """Find similar observation for grouping"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Convert observation type to enum if it's a string
        if isinstance(observation_type, str):
            try:
                observation_type = ObservationTypeEnum[observation_type.replace(' ', '_').upper()]
            except Exception as e:
                logger.error(f"Failed to convert observation type '{observation_type}' to enum: {e}")
                # Default to DATA_QUALITY if conversion fails
                observation_type = ObservationTypeEnum.DATA_QUALITY
        
        logger.info(f"Finding similar observation: phase_id={phase_id}, attribute_id={attribute_id}, type={observation_type}")
            
        query = select(ObservationRecord).where(
            and_(
                ObservationRecord.phase_id == phase_id,
                ObservationRecord.observation_type == observation_type,
                ObservationRecord.status.notin_([ObservationStatusEnum.RESOLVED, ObservationStatusEnum.CLOSED])
            )
        )
        
        if attribute_id:
            query = query.where(ObservationRecord.source_attribute_id == attribute_id)
        
        result = await db.execute(query)
        observations = result.scalars().all()
        
        logger.info(f"Found {len(observations)} observations matching criteria")
        for obs in observations:
            logger.info(f"  - Observation {obs.observation_id}: type={obs.observation_type} (value={obs.observation_type.value if obs.observation_type else 'None'}), attribute_id={obs.source_attribute_id}")
        
        # For observations with the same attribute and type, consider them similar
        # This handles cases where multiple test failures are for the same data quality issue
        if observations and attribute_id:
            # Return the first non-resolved observation for this attribute
            logger.info(f"Returning existing observation {observations[0].observation_id} for grouping")
            return observations[0]
        
        # If no attribute match, check for similar descriptions
        description_lower = description.lower()
        keywords = ['mismatch', 'incorrect', 'missing', 'invalid', 'failed', 'does not match']
        
        for obs in observations:
            obs_text = f"{obs.observation_title} {obs.observation_description}".lower()
            # Check if observations are about similar issues
            if any(keyword in description_lower and keyword in obs_text for keyword in keywords):
                # Additional check for data type similarity
                if 'current credit limit' in description_lower and 'current credit limit' in obs_text:
                    return obs
                elif 'customer id' in description_lower and 'customer id' in obs_text:
                    return obs
                # Add more specific matching rules as needed
        
        return None
    
    def _to_response_dto(self, observation: ObservationRecord) -> ObservationResponseDTO:
        """Convert observation model to response DTO"""
        # Convert enums to their string values for DTO compatibility
        obs_type_value = observation.observation_type.value if observation.observation_type and hasattr(observation.observation_type, 'value') else str(observation.observation_type) if observation.observation_type else "DATA_QUALITY"
        severity_value = observation.severity.value if observation.severity and hasattr(observation.severity, 'value') else str(observation.severity) if observation.severity else "MEDIUM"
        status_value = observation.status.value if observation.status and hasattr(observation.status, 'value') else str(observation.status) if observation.status else "DETECTED"
        
        # Get grouped count from supporting_data
        grouped_count = 1
        if observation.supporting_data and isinstance(observation.supporting_data, dict):
            grouped_count = observation.supporting_data.get('grouped_count', 1)
        
        # Get resolution status if resolution exists
        resolution_status = None
        if hasattr(observation, 'resolutions') and observation.resolutions:
            # Get the first resolution's status
            resolution_status = observation.resolutions[0].resolution_status.value if observation.resolutions[0].resolution_status else None
        
        return ObservationResponseDTO(
            observation_id=str(observation.observation_id),
            phase_id=str(observation.phase_id),
            cycle_id=observation.cycle_id,
            report_id=observation.report_id,
            observation_number=f"OBS-{observation.cycle_id}-{observation.report_id}-{observation.observation_id:04d}",
            observation_title=observation.observation_title,
            observation_description=observation.observation_description,
            observation_type=obs_type_value,
            severity=severity_value,
            status=status_value,
            source_attribute_id=observation.source_attribute_id,
            source_sample_id=observation.source_sample_record_id,
            test_execution_id=str(observation.source_test_execution_id) if observation.source_test_execution_id else None,
            grouped_count=grouped_count,
            supporting_data=observation.supporting_data,
            created_by=observation.created_by_id or observation.detected_by,
            created_at=observation.created_at,
            updated_at=observation.updated_at,
            submitted_at=getattr(observation, 'submitted_at', None),
            reviewed_by=getattr(observation, 'reviewed_by', None),
            reviewed_at=getattr(observation, 'reviewed_at', None),
            resolution_status=resolution_status
        )


class GetObservationUseCase(UseCase):
    """Get observation details"""
    
    async def execute(
        self,
        observation_id: str,
        db: AsyncSession
    ) -> ObservationResponseDTO:
        """Get observation by ID"""
        result = await db.execute(
            select(ObservationRecord)
            .options(selectinload(ObservationRecord.resolution))
            .where(ObservationRecord.observation_id == observation_id)
        )
        observation = result.scalar_one_or_none()
        
        if not observation:
            raise ValueError(f"Observation {observation_id} not found")
        
        return self._to_response_dto(observation)
    
    def _to_response_dto(self, observation: ObservationRecord) -> ObservationResponseDTO:
        """Convert observation model to response DTO"""
        # Convert enums to their string values for DTO compatibility
        obs_type_value = observation.observation_type.value if observation.observation_type and hasattr(observation.observation_type, 'value') else str(observation.observation_type) if observation.observation_type else "DATA_QUALITY"
        severity_value = observation.severity.value if observation.severity and hasattr(observation.severity, 'value') else str(observation.severity) if observation.severity else "MEDIUM"
        status_value = observation.status.value if observation.status and hasattr(observation.status, 'value') else str(observation.status) if observation.status else "DETECTED"
        
        # Get grouped count from supporting_data
        grouped_count = 1
        if observation.supporting_data and isinstance(observation.supporting_data, dict):
            grouped_count = observation.supporting_data.get('grouped_count', 1)
        
        # Get resolution status if resolution exists
        resolution_status = None
        if hasattr(observation, 'resolutions') and observation.resolutions:
            # Get the first resolution's status
            resolution_status = observation.resolutions[0].resolution_status.value if observation.resolutions[0].resolution_status else None
        
        return ObservationResponseDTO(
            observation_id=str(observation.observation_id),
            phase_id=str(observation.phase_id),
            cycle_id=observation.cycle_id,
            report_id=observation.report_id,
            observation_number=f"OBS-{observation.cycle_id}-{observation.report_id}-{observation.observation_id:04d}",
            observation_title=observation.observation_title,
            observation_description=observation.observation_description,
            observation_type=obs_type_value,
            severity=severity_value,
            status=status_value,
            source_attribute_id=observation.source_attribute_id,
            source_sample_id=observation.source_sample_record_id,
            test_execution_id=str(observation.source_test_execution_id) if observation.source_test_execution_id else None,
            grouped_count=grouped_count,
            supporting_data=observation.supporting_data,
            created_by=observation.created_by_id or observation.detected_by,
            created_at=observation.created_at,
            updated_at=observation.updated_at,
            submitted_at=getattr(observation, 'submitted_at', None),
            reviewed_by=getattr(observation, 'reviewed_by', None),
            reviewed_at=getattr(observation, 'reviewed_at', None),
            resolution_status=resolution_status
        )


class ListObservationsUseCase(UseCase):
    """List observations for a cycle/report"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        status: Optional[ObservationStatusEnum],
        severity: Optional[ObservationSeverityEnum],
        observation_type: Optional[ObservationTypeEnum],
        db: AsyncSession
    ) -> List[ObservationResponseDTO]:
        """List observations with filters"""
        # Get phase_id for this cycle and report
        phase_result = await db.execute(
            select(WorkflowPhase.phase_id)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Observations"
            ))
        )
        phase_id = phase_result.scalar_one_or_none()
        
        if not phase_id:
            return []
            
        query = select(ObservationRecord).options(
            selectinload(ObservationRecord.phase),
            selectinload(ObservationRecord.resolutions)
        ).where(
            ObservationRecord.phase_id == phase_id
        )
        
        if status:
            query = query.where(ObservationRecord.status == status)
        if severity:
            query = query.where(ObservationRecord.severity == severity)
        if observation_type:
            query = query.where(ObservationRecord.observation_type == observation_type)
        
        query = query.order_by(desc(ObservationRecord.created_at))
        
        result = await db.execute(query)
        observations = result.scalars().all()
        
        return [self._to_response_dto(obs) for obs in observations]
    
    def _to_response_dto(self, observation: ObservationRecord) -> ObservationResponseDTO:
        """Convert observation model to response DTO"""
        # Convert enums to their string values for DTO compatibility
        obs_type_value = observation.observation_type.value if observation.observation_type and hasattr(observation.observation_type, 'value') else str(observation.observation_type) if observation.observation_type else "DATA_QUALITY"
        severity_value = observation.severity.value if observation.severity and hasattr(observation.severity, 'value') else str(observation.severity) if observation.severity else "MEDIUM"
        status_value = observation.status.value if observation.status and hasattr(observation.status, 'value') else str(observation.status) if observation.status else "DETECTED"
        
        # Get grouped count from supporting_data
        grouped_count = 1
        if observation.supporting_data and isinstance(observation.supporting_data, dict):
            grouped_count = observation.supporting_data.get('grouped_count', 1)
        
        # Get resolution status if resolution exists
        resolution_status = None
        if hasattr(observation, 'resolutions') and observation.resolutions:
            # Get the first resolution's status
            resolution_status = observation.resolutions[0].resolution_status.value if observation.resolutions[0].resolution_status else None
        
        return ObservationResponseDTO(
            observation_id=str(observation.observation_id),
            phase_id=str(observation.phase_id),
            cycle_id=observation.cycle_id,
            report_id=observation.report_id,
            observation_number=f"OBS-{observation.cycle_id}-{observation.report_id}-{observation.observation_id:04d}",
            observation_title=observation.observation_title,
            observation_description=observation.observation_description,
            observation_type=obs_type_value,
            severity=severity_value,
            status=status_value,
            source_attribute_id=observation.source_attribute_id,
            source_sample_id=observation.source_sample_record_id,
            test_execution_id=str(observation.source_test_execution_id) if observation.source_test_execution_id else None,
            grouped_count=grouped_count,
            supporting_data=observation.supporting_data,
            created_by=observation.created_by_id or observation.detected_by,
            created_at=observation.created_at,
            updated_at=observation.updated_at,
            submitted_at=getattr(observation, 'submitted_at', None),
            reviewed_by=getattr(observation, 'reviewed_by', None),
            reviewed_at=getattr(observation, 'reviewed_at', None),
            resolution_status=resolution_status
        )


class UpdateObservationUseCase(UseCase):
    """Update an observation"""
    
    async def execute(
        self,
        observation_id: str,
        update_data: ObservationUpdateDTO,
        user_id: int,
        db: AsyncSession
    ) -> ObservationResponseDTO:
        """Update observation"""
        result = await db.execute(
            select(ObservationRecord)
            .where(ObservationRecord.observation_id == observation_id)
        )
        observation = result.scalar_one_or_none()
        
        if not observation:
            raise ValueError(f"Observation {observation_id} not found")
        
        # Check if observation can be updated
        if observation.status not in [ObservationStatusEnum.DETECTED, ObservationStatusEnum.REJECTED]:
            raise ValueError(f"Cannot update observation in {observation.status} status")
        
        # Update fields
        if hasattr(update_data, 'observation_title') and update_data.observation_title is not None:
            observation.observation_title = update_data.observation_title
        if hasattr(update_data, 'observation_description') and update_data.observation_description is not None:
            observation.observation_description = update_data.observation_description
        if hasattr(update_data, 'severity') and update_data.severity is not None:
            observation.severity = update_data.severity
        if hasattr(update_data, 'impact_description') and update_data.impact_description is not None:
            observation.impact_description = update_data.impact_description
        if hasattr(update_data, 'financial_impact_estimate') and update_data.financial_impact_estimate is not None:
            observation.financial_impact_estimate = update_data.financial_impact_estimate
        if hasattr(update_data, 'supporting_data') and update_data.supporting_data is not None:
            observation.supporting_data = update_data.supporting_data
        
        observation.updated_at = datetime.utcnow()
        observation.updated_by = user_id
        
        await db.commit()
        await db.refresh(observation)
        
        return self._to_response_dto(observation)
    
    def _to_response_dto(self, observation: ObservationRecord) -> ObservationResponseDTO:
        """Convert observation model to response DTO"""
        # Convert enums to their string values for DTO compatibility
        obs_type_value = observation.observation_type.value if observation.observation_type and hasattr(observation.observation_type, 'value') else str(observation.observation_type) if observation.observation_type else "DATA_QUALITY"
        severity_value = observation.severity.value if observation.severity and hasattr(observation.severity, 'value') else str(observation.severity) if observation.severity else "MEDIUM"
        status_value = observation.status.value if observation.status and hasattr(observation.status, 'value') else str(observation.status) if observation.status else "DETECTED"
        
        # Get grouped count from supporting_data
        grouped_count = 1
        if observation.supporting_data and isinstance(observation.supporting_data, dict):
            grouped_count = observation.supporting_data.get('grouped_count', 1)
        
        # Get resolution status if resolution exists
        resolution_status = None
        if hasattr(observation, 'resolutions') and observation.resolutions:
            # Get the first resolution's status
            resolution_status = observation.resolutions[0].resolution_status.value if observation.resolutions[0].resolution_status else None
        
        return ObservationResponseDTO(
            observation_id=str(observation.observation_id),
            phase_id=str(observation.phase_id),
            cycle_id=observation.cycle_id,
            report_id=observation.report_id,
            observation_number=f"OBS-{observation.cycle_id}-{observation.report_id}-{observation.observation_id:04d}",
            observation_title=observation.observation_title,
            observation_description=observation.observation_description,
            observation_type=obs_type_value,
            severity=severity_value,
            status=status_value,
            source_attribute_id=observation.source_attribute_id,
            source_sample_id=observation.source_sample_record_id,
            test_execution_id=str(observation.source_test_execution_id) if observation.source_test_execution_id else None,
            grouped_count=grouped_count,
            supporting_data=observation.supporting_data,
            created_by=observation.created_by_id or observation.detected_by,
            created_at=observation.created_at,
            updated_at=observation.updated_at,
            submitted_at=getattr(observation, 'submitted_at', None),
            reviewed_by=getattr(observation, 'reviewed_by', None),
            reviewed_at=getattr(observation, 'reviewed_at', None),
            resolution_status=resolution_status
        )


class SubmitObservationUseCase(UseCase):
    """Submit observation for review"""
    
    async def execute(
        self,
        observation_id: str,
        user_id: int,
        db: AsyncSession
    ) -> ObservationResponseDTO:
        """Submit observation"""
        result = await db.execute(
            select(ObservationRecord)
            .where(ObservationRecord.observation_id == observation_id)
        )
        observation = result.scalar_one_or_none()
        
        if not observation:
            raise ValueError(f"Observation {observation_id} not found")
        
        if observation.status != ObservationStatusEnum.DETECTED:
            raise ValueError(f"Can only submit observations in DETECTED status")
        
        observation.status = ObservationStatusEnum.SUBMITTED
        observation.submitted_at = datetime.utcnow()
        observation.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(observation)
        
        return self._to_response_dto(observation)
    
    def _to_response_dto(self, observation: ObservationRecord) -> ObservationResponseDTO:
        """Convert observation model to response DTO"""
        # Convert enums to their string values for DTO compatibility
        obs_type_value = observation.observation_type.value if observation.observation_type and hasattr(observation.observation_type, 'value') else str(observation.observation_type) if observation.observation_type else "DATA_QUALITY"
        severity_value = observation.severity.value if observation.severity and hasattr(observation.severity, 'value') else str(observation.severity) if observation.severity else "MEDIUM"
        status_value = observation.status.value if observation.status and hasattr(observation.status, 'value') else str(observation.status) if observation.status else "DETECTED"
        
        # Get grouped count from supporting_data
        grouped_count = 1
        if observation.supporting_data and isinstance(observation.supporting_data, dict):
            grouped_count = observation.supporting_data.get('grouped_count', 1)
        
        # Get resolution status if resolution exists
        resolution_status = None
        if hasattr(observation, 'resolutions') and observation.resolutions:
            # Get the first resolution's status
            resolution_status = observation.resolutions[0].resolution_status.value if observation.resolutions[0].resolution_status else None
        
        return ObservationResponseDTO(
            observation_id=str(observation.observation_id),
            phase_id=str(observation.phase_id),
            cycle_id=observation.cycle_id,
            report_id=observation.report_id,
            observation_number=f"OBS-{observation.cycle_id}-{observation.report_id}-{observation.observation_id:04d}",
            observation_title=observation.observation_title,
            observation_description=observation.observation_description,
            observation_type=obs_type_value,
            severity=severity_value,
            status=status_value,
            source_attribute_id=observation.source_attribute_id,
            source_sample_id=observation.source_sample_record_id,
            test_execution_id=str(observation.source_test_execution_id) if observation.source_test_execution_id else None,
            grouped_count=grouped_count,
            supporting_data=observation.supporting_data,
            created_by=observation.created_by_id or observation.detected_by,
            created_at=observation.created_at,
            updated_at=observation.updated_at,
            submitted_at=getattr(observation, 'submitted_at', None),
            reviewed_by=getattr(observation, 'reviewed_by', None),
            reviewed_at=getattr(observation, 'reviewed_at', None),
            resolution_status=resolution_status
        )


class ReviewObservationUseCase(UseCase):
    """Review and approve/reject observation"""
    
    async def execute(
        self,
        observation_id: str,
        review_data: ObservationApprovalRequestDTO,
        user_id: int,
        db: AsyncSession
    ) -> ObservationApprovalResponseDTO:
        """Review observation"""
        result = await db.execute(
            select(ObservationRecord)
            .where(ObservationRecord.observation_id == observation_id)
        )
        observation = result.scalar_one_or_none()
        
        if not observation:
            raise ValueError(f"Observation {observation_id} not found")
        
        if observation.status not in [ObservationStatusEnum.SUBMITTED, ObservationStatusEnum.UNDER_REVIEW]:
            raise ValueError(f"Observation must be in SUBMITTED or UNDER_REVIEW status")
        
        # Update observation with approval data
        if review_data.action == "approve":
            observation.status = ObservationStatusEnum.APPROVED
            decision = "Approved"
        else:
            observation.status = ObservationStatusEnum.REJECTED
            decision = "Rejected"
        
        # Update tester decision fields
        observation.tester_decision = decision
        observation.tester_comments = review_data.review_notes
        observation.tester_decision_by_id = user_id
        observation.tester_decision_at = datetime.utcnow()
        observation.approval_status = f"{decision} by Tester"
        observation.require_remediation = review_data.require_remediation
        observation.target_resolution_date = review_data.target_resolution_date
        
        observation.reviewed_by = user_id
        observation.reviewed_at = datetime.utcnow()
        observation.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return ObservationApprovalResponseDTO(
            approval_id=str(uuid.uuid4()),  # Generate a new ID for compatibility
            observation_id=observation.observation_id,
            reviewed_by=user_id,
            review_decision=review_data.action,
            review_notes=review_data.review_notes,
            reviewed_at=observation.reviewed_at,
            require_remediation=observation.require_remediation,
            target_resolution_date=observation.target_resolution_date
        )


class BatchReviewObservationsUseCase(UseCase):
    """Batch review multiple observations"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        batch_data: ObservationBatchReviewRequestDTO,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Batch review observations"""
        results = {
            "successful": [],
            "failed": []
        }
        
        for obs_id in batch_data.observation_ids:
            try:
                # Get observation
                result = await db.execute(
                    select(ObservationRecord)
                    .where(and_(
                        ObservationRecord.observation_id == obs_id,
                        ObservationRecord.cycle_id == cycle_id,
                        ObservationRecord.report_id == report_id
                    ))
                )
                observation = result.scalar_one_or_none()
                
                if not observation:
                    results["failed"].append({
                        "observation_id": obs_id,
                        "error": "Observation not found"
                    })
                    continue
                
                if observation.status not in [ObservationStatusEnum.SUBMITTED, ObservationStatusEnum.UNDER_REVIEW]:
                    results["failed"].append({
                        "observation_id": obs_id,
                        "error": f"Invalid status: {observation.status}"
                    })
                    continue
                
                # Update observation with approval data
                if batch_data.action == "approve":
                    observation.status = ObservationStatusEnum.APPROVED
                    decision = "Approved"
                else:
                    observation.status = ObservationStatusEnum.REJECTED
                    decision = "Rejected"
                
                # Update tester decision fields
                observation.tester_decision = decision
                observation.tester_comments = batch_data.review_notes
                observation.tester_decision_by_id = user_id
                observation.tester_decision_at = datetime.utcnow()
                observation.approval_status = f"{decision} by Tester"
                observation.require_remediation = batch_data.require_remediation
                observation.target_resolution_date = batch_data.target_resolution_date
                
                observation.reviewed_by = user_id
                observation.reviewed_at = datetime.utcnow()
                observation.updated_at = datetime.utcnow()
                
                results["successful"].append({
                    "observation_id": obs_id,
                    "new_status": observation.status
                })
                
            except Exception as e:
                results["failed"].append({
                    "observation_id": obs_id,
                    "error": str(e)
                })
        
        await db.commit()
        
        return {
            "total_processed": len(batch_data.observation_ids),
            "successful_count": len(results["successful"]),
            "failed_count": len(results["failed"]),
            "results": results
        }


class CreateImpactAssessmentUseCase(UseCase):
    """Create impact assessment for observation"""
    
    async def execute(
        self,
        observation_id: str,
        assessment_data: ImpactAssessmentCreateDTO,
        user_id: int,
        db: AsyncSession
    ) -> ImpactAssessmentResponseDTO:
        """Create impact assessment"""
        # Verify observation exists
        result = await db.execute(
            select(ObservationRecord)
            .where(ObservationRecord.observation_id == observation_id)
        )
        observation = result.scalar_one_or_none()
        
        if not observation:
            raise ValueError(f"Observation {observation_id} not found")
        
        # Create assessment
        assessment = ObservationImpactAssessment(
            assessment_id=str(uuid.uuid4()),
            observation_id=observation_id,
            impact_category=assessment_data.impact_category,
            impact_description=assessment_data.impact_description,
            estimated_financial_impact=assessment_data.estimated_financial_impact,
            affected_users_count=assessment_data.affected_users_count,
            regulatory_implications=assessment_data.regulatory_implications,
            remediation_timeline_days=assessment_data.remediation_timeline_days,
            remediation_cost_estimate=assessment_data.remediation_cost_estimate,
            assessed_by=user_id
        )
        
        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)
        
        return ImpactAssessmentResponseDTO(
            assessment_id=assessment.assessment_id,
            observation_id=assessment.observation_id,
            impact_category=assessment.impact_category,
            impact_description=assessment.impact_description,
            estimated_financial_impact=assessment.estimated_financial_impact,
            affected_users_count=assessment.affected_users_count,
            regulatory_implications=assessment.regulatory_implications,
            remediation_timeline_days=assessment.remediation_timeline_days,
            remediation_cost_estimate=assessment.remediation_cost_estimate,
            assessed_by=assessment.assessed_by,
            assessed_at=assessment.assessed_at
        )


class CreateResolutionUseCase(UseCase):
    """Create resolution for observation"""
    
    async def execute(
        self,
        observation_id: str,
        resolution_data: ResolutionCreateDTO,
        user_id: int,
        db: AsyncSession
    ) -> ResolutionResponseDTO:
        """Create resolution"""
        # Verify observation exists and is approved
        result = await db.execute(
            select(ObservationRecord)
            .where(ObservationRecord.observation_id == observation_id)
        )
        observation = result.scalar_one_or_none()
        
        if not observation:
            raise ValueError(f"Observation {observation_id} not found")
        
        if observation.status != ObservationStatusEnum.APPROVED:
            raise ValueError(f"Observation must be approved before resolution")
        
        # Create resolution
        resolution = ObservationResolution(
            resolution_id=str(uuid.uuid4()),
            observation_id=observation_id,
            resolution_description=resolution_data.resolution_description,
            resolution_type=resolution_data.resolution_type,
            resolution_status=ResolutionStatusEnum.PENDING,
            implemented_by=resolution_data.implemented_by,
            implementation_date=resolution_data.implementation_date,
            verification_method=resolution_data.verification_method,
            supporting_documents=resolution_data.supporting_documents,
            created_by=user_id
        )
        
        db.add(resolution)
        await db.commit()
        await db.refresh(resolution)
        
        return ResolutionResponseDTO(
            resolution_id=resolution.resolution_id,
            observation_id=resolution.observation_id,
            resolution_description=resolution.resolution_description,
            resolution_type=resolution.resolution_type,
            resolution_status=resolution.resolution_status,
            implemented_by=resolution.implemented_by,
            implementation_date=resolution.implementation_date,
            verified_by=resolution.verified_by,
            verified_at=resolution.verified_at,
            created_at=resolution.created_at,
            updated_at=resolution.updated_at
        )


class GetObservationPhaseStatusUseCase(UseCase):
    """Get observation phase status"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> ObservationPhaseStatusDTO:
        """Get phase status"""
        # Get phase
        result = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Observations"
            ))
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            # Return default status if phase doesn't exist
            return ObservationPhaseStatusDTO(
                phase_id="",
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status="Not Started",
                total_observations=0,
                observations_by_status={},
                observations_by_severity={},
                observations_by_type={},
                can_complete=False,
                completion_requirements=["Phase not started"]
            )
        
        # Get observation statistics
        stats_result = await db.execute(
            select(
                func.count(ObservationRecord.observation_id).label('total'),
                ObservationRecord.status,
                ObservationRecord.severity,
                ObservationRecord.observation_type
            )
            .where(
                ObservationRecord.phase_id == phase.phase_id
            )
            .group_by(
                ObservationRecord.status,
                ObservationRecord.severity,
                ObservationRecord.observation_type
            )
        )
        
        total_observations = 0
        by_status = {}
        by_severity = {}
        by_type = {}
        
        for row in stats_result:
            total_observations += row.total
            if row.status:
                status_key = row.status.value if hasattr(row.status, 'value') else str(row.status)
                by_status[status_key] = by_status.get(status_key, 0) + row.total
            if row.severity:
                severity_key = row.severity.value if hasattr(row.severity, 'value') else str(row.severity)
                by_severity[severity_key] = by_severity.get(severity_key, 0) + row.total
            if row.observation_type:
                type_key = row.observation_type.value if hasattr(row.observation_type, 'value') else str(row.observation_type)
                by_type[type_key] = by_type.get(type_key, 0) + row.total
        
        # Determine completion requirements
        completion_requirements = []
        can_complete = True
        
        # Check for unreviewed observations
        unreviewed = by_status.get(ObservationStatusEnum.SUBMITTED.value, 0)
        if unreviewed > 0:
            completion_requirements.append(f"Review {unreviewed} submitted observations")
            can_complete = False
        
        # Check for critical/high severity without resolution
        critical_high_count = (
            by_severity.get(ObservationSeverityEnum.CRITICAL.value, 0) +
            by_severity.get(ObservationSeverityEnum.HIGH.value, 0)
        )
        if critical_high_count > 0:
            # Check if they have resolutions
            resolution_result = await db.execute(
                select(func.count(ObservationResolution.resolution_id))
                .join(ObservationRecord)
                .where(and_(
                    ObservationRecord.cycle_id == cycle_id,
                    ObservationRecord.report_id == report_id,
                    ObservationRecord.severity.in_([
                        ObservationSeverityEnum.CRITICAL,
                        ObservationSeverityEnum.HIGH
                    ])
                ))
            )
            resolution_count = resolution_result.scalar() or 0
            
            if resolution_count < critical_high_count:
                completion_requirements.append(
                    f"Create resolution plans for {critical_high_count - resolution_count} critical/high observations"
                )
                can_complete = False
        
        if not completion_requirements:
            completion_requirements.append("All requirements met - ready to complete phase")
        
        return ObservationPhaseStatusDTO(
            phase_id=str(phase.phase_id),
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase.status,
            total_observations=total_observations,
            observations_by_status=by_status,
            observations_by_severity=by_severity,
            observations_by_type=by_type,
            can_complete=can_complete,
            completion_requirements=completion_requirements
        )


class CompleteObservationPhaseUseCase(UseCase):
    """Complete observation phase"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        completion_data: ObservationPhaseCompleteDTO,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Complete phase"""
        # Get phase
        result = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Observations"
            ))
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise ValueError("Observation phase not found")
        
        if phase.status == "Complete":
            raise ValueError("Phase is already complete")
        
        # Check completion requirements
        if not completion_data.override_checks:
            status_use_case = GetObservationPhaseStatusUseCase()
            status = await status_use_case.execute(cycle_id, report_id, db)
            
            if not status.can_complete:
                raise ValueError(
                    f"Cannot complete phase: {', '.join(status.completion_requirements)}"
                )
        
        # Update phase status
        phase.status = "Complete"
        phase.completed_by = user_id
        phase.completed_at = datetime.utcnow()
        phase.completion_notes = completion_data.completion_notes
        
        # Update workflow phase
        workflow_orchestrator = get_workflow_orchestrator()
        await workflow_orchestrator.complete_phase(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name="Observation Management",
            db=db
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Observation Management phase completed successfully",
            "phase_id": phase.phase_id,
            "completed_at": phase.completed_at
        }


class GetObservationAnalyticsUseCase(UseCase):
    """Get observation analytics"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> ObservationAnalyticsDTO:
        """Get analytics"""
        # Get basic statistics
        stats_result = await db.execute(
            select(
                func.count(ObservationRecord.observation_id).label('total'),
                ObservationRecord.status,
                ObservationRecord.severity,
                ObservationRecord.observation_type
            )
            .where(and_(
                ObservationRecord.cycle_id == cycle_id,
                ObservationRecord.report_id == report_id
            ))
            .group_by(
                ObservationRecord.status,
                ObservationRecord.severity,
                ObservationRecord.observation_type
            )
        )
        
        total_observations = 0
        by_status = {}
        by_severity = {}
        by_type = {}
        
        for row in stats_result:
            total_observations += row.total
            if row.status:
                status_key = row.status.value if hasattr(row.status, 'value') else str(row.status)
                by_status[status_key] = by_status.get(status_key, 0) + row.total
            if row.severity:
                severity_key = row.severity.value if hasattr(row.severity, 'value') else str(row.severity)
                by_severity[severity_key] = by_severity.get(severity_key, 0) + row.total
            if row.observation_type:
                type_key = row.observation_type.value if hasattr(row.observation_type, 'value') else str(row.observation_type)
                by_type[type_key] = by_type.get(type_key, 0) + row.total
        
        # Calculate average resolution time
        resolution_result = await db.execute(
            select(
                func.avg(
                    func.extract('epoch', ObservationResolution.verified_at - ObservationRecord.created_at) / 86400
                ).label('avg_days')
            )
            .join(ObservationRecord)
            .where(and_(
                ObservationRecord.cycle_id == cycle_id,
                ObservationRecord.report_id == report_id,
                ObservationResolution.verified_at.isnot(None)
            ))
        )
        avg_resolution_days = resolution_result.scalar()
        
        # Get grouping effectiveness
        grouping_result = await db.execute(
            select(
                func.count(ObservationRecord.grouping_key).label('grouped_count'),
                func.sum(ObservationRecord.grouped_count).label('total_grouped')
            )
            .where(and_(
                ObservationRecord.cycle_id == cycle_id,
                ObservationRecord.report_id == report_id,
                ObservationRecord.grouping_key.isnot(None)
            ))
        )
        grouping_data = grouping_result.first()
        
        grouping_effectiveness = {
            "groups_created": grouping_data.grouped_count or 0,
            "observations_grouped": grouping_data.total_grouped or 0,
            "grouping_rate": (
                (grouping_data.total_grouped / total_observations * 100)
                if total_observations > 0 else 0
            )
        }
        
        # Get top issues
        top_issues_result = await db.execute(
            select(
                ObservationRecord.observation_title,
                ObservationRecord.severity,
                ObservationRecord.observation_type,
                func.count(ObservationRecord.observation_id).label('count')
            )
            .where(and_(
                ObservationRecord.cycle_id == cycle_id,
                ObservationRecord.report_id == report_id
            ))
            .group_by(
                ObservationRecord.observation_title,
                ObservationRecord.severity,
                ObservationRecord.observation_type
            )
            .order_by(desc('count'))
            .limit(5)
        )
        
        top_issues = [
            {
                "title": row.observation_title,
                "severity": row.severity,
                "type": row.observation_type,
                "count": row.count
            }
            for row in top_issues_result
        ]
        
        # Trend analysis (simplified)
        trend_analysis = {
            "severity_trend": "stable",
            "volume_trend": "increasing" if total_observations > 10 else "stable",
            "resolution_trend": "improving" if avg_resolution_days and avg_resolution_days < 7 else "stable"
        }
        
        return ObservationAnalyticsDTO(
            total_observations=total_observations,
            by_status=by_status,
            by_severity=by_severity,
            by_type=by_type,
            average_resolution_time_days=avg_resolution_days,
            grouping_effectiveness=grouping_effectiveness,
            top_issues=top_issues,
            trend_analysis=trend_analysis
        )


class AutoDetectObservationsUseCase(UseCase):
    """Auto-detect observations from test failures"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        request_data: AutoDetectionRequestDTO,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Auto-detect and create observations"""
        created_observations = []
        
        if request_data.include_test_failures:
            # Get failed test executions
            query = select(TestExecution).where(and_(
                TestExecution.cycle_id == cycle_id,
                TestExecution.report_id == report_id,
                TestExecution.test_result == 'Failed'
            ))
            
            result = await db.execute(query)
            failed_tests = result.scalars().all()
            
            for test in failed_tests:
                # Check if observation already exists for this test
                existing_result = await db.execute(
                    select(ObservationRecord)
                    .where(ObservationRecord.test_execution_id == test.execution_id)
                )
                if existing_result.scalar_one_or_none():
                    continue
                
                # Categorize the failure
                obs_type, keywords = self._categorize_test_failure(test)
                
                # Determine severity based on test failure
                severity = ObservationSeverityEnum.HIGH if "critical" in test.execution_summary.lower() else ObservationSeverityEnum.MEDIUM
                
                # Skip if below severity threshold
                if request_data.severity_threshold:
                    severity_order = {
                        ObservationSeverityEnum.LOW: 1,
                        ObservationSeverityEnum.MEDIUM: 2,
                        ObservationSeverityEnum.HIGH: 3,
                        ObservationSeverityEnum.CRITICAL: 4
                    }
                    if severity_order.get(severity, 0) < severity_order.get(request_data.severity_threshold, 0):
                        continue
                
                # Create observation
                create_use_case = CreateObservationUseCase()
                observation_data = ObservationCreateDTO(
                    observation_title=f"Test Failure: {test.attribute_name}",
                    observation_description=test.execution_summary or "Test execution failed",
                    observation_type=obs_type,
                    severity=severity,
                    source_attribute_id=test.attribute_id,
                    source_sample_id=test.sample_id,
                    test_execution_id=test.execution_id,
                    suggested_action="Review test failure and determine root cause"
                )
                
                observation = await create_use_case.execute(
                    cycle_id, report_id, observation_data, user_id, db
                )
                created_observations.append(observation)
        
        return {
            "observations_created": len(created_observations),
            "observations": created_observations
        }
    
    def _categorize_test_failure(self, test_execution) -> tuple[ObservationTypeEnum, List[str]]:
        """Categorize test failure into observation type and keywords"""
        summary = test_execution.execution_summary.lower() if test_execution.execution_summary else ""
        
        # Data Quality issues
        if "value" in summary and ("not match" in summary or "mismatch" in summary or "incorrect" in summary):
            return ObservationTypeEnum.DATA_QUALITY, ["value mismatch", "incorrect data", "data quality"]
        
        # Documentation issues
        elif "document" in summary and ("not found" in summary or "missing" in summary or "no valid" in summary):
            return ObservationTypeEnum.DOCUMENTATION, ["missing documentation", "document not found", "lack of evidence"]
        
        # Primary key validation failures
        elif "primary key" in summary and "failed" in summary:
            return ObservationTypeEnum.DATA_QUALITY, ["primary key mismatch", "record identification", "wrong record"]
        
        # Process Control issues
        elif "process" in summary or "control" in summary:
            return ObservationTypeEnum.PROCESS_CONTROL, ["process failure", "control weakness"]
        
        # System issues
        elif "system" in summary or "connection" in summary or "timeout" in summary:
            return ObservationTypeEnum.SYSTEM_CONTROL, ["system error", "connectivity issue", "technical failure"]
        
        # Default to Data Quality
        else:
            return ObservationTypeEnum.DATA_QUALITY, ["general issue", "test failure"]