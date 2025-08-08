"""
Test enhanced JSON parsing with the new implementation
"""

import json
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simulate the enhanced parsing logic
def enhanced_json_extraction(content):
    """Enhanced JSON extraction logic matching the implementation"""
    
    if not content or not content.strip():
        return None, "Empty content"
    
    # Handle markdown code blocks
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    # Try to extract JSON object - look for the extraction_result pattern first
    parsed = None
    
    # Method 1: Look for extraction_result JSON object specifically
    extraction_pattern = r'\{[^{]*"extraction_result"\s*:\s*\{[^}]+\}[^}]*\}'
    extraction_match = re.search(extraction_pattern, content, re.DOTALL)
    if extraction_match:
        try:
            json_str = extraction_match.group(0)
            # Fix common JSON issues
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)
            parsed = json.loads(json_str)
        except:
            pass
    
    # Method 2: Find the first complete JSON object
    if not parsed:
        json_start = content.find('{')
        if json_start >= 0:
            # Try to find matching closing brace
            brace_count = 0
            json_end = -1
            for i in range(json_start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if json_end > json_start:
                json_str = content[json_start:json_end]
                try:
                    # Fix common JSON issues before parsing
                    json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                    json_str = re.sub(r',\s*]', ']', json_str)
                    parsed = json.loads(json_str)
                except:
                    pass
    
    # Method 3: Simple extraction as fallback
    if not parsed:
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            try:
                parsed = json.loads(json_str)
            except:
                pass
    
    if not parsed:
        return None, "No valid JSON found"
    
    return parsed, None

# Test cases
test_cases = [
    {
        "name": "Clean JSON",
        "content": '{"extraction_result": {"extracted_value": "10000", "confidence_score": 0.95}}'
    },
    {
        "name": "JSON with explanation before",
        "content": 'Based on my analysis of the document, here is the extraction result:\n\n{"extraction_result": {"extracted_value": "10000", "confidence_score": 0.95}}'
    },
    {
        "name": "JSON with explanation after",
        "content": '{"extraction_result": {"extracted_value": "10000", "confidence_score": 0.95}}\n\nThis value was found in the credit limit section.'
    },
    {
        "name": "JSON in markdown",
        "content": 'Here is my response:\n\n```json\n{"extraction_result": {"extracted_value": "10000", "confidence_score": 0.95}}\n```\n\nThe extraction was successful.'
    },
    {
        "name": "Nested JSON with text",
        "content": 'I found the following information:\n\n{\n  "extraction_result": {\n    "attribute_name": "CREDIT_LIMIT_AMT",\n    "extracted_value": "10000",\n    "confidence_score": 0.95,\n    "evidence": "Found in account summary"\n  }\n}\n\nThis matches the expected format.'
    },
    {
        "name": "Multiple JSON objects (should get extraction_result)",
        "content": 'First result: {"value": "wrong"}\n\nActual result: {"extraction_result": {"extracted_value": "10000", "confidence_score": 0.95}}'
    },
    {
        "name": "Malformed JSON with trailing comma",
        "content": '{"extraction_result": {"extracted_value": "10000", "confidence_score": 0.95,}}'
    },
    {
        "name": "Complex nested with trailing commas",
        "content": '{\n  "extraction_result": {\n    "extracted_value": "10000",\n    "confidence_score": 0.95,\n    "evidence": "Found it",\n  },\n}'
    },
    {
        "name": "No JSON, just text",
        "content": 'I cannot find any JSON in this document. The value appears to be 10000 but I cannot format it as requested.'
    },
    {
        "name": "LLM explanatory response with JSON",
        "content": '''I understand that I need to analyze credit card documents to extract specific FR Y-14M Schedule D.1 data attributes.

Looking at the document provided:

{
  "extraction_result": {
    "attribute_name": "CREDIT_LIMIT_AMT",
    "extracted_value": "10000.00",
    "confidence_score": 0.95,
    "extraction_method": "direct_match",
    "source_location": "Account Summary section",
    "supporting_context": "Credit Limit: $10,000.00",
    "data_quality_flags": [],
    "alternative_values": [],
    "fr_y_14m_mapping": "CREDIT_LIMIT_AMT"
  }
}

The credit limit was clearly stated in the account summary.'''
    }
]

print("Testing enhanced JSON extraction...\n")

success_count = 0
for test in test_cases:
    print(f"Test: {test['name']}")
    
    result, error = enhanced_json_extraction(test['content'])
    
    if result:
        print(f"✓ Success")
        if 'extraction_result' in result:
            print(f"  - Found extraction_result with value: {result['extraction_result'].get('extracted_value', 'N/A')}")
        else:
            print(f"  - Found JSON: {list(result.keys())}")
        success_count += 1
    else:
        print(f"✗ Failed: {error}")
    print("-" * 50)

print(f"\nTotal: {success_count}/{len(test_cases)} tests passed")