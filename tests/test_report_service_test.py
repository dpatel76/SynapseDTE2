"""
Test Report Service Tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.test_report_service import TestReportService
from app.services.approval_workflow_service import ApprovalWorkflowService
from app.services.report_generation_service import ReportGenerationService
from app.models.test_report import TestReportSection, TestReportGeneration, STANDARD_REPORT_SECTIONS
from app.models.workflow import WorkflowPhase
from app.models.user import User


class TestTestReportService:
    """Test cases for TestReportService"""
    
    def setup_method(self):
        """Setup test dependencies"""
        self.mock_db = Mock(spec=Session)
        self.service = TestReportService(self.mock_db)
    
    @pytest.mark.asyncio
    async def test_generate_test_report_new_generation(self):
        """Test generating a new test report"""
        phase_id = 1
        user_id = 1
        sections = ["executive_summary", "strategic_approach"]
        
        # Mock phase lookup
        mock_phase = Mock()
        mock_phase.phase_id = phase_id
        mock_phase.cycle_id = 1
        mock_phase.report_id = 1
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_phase
        
        # Mock generation lookup (no existing generation)
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [None, mock_phase]
        
        # Mock generate_section calls
        mock_section1 = Mock()
        mock_section1.section_name = "executive_summary"
        mock_section2 = Mock()
        mock_section2.section_name = "strategic_approach"
        
        with patch.object(self.service, 'generate_section', side_effect=[mock_section1, mock_section2]):
            result = await self.service.generate_test_report(phase_id, user_id, sections)
        
        # Verify generation was created
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()
        
        # Verify sections were generated
        assert result.status == 'completed'
        assert result.total_sections == 2
        assert result.sections_completed == 2
    
    @pytest.mark.asyncio
    async def test_generate_test_report_existing_generation(self):
        """Test generating test report with existing generation"""
        phase_id = 1
        user_id = 1
        
        # Mock existing generation
        mock_generation = Mock()
        mock_generation.status = 'pending'
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_generation
        
        # Mock generate_section calls
        mock_section = Mock()
        mock_section.section_name = "executive_summary"
        
        with patch.object(self.service, 'generate_section', return_value=mock_section):
            result = await self.service.generate_test_report(phase_id, user_id)
        
        # Verify existing generation was used
        self.mock_db.add.assert_not_called()
        assert result == mock_generation
    
    @pytest.mark.asyncio
    async def test_generate_test_report_with_error(self):
        """Test test report generation with error"""
        phase_id = 1
        user_id = 1
        
        # Mock phase lookup
        mock_phase = Mock()
        mock_phase.phase_id = phase_id
        mock_phase.cycle_id = 1
        mock_phase.report_id = 1
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_phase
        
        # Mock generation lookup (no existing generation)
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [None, mock_phase]
        
        # Mock generate_section to raise error
        with patch.object(self.service, 'generate_section', side_effect=Exception("Generation failed")):
            result = await self.service.generate_test_report(phase_id, user_id)
        
        # Verify error was handled
        assert result.status == 'failed'
        assert result.error_message == "Generation failed"
    
    @pytest.mark.asyncio
    async def test_generate_section_new_section(self):
        """Test generating a new section"""
        phase_id = 1
        section_name = "executive_summary"
        user_id = 1
        
        # Mock phase lookup
        mock_phase = Mock()
        mock_phase.phase_id = phase_id
        mock_phase.cycle_id = 1
        mock_phase.report_id = 1
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [mock_phase, None]
        
        # Mock collect_section_data
        mock_data = {"summary": "Test summary", "metrics": {"total_items": 100}}
        with patch.object(self.service, 'collect_section_data', return_value=mock_data):
            result = await self.service.generate_section(phase_id, section_name, user_id)
        
        # Verify section was created
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()
        
        # Verify section data was set
        created_section = self.mock_db.add.call_args[0][0]
        assert created_section.section_name == section_name
        assert created_section.section_content == mock_data
        assert created_section.status == 'generated'
    
    @pytest.mark.asyncio
    async def test_generate_section_existing_section(self):
        """Test generating an existing section"""
        phase_id = 1
        section_name = "executive_summary"
        user_id = 1
        
        # Mock phase lookup
        mock_phase = Mock()
        mock_phase.phase_id = phase_id
        mock_phase.cycle_id = 1
        mock_phase.report_id = 1
        
        # Mock existing section
        mock_section = Mock()
        mock_section.section_name = section_name
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [mock_phase, mock_section]
        
        # Mock collect_section_data
        mock_data = {"summary": "Updated summary"}
        with patch.object(self.service, 'collect_section_data', return_value=mock_data):
            result = await self.service.generate_section(phase_id, section_name, user_id)
        
        # Verify existing section was updated
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_called()
        
        # Verify section data was updated
        assert mock_section.section_content == mock_data
        assert mock_section.status == 'generated'
    
    @pytest.mark.asyncio
    async def test_generate_section_unknown_section(self):
        """Test generating an unknown section"""
        phase_id = 1
        section_name = "unknown_section"
        user_id = 1
        
        # Mock phase lookup
        mock_phase = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_phase
        
        with pytest.raises(ValueError, match="Unknown section: unknown_section"):
            await self.service.generate_section(phase_id, section_name, user_id)
    
    @pytest.mark.asyncio
    async def test_check_phase_completion_all_approved(self):
        """Test phase completion check when all sections are approved"""
        phase_id = 1
        
        # Mock sections - all approved
        mock_section1 = Mock()
        mock_section1.is_fully_approved.return_value = True
        mock_section2 = Mock()
        mock_section2.is_fully_approved.return_value = True
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_section1, mock_section2]
        
        # Mock generation and phase
        mock_generation = Mock()
        mock_phase = Mock()
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [mock_generation, mock_phase]
        
        result = await self.service.check_phase_completion(phase_id)
        
        # Verify completion was processed
        assert result == True
        assert mock_generation.all_approvals_received == True
        assert mock_generation.phase_completion_ready == True
        assert mock_phase.status == 'Complete'
        assert mock_phase.state == 'Complete'
    
    @pytest.mark.asyncio
    async def test_check_phase_completion_not_all_approved(self):
        """Test phase completion check when not all sections are approved"""
        phase_id = 1
        
        # Mock sections - not all approved
        mock_section1 = Mock()
        mock_section1.is_fully_approved.return_value = True
        mock_section2 = Mock()
        mock_section2.is_fully_approved.return_value = False
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_section1, mock_section2]
        
        result = await self.service.check_phase_completion(phase_id)
        
        # Verify completion was not processed
        assert result == False
        self.mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_final_report_success(self):
        """Test final report generation when all sections are approved"""
        phase_id = 1
        
        # Mock sections - all approved
        mock_section1 = Mock()
        mock_section1.is_fully_approved.return_value = True
        mock_section2 = Mock()
        mock_section2.is_fully_approved.return_value = True
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_section1, mock_section2]
        
        # Mock generation
        mock_generation = Mock()
        mock_generation.output_formats_generated = []
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_generation
        
        result = await self.service.generate_final_report(phase_id)
        
        # Verify PDF path was returned
        assert result.startswith("/reports/final_report_")
        assert result.endswith(".pdf")
        
        # Verify generation was updated
        assert 'pdf' in mock_generation.output_formats_generated
        assert mock_generation.phase_completion_ready == True
    
    @pytest.mark.asyncio
    async def test_generate_final_report_not_all_approved(self):
        """Test final report generation when not all sections are approved"""
        phase_id = 1
        
        # Mock sections - not all approved
        mock_section1 = Mock()
        mock_section1.is_fully_approved.return_value = True
        mock_section2 = Mock()
        mock_section2.is_fully_approved.return_value = False
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_section1, mock_section2]
        
        with pytest.raises(ValueError, match="All sections must be approved before final report generation"):
            await self.service.generate_final_report(phase_id)
    
    def test_get_sections_by_phase(self):
        """Test getting sections by phase"""
        phase_id = 1
        
        mock_sections = [Mock(), Mock()]
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_sections
        
        result = self.service.get_sections_by_phase(phase_id)
        
        assert result == mock_sections
    
    def test_get_generation_by_phase(self):
        """Test getting generation by phase"""
        phase_id = 1
        
        mock_generation = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_generation
        
        result = self.service.get_generation_by_phase(phase_id)
        
        assert result == mock_generation
    
    def test_get_approval_status(self):
        """Test getting approval status"""
        phase_id = 1
        
        # Mock sections with different approval states
        mock_section1 = Mock()
        mock_section1.id = 1
        mock_section1.section_name = "executive_summary"
        mock_section1.section_title = "Executive Summary"
        mock_section1.status = "generated"
        mock_section1.get_approval_status.return_value = "pending_tester"
        mock_section1.get_next_approver_level.return_value = "tester"
        mock_section1.is_fully_approved.return_value = False
        mock_section1.tester_approved = False
        mock_section1.report_owner_approved = False
        mock_section1.executive_approved = False
        
        mock_section2 = Mock()
        mock_section2.id = 2
        mock_section2.section_name = "strategic_approach"
        mock_section2.section_title = "Strategic Approach"
        mock_section2.status = "generated"
        mock_section2.get_approval_status.return_value = "fully_approved"
        mock_section2.get_next_approver_level.return_value = None
        mock_section2.is_fully_approved.return_value = True
        mock_section2.tester_approved = True
        mock_section2.report_owner_approved = True
        mock_section2.executive_approved = True
        
        with patch.object(self.service, 'get_sections_by_phase', return_value=[mock_section1, mock_section2]):
            result = self.service.get_approval_status(phase_id)
        
        assert result['total_sections'] == 2
        assert result['fully_approved'] == 1
        assert len(result['sections']) == 2
        assert result['sections'][0]['approval_status'] == 'pending_tester'
        assert result['sections'][1]['approval_status'] == 'fully_approved'


class TestApprovalWorkflowService:
    """Test cases for ApprovalWorkflowService"""
    
    def setup_method(self):
        """Setup test dependencies"""
        self.mock_db = Mock(spec=Session)
        self.service = ApprovalWorkflowService(self.mock_db)
    
    @pytest.mark.asyncio
    async def test_approve_section_success(self):
        """Test successful section approval"""
        section_id = 1
        approver_id = 1
        approval_level = "tester"
        notes = "Approved"
        
        # Mock section
        mock_section = Mock()
        mock_section.id = section_id
        mock_section.get_next_approver_level.return_value = approval_level
        mock_section.approve_section.return_value = True
        mock_section.is_fully_approved.return_value = False
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_section
        
        # Mock permission check
        with patch.object(self.service, 'can_approve_at_level', return_value=True):
            result = await self.service.approve_section(section_id, approver_id, approval_level, notes)
        
        assert result == mock_section
        mock_section.approve_section.assert_called_once_with(approver_id, approval_level, notes)
        self.mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_approve_section_unauthorized(self):
        """Test section approval when user is not authorized"""
        section_id = 1
        approver_id = 1
        approval_level = "tester"
        
        # Mock section
        mock_section = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_section
        
        # Mock permission check - unauthorized
        with patch.object(self.service, 'can_approve_at_level', return_value=False):
            with pytest.raises(ValueError, match="User not authorized to approve at tester level"):
                await self.service.approve_section(section_id, approver_id, approval_level)
    
    @pytest.mark.asyncio
    async def test_approve_section_wrong_level(self):
        """Test section approval at wrong level"""
        section_id = 1
        approver_id = 1
        approval_level = "executive"
        
        # Mock section
        mock_section = Mock()
        mock_section.get_next_approver_level.return_value = "tester"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_section
        
        # Mock permission check
        with patch.object(self.service, 'can_approve_at_level', return_value=True):
            with pytest.raises(ValueError, match="Expected approval level tester, got executive"):
                await self.service.approve_section(section_id, approver_id, approval_level)
    
    @pytest.mark.asyncio
    async def test_reject_section_success(self):
        """Test successful section rejection"""
        section_id = 1
        rejector_id = 1
        rejection_level = "tester"
        notes = "Needs revision"
        
        # Mock section
        mock_section = Mock()
        mock_section.id = section_id
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_section
        
        # Mock permission check
        with patch.object(self.service, 'can_approve_at_level', return_value=True):
            result = await self.service.reject_section(section_id, rejector_id, rejection_level, notes)
        
        assert result == mock_section
        assert mock_section.status == 'rejected'
        assert mock_section.updated_by == rejector_id
        assert mock_section.tester_notes == f"REJECTED: {notes}"
        self.mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_complete_phase_success(self):
        """Test successful phase completion"""
        phase_id = 1
        user_id = 1
        
        # Mock phase
        mock_phase = Mock()
        mock_phase.phase_id = phase_id
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_phase
        
        # Mock generation
        mock_generation = Mock()
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [mock_phase, mock_generation]
        
        # Mock check_phase_completion
        with patch.object(self.service, 'check_phase_completion', return_value=True):
            result = await self.service.complete_phase(phase_id, user_id)
        
        assert result == True
        assert mock_phase.status == 'Complete'
        assert mock_phase.state == 'Complete'
        assert mock_phase.completed_by == user_id
        assert mock_generation.all_approvals_received == True
        assert mock_generation.phase_completion_ready == True
        assert mock_generation.phase_completed_by == user_id
    
    @pytest.mark.asyncio
    async def test_complete_phase_not_ready(self):
        """Test phase completion when not ready"""
        phase_id = 1
        user_id = 1
        
        # Mock check_phase_completion
        with patch.object(self.service, 'check_phase_completion', return_value=False):
            with pytest.raises(ValueError, match="Cannot complete phase: Not all sections are fully approved"):
                await self.service.complete_phase(phase_id, user_id)
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals(self):
        """Test getting pending approvals for user"""
        user_id = 1
        
        # Mock user roles
        with patch.object(self.service, 'get_user_approval_roles', return_value=['tester', 'executive']):
            # Mock sections for tester role
            mock_tester_section = Mock()
            mock_tester_section.id = 1
            mock_tester_section.section_name = "executive_summary"
            mock_tester_section.section_title = "Executive Summary"
            mock_tester_section.phase_id = 1
            mock_tester_section.cycle_id = 1
            mock_tester_section.report_id = 1
            mock_tester_section.status = "generated"
            mock_tester_section.created_at = datetime.now()
            mock_tester_section.updated_at = datetime.now()
            
            # Mock sections for executive role
            mock_exec_section = Mock()
            mock_exec_section.id = 2
            mock_exec_section.section_name = "strategic_approach"
            mock_exec_section.section_title = "Strategic Approach"
            mock_exec_section.phase_id = 1
            mock_exec_section.cycle_id = 1
            mock_exec_section.report_id = 1
            mock_exec_section.status = "generated"
            mock_exec_section.created_at = datetime.now()
            mock_exec_section.updated_at = datetime.now()
            
            self.mock_db.query.return_value.filter.return_value.all.side_effect = [
                [mock_tester_section],  # tester pending
                [mock_exec_section]     # executive pending
            ]
            
            result = await self.service.get_pending_approvals(user_id)
        
        assert len(result) == 2
        assert result[0]['approval_level'] == 'tester'
        assert result[0]['section_name'] == 'executive_summary'
        assert result[1]['approval_level'] == 'executive'
        assert result[1]['section_name'] == 'strategic_approach'


if __name__ == "__main__":
    pytest.main([__file__])