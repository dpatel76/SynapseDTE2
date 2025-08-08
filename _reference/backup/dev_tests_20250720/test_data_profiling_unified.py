#!/usr/bin/env python3
"""
Test script for unified data profiling implementation
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule, VersionStatus
from app.services.data_profiling_service import DataProfilingService


async def test_data_profiling_models():
    """Test data profiling models creation"""
    print("Testing data profiling models...")
    
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
        
        # Test hybrid properties
        print(f"✅ Version completion: {version.completion_percentage}%")
        print(f"✅ Rule final decision: {rule.final_decision}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False


async def test_data_profiling_service():
    """Test data profiling service (mock mode)"""
    print("\nTesting data profiling service...")
    
    try:
        # Mock database session
        class MockDB:
            def __init__(self):
                self.committed = False
                self.flushed = False
                
            def add(self, obj):
                pass
                
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
        
        # Test service initialization
        service = DataProfilingService(MockDB())
        print(f"✅ Created service: {service}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing service: {e}")
        return False


def test_data_profiling_schemas():
    """Test data profiling schemas"""
    print("\nTesting data profiling schemas...")
    
    try:
        from app.schemas.data_profiling_schemas import (
            DataProfilingVersionResponse, ProfilingRuleResponse, 
            CreateVersionRequest, TesterDecisionRequest
        )
        
        # Test request schema
        request = CreateVersionRequest(
            data_source_config={
                "type": "database_source",
                "table_name": "test_table"
            }
        )
        print(f"✅ Created request: {request}")
        
        # Test response schema
        response = DataProfilingVersionResponse(
            version_id="123",
            phase_id=1,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            total_rules=5,
            approved_rules=0,
            rejected_rules=0,
            created_at="2025-07-18T10:00:00Z",
            created_by_id=1
        )
        print(f"✅ Created response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing schemas: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Testing Unified Data Profiling Implementation")
    print("=" * 50)
    
    tests = [
        ("Models", test_data_profiling_models()),
        ("Service", test_data_profiling_service()),
        ("Schemas", test_data_profiling_schemas())
    ]
    
    results = []
    for name, test_coro in tests:
        if asyncio.iscoroutine(test_coro):
            result = await test_coro
        else:
            result = test_coro
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Unified data profiling implementation is working.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)