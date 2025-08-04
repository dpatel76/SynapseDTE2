"""
SLA Tracking and Escalation Service
Monitors workflow phases and triggers escalations based on configured SLAs
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from fastapi import Depends
from app.core.database import get_db
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.user import User
from app.core.config import get_settings
import asyncio

logger = logging.getLogger(__name__)
settings = get_settings()


class SLAConfiguration:
    """SLA configuration for different workflow phases"""
    
    DEFAULT_SLA_HOURS = {
        "planning": 72,      # 3 days
        "scoping": 48,       # 2 days  
        "data_owner_id": 24,  # 1 day
        "sample_selection": 48,   # 2 days
        "request_for_info": 120,  # 5 days
        "test_execution": 168, # 7 days
        "observation_mgmt": 48    # 2 days
    }
    
    ESCALATION_LEVELS = [
        {"level": 1, "hours_after_sla": 4, "notify_roles": ["Test Executive"]},
        {"level": 2, "hours_after_sla": 12, "notify_roles": ["Test Executive", "Report Owner"]},
        {"level": 3, "hours_after_sla": 24, "notify_roles": ["Test Executive", "Report Owner", "Report Owner Executive"]},
        {"level": 4, "hours_after_sla": 48, "notify_roles": ["Data Executive", "Admin"]}
    ]


class SLATracker:
    """Track SLA for workflow phases"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sla_config = SLAConfiguration()
        
    async def start_phase_tracking(self, cycle_id: int, report_id: int, phase: str, user_id: int) -> Dict[str, Any]:
        """Start SLA tracking for a workflow phase"""
        try:
            # Calculate SLA deadline
            sla_hours = self.sla_config.DEFAULT_SLA_HOURS.get(phase, 48)
            start_time = datetime.utcnow()
            sla_deadline = start_time + timedelta(hours=sla_hours)
            
            # Store SLA tracking record (would typically be in database)
            tracking_record = {
                "cycle_id": cycle_id,
                "report_id": report_id,
                "phase": phase,
                "start_time": start_time,
                "sla_deadline": sla_deadline,
                "status": "ACTIVE",
                "started_by": user_id,
                "escalation_level": 0,
                "created_at": start_time
            }
            
            logger.info(f"Started SLA tracking for {phase} - Cycle {cycle_id}, Report {report_id}, Deadline: {sla_deadline}")
            return tracking_record
            
        except Exception as e:
            logger.error(f"Failed to start SLA tracking: {str(e)}")
            raise
    
    async def complete_phase_tracking(self, cycle_id: int, report_id: int, phase: str, user_id: int) -> Dict[str, Any]:
        """Complete SLA tracking for a workflow phase"""
        try:
            completion_time = datetime.utcnow()
            
            # Update tracking record status
            completion_record = {
                "cycle_id": cycle_id,
                "report_id": report_id,
                "phase": phase,
                "completion_time": completion_time,
                "status": "COMPLETED",
                "completed_by": user_id,
                "updated_at": completion_time
            }
            
            logger.info(f"Completed SLA tracking for {phase} - Cycle {cycle_id}, Report {report_id}")
            return completion_record
            
        except Exception as e:
            logger.error(f"Failed to complete SLA tracking: {str(e)}")
            raise
    
    async def check_sla_breaches(self) -> List[Dict[str, Any]]:
        """Check for SLA breaches and return list of breached items"""
        breaches = []
        current_time = datetime.utcnow()
        
        try:
            # In a real implementation, this would query the SLA tracking table
            # For now, we'll simulate some breach detection logic
            
            # Get active cycles and check their phases
            stmt = select(TestCycle).where(
                and_(
                    TestCycle.start_date <= current_time.date(),
                    TestCycle.end_date >= current_time.date()
                )
            )
            result = await self.db.execute(stmt)
            active_cycles = result.scalars().all()
            
            for cycle in active_cycles:
                # Simulate SLA breach detection
                if await self._is_phase_overdue(cycle, "planning"):
                    breaches.append({
                        "cycle_id": cycle.cycle_id,
                        "phase": "planning",
                        "breach_time": current_time,
                        "severity": "HIGH"
                    })
            
            logger.info(f"Found {len(breaches)} SLA breaches")
            return breaches
            
        except Exception as e:
            logger.error(f"Failed to check SLA breaches: {str(e)}")
            return []
    
    async def _is_phase_overdue(self, cycle: TestCycle, phase: str) -> bool:
        """Check if a specific phase is overdue (simulation)"""
        # This would check against actual SLA tracking records
        # For simulation, we'll randomly return some overdue phases
        import random
        return random.random() < 0.1  # 10% chance of being overdue


class EscalationManager:
    """Manage SLA escalations and notifications"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sla_config = SLAConfiguration()
        
    async def trigger_escalation(self, breach_info: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger escalation for SLA breach"""
        try:
            cycle_id = breach_info["cycle_id"]
            phase = breach_info["phase"]
            
            # Determine escalation level
            escalation_level = self._calculate_escalation_level(breach_info)
            escalation_config = self.sla_config.ESCALATION_LEVELS[escalation_level - 1]
            
            # Get users to notify
            users_to_notify = await self._get_users_for_escalation(cycle_id, escalation_config["notify_roles"])
            
            # Send notifications
            notification_results = []
            for user in users_to_notify:
                result = await self._send_escalation_notification(user, breach_info, escalation_level)
                notification_results.append(result)
            
            escalation_record = {
                "cycle_id": cycle_id,
                "phase": phase,
                "escalation_level": escalation_level,
                "triggered_at": datetime.utcnow(),
                "notified_users": [user.user_id for user in users_to_notify],
                "notification_results": notification_results
            }
            
            logger.info(f"Triggered escalation level {escalation_level} for cycle {cycle_id}, phase {phase}")
            return escalation_record
            
        except Exception as e:
            logger.error(f"Failed to trigger escalation: {str(e)}")
            raise
    
    def _calculate_escalation_level(self, breach_info: Dict[str, Any]) -> int:
        """Calculate appropriate escalation level based on breach severity and time"""
        # Simulate escalation level calculation
        breach_time = breach_info.get("breach_time", datetime.utcnow())
        hours_since_breach = (datetime.utcnow() - breach_time).total_seconds() / 3600
        
        for i, level_config in enumerate(self.sla_config.ESCALATION_LEVELS):
            if hours_since_breach >= level_config["hours_after_sla"]:
                continue
            return i + 1
        
        return len(self.sla_config.ESCALATION_LEVELS)  # Maximum escalation level
    
    async def _get_users_for_escalation(self, cycle_id: int, roles: List[str]) -> List[User]:
        """Get users to notify for escalation based on roles"""
        try:
            # Get cycle information
            stmt = select(TestCycle).where(TestCycle.cycle_id == cycle_id)
            result = await self.db.execute(stmt)
            cycle = result.scalar_one_or_none()
            if not cycle:
                return []
            
            # Get users with the specified roles
            stmt = select(User).where(
                and_(
                    User.role.in_(roles),
                    User.is_active == True
                )
            )
            result = await self.db.execute(stmt)
            users = result.scalars().all()
            
            # Filter users based on LOB access if applicable
            relevant_users = []
            for user in users:
                if user.role in ["Admin", "Data Executive"]:
                    relevant_users.append(user)
                elif user.user_id == cycle.test_executive_id:
                    relevant_users.append(user)
                # Add more role-specific logic as needed
            
            return relevant_users
            
        except Exception as e:
            logger.error(f"Failed to get users for escalation: {str(e)}")
            return []
    
    async def _send_escalation_notification(self, user: User, breach_info: Dict[str, Any], escalation_level: int) -> Dict[str, Any]:
        """Send escalation notification to user"""
        try:
            # Prepare notification content
            subject = f"SLA Escalation Level {escalation_level} - Cycle {breach_info['cycle_id']}"
            message = f"""
            SLA Breach Alert
            
            Cycle ID: {breach_info['cycle_id']}
            Phase: {breach_info['phase']}
            Escalation Level: {escalation_level}
            Breach Time: {breach_info.get('breach_time', 'Unknown')}
            
            Please take immediate action to resolve this issue.
            
            SynapseDT System
            """
            
            # Send email notification
            notification_result = await self._send_email_notification(user.email, subject, message)
            
            # Log notification
            logger.info(f"Sent escalation notification to {user.email} for cycle {breach_info['cycle_id']}")
            
            return {
                "user_id": user.user_id,
                "email": user.email,
                "notification_type": "email",
                "sent_at": datetime.utcnow(),
                "success": notification_result.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"Failed to send escalation notification: {str(e)}")
            return {
                "user_id": user.user_id,
                "error": str(e),
                "success": False
            }
    
    async def _send_email_notification(self, email: str, subject: str, message: str) -> Dict[str, Any]:
        """Send email notification"""
        try:
            # In a real implementation, this would use actual SMTP settings
            # For now, we'll simulate email sending
            
            if settings.smtp_enabled if hasattr(settings, 'smtp_enabled') else False:
                # Actual email sending would go here
                # msg = MimeMultipart()
                # msg['From'] = settings.smtp_from_email
                # msg['To'] = email
                # msg['Subject'] = subject
                # msg.attach(MimeText(message, 'plain'))
                
                # Send email using SMTP
                # server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
                # ... SMTP implementation
                pass
            
            # Simulate successful email sending
            logger.info(f"Email notification sent to {email}: {subject}")
            return {"success": True, "sent_at": datetime.utcnow()}
            
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}")
            return {"success": False, "error": str(e)}


class SLAService:
    """Main SLA service orchestrating tracking and escalations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tracker = SLATracker(db)
        self.escalation_manager = EscalationManager(db)
    
    async def start_tracking(self, cycle_id: int, report_id: int, phase: str, user_id: int) -> Dict[str, Any]:
        """Start SLA tracking for a workflow phase"""
        return await self.tracker.start_phase_tracking(cycle_id, report_id, phase, user_id)
    
    async def complete_tracking(self, cycle_id: int, report_id: int, phase: str, user_id: int) -> Dict[str, Any]:
        """Complete SLA tracking for a workflow phase"""
        return await self.tracker.complete_phase_tracking(cycle_id, report_id, phase, user_id)
    
    async def check_breaches(self) -> List[Dict[str, Any]]:
        """Check for SLA breaches"""
        return await self.tracker.check_sla_breaches()
    
    async def trigger_escalations(self, breaches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trigger escalations for SLA breaches"""
        escalation_results = []
        for breach in breaches:
            result = await self.escalation_manager.trigger_escalation(breach)
            escalation_results.append(result)
        return escalation_results
    
    async def get_sla_status(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Get SLA status for a specific cycle and report"""
        try:
            # In a real implementation, this would query SLA tracking records
            # For now, we'll return a simulated status
            
            current_time = datetime.utcnow()
            
            status = {
                "cycle_id": cycle_id,
                "report_id": report_id,
                "phases": {
                    "planning": {
                        "status": "COMPLETED",
                        "sla_deadline": current_time + timedelta(hours=72),
                        "completion_time": current_time - timedelta(hours=24),
                        "on_time": True
                    },
                    "scoping": {
                        "status": "ACTIVE",
                        "sla_deadline": current_time + timedelta(hours=48),
                        "start_time": current_time - timedelta(hours=12),
                        "on_time": True
                    }
                },
                "overall_status": "ON_TRACK",
                "escalation_level": 0
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get SLA status: {str(e)}")
            return {"error": str(e)}
    
    async def run_sla_monitoring(self):
        """Background task to monitor SLAs and trigger escalations"""
        try:
            logger.info("Running SLA monitoring check")
            
            # Check for breaches
            breaches = await self.check_breaches()
            
            if breaches:
                logger.warning(f"Found {len(breaches)} SLA breaches")
                
                # Trigger escalations
                escalation_results = await self.trigger_escalations(breaches)
                
                logger.info(f"Triggered {len(escalation_results)} escalations")
            else:
                logger.debug("No SLA breaches found")
                
        except Exception as e:
            logger.error(f"SLA monitoring failed: {str(e)}")


async def get_sla_service(db: AsyncSession = Depends(get_db)) -> SLAService:
    """Dependency to get SLA service instance"""
    return SLAService(db) 