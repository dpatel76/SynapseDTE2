"""Test script to verify regulation-specific PDE mapping and classification prompts"""

import asyncio
import json
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.core.prompt_manager import get_prompt_manager
from app.models.report import Report
from app.models.report_attribute import ReportAttribute
from app.models.test_cycle import TestCycle
from app.models.cycle_report import CycleReport
from app.services.llm_service import get_llm_service

logger = get_logger(__name__)


async def test_pde_mapping_prompt():
    """Test PDE mapping with FR Y-14M Schedule D.1 context"""
    
    async with AsyncSessionLocal() as session:
        # Find a report with FR Y-14M Schedule D.1 context
        query = select(Report).where(
            Report.regulation.ilike('%FR Y-14M%')
        ).limit(1)
        
        result = await session.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            logger.info("Creating test report with FR Y-14M Schedule D.1 context")
            # Create a test report
            report = Report(
                report_name="Credit Card Portfolio Test",
                report_number="FRY14M-D1-001",
                regulation="FR Y-14M Schedule D.1 - Domestic Credit Card Data Collection",
                description="Credit card loan level data for stress testing",
                regulatory_requirement=True,
                created_by_id=1,
                updated_by_id=1
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
        
        logger.info(f"Using report: {report.report_name} with regulation: {report.regulation}")
        
        # Test attribute for PDE mapping
        test_attribute = ReportAttribute(
            report_id=report.report_id,
            attribute_name="CYCL_DT_BAL",
            description="Cycle date balance - outstanding balance as of cycle date",
            data_type="Decimal",
            mandatory_flag="Mandatory",
            is_primary_key=False,
            cde_flag=False,
            validation_rules="Must be positive decimal, format 12.2",
            created_by_id=1,
            updated_by_id=1
        )
        
        # Prepare test data sources
        test_data_sources = [
            {
                'id': 1,
                'name': 'Credit Card Core System',
                'type': 'Database',
                'description': 'Main credit card processing system'
            },
            {
                'id': 2,
                'name': 'Loan Servicing Platform',
                'type': 'Database',
                'description': 'Loan servicing and billing system'
            }
        ]
        
        # Test regulation detection
        regulatory_report = None
        schedule = None
        
        if report.regulation:
            context_lower = report.regulation.lower()
            if 'fr y-14m' in context_lower or 'fr_y_14m' in context_lower:
                regulatory_report = 'fr_y_14m'
                if 'schedule d' in context_lower:
                    if 'd.1' in context_lower or 'd1' in context_lower:
                        schedule = 'schedule_d_1'
        
        logger.info(f"Detected regulatory report: {regulatory_report}, schedule: {schedule}")
        
        # Test PDE mapping prompt
        prompt_manager = get_prompt_manager()
        
        pde_mapping_prompt = prompt_manager.format_prompt(
            "pde_mapping",
            regulatory_report=regulatory_report,
            schedule=schedule,
            report_name=report.report_name,
            regulatory_context=report.regulation,
            attribute_name=test_attribute.attribute_name,
            attribute_description=test_attribute.description,
            data_type=test_attribute.data_type,
            mandatory_flag=test_attribute.mandatory_flag,
            is_primary_key=str(test_attribute.is_primary_key),
            cde_flag=str(test_attribute.cde_flag),
            validation_rules=test_attribute.validation_rules,
            data_sources=json.dumps(test_data_sources, indent=2)
        )
        
        if pde_mapping_prompt:
            logger.info("✅ PDE mapping prompt loaded successfully")
            logger.info(f"Prompt length: {len(pde_mapping_prompt)} characters")
            logger.info("Prompt preview (first 500 chars):")
            logger.info(pde_mapping_prompt[:500])
            
            # Test with LLM if available
            try:
                llm_service = get_llm_service()
                logger.info("\nTesting with LLM...")
                response = await llm_service.generate_completion(
                    pde_mapping_prompt, 
                    preferred_provider='claude'
                )
                
                if response and response.get('content'):
                    suggestion = json.loads(response['content'])
                    logger.info("\n✅ LLM Response:")
                    logger.info(json.dumps(suggestion, indent=2))
                else:
                    logger.warning("No response from LLM")
                    
            except Exception as e:
                logger.error(f"LLM test failed: {e}")
        else:
            logger.error("❌ Failed to load PDE mapping prompt")
        
        # Test information security classification prompt
        logger.info("\n" + "="*60)
        logger.info("Testing Information Security Classification Prompt")
        logger.info("="*60)
        
        # Mock PDE mapping data
        test_pde = {
            'pde_name': 'CYCL_DT_BAL',
            'pde_code': 'D1_CYCL_BAL',
            'pde_description': 'Cycle date balance from credit card system',
            'business_process': 'Billing cycle',
            'source_system': 'Credit Card Core System'
        }
        
        classification_prompt = prompt_manager.format_prompt(
            "information_security_classification",
            regulatory_report=regulatory_report,
            schedule=schedule,
            report_name=report.report_name,
            regulatory_context=report.regulation,
            pde_name=test_pde['pde_name'],
            pde_code=test_pde['pde_code'],
            pde_description=test_pde['pde_description'],
            business_process=test_pde['business_process'],
            source_system=test_pde['source_system'],
            attribute_name=test_attribute.attribute_name,
            data_type=test_attribute.data_type,
            cde_flag=str(test_attribute.cde_flag),
            is_primary_key=str(test_attribute.is_primary_key),
            historical_issues_flag='False',
            validation_rules=test_attribute.validation_rules
        )
        
        if classification_prompt:
            logger.info("✅ Information security classification prompt loaded successfully")
            logger.info(f"Prompt length: {len(classification_prompt)} characters")
            logger.info("Prompt preview (first 500 chars):")
            logger.info(classification_prompt[:500])
            
            # Test with LLM if available
            try:
                llm_service = get_llm_service()
                logger.info("\nTesting with LLM...")
                response = await llm_service.generate_completion(
                    classification_prompt, 
                    preferred_provider='claude'
                )
                
                if response and response.get('content'):
                    suggestion = json.loads(response['content'])
                    logger.info("\n✅ LLM Response:")
                    logger.info(json.dumps(suggestion, indent=2))
                else:
                    logger.warning("No response from LLM")
                    
            except Exception as e:
                logger.error(f"LLM test failed: {e}")
        else:
            logger.error("❌ Failed to load information security classification prompt")
            
        # Test with non-regulatory context
        logger.info("\n" + "="*60)
        logger.info("Testing Generic Prompts (Non-Regulatory Context)")
        logger.info("="*60)
        
        generic_prompt = prompt_manager.format_prompt(
            "pde_mapping",
            regulatory_report=None,
            schedule=None,
            report_name="Generic Report",
            regulatory_context="",
            attribute_name="test_field",
            attribute_description="Test field description",
            data_type="String",
            mandatory_flag="Optional",
            is_primary_key="False",
            cde_flag="False",
            validation_rules="None",
            data_sources=json.dumps(test_data_sources, indent=2)
        )
        
        if generic_prompt:
            logger.info("✅ Generic PDE mapping prompt loaded successfully")
            logger.info("This confirms fallback to generic prompt works")
        else:
            logger.error("❌ Failed to load generic PDE mapping prompt")


async def main():
    """Main test function"""
    logger.info("Starting regulation-specific prompt testing...")
    
    try:
        await test_pde_mapping_prompt()
        logger.info("\n✅ All tests completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())