"""
Test script to verify document extraction uses regulation-specific prompts
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import HybridLLMService
from app.core.logging import get_logger

logger = get_logger(__name__)

async def test_document_extraction():
    """Test document extraction with regulation-specific prompts"""
    
    # Initialize LLM service
    llm_service = HybridLLMService()
    
    # Test cases for different regulations
    test_cases = [
        {
            "name": "FR Y-14M Schedule D.1 Credit Card",
            "document_content": """
            Credit Card Statement
            Account Number: ****1234
            
            Account Summary:
            Current Balance: $2,543.67
            Credit Limit: $10,000.00
            Available Credit: $7,456.33
            Minimum Payment Due: $75.00
            Payment Due Date: 01/15/2024
            
            APR Information:
            Purchase APR: 18.99%
            Cash Advance APR: 24.99%
            """,
            "attribute_name": "CREDIT_LIMIT_AMT",
            "attribute_context": {
                "data_type": "Currency",
                "description": "Total credit limit on the account",
                "keywords_to_look_for": "credit limit, limit amount"
            },
            "primary_key_field": "ACCT_NUM",
            "primary_key_value": "****1234",
            "cycle_id": 1,
            "report_id": 1,
            "regulatory_report": "fr_y_14m",
            "regulatory_schedule": "schedule_d_1"
        },
        {
            "name": "FR Y-14M Schedule A.1 Mortgage",
            "document_content": """
            Mortgage Statement
            Loan Number: 123456789
            Property Address: 123 Main St, Anytown, ST 12345
            
            Loan Information:
            Original Loan Amount: $250,000.00
            Current Principal Balance: $223,456.78
            Interest Rate: 4.25%
            Monthly Payment (P&I): $1,229.85
            
            Loan Origination Date: 06/15/2020
            Maturity Date: 06/15/2050
            """,
            "attribute_name": "CURR_BAL_AMT",
            "attribute_context": {
                "data_type": "Currency",
                "description": "Current principal balance of the mortgage",
                "keywords_to_look_for": "current balance, principal balance"
            },
            "primary_key_field": "LOAN_ID",
            "primary_key_value": "123456789",
            "cycle_id": 2,
            "report_id": 2,
            "regulatory_report": "fr_y_14m",
            "regulatory_schedule": "schedule_a_1"
        },
        {
            "name": "General Document (No Regulation)",
            "document_content": """
            Account Statement
            Account: 9876543
            
            Balance Information:
            Current Balance: $5,000.00
            Previous Balance: $4,500.00
            """,
            "attribute_name": "Current Balance",
            "attribute_context": {
                "data_type": "Currency",
                "description": "Current account balance"
            },
            "primary_key_field": "Account",
            "primary_key_value": "9876543",
            "cycle_id": 3,
            "report_id": 3,
            "regulatory_report": None,
            "regulatory_schedule": None
        }
    ]
    
    print("\n=== Testing Document Extraction with Regulation-Specific Prompts ===\n")
    
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
                cycle_id=test_case.get("cycle_id"),
                report_id=test_case.get("report_id"),
                regulatory_report=test_case.get("regulatory_report"),
                regulatory_schedule=test_case.get("regulatory_schedule")
            )
            
            if result.get("success"):
                print(f"✓ Extraction successful!")
                print(f"  - Extracted Value: {result.get('extracted_value')}")
                print(f"  - Confidence Score: {result.get('confidence_score')}")
                print(f"  - Evidence: {result.get('evidence', 'N/A')}")
                print(f"  - Location: {result.get('location', 'N/A')}")
            else:
                print(f"✗ Extraction failed: {result.get('error')}")
                
        except Exception as e:
            print(f"✗ Error during extraction: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n=== Test Complete ===\n")

if __name__ == "__main__":
    asyncio.run(test_document_extraction())