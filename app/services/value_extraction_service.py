"""
Value Extraction Service - Reusable service for extracting values from evidence
Used by both RFI and Test Execution phases
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.llm_service import get_llm_service
from app.services.database_connection_service import DatabaseConnectionService
from app.core.exceptions import BusinessLogicError

logger = logging.getLogger(__name__)


class ValueExtractionService:
    """Service for extracting values from various evidence types"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.db_service = DatabaseConnectionService()
    
    async def extract_values_from_evidence(
        self,
        evidence: Dict[str, Any],
        sample_data: Dict[str, Any],
        evidence_type: str = "document"
    ) -> Dict[str, Any]:
        """
        Extract values from evidence (document or database query)
        
        Args:
            evidence: Evidence data (document content or query details)
            sample_data: Sample data including expected values and attribute info
            evidence_type: Type of evidence ("document" or "database_query")
            
        Returns:
            Dictionary containing extracted values and metadata
        """
        try:
            if evidence_type == "document":
                return await self._extract_from_document(evidence, sample_data)
            elif evidence_type == "database_query":
                return await self._extract_from_query(evidence, sample_data)
            else:
                raise BusinessLogicError(f"Unsupported evidence type: {evidence_type}")
                
        except Exception as e:
            logger.error(f"Value extraction failed: {str(e)}")
            raise
    
    async def _extract_from_document(
        self,
        evidence: Dict[str, Any],
        sample_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract values from document using LLM"""
        
        document_content = evidence.get("content", "")
        attribute_name = sample_data.get("attribute_name")
        
        logger.info(f"Extracting from document - attribute: {attribute_name}")
        logger.info(f"Document content length: {len(document_content)}")
        logger.info(f"Document content preview: {document_content[:200]}...")
        
        # Get primary key attributes
        primary_key_attributes = sample_data.get("primary_key_attributes", {})
        
        # Prepare attribute context for LLM
        attribute_context = {
            "attribute_name": attribute_name,
            "sample_data": sample_data,
            "document_type": evidence.get("document_type"),
            "primary_keys": list(primary_key_attributes.keys()),
            "regulatory_definition": sample_data.get("regulatory_definition", ""),
            "data_type": sample_data.get("data_type", "string")
        }
        
        logger.info(f"Calling LLM with attribute context: {attribute_context}")
        
        # Use LLM to extract values (using the correct method signature)
        llm_response = await self.llm_service.extract_test_value_from_document(
            attribute_context=attribute_context,
            document_text=document_content,
            sample_identifier=sample_data.get("sample_identifier")
        )
        
        logger.info(f"LLM response: {llm_response}")
        
        # Extract primary key values from LLM response
        extracted_pks = {}
        if llm_response.get("primary_keys"):
            for pk_name in primary_key_attributes.keys():
                if pk_name in llm_response["primary_keys"]:
                    extracted_pks[pk_name] = llm_response["primary_keys"][pk_name]
        
        return {
            "extracted_value": llm_response.get("extracted_value"),
            "primary_key_values": extracted_pks,
            "confidence_score": llm_response.get("confidence_score", 0.0),
            "extraction_method": "llm",
            "extraction_metadata": {
                "model": llm_response.get("model", "unknown"),
                "tokens_used": llm_response.get("tokens", 0),
                "processing_time_ms": llm_response.get("processing_time_ms", 0),
                "rationale": llm_response.get("location_in_document", ""),
                "success": llm_response.get("success", False)
            },
            "extraction_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _extract_from_query(
        self,
        evidence: Dict[str, Any],
        sample_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract values from database query results"""
        
        # Get query execution details
        query_text = evidence.get("query_text", "")
        data_source_id = evidence.get("data_source_id")
        connection_details = evidence.get("connection_details", {})
        connection_type = evidence.get("connection_type", "postgresql")
        
        # Execute query
        query_result = await self.db_service.execute_query(
            connection_type=connection_type,
            connection_details=connection_details,
            query=query_text,
            parameters=sample_data
        )
        
        # Extract values from query result
        rows = query_result.get("rows", [])
        columns = query_result.get("columns", [])
        
        # Get the attribute name we're testing
        attribute_name = sample_data.get("attribute_name", "")
        
        # Extract values
        extracted_value = None
        primary_key_values = {}
        
        if rows and len(rows) > 0:
            first_row = rows[0]
            
            # Look for the attribute value - try multiple matching strategies
            for col in columns:
                col_normalized = col.lower().replace(" ", "_")
                attr_normalized = attribute_name.lower().replace(" ", "_")
                
                # Check for exact match or close match
                if (col_normalized == attr_normalized or 
                    col.lower().replace(" ", "") == attribute_name.lower().replace(" ", "") or
                    col in first_row and attribute_name.lower() in col.lower()):
                    extracted_value = first_row.get(col)
                    break
            
            # Extract primary key values
            # Get primary keys from sample data or use defaults
            primary_keys = sample_data.get("primary_key_list", [])
            if not primary_keys:
                # Fall back to standard primary keys for banking data
                primary_keys = ['Bank ID', 'Customer ID', 'Period ID', 'Reference Number']
            
            for pk in primary_keys:
                # Check for exact match first
                if pk in first_row:
                    primary_key_values[pk] = first_row.get(pk)
                else:
                    # Fall back to case-insensitive search
                    for col in columns:
                        if col.lower() == pk.lower():
                            primary_key_values[pk] = first_row.get(col)
                            break
        
        return {
            "extracted_value": extracted_value,
            "primary_key_values": primary_key_values,
            "row_count": query_result.get("row_count", 0),
            "extraction_method": "sql",
            "query_executed": query_text,
            "all_rows": rows,  # Keep all data for display
            "columns": columns,
            "extraction_timestamp": datetime.utcnow().isoformat()
        }
    
    def format_for_display(
        self,
        extracted_values: Dict[str, Any],
        sample_data: Dict[str, Any],
        hide_sample_values: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Format extracted values for display in UI
        
        Returns list of rows for table display
        """
        rows = []
        
        # Add primary key rows
        primary_keys = extracted_values.get("primary_key_values", {})
        expected_pks = sample_data.get("primary_key_attributes", {})
        
        for pk_name, extracted_value in primary_keys.items():
            rows.append({
                "attribute_name": pk_name,
                "is_primary_key": True,
                "sample_value": expected_pks.get(pk_name, "N/A") if not hide_sample_values else "Hidden",
                "extracted_value": extracted_value,
                "match_status": None  # Don't auto-decide
            })
        
        # Add the main attribute
        attribute_name = sample_data.get("attribute_name")
        if attribute_name:
            sample_value = sample_data.get("expected_value") or sample_data.get("sample_value", "N/A")
            rows.append({
                "attribute_name": attribute_name,
                "is_primary_key": False,
                "sample_value": sample_value if not hide_sample_values else "Hidden",
                "extracted_value": extracted_values.get("extracted_value"),
                "match_status": None  # Don't auto-decide
            })
        
        return rows