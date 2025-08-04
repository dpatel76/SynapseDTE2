"""
External Prompt Management Service
Handles loading and formatting of external prompt templates
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from string import Template
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages external prompt templates for LLM operations with regulatory report support"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._templates_cache: Dict[str, Template] = {}
        
    def load_prompt_template(self, template_name: str, regulatory_report: Optional[str] = None, 
                           schedule: Optional[str] = None) -> Optional[Template]:
        """Load a prompt template from external file with regulatory report support"""
        
        # Build cache key including regulatory context
        cache_key = self._build_cache_key(template_name, regulatory_report, schedule)
        
        # Check cache first
        if cache_key in self._templates_cache:
            return self._templates_cache[cache_key]
        
        # Try to load regulatory-specific template first
        template_path = self._get_template_path(template_name, regulatory_report, schedule)
        
        if not template_path or not template_path.exists():
            # Fall back to generic template
            template_path = self.prompts_dir / f"{template_name}.txt"
            
        if not template_path.exists():
            logger.error(f"Prompt template not found: {template_path}")
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            template = Template(template_content)
            self._templates_cache[cache_key] = template
            logger.info(f"Loaded prompt template: {cache_key} from {template_path}")
            logger.debug(f"Template content preview (first 200 chars): {template_content[:200]}...")
            return template
            
        except Exception as e:
            logger.error(f"Error loading prompt template {template_name}: {str(e)}")
            return None
    
    def _build_cache_key(self, template_name: str, regulatory_report: Optional[str] = None,
                        schedule: Optional[str] = None) -> str:
        """Build cache key for template"""
        parts = [template_name]
        if regulatory_report:
            parts.append(regulatory_report.lower().replace(' ', '_').replace('-', '_'))
        if schedule:
            # Handle dots in schedule names consistently with path resolution
            parts.append(schedule.lower().replace(' ', '_').replace('.', '_'))
        return "_".join(parts)
    
    def _get_template_path(self, template_name: str, regulatory_report: Optional[str] = None,
                          schedule: Optional[str] = None) -> Optional[Path]:
        """Get the path for a regulatory-specific template"""
        if not regulatory_report:
            return None
            
        # Normalize regulatory report name (e.g., "FR Y-14M" -> "fr_y_14m")
        report_dir = regulatory_report.lower().replace(' ', '_').replace('-', '_')
        
        if schedule:
            # Try schedule-specific path first
            # Handle dots in schedule names (e.g., "Schedule D.1" -> "schedule_d_1")
            schedule_dir = schedule.lower().replace(' ', '_').replace('.', '_')
            specific_path = self.prompts_dir / "regulatory" / report_dir / schedule_dir / f"{template_name}.txt"
            if specific_path.exists():
                return specific_path
            
        # Try report-level common path
        common_path = self.prompts_dir / "regulatory" / report_dir / "common" / f"{template_name}.txt"
        if common_path.exists():
            return common_path
            
        return None
    
    def format_prompt(self, template_name: str, regulatory_report: Optional[str] = None,
                     schedule: Optional[str] = None, **kwargs) -> Optional[str]:
        """Format a prompt template with provided parameters and regulatory context"""
        
        template = self.load_prompt_template(template_name, regulatory_report, schedule)
        if not template:
            return None
        
        try:
            # Replace missing keys with empty strings to avoid KeyError
            safe_kwargs = {}
            for key, value in kwargs.items():
                if value is None:
                    safe_kwargs[key] = ""
                else:
                    safe_kwargs[key] = str(value)
            
            formatted_prompt = template.safe_substitute(**safe_kwargs)
            logger.debug(f"Formatted prompt template: {template_name}")
            return formatted_prompt
            
        except Exception as e:
            logger.error(f"Error formatting prompt template {template_name}: {str(e)}")
            return None
    
    def get_available_templates(self) -> list[str]:
        """Get list of available prompt templates"""
        
        if not self.prompts_dir.exists():
            return []
        
        templates = []
        for file_path in self.prompts_dir.glob("*.txt"):
            templates.append(file_path.stem)
        
        return sorted(templates)
    
    def clear_cache(self):
        """Clear the templates cache"""
        self._templates_cache.clear()
        logger.info("Prompt templates cache cleared")


# Global prompt manager instance
prompt_manager = PromptManager()


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance"""
    return prompt_manager


# Convenience functions for common operations
def load_attribute_generation_prompt(regulatory_report: Optional[str] = None, 
                                   schedule: Optional[str] = None, **kwargs) -> Optional[str]:
    """Load and format attribute generation prompt with regulatory support"""
    return prompt_manager.format_prompt("attribute_generation", regulatory_report, schedule, **kwargs)


def load_scoping_recommendations_prompt(regulatory_report: Optional[str] = None,
                                      schedule: Optional[str] = None, **kwargs) -> Optional[str]:
    """Load and format scoping recommendations prompt with regulatory support"""
    return prompt_manager.format_prompt("scoping_recommendations", regulatory_report, schedule, **kwargs)


def load_document_extraction_prompt(regulatory_report: Optional[str] = None,
                                  schedule: Optional[str] = None, **kwargs) -> Optional[str]:
    """Load and format document extraction prompt with regulatory support"""
    return prompt_manager.format_prompt("document_extraction", regulatory_report, schedule, **kwargs)


def load_sample_generation_prompt(regulatory_report: Optional[str] = None,
                                schedule: Optional[str] = None, **kwargs) -> Optional[str]:
    """Load and format sample generation prompt with regulatory support"""
    return prompt_manager.format_prompt("sample_generation", regulatory_report, schedule, **kwargs) 