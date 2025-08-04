# ReportLab Implementation Guide for Professional Test Reports

## Overview
This guide provides specific ReportLab code patterns to implement the professional design standards defined in our design documents.

## Table of Contents
1. [Setup and Configuration](#setup-and-configuration)
2. [Custom Styles](#custom-styles)
3. [Component Templates](#component-templates)
4. [Table Formatting](#table-formatting)
5. [Text Management](#text-management)
6. [Page Layout](#page-layout)
7. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Setup and Configuration

### Required Imports
```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image, Flowable
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
```

### Document Setup
```python
class ProfessionalTestReport:
    def __init__(self, filename):
        self.filename = filename
        self.page_width = letter[0]
        self.page_height = letter[1]
        
        # Professional margins
        self.left_margin = 1.25 * inch
        self.right_margin = 1.0 * inch
        self.top_margin = 1.0 * inch
        self.bottom_margin = 1.0 * inch
        
        # Content width calculation
        self.content_width = self.page_width - self.left_margin - self.right_margin
        
        # Initialize document
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            leftMargin=self.left_margin,
            rightMargin=self.right_margin,
            topMargin=self.top_margin,
            bottomMargin=self.bottom_margin
        )
```

---

## Custom Styles

### Color Palette
```python
class ReportColors:
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
```

### Text Styles
```python
def create_custom_styles():
    styles = getSampleStyleSheet()
    
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
        leftIndent=12,
        rightIndent=12,
        spaceAfter=12,
        leading=16.5
    ))
    
    return styles
```

---

## Component Templates

### 1. Executive Commentary Box
```python
def create_commentary_box(title, content, box_color=ReportColors.INFO_BLUE):
    """Creates a professional commentary box with colored header"""
    
    # Header data
    header_data = [[title]]
    
    # Content data
    content_data = [[Paragraph(content, styles['Commentary'])]]
    
    # Create header table
    header_table = Table(header_data, colWidths=[6.25*inch])
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
    
    # Create content table
    content_table = Table(content_data, colWidths=[6.25*inch])
    content_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ReportColors.LIGHT_BLUE_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, box_color),
    ]))
    
    # Combine tables
    combined = Table([[header_table], [content_table]], colWidths=[6.25*inch])
    combined.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    return combined
```

### 2. Metrics Dashboard
```python
def create_metrics_dashboard(metrics_data):
    """Creates a metrics dashboard with cards"""
    
    # Create individual metric cards
    cards = []
    for metric in metrics_data:
        card_data = [
            [metric['value']],
            [metric['label']]
        ]
        
        card = Table(card_data, colWidths=[1.5*inch], rowHeights=[0.6*inch, 0.4*inch])
        card.setStyle(TableStyle([
            # Value styling
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 24),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (0, 0), ReportColors.NAVY_BLUE),
            
            # Label styling
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, 1), 10),
            ('ALIGN', (0, 1), (0, 1), 'CENTER'),
            ('TEXTCOLOR', (0, 1), (0, 1), ReportColors.CORPORATE_GRAY),
            
            # Box styling
            ('BOX', (0, 0), (-1, -1), 1, ReportColors.LIGHT_GRAY),
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
    
    dashboard = Table(rows, colWidths=[1.5*inch]*4, spaceBefore=12, spaceAfter=12)
    
    return dashboard
```

### 3. Professional Data Table
```python
def create_data_table(headers, data, col_widths=None, highlight_rows=None):
    """Creates a professional data table with proper formatting"""
    
    # Calculate column widths if not provided
    if col_widths is None:
        col_widths = calculate_column_widths(headers, data)
    
    # Ensure no text truncation
    wrapped_data = []
    for row in data:
        wrapped_row = []
        for i, cell in enumerate(row):
            if isinstance(cell, str) and len(cell) > 30:
                # Wrap long text
                wrapped_row.append(Paragraph(cell, styles['BodyText']))
            else:
                wrapped_row.append(cell)
        wrapped_data.append(wrapped_row)
    
    # Combine headers and data
    table_data = [headers] + wrapped_data
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Style configuration
    style_commands = [
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), ReportColors.NAVY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), ReportColors.CORPORATE_GRAY),
        
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
            style_commands.append(
                ('BACKGROUND', (0, row_idx), (-1, row_idx), ReportColors.WARNING_ORANGE)
            )
    
    table.setStyle(TableStyle(style_commands))
    
    return table
```

---

## Table Formatting

### Column Width Calculation
```python
def calculate_column_widths(headers, data, max_width=6.25*inch):
    """Intelligently calculate column widths to prevent truncation"""
    
    from reportlab.pdfbase.pdfmetrics import stringWidth
    
    col_count = len(headers)
    min_widths = []
    
    # Calculate minimum width for each column
    for i in range(col_count):
        max_width_needed = stringWidth(headers[i], 'Helvetica-Bold', 12)
        
        for row in data:
            if i < len(row):
                cell_text = str(row[i])
                width_needed = stringWidth(cell_text, 'Helvetica', 10)
                max_width_needed = max(max_width_needed, width_needed)
        
        # Add padding
        min_widths.append(max_width_needed + 12)
    
    # Distribute width proportionally
    total_min_width = sum(min_widths)
    
    if total_min_width <= max_width:
        # We have enough space
        return min_widths
    else:
        # Need to compress - maintain proportions
        scale_factor = max_width / total_min_width
        return [w * scale_factor for w in min_widths]
```

### Smart Text Abbreviation
```python
def abbreviate_intelligently(text, max_length=30):
    """Abbreviate text intelligently without breaking words"""
    
    if len(text) <= max_length:
        return text
    
    # Common abbreviations
    abbreviations = {
        'Account': 'Acct',
        'Number': 'Num',
        'Credit': 'Cr',
        'Debit': 'Dr',
        'Status': 'Sts',
        'Information': 'Info',
        'Management': 'Mgmt',
        'Customer': 'Cust',
        'Reference': 'Ref',
        'Percentage': '%',
        'Amount': 'Amt',
        'Transaction': 'Txn',
        'Department': 'Dept',
        'Organization': 'Org'
    }
    
    # Apply abbreviations
    result = text
    for full, abbr in abbreviations.items():
        result = result.replace(full, abbr)
    
    # If still too long, truncate at word boundary
    if len(result) > max_length:
        words = result.split()
        truncated = ''
        for word in words:
            if len(truncated + ' ' + word) <= max_length - 3:
                truncated = (truncated + ' ' + word).strip()
            else:
                break
        result = truncated + '...'
    
    return result
```

---

## Text Management

### Preventing Text Overflow
```python
def create_wrapped_cell(text, width, style='BodyText'):
    """Create a cell that wraps text properly"""
    
    # Calculate required height
    para = Paragraph(text, styles[style])
    w, h = para.wrap(width, 10000)  # Large height to get actual needed height
    
    return para, h

def create_auto_height_table(headers, data, col_widths):
    """Create table with automatic row heights based on content"""
    
    table_data = [headers]
    row_heights = [None]  # Auto height for header
    
    for row in data:
        new_row = []
        max_height = 20  # Minimum row height
        
        for i, cell in enumerate(row):
            if isinstance(cell, str) and len(cell) > 30:
                para, height = create_wrapped_cell(cell, col_widths[i])
                new_row.append(para)
                max_height = max(max_height, height + 12)  # Add padding
            else:
                new_row.append(cell)
        
        table_data.append(new_row)
        row_heights.append(max_height)
    
    return Table(table_data, colWidths=col_widths, rowHeights=row_heights)
```

---

## Page Layout

### Header and Footer
```python
def add_header_footer(canvas, doc):
    """Add professional header and footer to each page"""
    
    canvas.saveState()
    
    # Header
    canvas.setFont('Helvetica-Bold', 14)
    canvas.setFillColor(ReportColors.NAVY_BLUE)
    canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 0.5*inch,
                     "FR Y-14M Schedule D.1 Test Report")
    
    canvas.setFont('Helvetica', 10)
    canvas.setFillColor(ReportColors.CORPORATE_GRAY)
    canvas.drawRightString(doc.width + doc.rightMargin, 
                          doc.height + doc.topMargin - 0.5*inch,
                          f"Page {doc.page}")
    
    # Footer
    canvas.setFont('Helvetica-Oblique', 9)
    canvas.drawString(doc.leftMargin, doc.bottomMargin - 0.5*inch,
                     "CONFIDENTIAL - INTERNAL USE ONLY")
    
    canvas.drawRightString(doc.width + doc.rightMargin,
                          doc.bottomMargin - 0.5*inch,
                          f"Generated: {datetime.now().strftime('%B %d, %Y')}")
    
    # Footer line
    canvas.setStrokeColor(ReportColors.LIGHT_GRAY)
    canvas.line(doc.leftMargin, doc.bottomMargin, 
                doc.width + doc.rightMargin, doc.bottomMargin)
    
    canvas.restoreState()
```

### Page Breaks
```python
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
```

---

## Common Issues and Solutions

### Issue 1: Text Truncation in Tables
```python
# Problem: "Credit Card Workout Progr..."
# Solution: Use Paragraph objects for long text

# Bad
table_data = [["Credit Card Workout Program Status"]]

# Good
table_data = [[Paragraph("Credit Card Workout Program Status", styles['BodyText'])]]
```

### Issue 2: Inconsistent Spacing
```python
# Problem: Irregular gaps between sections
# Solution: Use consistent Spacer objects

elements = []
elements.append(Paragraph("Section 1", styles['SectionHeader']))
elements.append(Spacer(1, 0.25*inch))  # Consistent spacing
elements.append(content1)
elements.append(Spacer(1, 0.5*inch))   # Larger gap between major sections
elements.append(Paragraph("Section 2", styles['SectionHeader']))
```

### Issue 3: Tables Breaking Across Pages
```python
# Problem: Table headers separated from data
# Solution: Use KeepTogether

elements.append(KeepTogether([
    Paragraph("Table Title", styles['SubsectionHeader']),
    Spacer(1, 0.1*inch),
    create_data_table(headers, data[:5])  # Keep first few rows with header
]))
```

### Issue 4: Memory Issues with Large Reports
```python
# Problem: Large reports consuming too much memory
# Solution: Use streaming approach

class StreamingPDFReport:
    def __init__(self, filename):
        self.canvas = canvas.Canvas(filename, pagesize=letter)
        self.y_position = 10*inch  # Start from top
        
    def add_section(self, section_data):
        # Process one section at a time
        if self.y_position < 2*inch:
            self.canvas.showPage()
            self.y_position = 10*inch
        
        # Add section content
        self.draw_section(section_data)
        
    def save(self):
        self.canvas.save()
```

---

## Complete Example: Executive Summary Page

```python
def create_executive_summary_page(report_data):
    """Create a complete executive summary page"""
    
    elements = []
    styles = create_custom_styles()
    
    # Title
    elements.append(Paragraph("EXECUTIVE SUMMARY", styles['SectionHeader']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Plain English explanation box
    plain_english = create_commentary_box(
        "PLAIN ENGLISH EXPLANATION",
        report_data['plain_english_explanation'],
        ReportColors.INFO_BLUE
    )
    elements.append(plain_english)
    elements.append(Spacer(1, 0.25*inch))
    
    # Stakeholders table
    stakeholder_headers = ['Role', 'Name', 'Responsibility']
    stakeholder_data = [
        ['Report Owner', report_data['report_owner'], 'Overall report accuracy'],
        ['Lead Tester', report_data['lead_tester'], 'Test execution'],
        ['Data Provider', report_data['data_provider'], 'Source data quality'],
        ['Data Executive', report_data['data_executive'], 'Data governance']
    ]
    
    elements.append(Paragraph("KEY STAKEHOLDERS", styles['SubsectionHeader']))
    elements.append(create_data_table(stakeholder_headers, stakeholder_data))
    elements.append(Spacer(1, 0.25*inch))
    
    # Metrics dashboard
    metrics = [
        {'value': '118', 'label': 'Total Attrs'},
        {'value': '1', 'label': 'Attrs Tested'},
        {'value': '0.88%', 'label': 'Coverage'},
        {'value': 'HIGH', 'label': 'Risk'}
    ]
    
    elements.append(create_metrics_dashboard(metrics))
    elements.append(Spacer(1, 0.25*inch))
    
    # Risk assessment
    risk_assessment = create_commentary_box(
        "⚠️ CRITICAL RISK ASSESSMENT",
        report_data['risk_assessment'],
        ReportColors.DANGER_RED
    )
    elements.append(risk_assessment)
    
    return elements
```

This implementation guide provides the specific code patterns needed to create professional PDF reports that match our design standards, with no text truncation, consistent formatting, and clear visual hierarchy.