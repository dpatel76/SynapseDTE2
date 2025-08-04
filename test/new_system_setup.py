#!/usr/bin/env python3
"""
New SynapseDTE System Setup Script

This script sets up a completely new SynapseDTE database with all foundational data.
Use this ONLY for new system installations, NOT for existing systems.
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from test.migration.foundational_seed_data_migration import upgrade as seed_upgrade
from app.core.database import Base


def setup_new_synapse_database(database_url: str):
    """Complete setup for new SynapseDTE database"""
    
    print("🚀 NEW SYNAPSDTE SYSTEM SETUP")
    print("=" * 50)
    print("⚠️  WARNING: This is for NEW systems only!")
    print("⚠️  Do NOT run on existing production databases!")
    print("=" * 50)
    
    try:
        engine = create_engine(database_url)
        
        print("1️⃣  Creating database schema...")
        
        # Import all models to register them with metadata
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
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("   ✅ Database schema created")
        
        print("2️⃣  Seeding foundational data...")
        
        # Mock the alembic op for our migration
        class MockOp:
            def __init__(self, connection):
                self.connection = connection
            
            def bulk_insert(self, table, data):
                if data:
                    columns = list(data[0].keys())
                    placeholders = ', '.join([f":{col}" for col in columns])
                    query = f"INSERT INTO {table.name} ({', '.join(columns)}) VALUES ({placeholders})"
                    self.connection.execute(text(query), data)
        
        with engine.connect() as conn:
            # Create alembic version table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))
            
            # Set up mock op for our migration
            import test.migration.foundational_seed_data_migration as migration_module
            migration_module.op = MockOp(conn)
            
            # Run the foundational data migration
            seed_upgrade()
            
            # Mark migration as applied
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('foundational_seed_data')"))
            conn.commit()
            
        print("   ✅ Foundational data seeded")
        
        print("3️⃣  Verifying setup...")
        
        # Verify key tables have data
        with engine.connect() as conn:
            tables_to_check = ['roles', 'permissions', 'lobs', 'sla_configurations']
            
            for table in tables_to_check:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   ✅ {table}: {count} rows")
        
        print("\n🎉 NEW SYNAPSDTE SYSTEM SETUP COMPLETE!")
        print("\n📋 Next Steps:")
        print("1. Create admin user: python scripts/setup/create_admin_user.py")
        print("2. Start application: uvicorn app.main:app --reload")
        print("3. Access system and create additional users")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


def main():
    """Main setup function"""
    
    if len(sys.argv) != 2:
        print("Usage: python test/new_system_setup.py <database_url>")
        print("\nExample:")
        print("  python test/new_system_setup.py postgresql://user:pass@localhost:5432/synapse_new")
        sys.exit(1)
    
    database_url = sys.argv[1]
    
    # Safety check
    print("🛡️  SAFETY CHECK")
    print(f"Database URL: {database_url}")
    print("\n⚠️  This will create/modify the specified database.")
    print("⚠️  Make sure this is a NEW, empty database!")
    
    confirmation = input("\nProceed with setup? Type 'NEW SYSTEM' to confirm: ")
    
    if confirmation != "NEW SYSTEM":
        print("❌ Setup cancelled for safety.")
        sys.exit(1)
    
    success = setup_new_synapse_database(database_url)
    
    if success:
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()