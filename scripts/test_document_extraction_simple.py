"""
Simple test to verify prompt loading
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.prompt_manager import PromptManager

def test_prompt_loading():
    """Test prompt loading"""
    
    prompt_manager = PromptManager()
    
    # Test loading FR Y-14M Schedule D.1 document extraction prompt
    template = prompt_manager.load_prompt_template(
        'document_extraction',
        regulatory_report='fr_y_14m',
        schedule='schedule_d_1'
    )
    
    if template:
        print("✓ Successfully loaded FR Y-14M Schedule D.1 document extraction prompt")
        
        # Test substitution
        context = {
            'document_content': 'Test document content',
            'attribute_name': 'CREDIT_LIMIT_AMT',
            'attribute_description': 'Credit limit amount',
            'primary_key_info': 'ACCT_NUM: 1234',
            'search_keywords': 'credit limit',
            'data_type': 'Currency'
        }
        
        rendered = template.safe_substitute(**context)
        print("\nRendered prompt preview (first 500 chars):")
        print("-" * 50)
        print(rendered[:500])
        print("...")
    else:
        print("✗ Failed to load prompt")
    
    # Test loading general document extraction prompt
    template_general = prompt_manager.load_prompt_template('document_extraction')
    if template_general:
        print("\n✓ Successfully loaded general document extraction prompt")
    else:
        print("\n✗ Failed to load general prompt")

if __name__ == "__main__":
    test_prompt_loading()