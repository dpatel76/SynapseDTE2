"""
Comprehensive tests for the unified planning system
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import (
    PlanningVersion, PlanningDataSource, PlanningAttribute, PlanningPDEMapping,
    VersionStatus, DataSourceType, AttributeDataType, 
    InformationSecurityClassification, MappingType, Decision, Status
)
from app.models.user import User
from app.services.planning_service_unified import PlanningServiceUnified
from app.core.exceptions import (
    ResourceNotFoundError, ValidationError, ConflictError, BusinessLogicError
)


class TestPlanningServiceUnified:
    """Test suite for PlanningServiceUnified"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = Mock()
        return session
    
    @pytest.fixture
    def mock_user(self):
        """Mock user"""
        user = Mock(spec=User)
        user.user_id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.role = "Tester"
        return user
    
    @pytest.fixture
    def planning_service(self, mock_db_session):
        """Planning service instance"""
        return PlanningServiceUnified(mock_db_session)
    
    @pytest.fixture
    def sample_version_data(self):
        """Sample version data"""
        return {
            "phase_id": 1,
            "workflow_activity_id": 1,
            "version_number": 1,
            "version_status": VersionStatus.DRAFT
        }
    
    @pytest.fixture
    def sample_data_source_data(self):
        """Sample data source data"""
        return {
            "source_name": "Test Database",
            "source_type": "database",
            "description": "Test database source",
            "connection_config": {
                "host": "localhost",
                "port": 5432,
                "database": "testdb"
            },
            "auth_config": {
                "username": "testuser",
                "password": "testpass"
            }
        }
    
    @pytest.fixture
    def sample_attribute_data(self):
        """Sample attribute data"""
        return {
            "attribute_name": "test_attribute",
            "data_type": "string",
            "description": "Test attribute",
            "business_definition": "Test business definition",
            "is_mandatory": True,
            "is_cde": False,
            "is_primary_key": False,
            "information_security_classification": "internal"
        }
    
    @pytest.fixture
    def sample_pde_mapping_data(self):
        """Sample PDE mapping data"""
        return {
            "pde_name": "Test PDE",
            "pde_code": "TEST_001",
            "mapping_type": "direct",
            "source_table": "test_table",
            "source_column": "test_column",
            "source_field": "schema.test_table.test_column",
            "column_data_type": "VARCHAR(255)",
            "is_primary": False,
            "classification": {
                "criticality": "medium",
                "risk_level": "low",
                "information_security": "internal"
            }
        }


class TestPlanningVersionManagement:
    """Test planning version management"""
    
    @pytest.mark.asyncio
    async def test_create_version_success(self, planning_service, mock_user):
        """Test successful version creation"""
        # Mock database responses
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = None
        planning_service.db.execute.return_value.scalar.return_value = 0
        
        # Create version
        version = await planning_service.create_version(
            phase_id=1,
            current_user=mock_user,
            workflow_activity_id=1
        )
        
        # Verify version was created
        assert isinstance(version, PlanningVersion)
        assert version.phase_id == 1
        assert version.version_number == 1
        assert version.version_status == VersionStatus.DRAFT
        
        # Verify database operations
        planning_service.db.add.assert_called_once()
        planning_service.db.commit.assert_called_once()
        planning_service.db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_version_draft_exists(self, planning_service, mock_user):
        """Test version creation when draft already exists"""
        # Mock existing draft version
        existing_version = Mock(spec=PlanningVersion)
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = existing_version
        
        # Attempt to create version
        with pytest.raises(ConflictError, match="A draft version already exists"):
            await planning_service.create_version(
                phase_id=1,
                current_user=mock_user
            )
    
    @pytest.mark.asyncio
    async def test_get_version_by_id_success(self, planning_service):
        """Test successful version retrieval"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_id = version_id
        
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = mock_version
        
        # Get version
        result = await planning_service.get_version_by_id(version_id)
        
        # Verify result
        assert result == mock_version
        assert result.version_id == version_id
    
    @pytest.mark.asyncio
    async def test_get_version_by_id_not_found(self, planning_service):
        """Test version retrieval when not found"""
        # Mock not found
        version_id = uuid.uuid4()
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Attempt to get version
        with pytest.raises(ResourceNotFoundError, match=f"Version {version_id} not found"):
            await planning_service.get_version_by_id(version_id)


class TestPlanningDataSourceManagement:
    """Test planning data source management"""
    
    @pytest.mark.asyncio
    async def test_create_data_source_success(self, planning_service, mock_user, sample_data_source_data):
        """Test successful data source creation"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_id = version_id
        mock_version.version_status = VersionStatus.DRAFT
        mock_version.phase_id = 1
        
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = None
        planning_service.update_version_summary = AsyncMock()
        
        # Create data source
        data_source = await planning_service.create_data_source(
            version_id=version_id,
            data_source_data=sample_data_source_data,
            current_user=mock_user
        )
        
        # Verify data source was created
        assert isinstance(data_source, PlanningDataSource)
        assert data_source.version_id == version_id
        assert data_source.source_name == "Test Database"
        assert data_source.source_type == DataSourceType.DATABASE
        assert data_source.status == Status.PENDING
        
        # Verify database operations
        planning_service.db.add.assert_called_once()
        planning_service.db.commit.assert_called_once()
        planning_service.update_version_summary.assert_called_once_with(version_id)
    
    @pytest.mark.asyncio
    async def test_create_data_source_duplicate_name(self, planning_service, mock_user, sample_data_source_data):
        """Test data source creation with duplicate name"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_status = VersionStatus.DRAFT
        
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        
        # Mock existing data source
        existing_data_source = Mock(spec=PlanningDataSource)
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = existing_data_source
        
        # Attempt to create data source
        with pytest.raises(ConflictError, match="Data source 'Test Database' already exists"):
            await planning_service.create_data_source(
                version_id=version_id,
                data_source_data=sample_data_source_data,
                current_user=mock_user
            )
    
    @pytest.mark.asyncio
    async def test_update_data_source_tester_decision(self, planning_service, mock_user):
        """Test updating data source tester decision"""
        # Mock data source
        data_source_id = uuid.uuid4()
        version_id = uuid.uuid4()
        mock_data_source = Mock(spec=PlanningDataSource)
        mock_data_source.data_source_id = data_source_id
        mock_data_source.version_id = version_id
        
        # Mock version
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_status = VersionStatus.DRAFT
        
        planning_service.get_data_source_by_id = AsyncMock(return_value=mock_data_source)
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        planning_service.update_version_summary = AsyncMock()
        
        # Update decision
        result = await planning_service.update_data_source_tester_decision(
            data_source_id=data_source_id,
            decision=Decision.APPROVE,
            notes="Approved for testing",
            current_user=mock_user
        )
        
        # Verify decision was updated
        assert result == mock_data_source
        assert result.tester_decision == Decision.APPROVE
        assert result.tester_notes == "Approved for testing"
        assert result.tester_decided_by == mock_user.user_id
        assert result.status == Status.APPROVED
        
        # Verify database operations
        planning_service.db.commit.assert_called_once()
        planning_service.update_version_summary.assert_called_once_with(version_id)


class TestPlanningAttributeManagement:
    """Test planning attribute management"""
    
    @pytest.mark.asyncio
    async def test_create_attribute_success(self, planning_service, mock_user, sample_attribute_data):
        """Test successful attribute creation"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_id = version_id
        mock_version.version_status = VersionStatus.DRAFT
        mock_version.phase_id = 1
        
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = None
        planning_service.update_version_summary = AsyncMock()
        
        # Create attribute
        attribute = await planning_service.create_attribute(
            version_id=version_id,
            attribute_data=sample_attribute_data,
            current_user=mock_user
        )
        
        # Verify attribute was created
        assert isinstance(attribute, PlanningAttribute)
        assert attribute.version_id == version_id
        assert attribute.attribute_name == "test_attribute"
        assert attribute.data_type == AttributeDataType.STRING
        assert attribute.is_mandatory == True
        assert attribute.status == Status.PENDING
        
        # Verify database operations
        planning_service.db.add.assert_called_once()
        planning_service.db.commit.assert_called_once()
        planning_service.update_version_summary.assert_called_once_with(version_id)
    
    @pytest.mark.asyncio
    async def test_create_attribute_duplicate_name(self, planning_service, mock_user, sample_attribute_data):
        """Test attribute creation with duplicate name"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_status = VersionStatus.DRAFT
        
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        
        # Mock existing attribute
        existing_attribute = Mock(spec=PlanningAttribute)
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = existing_attribute
        
        # Attempt to create attribute
        with pytest.raises(ConflictError, match="Attribute 'test_attribute' already exists"):
            await planning_service.create_attribute(
                version_id=version_id,
                attribute_data=sample_attribute_data,
                current_user=mock_user
            )


class TestPlanningPDEMappingManagement:
    """Test planning PDE mapping management"""
    
    @pytest.mark.asyncio
    async def test_create_pde_mapping_success(self, planning_service, mock_user, sample_pde_mapping_data):
        """Test successful PDE mapping creation"""
        # Mock attribute
        attribute_id = uuid.uuid4()
        version_id = uuid.uuid4()
        mock_attribute = Mock(spec=PlanningAttribute)
        mock_attribute.attribute_id = attribute_id
        mock_attribute.version_id = version_id
        mock_attribute.phase_id = 1
        
        # Mock data source
        data_source_id = uuid.uuid4()
        mock_data_source = Mock(spec=PlanningDataSource)
        mock_data_source.data_source_id = data_source_id
        mock_data_source.version_id = version_id
        
        # Mock version
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_status = VersionStatus.DRAFT
        
        planning_service.get_attribute_by_id = AsyncMock(return_value=mock_attribute)
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        planning_service.get_data_source_by_id = AsyncMock(return_value=mock_data_source)
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = None
        planning_service.update_version_summary = AsyncMock()
        planning_service._should_auto_approve = Mock(return_value=False)
        
        # Create PDE mapping
        pde_mapping = await planning_service.create_pde_mapping(
            attribute_id=attribute_id,
            data_source_id=data_source_id,
            pde_mapping_data=sample_pde_mapping_data,
            current_user=mock_user
        )
        
        # Verify PDE mapping was created
        assert isinstance(pde_mapping, PlanningPDEMapping)
        assert pde_mapping.attribute_id == attribute_id
        assert pde_mapping.data_source_id == data_source_id
        assert pde_mapping.pde_name == "Test PDE"
        assert pde_mapping.pde_code == "TEST_001"
        assert pde_mapping.mapping_type == MappingType.DIRECT
        assert pde_mapping.status == Status.PENDING
        
        # Verify database operations
        planning_service.db.add.assert_called_once()
        planning_service.db.commit.assert_called_once()
        planning_service.update_version_summary.assert_called_once_with(version_id)
    
    @pytest.mark.asyncio
    async def test_create_pde_mapping_auto_approval(self, planning_service, mock_user, sample_pde_mapping_data):
        """Test PDE mapping creation with auto-approval"""
        # Mock attribute
        attribute_id = uuid.uuid4()
        version_id = uuid.uuid4()
        mock_attribute = Mock(spec=PlanningAttribute)
        mock_attribute.attribute_id = attribute_id
        mock_attribute.version_id = version_id
        mock_attribute.phase_id = 1
        
        # Mock data source
        data_source_id = uuid.uuid4()
        mock_data_source = Mock(spec=PlanningDataSource)
        mock_data_source.data_source_id = data_source_id
        mock_data_source.version_id = version_id
        
        # Mock version
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_status = VersionStatus.DRAFT
        
        planning_service.get_attribute_by_id = AsyncMock(return_value=mock_attribute)
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        planning_service.get_data_source_by_id = AsyncMock(return_value=mock_data_source)
        planning_service.db.execute.return_value.scalar_one_or_none.return_value = None
        planning_service.update_version_summary = AsyncMock()
        planning_service._should_auto_approve = Mock(return_value=True)
        
        # Create PDE mapping
        pde_mapping = await planning_service.create_pde_mapping(
            attribute_id=attribute_id,
            data_source_id=data_source_id,
            pde_mapping_data=sample_pde_mapping_data,
            current_user=mock_user
        )
        
        # Verify PDE mapping was auto-approved
        assert pde_mapping.tester_decision == Decision.APPROVE
        assert pde_mapping.auto_approved == True
        assert pde_mapping.status == Status.APPROVED
        assert pde_mapping.tester_notes == "Auto-approved based on approval rules"


class TestPlanningWorkflowManagement:
    """Test planning workflow management"""
    
    @pytest.mark.asyncio
    async def test_submit_for_approval_success(self, planning_service, mock_user):
        """Test successful submission for approval"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_id = version_id
        mock_version.version_status = VersionStatus.DRAFT
        
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        planning_service._validate_version_for_submission = AsyncMock(return_value=[])
        
        # Submit for approval
        result = await planning_service.submit_for_approval(
            version_id=version_id,
            current_user=mock_user
        )
        
        # Verify submission
        assert result == mock_version
        assert result.version_status == VersionStatus.PENDING_APPROVAL
        assert result.submitted_by_id == mock_user.user_id
        assert result.submitted_at is not None
        
        # Verify database operations
        planning_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_for_approval_validation_errors(self, planning_service, mock_user):
        """Test submission with validation errors"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_status = VersionStatus.DRAFT
        
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        planning_service._validate_version_for_submission = AsyncMock(return_value=[
            "All data sources must have tester decisions",
            "All attributes must have tester decisions"
        ])
        
        # Attempt to submit for approval
        with pytest.raises(BusinessLogicError, match="Version cannot be submitted"):
            await planning_service.submit_for_approval(
                version_id=version_id,
                current_user=mock_user
            )
    
    @pytest.mark.asyncio
    async def test_approve_version_success(self, planning_service, mock_user):
        """Test successful version approval"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_id = version_id
        mock_version.version_status = VersionStatus.PENDING_APPROVAL
        mock_version.phase_id = 1
        
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        
        # Approve version
        result = await planning_service.approve_version(
            version_id=version_id,
            current_user=mock_user
        )
        
        # Verify approval
        assert result == mock_version
        assert result.version_status == VersionStatus.APPROVED
        assert result.approved_by_id == mock_user.user_id
        assert result.approved_at is not None
        
        # Verify database operations
        planning_service.db.execute.assert_called()
        planning_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reject_version_success(self, planning_service, mock_user):
        """Test successful version rejection"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_id = version_id
        mock_version.version_status = VersionStatus.PENDING_APPROVAL
        
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        
        # Reject version
        result = await planning_service.reject_version(
            version_id=version_id,
            rejection_reason="Missing required data",
            current_user=mock_user
        )
        
        # Verify rejection
        assert result == mock_version
        assert result.version_status == VersionStatus.REJECTED
        assert result.rejection_reason == "Missing required data"
        
        # Verify database operations
        planning_service.db.commit.assert_called_once()


class TestPlanningAutoApproval:
    """Test planning auto-approval logic"""
    
    def test_should_auto_approve_high_confidence(self, planning_service):
        """Test auto-approval with high LLM confidence"""
        pde_mapping_data = {
            "llm_metadata": {
                "confidence_score": 0.9
            },
            "classification": {
                "information_security": "internal",
                "risk_level": "low",
                "criticality": "low"
            }
        }
        
        result = planning_service._should_auto_approve(pde_mapping_data)
        assert result == True
    
    def test_should_auto_approve_low_confidence(self, planning_service):
        """Test auto-approval with low LLM confidence"""
        pde_mapping_data = {
            "llm_metadata": {
                "confidence_score": 0.7
            },
            "classification": {
                "information_security": "internal",
                "risk_level": "medium",
                "criticality": "medium"
            }
        }
        
        result = planning_service._should_auto_approve(pde_mapping_data)
        assert result == False
    
    def test_should_auto_approve_public_classification(self, planning_service):
        """Test auto-approval with public classification"""
        pde_mapping_data = {
            "llm_metadata": {
                "confidence_score": 0.9
            },
            "classification": {
                "information_security": "public",
                "risk_level": "high",
                "criticality": "high"
            }
        }
        
        result = planning_service._should_auto_approve(pde_mapping_data)
        assert result == True
    
    def test_should_auto_approve_primary_key(self, planning_service):
        """Test auto-approval with primary key"""
        pde_mapping_data = {
            "llm_metadata": {
                "confidence_score": 0.9
            },
            "is_primary": True,
            "classification": {
                "information_security": "internal",
                "risk_level": "medium",
                "criticality": "medium"
            }
        }
        
        result = planning_service._should_auto_approve(pde_mapping_data)
        assert result == True
    
    def test_calculate_risk_score_high_risk(self, planning_service):
        """Test risk score calculation for high risk"""
        classification = {
            "risk_level": "high",
            "criticality": "high",
            "information_security": "restricted"
        }
        
        risk_score = planning_service._calculate_risk_score(classification)
        assert risk_score == 10  # 4 + 3 + 3 = 10, capped at 10
    
    def test_calculate_risk_score_low_risk(self, planning_service):
        """Test risk score calculation for low risk"""
        classification = {
            "risk_level": "low",
            "criticality": "low",
            "information_security": "public"
        }
        
        risk_score = planning_service._calculate_risk_score(classification)
        assert risk_score == 2  # 1 + 1 + 0 = 2


class TestPlanningBulkOperations:
    """Test planning bulk operations"""
    
    @pytest.mark.asyncio
    async def test_bulk_tester_decision_success(self, planning_service, mock_user):
        """Test successful bulk tester decision"""
        # Mock item IDs
        item_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        
        # Mock successful decision updates
        planning_service.update_data_source_tester_decision = AsyncMock()
        
        # Perform bulk decision
        results = await planning_service.bulk_tester_decision(
            item_ids=item_ids,
            item_type="data_source",
            decision=Decision.APPROVE,
            notes="Bulk approval",
            current_user=mock_user
        )
        
        # Verify results
        assert results["total_requested"] == 3
        assert results["successful"] == 3
        assert results["failed"] == 0
        assert len(results["errors"]) == 0
        
        # Verify all items were processed
        assert planning_service.update_data_source_tester_decision.call_count == 3
    
    @pytest.mark.asyncio
    async def test_bulk_tester_decision_partial_failure(self, planning_service, mock_user):
        """Test bulk tester decision with partial failures"""
        # Mock item IDs
        item_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        
        # Mock mixed success/failure
        def mock_decision_update(item_id, decision, notes, current_user):
            if item_id == item_ids[1]:  # Second item fails
                raise ValidationError("Item not found")
            return AsyncMock()
        
        planning_service.update_attribute_tester_decision = AsyncMock(side_effect=mock_decision_update)
        
        # Perform bulk decision
        results = await planning_service.bulk_tester_decision(
            item_ids=item_ids,
            item_type="attribute",
            decision=Decision.APPROVE,
            notes="Bulk approval",
            current_user=mock_user
        )
        
        # Verify results
        assert results["total_requested"] == 3
        assert results["successful"] == 2
        assert results["failed"] == 1
        assert len(results["errors"]) == 1
        assert "Item not found" in results["errors"][0]


class TestPlanningDashboard:
    """Test planning dashboard functionality"""
    
    @pytest.mark.asyncio
    async def test_get_version_dashboard_success(self, planning_service):
        """Test successful dashboard data retrieval"""
        # Mock version
        version_id = uuid.uuid4()
        mock_version = Mock(spec=PlanningVersion)
        mock_version.version_id = version_id
        
        # Mock data sources
        mock_data_sources = [
            Mock(spec=PlanningDataSource, tester_decision=Decision.APPROVE),
            Mock(spec=PlanningDataSource, tester_decision=None)
        ]
        
        # Mock attributes
        mock_attributes = [
            Mock(spec=PlanningAttribute, tester_decision=Decision.APPROVE),
            Mock(spec=PlanningAttribute, tester_decision=Decision.REJECT),
            Mock(spec=PlanningAttribute, tester_decision=None)
        ]
        
        # Mock PDE mappings
        mock_pde_mappings = [
            Mock(spec=PlanningPDEMapping, tester_decision=Decision.APPROVE),
            Mock(spec=PlanningPDEMapping, tester_decision=None)
        ]
        
        planning_service.get_version_by_id = AsyncMock(return_value=mock_version)
        planning_service.get_data_sources_by_version = AsyncMock(return_value=mock_data_sources)
        planning_service.get_attributes_by_version = AsyncMock(return_value=mock_attributes)
        planning_service.get_pde_mappings_by_version = AsyncMock(return_value=mock_pde_mappings)
        planning_service._validate_version_for_submission = AsyncMock(return_value=[])
        
        # Get dashboard data
        dashboard_data = await planning_service.get_version_dashboard(version_id)
        
        # Verify dashboard data
        assert dashboard_data["version"] == mock_version
        assert len(dashboard_data["data_sources"]) == 2
        assert len(dashboard_data["attributes"]) == 3
        assert len(dashboard_data["pde_mappings"]) == 2
        
        # Verify completion statistics
        # Total items: 2 + 3 + 2 = 7
        # Decided items: 1 + 2 + 1 = 4
        # Completion percentage: 4/7 * 100 = 57.14%
        assert dashboard_data["completion_percentage"] == pytest.approx(57.14, rel=1e-2)
        assert dashboard_data["pending_decisions"] == 3
        assert dashboard_data["can_submit"] == True
        assert dashboard_data["submission_requirements"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])