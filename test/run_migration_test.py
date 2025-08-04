#!/usr/bin/env python3
"""
Complete Migration Test Suite

This script safely tests the foundational migration by:
1. Creating an isolated test database
2. Running the migration
3. Comparing results against the production database
4. Generating a comprehensive report
5. Cleaning up test resources

SAFETY: Uses completely isolated test database - NO impact on production.
"""

import asyncio
import sys
import subprocess
import tempfile
import os
import shutil
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from test.create_test_database import create_test_database, cleanup_test_database
from test.database_reconciliation_report import run_reconciliation


class MigrationTester:
    """Orchestrates the complete migration testing process"""
    
    def __init__(self):
        self.test_info = None
        self.temp_alembic_dir = None
        
    async def setup_test_environment(self):
        """Set up isolated test environment"""
        print("🏗️  Setting up test environment...")
        
        # Create test database
        print("  📊 Creating test database...")
        self.test_info = create_test_database()
        if not self.test_info:
            raise Exception("Failed to create test database")
        
        print(f"  ✅ Test database ready: {self.test_info['database_name']}")
        
        # Create temporary alembic environment for test migration
        print("  ⚙️  Setting up test migration environment...")
        self.temp_alembic_dir = tempfile.mkdtemp(prefix="synapse_migration_test_")
        
        # Copy essential alembic files
        shutil.copy("alembic.ini", self.temp_alembic_dir)
        
        # Create versions directory and copy our test migration
        versions_dir = Path(self.temp_alembic_dir) / "alembic" / "versions"
        versions_dir.mkdir(parents=True)
        
        # Copy our foundational migration
        test_migration_file = versions_dir / "001_foundational_seed_data.py"
        shutil.copy("test/migration/foundational_seed_data_migration.py", test_migration_file)
        
        # Create alembic env.py for test
        alembic_dir = Path(self.temp_alembic_dir) / "alembic"
        alembic_dir.mkdir(exist_ok=True)
        
        env_py_content = f'''"""
Test Alembic environment for migration testing
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Add app path
sys.path.append('{Path(__file__).parent.parent.absolute()}')

from app.core.database import Base
import app.models.base
import app.models.lob  
import app.models.user
import app.models.rbac
import app.models.sla
import app.models.report
import app.models.test_cycle

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = "{self.test_info['url']}"
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = "{self.test_info['url']}"
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        
        with open(alembic_dir / "env.py", "w") as f:
            f.write(env_py_content)
            
        print(f"  ✅ Test migration environment ready at: {self.temp_alembic_dir}")
        
    async def run_schema_creation(self):
        """Create the database schema first"""
        print("  🏗️  Creating database schema...")
        
        try:
            # Use SQLAlchemy to create all tables
            from sqlalchemy import create_engine
            from app.core.database import Base
            
            # Import all models to register them
            import app.models.base
            import app.models.lob  
            import app.models.user
            import app.models.rbac
            import app.models.sla
            import app.models.report
            import app.models.test_cycle
            import app.models.cycle_report
            import app.models.workflow
            import app.models.document
            import app.models.report_attribute
            import app.models.scoping
            import app.models.data_owner
            import app.models.sample_selection
            import app.models.testing
            import app.models.audit
            import app.models.request_info
            import app.models.observation_management
            
            engine = create_engine(self.test_info['url'])
            Base.metadata.create_all(bind=engine)
            
            print("  ✅ Database schema created successfully")
            
        except Exception as e:
            print(f"  ❌ Schema creation failed: {e}")
            raise
    
    async def run_migration(self):
        """Run the foundational migration"""
        print("🚀 Running foundational migration...")
        
        try:
            # First create the schema
            await self.run_schema_creation()
            
            # Then run our data migration directly
            print("  📊 Executing foundational data migration...")
            
            from sqlalchemy import create_engine
            from test.migration.foundational_seed_data_migration import upgrade
            
            # Temporarily set up alembic context
            from alembic import context
            from alembic.config import Config
            
            engine = create_engine(self.test_info['url'])
            
            with engine.connect() as connection:
                # Create alembic_version table
                connection.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))")
                connection.execute("INSERT INTO alembic_version (version_num) VALUES ('001_foundational_seed_data') ON CONFLICT DO NOTHING")
                connection.commit()
                
                # Mock alembic context for our migration
                class MockOp:
                    def __init__(self, connection):
                        self.connection = connection
                    
                    def bulk_insert(self, table, data):
                        if data:
                            columns = list(data[0].keys())
                            placeholders = ', '.join([f":{col}" for col in columns])
                            query = f"INSERT INTO {table.name} ({', '.join(columns)}) VALUES ({placeholders})"
                            self.connection.execute(query, data)
                
                # Import and setup op for our migration
                import test.migration.foundational_seed_data_migration as migration_module
                migration_module.op = MockOp(connection)
                
                # Run the upgrade
                upgrade()
                connection.commit()
                
            print("  ✅ Foundational migration completed successfully")
            
        except Exception as e:
            print(f"  ❌ Migration failed: {e}")
            raise
    
    async def run_reconciliation(self):
        """Run reconciliation against production database"""
        print("🔍 Running reconciliation against production database...")
        
        try:
            report = await run_reconciliation(self.test_info['url'])
            return report
        except Exception as e:
            print(f"❌ Reconciliation failed: {e}")
            raise
    
    async def cleanup(self):
        """Clean up test resources"""
        print("🧹 Cleaning up test resources...")
        
        if self.test_info:
            cleanup_test_database(self.test_info)
            
        if self.temp_alembic_dir and os.path.exists(self.temp_alembic_dir):
            shutil.rmtree(self.temp_alembic_dir)
            print(f"  ✅ Removed temporary directory: {self.temp_alembic_dir}")
    
    async def run_complete_test(self):
        """Run the complete migration test suite"""
        print("🧪 SYNAPSDTE FOUNDATIONAL MIGRATION TEST SUITE")
        print("=" * 70)
        print("This test suite validates our foundational migration against")
        print("the current production database in a completely safe manner.")
        print("=" * 70)
        
        try:
            # Setup
            await self.setup_test_environment()
            
            # Run migration
            await self.run_migration()
            
            # Reconciliation
            report = await self.run_reconciliation()
            
            # Final assessment
            print("\\n🎯 FINAL ASSESSMENT")
            print("-" * 30)
            
            critical_issues = 0
            for table, comparison in report['detailed_comparison'].items():
                if not comparison['differences']['exists_in_both']:
                    if comparison['production']['exists']:
                        critical_issues += 1
                        print(f"❌ CRITICAL: Table '{table}' missing in migration")
                elif comparison['production']['row_count'] > 0 and comparison['test']['row_count'] == 0:
                    critical_issues += 1
                    print(f"⚠️  WARNING: Table '{table}' has no seed data")
            
            if critical_issues == 0:
                print("🎉 SUCCESS: Foundational migration covers all essential requirements!")
                print("✅ The migration file is ready for production use.")
            else:
                print(f"⚠️  {critical_issues} issues found that need attention before production use.")
            
            return report
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main test runner"""
    tester = MigrationTester()
    try:
        await tester.run_complete_test()
    except KeyboardInterrupt:
        print("\\n⏹️  Test interrupted by user")
        await tester.cleanup()
    except Exception as e:
        print(f"\\n💥 Test suite error: {e}")
        await tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())