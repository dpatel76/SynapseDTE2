"""
PDF Export Service for Test Reports

This service generates professionally formatted PDF reports from test report data
with comprehensive styling, charts, tables, and regulatory compliance formatting.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import tempfile
from pathlib import Path
import json
import base64
from io import BytesIO
import logging

# PDF generation libraries
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

# Import our professional PDF service
from app.services.professional_pdf_service import ProfessionalPDFService

logger = logging.getLogger(__name__)

# For chart generation
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.comprehensive_data_collection_service import ComprehensiveDataCollectionService


class PDFExportService:
    """Service for generating professional PDF reports"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data_service = ComprehensiveDataCollectionService(db)
        
        # Set up styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles for the report"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f4e79')
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#1f4e79'),
            borderWidth=1,
            borderColor=colors.HexColor('#1f4e79'),
            borderPadding=5
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#2f5f8f')
        ))
        
        # Key metrics style
        self.styles.add(ParagraphStyle(
            name='KeyMetric',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            leftIndent=20
        ))
        
        # Executive summary style
        self.styles.add(ParagraphStyle(
            name='ExecutiveSummary',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leftIndent=10,
            rightIndent=10
        ))
        
        # Table header style
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white
        ))
        
        # Table cell style
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=9
        ))
    
    async def generate_comprehensive_pdf_report(self, cycle_id: int, report_id: int, 
                                              output_path: Optional[str] = None) -> str:
        """Generate comprehensive PDF test report using professional design"""
        
        # Collect all data
        try:
            logger.info(f"Collecting comprehensive data for cycle {cycle_id}, report {report_id}")
            comprehensive_data = await self.data_service.collect_all_phase_data(cycle_id, report_id)
        except Exception as e:
            logger.error(f"Error collecting data: {str(e)}")
            raise
        
        try:
            # Use professional PDF service
            logger.info("Using professional PDF service for report generation")
            professional_service = ProfessionalPDFService()
            
            # Prepare data for professional report
            professional_data = self._prepare_professional_data(comprehensive_data, cycle_id, report_id)
            
            # Generate PDF bytes
            pdf_bytes = professional_service.generate_comprehensive_report(professional_data)
            
            # Write to file if path specified, otherwise to temp
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"/tmp/test_report_{cycle_id}_{report_id}_{timestamp}.pdf"
            
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            
            logger.info(f"PDF report generated successfully at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating professional PDF: {str(e)}")
            # Fallback to legacy method
            logger.info("Falling back to legacy PDF generation")
            return await self._generate_legacy_pdf_report(comprehensive_data, cycle_id, report_id, output_path)
    
    def _prepare_professional_data(self, comp_data: Dict[str, Any], cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Prepare data for professional PDF generation"""
        try:
            # Extract report info
            report_info = comp_data.get('report_info', {})
            summary_data = comp_data.get('summary', {})
            
            # Calculate testable attributes
            planning_summary = comp_data.get('planning', {}).get('summary', {})
            total_attrs = planning_summary.get('total_attributes', 118)
            pk_attrs = planning_summary.get('pk_count', 4)
            testable_attrs = total_attrs - pk_attrs
            
            # Update summary with calculated fields
            summary_data['testable_attributes'] = testable_attrs
            summary_data['scoped_attributes'] = comp_data.get('scoping', {}).get('summary', {}).get('approved_selections', 0)
            summary_data['test_cases_executed'] = len(comp_data.get('test_execution', {}).get('test_cases', []))
            summary_data['test_cases_passed'] = sum(1 for tc in comp_data.get('test_execution', {}).get('test_cases', []) 
                                                   if tc.get('result') == 'pass')
            summary_data['test_pass_rate'] = (summary_data['test_cases_passed'] / summary_data['test_cases_executed'] * 100) \
                                            if summary_data['test_cases_executed'] > 0 else 0
            summary_data['observations_total'] = comp_data.get('observation_management', {}).get('summary', {}).get('total_observations', 0)
            
            professional_data = {
                # Report metadata
                'report_id': report_id,
                'report_name': report_info.get('report_name', 'FR Y-14M Schedule D.1'),
                'cycle_id': cycle_id,
                'cycle_name': report_info.get('cycle_name'),
                'cycle_year': report_info.get('cycle_year'),
                'cycle_quarter': report_info.get('cycle_quarter'),
                
                # Executive summary
                'executive_summary': {
                    'plain_english_explanation': self._generate_plain_english(report_info),
                    'stakeholders': comp_data.get('stakeholders', {}),
                    'summary': summary_data,
                    'what_actually_happened': self._generate_executive_commentary(comp_data),
                    'execution_metrics': comp_data.get('execution_metrics', {})
                },
                
                # Planning phase
                'planning': {
                    'summary': planning_summary,
                    'attributes': comp_data.get('planning', {}).get('attributes', []),
                    'versions': comp_data.get('planning', {}).get('versions', []),
                    'what_actually_happened': self._generate_planning_commentary(comp_data.get('planning', {}))
                },
                
                # Data profiling phase
                'data_profiling': {
                    'summary': comp_data.get('data_profiling', {}).get('summary', {}),
                    'rule_results': comp_data.get('data_profiling', {}).get('rule_results', []),
                    'version_history': comp_data.get('data_profiling', {}).get('version_history', []),
                    'what_actually_happened': self._generate_profiling_commentary(comp_data.get('data_profiling', {}))
                },
                
                # Scoping phase  
                'scoping': {
                    'summary': comp_data.get('scoping', {}).get('summary', {}),
                    'selected_attributes': comp_data.get('scoping', {}).get('selected_attributes', []),
                    'version_history': comp_data.get('scoping', {}).get('version_history', []),
                    'what_actually_happened': self._generate_scoping_commentary(comp_data.get('scoping', {}))
                },
                
                # Sample selection phase
                'sample_selection': {
                    'summary': comp_data.get('sample_selection', {}).get('summary', {}),
                    'samples': comp_data.get('sample_selection', {}).get('samples', []),
                    'version_history': comp_data.get('sample_selection', {}).get('version_history', []),
                    'what_actually_happened': self._generate_sample_commentary(comp_data.get('sample_selection', {}))
                },
                
                # Request info phase
                'request_info': {
                    'summary': comp_data.get('request_info', {}).get('summary', {}),
                    'test_cases': comp_data.get('request_info', {}).get('test_cases', []),
                    'version_history': comp_data.get('request_info', {}).get('version_history', []),
                    'what_actually_happened': self._generate_request_commentary(comp_data.get('request_info', {}))
                },
                
                # Test execution phase
                'test_execution': {
                    'summary': comp_data.get('test_execution', {}).get('summary', {}),
                    'test_cases': comp_data.get('test_execution', {}).get('test_cases', []),
                    'version_history': comp_data.get('test_execution', {}).get('version_history', []),
                    'what_actually_happened': self._generate_execution_commentary(comp_data.get('test_execution', {}))
                },
                
                # Observation management phase
                'observation_management': {
                    'summary': comp_data.get('observation_management', {}).get('summary', {}),
                    'observations': comp_data.get('observation_management', {}).get('observations', []),
                    'version_history': comp_data.get('observation_management', {}).get('version_history', []),
                    'what_actually_happened': self._generate_observation_commentary(comp_data.get('observation_management', {}))
                }
            }
            
            return professional_data
            
        except Exception as e:
            logger.error(f"Error preparing professional data: {str(e)}")
            raise
    
    def _generate_plain_english(self, report_info: Dict[str, Any]) -> str:
        """Generate plain English explanation"""
        return f"""This report documents the testing of {report_info.get('report_name', 'FR Y-14M Schedule D.1')} submission to the Federal Reserve. This {report_info.get('frequency', 'monthly')} report provides loan-level details for commercial real estate loans. The Fed uses this data to stress test our portfolio and determine if we have enough capital to survive a severe recession.

Why This Matters: Errors in this report could lead to incorrect capital requirements, regulatory penalties, or restrictions on dividends and share buybacks."""
    
    def _generate_executive_commentary(self, data: Dict[str, Any]) -> str:
        """Generate executive what happened commentary"""
        summary = data.get('summary', {})
        scoped = summary.get('scoped_attributes', 0)
        testable = summary.get('testable_attributes', 114)
        test_cases = summary.get('test_cases_executed', 0)
        
        if scoped <= 1:
            return f"""The testing approach for Report 156 was extraordinarily limited. Of the {testable} testable (non-PK) attributes, only {scoped} attribute was selected for testing ({(scoped/testable*100) if testable > 0 else 0:.2f}%), with just {test_cases} test cases executed. This minimal approach raises serious concerns about testing adequacy and regulatory compliance."""
        else:
            return f"""The testing covered {scoped} of {testable} testable attributes ({(scoped/testable*100) if testable > 0 else 0:.1f}%), with {test_cases} test cases executed. While this represents a risk-based approach, significant coverage gaps remain."""
    
    def _generate_planning_commentary(self, planning_data: Dict[str, Any]) -> str:
        """Generate planning phase commentary"""
        summary = planning_data.get('summary', {})
        total = summary.get('total_attributes', 118)
        cde = summary.get('cde_count', 1)
        
        return f"""During the planning phase, we analyzed all {total} data attributes in the FR Y-14M Schedule D.1 report to understand each commercial real estate loan data point, its source, and criticality. This comprehensive inventory forms the foundation for our risk-based testing approach.

Key Finding: The report has relatively few critical elements - only {cde} CDE out of {total} attributes ({(cde/total*100) if total > 0 else 0:.1f}%), suggesting most fields are informational rather than calculation-critical."""
    
    def _generate_profiling_commentary(self, profiling_data: Dict[str, Any]) -> str:
        """Generate data profiling commentary"""
        summary = profiling_data.get('summary', {})
        generated = summary.get('total_rules_generated', 385)
        approved = summary.get('approved_rules', 21)
        
        return f"""We used AI to generate {generated} data quality rules - about {generated/118:.1f} rules per attribute. However, the approval process was extremely selective:

• Generated: {generated} rules (100%)
• Approved: {approved} rules ({(approved/generated*100) if generated > 0 else 0:.1f}% approval rate)
• Rejected: {generated-approved} rules ({((generated-approved)/generated*100) if generated > 0 else 0:.1f}%)

CONCERN: The {((generated-approved)/generated*100) if generated > 0 else 0:.1f}% rejection rate suggests either overly restrictive approval criteria or a decision to minimize profiling efforts."""
    
    def _generate_scoping_commentary(self, scoping_data: Dict[str, Any]) -> str:
        """Generate scoping commentary"""
        summary = scoping_data.get('summary', {})
        testable = summary.get('total_attributes', 114) - summary.get('primary_key_attributes', 4)
        selected = summary.get('non_pk_attributes_selected', 5)
        approved = summary.get('approved_selections', 1)
        
        return f"""The scoping phase revealed an extremely conservative testing approach:

• Started with: {testable} testable attributes (excluding Primary Keys)
• Selected: {selected} attributes ({(selected/testable*100) if testable > 0 else 0:.1f}% coverage)
• Approved: {approved} attribute ({(approved/testable*100) if testable > 0 else 0:.2f}% final coverage)

CRITICAL ISSUE: With {((testable-approved)/testable*100) if testable > 0 else 0:.1f}% of attributes untested, we have virtually no assurance about data quality."""
    
    def _generate_sample_commentary(self, sample_data: Dict[str, Any]) -> str:
        """Generate sample selection commentary"""
        summary = sample_data.get('summary', {})
        total = summary.get('total_samples', 5)
        approved = summary.get('approved_samples', 4)
        
        return f"""Sample selection identified {total} samples for testing, with {approved} approved. This minimal sample size provides limited statistical validity for a report that likely contains thousands of loans."""
    
    def _generate_request_commentary(self, request_data: Dict[str, Any]) -> str:
        """Generate request for information commentary"""
        test_cases = len(request_data.get('test_cases', []))
        return f"""Request for Information was sent to data providers covering {test_cases} test cases. Evidence collection methods included document requests, database queries, and system screenshots."""
    
    def _generate_execution_commentary(self, execution_data: Dict[str, Any]) -> str:
        """Generate test execution commentary"""
        summary = execution_data.get('summary', {})
        total = summary.get('total_test_cases', 0)
        passed = summary.get('passed_test_cases', 0)
        
        return f"""Test execution completed with {total} test cases. {passed} tests passed ({(passed/total*100) if total > 0 else 0:.1f}% pass rate). Any failures indicate potential data quality issues requiring remediation."""
    
    def _generate_observation_commentary(self, observation_data: Dict[str, Any]) -> str:
        """Generate observation management commentary"""
        summary = observation_data.get('summary', {})
        total = summary.get('total_observations', 0)
        resolved = summary.get('resolved_observations', 0)
        
        return f"""Observation management identified {total} issues during testing. {resolved} observations have been resolved ({(resolved/total*100) if total > 0 else 0:.1f}% resolution rate). Outstanding observations require management attention and remediation plans."""
    
    async def _generate_legacy_pdf_report(self, comprehensive_data: Dict[str, Any], 
                                         cycle_id: int, report_id: int,
                                         output_path: Optional[str] = None) -> str:
        """Legacy PDF generation method - fallback"""
        # Set up output path
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/tmp/test_report_{cycle_id}_{report_id}_{timestamp}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build document content
        story = []
        
        # Title page
        try:
            story.extend(self._create_title_page(comprehensive_data))
            story.append(PageBreak())
        except Exception as e:
            import traceback
            print(f"Error creating title page: {e}")
            print(traceback.format_exc())
            raise
        
        # Executive summary
        story.extend(self._create_executive_summary(comprehensive_data))
        story.append(PageBreak())
        
        # Planning phase section
        story.extend(self._create_planning_section(comprehensive_data))
        story.append(PageBreak())
        
        # Data profiling section
        story.extend(self._create_data_profiling_section(comprehensive_data))
        story.append(PageBreak())
        
        # Scoping section
        story.extend(self._create_scoping_section(comprehensive_data))
        story.append(PageBreak())
        
        # Sample selection section
        story.extend(self._create_sample_selection_section(comprehensive_data))
        story.append(PageBreak())
        
        # Request info section
        story.extend(self._create_request_info_section(comprehensive_data))
        story.append(PageBreak())
        
        # Test execution section
        story.extend(self._create_test_execution_section(comprehensive_data))
        story.append(PageBreak())
        
        # Observation management section
        story.extend(self._create_observation_section(comprehensive_data))
        story.append(PageBreak())
        
        # Execution metrics section
        story.extend(self._create_execution_metrics_section(comprehensive_data))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def _create_title_page(self, data: Dict[str, Any]) -> List:
        """Create title page elements"""
        
        report_info = data["report_info"]
        stakeholders = data["stakeholders"]
        
        story = []
        
        # Main title
        title = f"Test Report - {report_info['report_name']}"
        story.append(Paragraph(title, self.styles['ReportTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Cycle information
        cycle_info = f"""
        <b>Cycle:</b> {report_info['cycle_name']}<br/>
        <b>Year:</b> {report_info['cycle_year']}<br/>
        <b>Quarter:</b> Q{report_info['cycle_quarter']}<br/>
        <b>Line of Business:</b> {report_info['lob_name']}<br/>
        <b>Regulation:</b> {report_info['regulatory_framework']}<br/>
        <b>Risk Rating:</b> {report_info.get('risk_rating', 'Not specified')}<br/>
        """
        story.append(Paragraph(cycle_info, self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Stakeholders table
        report_owner = stakeholders.get('report_owner') or {}
        tester = stakeholders.get('tester') or {}
        data_provider = stakeholders.get('data_provider') or {}
        data_executive = stakeholders.get('data_executive') or {}
        
        stakeholder_data = [
            ['Role', 'Name', 'Contact'],
            ['Report Owner', report_owner.get('name', 'Not assigned') if isinstance(report_owner, dict) else 'Not assigned', 
             report_owner.get('email', 'N/A') if isinstance(report_owner, dict) else 'N/A'],
            ['Tester', tester.get('name', 'Not assigned') if isinstance(tester, dict) else 'Not assigned',
             tester.get('email', 'N/A') if isinstance(tester, dict) else 'N/A'],
            ['Data Provider', data_provider.get('name', 'Not assigned') if isinstance(data_provider, dict) else 'Not assigned',
             data_provider.get('email', 'N/A') if isinstance(data_provider, dict) else 'N/A'],
            ['Data Executive', data_executive.get('name', 'Not assigned') if isinstance(data_executive, dict) else 'Not assigned',
             data_executive.get('email', 'N/A') if isinstance(data_executive, dict) else 'N/A']
        ]
        
        stakeholder_table = Table(stakeholder_data, colWidths=[2*inch, 2.5*inch, 2*inch])
        stakeholder_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("<b>Stakeholders</b>", self.styles['SubsectionHeader']))
        story.append(stakeholder_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Generation date
        story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y')}", 
                              self.styles['Normal']))
        
        return story
    
    def _create_executive_summary(self, data: Dict[str, Any]) -> List:
        """Create executive summary section"""
        
        story = []
        
        # Add executive overview box with plain English explanation
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        # Add plain English explanation if available
        exec_summary = data.get("executive_summary", {})
        if exec_summary.get("plain_english_explanation"):
            story.append(Paragraph("In Plain English:", self.styles['SubsectionHeader']))
            story.append(Paragraph(exec_summary["plain_english_explanation"], self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Add "What Actually Happened" box if available
        if exec_summary.get("what_actually_happened"):
            what_happened_text = f"<b>What We Found:</b> {exec_summary['what_actually_happened']}"
            story.append(Paragraph(what_happened_text, self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Key metrics from all phases
        try:
            planning_data = data.get("planning", {})
            test_execution_data = data.get("test_execution", {})
            observation_data = data.get("observation_management", {})
            execution_metrics = data.get("execution_metrics", {})
            scoping_data = data.get("scoping", {})
            sample_data = data.get("sample_selection", {})
            
            # Debug print
            print(f"planning_data type: {type(planning_data)}")
            print(f"test_execution_data type: {type(test_execution_data)}")
            print(f"observation_data type: {type(observation_data)}")
            print(f"execution_metrics type: {type(execution_metrics)}")
            
            if isinstance(planning_data, dict):
                print(f"planning_data.summary type: {type(planning_data.get('summary'))}")
            
        except Exception as e:
            print(f"Error getting phase data: {e}")
            import traceback
            print(traceback.format_exc())
            raise
        
        # Key metrics table
        metrics_data = [
            ['Metric', 'Value', 'Details'],
            ['Total Attributes', str(planning_data.get('summary', {}).get('total_attributes', 0)), 'Attributes analyzed in planning phase'],
            ['Scoped Attributes', str(scoping_data.get('summary', {}).get('non_pk_attributes_approved', 0)), 'Attributes selected for testing'],
            ['Total Samples', str(sample_data.get('summary', {}).get('approved_samples', 0)), 'Samples approved for testing'],
            ['Test Cases', str(test_execution_data.get('summary', {}).get('total_test_cases', 0)), 'Test cases executed'],
            ['Total Attributes', str(planning_data.get("summary", {}).get("total_attributes", 0)), 
             'Attributes analyzed in planning phase'],
            ['Test Pass Rate', f"{test_execution_data.get('summary', {}).get('pass_rate', 0):.1f}%", 
             'Percentage of tests that passed'],
            ['Total Observations', str(observation_data.get("summary", {}).get("total_observations", 0)), 
             'Issues identified during testing'],
            ['Cycle Duration', f"{execution_metrics.get('total_duration_days', 0)} days", 
             'Total time from start to completion'],
            ['CDE Count', str(planning_data.get("summary", {}).get("cde_count", 0)), 
             'Critical Data Elements identified'],
            ['Resolution Rate', f"{observation_data.get('summary', {}).get('resolution_rate', 0):.1f}%", 
             'Percentage of observations resolved']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Key Metrics", self.styles['SubsectionHeader']))
        story.append(metrics_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Executive summary narrative
        report_info = data["report_info"]
        summary_text = f"""
        The {report_info['cycle_name']} testing cycle for {report_info['report_name']} 
        has been completed successfully. This comprehensive testing program evaluated 
        {planning_data.get('summary', {}).get('total_attributes', 0)} attributes through a risk-based approach.
        
        Key accomplishments include thorough planning and scoping phases, comprehensive data profiling 
        with AI-powered rule generation, systematic sample selection, and rigorous test execution. 
        The testing demonstrates effective controls and data quality management across all tested attributes.
        """
        
        story.append(Paragraph("Summary", self.styles['SubsectionHeader']))
        story.append(Paragraph(summary_text, self.styles['ExecutiveSummary']))
        story.append(Spacer(1, 0.2*inch))
        
        # Add critical risk assessment if coverage is too low
        if test_execution_data.get('summary', {}).get('total_test_cases', 0) == 0 or \
           scoping_data.get('summary', {}).get('non_pk_attributes_approved', 0) <= 1:
            risk_box_data = [
                ["CRITICAL TESTING GAPS IDENTIFIED"],
                ["Major Concerns:"],
                ["• Only 1 of 114 non-PK attributes selected (0.88%)"],
                ["• 113 testable attributes have zero testing"],
                ["• No statistical validity with minimal samples"],
                ["• Unknown if CDE is included in testing"],
                [""],
                ["Risk Statement:"],
                ["Testing only 0.88% of report attributes provides virtually no"],
                ["assurance about report accuracy. This approach falls far below"],
                ["any reasonable testing standard and requires immediate expansion."]
            ]
            
            risk_table = Table(risk_box_data, colWidths=[6*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                ('BOX', (0, 0), (-1, -1), 1, colors.red),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(risk_table)
            story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _create_planning_section(self, data: Dict[str, Any]) -> List:
        """Create planning phase section"""
        
        story = []
        story.append(Paragraph("Planning Phase Section", self.styles['SectionHeader']))
        
        planning_data = data.get("planning", {})
        
        if planning_data.get("status") == "not_found":
            story.append(Paragraph("Planning phase data not available", self.styles['Normal']))
            return story
        
        summary = planning_data.get("summary", {})
        
        # Summary text
        summary_text = f"""
        The planning phase analyzed {summary.get('total_attributes', 0)} total attributes, identifying 
        {summary.get('cde_count', 0)} Critical Data Elements, {summary.get('pk_count', 0)} Primary Keys, 
        and {summary.get('issues_count', 0)} attributes with historical issues. 
        {summary.get('approved_count', 0)} attributes were approved for testing.
        """
        
        story.append(Paragraph("Planning Summary", self.styles['SubsectionHeader']))
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Add "What Actually Happened" commentary if available
        if planning_data.get("what_actually_happened"):
            what_happened_data = [
                ["PLANNING PHASE COMMENTARY"],
                ["What Actually Happened:"],
                [planning_data["what_actually_happened"]]
            ]
            
            what_table = Table(what_happened_data, colWidths=[6*inch])
            what_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4B7BA1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0F8FF')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#4B7BA1')),
                ('TOPPADDING', (0, 2), (-1, 2), 8),
                ('BOTTOMPADDING', (0, 2), (-1, 2), 8),
                ('LEFTPADDING', (0, 2), (-1, 2), 10),
                ('RIGHTPADDING', (0, 2), (-1, 2), 10)
            ]))
            story.append(what_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Approval summary table
        # Planning doesn't have approval_summary, use direct values from summary
        total_attrs = summary.get('total_attributes', 0)
        approved = summary.get('approved_count', 0)
        approval_rate = summary.get('approval_rate', 0)
        
        approval_table_data = [
            ['Approval Status', 'Count', 'Percentage'],
            ['Total Submitted', str(total_attrs), '100%'],
            ['Approved', str(approved), f"{approval_rate:.1f}%"],
            ['Rejected', '0', '0.0%'],
            ['Pending', '0', '0.0%']
        ]
        
        approval_table = Table(approval_table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        approval_table.setStyle(self._get_standard_table_style())
        
        story.append(Paragraph("Approval Summary", self.styles['SubsectionHeader']))
        story.append(approval_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Attributes table (first 20 rows for space)
        attributes = planning_data.get("attributes", [])[:20]
        print(f"attributes type: {type(attributes)}")
        if attributes:
            print(f"First attribute type: {type(attributes[0])}")
        if attributes:
            attr_table_data = [['Line #', 'Attribute Name', 'Type', 'Flags', 'Status']]
            
            for attr in attributes:
                flags = []
                if attr.get("cde_flag"):
                    flags.append("CDE")
                if attr.get("is_primary_key"):
                    flags.append("PK")
                if attr.get("historical_issues_flag"):
                    flags.append("Issues")
                if attr.get("mandatory_flag"):
                    flags.append("Mandatory")
                
                try:
                    line_num = str(attr.get("line_item_number", "") if isinstance(attr, dict) else "")
                    attr_name = attr.get("attribute_name", "") if isinstance(attr, dict) else ""
                    attr_name = attr_name[:25] + "..." if len(attr_name) > 25 else attr_name
                    data_type = attr.get("data_type", "") if isinstance(attr, dict) else ""
                    status = attr.get("approval_status", "") if isinstance(attr, dict) else ""
                    
                    attr_table_data.append([
                        line_num,
                        attr_name,
                        data_type,
                        ", ".join(flags),
                        status
                    ])
                except Exception as e:
                    print(f"Error processing attribute: {e}")
                    print(f"Attribute type: {type(attr)}")
                    print(f"Attribute value: {attr}")
                    raise
            
            attr_table = Table(attr_table_data, colWidths=[0.8*inch, 2.2*inch, 1*inch, 1.5*inch, 1*inch])
            attr_table.setStyle(self._get_standard_table_style())
            
            story.append(Paragraph(f"Attributes Summary (showing first {len(attributes)} of {len(planning_data.get('attributes', []))})", 
                                  self.styles['SubsectionHeader']))
            story.append(attr_table)
        
        return story
    
    def _create_data_profiling_section(self, data: Dict[str, Any]) -> List:
        """Create data profiling section"""
        
        story = []
        story.append(Paragraph("Data Profiling Section", self.styles['SectionHeader']))
        
        profiling_data = data.get("data_profiling", {})
        
        if profiling_data.get("status") == "not_found":
            story.append(Paragraph("Data profiling phase data not available", self.styles['Normal']))
            return story
        
        summary = profiling_data.get("summary", {})
        
        # Summary text
        summary_text = f"""
        The data profiling phase generated {summary.get('total_rules_generated', 0)} data quality rules 
        using AI-powered analysis. {summary.get('rules_approved', 0)} rules were approved for execution, 
        with {summary.get('rules_executed', 0)} rules successfully executed achieving a 
        {(summary.get('rules_executed', 0) / summary.get('rules_approved', 1) * 100) if summary.get('rules_approved', 0) > 0 else 0:.1f}% pass rate.
        """
        
        story.append(Paragraph("Data Profiling Summary", self.styles['SubsectionHeader']))
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Rule execution results table
        execution_results = profiling_data.get("execution_results", [])[:15]  # First 15 for space
        if execution_results:
            results_table_data = [['Rule Name', 'Attribute', 'Status', 'Pass Rate']]
            
            for result in execution_results:
                total = result.get("total_records", 0)
                passed = result.get("passed_records", 0)
                pass_rate = (passed / total * 100) if total > 0 else 0
                
                results_table_data.append([
                    result.get("rule_name", "")[:20] + "..." if len(result.get("rule_name", "")) > 20 else result.get("rule_name", ""),
                    result.get("attribute_name", "")[:20] + "..." if len(result.get("attribute_name", "")) > 20 else result.get("attribute_name", ""),
                    result.get("execution_status", ""),
                    f"{pass_rate:.1f}%"
                ])
            
            results_table = Table(results_table_data, colWidths=[2*inch, 2*inch, 1*inch, 1*inch])
            results_table.setStyle(self._get_standard_table_style())
            
            story.append(Paragraph(f"Rule Execution Results (showing first {len(execution_results)})", 
                                  self.styles['SubsectionHeader']))
            story.append(results_table)
        
        return story
    
    def _create_scoping_section(self, data: Dict[str, Any]) -> List:
        """Create scoping section"""
        
        story = []
        story.append(Paragraph("Scoping Section", self.styles['SectionHeader']))
        
        scoping_data = data.get("scoping", {})
        
        if scoping_data.get("status") == "not_found":
            story.append(Paragraph("Scoping phase data not available", self.styles['Normal']))
            return story
        
        summary = scoping_data.get("summary", {})
        
        # Summary text
        summary_text = f"""
        From {summary.get('total_non_pk_attributes', 0)} available non-Primary Key attributes, 
        {summary.get('non_pk_attributes_selected', 0)} attributes were selected for testing 
        ({summary.get('selection_rate', 0):.1f}% coverage). {summary.get('non_pk_attributes_approved', 0)} 
        selections were approved through the review process.
        """
        
        story.append(Paragraph("Scoping Summary", self.styles['SubsectionHeader']))
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Selected attributes table
        selected_attrs = scoping_data.get("selected_attributes", [])[:15]  # First 15 for space
        if selected_attrs:
            selected_table_data = [['Line #', 'Attribute Name', 'Risk Score', 'Data Type', 'Status']]
            
            for attr in selected_attrs:
                selected_table_data.append([
                    str(attr.get("line_item_number", "")),
                    attr.get("attribute_name", "")[:25] + "..." if len(attr.get("attribute_name", "")) > 25 else attr.get("attribute_name", ""),
                    str(attr.get("risk_score", "")),
                    attr.get("data_type", ""),
                    attr.get("approval_status", "")
                ])
            
            selected_table = Table(selected_table_data, colWidths=[0.8*inch, 2.2*inch, 1*inch, 1*inch, 1*inch])
            selected_table.setStyle(self._get_standard_table_style())
            
            story.append(Paragraph(f"Selected Attributes for Testing (showing first {len(selected_attrs)})", 
                                  self.styles['SubsectionHeader']))
            story.append(selected_table)
        
        return story
    
    def _create_sample_selection_section(self, data: Dict[str, Any]) -> List:
        """Create sample selection section"""
        
        story = []
        story.append(Paragraph("Sample Selection Section", self.styles['SectionHeader']))
        
        sample_data = data.get("sample_selection", {})
        
        if sample_data.get("status") == "not_found":
            story.append(Paragraph("Sample selection phase data not available", self.styles['Normal']))
            return story
        
        summary = sample_data.get("summary", {})
        
        # Summary text
        summary_text = f"""
        Sample selection was performed using {summary.get('sampling_methodology', 'standard methodology')}. 
        A total of {summary.get('total_samples', 0)} samples were selected for the testing period.
        """
        
        story.append(Paragraph("Sample Selection Summary", self.styles['SubsectionHeader']))
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Sample period table
        sample_period = summary.get("sample_period", "Not specified")
        period_table_data = [
            ['Sample Period Details', 'Value'],
            ['Sample Period', sample_period if isinstance(sample_period, str) else 'Not specified'],
            ['Total Samples', str(summary.get('total_samples', 0))],
            ['Approved Samples', str(summary.get('approved_samples', 0))],
            ['Methodology', summary.get('sampling_methodology', 'Not specified')]
        ]
        
        period_table = Table(period_table_data, colWidths=[2.5*inch, 3*inch])
        period_table.setStyle(self._get_standard_table_style())
        
        story.append(period_table)
        
        return story
    
    def _create_request_info_section(self, data: Dict[str, Any]) -> List:
        """Create request info section"""
        
        story = []
        story.append(Paragraph("Request Info Section", self.styles['SectionHeader']))
        
        rfi_data = data.get("request_info", {})
        
        if rfi_data.get("status") == "not_found":
            story.append(Paragraph("Request info phase data not available", self.styles['Normal']))
            return story
        
        summary = rfi_data.get("summary", {})
        
        # Summary text
        summary_text = f"""
        Request for Information (RFI) was sent on {summary.get('rfi_sent_date', 'Not specified')} 
        with a due date of {summary.get('rfi_due_date', 'Not specified')}. The RFI covered 
        {summary.get('total_test_cases', 0)} test cases with evidence collection methods including: 
        {', '.join(summary.get('evidence_collection_methods', []))}.
        """
        
        story.append(Paragraph("Request Info Summary", self.styles['SubsectionHeader']))
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Test cases summary table (first 10)
        test_cases = rfi_data.get("test_cases", [])[:10]
        if test_cases:
            tc_table_data = [['Test Case ID', 'Attribute', 'Evidence Method']]
            
            for tc in test_cases:
                tc_table_data.append([
                    tc.get("test_case_id", "")[:8] + "...",
                    tc.get("attribute_name", "")[:20] + "..." if len(tc.get("attribute_name", "")) > 20 else tc.get("attribute_name", ""),
                    tc.get("evidence_collection_method", "")
                ])
            
            tc_table = Table(tc_table_data, colWidths=[1.5*inch, 2.5*inch, 2*inch])
            tc_table.setStyle(self._get_standard_table_style())
            
            story.append(Paragraph(f"Test Cases Summary (showing first {len(test_cases)} of {len(rfi_data.get('test_cases', []))})", 
                                  self.styles['SubsectionHeader']))
            story.append(tc_table)
        
        return story
    
    def _create_test_execution_section(self, data: Dict[str, Any]) -> List:
        """Create test execution section"""
        
        story = []
        story.append(Paragraph("Test Execution Section", self.styles['SectionHeader']))
        
        execution_data = data.get("test_execution", {})
        
        if execution_data.get("status") == "not_found":
            story.append(Paragraph("Test execution phase data not available", self.styles['Normal']))
            return story
        
        summary = execution_data.get("summary", {})
        
        # Summary text
        summary_text = f"""
        Test execution was completed with {summary.get('total_test_executions', 0)} total test executions. 
        The overall pass rate was {summary.get('pass_rate', 0):.1f}%, with {summary.get('passed_tests', 0)} 
        tests passing, {summary.get('failed_tests', 0)} tests failing, and 
        {summary.get('inconclusive_tests', 0)} tests marked as inconclusive.
        """
        
        story.append(Paragraph("Test Execution Summary", self.styles['SubsectionHeader']))
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Results summary table
        results_summary_data = [
            ['Test Result', 'Count', 'Percentage'],
            ['Passed', str(summary.get('passed_tests', 0)), 
             f"{(summary.get('passed_tests', 0) / summary.get('total_test_executions', 1) * 100):.1f}%"],
            ['Failed', str(summary.get('failed_tests', 0)), 
             f"{(summary.get('failed_tests', 0) / summary.get('total_test_executions', 1) * 100):.1f}%"],
            ['Inconclusive', str(summary.get('inconclusive_tests', 0)), 
             f"{(summary.get('inconclusive_tests', 0) / summary.get('total_test_executions', 1) * 100):.1f}%"]
        ]
        
        results_table = Table(results_summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        results_table.setStyle(self._get_standard_table_style())
        
        story.append(Paragraph("Test Results Summary", self.styles['SubsectionHeader']))
        story.append(results_table)
        
        return story
    
    def _create_observation_section(self, data: Dict[str, Any]) -> List:
        """Create observation management section"""
        
        story = []
        story.append(Paragraph("Observation Management Section", self.styles['SectionHeader']))
        
        obs_data = data.get("observation_management", {})
        summary = obs_data.get("summary", {})
        
        # Summary text
        summary_text = f"""
        Observation management identified {summary.get('total_observations', 0)} total observations 
        with a resolution rate of {summary.get('resolution_rate', 0):.1f}%. Observations were 
        categorized by severity and managed through a structured resolution process.
        """
        
        story.append(Paragraph("Observation Management Summary", self.styles['SubsectionHeader']))
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Observations by severity table
        severity_data = [['Severity', 'Count']]
        for severity, count in summary.get("by_severity", {}).items():
            severity_data.append([severity, str(count)])
        
        if len(severity_data) > 1:
            severity_table = Table(severity_data, colWidths=[2*inch, 1.5*inch])
            severity_table.setStyle(self._get_standard_table_style())
            
            story.append(Paragraph("Observations by Severity", self.styles['SubsectionHeader']))
            story.append(severity_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Observations by status table
        status_data = [['Status', 'Count']]
        for status, count in summary.get("by_status", {}).items():
            status_data.append([status, str(count)])
        
        if len(status_data) > 1:
            status_table = Table(status_data, colWidths=[2*inch, 1.5*inch])
            status_table.setStyle(self._get_standard_table_style())
            
            story.append(Paragraph("Observations by Status", self.styles['SubsectionHeader']))
            story.append(status_table)
        
        return story
    
    def _create_execution_metrics_section(self, data: Dict[str, Any]) -> List:
        """Create execution metrics section"""
        
        story = []
        story.append(Paragraph("Execution Metrics", self.styles['SectionHeader']))
        
        metrics = data["execution_metrics"]
        
        # Summary text
        total_duration = metrics.get("total_duration_days", 0)
        efficiency = metrics.get("cycle_efficiency", {}).get("efficiency_percentage", 0)
        
        summary_text = f"""
        The testing cycle was completed in {total_duration} days with an efficiency rating of 
        {efficiency:.1f}%. Time was distributed across multiple phases with comprehensive 
        version control and role-based collaboration.
        """
        
        story.append(Paragraph("Execution Metrics Summary", self.styles['SubsectionHeader']))
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Time per phase table
        time_data = [['Phase Name', 'Duration (Days)', 'Status']]
        for phase_name, phase_info in metrics.get("time_per_phase", {}).items():
            time_data.append([
                phase_name,
                str(phase_info.get("duration_days", 0)),
                phase_info.get("status", "Unknown")
            ])
        
        if len(time_data) > 1:
            time_table = Table(time_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
            time_table.setStyle(self._get_standard_table_style())
            
            story.append(Paragraph("Time per Phase", self.styles['SubsectionHeader']))
            story.append(time_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Role breakdown table
        role_data = [['Role', 'Contribution (%)']]
        for role, percentage in metrics.get("role_breakdown", {}).items():
            role_data.append([role, f"{percentage}%"])
        
        if len(role_data) > 1:
            role_table = Table(role_data, colWidths=[2*inch, 1.5*inch])
            role_table.setStyle(self._get_standard_table_style())
            
            story.append(Paragraph("Role Breakdown", self.styles['SubsectionHeader']))
            story.append(role_table)
        
        return story
    
    def _get_standard_table_style(self) -> TableStyle:
        """Get standard table styling"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ])
    
    async def generate_chart_images(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate chart images for inclusion in PDF"""
        
        charts = {}
        
        # Test results pie chart
        execution_data = data.get("test_execution", {})
        if execution_data.get("summary"):
            summary = execution_data["summary"]
            
            plt.figure(figsize=(6, 6))
            labels = ['Passed', 'Failed', 'Inconclusive']
            sizes = [
                summary.get('passed_tests', 0),
                summary.get('failed_tests', 0),
                summary.get('inconclusive_tests', 0)
            ]
            colors_list = ['#2E8B57', '#DC143C', '#FFD700']
            
            if sum(sizes) > 0:
                plt.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
                plt.title('Test Results Distribution')
                
                # Save to bytes
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
                img_buffer.seek(0)
                
                # Save to temp file
                temp_path = f"/tmp/test_results_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                with open(temp_path, 'wb') as f:
                    f.write(img_buffer.getvalue())
                
                charts['test_results'] = temp_path
                plt.close()
        
        return charts