"""
Universal Metrics Service - Single source of truth for all phase metrics
Provides consistent metrics across all pages and phases based on context
"""

from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, distinct, text
from dataclasses import dataclass
import logging
import traceback

from app.models.workflow import WorkflowPhase
from app.models.data_profiling import ProfilingResult, VersionStatus as DataProfilingVersionStatus
from app.models.scoping import ScopingSubmission, ReportOwnerScopingReview, VersionStatus
from app.models.sample_selection import SampleSelectionVersion, SampleSelectionSample
from app.models.request_info import CycleReportTestCase
from app.models.test_execution import TestExecution
from app.models.user import User
from app.models.report import Report

logger = logging.getLogger(__name__)


@dataclass
class MetricsContext:
    """Context for metrics calculation"""
    cycle_id: int
    report_id: int
    user_id: Optional[int] = None
    user_role: Optional[str] = None
    lob_id: Optional[int] = None
    phase_name: Optional[str] = None


@dataclass
class UniversalMetrics:
    """Universal metrics data structure"""
    # Core metrics available across all phases
    total_attributes: int  # (1) Approved attributes from planning
    all_dq_rules: int  # (2) Total DQ rules in approved version
    approved_dq_rules: int  # (3) Report owner approved DQ rules
    scoped_attributes_pk: int  # (4a) Primary key attributes (auto-approved)
    scoped_attributes_non_pk: int  # (4b) Non-PK scoped attributes
    approved_samples: int  # (5) Report owner approved samples
    lobs_count: int  # (6) Distinct LOBs from approved samples
    data_providers_count: int  # (7) Distinct data providers
    test_cases_total: int  # (8a) Total test cases
    test_cases_passed: int  # (8b) Passed test cases
    test_cases_failed: int  # (8c) Failed test cases
    test_cases_pending: int  # (8d) Pending test cases
    
    # Computed metrics
    scoped_attributes_total: int  # PK + Non-PK
    dq_rules_approval_rate: float  # Approved / Total DQ rules
    test_execution_rate: float  # (Passed + Failed) / Total test cases
    test_pass_rate: float  # Passed / (Passed + Failed) if any executed
    
    # Metadata
    calculated_at: datetime
    context: MetricsContext


class UniversalMetricsService:
    """Service for calculating universal metrics across all phases"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_phase_safe(self, cycle_id: int, report_id: int, phase_name: str) -> Optional[Any]:
        """Safely get workflow phase avoiding enum issues"""
        try:
            result = await self.db.execute(
                text("""
                    SELECT phase_id, cycle_id, report_id, phase_name, status, phase_data
                    FROM workflow_phases 
                    WHERE cycle_id = :cycle_id 
                    AND report_id = :report_id 
                    AND phase_name::text = :phase_name
                """),
                {"cycle_id": cycle_id, "report_id": report_id, "phase_name": phase_name}
            )
            return result.first()
        except Exception as e:
            logger.error(f"Error querying phase {phase_name}: {e}")
            return None
    
    async def get_metrics(self, context: MetricsContext) -> UniversalMetrics:
        """Get universal metrics based on context"""
        logger.info(f"Calculating universal metrics for cycle {context.cycle_id}, report {context.report_id}")
        
        try:
            # Calculate all metrics in parallel where possible
            metrics = await self._calculate_all_metrics(context)
            
            # Add computed metrics
            metrics.scoped_attributes_total = metrics.scoped_attributes_pk + metrics.scoped_attributes_non_pk
        except Exception as e:
            logger.error(f"Error calculating metrics, rolling back: {e}")
            # Rollback the transaction to clear the error state
            await self.db.rollback()
            # Return default metrics
            return UniversalMetrics(
                total_attributes=0,
                all_dq_rules=0,
                approved_dq_rules=0,
                scoped_attributes_pk=0,
                scoped_attributes_non_pk=0,
                approved_samples=0,
                lobs_count=0,
                data_providers_count=0,
                test_cases_total=0,
                test_cases_passed=0,
                test_cases_failed=0,
                test_cases_pending=0,
                scoped_attributes_total=0,
                dq_rules_approval_rate=0.0,
                test_execution_rate=0.0,
                test_pass_rate=0.0,
                calculated_at=datetime.utcnow(),
                context=context
            )
        
        # Calculate rates
        metrics.dq_rules_approval_rate = (
            (metrics.approved_dq_rules / metrics.all_dq_rules * 100) 
            if metrics.all_dq_rules > 0 else 0.0
        )
        
        executed_tests = metrics.test_cases_passed + metrics.test_cases_failed
        metrics.test_execution_rate = (
            (executed_tests / metrics.test_cases_total * 100)
            if metrics.test_cases_total > 0 else 0.0
        )
        
        metrics.test_pass_rate = (
            (metrics.test_cases_passed / executed_tests * 100)
            if executed_tests > 0 else 0.0
        )
        
        metrics.calculated_at = datetime.utcnow()
        metrics.context = context
        
        logger.info(f"Universal metrics calculated: {metrics}")
        return metrics
    
    async def _calculate_all_metrics(self, context: MetricsContext) -> UniversalMetrics:
        """Calculate all metrics"""
        
        # Initialize defaults
        total_attributes = 0
        all_dq_rules = 0
        approved_dq_rules = 0
        scoped_pk = 0
        scoped_non_pk = 0
        approved_samples = 0
        lobs_count = 0
        data_providers = 0
        test_metrics = {'total': 0, 'passed': 0, 'failed': 0, 'pending': 0}
        
        try:
            # (1) Total Attributes - Approved during planning
            total_attributes = await self._get_total_attributes(context)
        except Exception as e:
            logger.error(f"Error in _get_total_attributes: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        try:
            # (2) & (3) DQ Rules metrics
            all_dq_rules, approved_dq_rules = await self._get_dq_rules_metrics(context)
        except Exception as e:
            logger.error(f"Error in _get_dq_rules_metrics: {e}")
        
        try:
            # (4) Scoped Attributes (PK/Non-PK)
            scoped_pk, scoped_non_pk = await self._get_scoped_attributes(context)
        except Exception as e:
            logger.error(f"Error in _get_scoped_attributes: {e}")
        
        try:
            # (5) & (6) & (7) Sample Selection metrics
            approved_samples, lobs_count, data_providers = await self._get_sample_metrics(context)
        except Exception as e:
            logger.error(f"Error in _get_sample_metrics: {e}")
        
        try:
            # (8) Test Cases metrics
            test_metrics = await self._get_test_case_metrics(context)
        except Exception as e:
            logger.error(f"Error in _get_test_case_metrics: {e}")
        
        return UniversalMetrics(
            total_attributes=total_attributes,
            all_dq_rules=all_dq_rules,
            approved_dq_rules=approved_dq_rules,
            scoped_attributes_pk=scoped_pk,
            scoped_attributes_non_pk=scoped_non_pk,
            approved_samples=approved_samples,
            lobs_count=lobs_count,
            data_providers_count=data_providers,
            test_cases_total=test_metrics['total'],
            test_cases_passed=test_metrics['passed'],
            test_cases_failed=test_metrics['failed'],
            test_cases_pending=test_metrics['pending'],
            scoped_attributes_total=0,  # Will be computed
            dq_rules_approval_rate=0.0,  # Will be computed
            test_execution_rate=0.0,  # Will be computed
            test_pass_rate=0.0,  # Will be computed
            calculated_at=datetime.utcnow(),
            context=context
        )
    
    async def _get_total_attributes(self, context: MetricsContext) -> int:
        """(1) Get total attributes from planning phase"""
        try:
            # Get planning phase
            planning_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Planning')
            if not planning_phase:
                return 0
                
            # Count all active attributes from planning phase
            result = await self.db.execute(
                text("""
                    SELECT COUNT(*) as count
                    FROM cycle_report_planning_attributes
                    WHERE phase_id = :phase_id
                    AND is_active = true
                """),
                {"phase_id": planning_phase.phase_id}
            )
            row = result.first()
            return row.count if row else 0
        except Exception as e:
            logger.error(f"Error querying total attributes: {e}")
            return 0
    
    async def _get_dq_rules_metrics(self, context: MetricsContext) -> tuple[int, int]:
        """(2) & (3) Get DQ rules metrics from approved profiling version"""
        # Get the Data Profiling phase
        profiling_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Data Profiling')
        
        if not profiling_phase:
            return 0, 0
        
        # Get approved profiling version (latest approved version)
        # Use text query to avoid enum issues
        approved_version_query = await self.db.execute(
            text("""
                SELECT version_id FROM cycle_report_data_profiling_rule_versions
                WHERE phase_id = :phase_id
                AND version_status::text = 'approved'
                ORDER BY version_number DESC
                LIMIT 1
            """),
            {"phase_id": profiling_phase.phase_id}
        )
        approved_version_row = approved_version_query.first()
        
        if not approved_version_row:
            return 0, 0
            
        approved_version_id = approved_version_row.version_id
        
        # Count all rules in the approved version
        all_rules_query = await self.db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM cycle_report_data_profiling_rules
                WHERE version_id = :version_id
            """),
            {"version_id": approved_version_id}
        )
        all_rules_row = all_rules_query.first()
        all_rules = all_rules_row.count if all_rules_row else 0
        
        # Count report owner approved rules
        approved_rules_query = await self.db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM cycle_report_data_profiling_rules
                WHERE version_id = :version_id
                AND report_owner_decision = 'approved'
            """),
            {"version_id": approved_version_id}
        )
        approved_rules_row = approved_rules_query.first()
        approved_rules = approved_rules_row.count if approved_rules_row else 0
        
        return all_rules, approved_rules
    
    async def _get_scoped_attributes(self, context: MetricsContext) -> tuple[int, int]:
        """(4) Get scoped attributes split by PK/Non-PK from approved scoping"""
        # Get the Scoping phase first
        scoping_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Scoping')
        
        if not scoping_phase:
            return 0, 0
        
        # Get the latest approved scoping version
        # Use text query to avoid enum issues
        scoping_version_query = await self.db.execute(
            text("""
                SELECT version_id FROM cycle_report_scoping_versions
                WHERE phase_id = :phase_id
                AND version_status::text = 'approved'
                ORDER BY version_number DESC
                LIMIT 1
            """),
            {"phase_id": scoping_phase.phase_id}
        )
        scoping_version = scoping_version_query.first()
        
        if not scoping_version:
            return 0, 0
        
        # Count PK and Non-PK scoped attributes based on tester decisions in approved scoping version
        # PK attributes are auto-accepted
        pk_query = await self.db.execute(
            text("""
                SELECT COUNT(DISTINCT sa.planning_attribute_id) as pk_count
                FROM cycle_report_scoping_attributes sa
                JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
                WHERE sa.version_id = :version_id
                AND sa.tester_decision = 'accept'
                AND pa.is_primary_key = true
            """),
            {"version_id": scoping_version.version_id}
        )
        pk_row = pk_query.first()
        pk_count = pk_row.pk_count if pk_row else 0
        
        # Non-PK attributes
        non_pk_query = await self.db.execute(
            text("""
                SELECT COUNT(DISTINCT sa.planning_attribute_id) as non_pk_count
                FROM cycle_report_scoping_attributes sa
                JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
                WHERE sa.version_id = :version_id
                AND sa.tester_decision = 'accept'
                AND pa.is_primary_key = false
            """),
            {"version_id": scoping_version.version_id}
        )
        non_pk_row = non_pk_query.first()
        non_pk_count = non_pk_row.non_pk_count if non_pk_row else 0
        
        return pk_count, non_pk_count
    
    async def _get_sample_metrics(self, context: MetricsContext) -> tuple[int, int, int]:
        """(5) & (6) & (7) Get sample selection metrics"""
        # Get the Sample Selection phase
        # Use text query to avoid enum issues
        sample_phase_query = await self.db.execute(
            text("""
                SELECT phase_id FROM workflow_phases 
                WHERE cycle_id = :cycle_id 
                AND report_id = :report_id 
                AND phase_name::text = 'Sample Selection'
            """),
            {"cycle_id": context.cycle_id, "report_id": context.report_id}
        )
        sample_phase_row = sample_phase_query.first()
        sample_phase = sample_phase_row if sample_phase_row else None
        
        if not sample_phase:
            return 0, 0, 0
        
        phase_id = sample_phase.phase_id
        
        # Get latest approved version
        # Use text query to avoid enum issues
        approved_version_query = await self.db.execute(
            text("""
                SELECT version_id FROM cycle_report_sample_selection_versions
                WHERE phase_id = :phase_id
                AND version_status::text = 'approved'
                ORDER BY version_number DESC
                LIMIT 1
            """),
            {"phase_id": phase_id}
        )
        approved_version_row = approved_version_query.first()
        
        if not approved_version_row:
            return 0, 0, 0
            
        approved_version_id = approved_version_row.version_id
        
        # Get approved samples count and LOB info
        samples_stats_query = await self.db.execute(
            text("""
                SELECT 
                    COUNT(*) as approved_count,
                    COUNT(DISTINCT lob_id) as lob_count
                FROM cycle_report_sample_selection_samples
                WHERE version_id = :version_id
                AND report_owner_decision = 'approved'
            """),
            {"version_id": approved_version_id}
        )
        stats_row = samples_stats_query.first()
        
        if stats_row:
            approved_count = stats_row.approved_count or 0
            lobs_count = stats_row.lob_count or 0
        else:
            approved_count = 0
            lobs_count = 0
            
        # Get data providers count
        # Need to join with workflow_phases to get cycle_id and report_id
        data_providers_query = await self.db.execute(
            text("""
                SELECT COUNT(DISTINCT a.data_owner_id) as count
                FROM cycle_report_data_owner_lob_mapping a
                JOIN workflow_phases p ON a.phase_id = p.phase_id
                WHERE p.cycle_id = :cycle_id
                AND p.report_id = :report_id
                AND a.data_owner_id IS NOT NULL
            """),
            {"cycle_id": context.cycle_id, "report_id": context.report_id}
        )
        providers_row = data_providers_query.first()
        data_providers = providers_row.count if providers_row else 0
        
        return approved_count, lobs_count, data_providers
    
    async def _get_test_case_metrics(self, context: MetricsContext) -> Dict[str, int]:
        """(8) Get test case metrics"""
        # Get Request for Information phase
        rfi_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Request for Information')
        if not rfi_phase:
            return {'total': 0, 'passed': 0, 'failed': 0, 'pending': 0}
            
        # Get total test cases using text query
        total_query = await self.db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM cycle_report_test_cases
                WHERE phase_id = :phase_id
            """),
            {"phase_id": rfi_phase.phase_id}
        )
        total_row = total_query.first()
        total = total_row.count if total_row else 0
        
        # Get test execution results using text query
        results_query = await self.db.execute(
            text("""
                SELECT test_result, COUNT(*) as count
                FROM cycle_report_test_execution_results
                WHERE phase_id = :phase_id
                AND is_latest_execution = true
                GROUP BY test_result
            """),
            {"phase_id": rfi_phase.phase_id}
        )
        
        passed = 0
        failed = 0
        pending = total  # Start with all as pending
        
        for row in results_query:
            result = row.test_result
            count = row.count
            if result == 'Pass':
                passed = count
                pending -= count
            elif result == 'Fail':
                failed = count
                pending -= count
            elif result is not None:  # Other results also reduce pending
                pending -= count
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pending': max(0, pending)  # Ensure non-negative
        }
    
    async def get_phase_specific_metrics(
        self, 
        context: MetricsContext
    ) -> Dict[str, Any]:
        """Get phase-specific additional metrics beyond the universal ones"""
        if not context.phase_name:
            return {}
        
        # For now, return simplified metrics based on phase
        # This avoids the complex queries that are causing enum issues
        if context.phase_name == "Data Provider ID":
            return await self._get_data_owner_metrics(context)
        elif context.phase_name == "Sample Selection":
            return await self._get_sample_selection_metrics(context)
        elif context.phase_name == "Data Profiling":
            return await self._get_data_profiling_metrics(context)
        elif context.phase_name == "Scoping":
            return await self._get_scoping_metrics(context)
        elif context.phase_name == "Test Execution":
            return await self._get_test_execution_metrics(context)
        elif context.phase_name == "Observations" or context.phase_name == "Observation Management":
            return await self._get_observation_metrics(context)
        
        return {}
    
    async def _get_data_owner_metrics(self, context: MetricsContext) -> Dict[str, Any]:
        """Get Data Owner specific metrics with simplified queries"""
        try:
            # Get Planning phase for attributes
            planning_phase = await self.db.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == context.cycle_id,
                        WorkflowPhase.report_id == context.report_id,
                        WorkflowPhase.phase_name == 'Planning'
                    )
                )
            )
            planning_phase = planning_phase.scalar_one_or_none()
            
            total_attributes = 0
            scoped_attributes = 0
            
            if planning_phase:
                # Count total approved attributes using text query
                attr_count_query = await self.db.execute(
                    text("""
                        SELECT COUNT(*) as count
                        FROM cycle_report_planning_attributes
                        WHERE phase_id = :phase_id
                        AND is_active = true
                    """),
                    {"phase_id": planning_phase.phase_id}
                )
                attr_row = attr_count_query.first()
                total_attributes = attr_row.count if attr_row else 0
                
                # Count scoped non-PK attributes from scoping decisions
                # First get the scoping phase
                scoping_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Scoping')
                
                if scoping_phase:
                    # Count scoped non-PK attributes based on tester decisions in approved scoping version
                    scoped_query = text("""
                        SELECT COUNT(DISTINCT sa.planning_attribute_id) as scoped_count
                        FROM cycle_report_scoping_attributes sa
                        JOIN cycle_report_scoping_versions sv ON sa.version_id = sv.version_id
                        JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
                        WHERE sv.phase_id = :scoping_phase_id
                        AND sv.version_status::text = 'approved'
                        AND sa.tester_decision = 'accept'
                        AND pa.is_primary_key = false
                    """)
                    result = await self.db.execute(scoped_query, {"scoping_phase_id": scoping_phase.phase_id})
                    row = result.first()
                    scoped_attributes = row.scoped_count if row else 0
                else:
                    scoped_attributes = 0
            
            # Get Sample Selection phase for samples and LOBs
            sample_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Sample Selection')
            
            total_samples = 0
            total_lobs = 0
            
            if sample_phase:
                # Get approved samples count - direct query avoiding version status
                samples_query = """
                    SELECT COUNT(DISTINCT s.sample_id) as sample_count,
                           COUNT(DISTINCT s.lob_id) as lob_count
                    FROM cycle_report_sample_selection_samples s
                    JOIN cycle_report_sample_selection_versions v ON s.version_id = v.version_id
                    WHERE v.phase_id = :phase_id
                    AND s.report_owner_decision = 'approved'
                    AND v.version_status::text = 'approved'
                """
                result = await self.db.execute(
                    text(samples_query),
                    {"phase_id": sample_phase.phase_id}
                )
                row = result.first()
                if row:
                    total_samples = row.sample_count or 0
                    total_lobs = row.lob_count or 0
            
            # Get data provider counts
            assigned_data_providers = 0
            total_data_providers = 0
            data_owner_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Data Provider ID')
            
            if data_owner_phase:
                try:
                    # Count distinct data owners assigned
                    assigned_query = await self.db.execute(
                        text("""
                            SELECT COUNT(DISTINCT data_owner_id) as count
                            FROM cycle_report_data_owner_lob_mapping
                            WHERE phase_id = :phase_id
                            AND data_owner_id IS NOT NULL
                        """),
                        {"phase_id": data_owner_phase.phase_id}
                    )
                    assigned_row = assigned_query.first()
                    assigned_data_providers = assigned_row.count if assigned_row else 0
                except Exception as e:
                    logger.warning(f"Error counting data owner assignments: {e}")
                    assigned_data_providers = 0
                
                # Get total potential data providers based on LOBs
                # Count distinct combinations of (attribute, lob) that need assignments
                try:
                    total_query = await self.db.execute(
                        text("""
                            SELECT COUNT(DISTINCT CONCAT(attribute_id, '-', lob_id)) as count
                            FROM cycle_report_data_owner_lob_mapping
                            WHERE phase_id = :phase_id
                        """),
                        {"phase_id": data_owner_phase.phase_id}
                    )
                    total_row = total_query.first()
                    total_data_providers = total_row.count if total_row else 0
                except Exception as e:
                    logger.warning(f"Error counting total data provider needs: {e}")
                    # Fallback to counting all data owners in the system
                    total_data_providers = await self._get_total_data_providers()
            
            return {
                "total_attributes": total_attributes,
                "scoped_attributes": scoped_attributes,
                "total_samples": total_samples,
                "total_lobs": total_lobs,
                "assigned_data_providers": assigned_data_providers,
                "total_data_providers": total_data_providers
            }
            
        except Exception as e:
            logger.error(f"Error in _get_data_owner_metrics: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return empty metrics on error to prevent page crashes
            return {
                "total_attributes": 0,
                "scoped_attributes": 0,
                "total_samples": 0,
                "total_lobs": 0,
                "assigned_data_providers": 0,
                "total_data_providers": 0
            }
    
    async def _get_sample_selection_metrics(self, context: MetricsContext) -> Dict[str, Any]:
        """Get Sample Selection specific metrics"""
        try:
            # Get basic metrics from universal calculation
            universal = await self.get_metrics(context)
            
            return {
                "total_attributes": universal.scoped_attributes_total,
                "approved_samples": universal.approved_samples,
                "total_lobs": universal.lobs_count
            }
        except Exception as e:
            logger.error(f"Error in _get_sample_selection_metrics: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return empty dict to let individual endpoints handle defaults
            return {}
    
    async def _get_data_profiling_metrics(self, context: MetricsContext) -> Dict[str, Any]:
        """Get Data Profiling specific metrics"""
        # For now, return empty - can be implemented later
        return {}
    
    async def _get_scoping_metrics(self, context: MetricsContext) -> Dict[str, Any]:
        """Get Scoping specific metrics"""
        try:
            # Get CDE attributes count (attributes marked with is_cde flag)
            planning_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Planning')
            
            cde_attributes_count = 0
            historical_issues_count = 0
            
            if planning_phase:
                # Count CDE attributes
                cde_query = await self.db.execute(
                    text("""
                        SELECT COUNT(*) as count
                        FROM cycle_report_planning_attributes
                        WHERE phase_id = :phase_id
                        AND is_cde = true
                        AND is_active = true
                    """),
                    {"phase_id": planning_phase.phase_id}
                )
                cde_row = cde_query.first()
                cde_attributes_count = cde_row.count if cde_row else 0
                
                # Count attributes with historical issues
                historical_query = await self.db.execute(
                    text("""
                        SELECT COUNT(*) as count
                        FROM cycle_report_planning_attributes
                        WHERE phase_id = :phase_id
                        AND has_issues = true
                        AND is_active = true
                    """),
                    {"phase_id": planning_phase.phase_id}
                )
                historical_row = historical_query.first()
                historical_issues_count = historical_row.count if historical_row else 0
            
            # Get attributes with anomalies (composite DQ score < 95%)
            # Use the same approach as in the data_profiling endpoint
            attributes_with_anomalies = 0
            
            if planning_phase:
                try:
                    from app.services.data_quality_service import DataQualityService
                    
                    # Get all attributes from planning
                    attributes_query = await self.db.execute(
                        text("""
                            SELECT id, attribute_name
                            FROM cycle_report_planning_attributes
                            WHERE phase_id = :phase_id
                            AND is_active = true
                        """),
                        {"phase_id": planning_phase.phase_id}
                    )
                    
                    for attr_row in attributes_query:
                        attr_id = attr_row.id
                        # Calculate composite DQ score for this attribute
                        dq_data = await DataQualityService.calculate_composite_dq_score(
                            self.db,
                            context.cycle_id, 
                            context.report_id, 
                            attr_id
                        )
                        # The result is a dict with 'composite_score' key
                        if dq_data and dq_data.get('composite_score', 100) < 95:
                            attributes_with_anomalies += 1
                            
                except Exception as e:
                    logger.warning(f"Error calculating anomalies: {e}")
                    attributes_with_anomalies = 0
            
            return {
                'cde_attributes_count': cde_attributes_count,
                'attributes_with_anomalies': attributes_with_anomalies,
                'historical_issues_count': historical_issues_count
            }
            
        except Exception as e:
            logger.error(f"Error getting scoping metrics: {e}")
            return {}
    
    async def _get_total_data_providers(self) -> int:
        """Get total count of users with Data Owner role"""
        query = select(func.count(User.user_id)).where(
            User.role == 'Data Owner'
        )
        result = await self.db.scalar(query)
        return result or 0
    
    async def _get_test_execution_metrics(self, context: MetricsContext) -> Dict[str, Any]:
        """Get Test Execution specific metrics"""
        try:
            # Get total attributes from planning phase
            total_attributes = await self._get_total_attributes(context)
            
            # Get scoped attributes (PK + Non-PK) from scoping phase
            scoped_pk, scoped_non_pk = await self._get_scoped_attributes(context)
            scoped_attributes = scoped_pk + scoped_non_pk
            
            # Get approved samples
            # Get Sample Selection phase
            sample_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Sample Selection')
            
            if sample_phase:
                # Get approved samples count using correct model and field names
                samples_query = await self.db.execute(
                    text("""
                        SELECT COUNT(DISTINCT s.sample_id) as sample_count
                        FROM cycle_report_sample_selection_samples s
                        JOIN cycle_report_sample_selection_versions v ON s.version_id = v.version_id
                        WHERE v.phase_id = :phase_id
                        AND s.report_owner_decision = 'approved'
                        AND v.version_status::text = 'approved'
                    """),
                    {"phase_id": sample_phase.phase_id}
                )
                sample_row = samples_query.first()
                total_samples = sample_row.sample_count if sample_row else 0
            else:
                total_samples = 0
            
            # Get LOBs (usually one per report)
            total_lobs = 1
            
            # Get data providers
            # Get Data Owner phase to get data provider count
            data_owner_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Data Provider ID')
            
            if data_owner_phase:
                # Count distinct data owners assigned
                providers_query = await self.db.execute(
                    text("""
                        SELECT COUNT(DISTINCT data_owner_id) as count
                        FROM cycle_report_data_owner_lob_mapping
                        WHERE phase_id = :phase_id
                        AND data_owner_id IS NOT NULL
                    """),
                    {"phase_id": data_owner_phase.phase_id}
                )
                providers_row = providers_query.first()
                total_data_providers = providers_row.count if providers_row else 0
            else:
                total_data_providers = 0
            
            return {
                'total_attributes': total_attributes,
                'scoped_attributes': scoped_attributes,
                'total_samples': total_samples,
                'total_lobs': total_lobs,
                'total_data_providers': total_data_providers
            }
        except Exception as e:
            logger.error(f"Error getting test execution metrics: {e}")
            return {}
    
    async def _get_observation_metrics(self, context: MetricsContext) -> Dict[str, Any]:
        """Get Observation Management specific metrics"""
        try:
            # Get total attributes from planning phase
            total_attributes = await self._get_total_attributes(context)
            
            # Get scoped attributes (PK + Non-PK) from scoping phase
            scoped_pk, scoped_non_pk = await self._get_scoped_attributes(context)
            scoped_attributes = scoped_pk + scoped_non_pk
            
            # Get approved samples
            # Get Sample Selection phase
            sample_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Sample Selection')
            
            if sample_phase:
                # Get approved samples count using correct model and field names
                samples_query = await self.db.execute(
                    text("""
                        SELECT COUNT(DISTINCT s.sample_id) as sample_count
                        FROM cycle_report_sample_selection_samples s
                        JOIN cycle_report_sample_selection_versions v ON s.version_id = v.version_id
                        WHERE v.phase_id = :phase_id
                        AND s.report_owner_decision = 'approved'
                        AND v.version_status::text = 'approved'
                    """),
                    {"phase_id": sample_phase.phase_id}
                )
                sample_row = samples_query.first()
                total_samples = sample_row.sample_count if sample_row else 0
            else:
                total_samples = 0
            
            # Get observations count
            total_observations = 0
            approved_observations = 0
            
            try:
                # Get Observations phase
                obs_phase = await self._get_phase_safe(context.cycle_id, context.report_id, 'Observations')
                
                if obs_phase:
                    # Count total observations
                    obs_count_query = await self.db.execute(
                        text("""
                            SELECT COUNT(*) as count
                            FROM cycle_report_observation_mgmt_observation_records
                            WHERE phase_id = :phase_id
                        """),
                        {"phase_id": obs_phase.phase_id}
                    )
                    obs_count_row = obs_count_query.first()
                    total_observations = obs_count_row.count if obs_count_row else 0
                    
                    # Count approved observations (using the varchar value)
                    approved_count_query = await self.db.execute(
                        text("""
                            SELECT COUNT(*) as count
                            FROM cycle_report_observation_mgmt_observation_records
                            WHERE phase_id = :phase_id
                            AND approval_status = 'Approved'
                        """),
                        {"phase_id": obs_phase.phase_id}
                    )
                    approved_row = approved_count_query.first()
                    approved_observations = approved_row.count if approved_row else 0
            except Exception as e:
                logger.error(f"Error counting observations: {e}")
                total_observations = 0
                approved_observations = 0
            
            return {
                'total_attributes': total_attributes,
                'scoped_attributes': scoped_attributes,
                'total_samples': total_samples,
                'total_observations': total_observations,
                'approved_observations': approved_observations
            }
        except Exception as e:
            logger.error(f"Error getting observation metrics: {e}")
            return {}


def get_universal_metrics_service(db: AsyncSession) -> UniversalMetricsService:
    """Factory function to get metrics service instance"""
    return UniversalMetricsService(db)