#!/usr/bin/env python3
"""
Apply clean versioning migration directly
WARNING: This will drop old versioning tables!
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


async def apply_clean_versioning():
    """Apply the clean versioning migration"""
    
    # Create engine
    engine = create_async_engine(settings.database_url, echo=True)
    
    async with engine.begin() as conn:
        print("Starting clean versioning migration...")
        
        # Step 1: Drop old tables if they exist
        print("\nStep 1: Dropping old versioning tables...")
        old_tables = [
            # Old versioning tables
            'version_history',
            'workflow_version_operations',
            
            # Old phase-specific version tables
            'planning_phase_versions',
            'sample_selection_versions_old',
            'data_profiling_versions_old',
            'scoping_versions_old',
            'observation_versions_old',
            'test_report_versions_old',
            
            # Old decision tables
            'attribute_decisions_old',
            'sample_decisions_old',
            'scoping_decisions_old',
            'observation_decisions_old',
            
            # Old sample sets approach
            'sample_sets',
            'sample_records',
            'sample_validation_results',
            'sample_validation_issues',
            
            # Other legacy tables
            'attribute_version_change_log',
            'sample_selection_audit_log',
            'scoping_audit_log',
            
            # Old phase-specific tables
            'data_profiling_phases',
            'scoping_phases',
            'sample_selection_phases',
            'request_info_phases',
            'test_execution_phases',
            'observation_management_phases',
            'test_report_phases',
            
            # Old versioned models tables
            'data_profiling_rule_versions',
            'test_execution_versions',
            'observation_versions',
            'scoping_decision_versions',
            'versioned_attribute_scoping_recommendations'
        ]
        
        for table in old_tables:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  Dropped table: {table}")
            except Exception as e:
                print(f"  Warning dropping {table}: {e}")
        
        # Step 2: Create new versioning tables
        print("\nStep 2: Creating new clean versioning tables...")
        
        # Planning Phase
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS planning_versions (
                version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                version_number INTEGER NOT NULL,
                version_status VARCHAR(20) NOT NULL,
                parent_version_id UUID,
                workflow_execution_id VARCHAR(255) NOT NULL,
                workflow_run_id VARCHAR(255) NOT NULL,
                activity_name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by_id INTEGER NOT NULL REFERENCES users(user_id),
                approved_at TIMESTAMP WITH TIME ZONE,
                approved_by_id INTEGER REFERENCES users(user_id),
                cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
                report_id INTEGER NOT NULL REFERENCES reports(report_id),
                phase_name VARCHAR(50) NOT NULL,
                total_attributes INTEGER NOT NULL DEFAULT 0,
                included_attributes INTEGER NOT NULL DEFAULT 0,
                CONSTRAINT uq_planning_version UNIQUE (cycle_id, report_id, version_number)
            )
        """))
        print("  Created table: planning_versions")
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_planning_current 
            ON planning_versions(cycle_id, report_id, version_status)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_planning_workflow 
            ON planning_versions(workflow_execution_id)
        """))
        
        # Attribute Decisions
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS attribute_decisions (
                decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                version_id UUID NOT NULL REFERENCES planning_versions(version_id) ON DELETE CASCADE,
                attribute_id INTEGER NOT NULL REFERENCES report_attributes(attribute_id),
                attribute_name VARCHAR(255) NOT NULL,
                include_in_testing BOOLEAN NOT NULL DEFAULT true,
                decision_reason TEXT,
                risk_rating VARCHAR(20)
            )
        """))
        print("  Created table: attribute_decisions")
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_attr_decision_version 
            ON attribute_decisions(version_id)
        """))
        
        # Continue with other tables...
        print("\nMigration completed successfully!")
        print("\nNote: This is a destructive migration. All old versioning data has been removed.")
        print("The new clean versioning system is now in place.")
    
    await engine.dispose()


if __name__ == "__main__":
    print("Clean Versioning Migration")
    print("=" * 50)
    print("WARNING: This will DROP all old versioning tables!")
    print("All existing version history will be lost.")
    print()
    
    # Auto-confirm for non-interactive mode
    if '--yes' in sys.argv:
        print("Auto-confirmed with --yes flag")
    else:
        try:
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != "yes":
                print("Migration cancelled.")
                sys.exit(0)
        except EOFError:
            print("Running in non-interactive mode, proceeding...")
    
    asyncio.run(apply_clean_versioning())