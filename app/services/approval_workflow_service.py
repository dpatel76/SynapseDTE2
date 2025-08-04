"""
Approval Workflow Service
Manages the approval workflow for test report sections
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select

from app.models.test_report import TestReportSection, TestReportGeneration
from app.models.workflow import WorkflowPhase
from app.models.user import User
from app.models.rbac import UserRole, Role


class ApprovalWorkflowService:
    """Service for managing test report approval workflows"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def submit_for_approval(self, section_id: int, submitter_id: int) -> TestReportSection:
        """Submit a section for approval"""
        
        result = await self.db.execute(
            select(TestReportSection).where(TestReportSection.id == section_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            raise ValueError(f"Section {section_id} not found")
        
        # Check if user has permission to submit
        if not await self.can_submit_section(submitter_id, section):
            raise ValueError("User not authorized to submit this section")
        
        # Update section status
        section.status = 'pending_approval'
        section.updated_by = submitter_id
        
        await self.db.commit()
        
        # Send notifications to approvers
        await self.send_approval_notifications(section)
        
        return section
    
    async def approve_section(self, section_id: int, approver_id: int, approval_level: str, notes: str = None) -> TestReportSection:
        """Approve a section at a specific level"""
        
        result = await self.db.execute(
            select(TestReportSection).where(TestReportSection.id == section_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            raise ValueError(f"Section {section_id} not found")
        
        # Check if user has permission to approve at this level
        if not await self.can_approve_at_level(approver_id, approval_level, section):
            raise ValueError(f"User not authorized to approve at {approval_level} level")
        
        # Check if this is the next approval level needed
        current_level = section.get_next_approver_level()
        if current_level != approval_level:
            raise ValueError(f"Expected approval level {current_level}, got {approval_level}")
        
        # Apply the approval
        success = section.approve_section(approver_id, approval_level, notes)
        if not success:
            raise ValueError(f"Failed to approve section at {approval_level} level")
        
        await self.db.commit()
        
        # Send notifications
        await self.send_approval_confirmation(section, approver_id, approval_level)
        
        # If not fully approved, notify next approver
        if not section.is_fully_approved():
            await self.send_next_level_notification(section)
        else:
            # Section is fully approved, check phase completion
            await self.check_phase_completion(section.phase_id)
        
        return section
    
    async def reject_section(self, section_id: int, rejector_id: int, rejection_level: str, notes: str) -> TestReportSection:
        """Reject a section at a specific level"""
        
        result = await self.db.execute(
            select(TestReportSection).where(TestReportSection.id == section_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            raise ValueError(f"Section {section_id} not found")
        
        # Check if user has permission to reject at this level
        if not await self.can_approve_at_level(rejector_id, rejection_level, section):
            raise ValueError(f"User not authorized to reject at {rejection_level} level")
        
        # Reset approvals and update status
        section.status = 'rejected'
        section.updated_by = rejector_id
        
        # Clear all approvals
        section.tester_approved = False
        section.tester_approved_by = None
        section.tester_approved_at = None
        section.tester_notes = None
        
        section.report_owner_approved = False
        section.report_owner_approved_by = None
        section.report_owner_approved_at = None
        section.report_owner_notes = None
        
        section.executive_approved = False
        section.executive_approved_by = None
        section.executive_approved_at = None
        section.executive_notes = None
        
        # Add rejection notes based on level
        if rejection_level == 'tester':
            section.tester_notes = f"REJECTED: {notes}"
        elif rejection_level == 'report_owner':
            section.report_owner_notes = f"REJECTED: {notes}"
        elif rejection_level == 'executive':
            section.executive_notes = f"REJECTED: {notes}"
        
        await self.db.commit()
        
        # Send rejection notifications
        await self.send_rejection_notification(section, rejector_id, rejection_level, notes)
        
        return section
    
    async def request_revision(self, section_id: int, requester_id: int, revision_level: str, notes: str) -> TestReportSection:
        """Request revision of a section"""
        
        result = await self.db.execute(
            select(TestReportSection).where(TestReportSection.id == section_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            raise ValueError(f"Section {section_id} not found")
        
        # Check if user has permission to request revision
        if not await self.can_approve_at_level(requester_id, revision_level, section):
            raise ValueError(f"User not authorized to request revision at {revision_level} level")
        
        # Update section status
        section.status = 'revision_requested'
        section.updated_by = requester_id
        
        # Add revision notes
        revision_note = f"REVISION REQUESTED: {notes}"
        if revision_level == 'tester':
            section.tester_notes = revision_note
        elif revision_level == 'report_owner':
            section.report_owner_notes = revision_note
        elif revision_level == 'executive':
            section.executive_notes = revision_note
        
        await self.db.commit()
        
        # Send revision request notifications
        await self.send_revision_request_notification(section, requester_id, revision_level, notes)
        
        return section
    
    async def get_pending_approvals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all sections pending approval by a user"""
        
        # Get user's roles
        user_roles = await self.get_user_approval_roles(user_id)
        
        pending_sections = []
        
        # Get sections where user can approve
        for role in user_roles:
            if role == 'tester':
                sections_result = await self.db.execute(
                    select(TestReportSection).where(
                        and_(
                            TestReportSection.status.in_(['pending_approval', 'generated']),
                            TestReportSection.tester_approved == False
                        )
                    )
                )
                sections = sections_result.scalars().all()
            elif role == 'report_owner':
                sections_result = await self.db.execute(
                    select(TestReportSection).where(
                        and_(
                            TestReportSection.status.in_(['pending_approval', 'generated']),
                            TestReportSection.tester_approved == True,
                            TestReportSection.report_owner_approved == False
                        )
                    )
                )
                sections = sections_result.scalars().all()
            elif role == 'executive':
                sections_result = await self.db.execute(
                    select(TestReportSection).where(
                        and_(
                            TestReportSection.status.in_(['pending_approval', 'generated']),
                            TestReportSection.tester_approved == True,
                            TestReportSection.report_owner_approved == True,
                            TestReportSection.executive_approved == False
                        )
                    )
                )
                sections = sections_result.scalars().all()
            else:
                continue
            
            for section in sections:
                pending_sections.append({
                    'section_id': section.id,
                    'section_name': section.section_name,
                    'section_title': section.section_title,
                    'phase_id': section.phase_id,
                    'cycle_id': section.cycle_id,
                    'report_id': section.report_id,
                    'status': section.status,
                    'approval_level': role,
                    'created_at': section.created_at,
                    'last_updated': section.updated_at
                })
        
        return pending_sections
    
    async def get_approval_history(self, section_id: int) -> List[Dict[str, Any]]:
        """Get approval history for a section"""
        
        result = await self.db.execute(
            select(TestReportSection).where(TestReportSection.id == section_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            raise ValueError(f"Section {section_id} not found")
        
        history = []
        
        # Tester approval
        if section.tester_approved:
            approver_result = await self.db.execute(
                select(User).where(User.user_id == section.tester_approved_by)
            )
            approver = approver_result.scalar_one_or_none()
            history.append({
                'level': 'tester',
                'action': 'approved',
                'approver': f"{approver.first_name} {approver.last_name}" if approver else 'Unknown',
                'timestamp': section.tester_approved_at,
                'notes': section.tester_notes
            })
        
        # Report owner approval
        if section.report_owner_approved:
            approver_result = await self.db.execute(
                select(User).where(User.user_id == section.report_owner_approved_by)
            )
            approver = approver_result.scalar_one_or_none()
            history.append({
                'level': 'report_owner',
                'action': 'approved',
                'approver': f"{approver.first_name} {approver.last_name}" if approver else 'Unknown',
                'timestamp': section.report_owner_approved_at,
                'notes': section.report_owner_notes
            })
        
        # Executive approval
        if section.executive_approved:
            approver_result = await self.db.execute(
                select(User).where(User.user_id == section.executive_approved_by)
            )
            approver = approver_result.scalar_one_or_none()
            history.append({
                'level': 'executive',
                'action': 'approved',
                'approver': f"{approver.first_name} {approver.last_name}" if approver else 'Unknown',
                'timestamp': section.executive_approved_at,
                'notes': section.executive_notes
            })
        
        return sorted(history, key=lambda x: x['timestamp'] or datetime.min)
    
    async def get_approval_status_summary(self, phase_id: int) -> Dict[str, Any]:
        """Get approval status summary for all sections in a phase"""
        
        result = await self.db.execute(
            select(TestReportSection).where(
                TestReportSection.phase_id == phase_id
            ).order_by(TestReportSection.section_order)
        )
        sections = result.scalars().all()
        
        summary = {
            'total_sections': len(sections),
            'pending_tester': 0,
            'pending_report_owner': 0,
            'pending_executive': 0,
            'fully_approved': 0,
            'rejected': 0,
            'revision_requested': 0,
            'sections': []
        }
        
        for section in sections:
            section_status = {
                'id': section.id,
                'name': section.section_name,
                'title': section.section_title,
                'status': section.status,
                'approval_status': section.get_approval_status(),
                'next_approver': section.get_next_approver_level(),
                'is_fully_approved': section.is_fully_approved()
            }
            
            summary['sections'].append(section_status)
            
            # Count status
            if section.status == 'rejected':
                summary['rejected'] += 1
            elif section.status == 'revision_requested':
                summary['revision_requested'] += 1
            elif section.is_fully_approved():
                summary['fully_approved'] += 1
            elif not section.tester_approved:
                summary['pending_tester'] += 1
            elif not section.report_owner_approved:
                summary['pending_report_owner'] += 1
            elif not section.executive_approved:
                summary['pending_executive'] += 1
        
        return summary
    
    async def bulk_approve_sections(self, section_ids: List[int], approver_id: int, approval_level: str, notes: str = None) -> List[TestReportSection]:
        """Bulk approve multiple sections"""
        
        approved_sections = []
        
        for section_id in section_ids:
            try:
                section = await self.approve_section(section_id, approver_id, approval_level, notes)
                approved_sections.append(section)
            except Exception as e:
                # Log error but continue with other sections
                print(f"Error approving section {section_id}: {e}")
                continue
        
        return approved_sections
    
    # Permission checking methods
    async def can_submit_section(self, user_id: int, section: TestReportSection) -> bool:
        """Check if user can submit a section for approval"""
        
        # Check if user is the section creator or has appropriate role
        if section.created_by == user_id:
            return True
        
        # Check if user has tester role
        user_roles = await self.get_user_approval_roles(user_id)
        return 'tester' in user_roles
    
    async def can_approve_at_level(self, user_id: int, approval_level: str, section: TestReportSection) -> bool:
        """Check if user can approve at a specific level"""
        
        user_roles = await self.get_user_approval_roles(user_id)
        
        # Check specific role requirements
        if approval_level == 'tester':
            return 'tester' in user_roles
        elif approval_level == 'report_owner':
            return 'report_owner' in user_roles
        elif approval_level == 'executive':
            return 'executive' in user_roles
        
        return False
    
    async def get_user_approval_roles(self, user_id: int) -> List[str]:
        """Get user's approval roles"""
        
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return []
        
        roles = []
        
        # Check user's direct role
        if user.role in ['Tester', 'Test Executive']:
            roles.append('tester')
        
        if user.role in ['Report Owner', 'Report Owner Executive']:
            roles.append('report_owner')
        
        if user.role in ['Executive', 'Test Executive', 'Report Owner Executive', 'Data Executive']:
            roles.append('executive')
        
        return roles
    
    # Phase completion checking
    async def check_phase_completion(self, phase_id: int) -> bool:
        """Check if phase can be completed based on section approvals"""
        
        sections_result = await self.db.execute(
            select(TestReportSection).where(
                TestReportSection.phase_id == phase_id
            )
        )
        sections = sections_result.scalars().all()
        
        # Check if all sections are fully approved
        all_approved = all(section.is_fully_approved() for section in sections)
        
        if all_approved:
            # Update generation record
            generation_result = await self.db.execute(
                select(TestReportGeneration).where(
                    TestReportGeneration.phase_id == phase_id
                )
            )
            generation = generation_result.scalar_one_or_none()
            
            if generation:
                generation.all_approvals_received = True
                generation.phase_completion_ready = True
                await self.db.commit()
            
            # Update phase status
            phase_result = await self.db.execute(
                select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
            )
            phase = phase_result.scalar_one_or_none()
            if phase:
                phase.status = 'Complete'
                phase.state = 'Complete'
                phase.actual_end_date = datetime.utcnow()
                await self.db.commit()
        
        return all_approved
    
    async def complete_phase(self, phase_id: int, user_id: int) -> bool:
        """Complete the test report phase if all requirements are met"""
        
        # Check if phase can be completed
        can_complete = await self.check_phase_completion(phase_id)
        
        if not can_complete:
            raise ValueError("Cannot complete phase: Not all sections are fully approved")
        
        # Get phase
        phase_result = await self.db.execute(
            select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        )
        phase = phase_result.scalar_one_or_none()
        if not phase:
            raise ValueError(f"Phase {phase_id} not found")
        
        # Mark phase as completed
        phase.status = 'Complete'
        phase.state = 'Complete'
        phase.actual_end_date = datetime.utcnow()
        phase.completed_by = user_id
        
        # Update generation record
        generation_result = await self.db.execute(
            select(TestReportGeneration).where(
                TestReportGeneration.phase_id == phase_id
            )
        )
        generation = generation_result.scalar_one_or_none()
        
        if generation:
            generation.all_approvals_received = True
            generation.phase_completion_ready = True
            generation.phase_completed_at = datetime.utcnow()
            generation.phase_completed_by = user_id
        
        await self.db.commit()
        
        return True
    
    # Notification methods (placeholders)
    async def send_approval_notifications(self, section: TestReportSection):
        """Send notifications to approvers"""
        # Implementation would integrate with notification service
        pass
    
    async def send_approval_confirmation(self, section: TestReportSection, approver_id: int, approval_level: str):
        """Send approval confirmation"""
        # Implementation would integrate with notification service
        pass
    
    async def send_next_level_notification(self, section: TestReportSection):
        """Send notification to next level approver"""
        # Implementation would integrate with notification service
        pass
    
    async def send_rejection_notification(self, section: TestReportSection, rejector_id: int, rejection_level: str, notes: str):
        """Send rejection notification"""
        # Implementation would integrate with notification service
        pass
    
    async def send_revision_request_notification(self, section: TestReportSection, requester_id: int, revision_level: str, notes: str):
        """Send revision request notification"""
        # Implementation would integrate with notification service
        pass
    
    # Utility methods
    async def get_approval_metrics(self, phase_id: int) -> Dict[str, Any]:
        """Get approval metrics for a phase"""
        
        sections_result = await self.db.execute(
            select(TestReportSection).where(
                TestReportSection.phase_id == phase_id
            )
        )
        sections = sections_result.scalars().all()
        
        if not sections:
            return {
                'total_sections': 0,
                'completion_rate': 0.0,
                'avg_approval_time': 0.0,
                'bottlenecks': []
            }
        
        total_sections = len(sections)
        approved_sections = sum(1 for s in sections if s.is_fully_approved())
        
        # Calculate average approval time (placeholder)
        avg_approval_time = 24.5  # hours
        
        # Identify bottlenecks
        bottlenecks = []
        pending_tester = sum(1 for s in sections if not s.tester_approved)
        pending_owner = sum(1 for s in sections if s.tester_approved and not s.report_owner_approved)
        pending_exec = sum(1 for s in sections if s.report_owner_approved and not s.executive_approved)
        
        if pending_tester > 0:
            bottlenecks.append(f"{pending_tester} sections pending tester approval")
        if pending_owner > 0:
            bottlenecks.append(f"{pending_owner} sections pending report owner approval")
        if pending_exec > 0:
            bottlenecks.append(f"{pending_exec} sections pending executive approval")
        
        return {
            'total_sections': total_sections,
            'approved_sections': approved_sections,
            'completion_rate': (approved_sections / total_sections) * 100,
            'avg_approval_time': avg_approval_time,
            'bottlenecks': bottlenecks
        }