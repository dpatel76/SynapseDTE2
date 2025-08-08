"""
Test JSON parsing robustness for various LLM response formats
"""

import json
import re

def extract_json_from_text(content):
    """Extract JSON from text that may contain explanatory content"""
    
    if not content or not content.strip():
        return None, "Empty content"
    
    # Handle markdown code blocks
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    # Try to find JSON object or array
    json_start = -1
    json_end = -1
    
    # Look for object
    obj_start = content.find('{')
    obj_end = content.rfind('}')
    
    # Look for array
    arr_start = content.find('[')
    arr_end = content.rfind(']')
    
    # Determine which comes first (object or array)
    if obj_start >= 0 and (arr_start < 0 or obj_start < arr_start):
        json_start = obj_start
        json_end = obj_end + 1
    elif arr_start >= 0:
        json_start = arr_start
        json_end = arr_end + 1
    
    if json_start >= 0 and json_end > json_start:
        json_str = content[json_start:json_end]
        try:
            return json.loads(json_str), None
        except json.JSONDecodeError as e:
            # Try to fix common issues
            # Remove trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            try:
                return json.loads(json_str), None
            except:
                return None, f"JSON parse error: {str(e)}"
    
    return None, "No JSON found"

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
        "name": "Multiple JSON objects (should get first)",
        "content": 'First result: {"value": "wrong"}\n\nActual result: {"extraction_result": {"extracted_value": "10000", "confidence_score": 0.95}}'
    },
    {
        "name": "Malformed JSON with trailing comma",
        "content": '{"extraction_result": {"extracted_value": "10000", "confidence_score": 0.95,}}'
    },
    {
        "name": "No JSON, just text",
        "content": 'I cannot find any JSON in this document. The value appears to be 10000 but I cannot format it as requested.'
    }
]

print("Testing JSON extraction robustness...\n")

for test in test_cases:
    print(f"Test: {test['name']}")
    print(f"Content: {test['content'][:50]}..." if len(test['content']) > 50 else f"Content: {test['content']}")
    
    result, error = extract_json_from_text(test['content'])
    
    if result:
        print(f"✓ Success: {json.dumps(result, indent=2)[:100]}...")
    else:
        print(f"✗ Failed: {error}")
    print("-" * 50)

# Now test the actual implementation's approach
print("\n\nTesting current implementation's approach:\n")

for test in test_cases:
    print(f"Test: {test['name']}")
    
    content = test['content']
    
    # Current implementation's logic
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    
    if json_start >= 0 and json_end > json_start:
        content = content[json_start:json_end]
        try:
            parsed = json.loads(content.strip())
            print(f"✓ Success with current approach")
        except Exception as e:
            print(f"✗ Failed with current approach: {str(e)}")
    else:
        print(f"✗ No JSON found with current approach")
    print("-" * 50)