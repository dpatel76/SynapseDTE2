"""
Scoping Service - New consolidated scoping system

This service manages the new scoping system with version management,
replacing the legacy scoping system with a unified approach.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_, or_, func, desc, asc, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import logging

from app.models.scoping import (
    ScopingVersion, ScopingAttribute,
    VersionStatus, TesterDecision, ReportOwnerDecision, AttributeStatus
)
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.user import User
from app.core.database import get_db
from app.core.exceptions import (
    ValidationError, NotFoundError, ConflictError, 
    BusinessLogicError, PermissionError
)

logger = logging.getLogger(__name__)

# Helper function for timezone-aware timestamps
def utc_now():
    """Get current UTC timestamp with timezone info"""
    return datetime.now(timezone.utc)


class ScopingService:
    """
    Service for managing scoping versions and attribute decisions.
    
    This service implements the version management pattern used across the application
    and provides comprehensive scoping functionality including LLM recommendations,
    tester decisions, and report owner approvals.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_version(
        self,
        phase_id: int,
        workflow_activity_id: Optional[int] = None,
        workflow_execution_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
        activity_name: Optional[str] = None,
        user_id: int = None,
        notes: Optional[str] = None
    ) -> ScopingVersion:
        """
        Create a new scoping version for a phase.
        
        Args:
            phase_id: The workflow phase ID
            workflow_activity_id: Optional workflow activity ID
            workflow_execution_id: Optional temporal workflow execution ID
            workflow_run_id: Optional temporal workflow run ID
            activity_name: Optional activity name
            user_id: User creating the version
            notes: Optional creation notes
            
        Returns:
            ScopingVersion: The newly created version
            
        Raises:
            NotFoundError: If phase not found
            ValidationError: If validation fails
        """
        try:
            # Validate phase exists
            phase = await self.db.get(WorkflowPhase, phase_id)
            if not phase:
                raise NotFoundError(f"Phase with ID {phase_id} not found")
            
            # Get the next version number
            version_number = await self._get_next_version_number(phase_id)
            
            # Create the new version
            version = ScopingVersion(
                phase_id=phase_id,
                workflow_activity_id=workflow_activity_id,
                version_number=version_number,
                version_status=VersionStatus.DRAFT,
                workflow_execution_id=workflow_execution_id,
                workflow_run_id=workflow_run_id,
                activity_name=activity_name,
                created_by_id=user_id,
                updated_by_id=user_id
            )
            
            self.db.add(version)
            await self.db.commit()
            await self.db.refresh(version)
            
            logger.info(f"Created scoping version {version.version_id} for phase {phase_id}")
            return version
            
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to create scoping version: {str(e)}")

    async def get_version(self, version_id: UUID) -> Optional[ScopingVersion]:
        """Get a scoping version by ID"""
        query = select(ScopingVersion).where(ScopingVersion.version_id == version_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_current_version(self, phase_id: int) -> Optional[Dict[str, Any]]:
        """Get the current scoping version for a phase"""
        # Get the latest version from the proper scoping versions table
        version_query = select(ScopingVersion).where(
            ScopingVersion.phase_id == phase_id
        ).order_by(ScopingVersion.version_number.desc()).limit(1)
        
        version_result = await self.db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            return None
            
        # Get statistics for this version
        stats_query = select(
            func.count(ScopingAttribute.attribute_id).label("total_attributes"),
            func.count(case((ScopingAttribute.final_scoping == True, 1))).label("scoped_attributes"),
            func.count(case((ScopingAttribute.final_scoping == False, 1))).label("declined_attributes")
        ).where(ScopingAttribute.version_id == version.version_id)
        
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.one()
        
        # Convert to expected format
        return {
            "version_id": str(version.version_id),
            "phase_id": phase_id,
            "version": version.version_number,
            "version_number": version.version_number,
            "version_status": version.version_status if isinstance(version.version_status, str) else (version.version_status.value if version.version_status else "draft"),
            "total_attributes": stats.total_attributes,
            "scoped_attributes": stats.scoped_attributes,
            "declined_attributes": stats.declined_attributes,
            "created_at": version.created_at,
            "submitted_at": version.submitted_at,
            "can_be_edited": version.version_status == "draft",
            "can_be_submitted": version.version_status == "draft" and stats.total_attributes > 0,
            "is_current": True
        }

    async def get_latest_version(self, phase_id: int) -> Optional[ScopingVersion]:
        """Get the latest version (regardless of status) for a phase"""
        query = select(ScopingVersion).where(
            ScopingVersion.phase_id == phase_id
        ).order_by(desc(ScopingVersion.version_number))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_version_with_attributes(self, version_id: UUID) -> Optional[ScopingVersion]:
        """Get a version with all its attributes loaded"""
        query = select(ScopingVersion).where(
            ScopingVersion.version_id == version_id
        ).options(
            selectinload(ScopingVersion.attributes)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_version_attributes_with_planning_details(self, version_id: UUID) -> List[Dict[str, Any]]:
        """Get version attributes with planning attribute details (name, line_item_number)"""
        from app.models.report_attribute import ReportAttribute
        
        query = select(
            ScopingAttribute,
            ReportAttribute.attribute_name,
            ReportAttribute.line_item_number
        ).select_from(
            ScopingAttribute.__table__.join(
                ReportAttribute.__table__,
                ScopingAttribute.attribute_id == ReportAttribute.id
            )
        ).where(
            ScopingAttribute.version_id == version_id
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Convert to list of dicts with all scoping attribute fields plus planning details
        attributes = []
        for scoping_attr, attr_name, line_item_number in rows:
            attr_dict = {
                # Basic fields
                "attribute_id": str(scoping_attr.attribute_id),
                "version_id": str(scoping_attr.version_id),
                "phase_id": scoping_attr.phase_id,
                "attribute_id": scoping_attr.attribute_id,
                
                # Planning attribute details
                "attribute_name": attr_name,
                "line_item_number": line_item_number,
                
                # LLM recommendation
                "llm_recommendation": scoping_attr.llm_recommendation or {},
                "llm_provider": scoping_attr.llm_provider,
                "llm_confidence_score": scoping_attr.llm_confidence_score,
                "llm_rationale": scoping_attr.llm_rationale,
                "llm_processing_time_ms": scoping_attr.llm_processing_time_ms,
                
                # Tester decision
                "tester_decision": scoping_attr.tester_decision.value if scoping_attr.tester_decision and hasattr(scoping_attr.tester_decision, 'value') else scoping_attr.tester_decision,
                "final_scoping": scoping_attr.final_scoping,
                "tester_rationale": scoping_attr.tester_rationale,
                "tester_decided_by_id": scoping_attr.tester_decided_by_id,
                "tester_decided_at": scoping_attr.tester_decided_at.isoformat() if scoping_attr.tester_decided_at else None,
                
                # Report owner decision
                "report_owner_decision": scoping_attr.report_owner_decision.value if scoping_attr.report_owner_decision and hasattr(scoping_attr.report_owner_decision, 'value') else scoping_attr.report_owner_decision,
                "report_owner_notes": scoping_attr.report_owner_notes,
                "report_owner_decided_by_id": scoping_attr.report_owner_decided_by_id,
                "report_owner_decided_at": scoping_attr.report_owner_decided_at.isoformat() if scoping_attr.report_owner_decided_at else None,
                
                # Special cases
                "is_override": scoping_attr.is_override if scoping_attr else False,
                "override_reason": scoping_attr.override_reason if scoping_attr else None,
                "is_cde": False,  # This should come from planning attribute, not scoping
                "has_historical_issues": False,  # This should come from planning attribute, not scoping
                "is_primary_key": False,  # This should come from planning attribute, not scoping
                
                # Data quality
                "data_quality_score": scoping_attr.data_quality_score if hasattr(scoping_attr, 'data_quality_score') else None,
                "data_quality_issues": scoping_attr.data_quality_issues if hasattr(scoping_attr, 'data_quality_issues') else None,
                
                # Expected source documents - handle both list and string formats
                "expected_source_documents": (
                    scoping_attr.expected_source_documents 
                    if isinstance(scoping_attr.expected_source_documents, (list, type(None)))
                    else scoping_attr.expected_source_documents.split(', ') if scoping_attr.expected_source_documents else []
                ),
                "search_keywords": (
                    scoping_attr.search_keywords
                    if isinstance(scoping_attr.search_keywords, (list, type(None)))
                    else scoping_attr.search_keywords.split(', ') if scoping_attr.search_keywords else []
                ),
                "risk_factors": scoping_attr.risk_factors,
                
                # Status
                "status": scoping_attr.status.value if scoping_attr.status and hasattr(scoping_attr.status, 'value') else (scoping_attr.status or "pending"),
                
                # Audit fields
                "created_at": scoping_attr.created_at.isoformat() if scoping_attr.created_at else None,
                "created_by_id": scoping_attr.created_by_id,
                "updated_at": scoping_attr.updated_at.isoformat() if scoping_attr.updated_at else None,
                "updated_by_id": scoping_attr.updated_by_id
            }
            attributes.append(attr_dict)
        
        return attributes

    async def add_attributes_to_version(
        self,
        version_id: UUID,
        attribute_ids: List[UUID],
        llm_recommendations: List[Dict[str, Any]],
        user_id: int
    ) -> List[ScopingAttribute]:
        """
        Add attributes to a scoping version with LLM recommendations.
        
        Args:
            version_id: The version to add attributes to
            attribute_ids: List of planning attribute IDs
            llm_recommendations: List of LLM recommendation objects
            user_id: User performing the operation
            
        Returns:
            List[ScopingAttribute]: Created scoping attributes
            
        Raises:
            NotFoundError: If version not found
            ValidationError: If validation fails
            BusinessLogicError: If version cannot be edited
        """
        try:
            # Get and validate version
            version = await self.get_version(version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            if not version.can_be_edited:
                raise BusinessLogicError(f"Version {version_id} cannot be edited (status: {version.version_status})")
            
            # Validate attributes exist
            if len(attribute_ids) != len(llm_recommendations):
                raise ValidationError("Number of attributes must match number of recommendations")
            
            # Create scoping attributes
            scoping_attributes = []
            for i, attr_id in enumerate(attribute_ids):
                # Validate planning attribute exists - query by id field, not primary key
                logger.info(f"Looking up planning attribute with ID: {attr_id} (type: {type(attr_id)})")
                
                # Query for the planning attribute by its id field
                planning_query = select(ReportAttribute).where(ReportAttribute.id == attr_id)
                planning_result = await self.db.execute(planning_query)
                planning_attr = planning_result.scalar_one_or_none()
                
                if not planning_attr:
                    logger.error(f"Planning attribute {attr_id} not found in database")
                    raise NotFoundError(f"Planning attribute {attr_id} not found")
                
                # Check if attribute already exists in this version
                existing_query = select(ScopingAttribute).where(
                    and_(
                        ScopingAttribute.version_id == version_id,
                        ScopingAttribute.attribute_id == attr_id
                    )
                )
                existing_result = await self.db.execute(existing_query)
                existing_attr = existing_result.scalar_one_or_none()
                
                if existing_attr:
                    # Update existing attribute with new LLM recommendation
                    # Build the complete recommendation object
                    llm_rec_data = {
                        "recommendation": llm_recommendations[i].get('recommendation', 'include'),
                        "confidence_score": llm_recommendations[i].get('confidence_score', 0.5),
                        "rationale": llm_recommendations[i].get('rationale', ''),
                        "provider": llm_recommendations[i].get('provider', 'anthropic'),
                        "processing_time_ms": llm_recommendations[i].get('processing_time_ms', 0),
                        "response_payload": llm_recommendations[i].get('response_payload', {})
                    }
                    
                    existing_attr.llm_recommendation = llm_rec_data
                    existing_attr.llm_provider = llm_recommendations[i].get('provider')
                    existing_attr.llm_confidence_score = llm_recommendations[i].get('confidence_score')
                    existing_attr.llm_rationale = llm_recommendations[i].get('rationale')
                    existing_attr.llm_processing_time_ms = llm_recommendations[i].get('processing_time_ms')
                    existing_attr.llm_request_payload = llm_recommendations[i].get('request_payload')
                    existing_attr.llm_response_payload = llm_recommendations[i].get('response_payload')
                    # These fields don't exist on ScopingAttribute - they're in planning
                    # existing_attr.is_cde = llm_recommendations[i].get('is_cde', False)
                    # existing_attr.is_primary_key = llm_recommendations[i].get('is_primary_key', False)
                    # existing_attr.has_historical_issues = llm_recommendations[i].get('has_historical_issues', False)
                    existing_attr.data_quality_score = llm_recommendations[i].get('data_quality_score')
                    existing_attr.data_quality_issues = llm_recommendations[i].get('data_quality_issues')
                    existing_attr.expected_source_documents = llm_recommendations[i].get('expected_source_documents')
                    existing_attr.search_keywords = llm_recommendations[i].get('search_keywords')
                    existing_attr.validation_rules = llm_recommendations[i].get('validation_rules')
                    existing_attr.testing_approach = llm_recommendations[i].get('testing_approach')
                    existing_attr.risk_factors = llm_recommendations[i].get('risk_factors')
                    existing_attr.updated_at = utc_now()
                    existing_attr.updated_by_id = user_id
                    
                    self.db.add(existing_attr)
                    scoping_attributes.append(existing_attr)
                    logger.info(f"Updated existing attribute {attr_id} in version {version_id}")
                    continue
                
                # Create scoping attribute
                # Build the complete recommendation object
                llm_rec_data = {
                    "recommendation": llm_recommendations[i].get('recommendation', 'include'),
                    "confidence_score": llm_recommendations[i].get('confidence_score', 0.5),
                    "rationale": llm_recommendations[i].get('rationale', ''),
                    "provider": llm_recommendations[i].get('provider', 'anthropic'),
                    "processing_time_ms": llm_recommendations[i].get('processing_time_ms', 0),
                    "response_payload": llm_recommendations[i].get('response_payload', {})
                }
                
                scoping_attr = ScopingAttribute(
                    version_id=version_id,
                    phase_id=version.phase_id,
                    attribute_id=attr_id,
                    llm_recommendation=llm_rec_data,
                    llm_provider=llm_recommendations[i].get('provider'),
                    llm_confidence_score=llm_recommendations[i].get('confidence_score'),
                    llm_rationale=llm_recommendations[i].get('rationale'),
                    llm_processing_time_ms=llm_recommendations[i].get('processing_time_ms'),
                    llm_request_payload=llm_recommendations[i].get('request_payload'),
                    llm_response_payload=llm_recommendations[i].get('response_payload'),
                    is_cde=llm_recommendations[i].get('is_cde', False),
                    is_primary_key=llm_recommendations[i].get('is_primary_key', False),
                    has_historical_issues=llm_recommendations[i].get('has_historical_issues', False),
                    data_quality_score=llm_recommendations[i].get('data_quality_score'),
                    data_quality_issues=llm_recommendations[i].get('data_quality_issues'),
                    expected_source_documents=llm_recommendations[i].get('expected_source_documents'),
                    search_keywords=llm_recommendations[i].get('search_keywords'),
                    validation_rules=llm_recommendations[i].get('validation_rules'),
                    testing_approach=llm_recommendations[i].get('testing_approach'),
                    risk_factors=llm_recommendations[i].get('risk_factors'),
                    status=AttributeStatus.PENDING,
                    created_by_id=user_id,
                    updated_by_id=user_id
                )
                
                self.db.add(scoping_attr)
                scoping_attributes.append(scoping_attr)
            
            # Commit the attributes
            await self.db.commit()
            
            # Refresh attributes to get IDs
            for attr in scoping_attributes:
                await self.db.refresh(attr)
            
            # Update version metadata with the total count
            version_update_query = """
                UPDATE cycle_report_scoping_versions
                SET total_attributes = (
                    SELECT COUNT(*) 
                    FROM cycle_report_scoping_attributes 
                    WHERE version_id = :version_id
                ),
                scoped_attributes = (
                    SELECT COUNT(*) 
                    FROM cycle_report_scoping_attributes 
                    WHERE version_id = :version_id 
                    AND llm_recommendation::jsonb->>'recommendation' = 'include'
                ),
                updated_at = NOW()
                WHERE version_id = :version_id
            """
            
            await self.db.execute(
                text(version_update_query),
                {"version_id": version_id}
            )
            await self.db.commit()
            
            logger.info(f"Added {len(scoping_attributes)} attributes to version {version_id}")
            return scoping_attributes
            
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to add attributes to version: {str(e)}")

    async def update_llm_recommendations(
        self,
        version_id: UUID,
        recommendations: List[Dict[str, Any]],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Update LLM recommendations for existing attributes in a version.
        
        Args:
            version_id: The version to update
            recommendations: List of recommendation dicts with attribute_id and recommendation data
            user_id: User performing the update
            
        Returns:
            Dict with update statistics
        """
        try:
            # Validate version exists and can be edited
            version = await self.get_version(version_id)
            if not version.can_be_edited:
                raise BusinessLogicError(f"Cannot update recommendations for version with status {version.version_status}")
            
            updated_count = 0
            not_found_count = 0
            
            for rec in recommendations:
                planning_attr_id = rec.get('attribute_id')
                if not planning_attr_id:
                    logger.warning(f"Recommendation missing attribute_id: {rec}")
                    not_found_count += 1
                    continue
                
                # Find existing scoping attribute
                existing_query = select(ScopingAttribute).where(
                    and_(
                        ScopingAttribute.version_id == version_id,
                        ScopingAttribute.attribute_id == planning_attr_id
                    )
                )
                existing_result = await self.db.execute(existing_query)
                existing_attr = existing_result.scalar_one_or_none()
                
                if not existing_attr:
                    logger.warning(f"No scoping attribute found for planning attribute {planning_attr_id} in version {version_id}")
                    not_found_count += 1
                    continue
                
                # Update LLM recommendation fields
                existing_attr.llm_recommendation = rec.get('recommendation')
                existing_attr.llm_provider = rec.get('provider', 'anthropic')
                existing_attr.llm_confidence_score = rec.get('confidence_score')
                existing_attr.llm_rationale = rec.get('rationale')
                existing_attr.llm_processing_time_ms = rec.get('processing_time_ms')
                existing_attr.llm_request_payload = rec.get('request_payload')
                existing_attr.llm_response_payload = rec.get('response_payload')
                existing_attr.updated_at = utc_now()
                existing_attr.updated_by_id = user_id
                
                self.db.add(existing_attr)
                updated_count += 1
            
            # Commit updates
            await self.db.commit()
            
            # Update version metadata
            await self._update_version_statistics(version_id)
            
            logger.info(f"Updated {updated_count} LLM recommendations in version {version_id}")
            
            return {
                "version_id": str(version_id),
                "updated_count": updated_count,
                "not_found_count": not_found_count,
                "total_processed": len(recommendations)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating LLM recommendations: {str(e)}")
            raise

    async def make_tester_decision(
        self,
        attribute_id: UUID,
        decision: TesterDecision,
        final_scoping: bool,
        rationale: Optional[str] = None,
        override_reason: Optional[str] = None,
        user_id: int = None
    ) -> ScopingAttribute:
        """
        Make a tester decision on a scoping attribute.
        
        Args:
            attribute_id: The attribute to make a decision on
            decision: The tester decision (accept, decline, override)
            final_scoping: Whether to scope in (True) or out (False)
            rationale: Optional rationale for the decision
            override_reason: Required if decision is override
            user_id: User making the decision
            
        Returns:
            ScopingAttribute: Updated attribute
            
        Raises:
            NotFoundError: If attribute not found
            ValidationError: If validation fails
            BusinessLogicError: If decision cannot be made
        """
        try:
            # Get the attribute
            attribute = await self.db.get(ScopingAttribute, attribute_id)
            if not attribute:
                raise NotFoundError(f"Scoping attribute {attribute_id} not found")
            
            # Get the version and validate it can be edited
            version = await self.get_version(attribute.version_id)
            if not version.can_be_edited:
                raise BusinessLogicError(f"Cannot make decision on attribute in version with status {version.version_status}")
            
            # Validate override
            if decision == TesterDecision.OVERRIDE and not override_reason:
                raise ValidationError("Override reason is required for override decisions")
            
            # Update the attribute
            attribute.tester_decision = decision
            attribute.final_scoping = final_scoping
            attribute.tester_rationale = rationale
            attribute.tester_decided_by_id = user_id
            attribute.tester_decided_at = utc_now()
            attribute.updated_by_id = user_id
            
            if decision == TesterDecision.OVERRIDE:
                attribute.is_override = True
                attribute.override_reason = override_reason
            
            # Update status
            attribute.status = AttributeStatus.SUBMITTED
            
            await self.db.commit()
            await self.db.refresh(attribute)
            
            logger.info(f"Tester decision made on attribute {attribute_id}: {decision} -> {final_scoping}")
            return attribute
            
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to make tester decision: {str(e)}")

    async def make_report_owner_decision(
        self,
        attribute_id: UUID,
        decision: ReportOwnerDecision,
        notes: Optional[str] = None,
        user_id: int = None
    ) -> ScopingAttribute:
        """
        Make a report owner decision on a scoping attribute.
        
        Args:
            attribute_id: The attribute to make a decision on
            decision: The report owner decision
            notes: Optional notes
            user_id: User making the decision
            
        Returns:
            ScopingAttribute: Updated attribute
        """
        try:
            # Get the attribute
            attribute = await self.db.get(ScopingAttribute, attribute_id)
            if not attribute:
                raise NotFoundError(f"Scoping attribute {attribute_id} not found")
            
            # Validate tester decision exists
            if not attribute.has_tester_decision:
                raise BusinessLogicError("Cannot make report owner decision before tester decision")
            
            # Update the attribute
            attribute.report_owner_decision = decision
            attribute.report_owner_notes = notes
            attribute.report_owner_decided_by_id = user_id
            attribute.report_owner_decided_at = utc_now()
            attribute.updated_by_id = user_id
            
            # Update status based on decision
            if decision == ReportOwnerDecision.APPROVED:
                attribute.status = AttributeStatus.APPROVED
            elif decision == ReportOwnerDecision.REJECTED:
                attribute.status = AttributeStatus.REJECTED
            elif decision == ReportOwnerDecision.NEEDS_REVISION:
                attribute.status = AttributeStatus.NEEDS_REVISION
            
            await self.db.commit()
            await self.db.refresh(attribute)
            
            logger.info(f"Report owner decision made on attribute {attribute_id}: {decision}")
            return attribute
            
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to make report owner decision: {str(e)}")

    async def submit_version_for_approval(
        self,
        version_id: UUID,
        submission_notes: Optional[str] = None,
        user_id: int = None
    ) -> ScopingVersion:
        """
        Submit a version for approval.
        
        Args:
            version_id: The version to submit
            submission_notes: Optional submission notes
            user_id: User submitting the version
            
        Returns:
            ScopingVersion: Updated version
            
        Raises:
            NotFoundError: If version not found
            BusinessLogicError: If version cannot be submitted
        """
        try:
            # Get the version
            version = await self.get_version_with_attributes(version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            # Allow re-submission if version is already approved or pending (workaround for enum issue)
            if version.version_status not in [VersionStatus.DRAFT, VersionStatus.REJECTED, VersionStatus.APPROVED, VersionStatus.PENDING_APPROVAL]:
                raise BusinessLogicError(f"Version {version_id} cannot be submitted (status: {version.version_status})")
            
            # Auto-approve any PK attributes without decisions before validation
            pk_without_decisions = []
            
            for attr in version.attributes:
                if not attr.has_tester_decision:
                    # Check if this is a PK attribute
                    planning_attr = await self.db.get(ReportAttribute, attr.attribute_id)
                    if planning_attr and planning_attr.is_primary_key:
                        # Auto-approve PK attribute
                        attr.tester_decision = TesterDecision.ACCEPT
                        attr.final_scoping = True
                        attr.tester_rationale = "Primary Key attribute - automatically included for testing"
                        attr.tester_decided_at = utc_now()
                        attr.tester_decided_by_id = user_id
                        attr.status = AttributeStatus.SUBMITTED
                        attr.updated_at = utc_now()
                        attr.updated_by_id = user_id
                        pk_without_decisions.append(attr.attribute_id)
            
            if pk_without_decisions:
                await self.db.commit()
                logger.info(f"Auto-approved {len(pk_without_decisions)} PK attributes for version {version_id}")
            
            # Now validate remaining attributes have tester decisions
            pending_attributes = []
            for attr in version.attributes:
                if not attr.has_tester_decision:
                    # Double-check it's not a PK we just missed
                    planning_attr = await self.db.get(ReportAttribute, attr.attribute_id)
                    if not planning_attr or not planning_attr.is_primary_key:
                        pending_attributes.append(attr)
            
            if pending_attributes:
                raise BusinessLogicError(f"Cannot submit version with {len(pending_attributes)} pending attribute decisions")
            
            # Reset report owner decisions on submission to avoid carrying over previous feedback
            # This ensures report owner provides fresh feedback on the updated tester decisions
            reset_count = 0
            for attr in version.attributes:
                if attr.report_owner_decision is not None:
                    attr.report_owner_decision = None
                    attr.report_owner_notes = None
                    attr.report_owner_decided_by_id = None
                    attr.report_owner_decided_at = None
                    attr.updated_at = utc_now()
                    attr.updated_by_id = user_id
                    reset_count += 1
            
            if reset_count > 0:
                logger.info(f"Reset {reset_count} report owner decisions for fresh review on version {version_id}")
            
            # Update version status
            version.version_status = VersionStatus.PENDING_APPROVAL  # Set to pending for Report Owner approval
            version.submission_notes = submission_notes
            version.submitted_by_id = user_id
            version.submitted_at = utc_now()
            version.updated_by_id = user_id
            
            await self.db.commit()
            # Don't refresh version - it has selectinload relationships that cause recursion
            
            # Mark version as approved by tester
            try:
                from app.services.version_tester_approval import VersionTesterApprovalService
                await VersionTesterApprovalService.mark_scoping_approved_by_tester(
                    self.db, str(version_id), user_id
                )
            except Exception as e:
                logger.error(f"Failed to mark version as approved by tester: {str(e)}")
                # Don't fail the submission if this fails
            
            # Create Universal Assignment for Report Owner
            try:
                from app.models.universal_assignment import UniversalAssignment
                from app.models.report import Report
                from app.models.workflow import WorkflowPhase
                
                # Get phase and report info
                phase_result = await self.db.get(WorkflowPhase, version.phase_id)
                if not phase_result:
                    logger.error(f"Phase not found for phase_id: {version.phase_id}")
                    return version
                
                # Get report with LOB loaded
                report = await self.db.get(Report, phase_result.report_id)
                lob = None
                if report and report.lob_id:
                    # Explicitly load the LOB to avoid lazy loading issues
                    from app.models.lob import LOB
                    lob = await self.db.get(LOB, report.lob_id)
                
                # Get cycle info for cycle_name
                from app.models.test_cycle import TestCycle
                cycle = await self.db.get(TestCycle, phase_result.cycle_id)
                
                if report and report.report_owner_id:
                    # Get user to determine from_role
                    from app.models.user import User
                    from_user = await self.db.get(User, user_id)
                    
                    # Create assignment for report owner
                    assignment = UniversalAssignment(
                        assignment_type="Scoping Approval",
                        from_role=from_user.role if from_user else "Tester",  # Role of the submitter
                        to_role="Report Owner",  # Fixed role for scoping approval
                        from_user_id=user_id,
                        to_user_id=report.report_owner_id,
                        title="Review Scoping Decisions",
                        description=f"Please review and approve scoping decisions for {report.report_name}",
                        context_type="Report",
                        context_data={
                            "cycle_id": phase_result.cycle_id,  # Keep as integer
                            "report_id": phase_result.report_id,  # Keep as integer
                            "phase_id": phase_result.phase_id,  # Add phase_id for version metadata updates
                            "phase_name": "Scoping",
                            "version_id": str(version_id),
                            "submitted_by": user_id,
                            "submitted_at": utc_now().isoformat(),
                            "submission_notes": submission_notes,
                            "total_attributes": version.total_attributes,
                            "scoped_attributes": version.scoped_attributes,
                            "report_name": report.report_name,
                            "cycle_name": cycle.cycle_name if cycle else None,
                            "lob": lob.lob_name if lob else "Unknown"
                        },
                        priority="High",
                        due_date=utc_now() + timedelta(days=2),  # 2 day SLA
                        created_by_id=user_id,
                        updated_by_id=user_id
                    )
                    self.db.add(assignment)
                    await self.db.commit()
                    logger.info(f"Created Scoping Approval assignment for Report Owner {report.report_owner_id}")
                else:
                    logger.warning(f"No Report Owner found for report {phase_result.report_id}")
            except Exception as e:
                logger.error(f"Failed to create UniversalAssignment: {str(e)}")
                logger.error(f"Assignment details - Type: Scoping Approval, From: {user_id}, To: {report.report_owner_id if 'report' in locals() and report else 'No report owner'}")
                logger.error(f"Phase details - Cycle: {phase_result.cycle_id}, Report: {phase_result.report_id}")
                # Don't fail the submission if assignment creation fails
                import traceback
                logger.error(traceback.format_exc())
            
            logger.info(f"Version {version_id} submitted for approval")
            return version
            
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to submit version for approval: {str(e)}")

    async def approve_version(
        self,
        version_id: UUID,
        approval_notes: Optional[str] = None,
        user_id: int = None
    ) -> ScopingVersion:
        """
        Approve a version.
        
        Args:
            version_id: The version to approve
            approval_notes: Optional approval notes
            user_id: User approving the version
            
        Returns:
            ScopingVersion: Updated version
        """
        try:
            # Get the version
            version = await self.get_version(version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            if not version.can_be_approved:
                raise BusinessLogicError(f"Version {version_id} cannot be approved (status: {version.version_status})")
            
            # Supersede any existing approved version
            await self._supersede_current_version(version.phase_id, user_id)
            
            # Update version status
            version.version_status = VersionStatus.APPROVED
            version.approval_notes = approval_notes
            version.approved_by_id = user_id
            version.approved_at = utc_now()
            version.updated_by_id = user_id
            
            await self.db.commit()
            await self.db.refresh(version)
            
            # Complete any Universal Assignment for this version approval
            try:
                from app.services.universal_assignment_service import UniversalAssignmentService
                from app.models.universal_assignment import UniversalAssignment
                
                assignment_service = UniversalAssignmentService(self.db)
                
                # Find the assignment for this version approval
                assignment_query = select(UniversalAssignment).where(
                    and_(
                        UniversalAssignment.assignment_type == "Scoping Approval",
                        UniversalAssignment.to_user_id == user_id,
                        UniversalAssignment.status == "Assigned"
                    )
                )
                
                # Check if context_data contains this version_id
                result = await self.db.execute(assignment_query)
                assignments = result.scalars().all()
                
                for assignment in assignments:
                    context_data = assignment.context_data or {}
                    if context_data.get("version_id") == str(version_id):
                        await assignment_service.complete_assignment(
                            assignment_id=assignment.assignment_id,
                            user_id=user_id,
                            completion_notes=f"Scoping version approved: {approval_notes or 'Approved'}",
                            completion_data={
                                "approval_action": "approved",
                                "version_id": str(version_id),
                                "version_number": version.version_number,
                                "approved_at": version.approved_at.isoformat() if version.approved_at else None
                            }
                        )
                        logger.info(f"Completed Universal Assignment {assignment.assignment_id} for approved version {version_id}")
                        break
                        
            except Exception as e:
                # Don't fail the approval if assignment completion fails
                logger.error(f"Failed to complete Universal Assignment for approved version {version_id}: {str(e)}")
            
            logger.info(f"Version {version_id} approved")
            return version
            
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to approve version: {str(e)}")

    async def reject_version(
        self,
        version_id: UUID,
        rejection_reason: str,
        requested_changes: Optional[Dict[str, Any]] = None,
        user_id: int = None
    ) -> ScopingVersion:
        """
        Reject a version.
        
        Args:
            version_id: The version to reject
            rejection_reason: Reason for rejection
            requested_changes: Optional structured requested changes
            user_id: User rejecting the version
            
        Returns:
            ScopingVersion: Updated version
        """
        try:
            # Get the version
            version = await self.get_version(version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            if not version.can_be_approved:
                raise BusinessLogicError(f"Version {version_id} cannot be rejected (status: {version.version_status})")
            
            # Update version status
            version.version_status = VersionStatus.REJECTED
            version.rejection_reason = rejection_reason
            version.requested_changes = requested_changes
            version.updated_by_id = user_id
            
            # Update corresponding Universal Assignment
            try:
                from app.models.universal_assignment import UniversalAssignment
                from app.models.workflow import WorkflowPhase
                import json
                
                # Get phase info
                phase_result = await self.db.get(WorkflowPhase, version.phase_id)
                if phase_result:
                    # Find the assignment for this version
                    assignment_query = select(UniversalAssignment).where(
                        and_(
                            UniversalAssignment.assignment_type == "Scoping Approval",
                            UniversalAssignment.status == "Assigned"
                        )
                    )
                    assignment_result = await self.db.execute(assignment_query)
                    assignments = assignment_result.scalars().all()
                    
                    for assignment in assignments:
                        context_data = assignment.context_data
                        if isinstance(context_data, str):
                            context_data = json.loads(context_data)
                        
                        # Check if this assignment is for our version
                        if (context_data.get('version_id') == str(version_id) and
                            context_data.get('cycle_id') == phase_result.cycle_id and
                            context_data.get('report_id') == phase_result.report_id):
                            
                            # Update assignment status to completed with rejection details
                            assignment.status = "Completed"
                            assignment.completed_at = utc_now()
                            assignment.completed_by_user_id = user_id
                            assignment.completion_notes = f"Version rejected: {rejection_reason}"
                            assignment.completion_data = {
                                "action": "rejected",
                                "rejection_reason": rejection_reason,
                                "requested_changes": requested_changes,
                                "rejected_at": utc_now().isoformat(),
                                "rejected_by": user_id
                            }
                            assignment.updated_by_id = user_id
                            assignment.updated_at = utc_now()
                            
                            logger.info(f"Updated Universal Assignment {assignment.assignment_id} for rejected version {version_id}")
                            break
                    else:
                        logger.warning(f"No matching Universal Assignment found for version {version_id}")
                        
            except Exception as e:
                logger.error(f"Failed to update UniversalAssignment for rejected version {version_id}: {str(e)}")
                # Don't fail the rejection if assignment update fails
                import traceback
                logger.error(traceback.format_exc())
            
            await self.db.commit()
            await self.db.refresh(version)
            
            logger.info(f"Version {version_id} rejected")
            return version
            
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to reject version: {str(e)}")

    async def get_version_statistics(self, version_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a version.
        
        Args:
            version_id: The version to get statistics for
            
        Returns:
            Dict containing comprehensive statistics
        """
        version = await self.get_version_with_attributes(version_id)
        if not version:
            raise NotFoundError(f"Version {version_id} not found")
        
        # Basic counts
        total_attributes = len(version.attributes)
        # Calculate metrics based on tester decisions
        scoped_attributes = len([attr for attr in version.attributes if attr.tester_decision == 'accept'])
        declined_attributes = len([attr for attr in version.attributes if attr.tester_decision == 'reject'])
        override_count = len([attr for attr in version.attributes if attr.is_override])
        # CDE count would need to be calculated from planning attributes, not scoping
        cde_count = 0  # Not available in scoping attributes
        
        # Decision progress - check if tester_decision is set
        pending_decisions = len([attr for attr in version.attributes if attr.tester_decision is None])
        completed_decisions = len([attr for attr in version.attributes if attr.tester_decision is not None])
        
        # Report owner decisions
        pending_report_owner = len([attr for attr in version.attributes if attr.tester_decision is not None and attr.report_owner_decision is None])
        approved_by_report_owner = len([attr for attr in version.attributes if attr.report_owner_decision == 'approved'])
        
        # LLM accuracy
        llm_accuracy = None
        if completed_decisions > 0:
            accurate_predictions = len([
                attr for attr in version.attributes 
                if attr.llm_agreed_with_tester is True
            ])
            llm_accuracy = accurate_predictions / completed_decisions
        
        return {
            "version_id": str(version_id),
            "version_number": version.version_number,
            "status": version.version_status if isinstance(version.version_status, str) else (version.version_status.value if version.version_status else "draft"),
            "total_attributes": total_attributes,
            "scoped_attributes": scoped_attributes,
            "declined_attributes": declined_attributes,
            "override_count": override_count,
            "cde_count": cde_count,
            "scoping_percentage": (scoped_attributes / total_attributes * 100) if total_attributes > 0 else 0,
            "override_percentage": (override_count / total_attributes * 100) if total_attributes > 0 else 0,
            "decision_progress": {
                "pending_decisions": pending_decisions,
                "completed_decisions": completed_decisions,
                "progress_percentage": (completed_decisions / total_attributes * 100) if total_attributes > 0 else 0
            },
            "report_owner_progress": {
                "pending_decisions": pending_report_owner,
                "approved_decisions": approved_by_report_owner,
                "progress_percentage": (approved_by_report_owner / completed_decisions * 100) if completed_decisions > 0 else 0
            },
            "llm_accuracy": llm_accuracy,
            "created_at": version.created_at.isoformat(),
            "submitted_at": version.submitted_at.isoformat() if version.submitted_at else None,
            "approved_at": version.approved_at.isoformat() if version.approved_at else None,
            "can_be_edited": version.can_be_edited,
            "can_be_submitted": version.can_be_submitted,
            "can_be_approved": version.can_be_approved,
            "is_current": version.is_current
        }

    async def get_phase_versions(
        self,
        phase_id: int,
        limit: int = 10,
        offset: int = 0,
        include_attributes: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all versions for a phase"""
        # Query scoping versions table
        query = select(ScopingVersion).where(
            ScopingVersion.phase_id == phase_id
        ).order_by(
            ScopingVersion.version_number.desc()
        ).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        versions = result.scalars().all()
        
        # Convert to expected format
        version_list = []
        # The first version in the list is the latest (due to desc ordering)
        latest_version_id = versions[0].version_id if versions else None
        
        for version in versions:
            version_list.append({
                "version_id": str(version.version_id),
                "version_number": version.version_number,
                "phase_id": version.phase_id,
                "version_status": version.version_status.value if hasattr(version.version_status, 'value') else (version.version_status if version.version_status else "draft"),
                "rejection_reason": version.rejection_reason,  # Add rejection_reason
                "created_at": version.created_at,
                "created_by": version.created_by_id,
                "submitted_at": version.submitted_at,
                "approved_at": version.approved_at,
                "total_attributes": version.total_attributes,
                "scoped_attributes": version.scoped_attributes or 0,
                "declined_attributes": version.declined_attributes or 0,
                "is_current": version.version_id == latest_version_id  # Mark the latest version as current
            })
        
        return version_list

    async def get_attribute_decision_history(
        self,
        attribute_id: int,
        phase_id: int
    ) -> List[ScopingAttribute]:
        """Get decision history for a planning attribute across all versions"""
        query = select(ScopingAttribute).where(
            and_(
                ScopingAttribute.attribute_id == attribute_id,
                ScopingAttribute.phase_id == phase_id
            )
        ).order_by(desc(ScopingAttribute.created_at))
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def bulk_update_attributes(
        self,
        version_id: UUID,
        updates: List[Dict[str, Any]],
        user_id: int
    ) -> List[ScopingAttribute]:
        """
        Bulk update multiple attributes in a version.
        
        Args:
            version_id: The version to update
            updates: List of update dictionaries containing attribute_id and fields to update
            user_id: User performing the update
            
        Returns:
            List of updated attributes
        """
        try:
            # Get the version and validate it can be edited
            version = await self.get_version(version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            if not version.can_be_edited:
                raise BusinessLogicError(f"Version {version_id} cannot be edited")
            
            updated_attributes = []
            
            for update in updates:
                attribute_id = update.get('attribute_id')
                if not attribute_id:
                    continue
                
                # Get the attribute
                attribute = await self.db.get(ScopingAttribute, attribute_id)
                if not attribute or attribute.version_id != version_id:
                    logger.warning(f"Attribute {attribute_id} not found in version {version_id}")
                    continue
                
                # Apply updates
                for field, value in update.items():
                    if field == 'attribute_id':
                        continue
                    if hasattr(attribute, field):
                        setattr(attribute, field, value)
                
                attribute.updated_by_id = user_id
                updated_attributes.append(attribute)
            
            await self.db.commit()
            
            for attr in updated_attributes:
                await self.db.refresh(attr)
            
            logger.info(f"Bulk updated {len(updated_attributes)} attributes in version {version_id}")
            return updated_attributes
            
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to bulk update attributes: {str(e)}")

    # Private helper methods
    async def _get_next_version_number(self, phase_id: int) -> int:
        """Get the next version number for a phase"""
        query = select(func.max(ScopingVersion.version_number)).where(
            ScopingVersion.phase_id == phase_id
        )
        result = await self.db.execute(query)
        max_version = result.scalar()
        return (max_version or 0) + 1

    async def _supersede_current_version(self, phase_id: int, user_id: int) -> None:
        """Supersede the current approved version for a phase"""
        # Use explicit type casting to avoid enum comparison issues
        from sqlalchemy import cast, String
        query = select(ScopingVersion).where(
            and_(
                ScopingVersion.phase_id == phase_id,
                cast(ScopingVersion.version_status, String) == 'approved'
            )
        )
        result = await self.db.execute(query)
        current_version = result.scalar_one_or_none()
        
        if current_version:
            current_version.version_status = VersionStatus.SUPERSEDED
            current_version.updated_by_id = user_id
            logger.info(f"Superseded version {current_version.version_id} for phase {phase_id}")

    async def copy_version(
        self,
        source_version_id: UUID,
        user_id: int,
        copy_attributes: bool = True,
        copy_decisions: bool = False
    ) -> ScopingVersion:
        """
        Create a copy of an existing version.
        
        Args:
            source_version_id: The version to copy
            user_id: User creating the copy
            copy_attributes: Whether to copy attributes
            copy_decisions: Whether to copy tester decisions
            
        Returns:
            ScopingVersion: The new version
        """
        try:
            # Get the source version
            source_version = await self.get_version_with_attributes(source_version_id)
            if not source_version:
                raise NotFoundError(f"Source version {source_version_id} not found")
            
            # Create new version
            new_version = await self.create_version(
                phase_id=source_version.phase_id,
                workflow_activity_id=source_version.workflow_activity_id,
                workflow_execution_id=source_version.workflow_execution_id,
                workflow_run_id=source_version.workflow_run_id,
                activity_name=source_version.activity_name,
                user_id=user_id,
                notes=f"Copied from version {source_version.version_number}"
            )
            
            # Set parent relationship
            new_version.parent_version_id = source_version_id
            
            # Copy attributes if requested
            if copy_attributes and source_version.attributes:
                for source_attr in source_version.attributes:
                    new_attr = ScopingAttribute(
                        version_id=new_version.version_id,
                        phase_id=new_version.phase_id,
                        attribute_id=source_attr.attribute_id,
                        llm_recommendation=source_attr.llm_recommendation,
                        llm_provider=source_attr.llm_provider,
                        llm_confidence_score=source_attr.llm_confidence_score,
                        llm_rationale=source_attr.llm_rationale,
                        llm_processing_time_ms=source_attr.llm_processing_time_ms,
                        llm_request_payload=source_attr.llm_request_payload,
                        llm_response_payload=source_attr.llm_response_payload,
                        # These fields don't exist on ScopingAttribute - skip them
                        # is_cde=source_attr.is_cde,
                        # is_primary_key=source_attr.is_primary_key,
                        # has_historical_issues=source_attr.has_historical_issues,
                        data_quality_score=source_attr.data_quality_score,
                        data_quality_issues=source_attr.data_quality_issues,
                        expected_source_documents=source_attr.expected_source_documents,
                        search_keywords=source_attr.search_keywords,
                        risk_factors=source_attr.risk_factors,
                        status=AttributeStatus.PENDING,
                        created_by_id=user_id,
                        updated_by_id=user_id
                    )
                    
                    # Copy decisions if requested
                    if copy_decisions and source_attr.has_tester_decision:
                        new_attr.tester_decision = source_attr.tester_decision
                        new_attr.final_scoping = source_attr.final_scoping
                        new_attr.tester_rationale = source_attr.tester_rationale
                        new_attr.is_override = source_attr.is_override
                        new_attr.override_reason = source_attr.override_reason
                        new_attr.status = AttributeStatus.SUBMITTED
                    
                    self.db.add(new_attr)
            
            await self.db.commit()
            await self.db.refresh(new_version)
            
            logger.info(f"Created copy of version {source_version_id} as {new_version.version_id}")
            return new_version
            
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to copy version: {str(e)}")

    async def get_version_history(
        self, 
        phase_id: int,
        status_filter: Optional[List[VersionStatus]] = None,
        include_statistics: bool = True
    ) -> List[ScopingVersion]:
        """
        Get all versions for a phase with optional filtering.
        
        Args:
            phase_id: The workflow phase ID
            status_filter: Optional list of version statuses to filter by
            include_statistics: Whether to include summary statistics
            
        Returns:
            List of scoping versions ordered by version number descending
        """
        try:
            query = select(ScopingVersion).where(
                and_(
                    ScopingVersion.phase_id == phase_id,
                    ScopingVersion.total_attributes > 0  # Filter out empty versions
                )
            )
            
            # Apply status filter if provided
            if status_filter:
                # Convert enum values to strings for database comparison
                status_values = []
                for status in status_filter:
                    if isinstance(status, str):
                        status_values.append(status)
                    elif hasattr(status, 'value'):
                        status_values.append(status.value)
                    else:
                        status_values.append(str(status))
                query = query.where(ScopingVersion.version_status.in_(status_values))
            
            # Order by version number descending (newest first)
            query = query.order_by(ScopingVersion.version_number.desc())
            
            result = await self.db.execute(query)
            versions = result.scalars().all()
            
            # Optionally load statistics
            if include_statistics:
                for version in versions:
                    # Load summary statistics
                    stats_query = select(
                        func.count(ScopingAttribute.attribute_id).label('total_attributes'),
                        func.count(ScopingAttribute.tester_decision).label('tester_decisions'),
                        func.count(ScopingAttribute.report_owner_decision).label('report_owner_decisions')
                    ).where(ScopingAttribute.version_id == version.version_id)
                    
                    stats_result = await self.db.execute(stats_query)
                    stats = stats_result.one()
                    
                    # Add statistics to version object (as transient attributes)
                    version._total_attributes = stats.total_attributes
                    version._tester_decisions = stats.tester_decisions
                    version._report_owner_decisions = stats.report_owner_decisions
            
            return versions
            
        except Exception as e:
            logger.error(f"Error getting version history for phase {phase_id}: {str(e)}")
            raise
    
    async def get_all_versions(self, phase_id: int) -> List[ScopingVersion]:
        """
        Get all versions for a phase (alias for get_version_history).
        Matches data profiling service interface.
        """
        return await self.get_version_history(phase_id)
    
    async def get_approved_versions(self, phase_id: int) -> List[ScopingVersion]:
        """Get only approved versions for a phase"""
        return await self.get_version_history(
            phase_id, 
            status_filter=[VersionStatus.APPROVED.value]  # Convert to string value
        )
    
    async def get_latest_version(self, phase_id: int) -> Optional[ScopingVersion]:
        """
        Get the latest version for a phase regardless of status.
        
        Returns:
            The version with the highest version number
        """
        try:
            query = select(ScopingVersion).where(
                ScopingVersion.phase_id == phase_id
            ).order_by(ScopingVersion.version_number.desc()).limit(1)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting latest version for phase {phase_id}: {str(e)}")
            raise
    
    async def bulk_approve_attributes(
        self,
        attribute_ids: List[UUID],
        user_id: int,
        user_role: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk approve multiple scoping attributes.
        Automatically determines whether to apply tester or report owner decision based on user role.
        
        Args:
            attribute_ids: List of attribute IDs to approve
            user_id: User performing the approval
            user_role: Role of the user performing the approval
            notes: Optional notes for the approval
            
        Returns:
            Dictionary with results including count and any errors
        """
        try:
            approved_count = 0
            errors = []
            processed_versions = set()
            
            for attribute_id in attribute_ids:
                try:
                    # Get the attribute
                    attribute = await self.db.get(ScopingAttribute, attribute_id)
                    if not attribute:
                        errors.append({
                            "attribute_id": str(attribute_id),
                            "error": "Attribute not found"
                        })
                        continue
                    
                    # Track which versions we're updating
                    processed_versions.add(attribute.version_id)
                    
                    # Update based on user role
                    if user_role in ["Tester", "Test Executive"]:
                        # Set tester approval
                        attribute.tester_decision = TesterDecision.ACCEPT
                        attribute.tester_rationale = notes or "Bulk approved"
                        attribute.tester_decided_by_id = user_id
                        attribute.tester_decided_at = utc_now()
                        
                        # Update status - if tester approves, mark as submitted for report owner review
                        if attribute.report_owner_decision == ReportOwnerDecision.APPROVED:
                            attribute.status = AttributeStatus.APPROVED
                        else:
                            attribute.status = AttributeStatus.SUBMITTED
                            
                    elif user_role in ["Report Owner", "Report Owner Executive"]:
                        # Set report owner approval
                        attribute.report_owner_decision = ReportOwnerDecision.APPROVED
                        attribute.report_owner_notes = notes or "Bulk approved"
                        attribute.report_owner_decided_by_id = user_id
                        attribute.report_owner_decided_at = utc_now()
                        
                        # Update status - only fully approved when both approve
                        if attribute.tester_decision == TesterDecision.ACCEPT:
                            attribute.status = AttributeStatus.APPROVED
                        # Otherwise keep current status
                            
                    else:
                        # Admin or other roles default to tester behavior
                        attribute.tester_decision = TesterDecision.ACCEPT
                        attribute.tester_rationale = notes or "Bulk approved"
                        attribute.tester_decided_by_id = user_id
                        attribute.tester_decided_at = utc_now()
                        
                        if attribute.report_owner_decision == ReportOwnerDecision.APPROVED:
                            attribute.status = AttributeStatus.APPROVED
                        else:
                            attribute.status = AttributeStatus.SUBMITTED
                    
                    attribute.updated_by_id = user_id
                    attribute.updated_at = utc_now()
                    
                    approved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error approving attribute {attribute_id}: {str(e)}")
                    errors.append({
                        "attribute_id": str(attribute_id),
                        "error": str(e)
                    })
            
            # Update version statistics for all affected versions
            for version_id in processed_versions:
                await self._update_version_statistics(version_id)
            
            await self.db.commit()
            
            logger.info(f"Bulk approved {approved_count} attributes by {user_role}")
            
            return {
                "approved_count": approved_count,
                "total_requested": len(attribute_ids),
                "errors": errors,
                "success": len(errors) == 0,
                "decision_type": "tester" if user_role in ["Tester", "Test Executive"] else "report_owner"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in bulk approve: {str(e)}")
            raise BusinessLogicError(f"Failed to bulk approve attributes: {str(e)}")
    
    async def bulk_reject_attributes(
        self,
        attribute_ids: List[UUID],
        user_id: int,
        user_role: str,
        reason: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk reject multiple scoping attributes.
        Automatically determines whether to apply tester or report owner decision based on user role.
        
        Args:
            attribute_ids: List of attribute IDs to reject
            user_id: User performing the rejection
            user_role: Role of the user performing the rejection
            reason: Reason for rejection
            notes: Optional additional notes
            
        Returns:
            Dictionary with results including count and any errors
        """
        try:
            rejected_count = 0
            errors = []
            processed_versions = set()
            
            for attribute_id in attribute_ids:
                try:
                    # Get the attribute
                    attribute = await self.db.get(ScopingAttribute, attribute_id)
                    if not attribute:
                        errors.append({
                            "attribute_id": str(attribute_id),
                            "error": "Attribute not found"
                        })
                        continue
                    
                    # Track which versions we're updating
                    processed_versions.add(attribute.version_id)
                    
                    rejection_text = f"{reason}. {notes or ''}".strip()
                    
                    # Update based on user role
                    if user_role in ["Tester", "Test Executive"]:
                        # Set tester rejection
                        attribute.tester_decision = TesterDecision.DECLINE
                        attribute.tester_rationale = rejection_text
                        attribute.tester_decided_by_id = user_id
                        attribute.tester_decided_at = utc_now()
                        
                        # Mark as rejected if tester rejects
                        attribute.status = AttributeStatus.REJECTED
                        
                    elif user_role in ["Report Owner", "Report Owner Executive"]:
                        # Set report owner rejection
                        attribute.report_owner_decision = ReportOwnerDecision.REJECTEDED
                        attribute.report_owner_notes = rejection_text
                        attribute.report_owner_decided_by_id = user_id
                        attribute.report_owner_decided_at = utc_now()
                        
                        # Mark as rejected if report owner rejects
                        attribute.status = AttributeStatus.REJECTED
                        
                    else:
                        # Admin or other roles default to tester behavior
                        attribute.tester_decision = TesterDecision.DECLINE
                        attribute.tester_rationale = rejection_text
                        attribute.tester_decided_by_id = user_id
                        attribute.tester_decided_at = utc_now()
                        attribute.status = AttributeStatus.REJECTED
                    
                    attribute.updated_by_id = user_id
                    attribute.updated_at = utc_now()
                    
                    rejected_count += 1
                    
                except Exception as e:
                    logger.error(f"Error rejecting attribute {attribute_id}: {str(e)}")
                    errors.append({
                        "attribute_id": str(attribute_id),
                        "error": str(e)
                    })
            
            # Update version statistics for all affected versions
            for version_id in processed_versions:
                await self._update_version_statistics(version_id)
            
            await self.db.commit()
            
            logger.info(f"Bulk rejected {rejected_count} attributes by {user_role}")
            
            return {
                "rejected_count": rejected_count,
                "total_requested": len(attribute_ids),
                "errors": errors,
                "success": len(errors) == 0,
                "decision_type": "tester" if user_role in ["Tester", "Test Executive"] else "report_owner"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in bulk reject: {str(e)}")
            raise BusinessLogicError(f"Failed to bulk reject attributes: {str(e)}")
    
    async def bulk_approve_report_owner(
        self,
        attribute_ids: List[UUID],
        user_id: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk approve multiple scoping attributes as report owner.
        
        Args:
            attribute_ids: List of attribute IDs to approve
            user_id: User performing the approval (must be report owner)
            notes: Optional notes for the approval
            
        Returns:
            Dictionary with results including count and any errors
        """
        try:
            approved_count = 0
            errors = []
            processed_versions = set()
            
            for attribute_id in attribute_ids:
                try:
                    # Get the attribute
                    attribute = await self.db.get(ScopingAttribute, attribute_id)
                    if not attribute:
                        errors.append({
                            "attribute_id": str(attribute_id),
                            "error": "Attribute not found"
                        })
                        continue
                    
                    # Verify tester has made a decision
                    if not attribute.tester_decision:
                        errors.append({
                            "attribute_id": str(attribute_id),
                            "error": "Tester decision required before report owner approval"
                        })
                        continue
                    
                    # Track which versions we're updating
                    processed_versions.add(attribute.version_id)
                    
                    # Update report owner decision
                    attribute.report_owner_decision = ReportOwnerDecision.APPROVED
                    attribute.report_owner_notes = notes or "Bulk approved by report owner"
                    attribute.report_owner_decided_by_id = user_id
                    attribute.report_owner_decided_at = utc_now()
                    attribute.status = AttributeStatus.APPROVED
                    attribute.updated_by_id = user_id
                    attribute.updated_at = utc_now()
                    
                    approved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error approving attribute {attribute_id} as report owner: {str(e)}")
                    errors.append({
                        "attribute_id": str(attribute_id),
                        "error": str(e)
                    })
            
            # Update version statistics for all affected versions
            for version_id in processed_versions:
                await self._update_version_statistics(version_id)
            
            await self.db.commit()
            
            logger.info(f"Report owner bulk approved {approved_count} attributes")
            
            return {
                "approved_count": approved_count,
                "total_requested": len(attribute_ids),
                "errors": errors,
                "success": len(errors) == 0
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in report owner bulk approve: {str(e)}")
            raise BusinessLogicError(f"Failed to bulk approve attributes as report owner: {str(e)}")
    
    async def get_attribute_by_id(
        self,
        version_id: UUID,
        attribute_id: int
    ) -> Optional[ScopingAttribute]:
        """
        Get a scoping attribute by version_id and attribute_id.
        
        Args:
            version_id: The version ID
            attribute_id: The attribute ID (from planning phase)
            
        Returns:
            ScopingAttribute if found, None otherwise
        """
        try:
            query = select(ScopingAttribute).where(
                and_(
                    ScopingAttribute.version_id == version_id,
                    ScopingAttribute.attribute_id == attribute_id
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting attribute by ID: {str(e)}")
            return None
    
    async def make_tester_decision_by_attribute_id(
        self,
        version_id: UUID,
        attribute_id: int,
        decision: TesterDecision,
        final_scoping: bool,
        rationale: Optional[str] = None,
        override_reason: Optional[str] = None,
        user_id: int = None
    ) -> ScopingAttribute:
        """
        Make a tester decision using attribute_id.
        
        Args:
            version_id: The version ID
            attribute_id: The attribute ID (from planning phase)
            decision: The tester decision
            final_scoping: Whether attribute is scoped in
            rationale: Optional rationale
            override_reason: Optional override reason
            user_id: User making the decision
            
        Returns:
            Updated ScopingAttribute
        """
        attribute = await self.get_attribute_by_id(version_id, attribute_id)
        if not attribute:
            raise NotFoundError(f"Attribute not found for ID {attribute_id} in version {version_id}")
        
        # Now we need to update the attribute directly since it uses composite key
        attribute.tester_decision = decision
        attribute.final_scoping = final_scoping
        attribute.tester_rationale = rationale
        attribute.tester_decided_by_id = user_id
        attribute.tester_decided_at = utc_now()
        attribute.updated_by_id = user_id
        attribute.updated_at = utc_now()
        
        # Handle override
        if decision == TesterDecision.OVERRIDE:
            attribute.is_override = True
            attribute.override_reason = override_reason
        
        # Calculate status
        if attribute.has_report_owner_decision:
            attribute.status = AttributeStatus.APPROVED if attribute.report_owner_decision == ReportOwnerDecision.APPROVED else AttributeStatus.REJECTED
        else:
            attribute.status = AttributeStatus.SUBMITTED
        
        await self.db.commit()
        await self.db.refresh(attribute)
        
        return attribute
    
    async def make_report_owner_decision_by_attribute_id(
        self,
        version_id: UUID,
        attribute_id: int,
        decision: ReportOwnerDecision,
        notes: Optional[str] = None,
        user_id: int = None
    ) -> ScopingAttribute:
        """
        Make a report owner decision using attribute_id.
        
        Args:
            version_id: The version ID
            attribute_id: The attribute ID (from planning phase)
            decision: The report owner decision
            notes: Optional notes
            user_id: User making the decision
            
        Returns:
            Updated ScopingAttribute
        """
        attribute = await self.get_attribute_by_id(version_id, attribute_id)
        if not attribute:
            raise NotFoundError(f"Attribute not found for ID {attribute_id} in version {version_id}")
        
        # Update the attribute directly
        attribute.report_owner_decision = decision
        attribute.report_owner_notes = notes
        attribute.report_owner_decided_by_id = user_id
        attribute.report_owner_decided_at = utc_now()
        attribute.updated_by_id = user_id
        attribute.updated_at = utc_now()
        
        # Update status
        attribute.status = AttributeStatus.APPROVED if decision == ReportOwnerDecision.APPROVED else AttributeStatus.REJECTED
        
        await self.db.commit()
        await self.db.refresh(attribute)
        
        return attribute
    
    async def _update_version_statistics(self, version_id: UUID) -> None:
        """
        Update version statistics after bulk operations.
        
        Args:
            version_id: Version ID to update statistics for
        """
        try:
            # Get counts
            stats_query = select(
                func.count(ScopingAttribute.attribute_id).label('total'),
                func.count(
                    case(
                        (ScopingAttribute.tester_decision == TesterDecision.ACCEPT, 1)
                    )
                ).label('scoped'),
                func.count(
                    case(
                        (ScopingAttribute.tester_decision == TesterDecision.DECLINE, 1)
                    )
                ).label('declined'),
                func.count(
                    case(
                        (ScopingAttribute.tester_decision == TesterDecision.OVERRIDE, 1)
                    )
                ).label('overrides')
            ).where(ScopingAttribute.version_id == version_id)
            
            result = await self.db.execute(stats_query)
            stats = result.one()
            
            # Update version
            version = await self.db.get(ScopingVersion, version_id)
            if version:
                version.total_attributes = stats.total
                version.scoped_attributes = stats.scoped
                version.declined_attributes = stats.declined
                version.override_count = stats.overrides
                version.updated_at = utc_now()
                
        except Exception as e:
            logger.error(f"Error updating version statistics: {str(e)}")

    async def create_version_from_feedback(
        self, 
        phase_id: int, 
        parent_version_id: UUID, 
        user_id: int
    ) -> ScopingVersion:
        """
        Create a new version for resubmission after report owner feedback.
        This method replicates the data profiling resubmission pattern.
        """
        from datetime import datetime
        from uuid import uuid4
        
        try:
            # Get the parent version
            parent_version = await self.db.get(ScopingVersion, parent_version_id)
            if not parent_version:
                raise NotFoundError(f"Parent version {parent_version_id} not found")
            
            # Find the next available version number for this phase
            max_version_query = select(func.max(ScopingVersion.version_number)).where(
                ScopingVersion.phase_id == phase_id
            )
            max_version_result = await self.db.execute(max_version_query)
            max_version = max_version_result.scalar() or 0
            new_version_number = max_version + 1
            new_version = ScopingVersion(
                version_id=uuid4(),
                phase_id=phase_id,
                version_number=new_version_number,
                version_status=VersionStatus.DRAFT,
                parent_version_id=parent_version_id,
                workflow_execution_id=parent_version.workflow_execution_id,
                workflow_run_id=parent_version.workflow_run_id,
                activity_name=parent_version.activity_name,
                created_by_id=user_id,
                updated_by_id=user_id
            )
            self.db.add(new_version)
            await self.db.flush()
            
            # Copy attributes from parent version, allowing tester to update decisions
            attributes_query = select(ScopingAttribute).where(
                ScopingAttribute.version_id == parent_version_id
            )
            attributes_result = await self.db.execute(attributes_query)
            attributes = attributes_result.scalars().all()
            
            for attr in attributes:
                # For attributes with report owner feedback, copy the attribute but reset tester decision
                # This allows tester to make new decisions based on feedback
                new_attribute = ScopingAttribute(
                    version_id=new_version.version_id,
                    phase_id=attr.phase_id,
                    attribute_id=attr.attribute_id,
                    
                    # Copy LLM recommendation data
                    llm_recommendation=attr.llm_recommendation,
                    llm_provider=attr.llm_provider,
                    llm_confidence_score=attr.llm_confidence_score,
                    llm_rationale=attr.llm_rationale,
                    llm_processing_time_ms=attr.llm_processing_time_ms,
                    llm_request_payload=attr.llm_request_payload,
                    llm_response_payload=attr.llm_response_payload,
                    
                    # Copy tester decisions - tester can amend these later
                    tester_decision=attr.tester_decision,
                    final_scoping=attr.final_scoping,
                    tester_rationale=attr.tester_rationale,
                    tester_decided_by_id=attr.tester_decided_by_id,
                    tester_decided_at=attr.tester_decided_at,
                    
                    # Keep report owner decisions so feedback tab remains visible while tester makes changes
                    # These will be reset when tester submits the version for approval
                    report_owner_decision=attr.report_owner_decision,
                    report_owner_notes=attr.report_owner_notes,
                    report_owner_decided_by_id=attr.report_owner_decided_by_id,
                    report_owner_decided_at=attr.report_owner_decided_at,
                    
                    # Copy other metadata
                    is_override=attr.is_override if hasattr(attr, 'is_override') else False,
                    override_reason=attr.override_reason if hasattr(attr, 'override_reason') else None,
                    # These fields don't exist on ScopingAttribute - skip them
                    # is_cde=attr.is_cde,
                    # has_historical_issues=attr.has_historical_issues,
                    # is_primary_key=attr.is_primary_key,
                    data_quality_score=attr.data_quality_score,
                    data_quality_issues=attr.data_quality_issues,
                    expected_source_documents=attr.expected_source_documents,
                    search_keywords=attr.search_keywords,
                    risk_factors=attr.risk_factors,
                    status=AttributeStatus.PENDING,
                    
                    created_by_id=user_id,
                    updated_by_id=user_id
                )
                self.db.add(new_attribute)
            
            # Update version statistics
            await self._update_version_statistics(new_version.version_id)
            
            logger.info(f"Created new version {new_version.version_id} (v{new_version_number}) from feedback on parent {parent_version_id}")
            return new_version
            
        except Exception as e:
            logger.error(f"Error creating version from feedback: {str(e)}")
            raise