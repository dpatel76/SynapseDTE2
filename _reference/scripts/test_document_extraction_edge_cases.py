"""
Test document extraction with edge cases and real-world scenarios
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import HybridLLMService
from app.core.logging import get_logger

logger = get_logger(__name__)

async def test_edge_cases():
    """Test document extraction with various edge cases"""
    
    # Initialize LLM service
    llm_service = HybridLLMService()
    
    # Edge case test scenarios
    test_cases = [
        {
            "name": "Empty Document",
            "document_content": "",
            "attribute_name": "CREDIT_LIMIT_AMT",
            "attribute_context": {"data_type": "Currency"},
            "primary_key_field": "ACCT_NUM",
            "primary_key_value": "1234",
            "expected_success": False
        },
        {
            "name": "Document Without Requested Attribute",
            "document_content": """
            Account Statement
            Account Number: 1234
            Customer Name: John Doe
            Statement Date: 01/01/2024
            
            Transaction History:
            - Purchase: $50.00
            - Payment: $100.00
            """,
            "attribute_name": "CREDIT_LIMIT_AMT",
            "attribute_context": {"data_type": "Currency", "description": "Credit limit amount"},
            "primary_key_field": "ACCT_NUM",
            "primary_key_value": "1234",
            "expected_success": True  # LLM should indicate it couldn't find the value
        },
        {
            "name": "Multiple Values for Same Attribute",
            "document_content": """
            Credit Card Statement
            Account: 1234
            
            Previous Credit Limit: $5,000.00
            New Credit Limit (effective 01/15/2024): $7,500.00
            Temporary Credit Limit Increase: $10,000.00 (expires 02/01/2024)
            """,
            "attribute_name": "CREDIT_LIMIT_AMT",
            "attribute_context": {"data_type": "Currency", "description": "Current credit limit"},
            "primary_key_field": "Account",
            "primary_key_value": "1234",
            "expected_success": True
        },
        {
            "name": "Wrong Primary Key",
            "document_content": """
            Credit Card Statement
            Account Number: 5678
            Credit Limit: $8,000.00
            """,
            "attribute_name": "CREDIT_LIMIT_AMT",
            "attribute_context": {"data_type": "Currency"},
            "primary_key_field": "Account Number",
            "primary_key_value": "1234",  # Wrong account number
            "expected_success": True  # Should indicate primary key mismatch
        },
        {
            "name": "Complex Document with Tables",
            "document_content": """
            Account Summary Report
            
            | Account | Type | Credit Limit | Balance | Status |
            |---------|------|--------------|---------|---------|
            | 1234    | VISA | $5,000.00   | $1,234.56| Active |
            | 5678    | MC   | $3,000.00   | $567.89 | Active |
            | 9012    | AMEX | $10,000.00  | $0.00   | Closed |
            """,
            "attribute_name": "CREDIT_LIMIT_AMT",
            "attribute_context": {"data_type": "Currency"},
            "primary_key_field": "Account",
            "primary_key_value": "1234",
            "expected_success": True
        },
        {
            "name": "Non-English Characters",
            "document_content": """
            账户报表
            Account/账号: 1234
            Credit Limit/信用额度: ¥50,000.00
            Available Credit/可用额度: ¥35,000.00
            """,
            "attribute_name": "CREDIT_LIMIT_AMT",
            "attribute_context": {"data_type": "Currency"},
            "primary_key_field": "Account",
            "primary_key_value": "1234",
            "expected_success": True
        },
        {
            "name": "Malformed/Corrupted Data",
            "document_content": """
            Acc###t St@tement
            Acc: 1234
            Cr#dit L!m*t: $5,0@0.#0
            B@l@nce: $1,2##.##
            """,
            "attribute_name": "CREDIT_LIMIT_AMT",
            "attribute_context": {"data_type": "Currency"},
            "primary_key_field": "Acc",
            "primary_key_value": "1234",
            "expected_success": True
        },
        {
            "name": "Very Long Document (truncated)",
            "document_content": "Credit Card Statement\nAccount: 1234\n" + ("Lorem ipsum dolor sit amet. " * 200) + "\nCredit Limit: $5,000.00\n" + ("More text here. " * 200),
            "attribute_name": "CREDIT_LIMIT_AMT",
            "attribute_context": {"data_type": "Currency"},
            "primary_key_field": "Account",
            "primary_key_value": "1234",
            "expected_success": True
        }
    ]
    
    print("\n=== Testing Document Extraction Edge Cases ===\n")
    
    success_count = 0
    for test_case in test_cases:
        print(f"\nTest Case: {test_case['name']}")
        print("-" * 50)
        
        try:
            result = await llm_service.extract_test_value_from_document(
                document_content=test_case["document_content"],
                attribute_name=test_case["attribute_name"],
                attribute_context=test_case["attribute_context"],
                primary_key_field=test_case["primary_key_field"],
                primary_key_value=test_case["primary_key_value"],
                cycle_id=1,
                report_id=1
            )
            
            if result.get("success"):
                print(f"✓ Extraction returned success")
                print(f"  - Extracted Value: {result.get('extracted_value', 'N/A')}")
                print(f"  - Confidence Score: {result.get('confidence_score', 0.0)}")
                print(f"  - Evidence: {result.get('evidence', 'N/A')[:100]}...")
                
                if test_case["expected_success"]:
                    success_count += 1
            else:
                print(f"✗ Extraction failed: {result.get('error', 'Unknown error')}")
                if "raw_response" in result and result["raw_response"]:
                    print(f"  - Raw response preview: {result['raw_response'][:200]}...")
                
                if not test_case["expected_success"]:
                    success_count += 1
                    
        except Exception as e:
            print(f"✗ Exception during extraction: {str(e)}")
            if not test_case["expected_success"]:
                success_count += 1
    
    print(f"\n=== Summary: {success_count}/{len(test_cases)} tests handled as expected ===\n")

if __name__ == "__main__":
    asyncio.run(test_edge_cases())