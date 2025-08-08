"""Tests for clean architecture use cases"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from app.application.dto.test_cycle_dto import CreateTestCycleDTO, AddReportToCycleDTO
from app.application.use_cases.planning import (
    CreateTestCycleUseCase,
    AddReportToCycleUseCase
)
from app.domain.entities.test_cycle import TestCycle
from app.domain.value_objects import CycleStatus


class TestCreateTestCycleUseCase:
    """Test create test cycle use case"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            "cycle_repository": Mock(),
            "user_repository": Mock(),
            "notification_service": Mock(),
            "audit_service": Mock()
        }
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case instance"""
        return CreateTestCycleUseCase(**mock_repositories)
    
    @pytest.mark.asyncio
    async def test_create_cycle_success(self, use_case, mock_repositories):
        """Test successful cycle creation"""
        # Arrange
        dto = CreateTestCycleDTO(
            cycle_name="Q1 2024 Testing",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            created_by=1,
            description="Quarterly testing cycle"
        )
        
        # Mock user exists
        mock_repositories["user_repository"].get = AsyncMock(
            return_value={"user_id": 1, "username": "testuser"}
        )
        
        # Mock no duplicate cycle
        mock_repositories["cycle_repository"].get_by_name = AsyncMock(
            return_value=None
        )
        
        # Mock save returns cycle with ID
        saved_cycle = TestCycle(
            cycle_name=dto.cycle_name,
            start_date=dto.start_date,
            end_date=dto.end_date,
            created_by=dto.created_by,
            description=dto.description
        )
        saved_cycle.id = 123
        mock_repositories["cycle_repository"].save = AsyncMock(
            return_value=saved_cycle
        )
        
        # Mock other services
        mock_repositories["audit_service"].log_action = AsyncMock()
        mock_repositories["notification_service"].send_bulk_notifications = AsyncMock()
        mock_repositories["user_repository"].find_by_role = AsyncMock(
            return_value=[{"user_id": 2}, {"user_id": 3}]
        )
        
        # Act
        result = await use_case.execute(dto)
        
        # Assert
        assert result.success is True
        assert result.data.cycle_id == 123
        assert result.data.cycle_name == dto.cycle_name
        assert result.data.status == CycleStatus.PLANNING.value
        assert len(result.events) == 1
        assert result.events[0].event_type == "TestCycleCreated"
        
        # Verify audit log was called
        mock_repositories["audit_service"].log_action.assert_called_once()
        
        # Verify notifications were sent
        mock_repositories["notification_service"].send_bulk_notifications.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_cycle_duplicate_name(self, use_case, mock_repositories):
        """Test cycle creation with duplicate name"""
        # Arrange
        dto = CreateTestCycleDTO(
            cycle_name="Existing Cycle",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            created_by=1
        )
        
        # Mock user exists
        mock_repositories["user_repository"].get = AsyncMock(
            return_value={"user_id": 1}
        )
        
        # Mock duplicate cycle exists
        mock_repositories["cycle_repository"].get_by_name = AsyncMock(
            return_value=TestCycle(
                cycle_name="Existing Cycle",
                start_date=datetime.now(),
                end_date=datetime.now(),
                created_by=1
            )
        )
        
        # Act
        result = await use_case.execute(dto)
        
        # Assert
        assert result.success is False
        assert "already exists" in result.error
    
    @pytest.mark.asyncio
    async def test_create_cycle_user_not_found(self, use_case, mock_repositories):
        """Test cycle creation with invalid user"""
        # Arrange
        dto = CreateTestCycleDTO(
            cycle_name="Test Cycle",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            created_by=999
        )
        
        # Mock user not found
        mock_repositories["user_repository"].get = AsyncMock(
            return_value=None
        )
        
        # Act
        result = await use_case.execute(dto)
        
        # Assert
        assert result.success is False
        assert "User not found" in result.error


class TestAddReportToCycleUseCase:
    """Test add report to cycle use case"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            "cycle_repository": Mock(),
            "report_repository": Mock(),
            "user_repository": Mock(),
            "workflow_repository": Mock(),
            "notification_service": Mock(),
            "audit_service": Mock()
        }
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case instance"""
        return AddReportToCycleUseCase(**mock_repositories)
    
    @pytest.mark.asyncio
    async def test_add_report_success(self, use_case, mock_repositories):
        """Test successful report addition"""
        # Arrange
        dto = AddReportToCycleDTO(
            cycle_id=1,
            report_id=10,
            tester_id=5,
            requested_by=2
        )
        
        # Create test cycle
        cycle = TestCycle(
            cycle_name="Test Cycle",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            created_by=1
        )
        cycle.id = 1
        
        # Mock cycle exists
        mock_repositories["cycle_repository"].get = AsyncMock(
            return_value=cycle
        )
        
        # Mock report exists
        mock_repositories["report_repository"].get = AsyncMock(
            return_value={
                "report_id": 10,
                "report_name": "Test Report"
            }
        )
        
        # Mock tester exists and has permissions
        mock_repositories["user_repository"].get = AsyncMock(
            return_value={"user_id": 5, "username": "tester"}
        )
        mock_repositories["user_repository"].get_user_permissions = AsyncMock(
            return_value=["testing.execute", "testing.view"]
        )
        
        # Mock save
        mock_repositories["cycle_repository"].save = AsyncMock(
            return_value=cycle
        )
        
        # Mock workflow repository
        mock_repositories["workflow_repository"].save_phase_status = AsyncMock()
        
        # Mock other services
        mock_repositories["audit_service"].log_action = AsyncMock()
        mock_repositories["notification_service"].send_bulk_notifications = AsyncMock()
        
        # Act
        result = await use_case.execute(dto)
        
        # Assert
        assert result.success is True
        assert result.data.cycle_id == 1
        assert len(result.data.reports) == 1
        assert result.data.reports[0]["report_id"] == 10
        
        # Verify workflow phases were initialized
        assert mock_repositories["workflow_repository"].save_phase_status.call_count == 8
    
    @pytest.mark.asyncio
    async def test_add_report_cycle_not_found(self, use_case, mock_repositories):
        """Test adding report to non-existent cycle"""
        # Arrange
        dto = AddReportToCycleDTO(
            cycle_id=999,
            report_id=10,
            requested_by=1
        )
        
        # Mock cycle not found
        mock_repositories["cycle_repository"].get = AsyncMock(
            return_value=None
        )
        
        # Act
        result = await use_case.execute(dto)
        
        # Assert
        assert result.success is False
        assert "Test cycle not found" in result.error


def test_domain_entity_business_logic():
    """Test domain entity business logic"""
    # Create test cycle
    cycle = TestCycle(
        cycle_name="Test Cycle",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        created_by=1
    )
    
    # Test initial status
    assert cycle.status == CycleStatus.PLANNING
    
    # Test adding report
    cycle.add_report(
        report_id=1,
        report_name="Test Report",
        tester_id=5
    )
    assert len(cycle.reports) == 1
    assert cycle.reports[0].report_id == 1
    assert cycle.reports[0].tester_id == 5
    
    # Test transition to active
    cycle.transition_to_active()
    assert cycle.status == CycleStatus.ACTIVE
    
    # Test cannot add report when active
    with pytest.raises(Exception) as exc_info:
        cycle.add_report(
            report_id=2,
            report_name="Another Report"
        )
    assert "Cannot add reports when cycle is in ACTIVE status" in str(exc_info.value)
    
    # Test complete cycle
    cycle.complete()
    assert cycle.status == CycleStatus.COMPLETED