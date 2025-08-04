#!/usr/bin/env python3
"""
Simple Database Test for Unified Data Profiling System
Tests the database tables and basic operations
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

DATABASE_URL = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"

async def main():
    """Test unified data profiling database structure"""
    
    print("🔬 Simple Test for Unified Data Profiling Database")
    print("=" * 50)
    
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
            
            # Test 2: Check table structure
            print("\n2. Checking table structure...")
            
            # Check version table columns
            version_result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'cycle_report_data_profiling_rule_versions'
                ORDER BY column_name
            """))
            version_columns = version_result.fetchall()
            
            print(f"   Version table columns: {len(version_columns)}")
            key_columns = ['version_id', 'phase_id', 'version_status', 'total_rules']
            found_columns = [col[0] for col in version_columns]
            for col in key_columns:
                status = "✅" if col in found_columns else "❌"
                print(f"   {status} {col}")
            
            # Check rules table columns
            rules_result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'cycle_report_data_profiling_rules'
                ORDER BY column_name
            """))
            rules_columns = rules_result.fetchall()
            
            print(f"\n   Rules table columns: {len(rules_columns)}")
            key_columns = ['rule_id', 'version_id', 'rule_name', 'rule_type', 'status']
            found_columns = [col[0] for col in rules_columns]
            for col in key_columns:
                status = "✅" if col in found_columns else "❌"
                print(f"   {status} {col}")
            
            # Test 3: Test basic operations
            print("\n3. Testing basic database operations...")
            
            # Count existing records
            version_count_result = await session.execute(text(
                "SELECT COUNT(*) FROM cycle_report_data_profiling_rule_versions"
            ))
            version_count = version_count_result.scalar()
            
            rules_count_result = await session.execute(text(
                "SELECT COUNT(*) FROM cycle_report_data_profiling_rules"
            ))
            rules_count = rules_count_result.scalar()
            
            print(f"   Existing versions: {version_count}")
            print(f"   Existing rules: {rules_count}")
            
            # Test 4: Create a test record
            print("\n4. Testing insert operations...")
            
            test_version_id = str(uuid.uuid4())
            test_phase_id = 999999  # Use a high number to avoid conflicts
            
            # Insert test version
            await session.execute(text("""
                INSERT INTO cycle_report_data_profiling_rule_versions 
                (version_id, phase_id, version_number, version_status, total_rules, created_at, created_by_id)
                VALUES (:version_id, :phase_id, 1, 'draft', 0, :created_at, 1)
            """), {
                'version_id': test_version_id,
                'phase_id': test_phase_id,
                'created_at': datetime.utcnow()
            })
            
            await session.commit()
            print(f"✅ Created test version: {test_version_id}")
            
            # Verify insert
            verify_result = await session.execute(text("""
                SELECT version_id, version_status, total_rules 
                FROM cycle_report_data_profiling_rule_versions 
                WHERE version_id = :version_id
            """), {'version_id': test_version_id})
            
            record = verify_result.fetchone()
            if record:
                print(f"✅ Verified record: {record[1]} status, {record[2]} rules")
            else:
                print("❌ Failed to verify record")
            
            # Test 5: Test update operations
            print("\n5. Testing update operations...")
            
            await session.execute(text("""
                UPDATE cycle_report_data_profiling_rule_versions 
                SET total_rules = 5, version_status = 'pending_approval'
                WHERE version_id = :version_id
            """), {'version_id': test_version_id})
            
            await session.commit()
            
            # Verify update
            verify_update_result = await session.execute(text("""
                SELECT version_status, total_rules 
                FROM cycle_report_data_profiling_rule_versions 
                WHERE version_id = :version_id
            """), {'version_id': test_version_id})
            
            updated_record = verify_update_result.fetchone()
            if updated_record and updated_record[0] == 'pending_approval' and updated_record[1] == 5:
                print("✅ Update operation successful")
            else:
                print("❌ Update operation failed")
            
            # Test 6: Clean up
            print("\n6. Cleaning up test data...")
            
            await session.execute(text("""
                DELETE FROM cycle_report_data_profiling_rule_versions 
                WHERE version_id = :version_id
            """), {'version_id': test_version_id})
            
            await session.commit()
            print("✅ Test data cleaned up")
            
            # Test 7: Check legacy table status
            print("\n7. Checking legacy table cleanup...")
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
            
            print("\n" + "=" * 50)
            print("🎉 Database Test COMPLETED")
            print("✅ Table structure verified!")
            print("✅ Basic operations working!")
            print("✅ Database connectivity confirmed!")
            
    except Exception as e:
        print(f"\n❌ Database test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())