"""
Unified Test Report Service
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select

from app.models.test_report import TestReportSection, TestReportGeneration, STANDARD_REPORT_SECTIONS
from app.models.workflow import WorkflowPhase
from app.models.user import User
from app.core.database import get_db
from app.core.logging import get_logger
from app.services.enhanced_report_generation_service import EnhancedReportGenerationService
from app.services.comprehensive_data_collection_service import ComprehensiveDataCollectionService

logger = get_logger(__name__)


class TestReportService:
    """Unified service for test report generation and management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.enhanced_generation_service = EnhancedReportGenerationService(db)
        self.data_collection_service = ComprehensiveDataCollectionService(db)
    
    async def generate_test_report(self, phase_id: int, user_id: int, sections: Optional[List[str]] = None) -> TestReportGeneration:
        """Generate complete test report with all sections"""
        
        # Get or create generation record
        result = await self.db.execute(
            select(TestReportGeneration).where(
                TestReportGeneration.phase_id == phase_id
            )
        )
        generation = result.scalar_one_or_none()
        
        if not generation:
            # Get phase information
            phase_result = await self.db.execute(
                select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
            )
            phase = phase_result.scalar_one_or_none()
            if not phase:
                raise ValueError(f"Phase {phase_id} not found")
            
            generation = TestReportGeneration(
                phase_id=phase_id,
                cycle_id=phase.cycle_id,
                report_id=phase.report_id,
                generated_by=user_id
            )
            self.db.add(generation)
            await self.db.commit()
        
        # Start generation
        generation.start_generation(user_id)
        await self.db.commit()
        
        try:
            # Determine sections to generate
            sections_to_generate = sections if sections else [s['name'] for s in STANDARD_REPORT_SECTIONS]
            
            # Generate each section
            generated_sections = []
            for section_name in sections_to_generate:
                section = await self.generate_section(phase_id, section_name, user_id)
                generated_sections.append(section)
            
            # Update generation status
            generation.complete_generation(len(sections_to_generate), len(generated_sections))
            
            # Update output formats
            generation.output_formats_generated = ['json', 'markdown', 'html']
            
            await self.db.commit()
            
            return generation
            
        except Exception as e:
            # Mark generation as failed
            generation.fail_generation(str(e))
            await self.db.commit()
            raise
    
    async def generate_section(self, phase_id: int, section_name: str, user_id: int) -> TestReportSection:
        """Generate or update a specific section"""
        
        # Get phase information
        phase_result = await self.db.execute(
            select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        )
        phase = phase_result.scalar_one_or_none()
        if not phase:
            raise ValueError(f"Phase {phase_id} not found")
        
        # Get section configuration
        section_config = next((s for s in STANDARD_REPORT_SECTIONS if s['name'] == section_name), None)
        if not section_config:
            raise ValueError(f"Unknown section: {section_name}")
        
        # Get or create section record
        section_result = await self.db.execute(
            select(TestReportSection).where(
                and_(
                    TestReportSection.phase_id == phase_id,
                    TestReportSection.section_name == section_name
                )
            )
        )
        section = section_result.scalar_one_or_none()
        
        if not section:
            section = TestReportSection(
                phase_id=phase_id,
                cycle_id=phase.cycle_id,
                report_id=phase.report_id,
                section_name=section_name,
                section_title=section_config['title'],
                section_order=section_config['order'],
                section_type='standard',
                section_content={},
                created_by_id=user_id,
                updated_by_id=user_id
            )
            self.db.add(section)
        
        # Generate section content
        section_data = await self.collect_section_data(phase_id, section_name)
        
        # Update section
        section.section_content = section_data
        section.data_sources = section_config.get('data_sources', [])
        section.last_generated_at = datetime.utcnow()
        section.requires_refresh = False
        section.status = 'generated'
        section.updated_by_id = user_id
        
        # Generate output formats
        section.markdown_content = self.generate_markdown_content(section_data)
        section.html_content = self.generate_html_content(section_data)
        
        await self.db.commit()
        
        return section
    
    async def collect_section_data(self, phase_id: int, section_name: str) -> Dict[str, Any]:
        """Collect data for specific section from all phases"""
        
        # Get phase information
        phase_result = await self.db.execute(
            select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        )
        phase = phase_result.scalar_one_or_none()
        if not phase:
            raise ValueError(f"Phase {phase_id} not found")
        
        # For now, return placeholder data - would be replaced with actual data collection
        return {
            "summary": f"Summary for {section_name}",
            "content": f"Content for {section_name} in phase {phase_id}",
            "metrics": {
                "total_items": 100,
                "completed_items": 85,
                "success_rate": 0.85
            },
            "data_sources": [section_name]
        }
    
    async def generate_comprehensive_report(self, phase_id: int, user_id: int, sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate comprehensive test report using enhanced services"""
        
        # Get phase information
        phase_result = await self.db.execute(
            select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        )
        phase = phase_result.scalar_one_or_none()
        if not phase:
            raise ValueError(f"Phase {phase_id} not found")
        
        # Generate comprehensive report using enhanced service
        comprehensive_report = await self.enhanced_generation_service.generate_comprehensive_report(
            cycle_id=phase.cycle_id,
            report_id=phase.report_id,
            phase_id=phase_id,
            user_id=user_id
        )
        
        # Create or update generation record
        generation_result = await self.db.execute(
            select(TestReportGeneration).where(
                TestReportGeneration.phase_id == phase_id
            )
        )
        generation = generation_result.scalar_one_or_none()
        
        if not generation:
            generation = TestReportGeneration(
                phase_id=phase_id,
                cycle_id=phase.cycle_id,
                report_id=phase.report_id,
                generated_by=user_id
            )
            self.db.add(generation)
        
        # Start generation
        generation.start_generation(user_id)
        
        try:
            # Create sections from comprehensive report
            section_count = 0
            for section_name, section_data in comprehensive_report["sections"].items():
                # Get or create section record
                section_result = await self.db.execute(
                    select(TestReportSection).where(
                        and_(
                            TestReportSection.phase_id == phase_id,
                            TestReportSection.section_name == section_name
                        )
                    )
                )
                section = section_result.scalar_one_or_none()
                
                if not section:
                    section = TestReportSection(
                        phase_id=phase_id,
                        cycle_id=phase.cycle_id,
                        report_id=phase.report_id,
                        section_name=section_name,
                        section_title=section_data.get("section_title", section_name.replace("_", " ").title()),
                        section_order=section_data.get("section_order", section_count + 1),
                        section_type='standard',
                        section_content=section_data.get("content", {}),
                        created_by_id=user_id,
                        updated_by_id=user_id
                    )
                    self.db.add(section)
                else:
                    # Update existing section
                    section.section_content = section_data.get("content", {})
                    section.updated_by_id = user_id
                
                # Generate output formats
                section.markdown_content = self.generate_markdown_from_structured_data(section_data)
                section.html_content = self.generate_html_from_structured_data(section_data)
                section.last_generated_at = datetime.utcnow()
                section.status = 'generated'
                
                section_count += 1
            
            # Complete generation
            generation.complete_generation(section_count, section_count)
            generation.output_formats_generated = ['json', 'markdown', 'html']
            
            await self.db.commit()
            
            return {
                "generation": generation,
                "comprehensive_data": comprehensive_report["comprehensive_data"],
                "sections": comprehensive_report["sections"],
                "generation_metadata": comprehensive_report["generation_metadata"]
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Error in generate_comprehensive_report: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            generation.fail_generation(str(e))
            await self.db.commit()
            raise
    
    def generate_markdown_from_structured_data(self, section_data: Dict[str, Any]) -> str:
        """Generate markdown content from structured section data"""
        
        content = section_data.get("content", {})
        tables = section_data.get("tables", [])
        
        markdown = f"# {section_data.get('section_title', 'Report Section')}\n\n"
        
        # Add summary if available
        if content.get("summary"):
            markdown += "## Summary\n\n"
            if isinstance(content["summary"], dict):
                for key, value in content["summary"].items():
                    markdown += f"- **{key.replace('_', ' ').title()}**: {value}\n"
            else:
                markdown += f"{content['summary']}\n"
            markdown += "\n"
        
        # Add key findings if available
        if content.get("key_findings"):
            markdown += "## Key Findings\n\n"
            for finding in content["key_findings"]:
                markdown += f"- {finding}\n"
            markdown += "\n"
        
        # Add tables
        for table in tables:
            markdown += f"## {table.get('title', 'Table')}\n\n"
            
            if table.get("headers") and table.get("rows"):
                # Create markdown table
                headers = table["headers"]
                markdown += "| " + " | ".join(headers) + " |\n"
                markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                
                for row in table["rows"]:
                    markdown += "| " + " | ".join(str(cell) for cell in row) + " |\n"
                markdown += "\n"
        
        return markdown
    
    def generate_html_from_structured_data(self, section_data: Dict[str, Any]) -> str:
        """Generate HTML content from structured section data"""
        
        content = section_data.get("content", {})
        tables = section_data.get("tables", [])
        
        html = f"<div class='report-section'>\n"
        html += f"<h1>{section_data.get('section_title', 'Report Section')}</h1>\n\n"
        
        # Add summary if available
        if content.get("summary"):
            html += "<h2>Summary</h2>\n"
            if isinstance(content["summary"], dict):
                html += "<ul>\n"
                for key, value in content["summary"].items():
                    html += f"<li><strong>{key.replace('_', ' ').title()}</strong>: {value}</li>\n"
                html += "</ul>\n"
            else:
                html += f"<p>{content['summary']}</p>\n"
        
        # Add key findings if available
        if content.get("key_findings"):
            html += "<h2>Key Findings</h2>\n<ul>\n"
            for finding in content["key_findings"]:
                html += f"<li>{finding}</li>\n"
            html += "</ul>\n"
        
        # Add tables
        for table in tables:
            html += f"<h2>{table.get('title', 'Table')}</h2>\n"
            
            if table.get("headers") and table.get("rows"):
                html += "<table class='report-table'>\n"
                
                # Headers
                html += "<thead>\n<tr>\n"
                for header in table["headers"]:
                    html += f"<th>{header}</th>\n"
                html += "</tr>\n</thead>\n"
                
                # Rows
                html += "<tbody>\n"
                for row in table["rows"]:
                    html += "<tr>\n"
                    for cell in row:
                        html += f"<td>{cell}</td>\n"
                    html += "</tr>\n"
                html += "</tbody>\n</table>\n"
        
        html += "</div>\n"
        return html
    
    async def approve_section(self, section_id: int, approver_id: int, approval_level: str, notes: str = None) -> TestReportSection:
        """Approve report section at specific level"""
        
        section_result = await self.db.execute(
            select(TestReportSection).where(TestReportSection.id == section_id)
        )
        section = section_result.scalar_one_or_none()
        if not section:
            raise ValueError(f"Section {section_id} not found")
        
        # Check if user is authorized for this approval level
        approver_result = await self.db.execute(
            select(User).where(User.user_id == approver_id)
        )
        approver = approver_result.scalar_one_or_none()
        if not approver:
            raise ValueError(f"Approver {approver_id} not found")
        
        # Approve the section
        if not section.approve_section(approver_id, approval_level, notes):
            raise ValueError(f"Invalid approval level: {approval_level}")
        
        await self.db.commit()
        
        # Check if all sections are approved and update phase completion
        if section.is_fully_approved():
            await self.check_phase_completion(section.phase_id)
        
        return section
    
    async def check_phase_completion(self, phase_id: int) -> bool:
        """Check if all sections are approved and phase can be completed"""
        
        # Get all sections for this phase
        sections_result = await self.db.execute(
            select(TestReportSection).where(
                TestReportSection.phase_id == phase_id
            )
        )
        sections = sections_result.scalars().all()
        
        # Check if all sections are fully approved
        all_approved = all(section.is_fully_approved() for section in sections)
        
        if all_approved:
            # Update generation record
            generation_result = await self.db.execute(
                select(TestReportGeneration).where(
                    TestReportGeneration.phase_id == phase_id
                )
            )
            generation = generation_result.scalar_one_or_none()
            
            if generation:
                generation.all_approvals_received = True
                generation.phase_completion_ready = True
                await self.db.commit()
            
            # Update phase status
            phase_result = await self.db.execute(
                select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
            )
            phase = phase_result.scalar_one_or_none()
            if phase:
                phase.status = 'Complete'
                phase.state = 'Complete'
                phase.actual_end_date = datetime.utcnow()
                await self.db.commit()
        
        return all_approved
    
    async def generate_final_report(self, phase_id: int) -> str:
        """Generate final PDF report from all sections"""
        
        # Get all sections
        sections_result = await self.db.execute(
            select(TestReportSection).where(
                TestReportSection.phase_id == phase_id
            ).order_by(TestReportSection.section_order)
        )
        sections = sections_result.scalars().all()
        
        # Ensure all sections are approved
        if not all(section.is_fully_approved() for section in sections):
            raise ValueError("All sections must be approved before final report generation")
        
        # Generate PDF (placeholder - would integrate with PDF generation service)
        pdf_path = f"/reports/final_report_{phase_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Update generation metadata
        generation_result = await self.db.execute(
            select(TestReportGeneration).where(
                TestReportGeneration.phase_id == phase_id
            )
        )
        generation = generation_result.scalar_one_or_none()
        
        if generation:
            if generation.output_formats_generated is None:
                generation.output_formats_generated = []
            generation.output_formats_generated.append('pdf')
            generation.phase_completion_ready = True
            await self.db.commit()
        
        return pdf_path
    
    async def get_section_by_id(self, section_id: int) -> Optional[TestReportSection]:
        """Get section by ID"""
        result = await self.db.execute(
            select(TestReportSection).where(TestReportSection.id == section_id)
        )
        return result.scalar_one_or_none()
    
    async def get_sections_by_phase(self, phase_id: int) -> List[TestReportSection]:
        """Get all sections for a phase"""
        result = await self.db.execute(
            select(TestReportSection).where(
                TestReportSection.phase_id == phase_id
            ).order_by(TestReportSection.section_order)
        )
        return result.scalars().all()
    
    async def get_generation_by_phase(self, phase_id: int) -> Optional[TestReportGeneration]:
        """Get generation record by phase"""
        result = await self.db.execute(
            select(TestReportGeneration).where(
                TestReportGeneration.phase_id == phase_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_approval_status(self, phase_id: int) -> Dict[str, Any]:
        """Get approval status for all sections"""
        sections = await self.get_sections_by_phase(phase_id)
        
        approval_status = {
            'total_sections': len(sections),
            'fully_approved': sum(1 for s in sections if s.is_fully_approved()),
            'sections': []
        }
        
        for section in sections:
            approval_status['sections'].append({
                'id': section.id,
                'name': section.section_name,
                'title': section.section_title,
                'status': section.status,
                'approval_status': section.get_approval_status(),
                'next_approver': section.get_next_approver_level(),
                'tester_approved': section.tester_approved,
                'report_owner_approved': section.report_owner_approved,
                'executive_approved': section.executive_approved
            })
        
        return approval_status
    
    # Output format generation methods
    def generate_markdown_content(self, section_data: Dict[str, Any]) -> str:
        """Generate markdown content from section data"""
        content = section_data.get('content', '')
        summary = section_data.get('summary', '')
        
        markdown = f"# {summary}\n\n{content}\n\n"
        
        # Add metrics
        if 'metrics' in section_data:
            markdown += "## Metrics\n\n"
            for key, value in section_data['metrics'].items():
                markdown += f"- **{key.replace('_', ' ').title()}**: {value}\n"
            markdown += "\n"
        
        # Add tables
        if 'tables' in section_data:
            for table in section_data['tables']:
                markdown += f"## {table['title']}\n\n"
                headers = table.get('headers', [])
                rows = table.get('rows', [])
                
                if headers:
                    markdown += "| " + " | ".join(headers) + " |\n"
                    markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                    
                    for row in rows:
                        markdown += "| " + " | ".join(str(cell) for cell in row) + " |\n"
                
                markdown += "\n"
        
        return markdown
    
    def generate_html_content(self, section_data: Dict[str, Any]) -> str:
        """Generate HTML content from section data"""
        content = section_data.get('content', '')
        summary = section_data.get('summary', '')
        
        html = f"<h1>{summary}</h1>\n<p>{content}</p>\n"
        
        # Add metrics
        if 'metrics' in section_data:
            html += "<h2>Metrics</h2>\n<ul>\n"
            for key, value in section_data['metrics'].items():
                html += f"<li><strong>{key.replace('_', ' ').title()}</strong>: {value}</li>\n"
            html += "</ul>\n"
        
        # Add tables
        if 'tables' in section_data:
            for table in section_data['tables']:
                html += f"<h2>{table['title']}</h2>\n"
                headers = table.get('headers', [])
                rows = table.get('rows', [])
                
                if headers:
                    html += "<table>\n<thead>\n<tr>\n"
                    for header in headers:
                        html += f"<th>{header}</th>\n"
                    html += "</tr>\n</thead>\n<tbody>\n"
                    
                    for row in rows:
                        html += "<tr>\n"
                        for cell in row:
                            html += f"<td>{cell}</td>\n"
                        html += "</tr>\n"
                    
                    html += "</tbody>\n</table>\n"
        
        return html


# Legacy service for backward compatibility
class LegacyTestReportService:
    """Legacy test report service - deprecated, use TestReportService instead"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.new_service = TestReportService(db)
    
    async def generate_test_report(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Legacy method - generates basic report data"""
        
        # Get the test report phase
        phase_result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Finalize Test Report'
                )
            )
        )
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise ValueError(f"Test report phase not found for cycle {cycle_id}, report {report_id}")
        
        # Use new service to generate report
        generation = await self.new_service.generate_test_report(phase.phase_id, 1)  # Default user
        
        # Return legacy format
        return {
            "raw_data": {
                "metadata": {
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "generation_date": generation.created_at.isoformat()
                },
                "executive_summary": {
                    "total_attributes_tested": 100,
                    "test_execution_rate": 85,
                    "total_observations": 0
                }
            },
            "formatted_report": {
                "generation_id": generation.id,
                "status": generation.status,
                "sections_count": generation.total_sections or 0
            }
        }