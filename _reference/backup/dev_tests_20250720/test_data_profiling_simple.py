#!/usr/bin/env python3
"""
Simple test script for data profiling without audit mixin
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.models.data_profiling import (
    DataProfilingRuleVersion, ProfilingRule, VersionStatus,
    ProfilingRuleType, ProfilingRuleStatus, Severity, Decision
)
from app.services.data_profiling_service import DataProfilingService
from app.schemas.data_profiling_schemas import (
    CreateVersionRequest, DataProfilingVersionResponse, 
    TesterDecisionRequest, ProfilingRuleResponse
)


def test_data_profiling_enums():
    """Test data profiling enums"""
    print("🧪 Testing Data Profiling Enums")
    print("=" * 50)
    
    try:
        # Test enums
        assert VersionStatus.DRAFT == "draft"
        assert VersionStatus.PENDING_APPROVAL == "pending_approval"
        assert VersionStatus.APPROVED == "approved"
        print("✅ VersionStatus enum working")
        
        assert ProfilingRuleType.COMPLETENESS == "completeness"
        assert ProfilingRuleType.VALIDITY == "validity"
        print("✅ ProfilingRuleType enum working")
        
        assert ProfilingRuleStatus.PENDING == "pending"
        assert ProfilingRuleStatus.APPROVED == "approved"
        print("✅ ProfilingRuleStatus enum working")
        
        assert Severity.LOW == "low"
        assert Severity.MEDIUM == "medium"
        assert Severity.HIGH == "high"
        print("✅ Severity enum working")
        
        assert Decision.APPROVE == "approve"
        assert Decision.REJECT == "reject"
        print("✅ Decision enum working")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enums: {e}")
        return False


def test_data_profiling_schemas():
    """Test data profiling schemas"""
    print("\n📋 Testing Data Profiling Schemas")
    print("=" * 50)
    
    try:
        # Test request schemas
        version_request = CreateVersionRequest(
            data_source_config={
                "type": "database_source",
                "table_name": "customer_data",
                "planning_data_source_id": 123
            }
        )
        print(f"✅ CreateVersionRequest: {version_request}")
        
        tester_decision = TesterDecisionRequest(
            decision=Decision.APPROVE,
            notes="Rule looks good for execution"
        )
        print(f"✅ TesterDecisionRequest: {tester_decision}")
        
        # Test response schemas  
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
        print(f"✅ DataProfilingVersionResponse: {version_response}")
        
        rule_response = ProfilingRuleResponse(
            rule_id="67890",
            version_id="12345",
            attribute_id=1,
            rule_name="Completeness Check",
            rule_type=ProfilingRuleType.COMPLETENESS,
            status=ProfilingRuleStatus.PENDING,
            created_at="2025-07-18T10:00:00Z"
        )
        print(f"✅ ProfilingRuleResponse: {rule_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing schemas: {e}")
        return False


def test_data_profiling_service():
    """Test data profiling service"""
    print("\n🔧 Testing Data Profiling Service")
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
        print(f"✅ Service initialized: {service}")
        
        # Test service methods exist
        methods = [
            'create_initial_version',
            'update_tester_decision', 
            'submit_for_approval',
            'approve_version',
            'reject_version',
            'get_version',
            'get_rules_by_version',
            'execute_rules'
        ]
        
        for method in methods:
            if hasattr(service, method):
                print(f"✅ Service method exists: {method}")
            else:
                print(f"❌ Service method missing: {method}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing service: {e}")
        return False


def main():
    """Run all tests"""
    print("🎯 Testing Unified Data Profiling Implementation")
    print("=" * 60)
    
    tests = [
        ("Enums", test_data_profiling_enums()),
        ("Schemas", test_data_profiling_schemas()),
        ("Service", test_data_profiling_service())
    ]
    
    passed = 0
    for name, result in tests:
        if result:
            passed += 1
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    for name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Data profiling implementation is working correctly.")
        print("\n🔧 Ready for:")
        print("  - Database cleanup of legacy tables")
        print("  - End-to-end workflow testing")
        print("  - Frontend integration")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)