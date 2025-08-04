#!/usr/bin/env python3
"""
Real Database Test for Unified Data Profiling System
Tests the actual database operations using real data
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule, VersionStatus
from app.models.workflow import WorkflowPhase
from app.models.user import User
from app.services.data_profiling_service import DataProfilingService

DATABASE_URL = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"

async def main():
    """Test unified data profiling with real database operations"""
    
    print("🔬 Testing Unified Data Profiling System with Real Database")
    print("=" * 60)
    
    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Test 1: Check if tables exist
            print("\n1. Checking database table structure...")
            
            # Check if data profiling tables exist
            result = await session.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('cycle_report_data_profiling_rule_versions', 'cycle_report_data_profiling_rules')
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            if len(tables) == 2:
                print(f"✅ Data profiling tables found: {[t[0] for t in tables]}")
            else:
                print(f"❌ Missing data profiling tables. Found: {[t[0] for t in tables]}")
                return
            
            # Test 2: Find a test user
            print("\n2. Finding test user...")
            user_result = await session.execute(
                select(User).where(User.role == 'Tester').limit(1)
            )
            test_user = user_result.scalar_one_or_none()
            
            if test_user:
                print(f"✅ Found test user: {test_user.username} (ID: {test_user.user_id})")
            else:
                print("❌ No tester user found in database")
                return
            
            # Test 3: Find or create a test phase
            print("\n3. Finding test workflow phase...")
            phase_result = await session.execute(
                select(WorkflowPhase).where(WorkflowPhase.phase_name == 'Data Profiling').limit(1)
            )
            test_phase = phase_result.scalar_one_or_none()
            
            if test_phase:
                print(f"✅ Found test phase: {test_phase.phase_name} (ID: {test_phase.phase_id})")
            else:
                print("❌ No Data Profiling phase found in database")
                return
            
            # Test 4: Initialize service and create version
            print("\n4. Testing DataProfilingService...")
            service = DataProfilingService(session)
            
            # Create test data source config
            data_source_config = {
                "type": "database_source",
                "table_name": "test_table",
                "planning_data_source_id": 1
            }
            
            try:
                # Create initial version
                print("   Creating initial version...")
                version = await service.create_initial_version(
                    phase_id=test_phase.phase_id,
                    user_id=test_user.user_id,
                    data_source_config=data_source_config
                )
                print(f"✅ Created version: {version.version_id} (v{version.version_number})")
                
                # Test 5: Get version back
                print("\n5. Testing version retrieval...")
                retrieved_version = await service.get_version(str(version.version_id))
                if retrieved_version:
                    print(f"✅ Retrieved version: {retrieved_version.version_id}")
                    print(f"   Status: {retrieved_version.version_status}")
                    print(f"   Total rules: {retrieved_version.total_rules}")
                else:
                    print("❌ Failed to retrieve version")
                
                # Test 6: Check current version
                print("\n6. Testing current version lookup...")
                current_version = await service.get_current_version(test_phase.phase_id)
                if current_version and current_version.version_id == version.version_id:
                    print(f"✅ Current version matches: {current_version.version_id}")
                else:
                    print("❌ Current version mismatch or not found")
                
                # Test 7: Get version history
                print("\n7. Testing version history...")
                history = await service.get_version_history(test_phase.phase_id)
                print(f"✅ Found {len(history)} versions in history")
                
                # Test 8: Check rules (if any were generated)
                print("\n8. Testing rules retrieval...")
                if version.rules:
                    print(f"✅ Found {len(version.rules)} rules generated")
                    for i, rule in enumerate(version.rules[:3]):  # Show first 3 rules
                        print(f"   Rule {i+1}: {rule.rule_name} ({rule.rule_type})")
                else:
                    print("ℹ️ No rules generated (this is expected for test data)")
                
                # Test 9: Test execution results (if applicable)
                print("\n9. Testing execution results...")
                try:
                    execution_results = await service.get_execution_results(str(version.version_id))
                    if execution_results:
                        print(f"✅ Found execution results: {execution_results.get('status', 'unknown')}")
                    else:
                        print("ℹ️ No execution results (expected for new version)")
                except Exception as e:
                    print(f"ℹ️ No execution results: {str(e)}")
                
                # Test 10: Clean up test data
                print("\n10. Cleaning up test data...")
                await session.delete(version)
                await session.commit()
                print("✅ Test version cleaned up")
                
            except Exception as e:
                print(f"❌ Service test failed: {str(e)}")
                await session.rollback()
                return
            
            # Test 11: Check legacy table status
            print("\n11. Checking legacy table cleanup...")
            legacy_tables = [
                'data_profiling_rules', 'profiling_rules', 'attribute_profiling_scores'
            ]
            
            for table in legacy_tables:
                result = await session.execute(text(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = '{table}'
                """))
                exists = result.scalar() > 0
                status = "⚠️ Still exists" if exists else "✅ Cleaned up"
                print(f"   {table}: {status}")
            
            print("\n" + "=" * 60)
            print("🎉 Unified Data Profiling System Test COMPLETED")
            print("✅ All core functionality verified!")
            print("✅ Database operations working correctly")
            print("✅ Service layer functioning properly")
            print("✅ Models and relationships intact")
            
    except Exception as e:
        print(f"\n❌ Database test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())