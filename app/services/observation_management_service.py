"""
Observation Management Service
Handles observation group management, review, and approval workflow
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc

# Observation enhanced models removed - use observation_management models
from app.models.observation_management import (
    ObservationRecord, Observation, ObservationRatingEnum, ObservationApprovalStatusEnum,
    ObservationRecordStatus, SeverityLevel, IssueType, ReviewDecision, ResolutionStatus
)
from app.models.user import User
from app.models.report_attribute import ReportAttribute
from app.models.lob import LOB
from app.models.workflow import WorkflowPhase

logger = logging.getLogger(__name__)


class ObservationManagementService:
    """Service for managing observation groups and individual observations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================
    # Observation Group Management
    # ============================================
    
    async def get_observation_groups(
        self,
        phase_id: Optional[int] = None,
        cycle_id: Optional[int] = None,
        report_id: Optional[int] = None,
        status: Optional[str] = None,
        severity_level: Optional[str] = None,
        assigned_to: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get observation groups with filtering and pagination
        
        Args:
            phase_id: Filter by phase ID
            cycle_id: Filter by cycle ID
            report_id: Filter by report ID
            status: Filter by status
            severity_level: Filter by severity level
            assigned_to: Filter by assigned user (tester or report owner)
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Paginated observation groups with metadata
        """
        try:
            query = self.db.query(ObservationRecord).options(
                joinedload(ObservationRecord.attribute),
                joinedload(ObservationRecord.lob),
                joinedload(ObservationRecord.detector),
                joinedload(ObservationRecord.tester_reviewer),
                joinedload(ObservationRecord.report_owner_approver)
            )
            
            # Apply filters
            if phase_id:
                query = query.filter(ObservationRecord.phase_id == phase_id)
            
            if cycle_id:
                query = query.filter(ObservationRecord.cycle_id == cycle_id)
            
            if report_id:
                query = query.filter(ObservationRecord.report_id == report_id)
            
            if status:
                query = query.filter(ObservationRecord.status == status)
            
            if severity_level:
                query = query.filter(ObservationRecord.severity_level == severity_level)
            
            if assigned_to:
                query = query.filter(
                    or_(
                        ObservationRecord.tester_reviewed_by == assigned_to,
                        ObservationRecord.report_owner_approved_by == assigned_to
                    )
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            groups = query.order_by(desc(ObservationRecord.created_at)).offset(offset).limit(page_size).all()
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "groups": [await self._serialize_observation_group(group) for group in groups],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting observation groups: {str(e)}")
            raise
    
    async def get_observation_group_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get observation group by ID with all related data"""
        try:
            group = self.db.query(ObservationRecord).options(
                joinedload(ObservationRecord.attribute),
                joinedload(ObservationRecord.lob),
                joinedload(ObservationRecord.detector),
                joinedload(ObservationRecord.tester_reviewer),
                joinedload(ObservationRecord.report_owner_approver),
                joinedload(ObservationRecord.observations)
            ).filter(ObservationRecord.id == group_id).first()
            
            if not group:
                return None
            
            return await self._serialize_observation_group(group, include_observations=True)
            
        except Exception as e:
            logger.error(f"Error getting observation group {group_id}: {str(e)}")
            raise
    
    async def create_observation_group(
        self,
        phase_id: int,
        cycle_id: int,
        report_id: int,
        attribute_id: int,
        lob_id: int,
        group_name: str,
        issue_summary: str,
        severity_level: str,
        issue_type: str,
        created_by: int,
        group_description: Optional[str] = None,
        impact_description: Optional[str] = None,
        proposed_resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new observation group"""
        try:
            # Validate inputs
            if severity_level not in [s.value for s in SeverityLevel]:
                raise ValueError(f"Invalid severity level: {severity_level}")
            
            if issue_type not in [i.value for i in IssueType]:
                raise ValueError(f"Invalid issue type: {issue_type}")
            
            # Check if group already exists for this attribute/LOB combination
            existing_group = self.db.query(ObservationRecord).filter(
                and_(
                    ObservationRecord.phase_id == phase_id,
                    ObservationRecord.attribute_id == attribute_id,
                    ObservationRecord.lob_id == lob_id
                )
            ).first()
            
            if existing_group:
                raise ValueError(f"Observation group already exists for attribute {attribute_id} and LOB {lob_id}")
            
            # Create new group
            group = ObservationRecord(
                phase_id=phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                group_name=group_name,
                group_description=group_description,
                attribute_id=attribute_id,
                lob_id=lob_id,
                issue_summary=issue_summary,
                impact_description=impact_description,
                proposed_resolution=proposed_resolution,
                severity_level=severity_level,
                issue_type=issue_type,
                status=ObservationRecordStatus.DRAFT.value,
                detection_method='manual_review',
                detected_by=created_by,
                detected_at=datetime.utcnow(),
                created_by=created_by,
                updated_by=created_by
            )
            
            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Created observation group {group.id}")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error creating observation group: {str(e)}")
            self.db.rollback()
            raise
    
    async def update_observation_group(
        self,
        group_id: int,
        updated_by: int,
        group_name: Optional[str] = None,
        group_description: Optional[str] = None,
        issue_summary: Optional[str] = None,
        impact_description: Optional[str] = None,
        proposed_resolution: Optional[str] = None,
        severity_level: Optional[str] = None,
        issue_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an observation group"""
        try:
            group = self.db.query(ObservationRecord).filter(
                ObservationRecord.id == group_id
            ).first()
            
            if not group:
                raise ValueError(f"Observation group {group_id} not found")
            
            # Check if group is in a state that allows updates
            if group.status in [ObservationRecordStatus.RESOLVED.value, ObservationRecordStatus.CLOSED.value]:
                raise ValueError("Cannot update resolved or closed observation groups")
            
            # Update fields
            if group_name is not None:
                group.group_name = group_name
            if group_description is not None:
                group.group_description = group_description
            if issue_summary is not None:
                group.issue_summary = issue_summary
            if impact_description is not None:
                group.impact_description = impact_description
            if proposed_resolution is not None:
                group.proposed_resolution = proposed_resolution
            if severity_level is not None:
                if severity_level not in [s.value for s in SeverityLevel]:
                    raise ValueError(f"Invalid severity level: {severity_level}")
                group.severity_level = severity_level
            if issue_type is not None:
                if issue_type not in [i.value for i in IssueType]:
                    raise ValueError(f"Invalid issue type: {issue_type}")
                group.issue_type = issue_type
            
            group.updated_by = updated_by
            
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Updated observation group {group_id}")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error updating observation group {group_id}: {str(e)}")
            self.db.rollback()
            raise
    
    # ============================================
    # Review and Approval Workflow
    # ============================================
    
    async def submit_for_tester_review(
        self,
        group_id: int,
        submitted_by: int
    ) -> Dict[str, Any]:
        """Submit observation group for tester review"""
        try:
            group = self.db.query(ObservationRecord).filter(
                ObservationRecord.id == group_id
            ).first()
            
            if not group:
                raise ValueError(f"Observation group {group_id} not found")
            
            if group.status != ObservationRecordStatus.DRAFT.value:
                raise ValueError(f"Cannot submit group with status {group.status}")
            
            # Update status
            group.status = ObservationRecordStatus.PENDING_TESTER_REVIEW.value
            group.updated_by = submitted_by
            
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Submitted observation group {group_id} for tester review")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error submitting group {group_id} for tester review: {str(e)}")
            self.db.rollback()
            raise
    
    async def tester_review_observation_group(
        self,
        group_id: int,
        reviewer_id: int,
        review_decision: str,
        review_notes: Optional[str] = None,
        review_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """Tester review of observation group"""
        try:
            group = self.db.query(ObservationRecord).filter(
                ObservationRecord.id == group_id
            ).first()
            
            if not group:
                raise ValueError(f"Observation group {group_id} not found")
            
            if group.status != ObservationRecordStatus.PENDING_TESTER_REVIEW.value:
                raise ValueError(f"Cannot review group with status {group.status}")
            
            if review_decision not in [d.value for d in ReviewDecision]:
                raise ValueError(f"Invalid review decision: {review_decision}")
            
            if review_score is not None and (review_score < 1 or review_score > 100):
                raise ValueError("Review score must be between 1 and 100")
            
            # Update review fields
            group.tester_review_status = review_decision
            group.tester_review_notes = review_notes
            group.tester_review_score = review_score
            group.tester_reviewed_by = reviewer_id
            group.tester_reviewed_at = datetime.utcnow()
            
            # Update status based on decision
            if review_decision == ReviewDecision.APPROVEDD.value:
                group.status = ObservationRecordStatus.TESTER_APPROVED.value
            elif review_decision == ReviewDecision.REJECTEDED.value:
                group.status = ObservationRecordStatus.REJECTED.value
            elif review_decision == ReviewDecision.NEEDS_CLARIFICATION.value:
                group.status = ObservationRecordStatus.DRAFT.value
                group.clarification_requested = True
            
            group.updated_by = reviewer_id
            
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Tester reviewed observation group {group_id}: {review_decision}")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error in tester review of group {group_id}: {str(e)}")
            self.db.rollback()
            raise
    
    async def submit_for_report_owner_approval(
        self,
        group_id: int,
        submitted_by: int
    ) -> Dict[str, Any]:
        """Submit observation group for report owner approval"""
        try:
            group = self.db.query(ObservationRecord).filter(
                ObservationRecord.id == group_id
            ).first()
            
            if not group:
                raise ValueError(f"Observation group {group_id} not found")
            
            if group.status != ObservationRecordStatus.TESTER_APPROVED.value:
                raise ValueError(f"Cannot submit group with status {group.status} for approval")
            
            # Update status
            group.status = ObservationRecordStatus.PENDING_REPORT_OWNER_APPROVAL.value
            group.updated_by = submitted_by
            
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Submitted observation group {group_id} for report owner approval")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error submitting group {group_id} for report owner approval: {str(e)}")
            self.db.rollback()
            raise
    
    async def report_owner_approve_observation_group(
        self,
        group_id: int,
        approver_id: int,
        approval_decision: str,
        approval_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Report owner approval of observation group"""
        try:
            group = self.db.query(ObservationRecord).filter(
                ObservationRecord.id == group_id
            ).first()
            
            if not group:
                raise ValueError(f"Observation group {group_id} not found")
            
            if group.status != ObservationRecordStatus.PENDING_REPORT_OWNER_APPROVAL.value:
                raise ValueError(f"Cannot approve group with status {group.status}")
            
            if approval_decision not in [d.value for d in ReviewDecision]:
                raise ValueError(f"Invalid approval decision: {approval_decision}")
            
            # Update approval fields
            group.report_owner_approval_status = approval_decision
            group.report_owner_approval_notes = approval_notes
            group.report_owner_approved_by = approver_id
            group.report_owner_approved_at = datetime.utcnow()
            
            # Update status based on decision
            if approval_decision == ReviewDecision.APPROVEDD.value:
                group.status = ObservationRecordStatus.REPORT_OWNER_APPROVED.value
            elif approval_decision == ReviewDecision.REJECTEDED.value:
                group.status = ObservationRecordStatus.REJECTED.value
            elif approval_decision == ReviewDecision.NEEDS_CLARIFICATION.value:
                group.status = ObservationRecordStatus.TESTER_APPROVED.value
                group.clarification_requested = True
            
            group.updated_by = approver_id
            
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Report owner approved observation group {group_id}: {approval_decision}")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error in report owner approval of group {group_id}: {str(e)}")
            self.db.rollback()
            raise
    
    # ============================================
    # Clarification Management
    # ============================================
    
    async def request_clarification(
        self,
        group_id: int,
        requester_id: int,
        clarification_text: str,
        due_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Request clarification on observation group"""
        try:
            group = self.db.query(ObservationRecord).filter(
                ObservationRecord.id == group_id
            ).first()
            
            if not group:
                raise ValueError(f"Observation group {group_id} not found")
            
            # Set clarification fields
            group.clarification_requested = True
            group.clarification_request_text = clarification_text
            group.clarification_due_date = due_date or datetime.utcnow() + timedelta(days=3)
            group.updated_by = requester_id
            
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Requested clarification for observation group {group_id}")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error requesting clarification for group {group_id}: {str(e)}")
            self.db.rollback()
            raise
    
    async def provide_clarification(
        self,
        group_id: int,
        provider_id: int,
        clarification_response: str
    ) -> Dict[str, Any]:
        """Provide clarification response"""
        try:
            group = self.db.query(ObservationRecord).filter(
                ObservationRecord.id == group_id
            ).first()
            
            if not group:
                raise ValueError(f"Observation group {group_id} not found")
            
            if not group.clarification_requested:
                raise ValueError("No clarification was requested for this group")
            
            # Update clarification fields
            group.clarification_response = clarification_response
            group.clarification_requested = False
            group.clarification_due_date = None
            group.updated_by = provider_id
            
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Provided clarification for observation group {group_id}")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error providing clarification for group {group_id}: {str(e)}")
            self.db.rollback()
            raise
    
    # ============================================
    # Resolution Management
    # ============================================
    
    async def start_resolution(
        self,
        group_id: int,
        resolution_owner_id: int,
        resolution_approach: str,
        resolution_timeline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start resolution process for observation group"""
        try:
            group = self.db.query(ObservationRecord).filter(
                ObservationRecord.id == group_id
            ).first()
            
            if not group:
                raise ValueError(f"Observation group {group_id} not found")
            
            if group.status != ObservationRecordStatus.REPORT_OWNER_APPROVED.value:
                raise ValueError(f"Cannot start resolution for group with status {group.status}")
            
            # Update resolution fields
            group.resolution_status = ResolutionStatus.IN_PROGRESS.value
            group.resolution_approach = resolution_approach
            group.resolution_timeline = resolution_timeline
            group.resolution_owner = resolution_owner_id
            group.updated_by = resolution_owner_id
            
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Started resolution for observation group {group_id}")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error starting resolution for group {group_id}: {str(e)}")
            self.db.rollback()
            raise
    
    async def complete_resolution(
        self,
        group_id: int,
        resolver_id: int,
        resolution_notes: str
    ) -> Dict[str, Any]:
        """Complete resolution of observation group"""
        try:
            group = self.db.query(ObservationRecord).filter(
                ObservationRecord.id == group_id
            ).first()
            
            if not group:
                raise ValueError(f"Observation group {group_id} not found")
            
            if group.resolution_status != ResolutionStatus.IN_PROGRESS.value:
                raise ValueError(f"Cannot complete resolution for group with resolution status {group.resolution_status}")
            
            # Update resolution fields
            group.resolution_status = ResolutionStatus.COMPLETED.value
            group.resolution_notes = resolution_notes
            group.resolved_by = resolver_id
            group.resolved_at = datetime.utcnow()
            group.status = ObservationRecordStatus.RESOLVED.value
            group.updated_by = resolver_id
            
            self.db.commit()
            self.db.refresh(group)
            
            logger.info(f"Completed resolution for observation group {group_id}")
            return await self._serialize_observation_group(group)
            
        except Exception as e:
            logger.error(f"Error completing resolution for group {group_id}: {str(e)}")
            self.db.rollback()
            raise
    
    # ============================================
    # Individual Observation Management
    # ============================================
    
    async def get_observations_for_group(
        self,
        group_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get observations for a specific group"""
        try:
            query = self.db.query(Observation).filter(
                Observation.group_id == group_id
            )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            observations = query.offset(offset).limit(page_size).all()
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "observations": [await self._serialize_observation(obs) for obs in observations],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting observations for group {group_id}: {str(e)}")
            raise
    
    async def get_observation_by_id(self, observation_id: int) -> Optional[Dict[str, Any]]:
        """Get observation by ID"""
        try:
            observation = self.db.query(Observation).filter(
                Observation.id == observation_id
            ).first()
            
            if not observation:
                return None
            
            return await self._serialize_observation(observation)
            
        except Exception as e:
            logger.error(f"Error getting observation {observation_id}: {str(e)}")
            raise
    
    # ============================================
    # Dashboard and Statistics
    # ============================================
    
    async def get_observation_statistics(
        self,
        phase_id: Optional[int] = None,
        cycle_id: Optional[int] = None,
        report_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get observation statistics"""
        try:
            query = self.db.query(ObservationRecord)
            
            if phase_id:
                query = query.filter(ObservationRecord.phase_id == phase_id)
            if cycle_id:
                query = query.filter(ObservationRecord.cycle_id == cycle_id)
            if report_id:
                query = query.filter(ObservationRecord.report_id == report_id)
            
            # Get status counts
            status_counts = {}
            for status in ObservationRecordStatus:
                count = query.filter(ObservationRecord.status == status.value).count()
                status_counts[status.value] = count
            
            # Get severity counts
            severity_counts = {}
            for severity in SeverityLevel:
                count = query.filter(ObservationRecord.severity_level == severity.value).count()
                severity_counts[severity.value] = count
            
            # Get issue type counts
            issue_type_counts = {}
            for issue_type in IssueType:
                count = query.filter(ObservationRecord.issue_type == issue_type.value).count()
                issue_type_counts[issue_type.value] = count
            
            # Get total observations
            total_observations = self.db.query(Observation).join(ObservationRecord)
            if phase_id:
                total_observations = total_observations.filter(ObservationRecord.phase_id == phase_id)
            if cycle_id:
                total_observations = total_observations.filter(ObservationRecord.cycle_id == cycle_id)
            if report_id:
                total_observations = total_observations.filter(ObservationRecord.report_id == report_id)
            
            total_observations_count = total_observations.count()
            
            return {
                "total_groups": query.count(),
                "total_observations": total_observations_count,
                "status_distribution": status_counts,
                "severity_distribution": severity_counts,
                "issue_type_distribution": issue_type_counts,
                "average_observations_per_group": (
                    total_observations_count / query.count() if query.count() > 0 else 0
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting observation statistics: {str(e)}")
            raise
    
    # ============================================
    # Utility Methods
    # ============================================
    
    async def _serialize_observation_group(
        self, 
        group: ObservationRecord, 
        include_observations: bool = False
    ) -> Dict[str, Any]:
        """Serialize observation group to dictionary"""
        data = {
            "id": group.id,
            "phase_id": group.phase_id,
            "cycle_id": group.cycle_id,
            "report_id": group.report_id,
            "group_name": group.group_name,
            "group_description": group.group_description,
            "attribute_id": group.attribute_id,
            "lob_id": group.lob_id,
            "observation_count": group.observation_count,
            "severity_level": group.severity_level,
            "issue_type": group.issue_type,
            "issue_summary": group.issue_summary,
            "impact_description": group.impact_description,
            "proposed_resolution": group.proposed_resolution,
            "status": group.status,
            "tester_review_status": group.tester_review_status,
            "tester_review_notes": group.tester_review_notes,
            "tester_review_score": group.tester_review_score,
            "tester_reviewed_by": group.tester_reviewed_by,
            "tester_reviewed_at": group.tester_reviewed_at.isoformat() if group.tester_reviewed_at else None,
            "report_owner_approval_status": group.report_owner_approval_status,
            "report_owner_approval_notes": group.report_owner_approval_notes,
            "report_owner_approved_by": group.report_owner_approved_by,
            "report_owner_approved_at": group.report_owner_approved_at.isoformat() if group.report_owner_approved_at else None,
            "clarification_requested": group.clarification_requested,
            "clarification_request_text": group.clarification_request_text,
            "clarification_response": group.clarification_response,
            "clarification_due_date": group.clarification_due_date.isoformat() if group.clarification_due_date else None,
            "resolution_status": group.resolution_status,
            "resolution_approach": group.resolution_approach,
            "resolution_timeline": group.resolution_timeline,
            "resolution_owner": group.resolution_owner,
            "resolution_notes": group.resolution_notes,
            "resolved_by": group.resolved_by,
            "resolved_at": group.resolved_at.isoformat() if group.resolved_at else None,
            "detection_method": group.detection_method,
            "detected_by": group.detected_by,
            "detected_at": group.detected_at.isoformat() if group.detected_at else None,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "updated_at": group.updated_at.isoformat() if group.updated_at else None,
            "created_by": group.created_by,
            "updated_by": group.updated_by,
        }
        
        # Add related object data
        if hasattr(group, 'attribute') and group.attribute:
            data["attribute"] = {
                "id": group.attribute.id,
                "name": group.attribute.attribute_name,
                "description": group.attribute.description
            }
        
        if hasattr(group, 'lob') and group.lob:
            data["lob"] = {
                "id": group.lob.lob_id,
                "name": group.lob.lob_name,
                "description": group.lob.lob_description
            }
        
        if hasattr(group, 'detector') and group.detector:
            data["detector"] = {
                "id": group.detector.user_id,
                "name": f"{group.detector.first_name} {group.detector.last_name}",
                "email": group.detector.email
            }
        
        if hasattr(group, 'tester_reviewer') and group.tester_reviewer:
            data["tester_reviewer"] = {
                "id": group.tester_reviewer.user_id,
                "name": f"{group.tester_reviewer.first_name} {group.tester_reviewer.last_name}",
                "email": group.tester_reviewer.email
            }
        
        if hasattr(group, 'report_owner_approver') and group.report_owner_approver:
            data["report_owner_approver"] = {
                "id": group.report_owner_approver.user_id,
                "name": f"{group.report_owner_approver.first_name} {group.report_owner_approver.last_name}",
                "email": group.report_owner_approver.email
            }
        
        if include_observations and hasattr(group, 'observations'):
            data["observations"] = [await self._serialize_observation(obs) for obs in group.observations]
        
        return data
    
    async def _serialize_observation(self, observation: Observation) -> Dict[str, Any]:
        """Serialize observation to dictionary"""
        return {
            "id": observation.id,
            "group_id": observation.group_id,
            "test_execution_id": observation.test_execution_id,
            "test_case_id": observation.test_case_id,
            "attribute_id": observation.attribute_id,
            "sample_id": observation.sample_id,
            "lob_id": observation.lob_id,
            "observation_title": observation.observation_title,
            "observation_description": observation.observation_description,
            "expected_value": observation.expected_value,
            "actual_value": observation.actual_value,
            "variance_details": observation.variance_details,
            "test_result": observation.test_result,
            "evidence_files": observation.evidence_files,
            "supporting_documentation": observation.supporting_documentation,
            "confidence_level": observation.confidence_level,
            "reproducible": observation.reproducible,
            "frequency_estimate": observation.frequency_estimate,
            "business_impact": observation.business_impact,
            "technical_impact": observation.technical_impact,
            "regulatory_impact": observation.regulatory_impact,
            "created_at": observation.created_at.isoformat() if observation.created_at else None,
            "updated_at": observation.updated_at.isoformat() if observation.updated_at else None,
            "created_by": observation.created_by,
            "updated_by": observation.updated_by,
        }


# Utility function to create service instance
def create_observation_management_service(db: Session) -> ObservationManagementService:
    """Create observation management service instance"""
    return ObservationManagementService(db)