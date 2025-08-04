"""
PDF Generation Service for Test Reports
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from typing import Dict, Any, List
import base64


class PDFGenerator:
    """Generate PDF reports from formatted test report data"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=12,
            spaceBefore=24
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubsectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#424242'),
            spaceAfter=10,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
    
    def generate_pdf_bytes(self, formatted_report: Dict[str, Any]) -> bytes:
        """Generate PDF bytes from formatted report data"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build the story (content)
        story = []
        
        # Title Page
        story.extend(self._create_title_page(formatted_report))
        story.append(PageBreak())
        
        # Executive Summary
        if 'executive_summary' in formatted_report:
            story.extend(self._create_executive_summary(formatted_report['executive_summary']))
            story.append(PageBreak())
        
        # Strategic Approach
        if 'strategic_approach' in formatted_report:
            story.extend(self._create_strategic_approach(formatted_report['strategic_approach']))
            story.append(PageBreak())
        
        # Testing Coverage
        if 'testing_coverage' in formatted_report:
            story.extend(self._create_testing_coverage(formatted_report['testing_coverage']))
        
        # Phase Analysis
        if 'phase_analysis' in formatted_report:
            story.append(PageBreak())
            story.extend(self._create_phase_analysis(formatted_report['phase_analysis']))
        
        # Testing Results
        if 'testing_results' in formatted_report:
            story.append(PageBreak())
            story.extend(self._create_testing_results(formatted_report['testing_results']))
        
        # Value Delivery
        if 'value_delivery' in formatted_report:
            story.append(PageBreak())
            story.extend(self._create_value_delivery(formatted_report['value_delivery']))
        
        # Recommendations
        if 'recommendations' in formatted_report:
            story.append(PageBreak())
            story.extend(self._create_recommendations(formatted_report['recommendations']))
        
        # Attestation
        if 'attestation' in formatted_report:
            story.append(PageBreak())
            story.extend(self._create_attestation(formatted_report['attestation']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def generate_pdf_base64(self, formatted_report: Dict[str, Any]) -> str:
        """Generate base64-encoded PDF data URL"""
        pdf_bytes = self.generate_pdf_bytes(formatted_report)
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        return f"data:application/pdf;base64,{pdf_base64}"
    
    def _create_title_page(self, report: Dict[str, Any]) -> List:
        """Create title page elements"""
        elements = []
        metadata = report.get('metadata', {})
        
        # Add spacing
        elements.append(Spacer(1, 2*inch))
        
        # Title
        elements.append(Paragraph(
            metadata.get('report_title', 'Test Report'),
            self.styles['CustomTitle']
        ))
        
        # Subtitle
        elements.append(Paragraph(
            metadata.get('subtitle', 'Comprehensive Test Report'),
            self.styles['Heading2']
        ))
        
        # Spacing
        elements.append(Spacer(1, inch))
        
        # Report details
        details_data = [
            ['Report ID:', str(metadata.get('report_id', 'N/A'))],
            ['Cycle:', metadata.get('cycle', 'N/A')],
            ['Period:', metadata.get('period', 'N/A')],
            ['Generated:', metadata.get('generated_date', 'N/A')]
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(details_table)
        
        return elements
    
    def _create_executive_summary(self, exec_summary: Dict[str, Any]) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionTitle']))
        
        # Overview
        if 'overview' in exec_summary:
            elements.append(Paragraph(exec_summary['overview'], self.styles['CustomBody']))
            elements.append(Spacer(1, 12))
        
        # Key Achievements
        if 'key_achievements' in exec_summary:
            elements.append(Paragraph("Key Achievements", self.styles['SubsectionTitle']))
            for achievement in exec_summary['key_achievements']:
                elements.append(Paragraph(f"• {achievement}", self.styles['CustomBody']))
            elements.append(Spacer(1, 12))
        
        # Metrics Summary
        if 'metrics_summary' in exec_summary:
            elements.append(Paragraph("Metrics Summary", self.styles['SubsectionTitle']))
            metrics = exec_summary['metrics_summary']
            metrics_data = [
                ['Coverage:', metrics.get('coverage', 'N/A')],
                ['Quality:', metrics.get('quality', 'N/A')],
                ['Efficiency:', metrics.get('efficiency', 'N/A')],
                ['Value:', metrics.get('value', 'N/A')]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[1.5*inch, 4*inch])
            metrics_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(metrics_table)
        
        return elements
    
    def _create_strategic_approach(self, approach: Dict[str, Any]) -> List:
        """Create strategic approach section"""
        elements = []
        
        elements.append(Paragraph(
            approach.get('title', 'Strategic Testing Approach'),
            self.styles['SectionTitle']
        ))
        
        if 'description' in approach:
            elements.append(Paragraph(approach['description'], self.styles['CustomBody']))
        
        if 'benefits' in approach:
            elements.append(Paragraph("Benefits", self.styles['SubsectionTitle']))
            for benefit in approach['benefits']:
                elements.append(Paragraph(f"• {benefit}", self.styles['CustomBody']))
        
        if 'justifications' in approach:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Regulatory Alignment", self.styles['SubsectionTitle']))
            for justification in approach['justifications']:
                elements.append(Paragraph(f"• {justification}", self.styles['CustomBody']))
        
        return elements
    
    def _create_testing_coverage(self, coverage: Dict[str, Any]) -> List:
        """Create testing coverage section"""
        elements = []
        
        elements.append(Paragraph(
            coverage.get('title', 'Testing Coverage'),
            self.styles['SectionTitle']
        ))
        
        # Coverage statistics
        coverage_data = [
            ['Total Attributes:', str(coverage.get('total_attributes', 0))],
            ['Attributes Tested:', str(coverage.get('tested_attributes', 0))],
            ['Coverage Percentage:', f"{coverage.get('coverage_percentage', 0):.2f}%"],
            ['Risk Coverage:', f"{coverage.get('risk_coverage_percentage', 0):.1f}%"]
        ]
        
        coverage_table = Table(coverage_data, colWidths=[2*inch, 2*inch])
        coverage_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        elements.append(coverage_table)
        
        if 'coverage_narrative' in coverage:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(coverage['coverage_narrative'], self.styles['CustomBody']))
        
        return elements
    
    def _create_phase_analysis(self, phase_analysis: Dict[str, Any]) -> List:
        """Create phase analysis section"""
        elements = []
        
        elements.append(Paragraph("Phase-by-Phase Analysis", self.styles['SectionTitle']))
        
        phases = phase_analysis.get('phases', [])
        for phase in phases:
            # Keep phase content together on same page if possible
            phase_elements = []
            
            phase_elements.append(Paragraph(
                phase.get('phase_name', 'Phase'),
                self.styles['SubsectionTitle']
            ))
            
            if 'status' in phase:
                phase_elements.append(Paragraph(
                    f"Status: {phase['status']}",
                    self.styles['CustomBody']
                ))
            
            if 'achievements' in phase:
                phase_elements.append(Paragraph("Achievements:", self.styles['Normal']))
                for achievement in phase['achievements']:
                    phase_elements.append(Paragraph(f"• {achievement}", self.styles['CustomBody']))
            
            elements.append(KeepTogether(phase_elements))
            elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_testing_results(self, results: Dict[str, Any]) -> List:
        """Create testing results section"""
        elements = []
        
        elements.append(Paragraph(
            results.get('title', 'Testing Results'),
            self.styles['SectionTitle']
        ))
        
        if 'pass_rate' in results:
            elements.append(Paragraph(
                f"Overall Pass Rate: {results['pass_rate']}%",
                self.styles['Heading3']
            ))
        
        if 'quality_achievements' in results:
            qa = results['quality_achievements']
            if 'description' in qa:
                elements.append(Paragraph(qa['description'], self.styles['CustomBody']))
        
        return elements
    
    def _create_value_delivery(self, value: Dict[str, Any]) -> List:
        """Create value delivery section"""
        elements = []
        
        elements.append(Paragraph(
            value.get('title', 'Value Delivered'),
            self.styles['SectionTitle']
        ))
        
        if 'quantifiable_benefits' in value:
            elements.append(Paragraph("Quantifiable Benefits", self.styles['SubsectionTitle']))
            for benefit in value['quantifiable_benefits']:
                elements.append(Paragraph(f"• {benefit}", self.styles['CustomBody']))
        
        if 'qualitative_benefits' in value:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Qualitative Benefits", self.styles['SubsectionTitle']))
            for benefit in value['qualitative_benefits']:
                elements.append(Paragraph(f"• {benefit}", self.styles['CustomBody']))
        
        return elements
    
    def _create_recommendations(self, recommendations: Dict[str, Any]) -> List:
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph(
            recommendations.get('title', 'Recommendations'),
            self.styles['SectionTitle']
        ))
        
        if 'building_on_success' in recommendations:
            elements.append(Paragraph("Building on Success", self.styles['SubsectionTitle']))
            for rec in recommendations['building_on_success']:
                elements.append(Paragraph(f"• {rec}", self.styles['CustomBody']))
        
        if 'continuous_improvement' in recommendations:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Continuous Improvement", self.styles['SubsectionTitle']))
            for rec in recommendations['continuous_improvement']:
                elements.append(Paragraph(f"• {rec}", self.styles['CustomBody']))
        
        return elements
    
    def _create_attestation(self, attestation: Dict[str, Any]) -> List:
        """Create attestation section"""
        elements = []
        
        elements.append(Paragraph(
            attestation.get('type', 'Attestation'),
            self.styles['SectionTitle']
        ))
        
        if 'text' in attestation:
            # Split attestation text into paragraphs
            for para in attestation['text'].split('\n\n'):
                if para.strip():
                    elements.append(Paragraph(para.strip(), self.styles['CustomBody']))
                    elements.append(Spacer(1, 6))
        
        # Signature lines
        if 'signatories' in attestation:
            elements.append(Spacer(1, inch))
            sig_data = []
            for signatory in attestation['signatories']:
                sig_data.append([
                    signatory.get('role', ''),
                    '_' * 40,
                    'Date: __________'
                ])
            
            sig_table = Table(sig_data, colWidths=[2*inch, 3*inch, 1.5*inch])
            sig_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 20),
            ]))
            elements.append(sig_table)
        
        return elements