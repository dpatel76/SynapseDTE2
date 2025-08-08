#!/usr/bin/env python3
"""Test LLM service directly"""

import asyncio
import sys
sys.path.append('.')

from app.services.llm_service import get_llm_service

async def test_llm():
    llm_service = get_llm_service()
    
    # Test with a simple attribute
    test_attributes = [
        {
            "attribute_id": 1,
            "attribute_name": "Customer ID",
            "data_type": "String",
            "is_primary_key": False,
            "is_cde": False,
            "is_mandatory": True,
            "has_historical_issues": False,
            "historical_issues": []
        }
    ]
    
    try:
        result = await llm_service.recommend_tests_batch(
            attributes=test_attributes,
            regulatory_context="FR Y-14M Schedule D.1",
            report_name="Credit Card Portfolio",
            report_type="Credit Card",
            batch_num=1,
            total_batches=1
        )
        
        print(f"LLM Result: {result}")
        if result.get('success'):
            print(f"\nRecommendations: {result.get('recommendations', [])}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error calling LLM: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())