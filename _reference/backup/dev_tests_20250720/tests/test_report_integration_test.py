"""
Test Report Integration Tests
End-to-end testing of the complete test report workflow
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import json
import tempfile
import os

from app.main import app
from app.core.dependencies import get_db
from app.models.base import Base
from app.models.test_report import TestReportSection, TestReportGeneration, STANDARD_REPORT_SECTIONS
from app.models.workflow import WorkflowPhase
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.lob import LOB


class TestReportIntegrationTest:
    """Integration tests for the complete test report workflow"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database and client"""
        # Create in-memory SQLite database for testing
        cls.db_fd, cls.db_path = tempfile.mkstemp()
        engine = create_engine(f"sqlite:///{cls.db_path}", connect_args={"check_same_thread": False})
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def override_get_db():
            try:
                db = cls.TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test database"""
        os.close(cls.db_fd)
        os.unlink(cls.db_path)
    
    def setup_method(self):
        """Set up test data for each test"""
        self.db = self.TestingSessionLocal()
        
        # Create test LOB
        self.test_lob = LOB(
            lob_id=1,
            lob_name="Test LOB",
            lob_description="Test Line of Business"
        )
        self.db.add(self.test_lob)
        
        # Create test user
        self.test_user = User(
            user_id=1,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role="Tester"
        )
        self.db.add(self.test_user)
        
        # Create executive user
        self.exec_user = User(
            user_id=2,
            email="exec@example.com",
            first_name="Executive",
            last_name="User",
            role="Executive"
        )
        self.db.add(self.exec_user)
        
        # Create test cycle
        self.test_cycle = TestCycle(
            cycle_id=1,
            cycle_name="Test Cycle Q1 2024",
            cycle_year=2024,
            cycle_quarter=1,
            cycle_status="Active"
        )
        self.db.add(self.test_cycle)
        
        # Create test report
        self.test_report = Report(
            id=1,
            report_name="Test Report",
            lob_id=1,
            description="Test report for integration testing",
            regulatory_framework="SOX",
            frequency="Quarterly"
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
    def test_complete_test_report_workflow(self, mock_get_current_user):
        """Test the complete test report workflow from start to finish"""
        mock_get_current_user.return_value = self.test_user
        
        # Step 1: Start the phase
        response = self.client.post("/test-report/1/reports/1/start")
        assert response.status_code == 200
        
        # Verify phase was started
        response = self.client.get("/test-report/1/reports/1/phase")
        assert response.status_code == 200
        phase_data = response.json()
        assert phase_data["state"] == "In Progress"
        
        # Step 2: Generate the report
        with patch('app.services.report_generation_service.ReportGenerationService') as mock_gen_service:
            # Mock the report generation service
            mock_gen_service.return_value.generate_executive_summary.return_value = {
                "summary": "Executive Summary",
                "content": "Test executive summary content",
                "metrics": {"total_attributes": 100, "test_pass_rate": 95.5}
            }
            mock_gen_service.return_value.generate_strategic_approach.return_value = {
                "summary": "Strategic Approach",
                "content": "Test strategic approach content"
            }
            
            response = self.client.post("/test-report/1/reports/1/generate", json={
                "sections": ["executive_summary", "strategic_approach"],
                "force_refresh": False
            })
            assert response.status_code == 200
            generation_data = response.json()
            assert generation_data["status"] == "completed"
            assert generation_data["total_sections"] == 2
            assert generation_data["sections_completed"] == 2
        
        # Step 3: Verify sections were created
        response = self.client.get("/test-report/1/reports/1/sections")
        assert response.status_code == 200
        sections = response.json()
        assert len(sections) == 2
        
        # Step 4: Check generation status
        response = self.client.get("/test-report/1/reports/1/generation/status")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["status"] == "completed"
        assert status_data["completion_percentage"] == 100.0
        
        # Step 5: Get specific section content
        response = self.client.get("/test-report/1/reports/1/sections/executive_summary")
        assert response.status_code == 200
        section_data = response.json()
        assert section_data["section_name"] == "executive_summary"
        assert section_data["section_title"] == "Executive Summary"
        assert section_data["is_fully_approved"] == False
        
        # Step 6: Approve sections (tester approval)
        sections_response = self.client.get("/test-report/1/reports/1/sections")
        sections = sections_response.json()
        
        for section in sections:
            response = self.client.post(
                f"/test-report/1/reports/1/sections/{section['id']}/approve",
                json={"approval_level": "tester", "notes": "Approved by tester"}
            )
            assert response.status_code == 200
        
        # Step 7: Approve sections (report owner approval)
        mock_get_current_user.return_value = User(
            user_id=3,
            email="owner@example.com",
            first_name="Report",
            last_name="Owner",
            role="Report Owner"
        )
        
        for section in sections:
            response = self.client.post(
                f"/test-report/1/reports/1/sections/{section['id']}/approve",
                json={"approval_level": "report_owner", "notes": "Approved by report owner"}
            )
            assert response.status_code == 200
        
        # Step 8: Approve sections (executive approval)
        mock_get_current_user.return_value = self.exec_user
        
        for section in sections:
            response = self.client.post(
                f"/test-report/1/reports/1/sections/{section['id']}/approve",
                json={"approval_level": "executive", "notes": "Approved by executive"}
            )
            assert response.status_code == 200
        
        # Step 9: Check approval status
        response = self.client.get("/test-report/1/reports/1/approvals")
        assert response.status_code == 200
        approval_data = response.json()
        assert approval_data["total_sections"] == 2
        assert approval_data["fully_approved"] == 2
        assert approval_data["pending_tester"] == 0
        assert approval_data["pending_report_owner"] == 0
        assert approval_data["pending_executive"] == 0
        
        # Step 10: Complete the phase
        response = self.client.post("/test-report/1/reports/1/complete")
        assert response.status_code == 200
        
        # Step 11: Verify phase completion
        response = self.client.get("/test-report/1/reports/1/phase")
        assert response.status_code == 200
        phase_data = response.json()
        assert phase_data["state"] == "Complete"
        assert phase_data["status"] == "Complete"
        
        # Step 12: Generate final report
        response = self.client.post("/test-report/1/reports/1/final-report")
        assert response.status_code == 200
        final_report_data = response.json()
        assert "pdf_path" in final_report_data
        assert final_report_data["message"] == "Final report generated successfully"
    
    @patch('app.core.dependencies.get_current_user')
    def test_approval_workflow_rejection(self, mock_get_current_user):
        """Test the approval workflow with rejection"""
        mock_get_current_user.return_value = self.test_user
        
        # Start phase and generate report
        self.client.post("/test-report/1/reports/1/start")
        
        with patch('app.services.report_generation_service.ReportGenerationService') as mock_gen_service:
            mock_gen_service.return_value.generate_executive_summary.return_value = {
                "summary": "Executive Summary",
                "content": "Test content"
            }
            
            self.client.post("/test-report/1/reports/1/generate", json={
                "sections": ["executive_summary"],
                "force_refresh": False
            })
        
        # Get the section
        sections_response = self.client.get("/test-report/1/reports/1/sections")
        sections = sections_response.json()
        section_id = sections[0]['id']
        
        # Reject the section
        response = self.client.post(
            f"/test-report/1/reports/1/sections/{section_id}/reject",
            json={"approval_level": "tester", "notes": "Needs more detail"}
        )
        assert response.status_code == 200
        
        # Verify rejection
        response = self.client.get(f"/test-report/1/reports/1/sections/executive_summary")
        assert response.status_code == 200
        section_data = response.json()
        assert section_data["status"] == "rejected"
        
        # Verify phase cannot be completed
        response = self.client.post("/test-report/1/reports/1/complete")
        assert response.status_code == 400
        assert "Not all sections are fully approved" in response.json()["detail"]
    
    @patch('app.core.dependencies.get_current_user')
    def test_approval_workflow_revision_request(self, mock_get_current_user):
        """Test the approval workflow with revision request"""
        mock_get_current_user.return_value = self.test_user
        
        # Start phase and generate report
        self.client.post("/test-report/1/reports/1/start")
        
        with patch('app.services.report_generation_service.ReportGenerationService') as mock_gen_service:
            mock_gen_service.return_value.generate_executive_summary.return_value = {
                "summary": "Executive Summary",
                "content": "Test content"
            }
            
            self.client.post("/test-report/1/reports/1/generate", json={
                "sections": ["executive_summary"],
                "force_refresh": False
            })
        
        # Get the section
        sections_response = self.client.get("/test-report/1/reports/1/sections")
        sections = sections_response.json()
        section_id = sections[0]['id']
        
        # Request revision
        response = self.client.post(
            f"/test-report/1/reports/1/sections/{section_id}/request-revision",
            json={"revision_level": "tester", "notes": "Please add more metrics"}
        )
        assert response.status_code == 200
        
        # Verify revision request
        response = self.client.get(f"/test-report/1/reports/1/sections/executive_summary")
        assert response.status_code == 200
        section_data = response.json()
        assert section_data["status"] == "revision_requested"
    
    @patch('app.core.dependencies.get_current_user')
    def test_section_regeneration(self, mock_get_current_user):
        """Test section regeneration"""
        mock_get_current_user.return_value = self.test_user
        
        # Start phase and generate report
        self.client.post("/test-report/1/reports/1/start")
        
        with patch('app.services.report_generation_service.ReportGenerationService') as mock_gen_service:
            mock_gen_service.return_value.generate_executive_summary.return_value = {
                "summary": "Executive Summary",
                "content": "Original content"
            }
            
            self.client.post("/test-report/1/reports/1/generate", json={
                "sections": ["executive_summary"],
                "force_refresh": False
            })
        
        # Verify original content
        response = self.client.get("/test-report/1/reports/1/sections/executive_summary")
        assert response.status_code == 200
        section_data = response.json()
        assert section_data["section_content"]["content"] == "Original content"
        
        # Regenerate section
        with patch('app.services.report_generation_service.ReportGenerationService') as mock_gen_service:
            mock_gen_service.return_value.generate_executive_summary.return_value = {
                "summary": "Executive Summary",
                "content": "Updated content"
            }
            
            response = self.client.post(
                "/test-report/1/reports/1/sections/executive_summary/regenerate",
                params={"force_refresh": True}
            )
            assert response.status_code == 200
        
        # Verify updated content
        response = self.client.get("/test-report/1/reports/1/sections/executive_summary")
        assert response.status_code == 200
        section_data = response.json()
        assert section_data["section_content"]["content"] == "Updated content"
    
    @patch('app.core.dependencies.get_current_user')
    def test_pending_approvals(self, mock_get_current_user):
        """Test getting pending approvals for a user"""
        mock_get_current_user.return_value = self.test_user
        
        # Start phase and generate report
        self.client.post("/test-report/1/reports/1/start")
        
        with patch('app.services.report_generation_service.ReportGenerationService') as mock_gen_service:
            mock_gen_service.return_value.generate_executive_summary.return_value = {
                "summary": "Executive Summary",
                "content": "Test content"
            }
            mock_gen_service.return_value.generate_strategic_approach.return_value = {
                "summary": "Strategic Approach",
                "content": "Test content"
            }
            
            self.client.post("/test-report/1/reports/1/generate", json={
                "sections": ["executive_summary", "strategic_approach"],
                "force_refresh": False
            })
        
        # Get pending approvals
        response = self.client.get("/test-report/1/reports/1/pending-approvals")
        assert response.status_code == 200
        pending_approvals = response.json()
        assert len(pending_approvals) == 2  # Two sections pending tester approval
        
        # Approve one section
        sections_response = self.client.get("/test-report/1/reports/1/sections")
        sections = sections_response.json()
        section_id = sections[0]['id']
        
        self.client.post(
            f"/test-report/1/reports/1/sections/{section_id}/approve",
            json={"approval_level": "tester", "notes": "Approved"}
        )
        
        # Check pending approvals again
        response = self.client.get("/test-report/1/reports/1/pending-approvals")
        assert response.status_code == 200
        pending_approvals = response.json()
        assert len(pending_approvals) == 1  # One section still pending tester approval
    
    @patch('app.core.dependencies.get_current_user')
    def test_approval_history(self, mock_get_current_user):
        """Test getting approval history for a section"""
        mock_get_current_user.return_value = self.test_user
        
        # Start phase and generate report
        self.client.post("/test-report/1/reports/1/start")
        
        with patch('app.services.report_generation_service.ReportGenerationService') as mock_gen_service:
            mock_gen_service.return_value.generate_executive_summary.return_value = {
                "summary": "Executive Summary",
                "content": "Test content"
            }
            
            self.client.post("/test-report/1/reports/1/generate", json={
                "sections": ["executive_summary"],
                "force_refresh": False
            })
        
        # Get the section
        sections_response = self.client.get("/test-report/1/reports/1/sections")
        sections = sections_response.json()
        section_id = sections[0]['id']
        
        # Approve at tester level
        self.client.post(
            f"/test-report/1/reports/1/sections/{section_id}/approve",
            json={"approval_level": "tester", "notes": "Approved by tester"}
        )
        
        # Get approval history
        response = self.client.get(f"/test-report/1/reports/1/sections/{section_id}/approval-history")
        assert response.status_code == 200
        history = response.json()
        assert len(history) == 1
        assert history[0]['level'] == 'tester'
        assert history[0]['action'] == 'approved'
        assert history[0]['notes'] == 'Approved by tester'
    
    @patch('app.core.dependencies.get_current_user')
    def test_report_metrics(self, mock_get_current_user):
        """Test getting report metrics"""
        mock_get_current_user.return_value = self.test_user
        
        # Start phase and generate report
        self.client.post("/test-report/1/reports/1/start")
        
        with patch('app.services.report_generation_service.ReportGenerationService') as mock_gen_service:
            mock_gen_service.return_value.generate_executive_summary.return_value = {
                "summary": "Executive Summary",
                "content": "Test content"
            }
            
            self.client.post("/test-report/1/reports/1/generate", json={
                "sections": ["executive_summary"],
                "force_refresh": False
            })
        
        # Get metrics
        response = self.client.get("/test-report/1/reports/1/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert "total_sections" in metrics
        assert "completion_rate" in metrics
        assert "avg_approval_time" in metrics
        assert "bottlenecks" in metrics
    
    def test_error_handling_phase_not_found(self):
        """Test error handling when phase is not found"""
        response = self.client.get("/test-report/999/reports/999/phase")
        assert response.status_code == 404
        assert "Test report phase not found" in response.json()["detail"]
    
    def test_error_handling_section_not_found(self):
        """Test error handling when section is not found"""
        response = self.client.get("/test-report/1/reports/1/sections/nonexistent")
        assert response.status_code == 404
        assert "Section not found" in response.json()["detail"]
    
    @patch('app.core.dependencies.get_current_user')
    def test_error_handling_unauthorized_approval(self, mock_get_current_user):
        """Test error handling for unauthorized approval"""
        mock_get_current_user.return_value = self.test_user
        
        # Start phase and generate report
        self.client.post("/test-report/1/reports/1/start")
        
        with patch('app.services.report_generation_service.ReportGenerationService') as mock_gen_service:
            mock_gen_service.return_value.generate_executive_summary.return_value = {
                "summary": "Executive Summary",
                "content": "Test content"
            }
            
            self.client.post("/test-report/1/reports/1/generate", json={
                "sections": ["executive_summary"],
                "force_refresh": False
            })
        
        # Get the section
        sections_response = self.client.get("/test-report/1/reports/1/sections")
        sections = sections_response.json()
        section_id = sections[0]['id']
        
        # Try to approve at wrong level
        response = self.client.post(
            f"/test-report/1/reports/1/sections/{section_id}/approve",
            json={"approval_level": "executive", "notes": "Trying to skip levels"}
        )
        assert response.status_code == 400
        assert "Expected approval level" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])