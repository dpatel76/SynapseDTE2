"""
Unified Planning Service
This service manages the unified planning phase architecture with 4 core tables:
1. PlanningVersion - Version management and planning metadata
2. PlanningDataSource - Phase-level data source definitions
3. PlanningAttribute - Individual planning attributes
4. PlanningPDEMapping - PDE mappings for attributes
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
from sqlalchemy import select, update, delete, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.planning import (
    PlanningVersion, 
    PlanningDataSource,
    PlanningAttribute,
    PlanningPDEMapping,
    VersionStatus,
    DataSourceType,
    AttributeDataType,
    InformationSecurityClassification,
    MappingType,
    Decision,
    Status
)
from app.models.user import User
from app.core.exceptions import (
    NotFoundException, 
    ValidationException, 
    ConflictError,
    BusinessLogicException
)
from app.services.base_service import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlanningServiceUnified:
    """Unified service for managing planning phase operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.version_service = BaseService(PlanningVersion)
        self.data_source_service = BaseService(PlanningDataSource)
        self.attribute_service = BaseService(PlanningAttribute)
        self.pde_mapping_service = BaseService(PlanningPDEMapping)
    
    # Version Management
    async def create_version(
        self, 
        phase_id: int,
        current_user: User,
        workflow_activity_id: Optional[int] = None,
        parent_version_id: Optional[uuid.UUID] = None
    ) -> PlanningVersion:
        """Create a new planning version"""
        
        # Check if draft version already exists
        existing_draft = await self.db.execute(
            select(PlanningVersion)
            .where(
                and_(
                    PlanningVersion.phase_id == phase_id,
                    PlanningVersion.version_status == VersionStatus.DRAFT
                )
            )
        )
        
        if existing_draft.scalar_one_or_none():
            raise ConflictError("A draft version already exists for this phase")
        
        # Get the next version number
        max_version = await self.db.execute(
            select(func.max(PlanningVersion.version_number))
            .where(PlanningVersion.phase_id == phase_id)
        )
        next_version = (max_version.scalar() or 0) + 1
        
        version = PlanningVersion(
            phase_id=phase_id,
            workflow_activity_id=workflow_activity_id,
            version_number=next_version,
            version_status=VersionStatus.DRAFT,
            parent_version_id=parent_version_id
        )
        
        self.version_service.set_audit_fields_on_create(version, current_user)
        
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        
        logger.info(f"Created planning version {version.version_id} for phase {phase_id}")
        return version
    
    async def get_version_by_id(self, version_id: uuid.UUID) -> PlanningVersion:
        """Get version by ID with error handling"""
        result = await self.db.execute(
            select(PlanningVersion)
            .options(
                selectinload(PlanningVersion.data_sources),
                selectinload(PlanningVersion.attributes),
                selectinload(PlanningVersion.pde_mappings)
            )
            .where(PlanningVersion.version_id == version_id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise NotFoundException(f"Version {version_id} not found")
        return version
    
    async def get_versions_by_phase(self, phase_id: int) -> List[PlanningVersion]:
        """Get all versions for a phase"""
        result = await self.db.execute(
            select(PlanningVersion)
            .where(PlanningVersion.phase_id == phase_id)
            .order_by(desc(PlanningVersion.version_number))
        )
        return result.scalars().all()
    
    async def get_current_version(self, phase_id: int) -> Optional[PlanningVersion]:
        """Get the current active version for a phase"""
        result = await self.db.execute(
            select(PlanningVersion)
            .where(
                and_(
                    PlanningVersion.phase_id == phase_id,
                    PlanningVersion.version_status.in_([VersionStatus.DRAFT, VersionStatus.APPROVED])
                )
            )
            .order_by(desc(PlanningVersion.version_number))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    # Data Source Management
    async def create_data_source(
        self,
        version_id: uuid.UUID,
        data_source_data: Dict[str, Any],
        current_user: User
    ) -> PlanningDataSource:
        """Create a new data source"""
        
        # Verify version exists and is editable
        version = await self.get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationException("Can only add data sources to draft versions")
        
        # Check for duplicate source name
        existing_source = await self.db.execute(
            select(PlanningDataSource)
            .where(
                and_(
                    PlanningDataSource.version_id == version_id,
                    PlanningDataSource.source_name == data_source_data["source_name"]
                )
            )
        )
        
        if existing_source.scalar_one_or_none():
            raise ConflictError(f"Data source '{data_source_data['source_name']}' already exists for this version")
        
        data_source = PlanningDataSource(
            version_id=version_id,
            phase_id=version.phase_id,
            source_name=data_source_data["source_name"],
            source_type=DataSourceType(data_source_data["source_type"]),
            description=data_source_data.get("description"),
            connection_config=data_source_data["connection_config"],
            auth_config=data_source_data.get("auth_config"),
            refresh_schedule=data_source_data.get("refresh_schedule"),
            validation_rules=data_source_data.get("validation_rules"),
            estimated_record_count=data_source_data.get("estimated_record_count"),
            data_freshness_hours=data_source_data.get("data_freshness_hours"),
            status=Status.PENDING
        )
        
        self.data_source_service.set_audit_fields_on_create(data_source, current_user)
        
        self.db.add(data_source)
        await self.db.commit()
        await self.db.refresh(data_source)
        
        # Update version summary
        await self.update_version_summary(version_id)
        
        logger.info(f"Created data source {data_source.data_source_id} for version {version_id}")
        return data_source
    
    async def update_data_source_tester_decision(
        self, 
        data_source_id: uuid.UUID, 
        decision: Decision,
        notes: Optional[str],
        current_user: User
    ) -> PlanningDataSource:
        """Update tester decision on a data source"""
        
        data_source = await self.get_data_source_by_id(data_source_id)
        
        # Verify version is editable
        version = await self.get_version_by_id(data_source.version_id)
        if version.version_status not in [VersionStatus.DRAFT, VersionStatus.PENDING_APPROVAL]:
            raise ValidationException("Cannot update decisions on finalized versions")
        
        data_source.tester_decision = decision
        data_source.tester_notes = notes
        data_source.tester_decided_by = current_user.user_id
        data_source.tester_decided_at = datetime.utcnow()
        
        # Update status based on decision
        if decision == Decision.APPROVED:
            data_source.status = Status.APPROVED
        elif decision == Decision.REJECTED:
            data_source.status = Status.REJECTED
        
        self.data_source_service.set_audit_fields_on_update(data_source, current_user)
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(data_source.version_id)
        
        logger.info(f"Updated tester decision for data source {data_source_id}: {decision}")
        return data_source
    
    async def get_data_source_by_id(self, data_source_id: uuid.UUID) -> PlanningDataSource:
        """Get data source by ID with error handling"""
        result = await self.db.execute(
            select(PlanningDataSource)
            .where(PlanningDataSource.data_source_id == data_source_id)
        )
        data_source = result.scalar_one_or_none()
        if not data_source:
            raise NotFoundException(f"Data source {data_source_id} not found")
        return data_source
    
    async def get_data_sources_by_version(self, version_id: uuid.UUID) -> List[PlanningDataSource]:
        """Get all data sources for a version"""
        result = await self.db.execute(
            select(PlanningDataSource)
            .where(PlanningDataSource.version_id == version_id)
            .order_by(PlanningDataSource.source_name)
        )
        return result.scalars().all()
    
    # Attribute Management
    async def create_attribute(
        self,
        version_id: uuid.UUID,
        attribute_data: Dict[str, Any],
        current_user: User
    ) -> PlanningAttribute:
        """Create a new planning attribute"""
        
        # Verify version exists and is editable
        version = await self.get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationException("Can only add attributes to draft versions")
        
        # Check for duplicate attribute name
        existing_attribute = await self.db.execute(
            select(PlanningAttribute)
            .where(
                and_(
                    PlanningAttribute.version_id == version_id,
                    PlanningAttribute.attribute_name == attribute_data["attribute_name"]
                )
            )
        )
        
        if existing_attribute.scalar_one_or_none():
            raise ConflictError(f"Attribute '{attribute_data['attribute_name']}' already exists for this version")
        
        attribute = PlanningAttribute(
            version_id=version_id,
            phase_id=version.phase_id,
            attribute_name=attribute_data["attribute_name"],
            data_type=AttributeDataType(attribute_data["data_type"]),
            description=attribute_data.get("description"),
            business_definition=attribute_data.get("business_definition"),
            is_mandatory=attribute_data.get("is_mandatory", False),
            is_cde=attribute_data.get("is_cde", False),
            is_primary_key=attribute_data.get("is_primary_key", False),
            max_length=attribute_data.get("max_length"),
            information_security_classification=InformationSecurityClassification(
                attribute_data.get("information_security_classification", "internal")
            ),
            llm_metadata=attribute_data.get("llm_metadata"),
            status=Status.PENDING
        )
        
        self.attribute_service.set_audit_fields_on_create(attribute, current_user)
        
        self.db.add(attribute)
        await self.db.commit()
        await self.db.refresh(attribute)
        
        # Update version summary
        await self.update_version_summary(version_id)
        
        logger.info(f"Created attribute {attribute.attribute_id} for version {version_id}")
        return attribute
    
    async def update_attribute_tester_decision(
        self, 
        attribute_id: uuid.UUID, 
        decision: Decision,
        notes: Optional[str],
        current_user: User
    ) -> PlanningAttribute:
        """Update tester decision on a planning attribute"""
        
        attribute = await self.get_attribute_by_id(attribute_id)
        
        # Verify version is editable
        version = await self.get_version_by_id(attribute.version_id)
        if version.version_status not in [VersionStatus.DRAFT, VersionStatus.PENDING_APPROVAL]:
            raise ValidationException("Cannot update decisions on finalized versions")
        
        attribute.tester_decision = decision
        attribute.tester_notes = notes
        attribute.tester_decided_by = current_user.user_id
        attribute.tester_decided_at = datetime.utcnow()
        
        # Update status based on decision
        if decision == Decision.APPROVED:
            attribute.status = Status.APPROVED
        elif decision == Decision.REJECTED:
            attribute.status = Status.REJECTED
        
        self.attribute_service.set_audit_fields_on_update(attribute, current_user)
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(attribute.version_id)
        
        logger.info(f"Updated tester decision for attribute {attribute_id}: {decision}")
        return attribute
    
    async def get_attribute_by_id(self, attribute_id: uuid.UUID) -> PlanningAttribute:
        """Get attribute by ID with error handling"""
        result = await self.db.execute(
            select(PlanningAttribute)
            .options(selectinload(PlanningAttribute.pde_mappings))
            .where(PlanningAttribute.attribute_id == attribute_id)
        )
        attribute = result.scalar_one_or_none()
        if not attribute:
            raise NotFoundException(f"Attribute {attribute_id} not found")
        return attribute
    
    async def get_attributes_by_version(self, version_id: uuid.UUID) -> List[PlanningAttribute]:
        """Get all attributes for a version"""
        result = await self.db.execute(
            select(PlanningAttribute)
            .where(PlanningAttribute.version_id == version_id)
            .order_by(PlanningAttribute.attribute_name)
        )
        return result.scalars().all()
    
    # PDE Mapping Management
    async def create_pde_mapping(
        self,
        attribute_id: uuid.UUID,
        data_source_id: uuid.UUID,
        pde_mapping_data: Dict[str, Any],
        current_user: User
    ) -> PlanningPDEMapping:
        """Create a new PDE mapping"""
        
        attribute = await self.get_attribute_by_id(attribute_id)
        
        # Verify version is editable
        version = await self.get_version_by_id(attribute.version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationException("Can only add PDE mappings to draft versions")
        
        # Verify data source exists and belongs to the same version
        data_source = await self.get_data_source_by_id(data_source_id)
        if data_source.version_id != attribute.version_id:
            raise ValidationException("Data source must be from the same version")
        
        # Check for duplicate PDE code for this attribute
        existing_pde = await self.db.execute(
            select(PlanningPDEMapping)
            .where(
                and_(
                    PlanningPDEMapping.attribute_id == attribute_id,
                    PlanningPDEMapping.pde_code == pde_mapping_data["pde_code"]
                )
            )
        )
        
        if existing_pde.scalar_one_or_none():
            raise ConflictError(f"PDE code '{pde_mapping_data['pde_code']}' already exists for this attribute")
        
        pde_mapping = PlanningPDEMapping(
            version_id=attribute.version_id,
            attribute_id=attribute_id,
            data_source_id=data_source_id,
            phase_id=attribute.phase_id,
            pde_name=pde_mapping_data["pde_name"],
            pde_code=pde_mapping_data["pde_code"],
            mapping_type=MappingType(pde_mapping_data.get("mapping_type", "direct")),
            source_table=pde_mapping_data["source_table"],
            source_column=pde_mapping_data["source_column"],
            source_field=pde_mapping_data["source_field"],
            column_data_type=pde_mapping_data.get("column_data_type"),
            transformation_rule=pde_mapping_data.get("transformation_rule"),
            condition_rule=pde_mapping_data.get("condition_rule"),
            is_primary=pde_mapping_data.get("is_primary", False),
            classification=pde_mapping_data.get("classification", {}),
            llm_metadata=pde_mapping_data.get("llm_metadata", {}),
            status=Status.PENDING
        )
        
        # Check for auto-approval
        if self._should_auto_approve(pde_mapping_data):
            pde_mapping.tester_decision = Decision.APPROVED
            pde_mapping.tester_decided_by = current_user.user_id
            pde_mapping.tester_decided_at = datetime.utcnow()
            pde_mapping.tester_notes = "Auto-approved based on approval rules"
            pde_mapping.auto_approved = True
            pde_mapping.status = Status.APPROVED
        
        self.pde_mapping_service.set_audit_fields_on_create(pde_mapping, current_user)
        
        self.db.add(pde_mapping)
        await self.db.commit()
        await self.db.refresh(pde_mapping)
        
        # Update version summary
        await self.update_version_summary(attribute.version_id)
        
        logger.info(f"Created PDE mapping {pde_mapping.pde_mapping_id} for attribute {attribute_id}")
        return pde_mapping
    
    async def update_pde_mapping_tester_decision(
        self, 
        pde_mapping_id: uuid.UUID, 
        decision: Decision,
        notes: Optional[str],
        current_user: User
    ) -> PlanningPDEMapping:
        """Update tester decision on a PDE mapping"""
        
        pde_mapping = await self.get_pde_mapping_by_id(pde_mapping_id)
        
        # Verify version is editable
        version = await self.get_version_by_id(pde_mapping.version_id)
        if version.version_status not in [VersionStatus.DRAFT, VersionStatus.PENDING_APPROVAL]:
            raise ValidationException("Cannot update decisions on finalized versions")
        
        pde_mapping.tester_decision = decision
        pde_mapping.tester_notes = notes
        pde_mapping.tester_decided_by = current_user.user_id
        pde_mapping.tester_decided_at = datetime.utcnow()
        
        # Update status based on decision
        if decision == Decision.APPROVED:
            pde_mapping.status = Status.APPROVED
        elif decision == Decision.REJECTED:
            pde_mapping.status = Status.REJECTED
        
        self.pde_mapping_service.set_audit_fields_on_update(pde_mapping, current_user)
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(pde_mapping.version_id)
        
        logger.info(f"Updated tester decision for PDE mapping {pde_mapping_id}: {decision}")
        return pde_mapping
    
    async def get_pde_mapping_by_id(self, pde_mapping_id: uuid.UUID) -> PlanningPDEMapping:
        """Get PDE mapping by ID with error handling"""
        result = await self.db.execute(
            select(PlanningPDEMapping)
            .options(
                joinedload(PlanningPDEMapping.attribute),
                joinedload(PlanningPDEMapping.data_source)
            )
            .where(PlanningPDEMapping.pde_mapping_id == pde_mapping_id)
        )
        pde_mapping = result.scalar_one_or_none()
        if not pde_mapping:
            raise NotFoundException(f"PDE mapping {pde_mapping_id} not found")
        return pde_mapping
    
    async def get_pde_mappings_by_version(self, version_id: uuid.UUID) -> List[PlanningPDEMapping]:
        """Get all PDE mappings for a version"""
        result = await self.db.execute(
            select(PlanningPDEMapping)
            .options(
                joinedload(PlanningPDEMapping.attribute),
                joinedload(PlanningPDEMapping.data_source)
            )
            .where(PlanningPDEMapping.version_id == version_id)
            .order_by(PlanningPDEMapping.pde_code)
        )
        return result.scalars().all()
    
    async def get_pde_mappings_by_attribute(self, attribute_id: uuid.UUID) -> List[PlanningPDEMapping]:
        """Get all PDE mappings for an attribute"""
        result = await self.db.execute(
            select(PlanningPDEMapping)
            .options(joinedload(PlanningPDEMapping.data_source))
            .where(PlanningPDEMapping.attribute_id == attribute_id)
            .order_by(PlanningPDEMapping.pde_code)
        )
        return result.scalars().all()
    
    # Version Workflow Management
    async def submit_for_approval(
        self, 
        version_id: uuid.UUID, 
        current_user: User
    ) -> PlanningVersion:
        """Submit planning version for tester approval"""
        
        version = await self.get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationException("Only draft versions can be submitted for approval")
        
        # Check if all components have been reviewed
        validation_errors = await self._validate_version_for_submission(version_id)
        if validation_errors:
            raise BusinessLogicException(f"Version cannot be submitted: {'; '.join(validation_errors)}")
        
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.submitted_by_id = current_user.user_id
        version.submitted_at = datetime.utcnow()
        
        self.version_service.set_audit_fields_on_update(version, current_user)
        
        await self.db.commit()
        
        logger.info(f"Submitted version {version_id} for approval by user {current_user.user_id}")
        return version
    
    async def approve_version(
        self, 
        version_id: uuid.UUID, 
        current_user: User
    ) -> PlanningVersion:
        """Approve planning version (tester action)"""
        
        version = await self.get_version_by_id(version_id)
        if version.version_status != VersionStatus.PENDING_APPROVAL:
            raise ValidationException("Only pending approval versions can be approved")
        
        # Mark previous versions as superseded
        await self.db.execute(
            update(PlanningVersion)
            .where(PlanningVersion.phase_id == version.phase_id)
            .where(PlanningVersion.version_status == VersionStatus.APPROVED)
            .values(version_status=VersionStatus.SUPERSEDED)
        )
        
        # Approve current version
        version.version_status = VersionStatus.APPROVED
        version.approved_by_id = current_user.user_id
        version.approved_at = datetime.utcnow()
        
        self.version_service.set_audit_fields_on_update(version, current_user)
        
        await self.db.commit()
        
        logger.info(f"Approved version {version_id} by user {current_user.user_id}")
        return version
    
    async def reject_version(
        self, 
        version_id: uuid.UUID, 
        rejection_reason: str,
        current_user: User
    ) -> PlanningVersion:
        """Reject planning version (tester action)"""
        
        version = await self.get_version_by_id(version_id)
        if version.version_status != VersionStatus.PENDING_APPROVAL:
            raise ValidationException("Only pending approval versions can be rejected")
        
        version.version_status = VersionStatus.REJECTED
        version.rejection_reason = rejection_reason
        
        self.version_service.set_audit_fields_on_update(version, current_user)
        
        await self.db.commit()
        
        logger.info(f"Rejected version {version_id} by user {current_user.user_id}")
        return version
    
    # Auto-approval Logic
    def _should_auto_approve(self, pde_mapping_data: Dict[str, Any]) -> bool:
        """Check if PDE mapping should be auto-approved based on rules"""
        
        # Auto-approval rules (configurable)
        auto_approval_rules = {
            "min_llm_confidence": 0.85,
            "auto_approve_cde": True,
            "auto_approve_primary_key": True,
            "auto_approve_public_classification": True,
            "max_risk_score_for_auto_approval": 5
        }
        
        # Check LLM confidence
        llm_confidence = pde_mapping_data.get("llm_metadata", {}).get("confidence_score", 0)
        if llm_confidence < auto_approval_rules["min_llm_confidence"]:
            return False
        
        # Check classification-based rules
        classification = pde_mapping_data.get("classification", {})
        
        # Auto-approve public classification
        if (auto_approval_rules["auto_approve_public_classification"] and 
            classification.get("information_security") == "public"):
            return True
        
        # Auto-approve primary keys
        if (auto_approval_rules["auto_approve_primary_key"] and 
            pde_mapping_data.get("is_primary", False)):
            return True
        
        # Check risk score
        risk_score = self._calculate_risk_score(classification)
        if risk_score <= auto_approval_rules["max_risk_score_for_auto_approval"]:
            return True
        
        return False
    
    def _calculate_risk_score(self, classification: Dict[str, Any]) -> int:
        """Calculate risk score for PDE mapping (0-10 scale)"""
        
        risk_score = 0
        
        # Risk level contribution
        risk_level = classification.get("risk_level", "medium")
        if risk_level == "high":
            risk_score += 4
        elif risk_level == "medium":
            risk_score += 2
        elif risk_level == "low":
            risk_score += 1
        
        # Criticality contribution
        criticality = classification.get("criticality", "medium")
        if criticality == "high":
            risk_score += 3
        elif criticality == "medium":
            risk_score += 2
        elif criticality == "low":
            risk_score += 1
        
        # Information security contribution
        info_security = classification.get("information_security", "internal")
        if info_security == "restricted":
            risk_score += 3
        elif info_security == "confidential":
            risk_score += 2
        elif info_security == "internal":
            risk_score += 1
        elif info_security == "public":
            risk_score += 0
        
        return min(risk_score, 10)  # Cap at 10
    
    # Helper Methods
    async def update_version_summary(self, version_id: uuid.UUID) -> None:
        """Update version summary statistics"""
        
        # Get counts from each table
        data_sources = await self.get_data_sources_by_version(version_id)
        attributes = await self.get_attributes_by_version(version_id)
        pde_mappings = await self.get_pde_mappings_by_version(version_id)
        
        # Update version summary
        version = await self.get_version_by_id(version_id)
        version.total_data_sources = len(data_sources)
        version.approved_data_sources = sum(1 for ds in data_sources if ds.status == Status.APPROVED)
        version.total_attributes = len(attributes)
        version.approved_attributes = sum(1 for attr in attributes if attr.status == Status.APPROVED)
        version.pk_attributes = sum(1 for attr in attributes if attr.is_primary_key)
        version.cde_attributes = sum(1 for attr in attributes if attr.is_cde)
        version.mandatory_attributes = sum(1 for attr in attributes if attr.is_mandatory)
        version.total_pde_mappings = len(pde_mappings)
        version.approved_pde_mappings = sum(1 for pde in pde_mappings if pde.status == Status.APPROVED)
        
        await self.db.commit()
    
    async def _validate_version_for_submission(self, version_id: uuid.UUID) -> List[str]:
        """Validate version for submission and return list of errors"""
        
        errors = []
        
        # Check if all data sources have tester decisions
        pending_data_sources = await self.db.execute(
            select(PlanningDataSource)
            .where(
                and_(
                    PlanningDataSource.version_id == version_id,
                    PlanningDataSource.tester_decision.is_(None)
                )
            )
        )
        
        if pending_data_sources.scalar_one_or_none():
            errors.append("All data sources must have tester decisions")
        
        # Check if all attributes have tester decisions
        pending_attributes = await self.db.execute(
            select(PlanningAttribute)
            .where(
                and_(
                    PlanningAttribute.version_id == version_id,
                    PlanningAttribute.tester_decision.is_(None)
                )
            )
        )
        
        if pending_attributes.scalar_one_or_none():
            errors.append("All attributes must have tester decisions")
        
        # Check if all PDE mappings have tester decisions
        pending_pde_mappings = await self.db.execute(
            select(PlanningPDEMapping)
            .where(
                and_(
                    PlanningPDEMapping.version_id == version_id,
                    PlanningPDEMapping.tester_decision.is_(None)
                )
            )
        )
        
        if pending_pde_mappings.scalar_one_or_none():
            errors.append("All PDE mappings must have tester decisions")
        
        # Check if version has at least one approved component
        version = await self.get_version_by_id(version_id)
        if (version.approved_data_sources == 0 and 
            version.approved_attributes == 0 and 
            version.approved_pde_mappings == 0):
            errors.append("Version must have at least one approved component")
        
        return errors
    
    # Bulk Operations
    async def bulk_tester_decision(
        self,
        item_ids: List[uuid.UUID],
        item_type: str,
        decision: Decision,
        notes: Optional[str],
        current_user: User
    ) -> Dict[str, Any]:
        """Perform bulk tester decision operations"""
        
        results = {
            "total_requested": len(item_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for item_id in item_ids:
            try:
                if item_type == "data_source":
                    await self.update_data_source_tester_decision(item_id, decision, notes, current_user)
                elif item_type == "attribute":
                    await self.update_attribute_tester_decision(item_id, decision, notes, current_user)
                elif item_type == "pde_mapping":
                    await self.update_pde_mapping_tester_decision(item_id, decision, notes, current_user)
                else:
                    raise ValueError(f"Unknown item type: {item_type}")
                
                results["successful"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Item {item_id}: {str(e)}")
                logger.error(f"Failed to update tester decision for {item_type} {item_id}: {e}")
        
        return results
    
    # Dashboard/Summary Methods
    async def get_version_dashboard(self, version_id: uuid.UUID) -> Dict[str, Any]:
        """Get dashboard data for a version"""
        
        version = await self.get_version_by_id(version_id)
        data_sources = await self.get_data_sources_by_version(version_id)
        attributes = await self.get_attributes_by_version(version_id)
        pde_mappings = await self.get_pde_mappings_by_version(version_id)
        
        # Calculate completion statistics
        total_items = len(data_sources) + len(attributes) + len(pde_mappings)
        decided_items = (
            sum(1 for ds in data_sources if ds.tester_decision is not None) +
            sum(1 for attr in attributes if attr.tester_decision is not None) +
            sum(1 for pde in pde_mappings if pde.tester_decision is not None)
        )
        
        completion_percentage = (decided_items / total_items * 100) if total_items > 0 else 0
        
        # Check submission requirements
        validation_errors = await self._validate_version_for_submission(version_id)
        can_submit = len(validation_errors) == 0 and version.version_status == VersionStatus.DRAFT
        
        return {
            "version": version,
            "data_sources": data_sources,
            "attributes": attributes,
            "pde_mappings": pde_mappings,
            "completion_percentage": completion_percentage,
            "pending_decisions": total_items - decided_items,
            "can_submit": can_submit,
            "submission_requirements": validation_errors
        }