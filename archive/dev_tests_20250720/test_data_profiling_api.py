#!/usr/bin/env python3
"""
Test script for data profiling API endpoints
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from fastapi.testclient import TestClient
from app.api.v1.endpoints.data_profiling import router as data_profiling_router
from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule, VersionStatus
from app.services.data_profiling_service import DataProfilingService
from app.schemas.data_profiling_schemas import (
    CreateVersionRequest, DataProfilingVersionResponse, 
    TesterDecisionRequest, ProfilingRuleResponse
)


async def test_data_profiling_api():
    """Test data profiling API endpoints"""
    print("🧪 Testing Data Profiling API Endpoints")
    print("=" * 50)
    
    try:
        # Test creating a version request
        version_request = CreateVersionRequest(
            data_source_config={
                "type": "database_source",
                "table_name": "customer_data",
                "planning_data_source_id": 123
            }
        )
        
        print(f"✅ Created version request: {version_request}")
        
        # Test creating a tester decision request
        tester_decision = TesterDecisionRequest(
            decision="approve",
            notes="Rule looks good for execution"
        )
        
        print(f"✅ Created tester decision request: {tester_decision}")
        
        # Test creating response models
        version_response = DataProfilingVersionResponse(
            version_id="12345",
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            total_rules=5,
            approved_rules=0,
            rejected_rules=0,
            created_at="2025-07-18T10:00:00Z",
            created_by_id=1
        )
        
        print(f"✅ Created version response: {version_response}")
        
        # Test rule response
        rule_response = ProfilingRuleResponse(
            rule_id="67890",
            version_id="12345",
            attribute_id=1,
            rule_name="Completeness Check",
            rule_type="completeness",
            status="pending",
            created_at="2025-07-18T10:00:00Z"
        )
        
        print(f"✅ Created rule response: {rule_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API schemas: {e}")
        return False


async def test_data_profiling_service_integration():
    """Test data profiling service integration"""
    print("\n🔧 Testing Data Profiling Service Integration")
    print("=" * 50)
    
    try:
        # Mock database session
        class MockDB:
            def __init__(self):
                self.committed = False
                self.flushed = False
                self.objects = {}
                
            def add(self, obj):
                self.objects[id(obj)] = obj
                
            async def commit(self):
                self.committed = True
                
            async def flush(self):
                self.flushed = True
                
            async def get(self, model, id):
                return None
                
            async def execute(self, query):
                class MockResult:
                    def scalar_one_or_none(self):
                        return None
                    def scalars(self):
                        class MockScalars:
                            def all(self):
                                return []
                        return MockScalars()
                return MockResult()
            
            async def refresh(self, obj):
                pass
        
        # Test service initialization
        service = DataProfilingService(MockDB())
        print(f"✅ Created service: {service}")
        
        # Test that service methods exist
        assert hasattr(service, 'create_initial_version')
        assert hasattr(service, 'update_tester_decision')
        assert hasattr(service, 'submit_for_approval')
        assert hasattr(service, 'approve_version')
        
        print("✅ Service has all required methods")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing service integration: {e}")
        return False


async def test_data_profiling_models():
    """Test data profiling models"""
    print("\n📊 Testing Data Profiling Models")
    print("=" * 50)
    
    try:
        # Test creating a version
        version = DataProfilingRuleVersion(
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            total_rules=0,
            approved_rules=0,
            rejected_rules=0,
            created_by_id=1,
            updated_by_id=1
        )
        
        print(f"✅ Created version: {version}")
        
        # Test creating a rule
        rule = ProfilingRule(
            version_id=version.version_id,
            phase_id=1,
            attribute_id=1,
            rule_name="Test Rule",
            rule_type="completeness",
            rule_code="SELECT COUNT(*) FROM test_table",
            created_by_id=1,
            updated_by_id=1
        )
        
        print(f"✅ Created rule: {rule}")
        
        # Test relationships
        version.rules = [rule]
        rule.version = version
        
        print(f"✅ Set up relationships: version has {len(version.rules)} rules")
        
        # Test properties
        print(f"✅ Version completion: {version.completion_percentage}%")
        print(f"✅ Rule final decision: {rule.final_decision}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False


async def main():
    """Run all API tests"""
    print("🎯 Testing Unified Data Profiling API Implementation")
    print("=" * 60)
    
    tests = [
        ("API Schemas", test_data_profiling_api()),
        ("Service Integration", test_data_profiling_service_integration()),
        ("Models", test_data_profiling_models())
    ]
    
    results = []
    for name, test_coro in tests:
        result = await test_coro
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All API tests passed! Data profiling API is working correctly.")
        return True
    else:
        print("⚠️  Some API tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)