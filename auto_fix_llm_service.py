#!/usr/bin/env python3
"""
Automated LLM Service Fixer
Analyzes and fixes the LLM prompt issue
"""

import os
import re
import json
import shutil
from datetime import datetime

def analyze_scoping_service():
    """Analyze the scoping service to find LLM prompt construction"""
    service_path = "app/services/scoping_service.py"
    
    with open(service_path, 'r') as f:
        content = f.read()
    
    # Find LLM prompt patterns
    prompt_patterns = [
        r'prompt.*=.*["\'].*Generate.*recommendations.*["\']',
        r'call_llm\s*\([^)]*prompt[^)]*\)',
        r'generate.*recommendations.*prompt',
        r'CRITICAL:.*generate recommendations.*JSON'
    ]
    
    findings = []
    for pattern in prompt_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            start = max(0, match.start() - 200)
            end = min(len(content), match.end() + 200)
            context = content[start:end]
            findings.append({
                "pattern": pattern,
                "match": match.group(),
                "context": context,
                "line": content[:match.start()].count('\n') + 1
            })
    
    return findings

def fix_data_profiling_service():
    """Fix the data profiling service LLM prompts"""
    service_path = "app/services/data_profiling_service.py"
    backup_path = f"{service_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"Backing up to {backup_path}")
    shutil.copy2(service_path, backup_path)
    
    with open(service_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Update the prompt to ensure JSON response
    # Look for the scoping recommendations prompt
    if 'Generate risk-based scoping recommendations' in content:
        print("Found scoping recommendations prompt")
        
        # Replace the prompt instruction
        old_prompt = 'IMPORTANT: You MUST respond with ONLY a JSON array. Do NOT include any conversational text, explanations, or questions. Return the complete JSON response regardless of length.'
        
        new_prompt = '''IMPORTANT: You MUST respond with ONLY a JSON array. Do NOT include any conversational text, explanations, or questions. Do not respond with "OK" or any other text. Start your response with [ and end with ].

Example of correct response:
[
  {
    "attribute_id": 1,
    "attribute_name": "example_field",
    "recommended_action": "Include",
    "risk_level": "High",
    "llm_rationale": "Critical field for regulatory reporting"
  }
]'''
        
        if old_prompt in content:
            content = content.replace(old_prompt, new_prompt)
            print("✅ Updated JSON instruction")
        
        # Fix 2: Add response validation
        # Find where the LLM response is processed
        parse_pattern = r'json\.loads\s*\(\s*llm_response'
        if re.search(parse_pattern, content):
            print("Found JSON parsing location")
            
            # Add validation before parsing
            validation_code = '''
                # Validate response format
                if isinstance(llm_response, str):
                    llm_response = llm_response.strip()
                    if llm_response.upper() == 'OK' or not llm_response.startswith('['):
                        logger.error(f"Invalid LLM response format: {llm_response[:100]}")
                        logger.info("Retrying with more explicit prompt...")
                        # Retry with ultra-explicit prompt
                        retry_prompt = f"""Return ONLY a JSON array starting with [ and ending with ].
Do not write OK or any other text.

Example: [{{"attribute_id": 1, "attribute_name": "field1", "recommended_action": "Include", "risk_level": "High", "llm_rationale": "Important field"}}]

Now generate for: {prompt_content[-1000:]}"""
                        llm_response = await self.llm_service.call_llm(
                            prompt_content=retry_prompt,
                            system_prompt="You are a JSON generator. Output only valid JSON arrays."
                        )
'''
            
            # Insert validation before JSON parsing
            content = re.sub(
                r'(\s+)(recommendations = json\.loads\s*\(\s*llm_response)',
                validation_code + r'\n\1\2',
                content
            )
            print("✅ Added response validation")
    
    # Write the fixed content
    with open(service_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {service_path}")
    return True

def create_test_script():
    """Create a script to test the fix"""
    test_script = '''#!/usr/bin/env python3
"""Test LLM fix"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.scoping_service import ScopingService

async def test():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"
    )
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        service = ScopingService(db)
        
        class MockUser:
            user_id = 3
            email = "tester@example.com"
        
        result = await service.generate_llm_recommendations(
            cycle_id=58,
            report_id=156,
            current_user=MockUser(),
            is_regeneration=True
        )
        
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test())
'''
    
    with open('test_llm_fix.py', 'w') as f:
        f.write(test_script)
    os.chmod('test_llm_fix.py', 0o755)
    print("✅ Created test_llm_fix.py")

def main():
    print("=" * 60)
    print("LLM Service Auto-Fixer")
    print("=" * 60)
    
    # Analyze the service
    print("\n1. Analyzing scoping service...")
    findings = analyze_scoping_service()
    print(f"Found {len(findings)} prompt locations")
    
    for finding in findings:
        print(f"\nLine {finding['line']}: {finding['match'][:100]}...")
    
    # Fix data profiling service (where scoping recommendations are)
    print("\n2. Fixing data profiling service...")
    fix_data_profiling_service()
    
    # Create test script
    print("\n3. Creating test script...")
    create_test_script()
    
    print("\n✅ Fix complete!")
    print("Run './test_llm_fix.py' to test the changes")

if __name__ == "__main__":
    main()