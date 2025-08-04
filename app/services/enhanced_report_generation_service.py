"""
Enhanced Report Generation Service
Generates comprehensive test report content with all phase details
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_report import TestReportGeneration
from app.services.comprehensive_data_collection_service import ComprehensiveDataCollectionService
from app.core.logging import get_logger

logger = get_logger(__name__)


class EnhancedReportGenerationService:
    """Service to generate comprehensive test report sections"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data_service = ComprehensiveDataCollectionService(db)
    
    async def generate_comprehensive_report(
        self, 
        phase_id: int, 
        cycle_id: int, 
        report_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Generate comprehensive test report with all sections"""
        logger.info(f"Generating comprehensive report for cycle {cycle_id}, report {report_id}")
        
        # Create or get generation record
        generation = await self._get_or_create_generation(phase_id, cycle_id, report_id)
        generation.start_generation(user_id)
        await self.db.commit()
        
        try:
            # Collect all phase data
            all_data = await self.data_service.collect_all_phase_data(cycle_id, report_id)
            
            # Generate each section as dictionary
            sections = {
                "executive_summary": await self._generate_executive_summary_dict(phase_id, cycle_id, report_id, all_data),
                "stakeholders": await self._generate_stakeholders_dict(phase_id, cycle_id, report_id, all_data),
                "planning_phase": await self._generate_planning_dict(phase_id, cycle_id, report_id, all_data),
                "data_profiling_phase": await self._generate_data_profiling_dict(phase_id, cycle_id, report_id, all_data),
                "scoping_phase": await self._generate_scoping_dict(phase_id, cycle_id, report_id, all_data),
                "sample_selection_phase": await self._generate_sample_selection_dict(phase_id, cycle_id, report_id, all_data),
                "request_info_phase": await self._generate_request_info_dict(phase_id, cycle_id, report_id, all_data),
                "test_execution_phase": await self._generate_test_execution_dict(phase_id, cycle_id, report_id, all_data),
                "observation_management_phase": await self._generate_observation_dict(phase_id, cycle_id, report_id, all_data),
                "execution_metrics": await self._generate_execution_metrics_dict(phase_id, cycle_id, report_id, all_data)
            }
            
            # Update generation status
            generation.complete_generation(
                total_sections=len(sections),
                sections_completed=len(sections)
            )
            
            await self.db.commit()
            
            logger.info(f"Successfully generated {len(sections)} sections")
            
            return {
                "generation": generation,
                "comprehensive_data": all_data,
                "sections": sections,
                "generation_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "generated_by": user_id,
                    "total_sections": len(sections),
                    "phase_id": phase_id
                }
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to generate report: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            generation.fail_generation(str(e))
            await self.db.commit()
            raise
    
    async def _get_or_create_generation(
        self, 
        phase_id: int, 
        cycle_id: int, 
        report_id: int
    ) -> TestReportGeneration:
        """Get or create generation record"""
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(TestReportGeneration).where(
                TestReportGeneration.phase_id == phase_id
            )
        )
        generation = result.scalar_one_or_none()
        
        if not generation:
            generation = TestReportGeneration(
                phase_id=phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                status='pending',
                total_sections=0,
                sections_completed=0,
                generated_by=1  # Default user ID, will be updated in start_generation
            )
            self.db.add(generation)
        
        return generation
    
    async def _generate_executive_summary_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary section"""
        report_info = data["report_info"]
        summary = data["summary"]
        scoping_data = data.get("scoping", {})
        sample_data = data.get("sample_selection", {})
        test_execution = data.get("test_execution", {})
        
        # Calculate correct metrics
        total_attributes = data["planning"]["summary"]["total_attributes"]
        scoped_attributes = scoping_data.get("summary", {}).get("attributes_approved", 0)
        total_samples = sample_data.get("summary", {}).get("approved_samples", 0)
        test_cases = test_execution.get("summary", {}).get("total_test_cases", 0)
        pass_rate = test_execution.get("summary", {}).get("pass_rate", 0)
        
        # Generate qualitative commentary
        qualitative_commentary = self._generate_executive_commentary(data)
        
        # Generate plain English explanation
        plain_english_explanation = (
            f"This report summarizes the comprehensive testing performed on the {report_info['report_name']} "
            f"regulatory report for the {report_info['cycle_quarter']}th quarter of {report_info['cycle_year']} testing cycle. "
            f"This report contains detailed commercial real estate loan data that gets reported to the Federal Reserve "
            f"for stress testing purposes."
        )
        
        # Generate "What Actually Happened" commentary
        what_happened = self._generate_what_happened_executive(data)
        
        content = {
            "plain_english_explanation": plain_english_explanation,
            "qualitative_assessment": qualitative_commentary,
            "what_actually_happened": what_happened,
            "summary": f"This comprehensive test report documents the testing activities for the {report_info['report_name']} report "
                      f"during {report_info['cycle_name']} ({report_info['cycle_year']} Q{report_info['cycle_quarter']}). "
                      f"The testing lifecycle encompassed {total_attributes} total attributes, with {scoped_attributes} "
                      f"attributes approved for detailed testing based on risk assessment and regulatory requirements. "
                      f"A total of {total_samples} samples were selected and {test_cases} test cases were executed "
                      f"with an overall pass rate of {pass_rate:.1f}%.",
            "content": {
                "report_details": {
                    "name": report_info["report_name"],
                    "description": report_info["description"],
                    "frequency": report_info["frequency"],
                    "regulatory_framework": report_info["regulatory_framework"],
                    "lob": report_info["lob_name"]
                },
                "testing_summary": {
                    "total_attributes": total_attributes,
                    "scoped_attributes": scoped_attributes,
                    "total_samples": total_samples,
                    "test_cases_executed": test_cases,
                    "overall_pass_rate": f"{pass_rate:.1f}%",
                    "cycle_duration_days": summary["cycle_duration_days"]
                },
                "key_findings": {
                    "total_observations": summary["total_observations"],
                    "high_risk_findings": summary["high_risk_findings"],
                    "resolution_status": "In Progress"
                }
            },
            "metrics": {
                "attributes_tested": summary["total_attributes_tested"],
                "test_pass_rate": summary["overall_pass_rate"],
                "total_observations": summary["total_observations"],
                "cycle_duration": summary["cycle_duration_days"]
            },
            "charts": [
                {
                    "type": "pie_chart",
                    "title": "Test Results Distribution",
                    "data": {
                        "labels": ["Passed", "Failed"],
                        "values": [
                            summary["test_cases_executed"] * summary["overall_pass_rate"] / 100,
                            summary["test_cases_executed"] * (100 - summary["overall_pass_rate"]) / 100
                        ]
                    }
                },
                {
                    "type": "bar_chart",
                    "title": "Observations by Severity",
                    "data": {
                        "labels": ["High", "Medium", "Low"],
                        "values": [
                            data["observation_management"]["summary"]["high_severity"],
                            data["observation_management"]["summary"]["medium_severity"],
                            data["observation_management"]["summary"]["low_severity"]
                        ]
                    }
                }
            ]
        }
        
        return {
            "section_title": "Executive Summary",
            "section_order": 1,
            "content": content
        }
    
    async def _generate_stakeholders_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate stakeholders section"""
        stakeholders = data["stakeholders"]
        
        # Format stakeholder table
        stakeholder_table = []
        
        if "report_owner" in stakeholders:
            owner = stakeholders["report_owner"]
            stakeholder_table.append([
                "Report Owner",
                owner["name"],
                owner["email"],
                "Overall report accountability"
            ])
        
        if "tester" in stakeholders:
            tester = stakeholders["tester"]
            stakeholder_table.append([
                "Tester",
                tester["name"],
                tester["email"],
                "Test execution and validation"
            ])
        
        # Add LOB assignments
        for lob_assignment in stakeholders.get("lob_assignments", []):
            if lob_assignment["data_provider"]:
                dp = lob_assignment["data_provider"]
                stakeholder_table.append([
                    f"Data Provider - {lob_assignment['lob_name']}",
                    dp["name"],
                    dp["email"],
                    "Data provision and clarification"
                ])
            
            if lob_assignment["data_executive"]:
                de = lob_assignment["data_executive"]
                stakeholder_table.append([
                    f"Data Executive - {lob_assignment['lob_name']}",
                    de["name"],
                    de["email"],
                    "Executive oversight and approval"
                ])
        
        content = {
            "summary": "Key stakeholders involved in the test cycle",
            "tables": [
                {
                    "title": "Stakeholder Assignments",
                    "headers": ["Role", "Name", "Email", "Responsibility"],
                    "rows": stakeholder_table
                }
            ]
        }
        
        return {
            "section_title": "Stakeholders",
            "section_order": 2,
            "content": content
        }
    
    async def _generate_planning_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate planning phase section"""
        planning = data["planning"]
        
        # Format version history commentary
        version_commentary = []
        for i, version in enumerate(planning["versions"]):
            if i == 0:
                version_commentary.append(
                    f"Version {version['version_number']}: Tester reviewed {version['total_attributes']} attributes "
                    f"and included {version['included_attributes']} attributes for initial planning submission."
                )
            else:
                version_commentary.append(
                    f"Version {version['version_number']}: Based on feedback, tester updated planning to include "
                    f"{version['included_attributes']} attributes and resubmitted for approval."
                )
        
        # Sort attributes: Primary Keys first, then CDE, then Issues, then by line item number
        sorted_attributes = sorted(planning["attributes"], key=lambda x: (
            not x.get("is_primary_key", False),  # PK first (False sorts before True when negated)
            not x.get("is_cde", False),          # Then CDE
            not x.get("has_issues", False),      # Then Issues
            x.get("line_item_number", 999999)   # Finally by line item number
        ))
        
        # Format attribute table - show ALL attributes
        attribute_rows = []
        for attr in sorted_attributes:
            attribute_rows.append([
                attr["line_item_number"],
                attr["attribute_name"],
                attr["llm_description"] or "-",
                attr["mdrm_code"] or "-",
                attr["mandatory_flag"],
                "✓" if attr["is_cde"] else "",
                "✓" if attr["is_primary_key"] else "",
                "✓" if attr["has_issues"] else "",
                attr["approval_status"].title()
            ])
        
        # Generate "What Actually Happened" commentary
        what_happened = (
            f"During the planning phase, we analyzed all {planning['summary']['total_attributes']} data attributes "
            f"in the FR Y-14M Schedule D.1 report to understand each commercial real estate loan data point, "
            f"its source, and criticality. This comprehensive inventory forms the foundation for our risk-based "
            f"testing approach.\n\n"
            f"Key Finding: The report has relatively few critical elements - only {planning['summary']['cde_count']} CDE "
            f"out of {planning['summary']['total_attributes']} attributes ({(planning['summary']['cde_count']/planning['summary']['total_attributes']*100):.1f}%), "
            f"suggesting most fields are informational rather than calculation-critical."
        )
        
        content = {
            "summary": f"Planning phase analysis of {planning['summary']['total_attributes']} attributes with "
                      f"{planning['summary']['cde_count']} CDE fields, {planning['summary']['pk_count']} primary keys, "
                      f"and {planning['summary']['issues_count']} attributes with issues identified. "
                      f"{planning['summary']['approved_count']} attributes were approved during planning.",
            "what_actually_happened": what_happened,
            "content": {
                "version_history": version_commentary,
                "statistics": {
                    "total_attributes": planning["summary"]["total_attributes"],
                    "cde_attributes": planning["summary"]["cde_count"],
                    "primary_keys": planning["summary"]["pk_count"],
                    "attributes_with_issues": planning["summary"]["issues_count"],
                    "approved_attributes": planning["summary"]["approved_count"],
                    "approval_rate": f"{planning['summary']['approval_rate']:.1f}%"
                }
            },
            "tables": [
                {
                    "title": "Attribute Planning Details",
                    "headers": ["Line #", "Attribute Name", "LLM Description", "MDRM Code", 
                               "M/C/O", "CDE", "PK", "Issues", "Approval"],
                    "rows": attribute_rows
                }
            ],
            "metrics": planning["summary"]
        }
        
        return {
            "section_title": "Planning Phase",
            "section_order": 3,
            "content": content
        }
    
    async def _generate_data_profiling_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate data profiling phase section"""
        profiling = data["data_profiling"]
        
        # Format version history table
        version_history_rows = []
        for version in profiling["versions"]:
            version_history_rows.append([
                f"Version {version['version_number']}",
                version["total_rules"],
                version["created_at"][:10] if version["created_at"] else "-",
                version["submitted_at"][:10] if version["submitted_at"] else "-",
                version["version_status"].title(),
                version["approved_at"][:10] if version["approved_at"] else "-",
                version["submitted_by"] or "-",
                version["approved_by"] or "-",
                version["rejection_reason"] or "-"
            ])
        
        # Format submission history table (legacy format for compatibility)
        submission_rows = []
        for submission in profiling["submission_history"]:
            submission_rows.append([
                f"Version {submission['version']}",
                submission["attributes_submitted"],
                submission["submission_datetime"][:10] if submission["submission_datetime"] else "-",
                submission["report_owner_decision"],
                submission["decision_datetime"][:10] if submission["decision_datetime"] else "-",
                f"{submission['duration_hours']:.1f} hours",
                submission["feedback"] or "-"
            ])
        
        # Format approved rules table
        approved_rules_rows = []
        for i, rule in enumerate(profiling["approved_executed_rules"], 1):
            approved_rules_rows.append([
                i,
                rule["attribute_name"],
                rule["dq_dimension"],
                rule["rule_description"],
                rule["records_processed"],
                rule["dq_result"]
            ])
        
        # Format unapproved rules table
        unapproved_rules_rows = []
        for i, rule in enumerate(profiling["unapproved_rules"], 1):
            unapproved_rules_rows.append([
                i,
                rule["attribute_name"],
                rule["dq_dimension"],
                rule["rule_description"],
                rule["rationale"] or "-"
            ])
        
        # Format latest version rules table
        latest_version_rules_rows = []
        for i, rule in enumerate(profiling.get("latest_version_rules", []), 1):
            latest_version_rules_rows.append([
                i,
                rule["attribute_name"],
                rule["rule_type"],
                rule["rule_description"],
                rule["report_owner_decision"],
                "✓" if rule["executed"] else "✗",
                rule["execution_status"]
            ])
        
        content = {
            "summary": f"Data profiling phase (Version {profiling['summary'].get('latest_version_number', 'N/A')}) "
                      f"generated {profiling['summary']['total_rules_generated']} rules "
                      f"covering {profiling['summary']['total_attributes']} attributes. "
                      f"{profiling['summary']['rules_approved']} rules were approved covering "
                      f"{profiling['summary']['attributes_with_approved_rules']} attributes. "
                      f"{profiling['summary']['rules_executed']} rules were executed with "
                      f"{profiling['summary']['rules_with_anomalies']} identifying data quality issues.",
            "tables": [
                {
                    "title": "Version History and Approval Flow",
                    "headers": ["Version", "# Rules", "Created", "Submitted", "Status", 
                               "Approved", "Submitted By", "Approved By", "Feedback"],
                    "rows": version_history_rows
                },
                {
                    "title": f"Latest Approved Version (v{profiling['summary'].get('latest_version_number', 'N/A')}) - All Rules",
                    "headers": ["#", "Attribute", "Rule Type", "Description", "Owner Decision", "Executed", "Status"],
                    "rows": latest_version_rules_rows
                },
                {
                    "title": "Approved and Executed Rules",
                    "headers": ["#", "Attribute", "DQ Dimension", "Rule", "Records", "Result"],
                    "rows": approved_rules_rows
                },
                {
                    "title": "Generated but Not Approved Rules",
                    "headers": ["#", "Attribute", "DQ Dimension", "Rule", "Rationale"],
                    "rows": unapproved_rules_rows
                }
            ],
            "metrics": profiling["summary"]
        }
        
        return {
            "section_title": "Data Profiling Phase",
            "section_order": 4,
            "content": content
        }
    
    async def _generate_scoping_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate scoping phase section"""
        scoping = data["scoping"]
        
        # Format version history table
        version_history_rows = []
        for version in scoping["versions"]:
            version_history_rows.append([
                f"Version {version['version_number']}",
                version["total_attributes"],
                version["included_attributes"],
                version["excluded_attributes"],
                version["created_at"][:10] if version["created_at"] else "-",
                version["submitted_at"][:10] if version["submitted_at"] else "-",
                version["version_status"].title(),
                version["approved_at"][:10] if version["approved_at"] else "-",
                version["submitted_by"] or "-",
                version["approved_by"] or "-",
                version["rejection_reason"] or "-"
            ])
        
        # Format submission history table (legacy format for compatibility)
        submission_rows = []
        for submission in scoping["submission_history"]:
            submission_rows.append([
                f"Version {submission['version']}",
                submission["non_pk_attributes_submitted"],
                submission["submission_datetime"][:10] if submission["submission_datetime"] else "-",
                submission["report_owner_decision"],
                submission["decision_datetime"][:10] if submission["decision_datetime"] else "-",
                f"{submission['duration_hours']:.1f} hours",
                submission["feedback"] or "-"
            ])
        
        # Format approved scoping table
        approved_rows = []
        for attr in scoping["approved_scoping"]:
            badges = []
            if attr["is_cde"]:
                badges.append("CDE")
            if attr["is_primary_key"]:
                badges.append("PK")
            if attr["has_issues"]:
                badges.append("Issues")
            
            approved_rows.append([
                attr["line_number"],
                f"{attr['attribute_name']} {' '.join(f'[{b}]' for b in badges)}",
                attr["llm_description"] or "-",
                attr["mdrm_code"] or "-",
                attr["llm_data_type"] or "-",
                attr["mandatory_flag"],
                attr["llm_risk_score"] or "-",
                attr["llm_rationale"] or "-"
            ])
        
        # Format not included table
        not_included_rows = []
        for attr in scoping["not_included"]:
            badges = []
            if attr["is_cde"]:
                badges.append("CDE")
            if attr["is_primary_key"]:
                badges.append("PK")
            if attr["has_issues"]:
                badges.append("Issues")
            
            not_included_rows.append([
                attr["line_number"],
                f"{attr['attribute_name']} {' '.join(f'[{b}]' for b in badges)}",
                attr["llm_description"] or "-",
                attr["mdrm_code"] or "-",
                attr["llm_data_type"] or "-",
                attr["mandatory_flag"],
                attr["llm_risk_score"] or "-",
                attr["llm_rationale"] or "-"
            ])
        
        # Format PK attributes table
        pk_attributes_rows = []
        for attr in scoping.get("pk_attributes", []):
            pk_attributes_rows.append([
                attr["line_number"],
                attr["attribute_name"],
                attr["llm_description"] or "-",
                attr["mdrm_code"] or "-",
                attr["mandatory_flag"],
                "✓" if attr["is_cde"] else "",
                attr["status"]
            ])
        
        content = {
            "summary": f"Scoping phase (Version {scoping['summary'].get('latest_version_number', 'N/A')}) "
                      f"analyzed {scoping['summary']['total_attributes']} attributes "
                      f"({scoping['summary']['pk_attributes']} PKs + {scoping['summary']['total_non_pk_attributes']} non-PKs). "
                      f"Selected {scoping['summary']['non_pk_attributes_selected']} non-PK attributes for testing. "
                      f"Report owner approved {scoping['summary']['non_pk_attributes_approved']} non-PK attributes. "
                      f"Total in scope: {scoping['summary']['total_in_scope']} attributes "
                      f"({scoping['summary']['approval_rate']:.1f}% non-PK approval rate).",
            "tables": [
                {
                    "title": "Version History and Approval Flow",
                    "headers": ["Version", "Total", "Included", "Excluded", "Created", "Submitted", 
                               "Status", "Approved", "Submitted By", "Approved By", "Feedback"],
                    "rows": version_history_rows
                },
                {
                    "title": "Primary Key Attributes (Automatically Included)",
                    "headers": ["Line #", "Attribute Name", "Description", "MDRM", "M/C/O", "CDE", "Status"],
                    "rows": pk_attributes_rows
                },
                {
                    "title": "Non-PK Attributes - Approved for Testing",
                    "headers": ["Line #", "Attribute Name", "LLM Description", "MDRM", 
                               "Data Type", "M/C/O", "Risk Score", "Rationale"],
                    "rows": approved_rows
                },
                {
                    "title": "Non-PK Attributes - Not Included in Scope",
                    "headers": ["Line #", "Attribute Name", "LLM Description", "MDRM", 
                               "Data Type", "M/C/O", "Risk Score", "Rationale"],
                    "rows": not_included_rows
                }
            ],
            "metrics": scoping["summary"]
        }
        
        return {
            "section_title": "Scoping Phase",
            "section_order": 5,
            "content": content
        }
    
    async def _generate_sample_selection_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate sample selection phase section"""
        sample_selection = data["sample_selection"]
        
        # Format version history table
        version_history_rows = []
        for version in sample_selection["versions"]:
            version_history_rows.append([
                f"Version {version['version_number']}",
                version["target_sample_size"],
                version["actual_sample_size"],
                version["created_at"][:10] if version["created_at"] else "-",
                version["submitted_at"][:10] if version["submitted_at"] else "-",
                version["version_status"].title(),
                version["approved_at"][:10] if version["approved_at"] else "-",
                version["submitted_by"] or "-",
                version["approved_by"] or "-",
                version["rejection_reason"] or "-"
            ])
        
        # Format submission history table (legacy format for compatibility)
        submission_rows = []
        for submission in sample_selection["submission_history"]:
            submission_rows.append([
                f"Version {submission['version']}",
                submission["target_sample_size"],
                submission["actual_sample_size"],
                submission["submission_datetime"][:10] if submission["submission_datetime"] else "-",
                submission["report_owner_decision"],
                submission["decision_datetime"][:10] if submission["decision_datetime"] else "-",
                f"{submission['duration_hours']:.1f} hours",
                submission["feedback"] or "-"
            ])
        
        # Format sample distribution table
        distribution_rows = []
        for category, count in sample_selection["sample_distribution"].items():
            distribution_rows.append([category, count])
        
        # Format approved samples table
        approved_samples_rows = []
        for i, sample in enumerate(sample_selection.get("approved_samples", []), 1):
            approved_samples_rows.append([
                i,
                sample["sample_id"],
                sample["entity_id"],
                sample["sample_category"],
                sample["lob_id"],
                sample["date_selected"],
                sample["report_owner_decision"]
            ])
        
        content = {
            "summary": f"Sample selection phase (Version {sample_selection['summary'].get('latest_version_number', 'N/A')}) "
                      f"identified {sample_selection['summary']['total_samples']} samples "
                      f"using {sample_selection['summary']['sampling_methodology']} methodology. "
                      f"{sample_selection['summary']['approved_samples']} samples were approved for testing.",
            "content": {
                "methodology": sample_selection["summary"]["sampling_methodology"],
                "sample_period": sample_selection["summary"]["sample_period"],
                "sample_categories": sample_selection["summary"]["sample_categories"]
            },
            "tables": [
                {
                    "title": "Version History and Approval Flow",
                    "headers": ["Version", "Target Size", "Actual Size", "Created", "Submitted", 
                               "Status", "Approved", "Submitted By", "Approved By", "Feedback"],
                    "rows": version_history_rows
                },
                {
                    "title": f"Latest Approved Version (v{sample_selection['summary'].get('latest_version_number', 'N/A')}) - Approved Samples",
                    "headers": ["#", "Sample ID", "Entity ID", "Category", "LOB", "Date Selected", "Decision"],
                    "rows": approved_samples_rows
                },
                {
                    "title": "Sample Distribution by Category",
                    "headers": ["Category", "Count"],
                    "rows": distribution_rows
                }
            ],
            "metrics": sample_selection["summary"]
        }
        
        return {
            "section_title": "Sample Selection Phase",
            "section_order": 6,
            "content": content
        }
    
    async def _generate_request_info_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate request info phase section"""
        request_info = data["request_info"]
        
        content = {
            "summary": f"Request for Information phase created {request_info['summary']['total_test_cases']} test cases. "
                      f"Evidence was collected for {request_info['summary']['test_cases_with_evidence']} test cases "
                      f"with {request_info['summary']['total_evidence_collected']} total pieces of evidence.",
            "content": {
                "evidence_collection_methods": request_info["summary"]["evidence_collection_methods"]
            },
            "metrics": request_info["summary"]
        }
        
        return {
            "section_title": "Request for Information Phase",
            "section_order": 7,
            "content": content
        }
    
    async def _generate_test_execution_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate test execution phase section"""
        test_execution = data["test_execution"]
        
        # Format test results by attribute table
        results_rows = []
        for attr_name, results in test_execution["test_results_by_attribute"].items():
            pass_rate = (results["passed"] / results["total"] * 100) if results["total"] > 0 else 0
            results_rows.append([
                attr_name,
                results["total"],
                results["passed"],
                results["failed"],
                f"{pass_rate:.1f}%"
            ])
        
        content = {
            "summary": f"Test execution phase completed {test_execution['summary']['total_test_cases']} test cases "
                      f"with {test_execution['summary']['passed_tests']} passed and "
                      f"{test_execution['summary']['failed_tests']} failed "
                      f"({test_execution['summary']['pass_rate']:.1f}% pass rate).",
            "content": {
                "execution_methods": test_execution["summary"]["execution_methods"]
            },
            "tables": [
                {
                    "title": "Test Results by Attribute",
                    "headers": ["Attribute", "Total Tests", "Passed", "Failed", "Pass Rate"],
                    "rows": results_rows
                }
            ],
            "metrics": test_execution["summary"],
            "charts": [
                {
                    "type": "bar_chart",
                    "title": "Test Results by Attribute",
                    "data": {
                        "labels": list(test_execution["test_results_by_attribute"].keys())[:10],
                        "values": [
                            r["passed"] / r["total"] * 100 if r["total"] > 0 else 0
                            for r in list(test_execution["test_results_by_attribute"].values())[:10]
                        ]
                    }
                }
            ]
        }
        
        return {
            "section_title": "Test Execution Phase",
            "section_order": 8,
            "content": content
        }
    
    async def _generate_observation_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate observation management phase section"""
        observations = data["observation_management"]
        
        # Format observations by severity table
        severity_rows = []
        for severity, count in observations["by_severity"].items():
            severity_rows.append([severity, count])
        
        # Format observations by status table
        status_rows = []
        for status, count in observations["by_status"].items():
            status_rows.append([status, count])
        
        content = {
            "summary": f"Observation management phase identified {observations['summary']['total_observations']} observations "
                      f"including {observations['summary']['high_severity']} high severity findings. "
                      f"{observations['summary']['resolved_observations']} observations have been resolved "
                      f"({observations['summary']['resolution_rate']:.1f}% resolution rate).",
            "tables": [
                {
                    "title": "Observations by Severity",
                    "headers": ["Severity", "Count"],
                    "rows": severity_rows
                },
                {
                    "title": "Observations by Status",
                    "headers": ["Status", "Count"],
                    "rows": status_rows
                }
            ],
            "metrics": observations["summary"],
            "charts": [
                {
                    "type": "pie_chart",
                    "title": "Observations by Severity",
                    "data": {
                        "labels": list(observations["by_severity"].keys()),
                        "values": list(observations["by_severity"].values())
                    }
                }
            ]
        }
        
        return {
            "section_title": "Observation Management Phase",
            "section_order": 9,
            "content": content
        }
    
    async def _generate_execution_metrics_dict(
        self, 
        phase_id: int,
        cycle_id: int,
        report_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate execution metrics section"""
        metrics = data["execution_metrics"]
        
        # Format phase duration table
        duration_rows = []
        for phase in metrics["phase_durations"]:
            duration_rows.append([
                phase["phase_name"],
                phase["started_at"][:10],
                phase["completed_at"][:10],
                f"{phase['duration_days']} days",
                f"{phase['duration_hours']:.1f} hours"
            ])
        
        # Format version counts table
        version_rows = []
        for phase_name, count in metrics["version_counts"].items():
            version_rows.append([phase_name, count])
        
        content = {
            "summary": f"The complete test cycle took {metrics['total_cycle_duration_days']} days "
                      f"({metrics['total_cycle_duration_hours']:.1f} hours) with "
                      f"{metrics['efficiency_metrics']['phases_completed']} phases completed.",
            "tables": [
                {
                    "title": "Phase Duration Analysis",
                    "headers": ["Phase", "Start Date", "End Date", "Duration (Days)", "Duration (Hours)"],
                    "rows": duration_rows
                },
                {
                    "title": "Version History by Phase",
                    "headers": ["Phase", "Number of Versions"],
                    "rows": version_rows
                }
            ],
            "metrics": {
                "total_duration_days": metrics["total_cycle_duration_days"],
                "total_duration_hours": metrics["total_cycle_duration_hours"],
                "average_phase_duration": metrics["efficiency_metrics"]["average_phase_duration_hours"],
                "phases_completed": metrics["efficiency_metrics"]["phases_completed"]
            },
            "charts": [
                {
                    "type": "timeline_chart",
                    "title": "Phase Timeline",
                    "data": {
                        "phases": [p["phase_name"] for p in metrics["phase_durations"]],
                        "durations": [p["duration_hours"] for p in metrics["phase_durations"]]
                    }
                }
            ]
        }
        
        return {
            "section_title": "Execution Metrics",
            "section_order": 10,
            "content": content
        }
    
    def _generate_what_happened_executive(self, data: Dict[str, Any]) -> str:
        """Generate 'What Actually Happened' executive commentary"""
        scoping = data.get("scoping", {})
        test_execution = data.get("test_execution", {})
        
        scoped_attrs = scoping.get("summary", {}).get("non_pk_attributes_approved", 0)
        total_non_pk = scoping.get("summary", {}).get("total_non_pk_attributes", 114)
        test_cases = test_execution.get("summary", {}).get("total_test_cases", 0)
        pass_rate = test_execution.get("summary", {}).get("pass_rate", 0)
        
        if scoped_attrs <= 1:
            return (
                f"The testing approach for Report 156 was extraordinarily limited. Of the {total_non_pk} testable "
                f"(non-PK) attributes, only {scoped_attrs} attribute was selected for testing "
                f"({(scoped_attrs/total_non_pk*100):.2f}%), with just {test_cases} test cases executed. "
                f"This minimal approach raises serious concerns about testing adequacy and regulatory compliance."
            )
        else:
            return (
                f"The testing cycle completed comprehensive validation across {scoped_attrs} critical attributes "
                f"out of {total_non_pk} testable attributes. A total of {test_cases} test cases were executed "
                f"with a {pass_rate:.1f}% pass rate, demonstrating the effectiveness of our controls."
            )
    
    def _generate_executive_commentary(self, data: Dict[str, Any]) -> str:
        """Generate qualitative executive commentary based on test results"""
        planning = data.get("planning", {})
        scoping = data.get("scoping", {})
        profiling = data.get("data_profiling", {})
        sample_selection = data.get("sample_selection", {})
        test_execution = data.get("test_execution", {})
        observations = data.get("observation_management", {})
        
        # Analyze key metrics
        total_attrs = planning.get("summary", {}).get("total_attributes", 0)
        scoped_attrs = scoping.get("summary", {}).get("attributes_approved", 0)
        pass_rate = test_execution.get("summary", {}).get("pass_rate", 0)
        total_obs = observations.get("summary", {}).get("total_observations", 0)
        high_severity = observations.get("summary", {}).get("high_severity", 0)
        
        # Build commentary
        commentary = []
        
        # Overall assessment
        if pass_rate >= 95:
            commentary.append("The testing cycle demonstrated strong control effectiveness with exceptional pass rates.")
        elif pass_rate >= 85:
            commentary.append("The testing cycle showed generally effective controls with good overall performance.")
        elif pass_rate >= 70:
            commentary.append("The testing cycle revealed moderate control effectiveness with areas requiring attention.")
        else:
            commentary.append("The testing cycle identified significant control gaps requiring immediate remediation.")
        
        # Scoping efficiency
        scoping_rate = (scoped_attrs / total_attrs * 100) if total_attrs > 0 else 0
        if scoping_rate < 10:
            commentary.append(f"The risk-based scoping approach efficiently focused on {scoped_attrs} critical attributes ({scoping_rate:.1f}% of total), demonstrating effective prioritization of testing resources.")
        else:
            commentary.append(f"The comprehensive scoping included {scoped_attrs} attributes ({scoping_rate:.1f}% of total), ensuring thorough coverage of risk areas.")
        
        # Data quality insights
        if profiling.get("summary", {}).get("rules_approved", 0) > 0:
            commentary.append("Data profiling rules were successfully implemented to validate data quality and integrity throughout the testing process.")
        
        # Observation significance
        if total_obs == 0:
            commentary.append("No observations were identified during the testing cycle, indicating robust control design and operating effectiveness.")
        elif high_severity > 0:
            commentary.append(f"The testing identified {high_severity} high-severity observations requiring immediate management attention and remediation plans.")
        else:
            commentary.append(f"A total of {total_obs} observations were documented, primarily of low to medium severity, with appropriate remediation plans established.")
        
        # Stakeholder collaboration
        commentary.append("The testing process benefited from strong collaboration between the testing team, report owners, data providers, and executive stakeholders.")
        
        return " ".join(commentary)
