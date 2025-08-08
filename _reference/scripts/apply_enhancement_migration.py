#!/usr/bin/env python3
"""
Apply the enhancement tables migration directly
"""
import asyncio
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_alembic_migration():
    """Run the alembic migration for enhancement tables"""
    print("Running enhancement tables migration...")
    
    try:
        # First check current migration state
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        print("Current migration state:")
        print(result.stdout)
        
        # Run alembic upgrade to apply the enhancement migration
        result = subprocess.run(
            ["alembic", "upgrade", "enhancement_001"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ Enhancement tables migration completed successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migration: {str(e)}")
        return False
    
    return True


def verify_tables():
    """Verify that all enhancement tables were created"""
    print("\nVerifying enhancement tables...")
    
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
        import asyncio
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        
        async def check_tables():
            database_url = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"
            engine = create_async_engine(database_url, echo=False)
            
            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = ANY(:tables)
                    ORDER BY table_name
                """), {"tables": expected_tables})
                
                existing_tables = [row[0] for row in result]
                
                print(f"\nFound {len(existing_tables)} of {len(expected_tables)} expected tables:")
                
                missing_tables = []
                for table in expected_tables:
                    if table in existing_tables:
                        print(f"  ✅ {table}")
                    else:
                        print(f"  ❌ {table} (missing)")
                        missing_tables.append(table)
                
                if missing_tables:
                    print(f"\nMissing tables: {', '.join(missing_tables)}")
                
                return len(existing_tables) == len(expected_tables)
        
        return asyncio.run(check_tables())
        
    except Exception as e:
        print(f"❌ Error verifying tables: {str(e)}")
        return False


def main():
    """Main execution function"""
    print("Enhancement Tables Migration")
    print("=" * 50)
    print("Applying database changes for:")
    print("- Enhanced data source configuration")
    print("- LLM-assisted attribute mapping")
    print("- Enterprise-grade profiling (40-50M records)")
    print("- Intelligent sample selection")
    print("- Dual-mode query capability")
    print("- HRCI/Confidential data masking")
    print("=" * 50)
    
    # Run migration
    if run_alembic_migration():
        # Verify tables
        if verify_tables():
            print("\n✅ All enhancement tables created successfully!")
            print("\n" + "=" * 50)
            print("MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 50)
            print("\nNext steps:")
            print("1. Configure data sources in the UI")
            print("2. Set up attribute mappings")
            print("3. Run profiling jobs")
            print("4. Use intelligent sampling")
        else:
            print("\n⚠️  Some tables may be missing. Check the migration logs.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")


if __name__ == "__main__":
    main()