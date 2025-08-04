"""Test all FR Y-14M Schedule D.1 prompts used in the implementation"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.core.prompt_manager import get_prompt_manager
from app.services.llm_service import get_llm_service

logger = get_logger(__name__)


class ScheduleD1PromptTester:
    """Test all Schedule D.1 prompts"""
    
    def __init__(self):
        self.prompt_manager = get_prompt_manager()
        self.regulatory_report = 'fr_y_14m'
        self.schedule = 'schedule_d_1'
        self.test_results = {}
    
    async def test_attribute_discovery(self):
        """Test attribute discovery prompt"""
        logger.info("\n" + "="*60)
        logger.info("Testing Attribute Discovery Prompt")
        logger.info("="*60)
        
        prompt = self.prompt_manager.format_prompt(
            "attribute_discovery",
            regulatory_report=self.regulatory_report,
            schedule=self.schedule,
            report_name="Credit Card Portfolio - FR Y-14M Schedule D.1",
            regulatory_context="FR Y-14M Schedule D.1 - Domestic Credit Card Data Collection"
        )
        
        if prompt:
            logger.info("✅ Attribute discovery prompt loaded successfully")
            logger.info(f"Prompt length: {len(prompt)} characters")
            logger.info("Prompt preview (first 300 chars):")
            logger.info(prompt[:300])
            
            # Test with LLM if available
            llm_response = await self._test_with_llm(prompt, "attribute_discovery")
            if llm_response:
                # Check if response is JSON array
                try:
                    attributes = json.loads(llm_response)
                    logger.info(f"✅ LLM returned {len(attributes)} attributes")
                    logger.info(f"Sample attributes: {attributes[:5]}")
                    self.test_results['attribute_discovery'] = {
                        'success': True,
                        'attribute_count': len(attributes)
                    }
                except:
                    logger.error("❌ LLM response is not valid JSON array")
                    self.test_results['attribute_discovery'] = {'success': False, 'error': 'Invalid JSON'}
        else:
            logger.error("❌ Failed to load attribute discovery prompt")
            self.test_results['attribute_discovery'] = {'success': False, 'error': 'Prompt not found'}
    
    async def test_attribute_batch_details(self):
        """Test attribute batch details prompt"""
        logger.info("\n" + "="*60)
        logger.info("Testing Attribute Batch Details Prompt")
        logger.info("="*60)
        
        # Sample attributes to test
        test_attributes = [
            "REFERENCE_NUMBER",
            "CYCLE_ENDING_BALANCE",
            "CREDIT_BUREAU_SCORE",
            "DAYS_PAST_DUE"
        ]
        
        prompt = self.prompt_manager.format_prompt(
            "attribute_batch_details",
            regulatory_report=self.regulatory_report,
            schedule=self.schedule,
            report_name="Credit Card Portfolio - FR Y-14M Schedule D.1",
            regulatory_context="FR Y-14M Schedule D.1 - Domestic Credit Card Data Collection",
            attribute_names_batch=json.dumps(test_attributes, indent=2)
        )
        
        if prompt:
            logger.info("✅ Attribute batch details prompt loaded successfully")
            logger.info(f"Prompt length: {len(prompt)} characters")
            logger.info(f"Testing with attributes: {test_attributes}")
            
            # Test with LLM if available
            llm_response = await self._test_with_llm(prompt, "attribute_batch_details")
            if llm_response:
                try:
                    details = json.loads(llm_response)
                    logger.info(f"✅ LLM returned details for {len(details)} attributes")
                    if details:
                        logger.info(f"Sample detail: {json.dumps(details[0], indent=2)}")
                    self.test_results['attribute_batch_details'] = {
                        'success': True,
                        'details_count': len(details)
                    }
                except:
                    logger.error("❌ LLM response is not valid JSON")
                    self.test_results['attribute_batch_details'] = {'success': False, 'error': 'Invalid JSON'}
        else:
            logger.error("❌ Failed to load attribute batch details prompt")
            self.test_results['attribute_batch_details'] = {'success': False, 'error': 'Prompt not found'}
    
    async def test_pde_mapping(self):
        """Test PDE mapping prompt"""
        logger.info("\n" + "="*60)
        logger.info("Testing PDE Mapping Prompt")
        logger.info("="*60)
        
        # Test data sources
        test_data_sources = [
            {
                'id': 1,
                'name': 'Credit Card Core System',
                'type': 'Database',
                'description': 'Main credit card processing system'
            }
        ]
        
        prompt = self.prompt_manager.format_prompt(
            "pde_mapping",
            regulatory_report=self.regulatory_report,
            schedule=self.schedule,
            report_name="Credit Card Portfolio - FR Y-14M Schedule D.1",
            regulatory_context="FR Y-14M Schedule D.1 - Domestic Credit Card Data Collection",
            attribute_name="CYCLE_ENDING_BALANCE",
            attribute_description="Outstanding balance at end of billing cycle",
            data_type="Decimal",
            mandatory_flag="Mandatory",
            is_primary_key="False",
            cde_flag="False",
            validation_rules="Decimal(20,2), must be non-negative",
            data_sources=json.dumps(test_data_sources, indent=2)
        )
        
        if prompt:
            logger.info("✅ PDE mapping prompt loaded successfully")
            logger.info(f"Prompt length: {len(prompt)} characters")
            logger.info(f"Contains FR Y-14M specific guidance: {'CYCL_DT_BAL' in prompt}")
            
            # Test with LLM if available
            llm_response = await self._test_with_llm(prompt, "pde_mapping")
            if llm_response:
                try:
                    mapping = json.loads(llm_response)
                    logger.info("✅ LLM returned mapping suggestion:")
                    logger.info(json.dumps(mapping, indent=2))
                    self.test_results['pde_mapping'] = {
                        'success': True,
                        'pde_name': mapping.get('pde_name'),
                        'confidence': mapping.get('confidence_score')
                    }
                except:
                    logger.error("❌ LLM response is not valid JSON")
                    self.test_results['pde_mapping'] = {'success': False, 'error': 'Invalid JSON'}
        else:
            logger.error("❌ Failed to load PDE mapping prompt")
            self.test_results['pde_mapping'] = {'success': False, 'error': 'Prompt not found'}
    
    async def test_information_security_classification(self):
        """Test information security classification prompt"""
        logger.info("\n" + "="*60)
        logger.info("Testing Information Security Classification Prompt")
        logger.info("="*60)
        
        prompt = self.prompt_manager.format_prompt(
            "information_security_classification",
            regulatory_report=self.regulatory_report,
            schedule=self.schedule,
            report_name="Credit Card Portfolio - FR Y-14M Schedule D.1",
            regulatory_context="FR Y-14M Schedule D.1 - Domestic Credit Card Data Collection",
            pde_name="CYCL_DT_BAL",
            pde_code="D1_CYCL_DT_BAL",
            pde_description="Cycle date balance from credit card system",
            business_process="Billing cycle",
            source_system="Credit Card Core System",
            attribute_name="CYCLE_ENDING_BALANCE",
            data_type="Decimal",
            cde_flag="False",
            is_primary_key="False",
            historical_issues_flag="False",
            validation_rules="Decimal(20,2), must be non-negative"
        )
        
        if prompt:
            logger.info("✅ Information security classification prompt loaded successfully")
            logger.info(f"Prompt length: {len(prompt)} characters")
            logger.info(f"Contains FR Y-14M security guidance: {'Federal Reserve' in prompt}")
            
            # Test with LLM if available
            llm_response = await self._test_with_llm(prompt, "information_security_classification")
            if llm_response:
                try:
                    classification = json.loads(llm_response)
                    logger.info("✅ LLM returned classification:")
                    logger.info(json.dumps(classification, indent=2))
                    self.test_results['information_security_classification'] = {
                        'success': True,
                        'criticality': classification.get('criticality'),
                        'risk_level': classification.get('risk_level')
                    }
                except:
                    logger.error("❌ LLM response is not valid JSON")
                    self.test_results['information_security_classification'] = {'success': False, 'error': 'Invalid JSON'}
        else:
            logger.error("❌ Failed to load information security classification prompt")
            self.test_results['information_security_classification'] = {'success': False, 'error': 'Prompt not found'}
    
    async def test_scoping_recommendations(self):
        """Test scoping recommendations prompt"""
        logger.info("\n" + "="*60)
        logger.info("Testing Scoping Recommendations Prompt")
        logger.info("="*60)
        
        # Sample attributes for scoping
        test_attributes = [
            {"name": "CYCLE_ENDING_BALANCE", "risk": "high"},
            {"name": "DAYS_PAST_DUE", "risk": "high"},
            {"name": "CREDIT_LIMIT", "risk": "medium"}
        ]
        
        prompt = self.prompt_manager.format_prompt(
            "scoping_recommendations",
            regulatory_report=self.regulatory_report,
            schedule=self.schedule,
            report_name="Credit Card Portfolio - FR Y-14M Schedule D.1",
            regulatory_context="FR Y-14M Schedule D.1 - Domestic Credit Card Data Collection",
            attributes=json.dumps(test_attributes, indent=2),
            total_population=100000,
            report_period="Q4 2024"
        )
        
        if prompt:
            logger.info("✅ Scoping recommendations prompt loaded successfully")
            logger.info(f"Prompt length: {len(prompt)} characters")
            
            # Test with LLM if available
            llm_response = await self._test_with_llm(prompt, "scoping_recommendations")
            if llm_response:
                logger.info("✅ LLM returned scoping recommendations")
                logger.info(f"Response preview (first 500 chars): {llm_response[:500]}")
                self.test_results['scoping_recommendations'] = {'success': True}
        else:
            logger.error("❌ Failed to load scoping recommendations prompt")
            self.test_results['scoping_recommendations'] = {'success': False, 'error': 'Prompt not found'}
    
    async def test_testing_approach(self):
        """Test testing approach prompt"""
        logger.info("\n" + "="*60)
        logger.info("Testing Testing Approach Prompt")
        logger.info("="*60)
        
        prompt = self.prompt_manager.format_prompt(
            "testing_approach",
            regulatory_report=self.regulatory_report,
            schedule=self.schedule,
            report_name="Credit Card Portfolio - FR Y-14M Schedule D.1",
            regulatory_context="FR Y-14M Schedule D.1 - Domestic Credit Card Data Collection",
            attribute_name="CYCLE_ENDING_BALANCE",
            attribute_description="Outstanding balance at end of billing cycle",
            data_type="Decimal",
            validation_rules="Decimal(20,2), must be non-negative"
        )
        
        if prompt:
            logger.info("✅ Testing approach prompt loaded successfully")
            logger.info(f"Prompt length: {len(prompt)} characters")
            
            # Test with LLM if available
            llm_response = await self._test_with_llm(prompt, "testing_approach")
            if llm_response:
                logger.info("✅ LLM returned testing approach")
                logger.info(f"Response preview (first 500 chars): {llm_response[:500]}")
                self.test_results['testing_approach'] = {'success': True}
        else:
            logger.error("❌ Failed to load testing approach prompt")
            self.test_results['testing_approach'] = {'success': False, 'error': 'Prompt not found'}
    
    async def _test_with_llm(self, prompt: str, prompt_type: str) -> Optional[str]:
        """Test prompt with LLM if available"""
        try:
            llm_service = get_llm_service()
            logger.info(f"\nTesting {prompt_type} with LLM...")
            
            response = await llm_service.generate_completion(
                prompt, 
                preferred_provider='claude'
            )
            
            if response and response.get('content'):
                return response['content']
            else:
                logger.warning("No response from LLM")
                return None
                
        except Exception as e:
            logger.warning(f"LLM test skipped: {e}")
            return None
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        
        for prompt_type, result in self.test_results.items():
            status = "✅ PASSED" if result.get('success') else "❌ FAILED"
            logger.info(f"{prompt_type}: {status}")
            if not result.get('success'):
                logger.info(f"  Error: {result.get('error', 'Unknown')}")
            else:
                # Print additional details if available
                for key, value in result.items():
                    if key != 'success':
                        logger.info(f"  {key}: {value}")
        
        # Overall status
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r.get('success'))
        logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")


async def main():
    """Main test function"""
    logger.info("Starting FR Y-14M Schedule D.1 prompt testing...")
    
    tester = ScheduleD1PromptTester()
    
    try:
        # Test all prompts
        await tester.test_attribute_discovery()
        await tester.test_attribute_batch_details()
        await tester.test_pde_mapping()
        await tester.test_information_security_classification()
        await tester.test_scoping_recommendations()
        await tester.test_testing_approach()
        
        # Print summary
        tester.print_summary()
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())