"""
Unit tests for Sample Selection V2 models and services
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.sample_selection import (
    SampleSelectionVersion, SampleSelectionSample,
    VersionStatus, SampleCategory, SampleDecision, SampleSource
)
from app.models.workflow import WorkflowPhase
from app.models.user import User
from app.models.lob import LOB
from app.services.sample_selection_service import SampleSelectionService
from app.services.sample_selection_table_service import SampleSelectionTableService
from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError


class TestSampleSelectionVersionModel:
    """Test SampleSelectionVersion model"""
    
    def test_version_creation(self):
        """Test creating a sample selection version"""
        version = SampleSelectionVersion(
            version_id=uuid.uuid4(),
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            workflow_execution_id="test-execution-id",
            workflow_run_id="test-run-id",
            activity_name="test-activity",
            selection_criteria={"test": "criteria"},
            target_sample_size=100,
            actual_sample_size=0,
            created_by_id=1
        )
        
        assert version.version_number == 1
        assert version.version_status == VersionStatus.DRAFT
        assert version.target_sample_size == 100
        assert version.actual_sample_size == 0
        assert version.selection_criteria == {"test": "criteria"}
    
    def test_version_properties(self):
        """Test version properties"""
        # Test draft version
        draft_version = SampleSelectionVersion(
            version_status=VersionStatus.DRAFT,
            target_sample_size=100,
            actual_sample_size=50
        )
        assert draft_version.can_be_edited is True
        assert draft_version.is_current_version is False
        
        # Test approved version
        approved_version = SampleSelectionVersion(
            version_status=VersionStatus.APPROVED,
            target_sample_size=100,
            actual_sample_size=50
        )
        assert approved_version.can_be_edited is False
        assert approved_version.is_current_version is True
        
        # Test pending approval version
        pending_version = SampleSelectionVersion(
            version_status=VersionStatus.PENDING_APPROVAL,
            target_sample_size=100,
            actual_sample_size=50
        )
        assert pending_version.can_be_edited is False
        assert pending_version.is_current_version is True
    
    def test_version_metadata(self):
        """Test version metadata generation"""
        version = SampleSelectionVersion(
            version_id=uuid.uuid4(),
            version_number=1,
            version_status=VersionStatus.DRAFT,
            target_sample_size=100,
            actual_sample_size=50,
            distribution_metrics={"clean": 15, "anomaly": 25, "boundary": 10},
            intelligent_sampling_config={"distribution": "30/50/20"}
        )
        
        metadata = version.get_metadata()
        
        assert metadata["version_number"] == 1
        assert metadata["version_status"] == "draft"
        assert metadata["target_sample_size"] == 100
        assert metadata["actual_sample_size"] == 50
        assert metadata["distribution_metrics"] == {"clean": 15, "anomaly": 25, "boundary": 10}
        assert metadata["intelligent_sampling_config"] == {"distribution": "30/50/20"}


class TestSampleSelectionSampleModel:
    """Test SampleSelectionSample model"""
    
    def test_sample_creation(self):
        """Test creating a sample"""
        sample = SampleSelectionSample(
            sample_id=uuid.uuid4(),
            version_id=uuid.uuid4(),
            phase_id=1,
            lob_id=1,
            sample_identifier="TEST_001",
            sample_data={"field": "value"},
            sample_category=SampleCategory.CLEAN,
            sample_source=SampleSource.MANUAL,
            risk_score=0.3,
            confidence_score=0.8
        )
        
        assert sample.sample_identifier == "TEST_001"
        assert sample.sample_category == SampleCategory.CLEAN
        assert sample.sample_source == SampleSource.MANUAL
        assert sample.risk_score == 0.3
        assert sample.confidence_score == 0.8
    
    def test_sample_decision_properties(self):
        """Test sample decision properties"""
        sample = SampleSelectionSample(
            tester_decision=SampleDecision.INCLUDE,
            report_owner_decision=SampleDecision.INCLUDE
        )
        assert sample.is_approved is True
        assert sample.is_rejected is False
        assert sample.needs_review is False
        
        sample.report_owner_decision = SampleDecision.EXCLUDE
        assert sample.is_approved is False
        assert sample.is_rejected is True
        assert sample.needs_review is False
        
        sample.tester_decision = SampleDecision.PENDING
        assert sample.is_approved is False
        assert sample.is_rejected is False
        assert sample.needs_review is True
    
    def test_sample_carry_forward_properties(self):
        """Test carry forward properties"""
        sample = SampleSelectionSample(
            sample_source=SampleSource.CARRIED_FORWARD,
            carried_from_version_id=uuid.uuid4()
        )
        assert sample.is_carried_forward is True
        
        sample.sample_source = SampleSource.MANUAL
        assert sample.is_carried_forward is False
    
    def test_sample_decision_summary(self):
        """Test decision summary generation"""
        sample = SampleSelectionSample(
            tester_decision=SampleDecision.INCLUDE,
            report_owner_decision=SampleDecision.EXCLUDE,
            tester_decision_at=datetime.utcnow(),
            report_owner_decision_at=datetime.utcnow()
        )
        
        summary = sample.get_decision_summary()
        
        assert summary["tester_decision"] == "include"
        assert summary["report_owner_decision"] == "exclude"
        assert summary["final_status"] == "rejected"
        assert summary["needs_review"] is False
    
    def test_sample_metadata(self):
        """Test sample metadata generation"""
        sample = SampleSelectionSample(
            sample_id=uuid.uuid4(),
            sample_identifier="TEST_001",
            sample_category=SampleCategory.ANOMALY,
            sample_source=SampleSource.LLM,
            risk_score=0.8,
            confidence_score=0.9,
            generation_metadata={"method": "intelligent"}
        )
        
        metadata = sample.get_metadata()
        
        assert metadata["sample_identifier"] == "TEST_001"
        assert metadata["sample_category"] == "anomaly"
        assert metadata["sample_source"] == "llm"
        assert metadata["risk_score"] == 0.8
        assert metadata["confidence_score"] == 0.9
        assert metadata["generation_metadata"] == {"method": "intelligent"}


class TestSampleSelectionService:
    """Test SampleSelectionService"""
    
    @pytest.fixture
    def service(self):
        """Create service instance"""
        return SampleSelectionService()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = Mock(spec=AsyncSession)
        db.add = Mock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.get = AsyncMock()
        db.execute = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user"""
        user = Mock(spec=User)
        user.user_id = 1
        user.full_name = "Test User"
        return user
    
    @pytest.fixture
    def mock_phase(self):
        """Create mock workflow phase"""
        phase = Mock(spec=WorkflowPhase)
        phase.phase_id = 1
        return phase
    
    @pytest_asyncio.async_fixture
    async def test_create_version(self, service, mock_db, mock_user, mock_phase):
        """Test creating a version"""
        # Mock phase lookup
        mock_db.get.return_value = mock_phase
        
        # Mock execute for version number query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        version = await service.create_version(
            db=mock_db,
            phase_id=1,
            selection_criteria={"test": "criteria"},
            target_sample_size=100,
            workflow_execution_id="test-execution",
            workflow_run_id="test-run",
            activity_name="test-activity",
            created_by_id=1
        )
        
        assert version.phase_id == 1
        assert version.version_number == 1
        assert version.version_status == VersionStatus.DRAFT
        assert version.target_sample_size == 100
        assert version.actual_sample_size == 0
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest_asyncio.async_fixture
    async def test_create_version_phase_not_found(self, service, mock_db):
        """Test creating version with non-existent phase"""
        # Mock phase lookup returning None
        mock_db.get.return_value = None
        
        with pytest.raises(NotFoundError):
            await service.create_version(
                db=mock_db,
                phase_id=999,
                selection_criteria={"test": "criteria"},
                target_sample_size=100,
                workflow_execution_id="test-execution",
                workflow_run_id="test-run",
                activity_name="test-activity",
                created_by_id=1
            )
    
    @pytest_asyncio.async_fixture
    async def test_add_samples_to_version(self, service, mock_db, mock_user):
        """Test adding samples to version"""
        # Create mock version
        version = Mock(spec=SampleSelectionVersion)
        version.version_id = uuid.uuid4()
        version.phase_id = 1
        version.can_be_edited = True
        
        # Mock get_version_by_id
        with patch.object(service, 'get_version_by_id', return_value=version):
            # Mock _get_sample_count and _calculate_distribution_metrics
            with patch.object(service, '_get_sample_count', return_value=2):
                with patch.object(service, '_calculate_distribution_metrics', return_value={"clean": 2}):
                    
                    samples_data = [
                        {
                            "lob_id": 1,
                            "sample_identifier": "TEST_001",
                            "sample_data": {"field": "value1"},
                            "sample_category": "clean",
                            "sample_source": "manual",
                            "risk_score": 0.2
                        },
                        {
                            "lob_id": 1,
                            "sample_identifier": "TEST_002",
                            "sample_data": {"field": "value2"},
                            "sample_category": "clean",
                            "sample_source": "manual",
                            "risk_score": 0.3
                        }
                    ]
                    
                    samples = await service.add_samples_to_version(
                        db=mock_db,
                        version_id=version.version_id,
                        samples_data=samples_data,
                        current_user_id=1
                    )
                    
                    assert len(samples) == 2
                    assert samples[0].sample_identifier == "TEST_001"
                    assert samples[1].sample_identifier == "TEST_002"
                    
                    # Verify samples were added to database
                    mock_db.add_all.assert_called_once()
                    mock_db.commit.assert_called_once()
    
    @pytest_asyncio.async_fixture
    async def test_add_samples_to_non_editable_version(self, service, mock_db):
        """Test adding samples to non-editable version"""
        # Create mock version that's not editable
        version = Mock(spec=SampleSelectionVersion)
        version.version_id = uuid.uuid4()
        version.can_be_edited = False
        version.version_status = VersionStatus.APPROVED
        
        # Mock get_version_by_id
        with patch.object(service, 'get_version_by_id', return_value=version):
            samples_data = [
                {
                    "lob_id": 1,
                    "sample_identifier": "TEST_001",
                    "sample_data": {"field": "value1"},
                    "sample_category": "clean"
                }
            ]
            
            with pytest.raises(ValidationError):
                await service.add_samples_to_version(
                    db=mock_db,
                    version_id=version.version_id,
                    samples_data=samples_data,
                    current_user_id=1
                )
    
    @pytest_asyncio.async_fixture
    async def test_submit_for_approval(self, service, mock_db, mock_user):
        """Test submitting version for approval"""
        # Create mock version
        version = Mock(spec=SampleSelectionVersion)
        version.version_id = uuid.uuid4()
        version.version_status = VersionStatus.DRAFT
        
        # Mock get_version_by_id and _get_sample_count
        with patch.object(service, 'get_version_by_id', return_value=version):
            with patch.object(service, '_get_sample_count', return_value=10):
                
                updated_version = await service.submit_for_approval(
                    db=mock_db,
                    version_id=version.version_id,
                    submitted_by_id=1,
                    submission_notes="Ready for review"
                )
                
                assert updated_version.version_status == VersionStatus.PENDING_APPROVAL
                assert updated_version.submitted_by_id == 1
                assert updated_version.submission_notes == "Ready for review"
                
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()
    
    @pytest_asyncio.async_fixture
    async def test_submit_empty_version(self, service, mock_db):
        """Test submitting empty version for approval"""
        # Create mock version
        version = Mock(spec=SampleSelectionVersion)
        version.version_id = uuid.uuid4()
        version.version_status = VersionStatus.DRAFT
        
        # Mock get_version_by_id and _get_sample_count
        with patch.object(service, 'get_version_by_id', return_value=version):
            with patch.object(service, '_get_sample_count', return_value=0):
                
                with pytest.raises(ValidationError):
                    await service.submit_for_approval(
                        db=mock_db,
                        version_id=version.version_id,
                        submitted_by_id=1
                    )
    
    @pytest_asyncio.async_fixture
    async def test_approve_version(self, service, mock_db, mock_user):
        """Test approving version"""
        # Create mock version
        version = Mock(spec=SampleSelectionVersion)
        version.version_id = uuid.uuid4()
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.phase_id = 1
        version.version_number = 1
        
        # Mock get_version_by_id and _supersede_previous_versions
        with patch.object(service, 'get_version_by_id', return_value=version):
            with patch.object(service, '_supersede_previous_versions', return_value=None):
                
                updated_version = await service.approve_version(
                    db=mock_db,
                    version_id=version.version_id,
                    approved_by_id=1,
                    approval_notes="Approved"
                )
                
                assert updated_version.version_status == VersionStatus.APPROVED
                assert updated_version.approved_by_id == 1
                assert updated_version.approval_notes == "Approved"
                
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()
    
    @pytest_asyncio.async_fixture
    async def test_carry_forward_samples(self, service, mock_db):
        """Test carrying forward samples"""
        # Create mock source version with samples
        source_version = Mock(spec=SampleSelectionVersion)
        source_version.version_id = uuid.uuid4()
        source_version.version_number = 1
        source_version.samples = [
            Mock(
                sample_id=uuid.uuid4(),
                is_approved=True,
                lob_id=1,
                sample_identifier="SOURCE_001",
                sample_data={"field": "value"},
                sample_category=SampleCategory.CLEAN,
                risk_score=0.2,
                confidence_score=0.8
            )
        ]
        
        # Create mock target version
        target_version = Mock(spec=SampleSelectionVersion)
        target_version.version_id = uuid.uuid4()
        target_version.phase_id = 1
        target_version.can_be_edited = True
        
        # Mock get_version_by_id calls
        def mock_get_version_by_id(db, version_id, include_samples=False):
            if version_id == source_version.version_id:
                return source_version
            elif version_id == target_version.version_id:
                return target_version
            return None
        
        with patch.object(service, 'get_version_by_id', side_effect=mock_get_version_by_id):
            with patch.object(service, '_get_sample_count', return_value=1):
                with patch.object(service, '_calculate_distribution_metrics', return_value={"clean": 1}):
                    
                    carried_samples = await service.carry_forward_samples(
                        db=mock_db,
                        source_version_id=source_version.version_id,
                        target_version_id=target_version.version_id,
                        sample_filters=None
                    )
                    
                    assert len(carried_samples) == 1
                    assert carried_samples[0].sample_source == SampleSource.CARRIED_FORWARD
                    assert carried_samples[0].sample_identifier == "SOURCE_001"
                    assert carried_samples[0].carried_from_version_id == source_version.version_id
                    
                    mock_db.add_all.assert_called_once()
                    mock_db.commit.assert_called_once()


class TestIntelligentSamplingDistributionService:
    """Test IntelligentSamplingDistributionService"""
    
    @pytest.fixture
    def service(self):
        """Create service instance"""
        return IntelligentSamplingDistributionService()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=AsyncSession)
    
    @pytest.fixture
    def mock_version(self):
        """Create mock version"""
        version = Mock(spec=SampleSelectionVersion)
        version.version_id = uuid.uuid4()
        version.phase_id = 1
        version.target_sample_size = 100
        return version
    
    @pytest_asyncio.async_fixture
    async def test_generate_intelligent_samples_default_distribution(self, service, mock_db, mock_version):
        """Test generating samples with default distribution"""
        data_source_config = {
            "type": "mock",
            "criteria": {}
        }
        
        result = await service.generate_intelligent_samples(
            db=mock_db,
            version=mock_version,
            data_source_config=data_source_config,
            profiling_rules=None,
            custom_distribution=None
        )
        
        # Check generation summary
        assert "generation_summary" in result
        assert "generation_results" in result
        
        summary = result["generation_summary"]
        assert summary["total_requested"] == 100
        assert summary["total_generated"] == 100
        
        # Check distribution
        distribution = summary["distribution_achieved"]
        assert "clean" in distribution
        assert "anomaly" in distribution
        assert "boundary" in distribution
        
        # Default distribution should be 30/50/20
        assert distribution["clean"]["target_percentage"] == 30.0
        assert distribution["anomaly"]["target_percentage"] == 50.0
        assert distribution["boundary"]["target_percentage"] == 20.0
    
    @pytest_asyncio.async_fixture
    async def test_generate_intelligent_samples_custom_distribution(self, service, mock_db, mock_version):
        """Test generating samples with custom distribution"""
        data_source_config = {
            "type": "mock",
            "criteria": {}
        }
        
        custom_distribution = {
            "clean": 0.4,
            "anomaly": 0.4,
            "boundary": 0.2
        }
        
        result = await service.generate_intelligent_samples(
            db=mock_db,
            version=mock_version,
            data_source_config=data_source_config,
            profiling_rules=None,
            custom_distribution=custom_distribution
        )
        
        # Check custom distribution was applied
        summary = result["generation_summary"]
        distribution = summary["distribution_achieved"]
        
        assert distribution["clean"]["target_percentage"] == 40.0
        assert distribution["anomaly"]["target_percentage"] == 40.0
        assert distribution["boundary"]["target_percentage"] == 20.0
    
    @pytest_asyncio.async_fixture
    async def test_generate_intelligent_samples_invalid_distribution(self, service, mock_db, mock_version):
        """Test generating samples with invalid distribution"""
        data_source_config = {
            "type": "mock",
            "criteria": {}
        }
        
        # Distribution doesn't sum to 1.0
        invalid_distribution = {
            "clean": 0.5,
            "anomaly": 0.5,
            "boundary": 0.5
        }
        
        with pytest.raises(ValidationError):
            await service.generate_intelligent_samples(
                db=mock_db,
                version=mock_version,
                data_source_config=data_source_config,
                profiling_rules=None,
                custom_distribution=invalid_distribution
            )
    
    def test_calculate_generation_quality(self, service):
        """Test generation quality calculation"""
        generation_results = {
            "clean": {
                "target_count": 30,
                "actual_count": 30,
                "samples": [
                    {"generation_metadata": {"method": "database_query"}},
                    {"generation_metadata": {"method": "file_analysis"}}
                ]
            },
            "anomaly": {
                "target_count": 50,
                "actual_count": 50,
                "samples": [
                    {"generation_metadata": {"method": "profiling_rules"}},
                    {"generation_metadata": {"method": "statistical_analysis"}}
                ]
            },
            "boundary": {
                "target_count": 20,
                "actual_count": 20,
                "samples": [
                    {"generation_metadata": {"method": "boundary_detection"}}
                ]
            }
        }
        
        quality_score = service._calculate_generation_quality(generation_results)
        
        # Quality should be high since we hit all targets and have diverse methods
        assert 0.7 <= quality_score <= 1.0
    
    @pytest_asyncio.async_fixture
    async def test_generate_clean_samples(self, service, mock_db, mock_version):
        """Test generating clean samples"""
        samples = await service._generate_mock_clean_samples(
            db=mock_db,
            version=mock_version,
            target_count=10
        )
        
        assert len(samples) == 10
        
        for sample in samples:
            assert sample["sample_category"] == SampleCategory.CLEAN
            assert sample["sample_source"] == SampleSource.LLM
            assert sample["risk_score"] <= 0.2  # Clean samples should have low risk
            assert sample["confidence_score"] >= 0.9  # Clean samples should have high confidence
            assert "sample_identifier" in sample
            assert "sample_data" in sample
    
    @pytest_asyncio.async_fixture
    async def test_generate_anomaly_samples(self, service, mock_db, mock_version):
        """Test generating anomaly samples"""
        profiling_rules = [
            {"rule_name": "test_rule_1", "rule_type": "validation"},
            {"rule_name": "test_rule_2", "rule_type": "quality"}
        ]
        
        samples = await service._generate_mock_anomaly_samples(
            db=mock_db,
            version=mock_version,
            target_count=10,
            profiling_rules=profiling_rules
        )
        
        assert len(samples) == 10
        
        for sample in samples:
            assert sample["sample_category"] == SampleCategory.ANOMALY
            assert sample["sample_source"] == SampleSource.LLM
            assert sample["risk_score"] >= 0.7  # Anomaly samples should have high risk
            assert sample["confidence_score"] >= 0.8  # Should have good confidence
            assert "sample_identifier" in sample
            assert "sample_data" in sample
    
    @pytest_asyncio.async_fixture
    async def test_generate_boundary_samples(self, service, mock_db, mock_version):
        """Test generating boundary samples"""
        samples = await service._generate_mock_boundary_samples(
            db=mock_db,
            version=mock_version,
            target_count=10
        )
        
        assert len(samples) == 10
        
        # Should have both high and low boundary samples
        high_boundary_count = sum(1 for s in samples if s["sample_data"]["boundary_type"] == "high")
        low_boundary_count = sum(1 for s in samples if s["sample_data"]["boundary_type"] == "low")
        
        assert high_boundary_count == 5
        assert low_boundary_count == 5
        
        for sample in samples:
            assert sample["sample_category"] == SampleCategory.BOUNDARY
            assert sample["sample_source"] == SampleSource.LLM
            assert 0.5 <= sample["risk_score"] <= 0.7  # Boundary samples should have medium risk
            assert sample["confidence_score"] >= 0.75
            assert "sample_identifier" in sample
            assert "sample_data" in sample


if __name__ == "__main__":
    pytest.main([__file__])