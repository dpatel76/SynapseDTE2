import asyncio
import sys
sys.path.append('.')
from app.services.llm_service import get_llm_service

async def test_full_generation():
    print('Testing full LLM generation...')
    llm = get_llm_service()
    
    try:
        result = await llm.generate_test_attributes(
            'CECL loan portfolio testing with borrower information, loan details, and payment history',
            'CECL Report',
            'gemini'
        )
        
        print('Result keys:', list(result.keys()))
        print('Success:', result.get('success'))
        
        if result.get('success'):
            print('Discovered count:', result.get('discovered_count'))
            print('Detailed count:', result.get('detailed_count'))
            print('Method:', result.get('method'))
            print('Discovery provider:', result.get('discovery_provider'))
            print('Details provider:', result.get('details_provider'))
            print('Batches processed:', result.get('batches_processed'))
            
            attributes = result.get('attributes', [])
            print(f'Total attributes: {len(attributes)}')
            
            if attributes:
                print('First 3 attributes:')
                for i, attr in enumerate(attributes[:3]):
                    print(f'  {i+1}. {attr.get("attribute_name")} ({attr.get("data_type")}) - {attr.get("mandatory_flag")}')
        else:
            print('Error:', result.get('error'))
            if 'raw_content' in result:
                print('Raw content preview:', result.get('raw_content')[:200])
            
    except Exception as e:
        print(f'Exception: {e}')
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    asyncio.run(test_full_generation()) 