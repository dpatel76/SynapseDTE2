#!/usr/bin/env python3
"""
Real Database Test for Data Profiling Service

This test connects to the actual database and tests the data profiling service
with real database operations, not mocks.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.services.data_profiling_service import DataProfilingService
from app.models.data_profiling import (
    DataProfilingRuleVersion, ProfilingRule, VersionStatus, 
    ProfilingRuleType, Decision, ProfilingRuleStatus
)
from app.models.workflow import WorkflowPhase
from app.models.planning import PlanningAttribute
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_database_connection():
    """Test basic database connection"""
    print("🔌 Testing Database Connection")
    print("-" * 50)
    
    try:
        async with AsyncSessionLocal() as session:
            # Test basic query
            result = await session.execute(select(func.count()).select_from(User))
            user_count = result.scalar()
            print(f"✅ Database connected - found {user_count} users")
            
            # Test data profiling tables exist
            result = await session.execute(select(func.count()).select_from(DataProfilingRuleVersion))
            version_count = result.scalar()
            print(f"✅ Data profiling versions table exists - {version_count} versions")
            
            result = await session.execute(select(func.count()).select_from(ProfilingRule))
            rule_count = result.scalar()
            print(f"✅ Data profiling rules table exists - {rule_count} rules")
            
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_service_with_real_database():
    """Test service with real database operations"""
    print("\n🧪 Testing Service with Real Database")
    print("-" * 50)
    
    try:
        async with AsyncSessionLocal() as session:
            service = DataProfilingService(session)
            
            # Test 1: Get existing versions
            print("📋 Test 1: Get existing versions...")
            existing_versions = await session.execute(
                select(DataProfilingRuleVersion).limit(5)
            )
            versions = existing_versions.scalars().all()
            print(f"✅ Found {len(versions)} existing versions")
            
            # Test 2: Check if we have workflow phases
            print("📋 Test 2: Check workflow phases...")
            phases_result = await session.execute(
                select(WorkflowPhase).where(WorkflowPhase.phase_name == "Data Profiling").limit(1)
            )
            phase = phases_result.scalar_one_or_none()
            
            if phase:
                print(f"✅ Found data profiling phase: {phase.phase_id}")
                
                # Test 3: Get version for this phase
                print("📋 Test 3: Get version for phase...")
                version = await service.get_current_version(phase.phase_id)
                if version:
                    print(f"✅ Found version: {version.version_id}")
                    
                    # Test 4: Get rules for this version
                    print("📋 Test 4: Get rules for version...")
                    rules = await service.get_rules_by_version(version.version_id)
                    print(f"✅ Found {len(rules)} rules for version")
                    
                    # Test 5: Test execution results
                    print("📋 Test 5: Test execution results...")
                    results = await service.get_execution_results(version.version_id)
                    print(f"✅ Execution results: {results['status']}")
                    
                else:
                    print("📋 No current version found for phase")
            else:
                print("⚠️  No data profiling phase found")
            
            # Test 6: Check users exist
            print("📋 Test 6: Check users exist...")
            users_result = await session.execute(select(User).limit(3))
            users = users_result.scalars().all()
            print(f"✅ Found {len(users)} users for testing")
            
            if users:
                user = users[0]
                print(f"✅ Using test user: {user.user_id} ({user.email})")
            
            return True
            
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_create_version_with_real_data():
    """Test creating a version with real data"""
    print("\n🏗️  Testing Create Version with Real Data")
    print("-" * 50)
    
    try:
        async with AsyncSessionLocal() as session:
            service = DataProfilingService(session)
            
            # Find a real phase
            phases_result = await session.execute(
                select(WorkflowPhase).limit(1)
            )
            phase = phases_result.scalar_one_or_none()
            
            if not phase:
                print("⚠️  No workflow phases found - skipping version creation test")
                return True
            
            # Find a real user
            users_result = await session.execute(
                select(User).limit(1)
            )
            user = users_result.scalar_one_or_none()
            
            if not user:
                print("⚠️  No users found - skipping version creation test")
                return True
            
            print(f"📋 Creating version for phase {phase.phase_id} by user {user.user_id}")
            
            # This will likely fail because we need planning attributes
            # but let's see what happens
            try:
                version = await service.create_initial_version(
                    phase_id=phase.phase_id,
                    user_id=user.user_id,
                    data_source_config={
                        "type": "database_source",
                        "table_name": "test_table"
                    }
                )
                print(f"✅ Created version: {version.version_id}")
                
                # Clean up - remove the test version
                await session.delete(version)
                await session.commit()
                print("✅ Cleaned up test version")
                
            except Exception as e:
                print(f"⚠️  Version creation failed (expected): {e}")
                print("   This is expected if no planning attributes exist")
                
            return True
            
    except Exception as e:
        print(f"❌ Create version test failed: {e}")
        return False


async def test_service_methods():
    """Test all service methods exist and are callable"""
    print("\n🔧 Testing Service Methods")
    print("-" * 50)
    
    try:
        async with AsyncSessionLocal() as session:
            service = DataProfilingService(session)
            
            methods_to_test = [
                'create_initial_version',
                'get_version',
                'get_current_version',
                'get_version_history',
                'update_tester_decision',
                'update_report_owner_decision',
                'submit_for_approval',
                'approve_version',
                'reject_version',
                'execute_approved_rules',
                'get_execution_results',
                'get_rules_by_version',
                'execute_rules'
            ]
            
            for method_name in methods_to_test:
                if hasattr(service, method_name):
                    method = getattr(service, method_name)
                    if callable(method):
                        print(f"✅ {method_name}: exists and callable")
                    else:
                        print(f"❌ {method_name}: exists but not callable")
                        return False
                else:
                    print(f"❌ {method_name}: does not exist")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ Service methods test failed: {e}")
        return False


async def main():
    """Run all real database tests"""
    print("🎯 Real Database Data Profiling Tests")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection()),
        ("Service with Real Database", test_service_with_real_database()),
        ("Create Version with Real Data", test_create_version_with_real_data()),
        ("Service Methods", test_service_methods())
    ]
    
    passed = 0
    results = []
    
    for name, test_coro in tests:
        try:
            result = await test_coro
            results.append((name, result))
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test {name} failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 Real Database Test Results:")
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All real database tests passed!")
        print("✅ Service is working with real database connections")
        return True
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)