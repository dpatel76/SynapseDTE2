"""Implementation of LLMService using HybridLLMService"""
from typing import Dict, Any, List, Optional
import json

from app.application.interfaces.services import LLMService
from app.services.llm_service import HybridLLMService, get_llm_service


class LLMServiceImpl(LLMService):
    """Implementation of LLM service using the existing HybridLLMService"""
    
    def __init__(self):
        self.hybrid_service = get_llm_service()
    
    async def generate_test_attributes(
        self,
        regulatory_context: str,
        report_type: str,
        sample_size: int,
        existing_attributes: Optional[List[Dict[str, Any]]] = None,
        preferred_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate test attributes using LLM"""
        try:
            # Use the existing hybrid service method
            result = await self.hybrid_service.generate_test_attributes(
                regulatory_context=regulatory_context,
                report_type=report_type,
                existing_attributes=existing_attributes,
                preferred_provider=preferred_provider
            )
            
            # Add sample size to the result
            if result.get('success') and result.get('attributes'):
                for attr in result['attributes']:
                    if 'sample_size' not in attr:
                        attr['sample_size'] = sample_size
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "attributes": []
            }
    
    async def analyze_document(
        self,
        document_content: str,
        attribute_name: str,
        expected_value: Any,
        analysis_context: Dict[str, Any],
        preferred_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze document for specific attribute"""
        try:
            # Use the hybrid service to analyze document
            result = await self.hybrid_service.analyze_document_for_attribute(
                document_content=document_content,
                attribute_name=attribute_name,
                expected_value=expected_value,
                test_context=analysis_context,
                preferred_provider=preferred_provider
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "found": False,
                "extracted_value": None,
                "confidence": 0.0
            }
    
    async def extract_data_from_document(
        self,
        document_content: str,
        extraction_schema: Dict[str, Any],
        preferred_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured data from document"""
        try:
            # Create a prompt for data extraction
            prompt = f"""
            Extract the following data from the document:
            
            Schema: {json.dumps(extraction_schema, indent=2)}
            
            Document:
            {document_content}
            
            Return the extracted data as JSON matching the schema.
            """
            
            # Use Gemini for extraction tasks as it's optimized for this
            provider = preferred_provider or "gemini"
            
            if provider == "gemini":
                result = await self.hybrid_service._call_gemini_api(
                    prompt=prompt,
                    system_prompt="You are a data extraction specialist. Extract structured data from documents according to the provided schema."
                )
            else:
                result = await self.hybrid_service._call_claude_api(
                    prompt=prompt,
                    system_prompt="You are a data extraction specialist. Extract structured data from documents according to the provided schema."
                )
            
            if result.get('success'):
                # Parse the extracted data
                extracted_text = result.get('content', '')
                try:
                    # Find JSON in the response
                    import re
                    json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
                    if json_match:
                        extracted_data = json.loads(json_match.group())
                    else:
                        extracted_data = {}
                    
                    return {
                        "success": True,
                        "data": extracted_data,
                        "provider_used": provider
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "Failed to parse extracted data as JSON",
                        "raw_response": extracted_text
                    }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    async def generate_report_summary(
        self,
        test_results: List[Dict[str, Any]],
        observations: List[Dict[str, Any]],
        cycle_context: Dict[str, Any],
        preferred_provider: Optional[str] = None
    ) -> str:
        """Generate a summary report from test results"""
        try:
            # Prepare the data for summarization
            prompt = f"""
            Generate an executive summary for the following test results:
            
            Test Cycle: {cycle_context.get('cycle_name')}
            Report: {cycle_context.get('report_name')}
            Period: {cycle_context.get('start_date')} to {cycle_context.get('end_date')}
            
            Test Results Summary:
            - Total Tests: {len(test_results)}
            - Passed: {sum(1 for r in test_results if r.get('status') == 'pass')}
            - Failed: {sum(1 for r in test_results if r.get('status') == 'fail')}
            - Pending: {sum(1 for r in test_results if r.get('status') == 'pending')}
            
            Key Observations ({len(observations)} total):
            - Critical: {sum(1 for o in observations if o.get('severity') == 'critical')}
            - High: {sum(1 for o in observations if o.get('severity') == 'high')}
            - Medium: {sum(1 for o in observations if o.get('severity') == 'medium')}
            - Low: {sum(1 for o in observations if o.get('severity') == 'low')}
            
            Please provide:
            1. Executive Summary
            2. Key Findings
            3. Risk Assessment
            4. Recommendations
            """
            
            # Use Claude for report generation as it's better at analysis
            provider = preferred_provider or "claude"
            
            if provider == "claude":
                result = await self.hybrid_service._call_claude_api(
                    prompt=prompt,
                    system_prompt="You are a regulatory compliance expert generating test reports."
                )
            else:
                result = await self.hybrid_service._call_gemini_api(
                    prompt=prompt,
                    system_prompt="You are a regulatory compliance expert generating test reports."
                )
            
            if result.get('success'):
                return result.get('content', 'Failed to generate summary')
            else:
                return f"Error generating summary: {result.get('error')}"
                
        except Exception as e:
            return f"Error generating report summary: {str(e)}"
    
    async def check_provider_health(self, provider: str) -> bool:
        """Check if a specific provider is healthy"""
        try:
            # Use the hybrid service's health check
            if provider == "claude":
                return await self.hybrid_service._check_claude_health()
            elif provider == "gemini":
                return await self.hybrid_service._check_gemini_health()
            else:
                return False
        except Exception:
            return False