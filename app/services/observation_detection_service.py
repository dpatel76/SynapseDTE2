"""
Observation Detection Service
Automatically detects and creates observations from failed test executions
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.database import get_db
# Observation enhanced models removed - use observation_management models
from app.models.observation_management import (
    ObservationRecord, Observation, ObservationRatingEnum,
    ObservationRecordStatus, SeverityLevel, IssueType, DetectionMethod, FrequencyEstimate
)
from app.models.planning import PlanningAttribute
from app.models.test_execution import TestExecution
from app.models.report_attribute import ReportAttribute
from app.models.lob import LOB
from app.models.workflow import WorkflowPhase
from app.models.user import User

logger = logging.getLogger(__name__)


class ObservationDetectionService:
    """Service for automatically detecting and creating observations from failed test executions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def detect_observations_from_failures(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        detection_user_id: int,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Detect failed test executions and create observations
        
        Args:
            phase_id: Test execution phase ID
            cycle_id: Test cycle ID
            report_id: Report ID
            detection_user_id: User ID for detection tracking
            batch_size: Number of test executions to process at once
            
        Returns:
            Detection results summary
        """
        logger.info(f"Starting observation detection for phase={phase_id}, cycle={cycle_id}, report={report_id}")
        
        try:
            # Get failed test executions that don't have observations yet
            failed_executions = await self._get_failed_executions_without_observations(
                phase_id, cycle_id, report_id, batch_size
            )
            
            if not failed_executions:
                logger.info("No failed test executions found without observations")
                return {
                    "processed_count": 0,
                    "groups_created": 0,
                    "observations_created": 0,
                    "errors": []
                }
            
            logger.info(f"Found {len(failed_executions)} failed test executions to process")
            
            # Group failed executions by attribute and LOB
            execution_groups = await self._group_executions_by_attribute_lob(failed_executions)
            
            results = {
                "processed_count": len(failed_executions),
                "groups_created": 0,
                "observations_created": 0,
                "errors": []
            }
            
            # Process each group
            for group_key, executions in execution_groups.items():
                try:
                    attribute_id, lob_id = group_key
                    
                    # Get or create observation group
                    observation_group = await self._get_or_create_observation_group(
                        phase_id=phase_id,
                        cycle_id=cycle_id,
                        report_id=report_id,
                        attribute_id=attribute_id,
                        lob_id=lob_id,
                        executions=executions,
                        detection_user_id=detection_user_id
                    )
                    
                    if observation_group:
                        if observation_group.id is None:  # New group created
                            results["groups_created"] += 1
                        
                        # Create individual observations
                        observations_created = await self._create_individual_observations(
                            observation_group, executions, detection_user_id
                        )
                        results["observations_created"] += observations_created
                    
                except Exception as e:
                    logger.error(f"Error processing group {group_key}: {str(e)}")
                    results["errors"].append(f"Group {group_key}: {str(e)}")
            
            # Update observation counts
            await self._update_observation_counts()
            
            self.db.commit()
            
            logger.info(f"Observation detection completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in observation detection: {str(e)}")
            self.db.rollback()
            raise
    
    async def _get_failed_executions_without_observations(
        self, 
        phase_id: int, 
        cycle_id: int, 
        report_id: int,
        batch_size: int
    ) -> List[TestExecution]:
        """Get failed test executions that don't have observations yet"""
        
        # Find test executions that failed but don't have observations
        query = self.db.query(TestExecution).filter(
            and_(
                TestExecution.phase_id == phase_id,
                TestExecution.cycle_id == cycle_id,
                TestExecution.report_id == report_id,
                TestExecution.execution_status == 'completed',
                or_(
                    TestExecution.test_result == 'fail',
                    TestExecution.test_result == 'inconclusive'
                )
            )
        ).filter(
            # Only get executions that don't have observations yet
            ~TestExecution.id.in_(
                self.db.query(Observation.test_execution_id).filter(
                    Observation.test_execution_id.isnot(None)
                )
            )
        ).limit(batch_size)
        
        return query.all()
    
    async def _group_executions_by_attribute_lob(
        self, 
        executions: List[TestExecution]
    ) -> Dict[tuple, List[TestExecution]]:
        """Group test executions by attribute and LOB combination"""
        
        groups = {}
        
        for execution in executions:
            # Extract attribute and LOB from test execution
            # This would need to be implemented based on how attributes and LOBs are stored
            # For now, we'll use placeholder logic
            
            # Get attribute_id and lob_id from the execution context
            # This might need adjustment based on actual data structure
            attribute_id = await self._extract_attribute_id(execution)
            lob_id = await self._extract_lob_id(execution)
            
            if attribute_id and lob_id:
                group_key = (attribute_id, lob_id)
                
                if group_key not in groups:
                    groups[group_key] = []
                
                groups[group_key].append(execution)
        
        return groups
    
    async def _extract_attribute_id(self, execution: TestExecution) -> Optional[int]:
        """Extract attribute ID from test execution"""
        # This would need to be implemented based on how attributes are linked to test cases
        # For now, we'll use a placeholder approach
        
        # Look for attribute information in the execution data
        if hasattr(execution, 'analysis_results') and execution.analysis_results:
            if isinstance(execution.analysis_results, dict):
                return execution.analysis_results.get('attribute_id')
        
        # Try to get from test case relationship
        # This would need actual implementation based on data structure
        return None
    
    async def _extract_lob_id(self, execution: TestExecution) -> Optional[int]:
        """Extract LOB ID from test execution"""
        # This would need to be implemented based on how LOBs are linked to test cases
        # For now, we'll use a placeholder approach
        
        # Look for LOB information in the execution data
        if hasattr(execution, 'analysis_results') and execution.analysis_results:
            if isinstance(execution.analysis_results, dict):
                return execution.analysis_results.get('lob_id')
        
        # Try to get from test case relationship
        # This would need actual implementation based on data structure
        return None
    
    async def _get_or_create_observation_group(
        self,
        phase_id: int,
        cycle_id: int,
        report_id: int,
        attribute_id: int,
        lob_id: int,
        executions: List[TestExecution],
        detection_user_id: int
    ) -> Optional[ObservationRecord]:
        """Get existing observation group or create new one"""
        
        # Check if group already exists
        existing_group = self.db.query(ObservationRecord).filter(
            and_(
                ObservationRecord.phase_id == phase_id,
                ObservationRecord.attribute_id == attribute_id,
                ObservationRecord.lob_id == lob_id
            )
        ).first()
        
        if existing_group:
            logger.info(f"Using existing observation group {existing_group.id}")
            return existing_group
        
        # Get attribute and LOB details
        attribute = self.db.query(PlanningAttribute).filter(
            PlanningAttribute.id == attribute_id
        ).first()
        
        lob = self.db.query(LOB).filter(
            LOB.lob_id == lob_id
        ).first()
        
        if not attribute or not lob:
            logger.error(f"Cannot find attribute {attribute_id} or LOB {lob_id}")
            return None
        
        # Analyze failures to determine severity and issue type
        severity_level, issue_type = await self._analyze_failure_severity_and_type(executions)
        
        # Generate group name and description
        group_name = f"{attribute.attribute_name} - {lob.lob_name} Issues"
        group_description = f"Automated observation group for {attribute.attribute_name} attribute in {lob.lob_name} LOB"
        
        # Generate issue summary
        issue_summary = await self._generate_issue_summary(executions, attribute, lob)
        
        # Create new observation group
        try:
            observation_group = ObservationRecord(
                phase_id=phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                group_name=group_name,
                group_description=group_description,
                attribute_id=attribute_id,
                lob_id=lob_id,
                observation_count=0,  # Will be updated automatically
                severity_level=severity_level.value,
                issue_type=issue_type.value,
                issue_summary=issue_summary,
                impact_description=await self._generate_impact_description(executions),
                proposed_resolution=await self._generate_proposed_resolution(executions),
                status=ObservationRecordStatus.DRAFT.value,
                detection_method=DetectionMethod.AUTO_DETECTED.value,
                detected_by=detection_user_id,
                detected_at=datetime.utcnow(),
                created_by=detection_user_id,
                updated_by=detection_user_id
            )
            
            self.db.add(observation_group)
            self.db.flush()  # Get the ID
            
            logger.info(f"Created new observation group {observation_group.id}")
            return observation_group
            
        except Exception as e:
            logger.error(f"Error creating observation group: {str(e)}")
            raise
    
    async def _create_individual_observations(
        self,
        observation_group: ObservationRecord,
        executions: List[TestExecution],
        detection_user_id: int
    ) -> int:
        """Create individual observations for each failed execution"""
        
        observations_created = 0
        
        for execution in executions:
            try:
                # Check if observation already exists for this execution
                existing_observation = self.db.query(Observation).filter(
                    Observation.test_execution_id == execution.id
                ).first()
                
                if existing_observation:
                    logger.info(f"Observation already exists for execution {execution.id}")
                    continue
                
                # Extract observation details from execution
                observation_title = await self._generate_observation_title(execution)
                observation_description = await self._generate_observation_description(execution)
                
                # Create observation
                observation = Observation(
                    group_id=observation_group.id,
                    test_execution_id=execution.id,
                    test_case_id=execution.test_case_id,
                    attribute_id=observation_group.attribute_id,
                    sample_id=await self._extract_sample_id(execution),
                    lob_id=observation_group.lob_id,
                    observation_title=observation_title,
                    observation_description=observation_description,
                    expected_value=execution.expected_value,
                    actual_value=execution.extracted_value,
                    variance_details=execution.variance_details,
                    test_result=execution.test_result,
                    evidence_files=await self._extract_evidence_files(execution),
                    supporting_documentation=await self._extract_supporting_documentation(execution),
                    confidence_level=execution.llm_confidence_score,
                    reproducible=await self._determine_reproducibility(execution),
                    frequency_estimate=await self._estimate_frequency(execution),
                    business_impact=await self._assess_business_impact(execution),
                    technical_impact=await self._assess_technical_impact(execution),
                    regulatory_impact=await self._assess_regulatory_impact(execution),
                    created_by=detection_user_id,
                    updated_by=detection_user_id
                )
                
                self.db.add(observation)
                observations_created += 1
                
                logger.info(f"Created observation for execution {execution.id}")
                
            except Exception as e:
                logger.error(f"Error creating observation for execution {execution.id}: {str(e)}")
                continue
        
        return observations_created
    
    async def _analyze_failure_severity_and_type(
        self, 
        executions: List[TestExecution]
    ) -> tuple[SeverityLevel, IssueType]:
        """Analyze failed executions to determine severity and issue type"""
        
        # Analyze execution results to determine severity
        total_executions = len(executions)
        high_confidence_failures = sum(1 for e in executions if e.llm_confidence_score and e.llm_confidence_score > 0.8)
        
        # Determine severity based on failure patterns
        if high_confidence_failures / total_executions > 0.8:
            severity_level = SeverityLevel.HIGH
        elif high_confidence_failures / total_executions > 0.5:
            severity_level = SeverityLevel.MEDIUM
        else:
            severity_level = SeverityLevel.LOW
        
        # Determine issue type based on failure patterns
        # This is a simplified approach - could be enhanced with ML/patterns
        issue_type = IssueType.DATA_QUALITY  # Default to data quality issues
        
        return severity_level, issue_type
    
    async def _generate_issue_summary(
        self, 
        executions: List[TestExecution], 
        attribute: PlanningAttribute, 
        lob: LOB
    ) -> str:
        """Generate issue summary for the observation group"""
        
        total_failures = len(executions)
        
        # Analyze common failure patterns
        failure_patterns = []
        for execution in executions:
            if execution.error_message:
                failure_patterns.append(execution.error_message)
        
        return f"Detected {total_failures} test failures for {attribute.attribute_name} in {lob.lob_name}. Common patterns include data quality issues."
    
    async def _generate_impact_description(self, executions: List[TestExecution]) -> str:
        """Generate impact description based on execution failures"""
        return f"Test execution failures detected across {len(executions)} test cases, potentially affecting data quality and compliance."
    
    async def _generate_proposed_resolution(self, executions: List[TestExecution]) -> str:
        """Generate proposed resolution based on execution failures"""
        return "Review failed test cases, validate data sources, and implement data quality controls."
    
    async def _generate_observation_title(self, execution: TestExecution) -> str:
        """Generate observation title for individual execution"""
        return f"Test failure in {execution.test_case_id}"
    
    async def _generate_observation_description(self, execution: TestExecution) -> str:
        """Generate observation description for individual execution"""
        description = f"Test case {execution.test_case_id} failed during execution."
        
        if execution.error_message:
            description += f" Error: {execution.error_message}"
        
        if execution.llm_analysis_rationale:
            description += f" Analysis: {execution.llm_analysis_rationale}"
        
        return description
    
    async def _extract_sample_id(self, execution: TestExecution) -> str:
        """Extract sample ID from execution"""
        # This would need to be implemented based on how samples are linked
        return f"sample_{execution.id}"
    
    async def _extract_evidence_files(self, execution: TestExecution) -> Optional[Dict[str, Any]]:
        """Extract evidence files from execution"""
        if hasattr(execution, 'analysis_results') and execution.analysis_results:
            if isinstance(execution.analysis_results, dict):
                return execution.analysis_results.get('evidence_files')
        return None
    
    async def _extract_supporting_documentation(self, execution: TestExecution) -> Optional[str]:
        """Extract supporting documentation from execution"""
        return execution.execution_summary
    
    async def _determine_reproducibility(self, execution: TestExecution) -> bool:
        """Determine if the issue is reproducible"""
        # Simple heuristic - issues with high confidence are more likely reproducible
        return execution.llm_confidence_score and execution.llm_confidence_score > 0.7
    
    async def _estimate_frequency(self, execution: TestExecution) -> str:
        """Estimate frequency of the issue"""
        # This would need more sophisticated logic
        return FrequencyEstimate.OCCASIONAL.value
    
    async def _assess_business_impact(self, execution: TestExecution) -> str:
        """Assess business impact of the failure"""
        return "Potential impact on data quality and regulatory compliance."
    
    async def _assess_technical_impact(self, execution: TestExecution) -> str:
        """Assess technical impact of the failure"""
        return "Technical validation failure requiring investigation."
    
    async def _assess_regulatory_impact(self, execution: TestExecution) -> str:
        """Assess regulatory impact of the failure"""
        return "May affect regulatory reporting accuracy."
    
    async def _update_observation_counts(self):
        """Update observation counts in all groups"""
        # This is handled automatically by the database trigger
        pass
    
    async def get_detection_statistics(
        self, 
        phase_id: int, 
        cycle_id: int, 
        report_id: int
    ) -> Dict[str, Any]:
        """Get detection statistics for a phase"""
        
        # Get total failed executions
        total_failed = self.db.query(TestExecution).filter(
            and_(
                TestExecution.phase_id == phase_id,
                TestExecution.cycle_id == cycle_id,
                TestExecution.report_id == report_id,
                TestExecution.execution_status == 'completed',
                or_(
                    TestExecution.test_result == 'fail',
                    TestExecution.test_result == 'inconclusive'
                )
            )
        ).count()
        
        # Get failed executions with observations
        failed_with_observations = self.db.query(TestExecution).filter(
            and_(
                TestExecution.phase_id == phase_id,
                TestExecution.cycle_id == cycle_id,
                TestExecution.report_id == report_id,
                TestExecution.execution_status == 'completed',
                or_(
                    TestExecution.test_result == 'fail',
                    TestExecution.test_result == 'inconclusive'
                )
            )
        ).filter(
            TestExecution.id.in_(
                self.db.query(Observation.test_execution_id).filter(
                    Observation.test_execution_id.isnot(None)
                )
            )
        ).count()
        
        # Get observation groups
        observation_groups = self.db.query(ObservationRecord).filter(
            ObservationRecord.phase_id == phase_id
        ).count()
        
        # Get total observations
        total_observations = self.db.query(Observation).join(
            ObservationRecord
        ).filter(
            ObservationRecord.phase_id == phase_id
        ).count()
        
        return {
            "total_failed_executions": total_failed,
            "failed_with_observations": failed_with_observations,
            "failed_without_observations": total_failed - failed_with_observations,
            "detection_coverage": failed_with_observations / total_failed if total_failed > 0 else 0,
            "observation_groups": observation_groups,
            "total_observations": total_observations
        }


# Utility function to create service instance
def create_observation_detection_service(db: Session) -> ObservationDetectionService:
    """Create observation detection service instance"""
    return ObservationDetectionService(db)