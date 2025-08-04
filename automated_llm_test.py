#!/usr/bin/env python3
"""
Automated LLM Testing Script
Runs at 1:01 AM to test and fix LLM recommendations
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_

# Import app modules
from app.models.report_attribute import ReportAttribute
from app.services.llm_service import LLMService
from app.services.scoping_service import ScopingService
from app.core.config import settings
from app.api.deps import get_current_user_from_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_llm_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Test configurations
TEST_PROMPTS = [
    # Original prompt structure
    {
        "name": "original",
        "system": "",
        "user": "Generate recommendations for these attributes: {attributes}"
    },
    # Explicit JSON instruction
    {
        "name": "explicit_json",
        "system": "You are a data testing expert. Always respond with valid JSON only.",
        "user": """Generate testing recommendations for these attributes.

IMPORTANT: Respond ONLY with a JSON array. No other text.

Example format:
[
  {
    "attribute_id": 123,
    "attribute_name": "field_name",
    "recommended_action": "Include",
    "risk_level": "High",
    "llm_rationale": "Reason for recommendation"
  }
]

Attributes: {attributes}"""
    },
    # Structured prompt with clear boundaries
    {
        "name": "structured",
        "system": "You are a JSON API that returns testing recommendations.",
        "user": """<task>
Generate testing recommendations as JSON array
</task>

<format>
[{"attribute_id": int, "attribute_name": str, "recommended_action": "Include"|"Exclude", "risk_level": "High"|"Medium"|"Low", "llm_rationale": str}]
</format>

<attributes>
{attributes}
</attributes>

<response>"""
    },
    # Ultra-simple prompt
    {
        "name": "simple",
        "system": "Return JSON array only. No explanations.",
        "user": "JSON recommendations for: {attributes}"
    }
]

async def get_test_token() -> str:
    """Get a valid test token for API calls"""
    # Read from test token file if exists
    if os.path.exists('.test_token'):
        with open('.test_token', 'r') as f:
            return f.read().strip()
    
    # Otherwise use a default test token
    return "test_token_123"

async def test_llm_direct(llm_service: LLMService, prompt_config: Dict[str, str], attributes: List[Dict]) -> Dict[str, Any]:
    """Test LLM directly with different prompts"""
    logger.info(f"Testing prompt: {prompt_config['name']}")
    
    # Format attributes for prompt
    attr_text = json.dumps(attributes, indent=2)
    user_prompt = prompt_config['user'].format(attributes=attr_text)
    
    try:
        # Call LLM
        start_time = time.time()
        response = await llm_service.call_llm(
            prompt_content=user_prompt,
            system_prompt=prompt_config['system']
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Response received in {elapsed:.2f}s")
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response content: {response[:500]}...")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response)
            logger.info(f"✅ Successfully parsed JSON with {len(parsed) if isinstance(parsed, list) else 'N/A'} items")
            return {
                "success": True,
                "prompt": prompt_config['name'],
                "response": response,
                "parsed": parsed,
                "elapsed": elapsed
            }
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON: {e}")
            return {
                "success": False,
                "prompt": prompt_config['name'],
                "response": response,
                "error": str(e),
                "elapsed": elapsed
            }
            
    except Exception as e:
        logger.error(f"❌ LLM call failed: {e}")
        return {
            "success": False,
            "prompt": prompt_config['name'],
            "error": str(e)
        }

async def test_scoping_service(db: AsyncSession, cycle_id: int, report_id: int) -> Dict[str, Any]:
    """Test the actual scoping service"""
    logger.info(f"Testing scoping service for cycle {cycle_id}, report {report_id}")
    
    try:
        # Get current user (using test user)
        class MockUser:
            user_id = 3  # tester user
            email = "tester@example.com"
        
        # Initialize scoping service
        scoping_service = ScopingService(db)
        
        # Test regular generation
        logger.info("Testing regular LLM generation...")
        result = await scoping_service.generate_llm_recommendations(
            cycle_id=cycle_id,
            report_id=report_id,
            current_user=MockUser()
        )
        
        logger.info(f"Generation result: {result}")
        
        # Check if recommendations were created
        query = select(ReportAttribute).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.llm_rationale.isnot(None)
            )
        )
        result = await db.execute(query)
        attrs_with_recommendations = result.scalars().all()
        
        logger.info(f"Attributes with recommendations: {len(attrs_with_recommendations)}")
        
        return {
            "success": len(attrs_with_recommendations) > 0,
            "attributes_with_recommendations": len(attrs_with_recommendations),
            "sample_recommendations": [
                {
                    "name": attr.attribute_name,
                    "recommendation": attr.llm_recommendation,
                    "rationale": attr.llm_rationale[:100] if attr.llm_rationale else None
                }
                for attr in attrs_with_recommendations[:3]
            ]
        }
        
    except Exception as e:
        logger.error(f"Scoping service test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

async def fix_llm_prompt_in_service():
    """Attempt to fix the LLM prompt in the service"""
    logger.info("Attempting to fix LLM prompt in scoping service...")
    
    # Read the scoping service file
    service_path = "app/services/scoping_service.py"
    
    try:
        with open(service_path, 'r') as f:
            content = f.read()
        
        # Look for prompt construction
        if "Generate recommendations" in content and "JSON" not in content:
            logger.info("Found prompt without explicit JSON instruction")
            # Add JSON instruction to prompt
            # (This would require careful analysis of the actual code structure)
            
        logger.info("Service analysis complete")
        
    except Exception as e:
        logger.error(f"Failed to analyze service: {e}")

async def run_tests():
    """Run all LLM tests"""
    logger.info("=" * 80)
    logger.info(f"Starting automated LLM tests at {datetime.now()}")
    logger.info("=" * 80)
    
    # Create async engine
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        # Test parameters
        cycle_id = 58
        report_id = 156
        
        # Get sample attributes
        query = select(ReportAttribute).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True
            )
        ).limit(3)
        
        result = await db.execute(query)
        attributes = result.scalars().all()
        
        if not attributes:
            logger.error("No attributes found for testing")
            return
        
        # Prepare attribute data for LLM
        attr_data = [
            {
                "attribute_id": attr.attribute_id,
                "attribute_name": attr.attribute_name,
                "attribute_type": attr.attribute_type,
                "is_primary_key": attr.is_primary_key
            }
            for attr in attributes
        ]
        
        logger.info(f"Testing with {len(attr_data)} attributes")
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Test 1: Direct LLM calls with different prompts
        logger.info("\n" + "=" * 60)
        logger.info("TEST 1: Direct LLM Calls")
        logger.info("=" * 60)
        
        results = []
        for prompt_config in TEST_PROMPTS:
            result = await test_llm_direct(llm_service, prompt_config, attr_data)
            results.append(result)
            await asyncio.sleep(2)  # Rate limiting
        
        # Find working prompt
        working_prompts = [r for r in results if r.get('success')]
        if working_prompts:
            logger.info(f"\n✅ Found {len(working_prompts)} working prompts!")
            best_prompt = working_prompts[0]
            logger.info(f"Best prompt: {best_prompt['prompt']}")
        else:
            logger.error("\n❌ No working prompts found")
        
        # Test 2: Scoping service
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: Scoping Service")
        logger.info("=" * 60)
        
        service_result = await test_scoping_service(db, cycle_id, report_id)
        
        if service_result['success']:
            logger.info("✅ Scoping service working!")
        else:
            logger.info("❌ Scoping service needs fixing")
            
            # Attempt to fix
            await fix_llm_prompt_in_service()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"Direct LLM Tests: {len(working_prompts)}/{len(TEST_PROMPTS)} working")
        logger.info(f"Scoping Service: {'✅ Working' if service_result['success'] else '❌ Needs Fix'}")
        
        if working_prompts:
            logger.info("\nRecommended fix:")
            logger.info(f"Use prompt configuration: {working_prompts[0]['prompt']}")
            logger.info("Update scoping service to use explicit JSON instructions")
        
        # Save results
        with open('llm_test_results.json', 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "direct_tests": results,
                "service_test": service_result,
                "recommendations": {
                    "working_prompts": [p['prompt'] for p in working_prompts],
                    "fix_needed": not service_result['success']
                }
            }, f, indent=2)
        
        logger.info("\nResults saved to llm_test_results.json")

async def wait_until_time(hour: int, minute: int):
    """Wait until specific time"""
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If target time has passed today, wait until tomorrow
    if target <= now:
        target += timedelta(days=1)
    
    wait_seconds = (target - now).total_seconds()
    logger.info(f"Waiting until {target} ({wait_seconds:.0f} seconds)...")
    
    await asyncio.sleep(wait_seconds)

async def main():
    """Main entry point"""
    if "--now" in sys.argv:
        # Run immediately for testing
        await run_tests()
    else:
        # Wait until 1:01 AM
        await wait_until_time(1, 1)
        await run_tests()

if __name__ == "__main__":
    asyncio.run(main())