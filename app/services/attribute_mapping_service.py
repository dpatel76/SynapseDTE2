"""
LLM-assisted attribute mapping service
Maps report attributes to physical database columns
"""
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import json

from app.models.data_source import DataSource, AttributeMapping, SecurityClassification
from app.models.report_attribute import ReportAttribute
from app.services.llm_service import HybridLLMService
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AttributeMappingService:
    """Service for mapping report attributes to physical database elements"""
    
    def __init__(self, llm_service: Optional[HybridLLMService] = None):
        self.llm_service = llm_service or HybridLLMService()
    
    async def discover_database_schema(self, data_source: DataSource) -> Dict[str, List[Dict[str, Any]]]:
        """Discover schema information from database"""
        try:
            config = data_source.decrypt_config()
            schema_info = {}
            
            # Based on database type, use appropriate discovery query
            if data_source.source_type.value in ['POSTGRESQL', 'MYSQL']:
                query = """
                    SELECT 
                        table_name,
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    ORDER BY table_name, ordinal_position
                """
                # Execute query using appropriate driver
                # This is a placeholder - actual implementation would use database drivers
                
            elif data_source.source_type.value == 'ORACLE':
                query = """
                    SELECT 
                        table_name,
                        column_name,
                        data_type,
                        nullable,
                        data_default,
                        data_length,
                        data_precision,
                        data_scale
                    FROM all_tab_columns
                    WHERE owner = %s
                    ORDER BY table_name, column_id
                """
            
            # Process results into schema_info dictionary
            # Placeholder for actual database query execution
            schema_info = {
                "sample_table": [
                    {
                        "column_name": "customer_id",
                        "data_type": "integer",
                        "is_nullable": False,
                        "is_primary_key": True
                    },
                    {
                        "column_name": "ssn",
                        "data_type": "varchar",
                        "length": 11,
                        "is_nullable": True
                    }
                ]
            }
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to discover schema: {str(e)}")
            raise
    
    async def suggest_attribute_mappings(
        self, 
        report_id: int,
        data_source_id: str,
        session: AsyncSession
    ) -> List[AttributeMapping]:
        """Use LLM to suggest mappings between attributes and database columns"""
        try:
            # Get report attributes
            attributes_result = await session.execute(
                select(ReportAttribute).filter(
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_active == True
                )
            )
            attributes = attributes_result.scalars().all()
            
            # Get data source
            data_source = await session.get(DataSource, data_source_id)
            if not data_source:
                raise ValueError(f"Data source {data_source_id} not found")
            
            # Discover database schema
            schema_info = await self.discover_database_schema(data_source)
            
            # Prepare context for LLM
            context = {
                "attributes": [
                    {
                        "name": attr.attribute_name,
                        "description": attr.description,
                        "data_type": attr.data_type,
                        "line_item": attr.line_item_number,
                        "technical_name": attr.technical_line_item_name,
                        "keywords": attr.keywords_to_look_for
                    }
                    for attr in attributes
                ],
                "schema": schema_info
            }
            
            # Use LLM to suggest mappings
            prompt = self._build_mapping_prompt(context)
            llm_suggestions = await self.llm_service.analyze_for_mappings(prompt)
            
            # Create AttributeMapping objects
            mappings = []
            for suggestion in llm_suggestions:
                mapping = AttributeMapping(
                    attribute_id=suggestion['attribute_id'],
                    data_source_id=data_source_id,
                    table_name=suggestion['table_name'],
                    column_name=suggestion['column_name'],
                    data_type=suggestion['data_type'],
                    security_classification=self._determine_classification(
                        suggestion['column_name'],
                        suggestion.get('sensitivity_indicators', [])
                    ),
                    mapping_confidence=suggestion['confidence'],
                    llm_suggested=True,
                    column_description=suggestion.get('reasoning', '')
                )
                mappings.append(mapping)
            
            return mappings
            
        except Exception as e:
            logger.error(f"Failed to suggest mappings: {str(e)}")
            raise
    
    def _build_mapping_prompt(self, context: Dict) -> str:
        """Build prompt for LLM to suggest mappings"""
        return f"""
        Given the following report attributes and database schema, suggest mappings between attributes and database columns.
        
        Report Attributes:
        {json.dumps(context['attributes'], indent=2)}
        
        Database Schema:
        {json.dumps(context['schema'], indent=2)}
        
        For each attribute, suggest:
        1. The most likely table and column
        2. Confidence level (0-100)
        3. Security classification indicators (HRCI, Confidential, etc.)
        4. Reasoning for the mapping
        
        Consider:
        - Attribute names and descriptions
        - Data types compatibility
        - Common naming patterns
        - Regulatory terminology
        - Security/sensitivity indicators (SSN, EIN, account numbers, etc.)
        """
    
    def _determine_classification(
        self, 
        column_name: str, 
        sensitivity_indicators: List[str]
    ) -> SecurityClassification:
        """Determine security classification based on column name and indicators"""
        column_lower = column_name.lower()
        
        # HRCI indicators
        hrci_patterns = ['ssn', 'social_security', 'salary', 'compensation', 'wage']
        if any(pattern in column_lower for pattern in hrci_patterns):
            return SecurityClassification.HRCI
        
        # Confidential indicators
        confidential_patterns = ['account', 'ein', 'tax_id', 'phone', 'email', 'address']
        if any(pattern in column_lower for pattern in confidential_patterns):
            return SecurityClassification.CONFIDENTIAL
        
        # Check LLM-provided indicators
        if sensitivity_indicators:
            if any('hrci' in ind.lower() for ind in sensitivity_indicators):
                return SecurityClassification.HRCI
            if any('confidential' in ind.lower() for ind in sensitivity_indicators):
                return SecurityClassification.CONFIDENTIAL
            if any('proprietary' in ind.lower() for ind in sensitivity_indicators):
                return SecurityClassification.PROPRIETARY
        
        return SecurityClassification.PUBLIC
    
    async def validate_mappings(
        self,
        mappings: List[AttributeMapping],
        session: AsyncSession
    ) -> List[Tuple[AttributeMapping, bool, Optional[str]]]:
        """Validate proposed mappings"""
        validation_results = []
        
        for mapping in mappings:
            try:
                # Get data source
                data_source = await session.get(DataSource, mapping.data_source_id)
                
                # Test if table and column exist
                # Placeholder for actual validation query
                exists = True  # Would execute actual query
                
                if exists:
                    mapping.is_validated = True
                    validation_results.append((mapping, True, None))
                else:
                    error = f"Column {mapping.table_name}.{mapping.column_name} not found"
                    mapping.validation_error = error
                    validation_results.append((mapping, False, error))
                    
            except Exception as e:
                error = str(e)
                mapping.validation_error = error
                validation_results.append((mapping, False, error))
        
        return validation_results
    
    async def apply_manual_override(
        self,
        mapping_id: str,
        updates: Dict[str, Any],
        user_id: int,
        session: AsyncSession
    ) -> AttributeMapping:
        """Apply manual override to a mapping"""
        mapping = await session.get(AttributeMapping, mapping_id)
        if not mapping:
            raise ValueError(f"Mapping {mapping_id} not found")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(mapping, key):
                setattr(mapping, key, value)
        
        # Mark as manually overridden
        mapping.manual_override = True
        mapping.updated_by = user_id
        mapping.updated_at = datetime.utcnow()
        
        await session.commit()
        return mapping
    
    async def batch_create_mappings(
        self,
        mappings: List[AttributeMapping],
        session: AsyncSession
    ) -> List[AttributeMapping]:
        """Create multiple mappings in a batch"""
        session.add_all(mappings)
        await session.commit()
        
        # Refresh to get IDs
        for mapping in mappings:
            await session.refresh(mapping)
        
        return mappings
    
    async def get_unmapped_attributes(
        self,
        report_id: int,
        session: AsyncSession
    ) -> List[ReportAttribute]:
        """Get attributes that don't have mappings yet"""
        # Query for attributes without mappings
        result = await session.execute(
            select(ReportAttribute).filter(
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True,
                ~ReportAttribute.attribute_mappings.any()
            )
        )
        return result.scalars().all()


class MappingAnalyzer:
    """Analyzes mapping quality and coverage"""
    
    async def analyze_mapping_coverage(
        self,
        report_id: int,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze coverage of attribute mappings"""
        # Get all attributes
        attributes_result = await session.execute(
            select(ReportAttribute).filter(
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True
            )
        )
        attributes = attributes_result.scalars().all()
        
        total_attributes = len(attributes)
        mapped_count = sum(1 for attr in attributes if attr.attribute_mappings)
        
        # Analyze by classification
        classification_stats = {
            'HRCI': {'total': 0, 'mapped': 0},
            'Confidential': {'total': 0, 'mapped': 0},
            'Proprietary': {'total': 0, 'mapped': 0},
            'Public': {'total': 0, 'mapped': 0}
        }
        
        for attr in attributes:
            if attr.attribute_mappings:
                for mapping in attr.attribute_mappings:
                    class_name = mapping.security_classification.value
                    classification_stats[class_name]['total'] += 1
                    if mapping.is_validated:
                        classification_stats[class_name]['mapped'] += 1
        
        return {
            'total_attributes': total_attributes,
            'mapped_attributes': mapped_count,
            'coverage_percentage': (mapped_count / total_attributes * 100) if total_attributes > 0 else 0,
            'classification_breakdown': classification_stats,
            'unmapped_attributes': [
                {
                    'id': attr.attribute_id,
                    'name': attr.attribute_name,
                    'mandatory': attr.mandatory_flag
                }
                for attr in attributes if not attr.attribute_mappings
            ]
        }