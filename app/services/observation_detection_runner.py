"""
Observation Detection Runner
Service for running observation detection jobs
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.observation_detection_service import ObservationDetectionService
from app.models.workflow import WorkflowPhase
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.user import User

logger = logging.getLogger(__name__)


class ObservationDetectionRunner:
    """Runner service for observation detection jobs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.detection_service = ObservationDetectionService(db)
    
    async def run_detection_for_phase(
        self,
        phase_id: int,
        detection_user_id: int,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Run observation detection for a specific phase
        
        Args:
            phase_id: Phase ID to detect observations for
            detection_user_id: User ID for detection tracking
            batch_size: Batch size for processing
            
        Returns:
            Detection results
        """
        try:
            # Get phase details
            phase = self.db.query(WorkflowPhase).filter(
                WorkflowPhase.phase_id == phase_id
            ).first()
            
            if not phase:
                raise ValueError(f"Phase {phase_id} not found")
            
            logger.info(f"Running observation detection for phase {phase_id}")
            
            # Get cycle and report from phase
            cycle_id = phase.cycle_id
            report_id = phase.report_id
            
            # Run detection
            results = await self.detection_service.detect_observations_from_failures(
                phase_id=phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                detection_user_id=detection_user_id,
                batch_size=batch_size
            )
            
            # Add phase information to results
            results.update({
                "phase_id": phase_id,
                "cycle_id": cycle_id,
                "report_id": report_id,
                "detection_timestamp": datetime.utcnow().isoformat(),
                "detection_user_id": detection_user_id
            })
            
            logger.info(f"Completed observation detection for phase {phase_id}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error running observation detection for phase {phase_id}: {str(e)}")
            raise
    
    async def run_detection_for_cycle(
        self,
        cycle_id: int,
        detection_user_id: int,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Run observation detection for all phases in a cycle
        
        Args:
            cycle_id: Cycle ID to detect observations for
            detection_user_id: User ID for detection tracking
            batch_size: Batch size for processing
            
        Returns:
            Detection results summary
        """
        try:
            # Get cycle details
            cycle = self.db.query(TestCycle).filter(
                TestCycle.cycle_id == cycle_id
            ).first()
            
            if not cycle:
                raise ValueError(f"Cycle {cycle_id} not found")
            
            logger.info(f"Running observation detection for cycle {cycle_id}")
            
            # Get all phases in cycle that need detection
            phases = self.db.query(WorkflowPhase).filter(
                WorkflowPhase.cycle_id == cycle_id
            ).all()
            
            cycle_results = {
                "cycle_id": cycle_id,
                "detection_timestamp": datetime.utcnow().isoformat(),
                "detection_user_id": detection_user_id,
                "phases_processed": 0,
                "total_processed_count": 0,
                "total_groups_created": 0,
                "total_observations_created": 0,
                "phase_results": [],
                "errors": []
            }
            
            # Process each phase
            for phase in phases:
                try:
                    phase_results = await self.run_detection_for_phase(
                        phase_id=phase.phase_id,
                        detection_user_id=detection_user_id,
                        batch_size=batch_size
                    )
                    
                    cycle_results["phases_processed"] += 1
                    cycle_results["total_processed_count"] += phase_results.get("processed_count", 0)
                    cycle_results["total_groups_created"] += phase_results.get("groups_created", 0)
                    cycle_results["total_observations_created"] += phase_results.get("observations_created", 0)
                    cycle_results["phase_results"].append(phase_results)
                    
                    # Collect any phase-level errors
                    if phase_results.get("errors"):
                        cycle_results["errors"].extend(phase_results["errors"])
                
                except Exception as e:
                    error_msg = f"Error processing phase {phase.phase_id}: {str(e)}"
                    logger.error(error_msg)
                    cycle_results["errors"].append(error_msg)
            
            logger.info(f"Completed observation detection for cycle {cycle_id}: {cycle_results}")
            return cycle_results
            
        except Exception as e:
            logger.error(f"Error running observation detection for cycle {cycle_id}: {str(e)}")
            raise
    
    async def run_detection_for_report(
        self,
        report_id: int,
        detection_user_id: int,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Run observation detection for all cycles in a report
        
        Args:
            report_id: Report ID to detect observations for
            detection_user_id: User ID for detection tracking
            batch_size: Batch size for processing
            
        Returns:
            Detection results summary
        """
        try:
            # Get report details
            report = self.db.query(Report).filter(
                Report.id == report_id
            ).first()
            
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            logger.info(f"Running observation detection for report {report_id}")
            
            # Get all cycles in report that need detection
            cycles = self.db.query(TestCycle).filter(
                TestCycle.report_id == report_id
            ).all()
            
            report_results = {
                "report_id": report_id,
                "detection_timestamp": datetime.utcnow().isoformat(),
                "detection_user_id": detection_user_id,
                "cycles_processed": 0,
                "total_processed_count": 0,
                "total_groups_created": 0,
                "total_observations_created": 0,
                "cycle_results": [],
                "errors": []
            }
            
            # Process each cycle
            for cycle in cycles:
                try:
                    cycle_results = await self.run_detection_for_cycle(
                        cycle_id=cycle.cycle_id,
                        detection_user_id=detection_user_id,
                        batch_size=batch_size
                    )
                    
                    report_results["cycles_processed"] += 1
                    report_results["total_processed_count"] += cycle_results.get("total_processed_count", 0)
                    report_results["total_groups_created"] += cycle_results.get("total_groups_created", 0)
                    report_results["total_observations_created"] += cycle_results.get("total_observations_created", 0)
                    report_results["cycle_results"].append(cycle_results)
                    
                    # Collect any cycle-level errors
                    if cycle_results.get("errors"):
                        report_results["errors"].extend(cycle_results["errors"])
                
                except Exception as e:
                    error_msg = f"Error processing cycle {cycle.cycle_id}: {str(e)}"
                    logger.error(error_msg)
                    report_results["errors"].append(error_msg)
            
            logger.info(f"Completed observation detection for report {report_id}: {report_results}")
            return report_results
            
        except Exception as e:
            logger.error(f"Error running observation detection for report {report_id}: {str(e)}")
            raise
    
    async def get_detection_status(
        self,
        phase_id: Optional[int] = None,
        cycle_id: Optional[int] = None,
        report_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get detection status for phase, cycle, or report
        
        Args:
            phase_id: Phase ID to get status for
            cycle_id: Cycle ID to get status for
            report_id: Report ID to get status for
            
        Returns:
            Detection status
        """
        try:
            if phase_id:
                # Get phase details
                phase = self.db.query(WorkflowPhase).filter(
                    WorkflowPhase.phase_id == phase_id
                ).first()
                
                if not phase:
                    raise ValueError(f"Phase {phase_id} not found")
                
                return await self.detection_service.get_detection_statistics(
                    phase_id=phase_id,
                    cycle_id=phase.cycle_id,
                    report_id=phase.report_id
                )
            
            elif cycle_id:
                # Get cycle details and aggregate phase statistics
                cycle = self.db.query(TestCycle).filter(
                    TestCycle.cycle_id == cycle_id
                ).first()
                
                if not cycle:
                    raise ValueError(f"Cycle {cycle_id} not found")
                
                phases = self.db.query(WorkflowPhase).filter(
                    WorkflowPhase.cycle_id == cycle_id
                ).all()
                
                # Aggregate statistics from all phases
                cycle_stats = {
                    "cycle_id": cycle_id,
                    "total_phases": len(phases),
                    "total_failed_executions": 0,
                    "total_failed_with_observations": 0,
                    "total_observation_groups": 0,
                    "total_observations": 0,
                    "phase_statistics": []
                }
                
                for phase in phases:
                    phase_stats = await self.detection_service.get_detection_statistics(
                        phase_id=phase.phase_id,
                        cycle_id=cycle_id,
                        report_id=phase.report_id
                    )
                    
                    cycle_stats["total_failed_executions"] += phase_stats.get("total_failed_executions", 0)
                    cycle_stats["total_failed_with_observations"] += phase_stats.get("failed_with_observations", 0)
                    cycle_stats["total_observation_groups"] += phase_stats.get("observation_groups", 0)
                    cycle_stats["total_observations"] += phase_stats.get("total_observations", 0)
                    
                    cycle_stats["phase_statistics"].append({
                        "phase_id": phase.phase_id,
                        **phase_stats
                    })
                
                # Calculate overall coverage
                if cycle_stats["total_failed_executions"] > 0:
                    cycle_stats["overall_detection_coverage"] = (
                        cycle_stats["total_failed_with_observations"] / 
                        cycle_stats["total_failed_executions"]
                    )
                else:
                    cycle_stats["overall_detection_coverage"] = 0
                
                return cycle_stats
            
            elif report_id:
                # Get report details and aggregate cycle statistics
                report = self.db.query(Report).filter(
                    Report.id == report_id
                ).first()
                
                if not report:
                    raise ValueError(f"Report {report_id} not found")
                
                cycles = self.db.query(TestCycle).filter(
                    TestCycle.report_id == report_id
                ).all()
                
                # Aggregate statistics from all cycles
                report_stats = {
                    "report_id": report_id,
                    "total_cycles": len(cycles),
                    "total_failed_executions": 0,
                    "total_failed_with_observations": 0,
                    "total_observation_groups": 0,
                    "total_observations": 0,
                    "cycle_statistics": []
                }
                
                for cycle in cycles:
                    cycle_stats = await self.get_detection_status(cycle_id=cycle.cycle_id)
                    
                    report_stats["total_failed_executions"] += cycle_stats.get("total_failed_executions", 0)
                    report_stats["total_failed_with_observations"] += cycle_stats.get("total_failed_with_observations", 0)
                    report_stats["total_observation_groups"] += cycle_stats.get("total_observation_groups", 0)
                    report_stats["total_observations"] += cycle_stats.get("total_observations", 0)
                    
                    report_stats["cycle_statistics"].append(cycle_stats)
                
                # Calculate overall coverage
                if report_stats["total_failed_executions"] > 0:
                    report_stats["overall_detection_coverage"] = (
                        report_stats["total_failed_with_observations"] / 
                        report_stats["total_failed_executions"]
                    )
                else:
                    report_stats["overall_detection_coverage"] = 0
                
                return report_stats
            
            else:
                raise ValueError("Must provide either phase_id, cycle_id, or report_id")
                
        except Exception as e:
            logger.error(f"Error getting detection status: {str(e)}")
            raise


# Utility function to create runner instance
def create_observation_detection_runner(db: Session) -> ObservationDetectionRunner:
    """Create observation detection runner instance"""
    return ObservationDetectionRunner(db)