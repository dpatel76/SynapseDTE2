"""
Unit tests for Scoping V2 models and services

This module contains comprehensive unit tests for the new consolidated scoping system,
testing models, services, and business logic.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.scoping import (
    ScopingVersion, ScopingAttribute,
    VersionStatus, TesterDecision, ReportOwnerDecision, AttributeStatus
)
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.user import User
from app.services.scoping_service import ScopingService
from app.core.exceptions import (
    ValidationError, NotFoundError, ConflictError, BusinessLogicError
)


class TestScopingVersion:
    """Test cases for ScopingVersion model"""
    
    def test_scoping_version_creation(self):
        """Test creating a new scoping version"""
        version = ScopingVersion(
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            total_attributes=10,
            scoped_attributes=6,
            declined_attributes=4,
            override_count=2,
            cde_count=3,
            recommendation_accuracy=0.8,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert version.phase_id == 1
        assert version.version_number == 1
        assert version.version_status == VersionStatus.DRAFT
        assert version.total_attributes == 10
        assert version.scoped_attributes == 6
        assert version.declined_attributes == 4
        assert version.override_count == 2
        assert version.cde_count == 3
        assert version.recommendation_accuracy == 0.8
    
    def test_version_lifecycle_properties(self):
        """Test version lifecycle properties"""
        # Test draft version
        draft_version = ScopingVersion(
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            total_attributes=5,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert draft_version.is_draft is True
        assert draft_version.is_pending_approval is False
        assert draft_version.is_approved is False
        assert draft_version.is_rejected is False
        assert draft_version.is_superseded is False
        assert draft_version.can_be_edited is True
        assert draft_version.can_be_submitted is True
        assert draft_version.can_be_approved is False
        assert draft_version.is_current is False
        
        # Test pending approval version
        pending_version = ScopingVersion(
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.PENDING_APPROVAL,
            total_attributes=5,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert pending_version.is_draft is False
        assert pending_version.is_pending_approval is True
        assert pending_version.can_be_edited is False
        assert pending_version.can_be_submitted is False
        assert pending_version.can_be_approved is True
        
        # Test approved version
        approved_version = ScopingVersion(
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.APPROVED,
            total_attributes=5,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert approved_version.is_approved is True
        assert approved_version.is_current is True
        assert approved_version.can_be_edited is False
        assert approved_version.can_be_submitted is False
        assert approved_version.can_be_approved is False
        
        # Test rejected version
        rejected_version = ScopingVersion(
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.REJECTED,
            total_attributes=5,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert rejected_version.is_rejected is True
        assert rejected_version.can_be_edited is True
        assert rejected_version.can_be_submitted is False
        assert rejected_version.can_be_approved is False
    
    def test_version_percentage_calculations(self):
        """Test percentage calculations"""
        version = ScopingVersion(
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            total_attributes=10,
            scoped_attributes=6,
            declined_attributes=4,
            override_count=2,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert version.scoping_percentage == 60.0
        assert version.override_percentage == 20.0
        
        # Test with zero attributes
        empty_version = ScopingVersion(
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            total_attributes=0,
            scoped_attributes=0,
            declined_attributes=0,
            override_count=0,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert empty_version.scoping_percentage == 0.0
        assert empty_version.override_percentage == 0.0
    
    def test_version_validation(self):
        """Test version field validation"""
        version = ScopingVersion(
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            created_by_id=1,
            updated_by_id=1
        )
        
        # Test version number validation
        with pytest.raises(ValueError, match="Version number must be positive"):
            version.validate_version_number('version_number', 0)
        
        with pytest.raises(ValueError, match="Version number must be positive"):
            version.validate_version_number('version_number', -1)
        
        # Test count validation
        with pytest.raises(ValueError, match="total_attributes cannot be negative"):
            version.validate_counts('total_attributes', -1)
        
        # Test accuracy validation
        with pytest.raises(ValueError, match="Recommendation accuracy must be between 0 and 1"):
            version.validate_accuracy('recommendation_accuracy', 1.5)
        
        with pytest.raises(ValueError, match="Recommendation accuracy must be between 0 and 1"):
            version.validate_accuracy('recommendation_accuracy', -0.1)
    
    def test_get_summary_stats(self):
        """Test version summary statistics"""
        version = ScopingVersion(
            version_id=uuid4(),
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            total_attributes=10,
            scoped_attributes=6,
            declined_attributes=4,
            override_count=2,
            cde_count=3,
            recommendation_accuracy=0.8,
            created_by_id=1,
            updated_by_id=1
        )
        
        stats = version.get_summary_stats()
        
        assert stats['version_number'] == 1
        assert stats['status'] == 'draft'
        assert stats['total_attributes'] == 10
        assert stats['scoped_attributes'] == 6
        assert stats['declined_attributes'] == 4
        assert stats['override_count'] == 2
        assert stats['cde_count'] == 3
        assert stats['scoping_percentage'] == 60.0
        assert stats['override_percentage'] == 20.0
        assert stats['recommendation_accuracy'] == 0.8
        assert stats['can_be_edited'] is True
        assert stats['can_be_submitted'] is True
        assert stats['can_be_approved'] is False
        assert stats['is_current'] is False


class TestScopingAttribute:
    """Test cases for ScopingAttribute model"""
    
    def test_scoping_attribute_creation(self):
        """Test creating a new scoping attribute"""
        llm_recommendation = {
            "recommended_action": "test",
            "confidence_score": 0.9,
            "rationale": "High-risk attribute requiring testing"
        }
        
        attribute = ScopingAttribute(
            version_id=uuid4(),
            phase_id=1,
            planning_attribute_id=1,
            llm_recommendation=llm_recommendation,
            llm_provider="openai",
            llm_confidence_score=0.9,
            llm_rationale="High-risk attribute requiring testing",
            status=AttributeStatus.PENDING,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert attribute.version_id is not None
        assert attribute.phase_id == 1
        assert attribute.planning_attribute_id == 1
        assert attribute.llm_recommendation == llm_recommendation
        assert attribute.llm_provider == "openai"
        assert attribute.llm_confidence_score == 0.9
        assert attribute.llm_rationale == "High-risk attribute requiring testing"
        assert attribute.status == AttributeStatus.PENDING
    
    def test_attribute_decision_properties(self):
        """Test attribute decision properties"""
        attribute = ScopingAttribute(
            version_id=uuid4(),
            phase_id=1,
            planning_attribute_id=1,
            llm_recommendation={"recommended_action": "test"},
            status=AttributeStatus.PENDING,
            created_by_id=1,
            updated_by_id=1
        )
        
        # Test initial state
        assert attribute.has_tester_decision is False
        assert attribute.has_report_owner_decision is False
        assert attribute.is_pending_decision is True
        assert attribute.is_scoped_in is False
        assert attribute.is_scoped_out is False
        
        # Test after tester decision
        attribute.tester_decision = TesterDecision.ACCEPT
        attribute.final_scoping = True
        attribute.tester_decided_by_id = 1
        attribute.tester_decided_at = datetime.utcnow()
        
        assert attribute.has_tester_decision is True
        assert attribute.is_pending_decision is False
        assert attribute.is_scoped_in is True
        assert attribute.is_scoped_out is False
        
        # Test after report owner decision
        attribute.report_owner_decision = ReportOwnerDecision.APPROVED
        attribute.report_owner_decided_by_id = 1
        attribute.report_owner_decided_at = datetime.utcnow()
        
        assert attribute.has_report_owner_decision is True
    
    def test_llm_recommendation_properties(self):
        """Test LLM recommendation properties"""
        # Test with test recommendation
        test_attribute = ScopingAttribute(
            version_id=uuid4(),
            phase_id=1,
            planning_attribute_id=1,
            llm_recommendation={"recommended_action": "test", "confidence_score": 0.9},
            tester_decision=TesterDecision.ACCEPT,
            final_scoping=True,
            status=AttributeStatus.PENDING,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert test_attribute.llm_recommended_action == "test"
        assert test_attribute.llm_agreed_with_tester is True
        
        # Test with skip recommendation
        skip_attribute = ScopingAttribute(
            version_id=uuid4(),
            phase_id=1,
            planning_attribute_id=1,
            llm_recommendation={"recommended_action": "skip", "confidence_score": 0.8},
            tester_decision=TesterDecision.DECLINE,
            final_scoping=False,
            status=AttributeStatus.PENDING,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert skip_attribute.llm_recommended_action == "skip"
        assert skip_attribute.llm_agreed_with_tester is True
        
        # Test disagreement
        disagree_attribute = ScopingAttribute(
            version_id=uuid4(),
            phase_id=1,
            planning_attribute_id=1,
            llm_recommendation={"recommended_action": "test", "confidence_score": 0.6},
            tester_decision=TesterDecision.DECLINE,
            final_scoping=False,
            status=AttributeStatus.PENDING,
            created_by_id=1,
            updated_by_id=1
        )
        
        assert disagree_attribute.llm_agreed_with_tester is False
    
    def test_attribute_validation(self):
        """Test attribute field validation"""
        attribute = ScopingAttribute(
            version_id=uuid4(),
            phase_id=1,
            planning_attribute_id=1,
            llm_recommendation={"recommended_action": "test"},
            status=AttributeStatus.PENDING,
            created_by_id=1,
            updated_by_id=1
        )
        
        # Test confidence score validation
        with pytest.raises(ValueError, match="LLM confidence score must be between 0 and 1"):
            attribute.validate_confidence_score('llm_confidence_score', 1.5)
        
        # Test data quality score validation
        with pytest.raises(ValueError, match="Data quality score must be between 0 and 1"):
            attribute.validate_data_quality_score('data_quality_score', -0.1)
        
        # Test processing time validation
        with pytest.raises(ValueError, match="Processing time cannot be negative"):
            attribute.validate_processing_time('llm_processing_time_ms', -100)
    
    def test_decision_timeline(self):
        """Test decision timeline generation"""
        created_at = datetime.utcnow()
        decided_at = datetime.utcnow()
        
        attribute = ScopingAttribute(
            version_id=uuid4(),
            phase_id=1,
            planning_attribute_id=1,
            llm_recommendation={"recommended_action": "test"},
            tester_decision=TesterDecision.ACCEPT,
            final_scoping=True,
            tester_decided_by_id=1,
            tester_decided_at=decided_at,
            status=AttributeStatus.PENDING,
            created_at=created_at,
            created_by_id=1,
            updated_by_id=1
        )
        
        timeline = attribute.decision_timeline
        
        assert len(timeline) == 2
        assert timeline[0]['event'] == 'attribute_created'
        assert timeline[0]['timestamp'] == created_at
        assert timeline[1]['event'] == 'tester_decision'
        assert timeline[1]['timestamp'] == decided_at
        assert timeline[1]['decision'] == TesterDecision.ACCEPT
        assert timeline[1]['scoping'] is True
    
    def test_get_decision_summary(self):
        """Test decision summary generation"""
        attribute = ScopingAttribute(
            attribute_id=uuid4(),
            version_id=uuid4(),
            phase_id=1,
            planning_attribute_id=1,
            llm_recommendation={"recommended_action": "test", "confidence_score": 0.9},
            llm_provider="openai",
            llm_confidence_score=0.9,
            llm_rationale="High-risk attribute",
            tester_decision=TesterDecision.ACCEPT,
            final_scoping=True,
            tester_rationale="Agree with LLM",
            tester_decided_by_id=1,
            tester_decided_at=datetime.utcnow(),
            is_cde=True,
            is_primary_key=False,
            data_quality_score=0.8,
            status=AttributeStatus.SUBMITTED,
            created_by_id=1,
            updated_by_id=1
        )
        
        summary = attribute.get_decision_summary()
        
        assert summary['planning_attribute_id'] == 1
        assert summary['status'] == 'submitted'
        assert summary['llm_recommendation']['recommended_action'] == "test"
        assert summary['llm_recommendation']['confidence_score'] == 0.9
        assert summary['tester_decision']['decision'] == 'accept'
        assert summary['tester_decision']['final_scoping'] is True
        assert summary['flags']['is_cde'] is True
        assert summary['flags']['is_primary_key'] is False
        assert summary['data_quality']['score'] == 0.8
        assert summary['llm_agreed_with_tester'] is True


class TestScopingService:
    """Test cases for ScopingService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock(spec=Session)
        db.get = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.rollback = AsyncMock()
        db.execute = AsyncMock()
        return db
    
    @pytest.fixture
    def scoping_service(self, mock_db):
        """Create ScopingService instance with mock database"""
        return ScopingService(mock_db)
    
    @pytest.mark.asyncio
    async def test_create_version_success(self, scoping_service, mock_db):
        """Test successful version creation"""
        # Mock phase exists
        mock_phase = Mock(spec=WorkflowPhase)
        mock_phase.phase_id = 1
        mock_db.get.return_value = mock_phase
        
        # Mock version number calculation
        mock_db.execute.return_value.scalar.return_value = 0
        
        # Mock created version
        mock_version = Mock(spec=ScopingVersion)
        mock_version.version_id = uuid4()
        mock_version.phase_id = 1
        mock_version.version_number = 1
        mock_version.version_status = VersionStatus.DRAFT
        
        version = await scoping_service.create_version(
            phase_id=1,
            user_id=1,
            notes="Test version"
        )
        
        # Verify database interactions
        mock_db.get.assert_called_once()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_version_phase_not_found(self, scoping_service, mock_db):
        """Test version creation with non-existent phase"""
        # Mock phase not found
        mock_db.get.return_value = None
        
        with pytest.raises(NotFoundError, match="Phase with ID 999 not found"):
            await scoping_service.create_version(
                phase_id=999,
                user_id=1
            )
    
    @pytest.mark.asyncio
    async def test_create_version_database_error(self, scoping_service, mock_db):
        """Test version creation with database error"""
        # Mock phase exists
        mock_phase = Mock(spec=WorkflowPhase)
        mock_db.get.return_value = mock_phase
        
        # Mock database error
        mock_db.execute.return_value.scalar.return_value = 0
        mock_db.commit.side_effect = IntegrityError("Database error", None, None)
        
        with pytest.raises(ConflictError, match="Failed to create scoping version"):
            await scoping_service.create_version(
                phase_id=1,
                user_id=1
            )
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_attributes_to_version_success(self, scoping_service, mock_db):
        """Test successful attribute addition"""
        version_id = uuid4()
        
        # Mock version exists and can be edited
        mock_version = Mock(spec=ScopingVersion)
        mock_version.version_id = version_id
        mock_version.version_status = VersionStatus.DRAFT
        mock_version.can_be_edited = True
        mock_version.phase_id = 1
        
        scoping_service.get_version = AsyncMock(return_value=mock_version)
        
        # Mock planning attribute exists
        mock_planning_attr = Mock(spec=ReportAttribute)
        mock_planning_attr.id = 1
        mock_db.get.return_value = mock_planning_attr
        
        # Mock no existing attribute
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        planning_attribute_ids = [1, 2]
        llm_recommendations = [
            {"recommended_action": "test", "confidence_score": 0.9},
            {"recommended_action": "skip", "confidence_score": 0.7}
        ]
        
        attributes = await scoping_service.add_attributes_to_version(
            version_id=version_id,
            planning_attribute_ids=planning_attribute_ids,
            llm_recommendations=llm_recommendations,
            user_id=1
        )
        
        # Verify database interactions
        mock_db.commit.assert_called_once()
        assert mock_db.add.call_count == 2  # Two attributes added
    
    @pytest.mark.asyncio
    async def test_add_attributes_version_not_found(self, scoping_service, mock_db):
        """Test attribute addition with non-existent version"""
        version_id = uuid4()
        
        scoping_service.get_version = AsyncMock(return_value=None)
        
        with pytest.raises(NotFoundError, match=f"Version {version_id} not found"):
            await scoping_service.add_attributes_to_version(
                version_id=version_id,
                planning_attribute_ids=[1],
                llm_recommendations=[{"recommended_action": "test"}],
                user_id=1
            )
    
    @pytest.mark.asyncio
    async def test_add_attributes_version_cannot_be_edited(self, scoping_service, mock_db):
        """Test attribute addition with non-editable version"""
        version_id = uuid4()
        
        # Mock version exists but cannot be edited
        mock_version = Mock(spec=ScopingVersion)
        mock_version.version_id = version_id
        mock_version.version_status = VersionStatus.APPROVED
        mock_version.can_be_edited = False
        
        scoping_service.get_version = AsyncMock(return_value=mock_version)
        
        with pytest.raises(BusinessLogicError, match="cannot be edited"):
            await scoping_service.add_attributes_to_version(
                version_id=version_id,
                planning_attribute_ids=[1],
                llm_recommendations=[{"recommended_action": "test"}],
                user_id=1
            )
    
    @pytest.mark.asyncio
    async def test_make_tester_decision_success(self, scoping_service, mock_db):
        """Test successful tester decision"""
        attribute_id = uuid4()
        version_id = uuid4()
        
        # Mock attribute exists
        mock_attribute = Mock(spec=ScopingAttribute)
        mock_attribute.attribute_id = attribute_id
        mock_attribute.version_id = version_id
        mock_db.get.return_value = mock_attribute
        
        # Mock version can be edited
        mock_version = Mock(spec=ScopingVersion)
        mock_version.can_be_edited = True
        mock_version.version_status = VersionStatus.DRAFT
        
        scoping_service.get_version = AsyncMock(return_value=mock_version)
        
        attribute = await scoping_service.make_tester_decision(
            attribute_id=attribute_id,
            decision=TesterDecision.ACCEPT,
            final_scoping=True,
            rationale="Agree with LLM recommendation",
            user_id=1
        )
        
        # Verify attribute was updated
        assert mock_attribute.tester_decision == TesterDecision.ACCEPT
        assert mock_attribute.final_scoping is True
        assert mock_attribute.tester_rationale == "Agree with LLM recommendation"
        assert mock_attribute.tester_decided_by_id == 1
        assert mock_attribute.status == AttributeStatus.SUBMITTED
        
        # Verify database interactions
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_tester_decision_override_without_reason(self, scoping_service, mock_db):
        """Test tester decision with override but no reason"""
        attribute_id = uuid4()
        version_id = uuid4()
        
        # Mock attribute exists
        mock_attribute = Mock(spec=ScopingAttribute)
        mock_attribute.attribute_id = attribute_id
        mock_attribute.version_id = version_id
        mock_db.get.return_value = mock_attribute
        
        # Mock version can be edited
        mock_version = Mock(spec=ScopingVersion)
        mock_version.can_be_edited = True
        mock_version.version_status = VersionStatus.DRAFT
        
        scoping_service.get_version = AsyncMock(return_value=mock_version)
        
        with pytest.raises(ValidationError, match="Override reason is required"):
            await scoping_service.make_tester_decision(
                attribute_id=attribute_id,
                decision=TesterDecision.OVERRIDE,
                final_scoping=True,
                user_id=1
            )
    
    @pytest.mark.asyncio
    async def test_submit_version_for_approval_success(self, scoping_service, mock_db):
        """Test successful version submission"""
        version_id = uuid4()
        
        # Mock version with attributes that have tester decisions
        mock_attribute = Mock(spec=ScopingAttribute)
        mock_attribute.has_tester_decision = True
        
        mock_version = Mock(spec=ScopingVersion)
        mock_version.version_id = version_id
        mock_version.can_be_submitted = True
        mock_version.version_status = VersionStatus.DRAFT
        mock_version.attributes = [mock_attribute]
        
        scoping_service.get_version_with_attributes = AsyncMock(return_value=mock_version)
        
        version = await scoping_service.submit_version_for_approval(
            version_id=version_id,
            submission_notes="Ready for review",
            user_id=1
        )
        
        # Verify version was updated
        assert mock_version.version_status == VersionStatus.PENDING_APPROVAL
        assert mock_version.submission_notes == "Ready for review"
        assert mock_version.submitted_by_id == 1
        
        # Verify database interactions
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_version_with_pending_decisions(self, scoping_service, mock_db):
        """Test version submission with pending attribute decisions"""
        version_id = uuid4()
        
        # Mock version with attributes that don't have tester decisions
        mock_attribute = Mock(spec=ScopingAttribute)
        mock_attribute.has_tester_decision = False
        
        mock_version = Mock(spec=ScopingVersion)
        mock_version.version_id = version_id
        mock_version.can_be_submitted = True
        mock_version.version_status = VersionStatus.DRAFT
        mock_version.attributes = [mock_attribute]
        
        scoping_service.get_version_with_attributes = AsyncMock(return_value=mock_version)
        
        with pytest.raises(BusinessLogicError, match="Cannot submit version with .* pending attribute decisions"):
            await scoping_service.submit_version_for_approval(
                version_id=version_id,
                user_id=1
            )
    
    @pytest.mark.asyncio
    async def test_approve_version_success(self, scoping_service, mock_db):
        """Test successful version approval"""
        version_id = uuid4()
        
        # Mock version can be approved
        mock_version = Mock(spec=ScopingVersion)
        mock_version.version_id = version_id
        mock_version.can_be_approved = True
        mock_version.version_status = VersionStatus.PENDING_APPROVAL
        mock_version.phase_id = 1
        
        scoping_service.get_version = AsyncMock(return_value=mock_version)
        scoping_service._supersede_current_version = AsyncMock()
        
        version = await scoping_service.approve_version(
            version_id=version_id,
            approval_notes="Approved for implementation",
            user_id=1
        )
        
        # Verify version was updated
        assert mock_version.version_status == VersionStatus.APPROVED
        assert mock_version.approval_notes == "Approved for implementation"
        assert mock_version.approved_by_id == 1
        
        # Verify supersede was called
        scoping_service._supersede_current_version.assert_called_once_with(1, 1)
        
        # Verify database interactions
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_version_statistics(self, scoping_service, mock_db):
        """Test version statistics calculation"""
        version_id = uuid4()
        
        # Mock version with attributes
        mock_attributes = [
            Mock(spec=ScopingAttribute, is_scoped_in=True, is_scoped_out=False, 
                 is_override=False, is_cde=True, is_pending_decision=False, 
                 has_tester_decision=True, has_report_owner_decision=False,
                 report_owner_decision=None, llm_agreed_with_tester=True),
            Mock(spec=ScopingAttribute, is_scoped_in=False, is_scoped_out=True, 
                 is_override=True, is_cde=False, is_pending_decision=False, 
                 has_tester_decision=True, has_report_owner_decision=True,
                 report_owner_decision=ReportOwnerDecision.APPROVED, llm_agreed_with_tester=False),
            Mock(spec=ScopingAttribute, is_scoped_in=False, is_scoped_out=False, 
                 is_override=False, is_cde=False, is_pending_decision=True, 
                 has_tester_decision=False, has_report_owner_decision=False,
                 report_owner_decision=None, llm_agreed_with_tester=None)
        ]
        
        mock_version = Mock(spec=ScopingVersion)
        mock_version.version_id = version_id
        mock_version.version_number = 1
        mock_version.version_status = VersionStatus.DRAFT
        mock_version.attributes = mock_attributes
        mock_version.created_at = datetime.utcnow()
        mock_version.submitted_at = None
        mock_version.approved_at = None
        mock_version.can_be_edited = True
        mock_version.can_be_submitted = True
        mock_version.can_be_approved = False
        mock_version.is_current = False
        
        scoping_service.get_version_with_attributes = AsyncMock(return_value=mock_version)
        
        stats = await scoping_service.get_version_statistics(version_id)
        
        # Verify statistics
        assert stats['total_attributes'] == 3
        assert stats['scoped_attributes'] == 1
        assert stats['declined_attributes'] == 1
        assert stats['override_count'] == 1
        assert stats['cde_count'] == 1
        assert stats['scoping_percentage'] == 33.33333333333333
        assert stats['override_percentage'] == 33.33333333333333
        assert stats['decision_progress']['pending_decisions'] == 1
        assert stats['decision_progress']['completed_decisions'] == 2
        assert stats['decision_progress']['progress_percentage'] == 66.66666666666666
        assert stats['report_owner_progress']['pending_decisions'] == 1
        assert stats['report_owner_progress']['approved_decisions'] == 1
        assert stats['llm_accuracy'] == 0.5  # 1 out of 2 accurate predictions
        assert stats['can_be_edited'] is True
        assert stats['can_be_submitted'] is True
        assert stats['can_be_approved'] is False
        assert stats['is_current'] is False
    
    @pytest.mark.asyncio
    async def test_copy_version_success(self, scoping_service, mock_db):
        """Test successful version copying"""
        source_version_id = uuid4()
        new_version_id = uuid4()
        
        # Mock source version with attributes
        mock_source_attribute = Mock(spec=ScopingAttribute)
        mock_source_attribute.planning_attribute_id = 1
        mock_source_attribute.llm_recommendation = {"recommended_action": "test"}
        mock_source_attribute.llm_provider = "openai"
        mock_source_attribute.has_tester_decision = True
        mock_source_attribute.tester_decision = TesterDecision.ACCEPT
        mock_source_attribute.final_scoping = True
        
        mock_source_version = Mock(spec=ScopingVersion)
        mock_source_version.version_id = source_version_id
        mock_source_version.phase_id = 1
        mock_source_version.workflow_activity_id = 1
        mock_source_version.attributes = [mock_source_attribute]
        
        # Mock new version creation
        mock_new_version = Mock(spec=ScopingVersion)
        mock_new_version.version_id = new_version_id
        mock_new_version.phase_id = 1
        
        scoping_service.get_version_with_attributes = AsyncMock(return_value=mock_source_version)
        scoping_service.create_version = AsyncMock(return_value=mock_new_version)
        
        new_version = await scoping_service.copy_version(
            source_version_id=source_version_id,
            user_id=1,
            copy_attributes=True,
            copy_decisions=True
        )
        
        # Verify new version was created
        scoping_service.create_version.assert_called_once()
        
        # Verify parent relationship was set
        assert mock_new_version.parent_version_id == source_version_id
        
        # Verify database interactions
        mock_db.add.assert_called()  # Attribute was added
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])