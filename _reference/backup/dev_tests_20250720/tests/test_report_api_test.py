"""
Test Report API Endpoint Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import json

from app.main import app
from app.core.dependencies import get_db
from app.models.test_report import TestReportSection, TestReportGeneration, STANDARD_REPORT_SECTIONS
from app.models.workflow import WorkflowPhase
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_test_reports.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestTestReportAPI:
    """Test cases for Test Report API endpoints"""
    
    def setup_method(self):
        """Setup test data"""
        self.db = TestingSessionLocal()
        
        # Create test user
        self.test_user = User(
            user_id=1,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role="Tester"
        )
        self.db.add(self.test_user)
        
        # Create test cycle
        self.test_cycle = TestCycle(
            cycle_id=1,
            cycle_name="Test Cycle",
            cycle_year=2024,
            cycle_quarter=1
        )
        self.db.add(self.test_cycle)
        
        # Create test report
        self.test_report = Report(
            id=1,
            report_name="Test Report",
            lob_name="Test LOB"
        )
        self.db.add(self.test_report)
        
        # Create test phase
        self.test_phase = WorkflowPhase(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            phase_name="Finalize Test Report",
            phase_order=9,
            status="Not Started",
            state="Not Started"
        )
        self.db.add(self.test_phase)
        
        self.db.commit()
    
    def teardown_method(self):
        """Clean up test data"""
        self.db.close()
    
    @patch('app.core.dependencies.get_current_user')
    def test_get_test_report_phase(self, mock_get_current_user):
        """Test GET /test-report/{cycle_id}/reports/{report_id}/phase"""
        mock_get_current_user.return_value = self.test_user
        
        response = client.get("/test-report/1/reports/1/phase")
        
        assert response.status_code == 200
        data = response.json()
        assert data["phase_id"] == 1
        assert data["cycle_id"] == 1
        assert data["report_id"] == 1
        assert data["phase_name"] == "Finalize Test Report"
        assert data["status"] == "Not Started"
    
    @patch('app.core.dependencies.get_current_user')
    def test_start_test_report_phase(self, mock_get_current_user):
        """Test POST /test-report/{cycle_id}/reports/{report_id}/start"""
        mock_get_current_user.return_value = self.test_user
        
        response = client.post("/test-report/1/reports/1/start")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Test report phase started successfully"
        
        # Verify phase was updated
        phase = self.db.query(WorkflowPhase).filter(WorkflowPhase.phase_id == 1).first()
        assert phase.state == "In Progress"
        assert phase.status == "In Progress"
        assert phase.started_by == 1
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.test_report_service.TestReportService.generate_test_report')
    def test_generate_test_report(self, mock_generate, mock_get_current_user):
        """Test POST /test-report/{cycle_id}/reports/{report_id}/generate"""
        mock_get_current_user.return_value = self.test_user
        
        # Mock the generation
        mock_generation = Mock()
        mock_generation.id = 1
        mock_generation.status = "completed"
        mock_generation.total_sections = 8
        mock_generation.sections_completed = 8
        mock_generation.output_formats_generated = ["json", "markdown", "html"]
        mock_generate.return_value = mock_generation
        
        response = client.post("/test-report/1/reports/1/generate", json={
            "sections": ["executive_summary", "strategic_approach"],
            "force_refresh": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["generation_id"] == 1
        assert data["status"] == "completed"
        assert data["total_sections"] == 8
        assert data["sections_completed"] == 8
        assert data["output_formats"] == ["json", "markdown", "html"]
    
    @patch('app.core.dependencies.get_current_user')
    def test_get_generation_status(self, mock_get_current_user):
        """Test GET /test-report/{cycle_id}/reports/{report_id}/generation/status"""
        mock_get_current_user.return_value = self.test_user
        
        # Create a generation record
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1,
            status="completed",
            total_sections=8,
            sections_completed=8
        )
        self.db.add(generation)
        self.db.commit()
        
        response = client.get("/test-report/1/reports/1/generation/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_sections"] == 8
        assert data["sections_completed"] == 8
        assert data["completion_percentage"] == 100.0
    
    @patch('app.core.dependencies.get_current_user')
    def test_get_report_sections(self, mock_get_current_user):
        """Test GET /test-report/{cycle_id}/reports/{report_id}/sections"""
        mock_get_current_user.return_value = self.test_user
        
        # Create test sections
        section1 = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            section_content={"summary": "Test summary"},
            created_by=1,
            updated_by=1
        )
        section2 = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="strategic_approach",
            section_title="Strategic Approach",
            section_order=2,
            section_content={"approach": "Test approach"},
            created_by=1,
            updated_by=1
        )
        self.db.add(section1)
        self.db.add(section2)
        self.db.commit()
        
        response = client.get("/test-report/1/reports/1/sections")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["section_name"] == "executive_summary"
        assert data[0]["section_title"] == "Executive Summary"
        assert data[0]["section_order"] == 1
        assert data[1]["section_name"] == "strategic_approach"
        assert data[1]["section_title"] == "Strategic Approach"
        assert data[1]["section_order"] == 2
    
    @patch('app.core.dependencies.get_current_user')
    def test_get_section_content(self, mock_get_current_user):
        """Test GET /test-report/{cycle_id}/reports/{report_id}/sections/{section_name}"""
        mock_get_current_user.return_value = self.test_user
        
        # Create test section
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            section_content={"summary": "Test summary", "key_findings": ["Finding 1", "Finding 2"]},
            markdown_content="# Executive Summary\n\nTest summary",
            html_content="<h1>Executive Summary</h1><p>Test summary</p>",
            created_by=1,
            updated_by=1
        )
        self.db.add(section)
        self.db.commit()
        
        response = client.get("/test-report/1/reports/1/sections/executive_summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["section_name"] == "executive_summary"
        assert data["section_title"] == "Executive Summary"
        assert data["section_content"]["summary"] == "Test summary"
        assert data["section_content"]["key_findings"] == ["Finding 1", "Finding 2"]
        assert data["markdown_content"] == "# Executive Summary\n\nTest summary"
        assert data["html_content"] == "<h1>Executive Summary</h1><p>Test summary</p>"
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.approval_workflow_service.ApprovalWorkflowService.approve_section')
    def test_approve_section(self, mock_approve, mock_get_current_user):
        """Test POST /test-report/{cycle_id}/reports/{report_id}/sections/{section_id}/approve"""
        mock_get_current_user.return_value = self.test_user
        
        # Create test section
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            section_content={"summary": "Test summary"},
            created_by=1,
            updated_by=1
        )
        self.db.add(section)
        self.db.commit()
        
        # Mock the approval
        mock_section = Mock()
        mock_section.id = section.id
        mock_section.section_name = "executive_summary"
        mock_section.get_approval_status.return_value = "pending_report_owner"
        mock_section.get_next_approver_level.return_value = "report_owner"
        mock_section.is_fully_approved.return_value = False
        mock_approve.return_value = mock_section
        
        response = client.post(f"/test-report/1/reports/1/sections/{section.id}/approve", json={
            "approval_level": "tester",
            "notes": "Approved by tester"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["section_id"] == section.id
        assert data["section_name"] == "executive_summary"
        assert data["approval_level"] == "tester"
        assert data["approval_status"] == "pending_report_owner"
        assert data["next_approver"] == "report_owner"
        assert data["is_fully_approved"] == False
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.approval_workflow_service.ApprovalWorkflowService.reject_section')
    def test_reject_section(self, mock_reject, mock_get_current_user):
        """Test POST /test-report/{cycle_id}/reports/{report_id}/sections/{section_id}/reject"""
        mock_get_current_user.return_value = self.test_user
        
        # Create test section
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            section_content={"summary": "Test summary"},
            created_by=1,
            updated_by=1
        )
        self.db.add(section)
        self.db.commit()
        
        # Mock the rejection
        mock_section = Mock()
        mock_section.id = section.id
        mock_section.section_name = "executive_summary"
        mock_section.status = "rejected"
        mock_reject.return_value = mock_section
        
        response = client.post(f"/test-report/1/reports/1/sections/{section.id}/reject", json={
            "approval_level": "tester",
            "notes": "Rejected due to incomplete data"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["section_id"] == section.id
        assert data["section_name"] == "executive_summary"
        assert data["rejection_level"] == "tester"
        assert data["status"] == "rejected"
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.approval_workflow_service.ApprovalWorkflowService.complete_phase')
    def test_complete_test_report_phase(self, mock_complete, mock_get_current_user):
        """Test POST /test-report/{cycle_id}/reports/{report_id}/complete"""
        mock_get_current_user.return_value = self.test_user
        
        # Mock successful completion
        mock_complete.return_value = True
        
        response = client.post("/test-report/1/reports/1/complete")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Test report phase completed successfully"
        
        # Verify the complete_phase method was called
        mock_complete.assert_called_once_with(1, 1)
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.approval_workflow_service.ApprovalWorkflowService.complete_phase')
    def test_complete_test_report_phase_not_ready(self, mock_complete, mock_get_current_user):
        """Test POST /test-report/{cycle_id}/reports/{report_id}/complete when not ready"""
        mock_get_current_user.return_value = self.test_user
        
        # Mock failure
        mock_complete.side_effect = ValueError("Cannot complete phase: Not all sections are fully approved")
        
        response = client.post("/test-report/1/reports/1/complete")
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Cannot complete phase: Not all sections are fully approved"
    
    @patch('app.core.dependencies.get_current_user')
    def test_get_approval_status(self, mock_get_current_user):
        """Test GET /test-report/{cycle_id}/reports/{report_id}/approvals"""
        mock_get_current_user.return_value = self.test_user
        
        # Create test sections with different approval states
        section1 = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            section_content={"summary": "Test summary"},
            tester_approved=True,
            tester_approved_by=1,
            created_by=1,
            updated_by=1
        )
        section2 = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="strategic_approach",
            section_title="Strategic Approach",
            section_order=2,
            section_content={"approach": "Test approach"},
            created_by=1,
            updated_by=1
        )
        self.db.add(section1)
        self.db.add(section2)
        self.db.commit()
        
        response = client.get("/test-report/1/reports/1/approvals")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_sections" in data
        assert "pending_tester" in data
        assert "pending_report_owner" in data
        assert "pending_executive" in data
        assert "fully_approved" in data
        assert "sections" in data
    
    def test_phase_not_found(self):
        """Test endpoints when phase is not found"""
        response = client.get("/test-report/999/reports/999/phase")
        assert response.status_code == 404
        assert "Test report phase not found" in response.json()["detail"]
    
    def test_section_not_found(self):
        """Test endpoints when section is not found"""
        response = client.get("/test-report/1/reports/1/sections/nonexistent")
        assert response.status_code == 404
        assert "Section not found" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])