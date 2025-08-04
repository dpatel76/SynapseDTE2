#!/usr/bin/env python3
"""
Simple test of LLM service to generate a single validation rule
"""
import asyncio
from app.services.llm_service import get_llm_service

async def simple_llm_test():
    """Test LLM service with a simple request"""
    
    print("🧪 Simple LLM Test")
    print("=" * 30)
    
    llm_service = get_llm_service()
    
    # Simple test prompt
    prompt = """
Generate a Python function that validates decimal precision for a pandas DataFrame column.
The function should:
1. Be named check_rule(df, column_name)
2. Check that values don't have more than 2 decimal places
3. Return {'passed': X, 'failed': Y, 'total': Z, 'pass_rate': P}
4. Handle type conversion errors gracefully
5. Use proper pandas patterns (no problematic .apply() with lambda)

Return ONLY the Python function code.
"""

    system_prompt = "You are a pandas expert. Generate clean, robust pandas code following best practices."
    
    try:
        response = await llm_service._generate_with_failover(
            prompt=prompt,
            system_prompt=system_prompt,
            preferred_provider="claude"
        )
        
        if response.get("success"):
            content = response.get("content", "")
            print(f"✅ LLM Response received ({len(content)} chars)")
            print("📄 Generated Code:")
            print("-" * 40)
            print(content)
            print("-" * 40)
            
            # Analyze for problematic patterns
            issues = []
            good_patterns = []
            
            if ".apply(lambda x:" in content:
                issues.append("❌ Uses problematic .apply(lambda x:) pattern")
            
            if "len(str(float(" in content and "try:" not in content:
                issues.append("❌ Complex type conversion without error handling")
            
            if "try:" in content and "except" in content:
                good_patterns.append("✅ Uses proper error handling")
            
            if "for " in content and " in " in content:
                good_patterns.append("✅ Uses explicit iteration instead of problematic lambda")
            
            print("\n📊 Code Analysis:")
            for pattern in good_patterns:
                print(pattern)
            for issue in issues:
                print(issue)
            
            if not issues:
                print("🎉 No problematic patterns found!")
            
            return len(issues) == 0
        else:
            print(f"❌ LLM failed: {response.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(simple_llm_test())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")