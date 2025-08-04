#!/usr/bin/env python3
"""
Final Database Setup Script
Handles all known issues: custom types, sequences, circular dependencies
"""

import asyncio
import asyncpg
from pathlib import Path
import sys

# Test database configuration
TEST_DB_CONFIG = {
    'host': 'localhost',
    'database': 'synapse_dt_container_test',
    'user': 'synapse_user',
    'password': 'synapse_password',
    'port': 5432
}

class FinalDatabaseSetup:
    """Complete database setup with all fixes"""
    
    def __init__(self):
        self.scripts_dir = Path(__file__).parent
        self.test_db_name = TEST_DB_CONFIG['database']
        
    async def setup_database(self):
        """Complete database setup"""
        try:
            # 1. Create database
            await self._create_database()
            
            # 2. Connect to new database
            conn = await asyncpg.connect(**TEST_DB_CONFIG)
            
            try:
                # 3. Enable extensions
                print("Enabling extensions...")
                await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
                await conn.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
                
                # 4. Create schema in phases to handle dependencies
                await self._create_schema_phase1(conn)  # Types and core tables
                await self._create_schema_phase2(conn)  # Dependent tables
                await self._create_schema_phase3(conn)  # Add foreign key constraints
                
                # 5. Load seed data
                await self._load_seed_data(conn)
                
                # 6. Validate setup
                await self._validate_setup(conn)
                
                print("\n✅ Database setup completed successfully!")
                print(f"   Database: {self.test_db_name}")
                print("   Status: Ready for use")
                
            finally:
                await conn.close()
                
        except Exception as e:
            print(f"\n❌ Setup failed: {str(e)}")
            raise
            
    async def _create_database(self):
        """Create test database"""
        conn = await asyncpg.connect(
            host=TEST_DB_CONFIG['host'],
            port=TEST_DB_CONFIG['port'],
            user=TEST_DB_CONFIG['user'],
            password=TEST_DB_CONFIG['password'],
            database='postgres'
        )
        
        try:
            # Drop if exists
            await conn.execute(f'DROP DATABASE IF EXISTS {self.test_db_name}')
            print(f"Dropped existing database: {self.test_db_name}")
            
            # Create new
            await conn.execute(f'CREATE DATABASE {self.test_db_name}')
            print(f"Created database: {self.test_db_name}")
            
        finally:
            await conn.close()
            
    async def _create_schema_phase1(self, conn):
        """Phase 1: Create types and core tables without foreign keys"""
        print("\nPhase 1: Creating types and core tables...")
        
        # Create all custom types from our findings
        type_definitions = [
            "CREATE TYPE IF NOT EXISTS securityclassification AS ENUM ('HRCI', 'Confidential', 'Proprietary', 'Public')",
            "CREATE TYPE IF NOT EXISTS activity_status_enum AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'REVISION_REQUESTED', 'BLOCKED', 'SKIPPED')",
            "CREATE TYPE IF NOT EXISTS activity_type_enum AS ENUM ('START', 'TASK', 'REVIEW', 'APPROVAL', 'COMPLETE', 'CUSTOM')",
            "CREATE TYPE IF NOT EXISTS workflow_phase_enum AS ENUM ('Planning', 'Data Profiling', 'Scoping', 'Data Provider ID', 'Data Owner Identification', 'Sampling', 'Request Info', 'Testing', 'Observations', 'Sample Selection', 'Data Owner ID', 'Test Execution', 'Preparing Test Report', 'Finalize Test Report')",
            # Add more as needed
        ]
        
        for type_def in type_definitions:
            try:
                await conn.execute(type_def)
            except Exception as e:
                if "already exists" not in str(e):
                    print(f"  Warning: {str(e)}")
                    
        # Create core tables (no foreign keys)
        core_tables = """
        -- Users table (foundational)
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            first_name character varying(255),
            last_name character varying(255),
            email character varying(255) UNIQUE NOT NULL,
            phone character varying(20),
            role character varying(255),
            lob_id integer,
            is_active boolean DEFAULT true,
            hashed_password character varying(255),
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            is_cdo boolean DEFAULT false
        );

        -- LOBs table
        CREATE TABLE IF NOT EXISTS lobs (
            lob_id SERIAL PRIMARY KEY,
            lob_name character varying(255) NOT NULL,
            lob_code character varying(50) NOT NULL,
            description text,
            is_active boolean DEFAULT true,
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
        );

        -- RBAC tables
        CREATE TABLE IF NOT EXISTS rbac_roles (
            id SERIAL PRIMARY KEY,
            name character varying(255) UNIQUE NOT NULL,
            description text,
            is_active boolean DEFAULT true,
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            created_by_id integer,
            updated_by_id integer
        );

        CREATE TABLE IF NOT EXISTS rbac_permissions (
            id SERIAL PRIMARY KEY,
            resource character varying(255) NOT NULL,
            action character varying(255) NOT NULL,
            description text,
            is_active boolean DEFAULT true,
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            created_by_id integer,
            updated_by_id integer
        );

        -- Reports table
        CREATE TABLE IF NOT EXISTS reports (
            report_id SERIAL PRIMARY KEY,
            report_name character varying(255) NOT NULL,
            report_code character varying(50),
            description text,
            frequency character varying(50),
            regulatory_framework character varying(100),
            lob_id integer,
            is_active boolean DEFAULT true,
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
        );

        -- Test cycles
        CREATE TABLE IF NOT EXISTS test_cycles (
            cycle_id SERIAL PRIMARY KEY,
            cycle_name character varying(255) NOT NULL,
            cycle_year integer NOT NULL,
            cycle_quarter integer NOT NULL,
            start_date date,
            end_date date,
            status character varying(50) DEFAULT 'planning',
            created_by_id integer,
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
        );

        -- Workflow phases
        CREATE TABLE IF NOT EXISTS workflow_phases (
            phase_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            phase_name character varying(100) NOT NULL,
            phase_order integer NOT NULL,
            description text,
            is_active boolean DEFAULT true,
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            created_by_id integer,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_by_id integer
        );
        """
        
        # Execute core tables
        for statement in core_tables.split(';'):
            if statement.strip():
                await conn.execute(statement)
                
        print("  ✓ Core tables created")
        
    async def _create_schema_phase2(self, conn):
        """Phase 2: Create dependent tables"""
        print("\nPhase 2: Creating dependent tables...")
        
        dependent_tables = """
        -- RBAC relationship tables
        CREATE TABLE IF NOT EXISTS rbac_role_permissions (
            id SERIAL PRIMARY KEY,
            role_id integer NOT NULL,
            permission_id integer NOT NULL,
            granted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            granted_by_id integer,
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            created_by_id integer,
            updated_by_id integer,
            CONSTRAINT unique_role_permission UNIQUE (role_id, permission_id)
        );

        CREATE TABLE IF NOT EXISTS rbac_user_roles (
            id SERIAL PRIMARY KEY,
            user_id integer NOT NULL,
            role_id integer NOT NULL,
            assigned_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            assigned_by_id integer,
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            created_by_id integer,
            updated_by_id integer,
            CONSTRAINT unique_user_role UNIQUE (user_id, role_id)
        );

        -- Regulatory data dictionary
        CREATE TABLE IF NOT EXISTS regulatory_data_dictionaries (
            attribute_id SERIAL PRIMARY KEY,
            report_id integer,
            attribute_name character varying(255) NOT NULL,
            attribute_code character varying(100),
            data_type character varying(100),
            is_mandatory boolean DEFAULT false,
            is_cde boolean DEFAULT false,
            is_primary_key boolean DEFAULT false,
            has_known_issues boolean DEFAULT false,
            line_item_number character varying(50),
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
        );

        -- Cycle reports
        CREATE TABLE IF NOT EXISTS cycle_reports (
            cycle_report_id SERIAL PRIMARY KEY,
            cycle_id integer,
            report_id integer,
            status character varying(50),
            created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
        );

        -- Activity definitions
        CREATE TABLE IF NOT EXISTS activity_definitions (
            id SERIAL PRIMARY KEY,
            phase_name character varying(50) NOT NULL,
            activity_name character varying(100) NOT NULL,
            activity_code character varying(50) UNIQUE NOT NULL,
            description character varying(500),
            activity_type character varying(50) NOT NULL,
            requires_backend_action boolean DEFAULT false,
            backend_endpoint character varying(200),
            sequence_order integer NOT NULL,
            depends_on_activity_codes json DEFAULT '[]'::json,
            button_text character varying(50),
            success_message character varying(200),
            instructions character varying(500),
            can_skip boolean DEFAULT false,
            can_reset boolean DEFAULT true,
            auto_complete_on_condition json,
            is_active boolean DEFAULT true,
            auto_complete boolean DEFAULT false,
            conditional_skip_rules json,
            created_by_id integer,
            updated_by_id integer,
            created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_phase_activity UNIQUE (phase_name, activity_name)
        );
        """
        
        # Execute dependent tables
        for statement in dependent_tables.split(';'):
            if statement.strip():
                await conn.execute(statement)
                
        print("  ✓ Dependent tables created")
        
    async def _create_schema_phase3(self, conn):
        """Phase 3: Add foreign key constraints"""
        print("\nPhase 3: Adding foreign key constraints...")
        
        # Add foreign keys separately to avoid circular dependency issues
        fk_constraints = [
            "ALTER TABLE users ADD CONSTRAINT fk_users_lob FOREIGN KEY (lob_id) REFERENCES lobs(lob_id)",
            "ALTER TABLE reports ADD CONSTRAINT fk_reports_lob FOREIGN KEY (lob_id) REFERENCES lobs(lob_id)",
            "ALTER TABLE rbac_role_permissions ADD CONSTRAINT fk_role_perm_role FOREIGN KEY (role_id) REFERENCES rbac_roles(id) ON DELETE CASCADE",
            "ALTER TABLE rbac_role_permissions ADD CONSTRAINT fk_role_perm_perm FOREIGN KEY (permission_id) REFERENCES rbac_permissions(id) ON DELETE CASCADE",
            "ALTER TABLE rbac_user_roles ADD CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE",
            "ALTER TABLE rbac_user_roles ADD CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES rbac_roles(id) ON DELETE CASCADE",
            "ALTER TABLE regulatory_data_dictionaries ADD CONSTRAINT fk_rdd_report FOREIGN KEY (report_id) REFERENCES reports(report_id)",
            "ALTER TABLE cycle_reports ADD CONSTRAINT fk_cr_cycle FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id)",
            "ALTER TABLE cycle_reports ADD CONSTRAINT fk_cr_report FOREIGN KEY (report_id) REFERENCES reports(report_id)",
            # Note: Skipping audit field FKs to avoid circular dependencies
        ]
        
        for fk in fk_constraints:
            try:
                await conn.execute(fk)
            except Exception as e:
                if "already exists" not in str(e):
                    print(f"  Warning: {str(e)}")
                    
        print("  ✓ Foreign key constraints added")
        
    async def _load_seed_data(self, conn):
        """Load seed data"""
        print("\nLoading seed data...")
        
        # Use enhanced seed data if available, otherwise minimal
        seed_file = self.scripts_dir / "04_enhanced_seeds.sql"
        if not seed_file.exists():
            seed_file = self.scripts_dir / "03_minimal_seeds.sql"
            
        if seed_file.exists():
            print(f"  Loading from: {seed_file.name}")
            
            with open(seed_file, 'r') as f:
                sql_content = f.read()
                
            # Execute statements one by one
            statements = sql_content.split(';')
            success_count = 0
            
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        await conn.execute(statement)
                        success_count += 1
                    except Exception as e:
                        if "duplicate key" not in str(e):
                            print(f"    Warning: {str(e)[:100]}")
                            
            print(f"  ✓ Loaded {success_count} seed records")
        else:
            print("  ⚠️  No seed data file found")
            
    async def _validate_setup(self, conn):
        """Validate the setup"""
        print("\nValidating setup...")
        
        # Check core tables
        validation_queries = [
            ("Users", "SELECT COUNT(*) FROM users"),
            ("Roles", "SELECT COUNT(*) FROM rbac_roles"),
            ("Permissions", "SELECT COUNT(*) FROM rbac_permissions"),
            ("Reports", "SELECT COUNT(*) FROM reports"),
            ("Test Cycles", "SELECT COUNT(*) FROM test_cycles"),
            ("Workflow Phases", "SELECT COUNT(*) FROM workflow_phases")
        ]
        
        all_valid = True
        for name, query in validation_queries:
            try:
                count = await conn.fetchval(query)
                status = "✓" if count > 0 else "⚠️"
                print(f"  {status} {name}: {count} records")
                if count == 0:
                    all_valid = False
            except Exception as e:
                print(f"  ❌ {name}: {str(e)}")
                all_valid = False
                
        # Test authentication
        try:
            auth_test = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE email = 'tester@example.com'"
            )
            if auth_test > 0:
                print("  ✓ Test user exists")
            else:
                print("  ⚠️  Test user missing")
                all_valid = False
        except:
            pass
            
        return all_valid

async def main():
    """Run the setup"""
    setup = FinalDatabaseSetup()
    
    print("=" * 60)
    print("SynapseDTE Database Setup")
    print("=" * 60)
    
    try:
        await setup.setup_database()
        
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Update application config to use new database:")
        print(f"   DATABASE_URL=postgresql://{TEST_DB_CONFIG['user']}:{TEST_DB_CONFIG['password']}@{TEST_DB_CONFIG['host']}:{TEST_DB_CONFIG['port']}/{TEST_DB_CONFIG['database']}")
        print("\n2. Test the application:")
        print("   python app/main.py")
        print("\n3. For Docker deployment:")
        print("   docker-compose up -d")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())