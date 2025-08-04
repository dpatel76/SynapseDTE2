"""
Test Report Model Tests
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from app.models.test_report import TestReportSection, TestReportGeneration, STANDARD_REPORT_SECTIONS


class TestTestReportSection:
    """Test cases for TestReportSection model"""
    
    def test_initialization(self):
        """Test TestReportSection initialization"""
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
        
        assert section.phase_id == 1
        assert section.cycle_id == 1
        assert section.report_id == 1
        assert section.section_name == "executive_summary"
        assert section.section_title == "Executive Summary"
        assert section.section_order == 1
        assert section.section_content == {"summary": "Test summary"}
        assert section.status == "draft"
        assert section.tester_approved == False
        assert section.report_owner_approved == False
        assert section.executive_approved == False
    
    def test_is_fully_approved_true(self):
        """Test is_fully_approved when all approvals are received"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            tester_approved=True,
            report_owner_approved=True,
            executive_approved=True,
            created_by=1,
            updated_by=1
        )
        
        assert section.is_fully_approved() == True
    
    def test_is_fully_approved_false(self):
        """Test is_fully_approved when not all approvals are received"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            tester_approved=True,
            report_owner_approved=True,
            executive_approved=False,  # Missing executive approval
            created_by=1,
            updated_by=1
        )
        
        assert section.is_fully_approved() == False
    
    def test_approve_section_tester(self):
        """Test approving section at tester level"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            created_by=1,
            updated_by=1
        )
        
        approver_id = 1
        approval_level = "tester"
        notes = "Approved by tester"
        
        result = section.approve_section(approver_id, approval_level, notes)
        
        assert result == True
        assert section.tester_approved == True
        assert section.tester_approved_by == approver_id
        assert section.tester_notes == notes
        assert section.tester_approved_at is not None
    
    def test_approve_section_report_owner(self):
        """Test approving section at report owner level"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            created_by=1,
            updated_by=1
        )
        
        approver_id = 2
        approval_level = "report_owner"
        notes = "Approved by report owner"
        
        result = section.approve_section(approver_id, approval_level, notes)
        
        assert result == True
        assert section.report_owner_approved == True
        assert section.report_owner_approved_by == approver_id
        assert section.report_owner_notes == notes
        assert section.report_owner_approved_at is not None
    
    def test_approve_section_executive(self):
        """Test approving section at executive level"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            created_by=1,
            updated_by=1
        )
        
        approver_id = 3
        approval_level = "executive"
        notes = "Approved by executive"
        
        result = section.approve_section(approver_id, approval_level, notes)
        
        assert result == True
        assert section.executive_approved == True
        assert section.executive_approved_by == approver_id
        assert section.executive_notes == notes
        assert section.executive_approved_at is not None
    
    def test_approve_section_invalid_level(self):
        """Test approving section with invalid level"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            created_by=1,
            updated_by=1
        )
        
        result = section.approve_section(1, "invalid_level", "test")
        
        assert result == False
        assert section.tester_approved == False
        assert section.report_owner_approved == False
        assert section.executive_approved == False
    
    def test_get_approval_status_pending_tester(self):
        """Test get_approval_status when pending tester approval"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            created_by=1,
            updated_by=1
        )
        
        assert section.get_approval_status() == "pending_tester"
    
    def test_get_approval_status_pending_report_owner(self):
        """Test get_approval_status when pending report owner approval"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            tester_approved=True,
            created_by=1,
            updated_by=1
        )
        
        assert section.get_approval_status() == "pending_report_owner"
    
    def test_get_approval_status_pending_executive(self):
        """Test get_approval_status when pending executive approval"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            tester_approved=True,
            report_owner_approved=True,
            created_by=1,
            updated_by=1
        )
        
        assert section.get_approval_status() == "pending_executive"
    
    def test_get_approval_status_fully_approved(self):
        """Test get_approval_status when fully approved"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            tester_approved=True,
            report_owner_approved=True,
            executive_approved=True,
            created_by=1,
            updated_by=1
        )
        
        assert section.get_approval_status() == "fully_approved"
    
    def test_get_next_approver_level_tester(self):
        """Test get_next_approver_level when tester approval is needed"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            created_by=1,
            updated_by=1
        )
        
        assert section.get_next_approver_level() == "tester"
    
    def test_get_next_approver_level_report_owner(self):
        """Test get_next_approver_level when report owner approval is needed"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            tester_approved=True,
            created_by=1,
            updated_by=1
        )
        
        assert section.get_next_approver_level() == "report_owner"
    
    def test_get_next_approver_level_executive(self):
        """Test get_next_approver_level when executive approval is needed"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            tester_approved=True,
            report_owner_approved=True,
            created_by=1,
            updated_by=1
        )
        
        assert section.get_next_approver_level() == "executive"
    
    def test_get_next_approver_level_none(self):
        """Test get_next_approver_level when fully approved"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            tester_approved=True,
            report_owner_approved=True,
            executive_approved=True,
            created_by=1,
            updated_by=1
        )
        
        assert section.get_next_approver_level() is None
    
    def test_can_regenerate_approved_section(self):
        """Test can_regenerate for approved section"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            tester_approved=True,
            report_owner_approved=True,
            executive_approved=True,
            created_by=1,
            updated_by=1
        )
        
        assert section.can_regenerate() == False
    
    def test_can_regenerate_non_approved_section(self):
        """Test can_regenerate for non-approved section"""
        section = TestReportSection(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            section_name="executive_summary",
            section_title="Executive Summary",
            section_order=1,
            created_by=1,
            updated_by=1
        )
        
        assert section.can_regenerate() == True


class TestTestReportGeneration:
    """Test cases for TestReportGeneration model"""
    
    def test_initialization(self):
        """Test TestReportGeneration initialization"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1
        )
        
        assert generation.phase_id == 1
        assert generation.cycle_id == 1
        assert generation.report_id == 1
        assert generation.generated_by == 1
        assert generation.status == "pending"
        assert generation.all_approvals_received == False
        assert generation.phase_completion_ready == False
    
    def test_start_generation(self):
        """Test start_generation method"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1
        )
        
        user_id = 2
        generation.start_generation(user_id)
        
        assert generation.status == "in_progress"
        assert generation.generated_by == user_id
        assert generation.generation_started_at is not None
        assert generation.error_message is None
    
    def test_complete_generation(self):
        """Test complete_generation method"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1
        )
        
        # First start generation
        generation.start_generation(1)
        
        # Then complete it
        total_sections = 8
        sections_completed = 8
        generation.complete_generation(total_sections, sections_completed)
        
        assert generation.status == "completed"
        assert generation.total_sections == total_sections
        assert generation.sections_completed == sections_completed
        assert generation.generation_completed_at is not None
        assert generation.generation_duration_ms is not None
        assert generation.generation_duration_ms > 0
    
    def test_fail_generation(self):
        """Test fail_generation method"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1
        )
        
        error_message = "Generation failed due to missing data"
        generation.fail_generation(error_message)
        
        assert generation.status == "failed"
        assert generation.error_message == error_message
        assert generation.generation_completed_at is not None
    
    def test_get_completion_percentage_no_sections(self):
        """Test get_completion_percentage when no sections"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1
        )
        
        assert generation.get_completion_percentage() == 0.0
    
    def test_get_completion_percentage_partial(self):
        """Test get_completion_percentage with partial completion"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1,
            total_sections=8,
            sections_completed=6
        )
        
        assert generation.get_completion_percentage() == 75.0
    
    def test_get_completion_percentage_complete(self):
        """Test get_completion_percentage with full completion"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1,
            total_sections=8,
            sections_completed=8
        )
        
        assert generation.get_completion_percentage() == 100.0
    
    def test_is_ready_for_approval_true(self):
        """Test is_ready_for_approval when generation is complete"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1,
            status="completed",
            total_sections=8,
            sections_completed=8
        )
        
        assert generation.is_ready_for_approval() == True
    
    def test_is_ready_for_approval_false(self):
        """Test is_ready_for_approval when generation is not complete"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1,
            status="in_progress",
            total_sections=8,
            sections_completed=6
        )
        
        assert generation.is_ready_for_approval() == False
    
    def test_is_ready_for_approval_failed(self):
        """Test is_ready_for_approval when generation failed"""
        generation = TestReportGeneration(
            phase_id=1,
            cycle_id=1,
            report_id=1,
            generated_by=1,
            status="failed",
            error_message="Generation failed"
        )
        
        assert generation.is_ready_for_approval() == False


class TestStandardReportSections:
    """Test cases for STANDARD_REPORT_SECTIONS constant"""
    
    def test_standard_sections_structure(self):
        """Test that STANDARD_REPORT_SECTIONS has correct structure"""
        assert isinstance(STANDARD_REPORT_SECTIONS, list)
        assert len(STANDARD_REPORT_SECTIONS) == 8
        
        for section in STANDARD_REPORT_SECTIONS:
            assert isinstance(section, dict)
            assert 'name' in section
            assert 'title' in section
            assert 'order' in section
            assert 'data_sources' in section
            assert isinstance(section['data_sources'], list)
    
    def test_standard_sections_order(self):
        """Test that STANDARD_REPORT_SECTIONS are in correct order"""
        orders = [section['order'] for section in STANDARD_REPORT_SECTIONS]
        assert orders == sorted(orders)
        assert orders == list(range(1, 9))
    
    def test_standard_sections_names(self):
        """Test that all expected section names are present"""
        expected_names = [
            'executive_summary',
            'strategic_approach',
            'testing_coverage',
            'phase_analysis',
            'testing_results',
            'value_delivery',
            'recommendations',
            'executive_attestation'
        ]
        
        actual_names = [section['name'] for section in STANDARD_REPORT_SECTIONS]
        assert set(actual_names) == set(expected_names)
    
    def test_standard_sections_unique_names(self):
        """Test that all section names are unique"""
        names = [section['name'] for section in STANDARD_REPORT_SECTIONS]
        assert len(names) == len(set(names))
    
    def test_standard_sections_unique_orders(self):
        """Test that all section orders are unique"""
        orders = [section['order'] for section in STANDARD_REPORT_SECTIONS]
        assert len(orders) == len(set(orders))


if __name__ == "__main__":
    pytest.main([__file__])