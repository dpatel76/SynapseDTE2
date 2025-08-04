#!/usr/bin/env python3
"""
Quick test script to verify LLM API keys are working
"""

import asyncio
import os
from app.services.llm_service import get_llm_service

async def test_llm():
    try:
        print("🧪 Testing LLM Service with API Keys")
        service = get_llm_service()
        print(f'✅ LLM Service initialized with providers: {list(service.providers.keys())}')
        
        health = await service.health_check()
        print(f'🏥 Health Check Status: {health.get("overall_status")}')
        
        if 'claude' in service.providers:
            print('🔵 Testing Claude...')
            response = await service.providers['claude'].generate('Say hello in one word')
            print(f'Claude response: {response.get("content", "No content")}')
            
        if 'gemini' in service.providers:
            print('🟢 Testing Gemini...')
            response = await service.providers['gemini'].generate('Say hello in one word')
            print(f'Gemini response: {response.get("content", "No content")}')
            
        print("✅ LLM API Keys are working correctly!")
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm()) 