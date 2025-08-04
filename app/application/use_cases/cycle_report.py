from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime

from app.models.user import User
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.test_cycle import TestCycle
from app.models.workflow import WorkflowPhase
# Observation enhanced models removed - use observation_management models
from app.models.audit import AuditLog
from app.core.auth import UserRoles
from app.application.dtos.cycle_report import (
    CycleReportDTO, CycleReportDetailDTO, TesterReportFilterDTO,
    DataOwnerReportFilterDTO, CycleReportWorkflowStatusDTO,
    CycleReportActivityDTO, CycleReportObservationDTO,
    CycleReportUpdateDTO, CycleReportBulkAssignDTO,
    CycleReportMetricsDTO
)


class CycleReportUseCase:
    """Use cases for cycle report management"""
    
    @staticmethod
    async def get_reports_by_tester(
        filter_dto: TesterReportFilterDTO,
        current_user: User,
        db: AsyncSession
    ) -> List[CycleReportDTO]:
        """Get all reports assigned to a tester"""
        # Check permissions
        if current_user.user_id != filter_dto.tester_id and current_user.role not in [
            UserRoles.TEST_EXECUTIVE, UserRoles.REPORT_OWNER_EXECUTIVE
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these reports"
            )
        
        # Build query with eager loading
        stmt = (
            select(CycleReport)
            .options(
                selectinload(CycleReport.report).selectinload(Report.lob),
                selectinload(CycleReport.cycle),
                selectinload(CycleReport.tester),
                selectinload(CycleReport.workflow_phases),
                selectinload(CycleReport.observations)
            )
            .where(CycleReport.tester_id == filter_dto.tester_id)
        )
        
        # Apply filters
        if filter_dto.status:
            stmt = stmt.where(CycleReport.status.in_(filter_dto.status))
        else:
            stmt = stmt.where(CycleReport.status.in_(['Not Started', 'In Progress', 'Complete']))
        
        if filter_dto.cycle_id:
            stmt = stmt.where(CycleReport.cycle_id == filter_dto.cycle_id)
        
        if filter_dto.lob_id:
            stmt = stmt.join(Report).where(Report.lob_id == filter_dto.lob_id)
        
        stmt = stmt.order_by(CycleReport.created_at.desc())
        
        result = await db.execute(stmt)
        cycle_reports = result.scalars().all()
        
        # Transform to DTOs
        dtos = []
        for cr in cycle_reports:
            dto = CycleReportDTO.model_validate(cr)
            
            # Add related data
            if cr.report:
                dto.report_name = cr.report.report_name
                if cr.report.lob:
                    dto.lob_name = cr.report.lob.lob_name
            
            if cr.cycle:
                dto.cycle_name = cr.cycle.cycle_name
            
            if cr.tester:
                dto.tester_name = f"{cr.tester.first_name} {cr.tester.last_name}"
            
            # Calculate progress
            if cr.workflow_phases:
                completed = len([p for p in cr.workflow_phases if p.status == 'Complete'])
                dto.completed_phases = completed
                dto.overall_progress = (completed / dto.total_phases) * 100
                
                # Get current phase
                incomplete = [p for p in cr.workflow_phases if p.status != 'Complete']
                if incomplete:
                    current = max(incomplete, key=lambda p: p.phase_id)
                    dto.current_phase = current.phase_name
            
            # Count issues
            if cr.observations:
                dto.issue_count = len(cr.observations)
            
            dtos.append(dto)
        
        return dtos
    
    @staticmethod
    async def get_reports_by_data_owner(
        filter_dto: DataOwnerReportFilterDTO,
        current_user: User,
        db: AsyncSession
    ) -> List[CycleReportDTO]:
        """Get all reports assigned to a data owner"""
        # Check permissions
        if current_user.user_id != filter_dto.data_owner_id and current_user.role not in [
            UserRoles.TEST_EXECUTIVE, UserRoles.DATA_EXECUTIVE
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these reports"
            )
        
        # Build query
        stmt = (
            select(CycleReport)
            .options(
                selectinload(CycleReport.report).selectinload(Report.lob),
                selectinload(CycleReport.cycle),
                selectinload(CycleReport.data_owner),
                selectinload(CycleReport.workflow_phases)
            )
            .join(TestCycle)
            .where(CycleReport.data_owner_id == filter_dto.data_owner_id)
        )
        
        # For non-Test Executive users, only show reports from active cycles
        if current_user.role != UserRoles.TEST_EXECUTIVE:
            stmt = stmt.where(TestCycle.status == "Active")
        
        # Apply filters
        if filter_dto.status:
            stmt = stmt.where(CycleReport.status.in_(filter_dto.status))
        
        if filter_dto.cycle_id:
            stmt = stmt.where(CycleReport.cycle_id == filter_dto.cycle_id)
        
        if filter_dto.lob_id:
            stmt = stmt.join(Report).where(Report.lob_id == filter_dto.lob_id)
        
        stmt = stmt.order_by(CycleReport.created_at.desc())
        
        result = await db.execute(stmt)
        cycle_reports = result.scalars().all()
        
        # Transform to DTOs
        dtos = []
        for cr in cycle_reports:
            dto = CycleReportDTO.model_validate(cr)
            
            # Add related data
            if cr.report:
                dto.report_name = cr.report.report_name
                if cr.report.lob:
                    dto.lob_name = cr.report.lob.lob_name
            
            if cr.cycle:
                dto.cycle_name = cr.cycle.cycle_name
            
            if cr.data_owner:
                dto.data_owner_name = f"{cr.data_owner.first_name} {cr.data_owner.last_name}"
            
            # Get current phase focused on data owner phases
            if cr.workflow_phases:
                data_owner_phases = ['Data Provider Identification', 'Request for Information']
                relevant_phases = [p for p in cr.workflow_phases if p.phase_name in data_owner_phases]
                if relevant_phases:
                    current = max(relevant_phases, key=lambda p: p.phase_id)
                    dto.current_phase = current.phase_name
            
            dtos.append(dto)
        
        return dtos
    
    @staticmethod
    async def get_cycle_report_detail(
        cycle_report_id: int,
        current_user: User,
        db: AsyncSession
    ) -> CycleReportDetailDTO:
        """Get detailed information about a cycle report"""
        # Get cycle report with all relationships
        stmt = (
            select(CycleReport)
            .options(
                selectinload(CycleReport.report).selectinload(Report.lob),
                selectinload(CycleReport.cycle),
                selectinload(CycleReport.tester),
                selectinload(CycleReport.data_owner),
                selectinload(CycleReport.workflow_phases),
                selectinload(CycleReport.observations)
            )
            .where(CycleReport.cycle_report_id == cycle_report_id)
        )
        
        result = await db.execute(stmt)
        cycle_report = result.scalar_one_or_none()
        
        if not cycle_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cycle report not found"
            )
        
        # Check permissions
        can_view = (
            current_user.user_id == cycle_report.tester_id or
            current_user.user_id == cycle_report.data_owner_id or
            current_user.role in [UserRoles.TEST_EXECUTIVE, UserRoles.REPORT_OWNER_EXECUTIVE, UserRoles.DATA_EXECUTIVE]
        )
        
        if not can_view:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this report"
            )
        
        # Create detailed DTO
        dto = CycleReportDetailDTO.model_validate(cycle_report)
        
        # Add related data
        if cycle_report.report:
            dto.report_name = cycle_report.report.report_name
            if cycle_report.report.lob:
                dto.lob_name = cycle_report.report.lob.lob_name
        
        if cycle_report.cycle:
            dto.cycle_name = cycle_report.cycle.cycle_name
        
        if cycle_report.tester:
            dto.tester_name = f"{cycle_report.tester.first_name} {cycle_report.tester.last_name}"
        
        if cycle_report.data_owner:
            dto.data_owner_name = f"{cycle_report.data_owner.first_name} {cycle_report.data_owner.last_name}"
        
        # Add workflow phases
        if cycle_report.workflow_phases:
            dto.workflow_phases = [
                {
                    "phase_id": p.phase_id,
                    "phase_name": p.phase_name,
                    "status": p.status,
                    "started_at": p.started_at.isoformat() if p.started_at else None,
                    "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                    "assigned_to": p.assigned_to
                }
                for p in sorted(cycle_report.workflow_phases, key=lambda x: x.phase_id)
            ]
            
            # Calculate progress
            completed = len([p for p in cycle_report.workflow_phases if p.status == 'Complete'])
            dto.completed_phases = completed
            dto.overall_progress = (completed / dto.total_phases) * 100
        
        # Add observations
        if cycle_report.observations:
            dto.observations = [
                {
                    "observation_id": o.observation_id,
                    "type": o.observation_type,
                    "title": o.title,
                    "severity": o.severity,
                    "status": o.status
                }
                for o in cycle_report.observations
            ]
            dto.issue_count = len(cycle_report.observations)
        
        return dto
    
    @staticmethod
    async def get_workflow_status(
        cycle_report_id: int,
        current_user: User,
        db: AsyncSession
    ) -> CycleReportWorkflowStatusDTO:
        """Get workflow status for a cycle report"""
        # Get cycle report
        stmt = (
            select(CycleReport)
            .options(
                selectinload(CycleReport.report),
                selectinload(CycleReport.workflow_phases)
            )
            .where(CycleReport.cycle_report_id == cycle_report_id)
        )
        
        result = await db.execute(stmt)
        cycle_report = result.scalar_one_or_none()
        
        if not cycle_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cycle report not found"
            )
        
        # Create workflow status DTO
        phase_statuses = {}
        phase_progress = {}
        workflow_phases = []
        current_phase = "Planning"
        is_blocked = False
        blocked_reason = None
        
        if cycle_report.workflow_phases:
            for phase in sorted(cycle_report.workflow_phases, key=lambda x: x.phase_id):
                phase_statuses[phase.phase_name] = phase.status
                
                # Calculate phase progress
                if phase.status == 'Complete':
                    phase_progress[phase.phase_name] = 100.0
                elif phase.status == 'In Progress':
                    phase_progress[phase.phase_name] = 50.0
                else:
                    phase_progress[phase.phase_name] = 0.0
                
                workflow_phases.append({
                    "phase_id": phase.phase_id,
                    "phase_name": phase.phase_name,
                    "status": phase.status,
                    "started_at": phase.started_at,
                    "completed_at": phase.completed_at
                })
                
                # Determine current phase
                if phase.status == 'In Progress':
                    current_phase = phase.phase_name
                
                # Check for blocks
                if phase.status == 'Blocked':
                    is_blocked = True
                    blocked_reason = f"Phase {phase.phase_name} is blocked"
        
        # Calculate overall progress
        total_phases = 7
        completed_phases = len([p for p in phase_statuses.values() if p == 'Complete'])
        overall_progress = (completed_phases / total_phases) * 100
        
        return CycleReportWorkflowStatusDTO(
            cycle_report_id=cycle_report_id,
            report_name=cycle_report.report.report_name if cycle_report.report else "Unknown",
            workflow_phases=workflow_phases,
            overall_progress=overall_progress,
            current_phase=current_phase,
            phase_statuses=phase_statuses,
            phase_progress=phase_progress,
            is_blocked=is_blocked,
            blocked_reason=blocked_reason
        )
    
    @staticmethod
    async def get_recent_activities(
        cycle_report_id: int,
        limit: int,
        current_user: User,
        db: AsyncSession
    ) -> List[CycleReportActivityDTO]:
        """Get recent activities for a cycle report"""
        # Check permissions by getting the cycle report first
        cr_stmt = select(CycleReport).where(CycleReport.cycle_report_id == cycle_report_id)
        cr_result = await db.execute(cr_stmt)
        cycle_report = cr_result.scalar_one_or_none()
        
        if not cycle_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cycle report not found"
            )
        
        # Get audit logs
        stmt = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == 'cycle_report',
                    AuditLog.entity_id == str(cycle_report_id)
                )
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        activities = result.scalars().all()
        
        # Transform to DTOs
        activity_dtos = []
        for activity in activities:
            # Parse change details to extract phase info
            phase_name = "General"
            if activity.changes:
                if "phase" in activity.changes:
                    phase_name = activity.changes.get("phase", "General")
            
            dto = CycleReportActivityDTO(
                activity_id=activity.audit_id,
                cycle_report_id=cycle_report_id,
                phase_name=phase_name,
                action=activity.action,
                details=activity.changes.get("details") if activity.changes else None,
                user_name=f"User {activity.user_id}",  # Would need to join with User table
                created_at=activity.created_at
            )
            activity_dtos.append(dto)
        
        return activity_dtos
    
    @staticmethod
    async def get_observations(
        cycle_report_id: int,
        current_user: User,
        db: AsyncSession
    ) -> List[CycleReportObservationDTO]:
        """Get observations for a cycle report"""
        # Get observations
        stmt = (
            select(Observation)
            .where(Observation.cycle_report_id == cycle_report_id)
            .order_by(Observation.created_at.desc())
        )
        
        result = await db.execute(stmt)
        observations = result.scalars().all()
        
        # Transform to DTOs
        observation_dtos = []
        for obs in observations:
            dto = CycleReportObservationDTO(
                observation_id=obs.observation_id,
                cycle_report_id=obs.cycle_report_id,
                observation_type=obs.observation_type,
                title=obs.title,
                description=obs.description,
                severity=obs.severity,
                status=obs.status,
                remediation_status=obs.remediation_status,
                created_by_name=f"User {obs.created_by}",  # Would need to join with User table
                created_at=obs.created_at,
                updated_at=obs.updated_at
            )
            observation_dtos.append(dto)
        
        return observation_dtos
    
    @staticmethod
    async def update_cycle_report(
        cycle_report_id: int,
        update_dto: CycleReportUpdateDTO,
        current_user: User,
        db: AsyncSession
    ) -> CycleReportDTO:
        """Update a cycle report"""
        # Check permissions
        if current_user.role not in [UserRoles.TEST_EXECUTIVE, UserRoles.REPORT_OWNER_EXECUTIVE]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update cycle reports"
            )
        
        # Get cycle report
        stmt = (
            select(CycleReport)
            .options(
                selectinload(CycleReport.report).selectinload(Report.lob),
                selectinload(CycleReport.cycle),
                selectinload(CycleReport.tester),
                selectinload(CycleReport.data_owner)
            )
            .where(CycleReport.cycle_report_id == cycle_report_id)
        )
        
        result = await db.execute(stmt)
        cycle_report = result.scalar_one_or_none()
        
        if not cycle_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cycle report not found"
            )
        
        # Update fields
        update_data = update_dto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cycle_report, field, value)
        
        # Update timestamps
        cycle_report.updated_at = datetime.utcnow()
        if update_dto.tester_id and not cycle_report.assigned_at:
            cycle_report.assigned_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(cycle_report)
        
        # Return updated DTO
        dto = CycleReportDTO.model_validate(cycle_report)
        
        # Add related data
        if cycle_report.report:
            dto.report_name = cycle_report.report.report_name
            if cycle_report.report.lob:
                dto.lob_name = cycle_report.report.lob.lob_name
        
        if cycle_report.cycle:
            dto.cycle_name = cycle_report.cycle.cycle_name
        
        if cycle_report.tester:
            dto.tester_name = f"{cycle_report.tester.first_name} {cycle_report.tester.last_name}"
        
        if cycle_report.data_owner:
            dto.data_owner_name = f"{cycle_report.data_owner.first_name} {cycle_report.data_owner.last_name}"
        
        return dto
    
    @staticmethod
    async def bulk_assign_reports(
        bulk_dto: CycleReportBulkAssignDTO,
        current_user: User,
        db: AsyncSession
    ) -> dict:
        """Bulk assign cycle reports to testers or data owners"""
        # Check permissions
        if current_user.role not in [UserRoles.TEST_EXECUTIVE]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to bulk assign reports"
            )
        
        # Get cycle reports
        stmt = select(CycleReport).where(CycleReport.cycle_report_id.in_(bulk_dto.cycle_report_ids))
        result = await db.execute(stmt)
        cycle_reports = result.scalars().all()
        
        if not cycle_reports:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No cycle reports found"
            )
        
        # Update assignments
        updated_count = 0
        for cr in cycle_reports:
            if bulk_dto.tester_id:
                cr.tester_id = bulk_dto.tester_id
                if not cr.assigned_at:
                    cr.assigned_at = datetime.utcnow()
            
            if bulk_dto.data_owner_id:
                cr.data_owner_id = bulk_dto.data_owner_id
            
            cr.updated_at = datetime.utcnow()
            updated_count += 1
        
        await db.commit()
        
        return {
            "message": f"Successfully updated {updated_count} cycle reports",
            "updated_count": updated_count
        }
    
    @staticmethod
    async def get_cycle_report_metrics(
        cycle_id: Optional[int],
        current_user: User,
        db: AsyncSession
    ) -> CycleReportMetricsDTO:
        """Get metrics for cycle reports"""
        # Base query
        base_stmt = select(CycleReport).options(selectinload(CycleReport.workflow_phases))
        
        if cycle_id:
            base_stmt = base_stmt.where(CycleReport.cycle_id == cycle_id)
        
        result = await db.execute(base_stmt)
        cycle_reports = result.scalars().all()
        
        # Calculate metrics
        total_reports = len(cycle_reports)
        by_status = {}
        by_phase = {}
        total_progress = 0
        overdue_count = 0
        at_risk_count = 0
        on_track_count = 0
        
        for cr in cycle_reports:
            # Count by status
            by_status[cr.status] = by_status.get(cr.status, 0) + 1
            
            # Calculate progress and phase counts
            if cr.workflow_phases:
                completed_phases = 0
                for phase in cr.workflow_phases:
                    if phase.status == 'Complete':
                        completed_phases += 1
                    
                    # Count current phases
                    if phase.status == 'In Progress':
                        by_phase[phase.phase_name] = by_phase.get(phase.phase_name, 0) + 1
                
                progress = (completed_phases / 7) * 100
                total_progress += progress
                
                # Categorize by risk
                # This is simplified - real logic would check against SLAs
                if progress < 30:
                    at_risk_count += 1
                elif progress < 70:
                    on_track_count += 1
                else:
                    on_track_count += 1
        
        average_progress = total_progress / total_reports if total_reports > 0 else 0
        
        return CycleReportMetricsDTO(
            total_reports=total_reports,
            by_status=by_status,
            by_phase=by_phase,
            average_progress=average_progress,
            overdue_count=overdue_count,
            at_risk_count=at_risk_count,
            on_track_count=on_track_count
        )