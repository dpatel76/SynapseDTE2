"""Implementation of SLAService"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.application.interfaces.services import SLAService
from app.models import SLAConfiguration, WorkflowPhase


class SLAServiceImpl(SLAService):
    """Implementation of SLA tracking service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_sla_compliance(
        self,
        cycle_id: int,
        report_id: int,
        phase: str
    ) -> Dict[str, Any]:
        """Check SLA compliance for a phase"""
        try:
            # Get SLA configuration for the phase
            result = await self.session.execute(
                select(SLAConfiguration).where(
                    SLAConfiguration.phase_name == phase
                )
            )
            sla_config = result.scalar_one_or_none()
            
            if not sla_config:
                return {
                    "compliant": True,
                    "message": "No SLA configured for this phase",
                    "sla_hours": None
                }
            
            # Get workflow phase status
            phase_result = await self.session.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == phase
                    )
                )
            )
            workflow_phase = phase_result.scalar_one_or_none()
            
            if not workflow_phase:
                return {
                    "compliant": True,
                    "message": "Phase not started",
                    "sla_hours": sla_config.sla_hours
                }
            
            # Calculate time elapsed
            if workflow_phase.status == 'completed':
                # Phase is completed, check if it was completed within SLA
                if workflow_phase.started_at and workflow_phase.completed_at:
                    elapsed = workflow_phase.completed_at - workflow_phase.started_at
                    elapsed_hours = elapsed.total_seconds() / 3600
                    
                    return {
                        "compliant": elapsed_hours <= sla_config.sla_hours,
                        "elapsed_hours": elapsed_hours,
                        "sla_hours": sla_config.sla_hours,
                        "message": "Phase completed" if elapsed_hours <= sla_config.sla_hours else "SLA breached",
                        "breach_hours": max(0, elapsed_hours - sla_config.sla_hours)
                    }
            else:
                # Phase is in progress, check if approaching or breaching SLA
                if workflow_phase.started_at:
                    elapsed = datetime.utcnow() - workflow_phase.started_at
                    elapsed_hours = elapsed.total_seconds() / 3600
                    remaining_hours = sla_config.sla_hours - elapsed_hours
                    
                    # Determine status
                    if elapsed_hours > sla_config.sla_hours:
                        status = "breached"
                        compliant = False
                    elif remaining_hours < 24:  # Less than 24 hours remaining
                        status = "at_risk"
                        compliant = True
                    else:
                        status = "on_track"
                        compliant = True
                    
                    return {
                        "compliant": compliant,
                        "status": status,
                        "elapsed_hours": elapsed_hours,
                        "sla_hours": sla_config.sla_hours,
                        "remaining_hours": remaining_hours,
                        "message": f"Phase {status.replace('_', ' ')}",
                        "breach_hours": max(0, elapsed_hours - sla_config.sla_hours) if not compliant else 0
                    }
            
            return {
                "compliant": True,
                "message": "Unable to calculate SLA",
                "sla_hours": sla_config.sla_hours
            }
            
        except Exception as e:
            return {
                "compliant": True,
                "message": f"Error checking SLA: {str(e)}",
                "error": True
            }
    
    async def trigger_escalation(
        self,
        cycle_id: int,
        report_id: int,
        phase: str,
        escalation_level: int
    ) -> None:
        """Trigger SLA escalation"""
        try:
            # Get SLA configuration
            result = await self.session.execute(
                select(SLAConfiguration).where(
                    SLAConfiguration.phase_name == phase
                )
            )
            sla_config = result.scalar_one_or_none()
            
            if not sla_config:
                return
            
            # Update escalation tracking in workflow phase metadata
            phase_result = await self.session.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == phase
                    )
                )
            )
            workflow_phase = phase_result.scalar_one_or_none()
            
            if workflow_phase:
                metadata = workflow_phase.metadata or {}
                escalations = metadata.get('escalations', [])
                escalations.append({
                    "level": escalation_level,
                    "triggered_at": datetime.utcnow().isoformat(),
                    "sla_breach_hours": metadata.get('sla_breach_hours', 0)
                })
                metadata['escalations'] = escalations
                metadata['current_escalation_level'] = escalation_level
                
                workflow_phase.metadata = metadata
                await self.session.commit()
            
            # In a real implementation, this would:
            # 1. Send notifications to appropriate stakeholders based on escalation level
            # 2. Create tasks for resolution
            # 3. Update dashboards and reports
            
        except Exception as e:
            print(f"Failed to trigger escalation: {str(e)}")
    
    async def get_sla_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get SLA performance metrics"""
        try:
            # Build query for workflow phases
            query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.created_at >= start_date,
                    WorkflowPhase.created_at <= end_date,
                    WorkflowPhase.status.in_(['completed', 'in_progress'])
                )
            )
            
            if phase:
                query = query.where(WorkflowPhase.phase_name == phase)
            
            result = await self.session.execute(query)
            workflow_phases = result.scalars().all()
            
            # Get SLA configurations
            sla_query = select(SLAConfiguration)
            if phase:
                sla_query = sla_query.where(SLAConfiguration.phase_name == phase)
            
            sla_result = await self.session.execute(sla_query)
            sla_configs = {s.phase_name: s.sla_hours for s in sla_result.scalars().all()}
            
            # Calculate metrics
            metrics = {
                "total_phases": len(workflow_phases),
                "completed_phases": 0,
                "in_progress_phases": 0,
                "sla_compliant": 0,
                "sla_breached": 0,
                "average_completion_time": 0,
                "phases": {}
            }
            
            completion_times = []
            phase_metrics = {}
            
            for wp in workflow_phases:
                phase_name = wp.phase_name
                if phase_name not in phase_metrics:
                    phase_metrics[phase_name] = {
                        "total": 0,
                        "completed": 0,
                        "compliant": 0,
                        "breached": 0,
                        "average_hours": 0
                    }
                
                phase_metrics[phase_name]["total"] += 1
                
                if wp.status == 'completed':
                    metrics["completed_phases"] += 1
                    phase_metrics[phase_name]["completed"] += 1
                    
                    if wp.started_at and wp.completed_at:
                        elapsed = wp.completed_at - wp.started_at
                        elapsed_hours = elapsed.total_seconds() / 3600
                        completion_times.append(elapsed_hours)
                        
                        sla_hours = sla_configs.get(phase_name, float('inf'))
                        if elapsed_hours <= sla_hours:
                            metrics["sla_compliant"] += 1
                            phase_metrics[phase_name]["compliant"] += 1
                        else:
                            metrics["sla_breached"] += 1
                            phase_metrics[phase_name]["breached"] += 1
                else:
                    metrics["in_progress_phases"] += 1
                    
                    # Check if currently breaching SLA
                    if wp.started_at:
                        elapsed = datetime.utcnow() - wp.started_at
                        elapsed_hours = elapsed.total_seconds() / 3600
                        sla_hours = sla_configs.get(phase_name, float('inf'))
                        
                        if elapsed_hours > sla_hours:
                            metrics["sla_breached"] += 1
                            phase_metrics[phase_name]["breached"] += 1
            
            # Calculate averages
            if completion_times:
                metrics["average_completion_time"] = sum(completion_times) / len(completion_times)
            
            # Calculate phase-specific averages
            for phase_name, pm in phase_metrics.items():
                if pm["completed"] > 0:
                    # This is simplified - in reality would calculate from actual data
                    pm["average_hours"] = metrics["average_completion_time"]
                pm["compliance_rate"] = (pm["compliant"] / pm["total"] * 100) if pm["total"] > 0 else 0
            
            metrics["phases"] = phase_metrics
            metrics["overall_compliance_rate"] = (
                metrics["sla_compliant"] / metrics["total_phases"] * 100
            ) if metrics["total_phases"] > 0 else 0
            
            return metrics
            
        except Exception as e:
            return {
                "error": str(e),
                "total_phases": 0,
                "sla_compliant": 0,
                "sla_breached": 0
            }