"""
Integration tests for Sample Selection V2 API endpoints
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime
from typing import Dict, Any, List
import uuid
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.sample_selection import (
    SampleSelectionVersion, SampleSelectionSample,
    VersionStatus, SampleCategory, SampleDecision, SampleSource
)
from app.models.workflow import WorkflowPhase
from app.models.user import User
from app.models.lob import LOB
from app.core.database import get_db
from app.core.security import get_current_user


class TestSampleSelectionV2API:
    """Integration tests for Sample Selection V2 API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
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
        """Create mock authenticated user"""
        user = Mock(spec=User)
        user.user_id = 1
        user.full_name = "Test User"
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_phase(self):
        """Create mock workflow phase"""
        phase = Mock(spec=WorkflowPhase)
        phase.phase_id = 1
        phase.phase_name = "Sample Selection"
        return phase
    
    @pytest.fixture
    def mock_lob(self):
        """Create mock LOB"""
        lob = Mock(spec=LOB)
        lob.lob_id = 1
        lob.name = "Test LOB"
        return lob
    
    @pytest.fixture
    def sample_version_data(self):
        """Sample version data for testing"""
        return {
            "phase_id": 1,
            "selection_criteria": {
                "data_source": "database",
                "filters": {"account_type": "checking"}
            },
            "target_sample_size": 100,
            "workflow_execution_id": "test-execution-id",
            "workflow_run_id": "test-run-id",
            "activity_name": "sample_selection_activity",
            "intelligent_sampling_config": {
                "distribution": "30/50/20",
                "enable_anomaly_detection": True
            },
            "data_source_config": {
                "type": "database",
                "connection": "primary_db"
            }
        }
    
    @pytest.fixture
    def sample_samples_data(self):
        """Sample samples data for testing"""
        return [
            {
                "lob_id": 1,
                "sample_identifier": "TEST_001",
                "sample_data": {
                    "customer_id": "CUST_001",
                    "account_number": "ACC_001",
                    "amount": 1000.0,
                    "transaction_date": "2024-01-01"
                },
                "sample_category": "clean",
                "sample_source": "manual",
                "risk_score": 0.2,
                "confidence_score": 0.9
            },
            {
                "lob_id": 1,
                "sample_identifier": "TEST_002",
                "sample_data": {
                    "customer_id": "CUST_002",
                    "account_number": "ACC_002",
                    "amount": 999999.0,
                    "transaction_date": "2024-01-02"
                },
                "sample_category": "anomaly",
                "sample_source": "llm",
                "risk_score": 0.9,
                "confidence_score": 0.8
            }
        ]
    
    def test_create_sample_selection_version(self, client, mock_db, mock_user, mock_phase, sample_version_data):
        """Test creating a new sample selection version"""
        # Override dependencies
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        # Mock database operations
        mock_db.get.return_value = mock_phase
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Mock version creation
        created_version = SampleSelectionVersion(
            version_id=uuid.uuid4(),
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            workflow_execution_id="test-execution-id",
            workflow_run_id="test-run-id",
            activity_name="sample_selection_activity",
            selection_criteria=sample_version_data["selection_criteria"],
            target_sample_size=100,
            actual_sample_size=0,
            created_by_id=1,
            intelligent_sampling_config=sample_version_data["intelligent_sampling_config"],
            data_source_config=sample_version_data["data_source_config"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock service method
        with patch('app.services.sample_selection_service.SampleSelectionService.create_version') as mock_create:
            mock_create.return_value = created_version
            
            response = client.post(
                "/api/v1/sample-selection-v2/versions",
                json=sample_version_data
            )
            
            assert response.status_code == 201
            data = response.json()
            
            assert data["phase_id"] == 1
            assert data["version_number"] == 1
            assert data["version_status"] == "draft"
            assert data["target_sample_size"] == 100
            assert data["actual_sample_size"] == 0
            assert data["workflow_execution_id"] == "test-execution-id"
            assert data["selection_criteria"] == sample_version_data["selection_criteria"]
            assert data["is_current_version"] is False
            assert data["can_be_edited"] is True
        
        # Clean up
        app.dependency_overrides.clear()
    
    def test_create_version_validation_error(self, client, mock_db, mock_user):
        """Test validation error when creating version"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        # Invalid data - missing required fields
        invalid_data = {
            "phase_id": 1,
            "target_sample_size": 100
            # Missing workflow_execution_id, workflow_run_id, activity_name, selection_criteria
        }
        
        response = client.post(
            "/api/v1/sample-selection-v2/versions",
            json=invalid_data
        )
        
        assert response.status_code == 422  # Validation error
        
        app.dependency_overrides.clear()
    
    def test_get_sample_selection_version(self, client, mock_db, mock_user):
        """Test getting a sample selection version"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        version_id = uuid.uuid4()
        
        # Create mock version
        mock_version = Mock(spec=SampleSelectionVersion)
        mock_version.version_id = version_id
        mock_version.phase_id = 1
        mock_version.version_number = 1
        mock_version.version_status = VersionStatus.DRAFT
        mock_version.target_sample_size = 100
        mock_version.actual_sample_size = 50
        mock_version.workflow_execution_id = "test-execution-id"
        mock_version.selection_criteria = {"test": "criteria"}
        mock_version.is_current_version = False
        mock_version.can_be_edited = True
        mock_version.created_at = datetime.utcnow()
        mock_version.updated_at = datetime.utcnow()
        mock_version.created_by = mock_user
        mock_version.submitted_by = None
        mock_version.approved_by = None
        
        # Mock service method
        with patch('app.services.sample_selection_service.SampleSelectionService.get_version_by_id') as mock_get:
            mock_get.return_value = mock_version
            
            response = client.get(f"/api/v1/sample-selection-v2/versions/{version_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["version_id"] == str(version_id)
            assert data["phase_id"] == 1
            assert data["version_number"] == 1
            assert data["version_status"] == "draft"
            assert data["target_sample_size"] == 100
            assert data["actual_sample_size"] == 50
            assert data["created_by_name"] == "Test User"
        
        app.dependency_overrides.clear()
    
    def test_get_version_not_found(self, client, mock_db, mock_user):
        """Test getting non-existent version"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        version_id = uuid.uuid4()
        
        # Mock service method to return None
        with patch('app.services.sample_selection_service.SampleSelectionService.get_version_by_id') as mock_get:
            mock_get.return_value = None
            
            response = client.get(f"/api/v1/sample-selection-v2/versions/{version_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
        
        app.dependency_overrides.clear()
    
    def test_add_samples_to_version(self, client, mock_db, mock_user, sample_samples_data):
        """Test adding samples to a version"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        version_id = uuid.uuid4()
        
        # Create mock samples
        mock_samples = []
        for i, sample_data in enumerate(sample_samples_data):
            mock_sample = Mock(spec=SampleSelectionSample)
            mock_sample.sample_id = uuid.uuid4()
            mock_sample.version_id = version_id
            mock_sample.phase_id = 1
            mock_sample.lob_id = sample_data["lob_id"]
            mock_sample.sample_identifier = sample_data["sample_identifier"]
            mock_sample.sample_data = sample_data["sample_data"]
            mock_sample.sample_category = SampleCategory(sample_data["sample_category"])
            mock_sample.sample_source = SampleSource(sample_data["sample_source"])
            mock_sample.risk_score = sample_data["risk_score"]
            mock_sample.confidence_score = sample_data["confidence_score"]
            mock_sample.tester_decision = SampleDecision.PENDING
            mock_sample.report_owner_decision = SampleDecision.PENDING
            mock_sample.is_approved = False
            mock_sample.is_rejected = False
            mock_sample.needs_review = True
            mock_sample.is_carried_forward = False
            mock_sample.created_at = datetime.utcnow()
            mock_sample.updated_at = datetime.utcnow()
            mock_sample.lob = Mock(name="Test LOB")
            mock_samples.append(mock_sample)
        
        # Mock service method
        with patch('app.services.sample_selection_service.SampleSelectionService.add_samples_to_version') as mock_add:
            mock_add.return_value = mock_samples
            
            response = client.post(
                f"/api/v1/sample-selection-v2/versions/{version_id}/samples",
                json={"samples": sample_samples_data}
            )
            
            assert response.status_code == 201
            data = response.json()
            
            assert len(data) == 2
            assert data[0]["sample_identifier"] == "TEST_001"
            assert data[0]["sample_category"] == "clean"
            assert data[0]["risk_score"] == 0.2
            assert data[1]["sample_identifier"] == "TEST_002"
            assert data[1]["sample_category"] == "anomaly"
            assert data[1]["risk_score"] == 0.9
        
        app.dependency_overrides.clear()
    
    def test_generate_intelligent_samples(self, client, mock_db, mock_user):
        """Test generating intelligent samples"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        version_id = uuid.uuid4()
        
        # Create mock version
        mock_version = Mock(spec=SampleSelectionVersion)
        mock_version.version_id = version_id
        mock_version.target_sample_size = 100
        
        # Create mock generated samples
        mock_samples = []
        for i in range(10):
            mock_sample = Mock(spec=SampleSelectionSample)
            mock_sample.sample_id = uuid.uuid4()
            mock_sample.sample_identifier = f"GEN_{i:03d}"
            mock_sample.sample_category = SampleCategory.CLEAN
            mock_sample.sample_source = SampleSource.LLM
            mock_sample.risk_score = 0.1 + (i * 0.01)
            mock_sample.confidence_score = 0.9
            mock_sample.created_at = datetime.utcnow()
            mock_sample.updated_at = datetime.utcnow()
            mock_samples.append(mock_sample)
        
        # Mock service methods
        with patch('app.services.sample_selection_service.SampleSelectionService.get_version_by_id') as mock_get_version:
            mock_get_version.return_value = mock_version
            
            with patch('app.services.sample_selection_intelligent_service.IntelligentSamplingDistributionService.generate_intelligent_samples') as mock_generate:
                mock_generate.return_value = {
                    "generation_summary": {
                        "total_requested": 100,
                        "total_generated": 100,
                        "distribution_achieved": {
                            "clean": {"count": 30, "percentage": 30.0, "target_percentage": 30.0},
                            "anomaly": {"count": 50, "percentage": 50.0, "target_percentage": 50.0},
                            "boundary": {"count": 20, "percentage": 20.0, "target_percentage": 20.0}
                        },
                        "generation_quality": 0.95
                    },
                    "generation_results": {
                        "clean": {"samples": [{"sample_identifier": "GEN_001", "sample_category": "clean"}]},
                        "anomaly": {"samples": [{"sample_identifier": "GEN_002", "sample_category": "anomaly"}]},
                        "boundary": {"samples": [{"sample_identifier": "GEN_003", "sample_category": "boundary"}]}
                    }
                }
                
                with patch('app.services.sample_selection_service.SampleSelectionService.add_samples_to_version') as mock_add:
                    mock_add.return_value = mock_samples
                    
                    request_data = {
                        "custom_distribution": {
                            "clean": 0.3,
                            "anomaly": 0.5,
                            "boundary": 0.2
                        },
                        "data_source_config": {
                            "type": "database",
                            "criteria": {"table": "transactions"}
                        }
                    }
                    
                    response = client.post(
                        f"/api/v1/sample-selection-v2/versions/{version_id}/generate-intelligent",
                        json=request_data
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["total_generated"] == 10  # Mock samples length
                    assert data["generation_quality"] == 0.95
                    assert "distribution_achieved" in data
                    assert len(data["samples_created"]) == 10
        
        app.dependency_overrides.clear()
    
    def test_submit_version_for_approval(self, client, mock_db, mock_user):
        """Test submitting version for approval"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        version_id = uuid.uuid4()
        
        # Create mock version
        mock_version = Mock(spec=SampleSelectionVersion)
        mock_version.version_id = version_id
        mock_version.version_status = VersionStatus.PENDING_APPROVAL
        mock_version.submitted_by_id = 1
        mock_version.submission_notes = "Ready for review"
        mock_version.submitted_at = datetime.utcnow()
        mock_version.is_current_version = True
        mock_version.can_be_edited = False
        mock_version.created_by = mock_user
        mock_version.submitted_by = mock_user
        mock_version.approved_by = None
        
        # Mock service method
        with patch('app.services.sample_selection_service.SampleSelectionService.submit_for_approval') as mock_submit:
            mock_submit.return_value = mock_version
            
            response = client.post(
                f"/api/v1/sample-selection-v2/versions/{version_id}/submit",
                json={"submission_notes": "Ready for review"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["version_status"] == "pending_approval"
            assert data["submitted_by_name"] == "Test User"
            assert data["is_current_version"] is True
            assert data["can_be_edited"] is False
        
        app.dependency_overrides.clear()
    
    def test_approve_version(self, client, mock_db, mock_user):
        """Test approving a version"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        version_id = uuid.uuid4()
        
        # Create mock version
        mock_version = Mock(spec=SampleSelectionVersion)
        mock_version.version_id = version_id
        mock_version.version_status = VersionStatus.APPROVED
        mock_version.approved_by_id = 1
        mock_version.approval_notes = "Approved"
        mock_version.approved_at = datetime.utcnow()
        mock_version.is_current_version = True
        mock_version.can_be_edited = False
        mock_version.created_by = mock_user
        mock_version.submitted_by = mock_user
        mock_version.approved_by = mock_user
        
        # Mock service method
        with patch('app.services.sample_selection_service.SampleSelectionService.approve_version') as mock_approve:
            mock_approve.return_value = mock_version
            
            response = client.post(
                f"/api/v1/sample-selection-v2/versions/{version_id}/approve",
                json={"approval_notes": "Approved"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["version_status"] == "approved"
            assert data["approved_by_name"] == "Test User"
            assert data["is_current_version"] is True
            assert data["can_be_edited"] is False
        
        app.dependency_overrides.clear()
    
    def test_update_sample_decision(self, client, mock_db, mock_user):
        """Test updating sample decision"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        sample_id = uuid.uuid4()
        
        # Create mock sample
        mock_sample = Mock(spec=SampleSelectionSample)
        mock_sample.sample_id = sample_id
        mock_sample.sample_identifier = "TEST_001"
        mock_sample.tester_decision = SampleDecision.INCLUDE
        mock_sample.tester_decision_notes = "Approved by tester"
        mock_sample.tester_decision_at = datetime.utcnow()
        mock_sample.tester_decision_by_id = 1
        mock_sample.report_owner_decision = SampleDecision.PENDING
        mock_sample.is_approved = False
        mock_sample.is_rejected = False
        mock_sample.needs_review = True
        mock_sample.is_carried_forward = False
        mock_sample.created_at = datetime.utcnow()
        mock_sample.updated_at = datetime.utcnow()
        mock_sample.lob = Mock(name="Test LOB")
        
        # Mock service method
        with patch('app.services.sample_selection_service.SampleSelectionService.update_sample_decision') as mock_update:
            mock_update.return_value = mock_sample
            
            response = client.put(
                f"/api/v1/sample-selection-v2/samples/{sample_id}/decision",
                json={
                    "decision_type": "tester",
                    "decision": "include",
                    "decision_notes": "Approved by tester"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["sample_id"] == str(sample_id)
            assert data["tester_decision"] == "include"
            assert data["tester_decision_notes"] == "Approved by tester"
            assert data["needs_review"] is True
        
        app.dependency_overrides.clear()
    
    def test_get_version_statistics(self, client, mock_db, mock_user):
        """Test getting version statistics"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        version_id = uuid.uuid4()
        
        # Mock statistics data
        mock_statistics = {
            "version_info": {
                "version_id": str(version_id),
                "version_number": 1,
                "version_status": "approved",
                "target_sample_size": 100,
                "actual_sample_size": 100
            },
            "sample_counts": {
                "total": 100,
                "approved": 85,
                "rejected": 10,
                "pending": 5,
                "approval_rate": 0.85
            },
            "category_distribution": {
                "clean": 30,
                "anomaly": 50,
                "boundary": 20
            },
            "source_distribution": {
                "llm": 80,
                "manual": 15,
                "carried_forward": 5
            },
            "lob_distribution": {
                "Test LOB": 100
            },
            "decision_statistics": {
                "tester_decisions": {
                    "include": 90,
                    "exclude": 5,
                    "pending": 5
                },
                "report_owner_decisions": {
                    "include": 85,
                    "exclude": 10,
                    "pending": 5
                }
            },
            "risk_statistics": {
                "min": 0.1,
                "max": 0.9,
                "avg": 0.5,
                "high_risk_count": 20
            }
        }
        
        # Mock service method
        with patch('app.services.sample_selection_service.SampleSelectionService.get_version_statistics') as mock_stats:
            mock_stats.return_value = mock_statistics
            
            response = client.get(f"/api/v1/sample-selection-v2/versions/{version_id}/statistics")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["version_info"]["version_id"] == str(version_id)
            assert data["sample_counts"]["total"] == 100
            assert data["sample_counts"]["approval_rate"] == 0.85
            assert data["category_distribution"]["clean"] == 30
            assert data["category_distribution"]["anomaly"] == 50
            assert data["category_distribution"]["boundary"] == 20
            assert data["risk_statistics"]["high_risk_count"] == 20
        
        app.dependency_overrides.clear()
    
    def test_get_samples_for_version(self, client, mock_db, mock_user):
        """Test getting samples for a version"""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        version_id = uuid.uuid4()
        
        # Create mock version with samples
        mock_version = Mock(spec=SampleSelectionVersion)
        mock_version.version_id = version_id
        mock_version.samples = []
        
        # Create mock samples
        for i in range(10):
            mock_sample = Mock(spec=SampleSelectionSample)
            mock_sample.sample_id = uuid.uuid4()
            mock_sample.sample_identifier = f"TEST_{i:03d}"
            mock_sample.sample_category = SampleCategory.CLEAN if i < 5 else SampleCategory.ANOMALY
            mock_sample.sample_source = SampleSource.LLM
            mock_sample.risk_score = 0.1 + (i * 0.1)
            mock_sample.confidence_score = 0.9
            mock_sample.lob_id = 1
            mock_sample.is_approved = i < 8
            mock_sample.is_rejected = i >= 8
            mock_sample.needs_review = False
            mock_sample.is_carried_forward = False
            mock_sample.created_at = datetime.utcnow()
            mock_sample.updated_at = datetime.utcnow()
            mock_sample.lob = Mock(name="Test LOB")
            mock_version.samples.append(mock_sample)
        
        # Mock service method
        with patch('app.services.sample_selection_service.SampleSelectionService.get_version_by_id') as mock_get:
            mock_get.return_value = mock_version
            
            # Test without filters
            response = client.get(f"/api/v1/sample-selection-v2/versions/{version_id}/samples")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 10
            
            # Test with category filter
            response = client.get(f"/api/v1/sample-selection-v2/versions/{version_id}/samples?category=clean")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 5
            assert all(sample["sample_category"] == "clean" for sample in data)
            
            # Test with decision status filter
            response = client.get(f"/api/v1/sample-selection-v2/versions/{version_id}/samples?decision_status=approved")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 8
            assert all(sample["is_approved"] is True for sample in data)
            
            # Test with risk score filter
            response = client.get(f"/api/v1/sample-selection-v2/versions/{version_id}/samples?min_risk_score=0.5")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 5
            assert all(sample["risk_score"] >= 0.5 for sample in data)
            
            # Test with pagination
            response = client.get(f"/api/v1/sample-selection-v2/versions/{version_id}/samples?limit=5&offset=5")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 5
        
        app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__])