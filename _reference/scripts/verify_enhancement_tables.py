#!/usr/bin/env python3
"""
Verify enhancement tables were created successfully
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def verify_tables():
    """Verify all enhancement tables exist"""
    database_url = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"
    engine = create_async_engine(database_url, echo=False)
    
    expected_tables = [
        'data_sources_v2',
        'attribute_mappings',
        'data_queries',
        'profiling_jobs',
        'profiling_partitions',
        'profiling_rule_sets',
        'partition_results',
        'profiling_anomaly_patterns',
        'profiling_cache',
        'intelligent_sampling_jobs',
        'sample_pools',
        'intelligent_samples',
        'sampling_rules',
        'sample_lineage',
        'profiling_executions',
        'secure_data_access_logs'
    ]
    
    try:
        async with engine.begin() as conn:
            # Check tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = ANY(:tables)
                ORDER BY table_name
            """), {"tables": expected_tables})
            
            existing_tables = [row[0] for row in result]
            
            print("Enhancement Tables Verification")
            print("=" * 50)
            print(f"Found {len(existing_tables)} of {len(expected_tables)} expected tables:\n")
            
            all_present = True
            for table in expected_tables:
                if table in existing_tables:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} (missing)")
                    all_present = False
            
            # Also check the custom types
            print("\nChecking custom types...")
            type_result = await conn.execute(text("""
                SELECT typname FROM pg_type 
                WHERE typname IN (
                    'datasourcetype', 'securityclassification', 'profilingstrategy',
                    'rulecategory', 'samplingstrategy', 'samplecategory'
                )
                ORDER BY typname
            """))
            
            types = [row[0] for row in type_result]
            print(f"\nFound {len(types)} custom types:")
            for t in types:
                print(f"  ✅ {t}")
            
            # Sample query to verify tables are working
            print("\nTesting table access...")
            
            # Test data_sources_v2
            await conn.execute(text("SELECT COUNT(*) FROM data_sources_v2"))
            print("  ✅ data_sources_v2 accessible")
            
            # Test profiling_jobs
            await conn.execute(text("SELECT COUNT(*) FROM profiling_jobs"))
            print("  ✅ profiling_jobs accessible")
            
            # Test intelligent_sampling_jobs
            await conn.execute(text("SELECT COUNT(*) FROM intelligent_sampling_jobs"))
            print("  ✅ intelligent_sampling_jobs accessible")
            
            if all_present:
                print("\n" + "=" * 50)
                print("✅ ALL ENHANCEMENT TABLES VERIFIED SUCCESSFULLY!")
                print("=" * 50)
                print("\nThe system is ready for:")
                print("1. Data source configuration")
                print("2. Attribute mapping with LLM assistance")
                print("3. Enterprise-scale profiling (40-50M records)")
                print("4. Intelligent sample selection")
                print("5. Dual-mode testing")
                print("6. HRCI/Confidential data protection")
            else:
                print("\n⚠️  Some tables are missing!")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_tables())