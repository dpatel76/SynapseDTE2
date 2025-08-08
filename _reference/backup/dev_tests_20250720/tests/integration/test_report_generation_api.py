"""
Integration tests for test report generation API
Tests the complete flow including ReportFormatter integration
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json

from app.main import app
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.observation_enhanced import TestReportPhase, TestReportSection
from app.models.user import User
from app.core.dependencies import get_db
from tests.conftest import override_get_db, create_test_user


@pytest.mark.asyncio
class TestReportGenerationAPI:
    """Test suite for report generation API endpoints"""
    
    @pytest.fixture
    async def test_data(self, db: AsyncSession):
        """Create test data for report generation"""
        # Create test cycle
        cycle = TestCycle(
            cycle_id=100,
            cycle_name="Integration Test Cycle",
            start_date=datetime(2024, 7, 1),
            end_date=datetime(2024, 9, 30),
            status="active"
        )
        db.add(cycle)
        
        # Create test report
        report = Report(
            report_id=200,
            report_name="FR Y-14Q Integration Test",
            lob_id=1,
            frequency="Quarterly"
        )
        db.add(report)
        
        # Create workflow phases
        phases = [
            WorkflowPhase(
                cycle_id=100,
                report_id=200,
                phase_name="Planning",
                state="Complete",
                status="All attributes catalogued"
            ),
            WorkflowPhase(
                cycle_id=100,
                report_id=200,
                phase_name="Observations",
                state="Complete",
                status="All observations finalized"
            ),
            WorkflowPhase(
                cycle_id=100,
                report_id=200,
                phase_name="Finalize Test Report",
                state="Not Started",
                status="Ready to generate report"
            )
        ]
        for phase in phases:
            db.add(phase)
        
        # Create test attributes
        for i in range(5):
            attr = ReportAttribute(
                cycle_id=100,
                report_id=200,
                attribute_name=f"Test Attribute {i+1}",
                is_scoped=i < 2,  # Only 2 scoped
                is_latest_version=True
            )
            db.add(attr)
        
        await db.commit()
        
        return {
            "cycle_id": 100,
            "report_id": 200,
            "total_attributes": 5,
            "scoped_attributes": 2
        }
    
    @pytest.fixture
    async def auth_headers(self, db: AsyncSession):
        """Create authenticated user and return headers"""
        user = await create_test_user(
            db,
            email="test@example.com",
            role="Tester"
        )
        
        # Mock authentication - in real tests, use proper auth flow
        return {"Authorization": f"Bearer test-token-{user.user_id}"}
    
    async def test_get_report_phase_creates_default(
        self,
        client: AsyncClient,
        test_data: dict,
        auth_headers: dict
    ):
        """Test getting report phase creates default if not exists"""
        response = await client.get(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/phase",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check default values
        assert data["cycle_id"] == test_data["cycle_id"]
        assert data["report_id"] == test_data["report_id"]
        assert data["status"] == "Not Started"
        assert data["include_executive_summary"] is True
        assert data["include_phase_artifacts"] is True
        assert data["include_detailed_observations"] is True
        assert data["include_metrics_dashboard"] is True
        
        # Check calculated metrics
        assert data["total_attributes"] == test_data["total_attributes"]
        assert data["scoped_attributes"] == test_data["scoped_attributes"]
    
    async def test_start_report_phase(
        self,
        client: AsyncClient,
        test_data: dict,
        auth_headers: dict
    ):
        """Test starting the test report phase"""
        response = await client.post(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/start",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Test report phase started successfully"
        
        # Verify phase status updated
        phase_response = await client.get(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/phase",
            headers=auth_headers
        )
        assert phase_response.json()["status"] == "In Progress"
    
    async def test_generate_report_with_formatter(
        self,
        client: AsyncClient,
        test_data: dict,
        auth_headers: dict,
        db: AsyncSession
    ):
        """Test report generation includes formatted data"""
        # Start the phase first
        await client.post(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/start",
            headers=auth_headers
        )
        
        # Generate report
        response = await client.post(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/generate",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for formatted report
        assert "formatted_report" in data
        formatted = data["formatted_report"]
        
        # Verify formatted sections
        assert "executive_summary" in formatted
        assert "strategic_approach" in formatted
        assert "testing_coverage" in formatted
        assert "markdown" in formatted
        assert "html" in formatted
        
        # Check positive framing in executive summary
        exec_summary = formatted["executive_summary"]
        assert "successfully completed" in exec_summary["overview"]
        assert len(exec_summary["key_achievements"]) > 0
        
        # Check coverage narrative
        coverage = formatted["testing_coverage"]
        assert coverage["tested_attributes"] == test_data["scoped_attributes"]
        assert coverage["total_attributes"] == test_data["total_attributes"]
        assert "risk-based" in coverage["coverage_narrative"].lower()
    
    async def test_get_report_sections_after_generation(
        self,
        client: AsyncClient,
        test_data: dict,
        auth_headers: dict
    ):
        """Test retrieving report sections after generation"""
        # Generate report first
        await client.post(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/start",
            headers=auth_headers
        )
        
        await client.post(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/generate",
            headers=auth_headers
        )
        
        # Get sections
        response = await client.get(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/sections",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        sections = response.json()
        
        # Should have multiple sections
        assert len(sections) > 5
        
        # Check for key sections
        section_names = [s["section_name"] for s in sections]
        assert "Executive Summary" in section_names
        assert "Strategic Approach" in section_names
        assert "Testing Coverage" in section_names
        assert "Full Report - HTML" in section_names
        
        # Verify HTML section exists
        html_section = next(
            (s for s in sections if s["section_type"] == "html"),
            None
        )
        assert html_section is not None
        assert len(html_section["content_text"]) > 1000  # Should have substantial content
    
    async def test_configure_report_options(
        self,
        client: AsyncClient,
        test_data: dict,
        auth_headers: dict
    ):
        """Test configuring report options"""
        config = {
            "include_executive_summary": True,
            "include_phase_artifacts": False,
            "include_detailed_observations": True,
            "include_metrics_dashboard": False
        }
        
        response = await client.put(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/configure",
            headers=auth_headers,
            json=config
        )
        
        assert response.status_code == 200
        
        # Verify configuration was saved
        phase_response = await client.get(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/phase",
            headers=auth_headers
        )
        phase_data = phase_response.json()
        
        assert phase_data["include_executive_summary"] is True
        assert phase_data["include_phase_artifacts"] is False
        assert phase_data["include_detailed_observations"] is True
        assert phase_data["include_metrics_dashboard"] is False
    
    async def test_minimal_coverage_scenario(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession
    ):
        """Test report generation with minimal coverage (like 0.88%)"""
        # Create minimal coverage scenario
        cycle = TestCycle(
            cycle_id=101,
            cycle_name="Minimal Coverage Test",
            start_date=datetime.now(),
            status="active"
        )
        db.add(cycle)
        
        report = Report(
            report_id=201,
            report_name="FR Y-14Q Minimal Test",
            lob_id=1
        )
        db.add(report)
        
        # Create 114 attributes, only 1 scoped
        for i in range(114):
            attr = ReportAttribute(
                cycle_id=101,
                report_id=201,
                attribute_name=f"Attribute {i+1}",
                is_scoped=(i == 0),  # Only first one scoped
                is_latest_version=True
            )
            db.add(attr)
        
        # Add necessary workflow phases
        phases = ["Planning", "Observations", "Finalize Test Report"]
        for phase_name in phases:
            phase = WorkflowPhase(
                cycle_id=101,
                report_id=201,
                phase_name=phase_name,
                state="Complete" if phase_name != "Finalize Test Report" else "Not Started"
            )
            db.add(phase)
        
        await db.commit()
        
        # Start and generate report
        await client.post(
            "/test-report/101/reports/201/start",
            headers=auth_headers
        )
        
        response = await client.post(
            "/test-report/101/reports/201/generate",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check formatted report emphasizes strategic focus
        formatted = data["formatted_report"]
        coverage = formatted["testing_coverage"]
        
        assert coverage["coverage_percentage"] < 1  # Very low coverage
        assert "strategically focused" in coverage["coverage_narrative"].lower()
        assert "superior assurance" in coverage["coverage_narrative"].lower()
        assert coverage["coverage_classification"] == "Targeted Risk-Based Coverage"
    
    async def test_error_handling_missing_prerequisites(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession
    ):
        """Test error when trying to generate report without completing prerequisites"""
        # Create incomplete workflow
        cycle = TestCycle(
            cycle_id=102,
            cycle_name="Incomplete Test",
            start_date=datetime.now(),
            status="active"
        )
        db.add(cycle)
        
        report = Report(
            report_id=202,
            report_name="Incomplete Report",
            lob_id=1
        )
        db.add(report)
        
        # Add phase but mark Observations as incomplete
        phase = WorkflowPhase(
            cycle_id=102,
            report_id=202,
            phase_name="Observations",
            state="In Progress"  # Not complete!
        )
        db.add(phase)
        
        await db.commit()
        
        # Try to generate report
        response = await client.post(
            "/test-report/102/reports/202/generate",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Observations phase must be completed first" in response.json()["detail"]
    
    async def test_get_report_data_endpoint(
        self,
        client: AsyncClient,
        test_data: dict,
        auth_headers: dict
    ):
        """Test the complete report data endpoint"""
        response = await client.get(
            f"/test-report/{test_data['cycle_id']}/reports/{test_data['report_id']}/data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have both raw and formatted data
        assert "raw_data" in data
        assert "formatted_report" in data
        
        # Check raw data structure
        raw = data["raw_data"]
        assert "metadata" in raw
        assert "executive_summary" in raw
        assert "phase_artifacts" in raw
        assert "observations" in raw
        assert "metrics" in raw


@pytest.mark.asyncio
class TestReportSecurity:
    """Test security aspects of report generation"""
    
    async def test_xss_prevention_in_report_name(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession
    ):
        """Test XSS prevention in report names"""
        # Create report with malicious name
        cycle = TestCycle(
            cycle_id=103,
            cycle_name="XSS Test Cycle",
            start_date=datetime.now()
        )
        db.add(cycle)
        
        report = Report(
            report_id=203,
            report_name="<script>alert('XSS')</script>Test Report",
            lob_id=1
        )
        db.add(report)
        
        # Add required phases
        for phase_name in ["Planning", "Observations"]:
            phase = WorkflowPhase(
                cycle_id=103,
                report_id=203,
                phase_name=phase_name,
                state="Complete"
            )
            db.add(phase)
        
        await db.commit()
        
        # Generate report
        await client.post(
            "/test-report/103/reports/203/start",
            headers=auth_headers
        )
        
        response = await client.post(
            "/test-report/103/reports/203/generate",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check HTML doesn't contain script tags
        html = data["formatted_report"]["html"]
        assert "<script>alert(" not in html
        assert "&lt;script&gt;" in html or "Test Report" in html
    
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test unauthorized access to report endpoints"""
        endpoints = [
            "/test-report/1/reports/1/phase",
            "/test-report/1/reports/1/sections",
            "/test-report/1/reports/1/data"
        ]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 401  # Unauthorized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])