"""
Integration tests for Scoping V2 API endpoints

This module contains integration tests for the new consolidated scoping API,
testing endpoint functionality, request/response handling, and error cases.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
import json

from app.main import app
from app.models.scoping import (
    ScopingVersion, ScopingAttribute,
    VersionStatus, TesterDecision, ReportOwnerDecision, AttributeStatus
)
from app.models.user import User
from app.services.scoping_service import ScopingService
from app.core.exceptions import NotFoundError, BusinessLogicError, ValidationError


class TestScopingV2API:
    """Integration tests for Scoping V2 API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = Mock(spec=User)
        user.user_id = 1
        user.email = "test@example.com"
        user.name = "Test User"
        return user
    
    @pytest.fixture
    def mock_version(self):
        """Mock scoping version"""
        version = Mock(spec=ScopingVersion)
        version.version_id = uuid4()
        version.phase_id = 1
        version.version_number = 1
        version.version_status = VersionStatus.DRAFT
        version.total_attributes = 5
        version.scoped_attributes = 3
        version.declined_attributes = 2
        version.override_count = 1
        version.cde_count = 2
        version.recommendation_accuracy = 0.8
        version.workflow_activity_id = None
        version.workflow_execution_id = None
        version.workflow_run_id = None
        version.activity_name = None
        version.parent_version_id = None
        version.submission_notes = None
        version.submitted_by_id = None
        version.submitted_at = None
        version.approval_notes = None
        version.approved_by_id = None
        version.approved_at = None
        version.rejection_reason = None
        version.requested_changes = None
        version.resource_impact_assessment = None
        version.risk_coverage_assessment = None
        version.created_at = datetime.utcnow()
        version.created_by_id = 1
        version.updated_at = datetime.utcnow()
        version.updated_by_id = 1
        version.is_draft = True
        version.is_pending_approval = False
        version.is_approved = False
        version.is_rejected = False
        version.is_superseded = False
        version.can_be_edited = True
        version.can_be_submitted = True
        version.can_be_approved = False
        version.is_current = False
        version.scoping_percentage = 60.0
        version.override_percentage = 20.0
        return version
    
    @pytest.fixture
    def mock_attribute(self):
        """Mock scoping attribute"""
        attribute = Mock(spec=ScopingAttribute)
        attribute.attribute_id = uuid4()
        attribute.version_id = uuid4()
        attribute.phase_id = 1
        attribute.planning_attribute_id = 1
        attribute.llm_recommendation = {"recommended_action": "test", "confidence_score": 0.9}
        attribute.llm_provider = "openai"
        attribute.llm_confidence_score = 0.9
        attribute.llm_rationale = "High-risk attribute"
        attribute.llm_processing_time_ms = 500
        attribute.tester_decision = TesterDecision.ACCEPT
        attribute.final_scoping = True
        attribute.tester_rationale = "Agree with LLM"
        attribute.tester_decided_by_id = 1
        attribute.tester_decided_at = datetime.utcnow()
        attribute.report_owner_decision = None
        attribute.report_owner_notes = None
        attribute.report_owner_decided_by_id = None
        attribute.report_owner_decided_at = None
        attribute.is_override = False
        attribute.override_reason = None
        attribute.is_cde = True
        attribute.has_historical_issues = False
        attribute.is_primary_key = False
        attribute.data_quality_score = 0.8
        attribute.data_quality_issues = None
        attribute.expected_source_documents = ["Document1", "Document2"]
        attribute.search_keywords = ["keyword1", "keyword2"]
        attribute.risk_factors = ["risk1", "risk2"]
        attribute.status = AttributeStatus.SUBMITTED
        attribute.created_at = datetime.utcnow()
        attribute.created_by_id = 1
        attribute.updated_at = datetime.utcnow()
        attribute.updated_by_id = 1
        attribute.has_tester_decision = True
        attribute.has_report_owner_decision = False
        attribute.is_scoped_in = True
        attribute.is_scoped_out = False
        attribute.is_pending_decision = False
        attribute.llm_recommended_action = "test"
        attribute.llm_agreed_with_tester = True
        return attribute
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_create_version_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_version):
        """Test successful version creation"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.create_version = AsyncMock(return_value=mock_version)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post(
                "/scoping/v2/versions",
                json={
                    "phase_id": 1,
                    "workflow_activity_id": 1,
                    "notes": "Test version"
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["phase_id"] == 1
            assert data["version_number"] == 1
            assert data["version_status"] == "draft"
            assert data["total_attributes"] == 5
            
            # Verify service was called
            mock_service.create_version.assert_called_once()
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_create_version_invalid_phase(self, mock_get_db, mock_get_current_user, client, mock_user):
        """Test version creation with invalid phase"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock service to raise NotFoundError
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.create_version = AsyncMock(side_effect=NotFoundError("Phase not found"))
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post(
                "/scoping/v2/versions",
                json={
                    "phase_id": 999,
                    "notes": "Test version"
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Phase not found" in response.json()["detail"]
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_get_version_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_version):
        """Test successful version retrieval"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_version = AsyncMock(return_value=mock_version)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.get(f"/scoping/v2/versions/{mock_version.version_id}")
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["version_id"] == str(mock_version.version_id)
            assert data["phase_id"] == 1
            assert data["version_status"] == "draft"
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_get_version_not_found(self, mock_get_db, mock_get_current_user, client, mock_user):
        """Test version retrieval with non-existent version"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock service to return None
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_version = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service
            
            version_id = uuid4()
            response = client.get(f"/scoping/v2/versions/{version_id}")
            
            # Verify response
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert f"Version {version_id} not found" in response.json()["detail"]
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_add_attributes_to_version_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_attribute):
        """Test successful attribute addition"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.add_attributes_to_version = AsyncMock(return_value=[mock_attribute])
            mock_service_class.return_value = mock_service
            
            version_id = uuid4()
            
            # Make request
            response = client.post(
                f"/scoping/v2/versions/{version_id}/attributes",
                json={
                    "attributes": [
                        {
                            "planning_attribute_id": 1,
                            "llm_recommendation": {
                                "recommended_action": "test",
                                "confidence_score": 0.9,
                                "rationale": "High-risk attribute",
                                "provider": "openai",
                                "is_cde": True,
                                "data_quality_score": 0.8,
                                "expected_source_documents": ["Document1"],
                                "search_keywords": ["keyword1"],
                                "risk_factors": ["risk1"]
                            }
                        }
                    ]
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert len(data) == 1
            assert data[0]["planning_attribute_id"] == 1
            assert data[0]["status"] == "submitted"
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_make_tester_decision_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_attribute):
        """Test successful tester decision"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.make_tester_decision = AsyncMock(return_value=mock_attribute)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post(
                f"/scoping/v2/attributes/{mock_attribute.attribute_id}/tester-decision",
                json={
                    "decision": "accept",
                    "final_scoping": True,
                    "rationale": "Agree with LLM recommendation"
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["tester_decision"] == "accept"
            assert data["final_scoping"] is True
            assert data["tester_rationale"] == "Agree with LLM"
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_make_tester_decision_override_without_reason(self, mock_get_db, mock_get_current_user, client, mock_user):
        """Test tester decision with override but no reason"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock service to raise ValidationError
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.make_tester_decision = AsyncMock(
                side_effect=ValidationError("Override reason is required")
            )
            mock_service_class.return_value = mock_service
            
            attribute_id = uuid4()
            
            # Make request
            response = client.post(
                f"/scoping/v2/attributes/{attribute_id}/tester-decision",
                json={
                    "decision": "override",
                    "final_scoping": True
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Override reason is required" in response.json()["detail"]
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_make_report_owner_decision_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_attribute):
        """Test successful report owner decision"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Update mock attribute to have report owner decision
        mock_attribute.report_owner_decision = ReportOwnerDecision.APPROVED
        mock_attribute.report_owner_notes = "Approved for testing"
        mock_attribute.has_report_owner_decision = True
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.make_report_owner_decision = AsyncMock(return_value=mock_attribute)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post(
                f"/scoping/v2/attributes/{mock_attribute.attribute_id}/report-owner-decision",
                json={
                    "decision": "approved",
                    "notes": "Approved for testing"
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["report_owner_decision"] == "approved"
            assert data["report_owner_notes"] == "Approved for testing"
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_submit_version_for_approval_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_version):
        """Test successful version submission"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Update mock version to pending approval
        mock_version.version_status = VersionStatus.PENDING_APPROVAL
        mock_version.is_pending_approval = True
        mock_version.can_be_edited = False
        mock_version.can_be_submitted = False
        mock_version.can_be_approved = True
        mock_version.submission_notes = "Ready for review"
        mock_version.submitted_by_id = 1
        mock_version.submitted_at = datetime.utcnow()
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.submit_version_for_approval = AsyncMock(return_value=mock_version)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post(
                f"/scoping/v2/versions/{mock_version.version_id}/submit",
                json={
                    "submission_notes": "Ready for review",
                    "resource_impact_assessment": "Low impact",
                    "risk_coverage_assessment": "Adequate coverage"
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["version_status"] == "pending_approval"
            assert data["submission_notes"] == "Ready for review"
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_approve_version_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_version):
        """Test successful version approval"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Update mock version to approved
        mock_version.version_status = VersionStatus.APPROVED
        mock_version.is_approved = True
        mock_version.is_current = True
        mock_version.can_be_edited = False
        mock_version.can_be_submitted = False
        mock_version.can_be_approved = False
        mock_version.approval_notes = "Approved for implementation"
        mock_version.approved_by_id = 1
        mock_version.approved_at = datetime.utcnow()
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.approve_version = AsyncMock(return_value=mock_version)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post(
                f"/scoping/v2/versions/{mock_version.version_id}/approve",
                json={
                    "approval_notes": "Approved for implementation"
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["version_status"] == "approved"
            assert data["approval_notes"] == "Approved for implementation"
            assert data["is_current"] is True
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_reject_version_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_version):
        """Test successful version rejection"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Update mock version to rejected
        mock_version.version_status = VersionStatus.REJECTED
        mock_version.is_rejected = True
        mock_version.can_be_edited = True
        mock_version.can_be_submitted = False
        mock_version.can_be_approved = False
        mock_version.rejection_reason = "Needs more analysis"
        mock_version.requested_changes = {"analysis": "Add more detailed analysis"}
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.reject_version = AsyncMock(return_value=mock_version)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post(
                f"/scoping/v2/versions/{mock_version.version_id}/reject",
                json={
                    "rejection_reason": "Needs more analysis",
                    "requested_changes": {"analysis": "Add more detailed analysis"}
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["version_status"] == "rejected"
            assert data["rejection_reason"] == "Needs more analysis"
            assert data["can_be_edited"] is True
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_get_version_statistics_success(self, mock_get_db, mock_get_current_user, client, mock_user):
        """Test successful version statistics retrieval"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        version_id = uuid4()
        
        # Mock statistics
        mock_statistics = {
            "version_id": str(version_id),
            "version_number": 1,
            "status": "draft",
            "total_attributes": 10,
            "scoped_attributes": 6,
            "declined_attributes": 4,
            "override_count": 2,
            "cde_count": 3,
            "scoping_percentage": 60.0,
            "override_percentage": 20.0,
            "decision_progress": {
                "pending_decisions": 2,
                "completed_decisions": 8,
                "progress_percentage": 80.0
            },
            "report_owner_progress": {
                "pending_decisions": 3,
                "approved_decisions": 5,
                "progress_percentage": 62.5
            },
            "llm_accuracy": 0.75,
            "created_at": datetime.utcnow().isoformat(),
            "submitted_at": None,
            "approved_at": None,
            "can_be_edited": True,
            "can_be_submitted": True,
            "can_be_approved": False,
            "is_current": False
        }
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_version_statistics = AsyncMock(return_value=mock_statistics)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.get(f"/scoping/v2/versions/{version_id}/statistics")
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["version_id"] == str(version_id)
            assert data["total_attributes"] == 10
            assert data["scoped_attributes"] == 6
            assert data["scoping_percentage"] == 60.0
            assert data["llm_accuracy"] == 0.75
            assert data["decision_progress"]["progress_percentage"] == 80.0
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_bulk_tester_decisions_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_version):
        """Test successful bulk tester decisions"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock version can be edited
        mock_version.can_be_edited = True
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_version = AsyncMock(return_value=mock_version)
            mock_service.make_tester_decision = AsyncMock(return_value=mock_attribute)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post(
                f"/scoping/v2/versions/{mock_version.version_id}/bulk-tester-decisions",
                json={
                    "decisions": [
                        {
                            "attribute_id": str(uuid4()),
                            "decision": "accept",
                            "final_scoping": True,
                            "rationale": "Agree with LLM"
                        },
                        {
                            "attribute_id": str(uuid4()),
                            "decision": "decline",
                            "final_scoping": False,
                            "rationale": "Not required"
                        }
                    ]
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_requested"] == 2
            assert data["successful_updates"] == 2
            assert data["failed_updates"] == 0
            assert len(data["errors"]) == 0
            assert len(data["updated_attributes"]) == 2
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_copy_version_success(self, mock_get_db, mock_get_current_user, client, mock_user, mock_version):
        """Test successful version copying"""
        mock_get_current_user.return_value = mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock new version
        new_version = Mock(spec=ScopingVersion)
        new_version.version_id = uuid4()
        new_version.phase_id = 1
        new_version.version_number = 2
        new_version.version_status = VersionStatus.DRAFT
        new_version.parent_version_id = mock_version.version_id
        new_version.total_attributes = 0
        new_version.scoped_attributes = 0
        new_version.declined_attributes = 0
        new_version.override_count = 0
        new_version.cde_count = 0
        new_version.recommendation_accuracy = None
        new_version.created_at = datetime.utcnow()
        new_version.created_by_id = 1
        new_version.updated_at = datetime.utcnow()
        new_version.updated_by_id = 1
        new_version.can_be_edited = True
        new_version.can_be_submitted = False
        new_version.can_be_approved = False
        new_version.is_current = False
        new_version.scoping_percentage = 0.0
        new_version.override_percentage = 0.0
        
        # Mock service
        with patch('app.api.v1.endpoints.scoping_v2.ScopingService') as mock_service_class:
            mock_service = Mock()
            mock_service.copy_version = AsyncMock(return_value=new_version)
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post(
                f"/scoping/v2/versions/{mock_version.version_id}/copy",
                json={
                    "source_version_id": str(mock_version.version_id),
                    "copy_attributes": True,
                    "copy_decisions": False,
                    "notes": "Copy for revision"
                }
            )
            
            # Verify response
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["version_number"] == 2
            assert data["version_status"] == "draft"
            assert data["parent_version_id"] == str(mock_version.version_id)
    
    @patch('app.api.v1.endpoints.scoping_v2.get_current_user')
    @patch('app.api.v1.endpoints.scoping_v2.get_db')
    def test_health_check(self, mock_get_db, mock_get_current_user, client):
        """Test health check endpoint"""
        # Health check shouldn't require authentication
        response = client.get("/scoping/v2/health")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "scoping-v2"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
    
    def test_create_version_validation_error(self, client):
        """Test version creation with validation errors"""
        # Test with invalid phase_id
        response = client.post(
            "/scoping/v2/versions",
            json={
                "phase_id": 0,  # Invalid: must be positive
                "notes": "Test version"
            }
        )
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "validation error" in response.json()["detail"][0]["type"]
    
    def test_tester_decision_validation_error(self, client):
        """Test tester decision with validation errors"""
        attribute_id = uuid4()
        
        # Test with invalid decision
        response = client.post(
            f"/scoping/v2/attributes/{attribute_id}/tester-decision",
            json={
                "decision": "invalid_decision",  # Invalid enum value
                "final_scoping": True
            }
        )
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "validation error" in response.json()["detail"][0]["type"]
    
    def test_version_rejection_validation_error(self, client):
        """Test version rejection with validation errors"""
        version_id = uuid4()
        
        # Test with short rejection reason
        response = client.post(
            f"/scoping/v2/versions/{version_id}/reject",
            json={
                "rejection_reason": "short"  # Too short
            }
        )
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "validation error" in response.json()["detail"][0]["type"]


if __name__ == "__main__":
    pytest.main([__file__])