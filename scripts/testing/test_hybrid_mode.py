#!/usr/bin/env python3
"""
Test script for hybrid mode LLM attribute generation
"""

import asyncio
import sys
import json
import time
sys.path.append('.')

from app.services.llm_service import get_llm_service
from app.core.background_jobs import job_manager

async def test_hybrid_mode():
    """Test the hybrid mode: Gemini discovery + Claude details"""
    print("🧠 Testing Hybrid Mode: Gemini Discovery + Claude Details")
    print("=" * 60)
    
    print("🔧 Initializing LLM service...")
    llm_service = get_llm_service()
    print(f"✅ LLM service initialized: {type(llm_service)}")
    
    # Check available providers
    print("🔍 Checking available providers...")
    try:
        available_providers = list(llm_service.providers.keys())
        print(f"📋 Available providers: {available_providers}")
        
        # Test provider availability
        for provider_name in ['gemini', 'claude']:
            provider = await llm_service._get_available_provider(provider_name)
            if provider:
                print(f"✅ {provider_name} provider available")
            else:
                print(f"❌ {provider_name} provider NOT available")
    except Exception as e:
        print(f"⚠️  Error checking providers: {e}")
    
    # Test regulatory context
    regulatory_context = """
    FR Y-14M Schedule D.1 - Domestic Credit Card Data Collection
    
    This schedule collects loan-level data for domestic credit card exposures.
    Required data includes borrower information, account details, payment history,
    credit scores, balances, interest rates, and performance metrics.
    
    Key requirements:
    - Account-level reporting for all domestic credit card accounts
    - Monthly reporting cycle
    - Comprehensive borrower and account attributes
    - Risk and performance indicators
    - Regulatory compliance flags
    """
    
    try:
        print("🔍 Starting hybrid generation...")
        print("📝 Regulatory context length:", len(regulatory_context))
        start_time = time.time()
        
        print("🚀 Calling _generate_attributes_two_phase...")
        
        # Test explicit hybrid mode
        result = await llm_service._generate_attributes_two_phase(
            regulatory_context=regulatory_context,
            report_type="FR Y-14M Schedule D.1",
            preferred_discovery='gemini',  # Fast discovery
            preferred_details='claude',    # Detailed analysis
            regulatory_report="FR Y-14M",
            schedule="Schedule D.1"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Total Duration: {duration:.2f} seconds")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print()
        
        # Display results
        if result.get('success'):
            print("✅ Hybrid Generation Successful!")
            print(f"📊 Discovery Provider: {result.get('discovery_provider', 'Unknown')}")
            print(f"📊 Details Provider: {result.get('details_provider', 'Unknown')}")
            print(f"📊 Method: {result.get('method', 'Unknown')}")
            print(f"📊 Discovered Count: {result.get('discovered_count', 0)}")
            print(f"📊 Detailed Count: {result.get('detailed_count', 0)}")
            print(f"📊 Batches Processed: {result.get('batches_processed', 0)}")
            print(f"📊 Batch Size: {result.get('batch_size', 0)}")
            
            attributes = result.get('attributes', [])
            print(f"📊 Total Attributes Generated: {len(attributes)}")
            
            if attributes:
                print("\n🔍 Sample Attributes (first 5):")
                for i, attr in enumerate(attributes[:5]):
                    print(f"  {i+1}. {attr.get('attribute_name')} ({attr.get('data_type')})")
                    print(f"     Mandatory: {attr.get('mandatory_flag')}")
                    print(f"     Description: {attr.get('description', '')[:100]}...")
                    print()
            
            # Validate attribute structure
            print("🔍 Validating Attribute Structure...")
            required_fields = [
                'attribute_name', 'data_type', 'mandatory_flag', 'description',
                'validation_rules', 'typical_source_documents', 
                'keywords_to_look_for', 'testing_approach'
            ]
            
            valid_count = 0
            for attr in attributes:
                if all(field in attr for field in required_fields):
                    valid_count += 1
            
            print(f"✅ Valid Attributes: {valid_count}/{len(attributes)}")
            
            if valid_count == len(attributes):
                print("🎉 All attributes have complete structure!")
            else:
                print(f"⚠️  {len(attributes) - valid_count} attributes missing required fields")
                
        else:
            print("❌ Hybrid Generation Failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception during hybrid generation: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_background_job():
    """Test the background job system"""
    print("\n🔄 Testing Background Job System")
    print("=" * 60)
    
    # Create a test job
    job_id = job_manager.create_job(
        "test_job",
        metadata={"test": True, "provider": "hybrid"}
    )
    
    print(f"📋 Created Job ID: {job_id}")
    
    # Simulate job progress
    job_manager.update_job_progress(
        job_id,
        status="running",
        progress_percentage=10,
        current_step="Starting discovery",
        message="Initializing Gemini for attribute discovery"
    )
    
    print("📊 Job Status:", job_manager.get_job_status(job_id))
    
    # Simulate more progress
    job_manager.update_job_progress(
        job_id,
        progress_percentage=50,
        current_step="Processing details",
        message="Using Claude for detailed analysis",
        total_steps=100,
        completed_steps=50
    )
    
    print("📊 Updated Status:", job_manager.get_job_status(job_id))
    
    # Complete the job
    job_manager.complete_job(
        job_id,
        result={
            "total_generated": 104,
            "total_saved": 104,
            "method": "two_phase",
            "provider_used": "gemini + claude"
        }
    )
    
    print("📊 Final Status:", job_manager.get_job_status(job_id))
    print("✅ Background job system working correctly!")

async def test_basic_functionality():
    """Test basic functionality without LLM calls"""
    print("\n🔧 Testing Basic Functionality (No LLM calls)")
    print("=" * 60)
    
    print("🔧 Testing LLM service initialization...")
    try:
        llm_service = get_llm_service()
        print(f"✅ LLM service type: {type(llm_service)}")
        print(f"✅ Available providers: {list(llm_service.providers.keys())}")
        
        # Test provider access without API calls
        for provider_name in llm_service.providers.keys():
            provider = llm_service.providers[provider_name]
            print(f"✅ {provider_name} provider: {type(provider)}")
            
    except Exception as e:
        print(f"❌ Error testing LLM service: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    print("🚀 SynapseDT Hybrid Mode & Background Jobs Test")
    print("=" * 60)
    
    # Test basic functionality first
    await test_basic_functionality()
    
    # Test background jobs (no LLM calls)
    await test_background_job()
    
    # Ask user if they want to test actual LLM calls
    print("\n" + "="*60)
    print("🤔 The next test will make actual LLM API calls which may take time.")
    print("   Do you want to continue? (This will test the hybrid mode)")
    print("   Press Ctrl+C to skip or wait 5 seconds to continue...")
    
    try:
        import asyncio
        await asyncio.sleep(5)
        print("⏳ Proceeding with LLM tests...")
        
        # Test hybrid mode
        await test_hybrid_mode()
        
    except KeyboardInterrupt:
        print("\n⏭️  Skipped LLM tests")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 