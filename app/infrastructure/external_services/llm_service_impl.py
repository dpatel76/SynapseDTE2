"""Production implementation of LLM service"""
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

from app.application.interfaces.external_services import ILLMService
from app.services.llm_service import HybridLLMService, get_llm_service

logger = logging.getLogger(__name__)


class LLMServiceImpl(ILLMService):
    """Production implementation of LLM service using existing HybridLLMService"""
    
    def __init__(self):
        # Use the existing hybrid LLM service
        self.hybrid_service = get_llm_service()
    
    async def generate_test_attributes(self, report_id: int, regulatory_context: str, 
                                     report_type: str) -> List[Dict[str, Any]]:
        """Generate test attributes using LLM"""
        try:
            # Use the existing service method
            result = await self.hybrid_service.generate_test_attributes(
                regulatory_context=regulatory_context,
                report_type=report_type,
                preferred_provider="claude"  # Prefer Claude for analysis tasks
            )
            
            # Extract attributes from result
            if isinstance(result, dict) and 'attributes' in result:
                return result['attributes']
            elif isinstance(result, list):
                return result
            else:
                # Parse JSON if needed
                if isinstance(result, str):
                    try:
                        parsed = json.loads(result)
                        if isinstance(parsed, list):
                            return parsed
                        elif isinstance(parsed, dict) and 'attributes' in parsed:
                            return parsed['attributes']
                    except json.JSONDecodeError:
                        pass
                
                logger.warning(f"Unexpected LLM response format: {type(result)}")
                return []
        
        except Exception as e:
            logger.error(f"Error generating test attributes: {str(e)}")
            raise
    
    async def generate_samples(self, report_id: int, sample_count: int, 
                             criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate sample data using LLM"""
        try:
            # Prepare prompt based on criteria
            regulatory_context = criteria.get('regulatory_context', 'General') if criteria else 'General'
            attributes = criteria.get('attributes', []) if criteria else []
            risk_focus_areas = criteria.get('risk_focus_areas', []) if criteria else []
            sample_type = criteria.get('sample_type', 'Population Sample') if criteria else 'Population Sample'
            
            # Build context for sample generation
            context = f"""
            Generate {sample_count} realistic test samples for regulatory compliance testing.
            
            Regulatory Context: {regulatory_context}
            Sample Type: {sample_type}
            Risk Focus Areas: {', '.join(risk_focus_areas) if risk_focus_areas else 'General compliance'}
            
            Attributes to include in each sample:
            """
            
            for attr in attributes:
                context += f"\n- {attr['attribute_name']} ({attr['data_type']})"
                if attr.get('is_primary_key'):
                    context += " [PRIMARY KEY]"
            
            context += f"""
            
            Return a JSON array with {sample_count} sample objects. Each sample should have:
            - sample_id: Unique identifier
            - sample_data: Object containing values for all attributes
            - risk_score: Float between 0 and 1
            - testing_rationale: Brief explanation of why this sample is important
            - primary_key_value: The value of the primary key attribute
            """
            
            # Call LLM service
            result = await self.hybrid_service.analyze_with_llm(
                content=context,
                analysis_type="sample_generation",
                preferred_provider="claude"
            )
            
            # Parse result
            if isinstance(result, str):
                try:
                    # Look for JSON array in the response
                    import re
                    json_match = re.search(r'\[\s*\{.*\}\s*\]', result, re.DOTALL)
                    if json_match:
                        samples = json.loads(json_match.group())
                        return samples[:sample_count]  # Ensure we don't exceed requested count
                except json.JSONDecodeError:
                    logger.error("Failed to parse LLM sample generation response")
            
            # Fallback: Generate basic samples if LLM fails
            logger.warning("LLM sample generation failed, using fallback")
            return self._generate_fallback_samples(sample_count, attributes)
        
        except Exception as e:
            logger.error(f"Error generating samples: {str(e)}")
            # Return fallback samples
            return self._generate_fallback_samples(sample_count, criteria.get('attributes', []) if criteria else [])
    
    async def analyze_document(self, document_content: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze document content using LLM"""
        try:
            result = await self.hybrid_service.analyze_with_llm(
                content=document_content,
                analysis_type=analysis_type,
                preferred_provider="claude"
            )
            
            # Return structured result
            if isinstance(result, dict):
                return result
            else:
                return {
                    "analysis_type": analysis_type,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            raise
    
    async def generate_test_cases(self, attribute_id: int, attribute_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test cases for an attribute"""
        try:
            context = f"""
            Generate comprehensive test cases for the following attribute:
            
            Attribute Name: {attribute_details.get('attribute_name', 'Unknown')}
            Data Type: {attribute_details.get('data_type', 'String')}
            Description: {attribute_details.get('description', 'No description')}
            Is Primary Key: {attribute_details.get('is_primary_key', False)}
            Regulatory Context: {attribute_details.get('regulatory_context', 'General')}
            
            Generate test cases that cover:
            1. Valid values (typical cases)
            2. Boundary values
            3. Invalid values
            4. Edge cases
            5. Regulatory compliance scenarios
            
            Return a JSON array of test cases. Each test case should have:
            - test_case_id: Unique identifier
            - test_case_name: Descriptive name
            - test_type: Type of test (valid, boundary, invalid, edge_case, compliance)
            - input_value: The test input
            - expected_result: Expected outcome
            - test_rationale: Why this test is important
            """
            
            result = await self.hybrid_service.analyze_with_llm(
                content=context,
                analysis_type="test_case_generation",
                preferred_provider="claude"
            )
            
            # Parse result
            if isinstance(result, str):
                try:
                    import re
                    json_match = re.search(r'\[\s*\{.*\}\s*\]', result, re.DOTALL)
                    if json_match:
                        test_cases = json.loads(json_match.group())
                        return test_cases
                except json.JSONDecodeError:
                    logger.error("Failed to parse LLM test case generation response")
            
            # Fallback: Generate basic test cases
            return self._generate_fallback_test_cases(attribute_details)
        
        except Exception as e:
            logger.error(f"Error generating test cases: {str(e)}")
            return self._generate_fallback_test_cases(attribute_details)
    
    def _generate_fallback_samples(self, sample_count: int, attributes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fallback samples when LLM fails"""
        samples = []
        for i in range(sample_count):
            sample_data = {}
            primary_key_value = f"SAMPLE_{i+1:04d}"
            
            for attr in attributes:
                attr_name = attr['attribute_name']
                data_type = attr.get('data_type', 'String')
                
                if attr.get('is_primary_key'):
                    sample_data[attr_name] = primary_key_value
                elif data_type in ['Integer', 'BIGINT']:
                    sample_data[attr_name] = 1000 + i
                elif data_type in ['Float', 'DECIMAL']:
                    sample_data[attr_name] = round(100.0 + i * 0.5, 2)
                elif data_type in ['Date', 'DateTime']:
                    sample_data[attr_name] = datetime.utcnow().isoformat()
                else:
                    sample_data[attr_name] = f"VALUE_{i+1}"
            
            samples.append({
                "sample_id": f"SAMPLE_{i+1:04d}",
                "sample_data": sample_data,
                "risk_score": 0.5,
                "testing_rationale": "Fallback sample for testing",
                "primary_key_value": primary_key_value
            })
        
        return samples
    
    def _generate_fallback_test_cases(self, attribute_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fallback test cases when LLM fails"""
        test_cases = []
        attr_name = attribute_details.get('attribute_name', 'test_attribute')
        data_type = attribute_details.get('data_type', 'String')
        
        # Valid case
        test_cases.append({
            "test_case_id": f"TC_{attr_name}_001",
            "test_case_name": f"Valid {attr_name} value",
            "test_type": "valid",
            "input_value": "VALID_VALUE_001" if data_type == 'String' else 100,
            "expected_result": "Pass",
            "test_rationale": "Test typical valid value"
        })
        
        # Invalid case
        test_cases.append({
            "test_case_id": f"TC_{attr_name}_002",
            "test_case_name": f"Invalid {attr_name} value",
            "test_type": "invalid",
            "input_value": None,
            "expected_result": "Fail",
            "test_rationale": "Test null/missing value handling"
        })
        
        # Edge case
        test_cases.append({
            "test_case_id": f"TC_{attr_name}_003",
            "test_case_name": f"Edge case {attr_name} value",
            "test_type": "edge_case",
            "input_value": "" if data_type == 'String' else 0,
            "expected_result": "Pass with warning",
            "test_rationale": "Test boundary conditions"
        })
        
        return test_cases