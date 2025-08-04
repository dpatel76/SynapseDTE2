"""
Comprehensive Data Collection Service for Test Report Generation
Collects and aggregates data from all phases for comprehensive reporting
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.models.workflow import WorkflowPhase
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.user import User
from app.models.lob import LOB
from app.models.report_attribute import ReportAttribute
from app.models.planning import PlanningPDEMapping
from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule
from app.models.scoping import ScopingVersion, ScopingAttribute
from app.models.sample_selection import SampleSelectionVersion, SampleSelectionSample
from app.models.request_info import CycleReportTestCase, TestCaseSourceEvidence
from app.models.test_execution import TestExecution
from app.models.observation_management import ObservationRecord
from app.core.logging import get_logger

logger = get_logger(__name__)


class ComprehensiveDataCollectionService:
    """Service to collect comprehensive data from all phases"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def collect_all_phase_data(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect comprehensive data from all phases"""
        logger.info(f"Collecting comprehensive data for cycle {cycle_id}, report {report_id}")
        
        # Get basic report and cycle information
        report_info = await self._get_report_info(cycle_id, report_id)
        stakeholders = await self._get_stakeholders(cycle_id, report_id)
        
        # Collect data from each phase
        phase_data = {
            "report_info": report_info,
            "stakeholders": stakeholders,
            "planning": await self._collect_planning_data(cycle_id, report_id),
            "data_profiling": await self._collect_data_profiling_data(cycle_id, report_id),
            "scoping": await self._collect_scoping_data(cycle_id, report_id),
            "sample_selection": await self._collect_sample_selection_data(cycle_id, report_id),
            "request_info": await self._collect_request_info_data(cycle_id, report_id),
            "test_execution": await self._collect_test_execution_data(cycle_id, report_id),
            "observation_management": await self._collect_observation_data(cycle_id, report_id),
            "execution_metrics": await self._collect_execution_metrics(cycle_id, report_id)
        }
        
        # Add summary statistics
        phase_data["summary"] = self._calculate_summary_statistics(phase_data)
        
        return phase_data
    
    async def _get_report_info(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Get basic report information"""
        # Get report details
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await self.db.execute(report_query)
        report = report_result.scalar_one()
        
        # Get cycle details
        cycle_query = select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        cycle_result = await self.db.execute(cycle_query)
        cycle = cycle_result.scalar_one()
        
        # Get LOB information
        lob_query = select(LOB).where(LOB.lob_id == report.lob_id)
        lob_result = await self.db.execute(lob_query)
        lob = lob_result.scalar_one()
        
        return {
            "report_id": report.report_id,
            "report_name": report.report_name,
            "description": report.description,
            "frequency": report.frequency,
            "regulatory_framework": report.regulation,
            "risk_rating": report.risk_rating if hasattr(report, 'risk_rating') else "Not specified",
            "lob_name": lob.lob_name,
            "lob_description": lob.lob_name,  # LOB doesn't have lob_description, using lob_name
            "cycle_name": cycle.cycle_name,
            "cycle_year": self._extract_year_from_cycle_name(cycle.cycle_name),
            "cycle_quarter": self._extract_quarter_from_cycle_name(cycle.cycle_name),
            "cycle_start_date": cycle.start_date.isoformat() if cycle.start_date else None,
            "cycle_end_date": cycle.end_date.isoformat() if cycle.end_date else None
        }
    
    async def _get_stakeholders(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Get all stakeholders involved in the test cycle"""
        stakeholders = {}
        
        # Get report owner
        report_query = select(Report).options(selectinload(Report.owner)).where(Report.report_id == report_id)
        report_result = await self.db.execute(report_query)
        report = report_result.scalar_one()
        
        if report.owner:
            stakeholders["report_owner"] = {
                "user_id": report.owner.user_id,
                "name": f"{report.owner.first_name} {report.owner.last_name}",
                "email": report.owner.email,
                "role": "Report Owner"
            }
        
        # Get tester from cycle assignment
        tester_query = text("""
            SELECT u.user_id, u.first_name, u.last_name, u.email
            FROM cycle_reports cr
            JOIN users u ON cr.tester_id = u.user_id
            WHERE cr.cycle_id = :cycle_id AND cr.report_id = :report_id
        """)
        tester_result = await self.db.execute(tester_query, {"cycle_id": cycle_id, "report_id": report_id})
        tester = tester_result.first()
        
        if tester:
            stakeholders["tester"] = {
                "user_id": tester.user_id,
                "name": f"{tester.first_name} {tester.last_name}",
                "email": tester.email,
                "role": "Tester"
            }
        
        # Get data providers and executives by LOB
        # Query users with Data Owner role for the report's LOB
        data_owner_query = select(User).where(
            and_(
                User.role == "Data Owner",
                User.lob_id == report.lob_id,
                User.is_active == True
            )
        )
        data_owner_result = await self.db.execute(data_owner_query)
        data_owner = data_owner_result.scalar_one_or_none()
        
        if data_owner:
            stakeholders["data_provider"] = {
                "user_id": data_owner.user_id,
                "name": f"{data_owner.first_name} {data_owner.last_name}",
                "email": data_owner.email,
                "role": "Data Owner"
            }
        
        # Query users with Data Executive role for the report's LOB
        data_executive_query = select(User).where(
            and_(
                User.role == "Data Executive",
                User.lob_id == report.lob_id,
                User.is_active == True
            )
        )
        data_executive_result = await self.db.execute(data_executive_query)
        data_executive = data_executive_result.scalar_one_or_none()
        
        if data_executive:
            stakeholders["data_executive"] = {
                "user_id": data_executive.user_id,
                "name": f"{data_executive.first_name} {data_executive.last_name}",
                "email": data_executive.email,
                "role": "Data Executive"
            }
        
        # Get LOB name for context
        lob_query = select(LOB).where(LOB.lob_id == report.lob_id)
        lob_result = await self.db.execute(lob_query)
        lob = lob_result.scalar_one_or_none()
        
        if lob:
            stakeholders["lob_info"] = {
                "lob_id": lob.lob_id,
                "lob_name": lob.lob_name
            }
        
        return stakeholders
    
    async def _collect_planning_data(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect planning phase data"""
        # Get all attributes
        attrs_query = select(ReportAttribute).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True
            )
        ).order_by(ReportAttribute.line_item_number)
        
        attrs_result = await self.db.execute(attrs_query)
        attributes = attrs_result.scalars().all()
        
        # Calculate statistics
        total_attributes = len(attributes)
        cde_count = sum(1 for a in attributes if a.cde_flag)
        pk_count = sum(1 for a in attributes if a.is_primary_key)
        issues_count = sum(1 for a in attributes if a.historical_issues_flag)
        approved_count = sum(1 for a in attributes if a.approval_status == 'approved')
        
        # Planning doesn't use versions - return empty list
        versions = []
        
        # Format attribute data for table
        attribute_table = []
        for attr in attributes:
            attribute_table.append({
                "line_item_number": attr.line_item_number,
                "attribute_name": attr.attribute_name,
                "llm_description": attr.description,  # ReportAttribute has description, not llm_description
                "mdrm_code": attr.mdrm,  # ReportAttribute has mdrm, not mdrm_code
                "mandatory_flag": attr.mandatory_flag,
                "is_cde": attr.cde_flag,  # ReportAttribute has cde_flag, not is_cde
                "is_primary_key": attr.is_primary_key,
                "has_issues": attr.historical_issues_flag,  # ReportAttribute has historical_issues_flag, not has_issues
                "approval_status": attr.approval_status,
                "approval_date": attr.approved_at.isoformat() if attr.approved_at else None
            })
        
        return {
            "summary": {
                "total_attributes": total_attributes,
                "cde_count": cde_count,
                "pk_count": pk_count,
                "issues_count": issues_count,
                "approved_count": approved_count,
                "approval_rate": (approved_count / total_attributes * 100) if total_attributes > 0 else 0
            },
            "versions": [
                {
                    "version_number": v.version_number,
                    "version_status": v.version_status,
                    "total_attributes": v.total_attributes,
                    "included_attributes": v.included_attributes,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "approved_at": v.approved_at.isoformat() if v.approved_at else None
                }
                for v in versions
            ],
            "attributes": attribute_table
        }
    
    async def _collect_data_profiling_data(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect data profiling phase data"""
        # Get profiling rule versions for version history
        versions_query = select(DataProfilingRuleVersion).options(
            selectinload(DataProfilingRuleVersion.submitted_by),
            selectinload(DataProfilingRuleVersion.approved_by)
        ).join(
            WorkflowPhase, DataProfilingRuleVersion.phase_id == WorkflowPhase.phase_id
        ).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Data Profiling'
            )
        ).order_by(DataProfilingRuleVersion.version_number)
        
        versions_result = await self.db.execute(versions_query)
        versions = versions_result.scalars().all()
        
        # Get LATEST APPROVED version only
        latest_approved_version = None
        for version in reversed(versions):  # Start from latest
            if version.version_status == 'approved':
                latest_approved_version = version
                break
        
        # Get profiling rules ONLY from latest approved version
        if latest_approved_version:
            rules_query = select(ProfilingRule).where(
                ProfilingRule.version_id == latest_approved_version.version_id
            )
            rules_result = await self.db.execute(rules_query)
            rules = rules_result.scalars().all()
        else:
            rules = []
        
        # Calculate statistics ONLY from latest approved version
        total_rules = len(rules)
        
        # Rules are approved if report owner approved them (in latest approved version)
        approved_rules = [r for r in rules if r.report_owner_decision == 'approved']
        
        # Check if rules have been executed by looking for execution results
        executed_rules = []
        rules_with_anomalies = []
        
        for rule in rules:
            # A rule is considered executed if it has execution result data
            if hasattr(rule, 'execution_result') and rule.execution_result:
                executed_rules.append(rule)
                if rule.execution_result.get('has_anomalies'):
                    rules_with_anomalies.append(rule)
        
        # Get unique attributes covered (only from latest approved version)
        covered_attributes = set()
        for rule in rules:
            if rule.attribute_id:
                covered_attributes.add(rule.attribute_id)
        
        # Format submission history
        submission_history = []
        for version in versions:
            submission_history.append({
                "version": version.version_number,
                "attributes_submitted": version.total_rules,  # DataProfilingRuleVersion has total_rules, not total_attributes
                "submission_datetime": version.created_at.isoformat() if version.created_at else None,
                "report_owner_decision": version.version_status,
                "decision_datetime": version.approved_at.isoformat() if version.approved_at else None,
                "duration_hours": self._calculate_duration(version.created_at, version.approved_at),
                "feedback": version.rejection_reason if hasattr(version, 'rejection_reason') else getattr(version, 'report_owner_feedback', None)
            })
        
        # Format approved and executed rules (from latest approved version only)
        approved_executed_rules = []
        for rule in executed_rules:
            if rule.report_owner_decision == 'approved':
                approved_executed_rules.append({
                    "attribute_name": rule.attribute_name,
                    "dq_dimension": rule.rule_type,
                    "rule_description": rule.rule_description,
                    "records_processed": rule.execution_result.get('records_processed', 0) if rule.execution_result else 0,
                    "dq_result": "Pass" if not rule.execution_result.get('has_anomalies') else "Anomalies Found"
                })
        
        # Format unapproved rules (from latest approved version only)
        unapproved_rules = []
        for rule in rules:
            if rule.report_owner_decision != 'approved':
                unapproved_rules.append({
                    "attribute_name": rule.attribute_name,
                    "dq_dimension": rule.rule_type,
                    "rule_description": rule.rule_description,
                    "rationale": rule.llm_rationale
                })
        
        # Format detailed rules table for latest approved version
        latest_version_rules = []
        for rule in rules:
            latest_version_rules.append({
                "attribute_name": rule.attribute_name,
                "rule_type": rule.rule_type,
                "rule_description": rule.rule_description,
                "report_owner_decision": rule.report_owner_decision or "Pending",
                "executed": hasattr(rule, 'execution_result') and rule.execution_result is not None,
                "execution_status": "Pass" if (hasattr(rule, 'execution_result') and rule.execution_result and not rule.execution_result.get('has_anomalies')) else "Fail" if (hasattr(rule, 'execution_result') and rule.execution_result) else "Not Executed"
            })
        
        return {
            "summary": {
                "total_attributes": len(covered_attributes),
                "total_rules_generated": total_rules,
                "rules_approved": len(approved_rules),
                "attributes_with_approved_rules": len(set(r.attribute_id for r in approved_rules if r.attribute_id)),
                "rules_executed": len(executed_rules),
                "rules_with_anomalies": len(rules_with_anomalies),
                "attributes_with_executed_rules": len(set(r.attribute_id for r in executed_rules if r.attribute_id)),
                "latest_version_number": latest_approved_version.version_number if latest_approved_version else 0
            },
            "versions": [
                {
                    "version_number": v.version_number,
                    "version_status": v.version_status,
                    "total_rules": v.total_rules,
                    "approved_rules": v.approved_rules,
                    "rejected_rules": v.rejected_rules,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "submitted_at": v.submitted_at.isoformat() if v.submitted_at else None,
                    "approved_at": v.approved_at.isoformat() if v.approved_at else None,
                    "submitted_by": f"{v.submitted_by.first_name} {v.submitted_by.last_name}" if v.submitted_by else None,
                    "approved_by": f"{v.approved_by.first_name} {v.approved_by.last_name}" if v.approved_by else None,
                    "rejection_reason": v.rejection_reason if hasattr(v, 'rejection_reason') else getattr(v, 'report_owner_feedback', None)
                }
                for v in versions
            ],
            "submission_history": submission_history,
            "approved_executed_rules": approved_executed_rules,
            "unapproved_rules": unapproved_rules,
            "latest_version_rules": latest_version_rules
        }
    
    async def _collect_scoping_data(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect scoping phase data"""
        # Get scoping versions for version history
        versions_query = select(ScopingVersion).options(
            selectinload(ScopingVersion.submitted_by),
            selectinload(ScopingVersion.approved_by)
        ).join(
            WorkflowPhase, ScopingVersion.phase_id == WorkflowPhase.phase_id
        ).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Scoping'
            )
        ).order_by(ScopingVersion.version_number)
        
        versions_result = await self.db.execute(versions_query)
        versions = versions_result.scalars().all()
        
        # Get LATEST APPROVED version only
        latest_approved_version = None
        for version in reversed(versions):  # Start from latest
            if version.version_status == 'approved':
                latest_approved_version = version
                break
        
        # Get scoping attributes ONLY from latest approved version
        if latest_approved_version:
            scoping_attrs_query = select(ScopingAttribute).where(
                ScopingAttribute.version_id == latest_approved_version.version_id
            )
            scoping_attrs_result = await self.db.execute(scoping_attrs_query)
            scoping_attrs = scoping_attrs_result.scalars().all()
        else:
            scoping_attrs = []
        
        # Get base attributes for additional info
        attrs_query = select(ReportAttribute).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True
            )
        )
        
        attrs_result = await self.db.execute(attrs_query)
        base_attrs = {a.id: a for a in attrs_result.scalars().all()}
        
        # Calculate correct statistics - total attributes including PKs
        total_attributes = len(base_attrs)
        
        # Count PK attributes from base attributes
        pk_attributes = [a for a in base_attrs.values() if a.is_primary_key]
        pk_count = len(pk_attributes)
        
        # Calculate non-PK attributes
        non_pk_count = total_attributes - pk_count
        
        # From scoping attributes (latest approved version only)
        selected_attrs = [a for a in scoping_attrs if a.is_scoped_in]
        approved_attrs = [a for a in selected_attrs if a.status == 'approved']
        
        # Total in scope = PK attributes + approved scoped non-PK attributes
        total_in_scope = pk_count + len(approved_attrs)
        
        # Format submission history
        submission_history = []
        for version in versions:
            submission_history.append({
                "version": version.version_number,
                "non_pk_attributes_submitted": version.total_attributes,
                "submission_datetime": version.created_at.isoformat() if version.created_at else None,
                "report_owner_decision": version.version_status,
                "decision_datetime": version.approved_at.isoformat() if version.approved_at else None,
                "duration_hours": self._calculate_duration(version.created_at, version.approved_at),
                "feedback": version.rejection_reason if hasattr(version, 'rejection_reason') else getattr(version, 'report_owner_feedback', None)
            })
        
        # Format approved scoping table
        approved_scoping = []
        for attr in selected_attrs:
            if attr.status == 'approved':
                base_attr = base_attrs.get(attr.attribute_id)
                if base_attr:
                    approved_scoping.append({
                        "line_number": base_attr.line_item_number,
                        "attribute_name": base_attr.attribute_name,
                        "is_cde": base_attr.cde_flag,
                        "has_issues": base_attr.historical_issues_flag,
                        "is_primary_key": base_attr.is_primary_key,
                        "llm_description": base_attr.description,
                        "mdrm_code": base_attr.mdrm,
                        "llm_data_type": base_attr.data_type,
                        "mandatory_flag": base_attr.mandatory_flag,
                        "llm_risk_score": attr.llm_risk_score,
                        "llm_rationale": attr.llm_rationale
                    })
        
        # Format not included table
        not_included = []
        for attr in scoping_attrs:
            if not attr.is_scoped_in:
                base_attr = base_attrs.get(attr.attribute_id)
                if base_attr:
                    not_included.append({
                        "line_number": base_attr.line_item_number,
                        "attribute_name": base_attr.attribute_name,
                        "is_cde": base_attr.cde_flag,
                        "has_issues": base_attr.historical_issues_flag,
                        "is_primary_key": base_attr.is_primary_key,
                        "llm_description": base_attr.description,
                        "mdrm_code": base_attr.mdrm,
                        "llm_data_type": base_attr.data_type,
                        "mandatory_flag": base_attr.mandatory_flag,
                        "llm_risk_score": attr.llm_risk_score,
                        "llm_rationale": attr.llm_rationale
                    })
        
        # Format detailed scoping tables for latest approved version
        pk_attributes_table = []
        for attr in pk_attributes:
            pk_attributes_table.append({
                "line_number": attr.line_item_number,
                "attribute_name": attr.attribute_name,
                "llm_description": attr.description,
                "mdrm_code": attr.mdrm,
                "mandatory_flag": attr.mandatory_flag,
                "is_cde": attr.cde_flag,
                "status": "Automatically Included (PK)"
            })
        
        return {
            "summary": {
                "total_attributes": total_attributes,
                "pk_attributes": pk_count,
                "total_non_pk_attributes": non_pk_count,
                "non_pk_attributes_selected": len(selected_attrs),
                "non_pk_attributes_approved": len(approved_attrs),
                "total_in_scope": total_in_scope,
                "selection_rate": (len(selected_attrs) / non_pk_count * 100) if non_pk_count > 0 else 0,
                "approval_rate": (len(approved_attrs) / len(selected_attrs) * 100) if selected_attrs else 0,
                "latest_version_number": latest_approved_version.version_number if latest_approved_version else 0
            },
            "versions": [
                {
                    "version_number": v.version_number,
                    "version_status": v.version_status,
                    "total_attributes": v.total_attributes,
                    "included_attributes": v.scoped_attributes,
                    "excluded_attributes": v.declined_attributes,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "submitted_at": v.submitted_at.isoformat() if v.submitted_at else None,
                    "approved_at": v.approved_at.isoformat() if v.approved_at else None,
                    "submitted_by": f"{v.submitted_by.first_name} {v.submitted_by.last_name}" if v.submitted_by else None,
                    "approved_by": f"{v.approved_by.first_name} {v.approved_by.last_name}" if v.approved_by else None,
                    "rejection_reason": v.rejection_reason if hasattr(v, 'rejection_reason') else getattr(v, 'report_owner_feedback', None)
                }
                for v in versions
            ],
            "submission_history": submission_history,
            "pk_attributes": pk_attributes_table,
            "approved_scoping": approved_scoping,
            "not_included": not_included
        }
    
    async def _collect_sample_selection_data(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect sample selection phase data"""
        # Get sample selection versions for version history
        versions_query = select(SampleSelectionVersion).options(
            selectinload(SampleSelectionVersion.submitted_by),
            selectinload(SampleSelectionVersion.approved_by)
        ).join(
            WorkflowPhase, SampleSelectionVersion.phase_id == WorkflowPhase.phase_id
        ).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Sample Selection'
            )
        ).order_by(SampleSelectionVersion.version_number)
        
        versions_result = await self.db.execute(versions_query)
        versions = versions_result.scalars().all()
        
        # Get LATEST APPROVED version only
        latest_approved_version = None
        for version in reversed(versions):  # Start from latest
            if version.version_status == 'approved':
                latest_approved_version = version
                break
        
        # Get samples ONLY from latest approved version
        if latest_approved_version:
            samples_query = select(SampleSelectionSample).where(
                SampleSelectionSample.version_id == latest_approved_version.version_id
            )
            samples_result = await self.db.execute(samples_query)
            samples = samples_result.scalars().all()
        else:
            samples = []
        
        # Calculate statistics (from latest approved version only)
        total_samples = len(samples)
        approved_samples = [s for s in samples if s.report_owner_decision == 'approved']
        
        # Group by category
        samples_by_category = {}
        for sample in samples:
            category = sample.sample_category or 'Uncategorized'
            if category not in samples_by_category:
                samples_by_category[category] = []
            samples_by_category[category].append(sample)
        
        # Format detailed sample data for latest approved version
        approved_samples_table = []
        for sample in approved_samples:
            approved_samples_table.append({
                "sample_id": str(sample.sample_id),
                "entity_id": sample.sample_identifier,
                "sample_category": sample.sample_category or "Uncategorized",
                "lob_id": sample.lob_id,
                "date_selected": sample.created_at.isoformat()[:10] if sample.created_at else None,
                "report_owner_decision": sample.report_owner_decision,
                "sample_data": sample.sample_data
            })
        
        # Format submission history
        submission_history = []
        for version in versions:
            submission_history.append({
                "version": version.version_number,
                "target_sample_size": version.target_sample_size,
                "actual_sample_size": version.actual_sample_size,
                "submission_datetime": version.created_at.isoformat() if version.created_at else None,
                "report_owner_decision": version.version_status,
                "decision_datetime": version.approved_at.isoformat() if version.approved_at else None,
                "duration_hours": self._calculate_duration(version.created_at, version.approved_at),
                "feedback": version.rejection_reason if hasattr(version, 'rejection_reason') else getattr(version, 'report_owner_feedback', None)
            })
        
        return {
            "summary": {
                "total_samples": total_samples,
                "approved_samples": len(approved_samples),
                "sample_categories": list(samples_by_category.keys()),
                "sampling_methodology": latest_approved_version.selection_criteria.get('methodology', 'Not specified') if latest_approved_version and latest_approved_version.selection_criteria else "Not specified",
                "sample_period": latest_approved_version.selection_criteria.get('period', 'Not specified') if latest_approved_version and latest_approved_version.selection_criteria else "Not specified",
                "latest_version_number": latest_approved_version.version_number if latest_approved_version else 0
            },
            "sample_distribution": {
                category: len(samples_list)
                for category, samples_list in samples_by_category.items()
            },
            "versions": [
                {
                    "version_number": v.version_number,
                    "version_status": v.version_status,
                    "target_sample_size": v.target_sample_size,
                    "actual_sample_size": v.actual_sample_size,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "submitted_at": v.submitted_at.isoformat() if v.submitted_at else None,
                    "approved_at": v.approved_at.isoformat() if v.approved_at else None,
                    "submitted_by": f"{v.submitted_by.first_name} {v.submitted_by.last_name}" if v.submitted_by else None,
                    "approved_by": f"{v.approved_by.first_name} {v.approved_by.last_name}" if v.approved_by else None,
                    "rejection_reason": v.rejection_reason if hasattr(v, 'rejection_reason') else getattr(v, 'report_owner_feedback', None)
                }
                for v in versions
            ],
            "submission_history": submission_history,
            "approved_samples": approved_samples_table
        }
    
    async def _collect_request_info_data(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect request info phase data"""
        # Get test cases through phase relationship
        test_cases_query = select(CycleReportTestCase).join(
            WorkflowPhase, CycleReportTestCase.phase_id == WorkflowPhase.phase_id
        ).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Request Info'
            )
        )
        
        test_cases_result = await self.db.execute(test_cases_query)
        test_cases = test_cases_result.scalars().all()
        
        # Get evidence for these test cases
        if test_cases:
            evidence_query = select(TestCaseSourceEvidence).where(
                TestCaseSourceEvidence.test_case_id.in_([tc.id for tc in test_cases])
            )
            
            evidence_result = await self.db.execute(evidence_query)
            evidence = evidence_result.scalars().all()
        else:
            evidence = []
        
        return {
            "summary": {
                "total_test_cases": len(test_cases),
                "test_cases_with_evidence": len(set(e.test_case_id for e in evidence)) if evidence else 0,
                "total_evidence_collected": len(evidence),
                "evidence_collection_methods": ["Document Request", "Database Query", "System Screenshot"]
            }
        }
    
    async def _collect_test_execution_data(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect test execution phase data"""
        # Get test executions through phase relationship
        executions_query = select(TestExecution).join(
            WorkflowPhase, TestExecution.phase_id == WorkflowPhase.phase_id
        ).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Test Execution',
                TestExecution.is_latest_execution == True
            )
        )
        
        executions_result = await self.db.execute(executions_query)
        executions = executions_result.scalars().all()
        
        # Calculate statistics
        total_tests = len(executions)
        passed_tests = [e for e in executions if e.test_result == 'Pass']
        failed_tests = [e for e in executions if e.test_result == 'Fail']
        
        return {
            "summary": {
                "total_test_cases": total_tests,
                "passed_tests": len(passed_tests),
                "failed_tests": len(failed_tests),
                "pass_rate": (len(passed_tests) / total_tests * 100) if total_tests > 0 else 0,
                "execution_methods": ["Manual Testing", "Automated Validation", "Evidence Review"]
            },
            "test_results_by_attribute": self._group_tests_by_attribute(executions)
        }
    
    async def _collect_observation_data(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect observation management phase data"""
        # Get observations through phase relationship
        observations_query = select(ObservationRecord).join(
            WorkflowPhase, ObservationRecord.phase_id == WorkflowPhase.phase_id
        ).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Observations'
            )
        )
        
        observations_result = await self.db.execute(observations_query)
        observations = observations_result.scalars().all()
        
        # Group by severity and status
        by_severity = {
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
            "INFORMATIONAL": []
        }
        
        by_status = {
            "Approved": [],
            "Rejected": [],
            "In Remediation": [],
            "Resolved": []
        }
        
        for obs in observations:
            severity = obs.severity or "MEDIUM"
            if severity in by_severity:
                by_severity[severity].append(obs)
            
            status = obs.status or "Detected"
            if status in by_status:
                by_status[status].append(obs)
        
        return {
            "summary": {
                "total_observations": len(observations),
                "high_severity": len(by_severity["HIGH"]),
                "medium_severity": len(by_severity["MEDIUM"]),
                "low_severity": len(by_severity["LOW"]),
                "informational": len(by_severity["INFORMATIONAL"]),
                "resolved_observations": len(by_status["Resolved"]),
                "resolution_rate": (len(by_status["Resolved"]) / len(observations) * 100) if observations else 0
            },
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_status": {k: len(v) for k, v in by_status.items()}
        }
    
    async def _collect_execution_metrics(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect execution metrics across all phases"""
        # Get all workflow phases
        phases_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id
            )
        ).order_by(WorkflowPhase.phase_order)
        
        phases_result = await self.db.execute(phases_query)
        phases = phases_result.scalars().all()
        
        # Calculate phase durations
        phase_metrics = []
        total_duration = timedelta()
        
        for phase in phases:
            if phase.actual_start_date and phase.actual_end_date:
                duration = phase.actual_end_date - phase.actual_start_date
                total_duration += duration
                
                phase_metrics.append({
                    "phase_name": phase.phase_name,
                    "started_at": phase.actual_start_date.isoformat(),
                    "completed_at": phase.actual_end_date.isoformat(),
                    "duration_hours": duration.total_seconds() / 3600,
                    "duration_days": duration.days
                })
        
        # Get version counts per phase
        version_counts = await self._get_version_counts(cycle_id, report_id)
        
        return {
            "total_cycle_duration_days": total_duration.days,
            "total_cycle_duration_hours": total_duration.total_seconds() / 3600,
            "phase_durations": phase_metrics,
            "version_counts": version_counts,
            "efficiency_metrics": {
                "average_phase_duration_hours": (total_duration.total_seconds() / 3600 / len(phases)) if phases else 0,
                "phases_completed": len([p for p in phases if p.state == 'Complete']),
                "phases_in_progress": len([p for p in phases if p.state == 'In Progress'])
            }
        }
    
    def _calculate_duration(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate duration in hours between two timestamps"""
        if start_time and end_time:
            delta = end_time - start_time
            return round(delta.total_seconds() / 3600, 2)
        return 0.0
    
    def _group_tests_by_attribute(self, executions: List[TestExecution]) -> Dict[str, Any]:
        """Group test execution results by attribute"""
        by_attribute = {}
        
        for execution in executions:
            attr_name = execution.attribute_name or "Unknown"
            if attr_name not in by_attribute:
                by_attribute[attr_name] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }
            
            by_attribute[attr_name]["total"] += 1
            if execution.test_result == "Pass":
                by_attribute[attr_name]["passed"] += 1
            else:
                by_attribute[attr_name]["failed"] += 1
        
        return by_attribute
    
    async def _get_version_counts(self, cycle_id: int, report_id: int) -> Dict[str, int]:
        """Get version counts for each phase"""
        version_counts = {}
        
        # Planning doesn't use versions
        version_counts["Planning"] = 0
        
        # Data Profiling versions
        profiling_result = await self.db.execute(
            select(func.count(DataProfilingRuleVersion.version_id)).join(
                WorkflowPhase, DataProfilingRuleVersion.phase_id == WorkflowPhase.phase_id
            ).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Data Profiling'
                )
            )
        )
        profiling_count = profiling_result.scalar()
        version_counts["Data Profiling"] = profiling_count or 0
        
        # Scoping versions
        scoping_result = await self.db.execute(
            select(func.count(ScopingVersion.version_id)).join(
                WorkflowPhase, ScopingVersion.phase_id == WorkflowPhase.phase_id
            ).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Scoping'
                )
            )
        )
        scoping_count = scoping_result.scalar()
        version_counts["Scoping"] = scoping_count or 0
        
        return version_counts
    
    def _calculate_summary_statistics(self, phase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall summary statistics"""
        return {
            "total_attributes_tested": phase_data["planning"]["summary"]["total_attributes"],
            "attributes_in_scope": phase_data["scoping"]["summary"]["non_pk_attributes_approved"],
            "test_cases_executed": phase_data["test_execution"]["summary"]["total_test_cases"],
            "overall_pass_rate": phase_data["test_execution"]["summary"]["pass_rate"],
            "total_observations": phase_data["observation_management"]["summary"]["total_observations"],
            "high_risk_findings": phase_data["observation_management"]["summary"]["high_severity"],
            "cycle_duration_days": phase_data["execution_metrics"]["total_cycle_duration_days"]
        }
    
    def _extract_year_from_cycle_name(self, cycle_name: str) -> int:
        """Extract year from cycle name (e.g., '2024 Q1' -> 2024)"""
        try:
            import re
            match = re.search(r'(\d{4})', cycle_name)
            if match:
                return int(match.group(1))
        except:
            pass
        return datetime.now().year
    
    def _extract_quarter_from_cycle_name(self, cycle_name: str) -> int:
        """Extract quarter from cycle name (e.g., '2024 Q1' -> 1)"""
        try:
            import re
            match = re.search(r'Q(\d)', cycle_name)
            if match:
                return int(match.group(1))
        except:
            pass
        return 1