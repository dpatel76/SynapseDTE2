"""Professional PDF Export Service for Comprehensive Test Reports"""

from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image, Flowable, PageTemplate, Frame
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
import io

logger = logging.getLogger(__name__)


class ReportColors:
    """Professional color palette for the report"""
    # Primary colors
    NAVY_BLUE = colors.HexColor('#003366')
    CORPORATE_GRAY = colors.HexColor('#4A4A4A')
    LIGHT_GRAY = colors.HexColor('#F5F5F5')
    
    # Semantic colors
    SUCCESS_GREEN = colors.HexColor('#28A745')
    WARNING_ORANGE = colors.HexColor('#FFC107')
    DANGER_RED = colors.HexColor('#DC3545')
    INFO_BLUE = colors.HexColor('#17A2B8')
    
    # Background colors
    LIGHT_BLUE_BG = colors.HexColor('#E3F2FD')
    LIGHT_RED_BG = colors.HexColor('#FFEBEE')
    LIGHT_GREEN_BG = colors.HexColor('#E8F5E9')
    LIGHT_ORANGE_BG = colors.HexColor('#FFF3E0')


class ConditionalPageBreak(Flowable):
    """Custom flowable for conditional page breaks"""
    
    def __init__(self, height):
        Flowable.__init__(self)
        self.height = height
    
    def draw(self):
        pass
    
    def wrap(self, availWidth, availHeight):
        if availHeight < self.height:
            return (availWidth, availHeight + 1)  # Force page break
        else:
            return (availWidth, 0)  # No page break needed


class ProfessionalPDFService:
    """Service for generating professional PDF reports"""
    
    def __init__(self):
        self.page_width = letter[0]
        self.page_height = letter[1]
        self.left_margin = 1.25 * inch
        self.right_margin = 1.0 * inch
        self.top_margin = 1.0 * inch
        self.bottom_margin = 1.0 * inch
        self.content_width = self.page_width - self.left_margin - self.right_margin
        self.styles = self._create_custom_styles()
        self.page_num = 0
        self.total_pages = 0
        
    def _create_custom_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=ReportColors.NAVY_BLUE,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=ReportColors.NAVY_BLUE,
            spaceAfter=18,
            spaceBefore=36,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection header style
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=ReportColors.NAVY_BLUE,
            spaceAfter=12,
            spaceBefore=24,
            fontName='Helvetica-Bold'
        ))
        
        # Component header style
        styles.add(ParagraphStyle(
            name='ComponentHeader',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=ReportColors.NAVY_BLUE,
            spaceAfter=12,
            spaceBefore=18,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        styles.add(ParagraphStyle(
            name='ProfessionalBody',
            parent=styles['BodyText'],
            fontSize=11,
            textColor=ReportColors.CORPORATE_GRAY,
            spaceAfter=12,
            leading=16.5,  # 1.5x line height
            alignment=TA_JUSTIFY
        ))
        
        # Commentary style
        styles.add(ParagraphStyle(
            name='Commentary',
            parent=styles['BodyText'],
            fontSize=11,
            textColor=ReportColors.CORPORATE_GRAY,
            leftIndent=0,
            rightIndent=0,
            spaceAfter=6,
            leading=16.5
        ))
        
        # Table text style
        styles.add(ParagraphStyle(
            name='TableText',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=ReportColors.CORPORATE_GRAY,
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0,
            leading=12
        ))
        
        return styles
    
    def _create_commentary_box(self, title: str, content: str, 
                              box_color: colors.Color = None,
                              bg_color: colors.Color = None) -> Table:
        """Create a professional commentary box with colored header"""
        if box_color is None:
            box_color = ReportColors.INFO_BLUE
        if bg_color is None:
            bg_color = ReportColors.LIGHT_BLUE_BG
            
        # Header
        header_data = [[Paragraph(title, self.styles['Normal'])]]
        header_table = Table(header_data, colWidths=[self.content_width])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), box_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        # Content
        content_para = Paragraph(content, self.styles['Commentary'])
        content_data = [[content_para]]
        content_table = Table(content_data, colWidths=[self.content_width])
        content_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        # Combine
        combined = Table([[header_table], [content_table]], colWidths=[self.content_width])
        combined.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, box_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        return combined
    
    def _create_metrics_dashboard(self, metrics: List[Dict[str, str]]) -> Table:
        """Create a metrics dashboard with cards"""
        cards = []
        
        for metric in metrics:
            # Create card content
            value_para = Paragraph(f"<b>{metric['value']}</b>", self.styles['Normal'])
            label_para = Paragraph(metric['label'], self.styles['Normal'])
            
            card_data = [[value_para], [label_para]]
            card = Table(card_data, colWidths=[1.5*inch], rowHeights=[0.6*inch, 0.4*inch])
            
            # Determine card color based on metric type
            card_color = ReportColors.NAVY_BLUE
            if 'color' in metric:
                if metric['color'] == 'danger':
                    card_color = ReportColors.DANGER_RED
                elif metric['color'] == 'warning':
                    card_color = ReportColors.WARNING_ORANGE
                elif metric['color'] == 'success':
                    card_color = ReportColors.SUCCESS_GREEN
            
            card.setStyle(TableStyle([
                # Value styling
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, 0), 24),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                ('TEXTCOLOR', (0, 0), (0, 0), card_color),
                
                # Label styling
                ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (0, 1), 10),
                ('ALIGN', (0, 1), (0, 1), 'CENTER'),
                ('VALIGN', (0, 1), (0, 1), 'TOP'),
                ('TEXTCOLOR', (0, 1), (0, 1), ReportColors.CORPORATE_GRAY),
                
                # Box styling
                ('BOX', (0, 0), (-1, -1), 1, card_color),
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ]))
            cards.append(card)
        
        # Arrange cards in a grid (4 per row)
        rows = []
        for i in range(0, len(cards), 4):
            row = cards[i:i+4]
            # Pad row if needed
            while len(row) < 4:
                row.append('')
            rows.append(row)
        
        dashboard_table = Table(rows, colWidths=[1.5*inch]*4, 
                               spaceBefore=12, spaceAfter=12,
                               hAlign='CENTER')
        
        # Create container with title
        title_para = Paragraph("TESTING SCORECARD", self.styles['ComponentHeader'])
        
        container_data = [[title_para], [dashboard_table]]
        container = Table(container_data, colWidths=[self.content_width])
        container.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 1, ReportColors.NAVY_BLUE),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        return container
    
    def _calculate_column_widths(self, headers: List[str], data: List[List[Any]], 
                                max_width: float = None) -> List[float]:
        """Calculate column widths to prevent truncation"""
        if max_width is None:
            max_width = self.content_width
            
        col_count = len(headers)
        min_widths = []
        
        # Calculate minimum width for each column
        for i in range(col_count):
            # Header width
            max_width_needed = stringWidth(str(headers[i]), 'Helvetica-Bold', 11) + 12
            
            # Data widths
            for row in data[:20]:  # Sample first 20 rows
                if i < len(row):
                    cell_text = str(row[i])
                    width_needed = stringWidth(cell_text, 'Helvetica', 10) + 12
                    max_width_needed = max(max_width_needed, width_needed)
            
            min_widths.append(max_width_needed)
        
        # Distribute width proportionally
        total_min_width = sum(min_widths)
        
        if total_min_width <= max_width:
            return min_widths
        else:
            # Need to compress - maintain proportions
            scale_factor = max_width / total_min_width
            return [w * scale_factor for w in min_widths]
    
    def _create_data_table(self, headers: List[str], data: List[List[Any]], 
                          col_widths: List[float] = None,
                          highlight_rows: List[int] = None,
                          wrap_text: bool = True) -> Table:
        """Create a professional data table"""
        if col_widths is None:
            col_widths = self._calculate_column_widths(headers, data)
        
        # Process data - wrap long text if needed
        processed_data = []
        for row in data:
            processed_row = []
            for i, cell in enumerate(row):
                if wrap_text and isinstance(cell, str) and len(cell) > 40:
                    processed_row.append(Paragraph(cell, self.styles['TableText']))
                else:
                    processed_row.append(str(cell))
            processed_data.append(processed_row)
        
        # Create table
        table_data = [headers] + processed_data
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Style configuration
        style_commands = [
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), ReportColors.NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # Data styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), ReportColors.CORPORATE_GRAY),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, ReportColors.LIGHT_GRAY),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        
        # Zebra striping
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style_commands.append(
                    ('BACKGROUND', (0, i), (-1, i), ReportColors.LIGHT_GRAY)
                )
        
        # Highlight specific rows
        if highlight_rows:
            for row_idx in highlight_rows:
                if row_idx < len(table_data):
                    style_commands.append(
                        ('BACKGROUND', (0, row_idx), (-1, row_idx), 
                         ReportColors.LIGHT_ORANGE_BG)
                    )
        
        table.setStyle(TableStyle(style_commands))
        return table
    
    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page"""
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica-Bold', 14)
        canvas_obj.setFillColor(ReportColors.NAVY_BLUE)
        canvas_obj.drawString(
            doc.leftMargin, 
            doc.height + doc.topMargin - 0.5*inch,
            "FR Y-14M Schedule D.1 Test Report"
        )
        
        # Page number
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.setFillColor(ReportColors.CORPORATE_GRAY)
        page_text = f"Page {canvas_obj.getPageNumber()}"
        canvas_obj.drawRightString(
            doc.width + doc.leftMargin,
            doc.height + doc.topMargin - 0.5*inch,
            page_text
        )
        
        # Footer line
        canvas_obj.setStrokeColor(ReportColors.LIGHT_GRAY)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(
            doc.leftMargin,
            doc.bottomMargin + 0.75*inch,
            doc.width + doc.leftMargin,
            doc.bottomMargin + 0.75*inch
        )
        
        # Footer text
        canvas_obj.setFont('Helvetica-Oblique', 9)
        canvas_obj.setFillColor(ReportColors.CORPORATE_GRAY)
        canvas_obj.drawString(
            doc.leftMargin,
            doc.bottomMargin + 0.5*inch,
            "CONFIDENTIAL - INTERNAL USE ONLY"
        )
        
        # Generation date
        canvas_obj.drawRightString(
            doc.width + doc.leftMargin,
            doc.bottomMargin + 0.5*inch,
            f"Generated: {datetime.now().strftime('%B %d, %Y')}"
        )
        
        canvas_obj.restoreState()
    
    def _create_cover_page(self, report_data: Dict[str, Any]) -> List[Flowable]:
        """Create the cover page"""
        elements = []
        
        # Add spacing
        elements.append(Spacer(1, 2*inch))
        
        # Title section
        elements.append(Paragraph("COMPREHENSIVE TEST REPORT", self.styles['ReportTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Report name
        elements.append(Paragraph(
            report_data.get('report_name', 'FR Y-14M Schedule D.1'),
            self.styles['SectionHeader']
        ))
        elements.append(Paragraph(
            "Commercial Real Estate Loans",
            self.styles['SubsectionHeader']
        ))
        elements.append(Spacer(1, 1*inch))
        
        # Cycle information
        cycle_info = f"""
        <para align="center">
        <b>Test Cycle:</b> {report_data.get('cycle_name', 'N/A')}<br/>
        <b>Year:</b> {report_data.get('cycle_year', 'N/A')}<br/>
        <b>Quarter:</b> Q{report_data.get('cycle_quarter', 'N/A')}<br/>
        </para>
        """
        elements.append(Paragraph(cycle_info, self.styles['ProfessionalBody']))
        elements.append(Spacer(1, 2*inch))
        
        # Footer information
        footer_info = f"""
        <para align="center">
        Generated: {datetime.now().strftime('%B %d, %Y')}<br/>
        Report ID: {report_data.get('report_id', 'N/A')}<br/>
        Cycle ID: {report_data.get('cycle_id', 'N/A')}
        </para>
        """
        elements.append(Paragraph(footer_info, self.styles['Normal']))
        
        # Force page break
        elements.append(PageBreak())
        
        return elements
    
    def _create_executive_summary(self, data: Dict[str, Any]) -> List[Flowable]:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.25*inch))
        
        # Plain English explanation
        if data.get('plain_english_explanation'):
            plain_english_box = self._create_commentary_box(
                "PLAIN ENGLISH EXPLANATION",
                data['plain_english_explanation'],
                ReportColors.INFO_BLUE,
                ReportColors.LIGHT_BLUE_BG
            )
            elements.append(plain_english_box)
            elements.append(Spacer(1, 0.25*inch))
        
        # Key stakeholders table
        if data.get('stakeholders'):
            elements.append(Paragraph("KEY STAKEHOLDERS", self.styles['SubsectionHeader']))
            
            stakeholder_headers = ['Role', 'Name', 'Responsibility']
            stakeholder_data = []
            
            # Map stakeholder data
            stakeholder_mapping = {
                'report_owner': ('Report Owner', 'Overall report accuracy'),
                'tester': ('Lead Tester', 'Test execution'),
                'data_provider': ('Data Provider', 'Source data quality'),
                'data_executive': ('Data Executive', 'Data governance')
            }
            
            for key, (role, responsibility) in stakeholder_mapping.items():
                if key in data['stakeholders']:
                    stakeholder = data['stakeholders'][key]
                    stakeholder_data.append([
                        role,
                        stakeholder.get('name', 'Not Assigned'),
                        responsibility
                    ])
            
            if stakeholder_data:
                stakeholder_table = self._create_data_table(
                    stakeholder_headers, 
                    stakeholder_data,
                    col_widths=[1.5*inch, 2*inch, 2.75*inch]
                )
                elements.append(stakeholder_table)
                elements.append(Spacer(1, 0.25*inch))
        
        # Testing scorecard
        metrics = []
        
        # Add metrics from summary data
        summary = data.get('summary', {})
        
        # Total attributes
        metrics.append({
            'value': str(summary.get('total_attributes', 0)),
            'label': 'Total Attrs'
        })
        
        # Scoped attributes
        scoped = summary.get('scoped_attributes', 0)
        metrics.append({
            'value': str(scoped),
            'label': 'Attrs Tested',
            'color': 'danger' if scoped <= 1 else 'warning'
        })
        
        # Coverage
        total_testable = summary.get('testable_attributes', 114)
        coverage = (scoped / total_testable * 100) if total_testable > 0 else 0
        metrics.append({
            'value': f"{coverage:.2f}%",
            'label': 'Coverage',
            'color': 'danger' if coverage < 10 else 'warning'
        })
        
        # Risk level
        risk_level = 'HIGH' if coverage < 10 else 'MEDIUM'
        metrics.append({
            'value': risk_level,
            'label': 'Risk',
            'color': 'danger' if risk_level == 'HIGH' else 'warning'
        })
        
        # Add second row of metrics
        metrics.extend([
            {
                'value': str(summary.get('test_cases_executed', 0)),
                'label': 'Test Cases'
            },
            {
                'value': str(summary.get('test_cases_passed', 0)),
                'label': 'Passed'
            },
            {
                'value': f"{summary.get('test_pass_rate', 0):.1f}%",
                'label': 'Pass Rate',
                'color': 'success' if summary.get('test_pass_rate', 0) >= 95 else 'warning'
            },
            {
                'value': str(summary.get('observations_total', 0)),
                'label': 'Issues',
                'color': 'success' if summary.get('observations_total', 0) == 0 else 'warning'
            }
        ])
        
        dashboard = self._create_metrics_dashboard(metrics)
        elements.append(dashboard)
        elements.append(Spacer(1, 0.25*inch))
        
        # What Actually Happened commentary
        if data.get('what_actually_happened'):
            what_happened_box = self._create_commentary_box(
                "WHAT ACTUALLY HAPPENED",
                data['what_actually_happened'],
                ReportColors.INFO_BLUE,
                ReportColors.LIGHT_BLUE_BG
            )
            elements.append(what_happened_box)
            elements.append(Spacer(1, 0.25*inch))
        
        # Critical risk assessment
        if coverage < 10:  # High risk threshold
            risk_content = f"""
Testing only {coverage:.2f}% of report attributes provides virtually no assurance about report accuracy.

RISKS IDENTIFIED:
• {total_testable - scoped} of {total_testable} testable attributes have ZERO testing
• Unknown if Critical Data Elements were tested
• No statistical validity with minimal samples
• High probability of undetected errors in production reports

REQUIRED ACTIONS:
1. Immediately expand testing to cover all CDEs and high-risk attributes
2. Increase sample size to achieve statistical confidence
3. Implement automated testing for future cycles
4. Executive review of risk acceptance if minimal testing continues
            """
            
            risk_box = self._create_commentary_box(
                "⚠️ CRITICAL RISK ASSESSMENT",
                risk_content,
                ReportColors.DANGER_RED,
                ReportColors.LIGHT_RED_BG
            )
            elements.append(risk_box)
        
        return elements
    
    def _create_planning_phase(self, data: Dict[str, Any]) -> List[Flowable]:
        """Create planning phase section"""
        elements = []
        
        elements.append(ConditionalPageBreak(4*inch))
        elements.append(Paragraph("PLANNING PHASE RESULTS", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.25*inch))
        
        # What Actually Happened
        if data.get('what_actually_happened'):
            what_happened_box = self._create_commentary_box(
                "WHAT ACTUALLY HAPPENED",
                data['what_actually_happened'],
                ReportColors.INFO_BLUE,
                ReportColors.LIGHT_BLUE_BG
            )
            elements.append(what_happened_box)
            elements.append(Spacer(1, 0.25*inch))
        
        # Planning metrics
        if data.get('summary'):
            summary = data['summary']
            
            elements.append(Paragraph("PLANNING METRICS", self.styles['SubsectionHeader']))
            
            metrics_headers = ['Metric', 'Count', 'Percentage of Total']
            metrics_data = [
                ['Total Attributes', str(summary.get('total_attributes', 0)), '100.0%'],
                ['Critical Data Elements', str(summary.get('cde_count', 0)), 
                 f"{(summary.get('cde_count', 0) / summary.get('total_attributes', 1) * 100):.1f}%"],
                ['Primary Keys', str(summary.get('pk_count', 0)),
                 f"{(summary.get('pk_count', 0) / summary.get('total_attributes', 1) * 100):.1f}%"],
                ['Attributes with Issues', str(summary.get('issues_count', 0)),
                 f"{(summary.get('issues_count', 0) / summary.get('total_attributes', 1) * 100):.1f}%"],
                ['Standard Attributes', 
                 str(summary.get('total_attributes', 0) - summary.get('cde_count', 0) - 
                     summary.get('pk_count', 0) - summary.get('issues_count', 0)),
                 f"{((summary.get('total_attributes', 0) - summary.get('cde_count', 0) - summary.get('pk_count', 0) - summary.get('issues_count', 0)) / summary.get('total_attributes', 1) * 100):.1f}%"],
                ['', '', ''],  # Separator
                ['Approved for Testing', str(summary.get('approved_count', 0)),
                 f"{summary.get('approval_rate', 0):.1f}%"],
                ['Rejected', '0', '0.0%']
            ]
            
            metrics_table = self._create_data_table(
                metrics_headers,
                metrics_data,
                col_widths=[2.5*inch, 1.5*inch, 2.25*inch]
            )
            elements.append(metrics_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Attribute inventory
        if data.get('attributes'):
            elements.append(Paragraph(
                "ATTRIBUTE INVENTORY (Sorted by Type, then Line Number)",
                self.styles['SubsectionHeader']
            ))
            
            # Sort attributes: PK first, then CDE, then issues, then others
            attrs = data['attributes']
            sorted_attrs = sorted(attrs, key=lambda x: (
                not x.get('is_primary_key', False),
                not x.get('is_cde', False),
                not x.get('has_issues', False),
                int(x.get('line_item_number', '999'))
            ))
            
            # Show all attributes, not just first 20
            attr_headers = ['Line #', 'Attribute Name', 'Type', 'Flags', 'Status']
            attr_data = []
            
            for attr in sorted_attrs:
                flags = []
                if attr.get('is_primary_key'):
                    flags.append('PK')
                if attr.get('is_cde'):
                    flags.append('CDE')
                if attr.get('has_issues'):
                    flags.append('Issue')
                if attr.get('mandatory_flag') == 'Mandatory':
                    flags.append('Req')
                
                attr_data.append([
                    attr.get('line_item_number', ''),
                    attr.get('attribute_name', ''),
                    'Text',  # Could be enhanced with actual type
                    ', '.join(flags) if flags else '-',
                    attr.get('approval_status', 'pending').title()
                ])
            
            # Create table with all attributes
            attr_table = self._create_data_table(
                attr_headers,
                attr_data,
                col_widths=[0.75*inch, 3*inch, 0.75*inch, 1*inch, 0.75*inch]
            )
            elements.append(attr_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Version history
        if data.get('versions'):
            elements.append(Paragraph("VERSION HISTORY", self.styles['SubsectionHeader']))
            
            version_headers = ['Version', 'Date', 'Submitted By', 'Status', 'Approved By', 'Comments']
            version_data = []
            
            for idx, version in enumerate(data['versions']):
                version_data.append([
                    f"v{idx + 1}",
                    version.get('submitted_date', 'N/A')[:10] if version.get('submitted_date') else 'N/A',
                    version.get('submitted_by', 'N/A'),
                    version.get('status', 'N/A').title(),
                    version.get('approved_by', 'N/A') if version.get('approved_by') else '-',
                    version.get('feedback', '') or version.get('comments', '') or '-'
                ])
            
            if version_data:
                version_table = self._create_data_table(
                    version_headers,
                    version_data,
                    col_widths=[0.7*inch, 1*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1.35*inch]
                )
                elements.append(version_table)
        
        return elements
    
    def _create_data_profiling_phase(self, data: Dict[str, Any]) -> List[Flowable]:
        """Create data profiling phase section"""
        elements = []
        
        elements.append(ConditionalPageBreak(4*inch))
        elements.append(Paragraph("DATA PROFILING PHASE RESULTS", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.25*inch))
        
        # What Actually Happened
        if data.get('what_actually_happened'):
            what_happened_box = self._create_commentary_box(
                "WHAT ACTUALLY HAPPENED",
                data['what_actually_happened'],
                ReportColors.INFO_BLUE,
                ReportColors.LIGHT_BLUE_BG
            )
            elements.append(what_happened_box)
            elements.append(Spacer(1, 0.25*inch))
        
        # Data profiling metrics
        if data.get('summary'):
            summary = data['summary']
            
            elements.append(Paragraph("DATA PROFILING METRICS", self.styles['SubsectionHeader']))
            
            total_generated = summary.get('total_rules_generated', 0)
            total_approved = summary.get('approved_rules', 0)
            total_executed = summary.get('executed_rules', 0)
            total_passed = summary.get('passed_rules', 0)
            
            metrics_headers = ['Metric', 'Count', 'Percent', 'Implication']
            metrics_data = [
                ['Rules Generated', str(total_generated), '100.0%', 'Comprehensive coverage'],
                ['Rules Approved', str(total_approved), 
                 f"{(total_approved / total_generated * 100) if total_generated > 0 else 0:.1f}%",
                 'Selective validation' if total_approved < total_generated * 0.5 else 'Good coverage'],
                ['Rules Executed', str(total_executed),
                 f"{(total_executed / total_approved * 100) if total_approved > 0 else 0:.1f}%",
                 'All approved rules ran' if total_executed == total_approved else 'Partial execution'],
                ['Rules Passed', str(total_passed),
                 f"{(total_passed / total_executed * 100) if total_executed > 0 else 0:.1f}%",
                 'No data quality issues' if total_passed == total_executed else 'Issues found'],
                ['Attributes with Rules', str(summary.get('attributes_with_rules', 0)),
                 f"{(summary.get('attributes_with_rules', 0) / 118 * 100):.1f}%",
                 f"{118 - summary.get('attributes_with_rules', 0)} attrs unchecked"]
            ]
            
            metrics_table = self._create_data_table(
                metrics_headers,
                metrics_data,
                col_widths=[1.75*inch, 1*inch, 1*inch, 2.5*inch]
            )
            elements.append(metrics_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Rule execution results
        if data.get('rule_results'):
            elements.append(Paragraph("APPROVED RULES DETAIL", self.styles['SubsectionHeader']))
            
            rule_headers = ['ID', 'Attribute', 'Rule Description', 'Result', 'Records']
            rule_data = []
            
            for idx, rule in enumerate(data['rule_results'][:50]):  # Show first 50
                rule_data.append([
                    str(idx + 1),
                    rule.get('attribute_name', 'N/A')[:30],
                    rule.get('rule_name', 'N/A')[:40],
                    'PASS ✓' if rule.get('passed', False) else 'FAIL ✗',
                    f"{rule.get('passed_count', 0)}/{rule.get('total_count', 0)}"
                ])
            
            if rule_data:
                rule_table = self._create_data_table(
                    rule_headers,
                    rule_data,
                    col_widths=[0.5*inch, 1.75*inch, 2.25*inch, 0.75*inch, 1*inch]
                )
                elements.append(rule_table)
                elements.append(Spacer(1, 0.25*inch))
        
        # Version history
        if data.get('version_history'):
            elements.append(Paragraph("VERSION HISTORY", self.styles['SubsectionHeader']))
            
            version_headers = ['Version', 'Date', 'Submitted By', 'Status', 'Reviewed By', 'Comments']
            version_data = []
            
            for idx, version in enumerate(data['version_history']):
                version_data.append([
                    f"v{idx + 1}",
                    version.get('submitted_date', 'N/A')[:10] if version.get('submitted_date') else 'N/A',
                    version.get('submitted_by', 'N/A'),
                    version.get('status', 'N/A').title(),
                    version.get('approved_by', 'N/A') if version.get('approved_by') else '-',
                    version.get('feedback', '') or '-'
                ])
            
            if version_data:
                version_table = self._create_data_table(
                    version_headers,
                    version_data,
                    col_widths=[0.7*inch, 1*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1.35*inch]
                )
                elements.append(version_table)
        
        return elements
    
    def _create_scoping_phase(self, data: Dict[str, Any]) -> List[Flowable]:
        """Create scoping phase section"""
        elements = []
        
        elements.append(ConditionalPageBreak(4*inch))
        elements.append(Paragraph("SCOPING PHASE RESULTS", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.25*inch))
        
        # What Actually Happened
        if data.get('what_actually_happened'):
            what_happened_box = self._create_commentary_box(
                "WHAT ACTUALLY HAPPENED",
                data['what_actually_happened'],
                ReportColors.INFO_BLUE,
                ReportColors.LIGHT_BLUE_BG
            )
            elements.append(what_happened_box)
            elements.append(Spacer(1, 0.25*inch))
        
        # Scoping decision matrix
        if data.get('summary'):
            summary = data['summary']
            
            elements.append(Paragraph("SCOPING DECISION MATRIX", self.styles['SubsectionHeader']))
            
            total_attrs = summary.get('total_attributes', 118)
            pk_attrs = summary.get('primary_key_attributes', 4)
            testable = total_attrs - pk_attrs
            selected = summary.get('non_pk_attributes_selected', 0)
            approved = summary.get('approved_selections', 0)
            
            decision_headers = ['Scoping Criteria', 'Count', 'Percent', 'Decision Impact']
            decision_data = [
                ['Total Attributes', str(total_attrs), '100.0%', 'Starting universe'],
                ['Less: Primary Keys', f"({pk_attrs})", f"{(pk_attrs/total_attrs*100):.1f}%", 'Not testable'],
                ['Testable Attributes', str(testable), f"{(testable/total_attrs*100):.1f}%", 'Available for testing'],
                ['Initially Selected', str(selected), f"{(selected/testable*100) if testable > 0 else 0:.1f}%", 'Risk-based selection'],
                ['Final Approved', str(approved), f"{(approved/testable*100) if testable > 0 else 0:.1f}%", 'Actual test coverage'],
                ['Not Tested', str(testable - approved), f"{((testable-approved)/testable*100) if testable > 0 else 0:.1f}%", 'Coverage gap']
            ]
            
            decision_table = self._create_data_table(
                decision_headers,
                decision_data,
                col_widths=[2*inch, 1*inch, 1*inch, 2.25*inch]
            )
            elements.append(decision_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Selected attributes detail
        if data.get('selected_attributes'):
            elements.append(Paragraph("SELECTED ATTRIBUTES DETAIL", self.styles['SubsectionHeader']))
            
            selected_headers = ['Line #', 'Attribute Name', 'Type', 'Status', 'Selection Reason']
            selected_data = []
            
            for attr in data['selected_attributes'][:10]:  # Show first 10
                attr_type = []
                if attr.get('is_cde'):
                    attr_type.append('CDE')
                if attr.get('has_issues'):
                    attr_type.append('Issue')
                if attr.get('risk_rating') == 'high':
                    attr_type.append('High Risk')
                
                selected_data.append([
                    attr.get('line_item_number', ''),
                    attr.get('attribute_name', '')[:35],
                    ', '.join(attr_type) if attr_type else 'Standard',
                    attr.get('approval_status', 'pending').upper(),
                    attr.get('selection_reason', 'Risk-based selection')[:30]
                ])
            
            if selected_data:
                selected_table = self._create_data_table(
                    selected_headers,
                    selected_data,
                    col_widths=[0.6*inch, 2.25*inch, 1*inch, 0.9*inch, 1.5*inch]
                )
                elements.append(selected_table)
                elements.append(Spacer(1, 0.25*inch))
        
        # Version history
        if data.get('version_history'):
            elements.append(Paragraph("VERSION HISTORY", self.styles['SubsectionHeader']))
            
            version_headers = ['Version', 'Date', 'Submitted By', 'Status', 'Reviewed By', 'Comments']
            version_data = []
            
            for idx, version in enumerate(data['version_history']):
                version_data.append([
                    f"v{idx + 1}",
                    version.get('submitted_date', 'N/A')[:10] if version.get('submitted_date') else 'N/A',
                    version.get('submitted_by', 'N/A'),
                    version.get('status', 'N/A').title(),
                    version.get('approved_by', 'N/A') if version.get('approved_by') else '-',
                    version.get('feedback', '') or '-'
                ])
            
            if version_data:
                version_table = self._create_data_table(
                    version_headers,
                    version_data,
                    col_widths=[0.7*inch, 1*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1.35*inch]
                )
                elements.append(version_table)
        
        return elements
    
    def _create_sample_selection_phase(self, data: Dict[str, Any]) -> List[Flowable]:
        """Create sample selection phase section"""
        elements = []
        
        elements.append(ConditionalPageBreak(4*inch))
        elements.append(Paragraph("SAMPLE SELECTION PHASE RESULTS", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.25*inch))
        
        # What Actually Happened
        if data.get('what_actually_happened'):
            what_happened_box = self._create_commentary_box(
                "WHAT ACTUALLY HAPPENED",
                data['what_actually_happened'],
                ReportColors.INFO_BLUE,
                ReportColors.LIGHT_BLUE_BG
            )
            elements.append(what_happened_box)
            elements.append(Spacer(1, 0.25*inch))
        
        # Sample selection summary
        if data.get('summary'):
            summary = data['summary']
            
            elements.append(Paragraph("SAMPLE SELECTION METRICS", self.styles['SubsectionHeader']))
            
            sample_headers = ['Sample Period Details', 'Value']
            sample_data = [
                ['Sample Period', summary.get('sample_period', 'Not specified')],
                ['Total Samples', str(summary.get('total_samples', 0))],
                ['Approved Samples', str(summary.get('approved_samples', 0))],
                ['Methodology', summary.get('methodology', 'Not specified')]
            ]
            
            sample_table = self._create_data_table(
                sample_headers,
                sample_data,
                col_widths=[3*inch, 3.25*inch]
            )
            elements.append(sample_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Sample details
        if data.get('samples'):
            elements.append(Paragraph("SAMPLE DETAILS", self.styles['SubsectionHeader']))
            
            sample_detail_headers = ['Sample ID', 'Period', 'Type', 'Status', 'Description']
            sample_detail_data = []
            
            for sample in data['samples'][:20]:  # Show first 20
                sample_detail_data.append([
                    str(sample.get('sample_id', '')),
                    sample.get('period', 'N/A'),
                    sample.get('sample_type', 'Standard'),
                    sample.get('status', 'pending').upper(),
                    sample.get('description', '')[:40]
                ])
            
            if sample_detail_data:
                detail_table = self._create_data_table(
                    sample_detail_headers,
                    sample_detail_data,
                    col_widths=[1*inch, 1.25*inch, 1*inch, 1*inch, 2*inch]
                )
                elements.append(detail_table)
                elements.append(Spacer(1, 0.25*inch))
        
        # Version history
        if data.get('version_history'):
            elements.append(Paragraph("VERSION HISTORY", self.styles['SubsectionHeader']))
            
            version_headers = ['Version', 'Date', 'Submitted By', 'Status', 'Reviewed By', 'Comments']
            version_data = []
            
            for idx, version in enumerate(data['version_history']):
                version_data.append([
                    f"v{idx + 1}",
                    version.get('submitted_date', 'N/A')[:10] if version.get('submitted_date') else 'N/A',
                    version.get('submitted_by', 'N/A'),
                    version.get('status', 'N/A').title(),
                    version.get('approved_by', 'N/A') if version.get('approved_by') else '-',
                    version.get('feedback', '') or '-'
                ])
            
            if version_data:
                version_table = self._create_data_table(
                    version_headers,
                    version_data,
                    col_widths=[0.7*inch, 1*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1.35*inch]
                )
                elements.append(version_table)
        
        return elements
    
    def _create_test_execution_phase(self, data: Dict[str, Any]) -> List[Flowable]:
        """Create test execution phase section"""
        elements = []
        
        elements.append(ConditionalPageBreak(4*inch))
        elements.append(Paragraph("TEST EXECUTION PHASE RESULTS", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.25*inch))
        
        # What Actually Happened
        if data.get('what_actually_happened'):
            what_happened_box = self._create_commentary_box(
                "WHAT ACTUALLY HAPPENED",
                data['what_actually_happened'],
                ReportColors.INFO_BLUE,
                ReportColors.LIGHT_BLUE_BG
            )
            elements.append(what_happened_box)
            elements.append(Spacer(1, 0.25*inch))
        
        # Test execution summary
        if data.get('summary'):
            summary = data['summary']
            
            elements.append(Paragraph("TEST RESULTS SUMMARY", self.styles['SubsectionHeader']))
            
            total_tests = summary.get('total_test_cases', 0)
            passed_tests = summary.get('passed_test_cases', 0)
            failed_tests = summary.get('failed_test_cases', 0)
            inconclusive = total_tests - passed_tests - failed_tests
            
            result_headers = ['Test Result', 'Count', 'Percentage']
            result_data = [
                ['Passed', str(passed_tests), f"{(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%"],
                ['Failed', str(failed_tests), f"{(failed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%"],
                ['Inconclusive', str(inconclusive), f"{(inconclusive/total_tests*100) if total_tests > 0 else 0:.1f}%"],
                ['', '', ''],  # Separator
                ['Total', str(total_tests), '100.0%']
            ]
            
            result_table = self._create_data_table(
                result_headers,
                result_data,
                col_widths=[2*inch, 2*inch, 2.25*inch]
            )
            elements.append(result_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Test case details
        if data.get('test_cases'):
            elements.append(Paragraph("TEST CASE DETAILS", self.styles['SubsectionHeader']))
            
            test_headers = ['Test ID', 'Attribute', 'Test Type', 'Result', 'Evidence']
            test_data = []
            
            for test in data['test_cases'][:30]:  # Show first 30
                test_data.append([
                    str(test.get('test_id', '')),
                    test.get('attribute_name', '')[:25],
                    test.get('test_type', 'Standard'),
                    'PASS ✓' if test.get('result') == 'pass' else 'FAIL ✗',
                    'Yes' if test.get('has_evidence') else 'No'
                ])
            
            if test_data:
                test_table = self._create_data_table(
                    test_headers,
                    test_data,
                    col_widths=[0.8*inch, 2*inch, 1.5*inch, 0.95*inch, 1*inch]
                )
                elements.append(test_table)
        
        return elements
    
    def _create_observation_management_phase(self, data: Dict[str, Any]) -> List[Flowable]:
        """Create observation management phase section"""
        elements = []
        
        elements.append(ConditionalPageBreak(4*inch))
        elements.append(Paragraph("OBSERVATION MANAGEMENT PHASE RESULTS", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.25*inch))
        
        # What Actually Happened
        if data.get('what_actually_happened'):
            what_happened_box = self._create_commentary_box(
                "WHAT ACTUALLY HAPPENED",
                data['what_actually_happened'],
                ReportColors.INFO_BLUE,
                ReportColors.LIGHT_BLUE_BG
            )
            elements.append(what_happened_box)
            elements.append(Spacer(1, 0.25*inch))
        
        # Observation summary
        if data.get('summary'):
            summary = data['summary']
            
            elements.append(Paragraph("OBSERVATION METRICS", self.styles['SubsectionHeader']))
            
            total_obs = summary.get('total_observations', 0)
            critical = summary.get('critical_observations', 0)
            high = summary.get('high_observations', 0)
            medium = summary.get('medium_observations', 0)
            low = summary.get('low_observations', 0)
            resolved = summary.get('resolved_observations', 0)
            
            obs_headers = ['Severity', 'Count', 'Percentage', 'Status']
            obs_data = [
                ['Critical', str(critical), f"{(critical/total_obs*100) if total_obs > 0 else 0:.1f}%", 'Immediate action required'],
                ['High', str(high), f"{(high/total_obs*100) if total_obs > 0 else 0:.1f}%", 'Priority remediation'],
                ['Medium', str(medium), f"{(medium/total_obs*100) if total_obs > 0 else 0:.1f}%", 'Standard remediation'],
                ['Low', str(low), f"{(low/total_obs*100) if total_obs > 0 else 0:.1f}%", 'Monitor'],
                ['', '', '', ''],  # Separator
                ['Total', str(total_obs), '100.0%', f'{resolved} resolved ({(resolved/total_obs*100) if total_obs > 0 else 0:.1f}%)']
            ]
            
            obs_table = self._create_data_table(
                obs_headers,
                obs_data,
                col_widths=[1.25*inch, 1*inch, 1.5*inch, 2.5*inch]
            )
            elements.append(obs_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Observation details
        if data.get('observations'):
            elements.append(Paragraph("OBSERVATION DETAILS", self.styles['SubsectionHeader']))
            
            obs_detail_headers = ['ID', 'Title', 'Severity', 'Status', 'Owner']
            obs_detail_data = []
            
            for obs in data['observations'][:20]:  # Show first 20
                obs_detail_data.append([
                    str(obs.get('observation_id', '')),
                    obs.get('title', '')[:30],
                    obs.get('severity', 'Medium'),
                    obs.get('status', 'Open').upper(),
                    obs.get('assigned_to', 'Unassigned')
                ])
            
            if obs_detail_data:
                detail_table = self._create_data_table(
                    obs_detail_headers,
                    obs_detail_data,
                    col_widths=[0.6*inch, 2.5*inch, 0.9*inch, 1*inch, 1.25*inch]
                )
                elements.append(detail_table)
        
        return elements
    
    def generate_comprehensive_report(self, report_data: Dict[str, Any]) -> bytes:
        """Generate the complete comprehensive test report"""
        try:
            # Create buffer
            buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=self.left_margin,
                rightMargin=self.right_margin,
                topMargin=self.top_margin,
                bottomMargin=self.bottom_margin,
                title="Comprehensive Test Report"
            )
            
            # Build content
            elements = []
            
            # Cover page
            elements.extend(self._create_cover_page(report_data))
            
            # Executive summary
            if 'executive_summary' in report_data:
                elements.extend(self._create_executive_summary(report_data['executive_summary']))
            
            # Planning phase
            if 'planning' in report_data:
                elements.extend(self._create_planning_phase(report_data['planning']))
            
            # Data profiling phase
            if 'data_profiling' in report_data:
                elements.extend(self._create_data_profiling_phase(report_data['data_profiling']))
            
            # Scoping phase
            if 'scoping' in report_data:
                elements.extend(self._create_scoping_phase(report_data['scoping']))
            
            # Sample selection phase
            if 'sample_selection' in report_data:
                elements.extend(self._create_sample_selection_phase(report_data['sample_selection']))
            
            # Request info phase - skip for now as it's minimal
            
            # Test execution phase
            if 'test_execution' in report_data:
                elements.extend(self._create_test_execution_phase(report_data['test_execution']))
            
            # Observation management phase
            if 'observation_management' in report_data:
                elements.extend(self._create_observation_management_phase(report_data['observation_management']))
            
            # Build PDF
            doc.build(elements, onFirstPage=self._add_header_footer, 
                     onLaterPages=self._add_header_footer)
            
            # Return PDF bytes
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise