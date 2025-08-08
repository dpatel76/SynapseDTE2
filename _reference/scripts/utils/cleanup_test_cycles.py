#!/usr/bin/env python3
"""
Script to clean up all test cycle related data from the database.
This will remove all test cycles and related data to start fresh.
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import sys

load_dotenv()

async def cleanup_test_cycles():
    """Remove all test cycle related data from the database"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        sys.exit(1)
    
    # Create async engine
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            print("\n=== Starting Test Cycle Data Cleanup ===\n")
            
            # Get counts before deletion
            print("Current data counts:")
            
            # Test cycles
            result = await session.execute(text("SELECT COUNT(*) FROM test_cycles"))
            count = result.scalar()
            print(f"  Test cycles: {count}")
            
            # Cycle reports
            result = await session.execute(text("SELECT COUNT(*) FROM cycle_reports"))
            count = result.scalar()
            print(f"  Cycle reports: {count}")
            
            # Workflow phases
            result = await session.execute(text("SELECT COUNT(*) FROM workflow_phases"))
            count = result.scalar()
            print(f"  Workflow phases: {count}")
            
            # Test executions
            result = await session.execute(text("SELECT COUNT(*) FROM cycle_report_test_execution_test_executions"))
            count = result.scalar()
            print(f"  Test executions: {count}")
            
            # Observations
            result = await session.execute(text("SELECT COUNT(*) FROM observations"))
            count = result.scalar()
            print(f"  Observations: {count}")
            
            # Observation groups
            result = await session.execute(text("SELECT COUNT(*) FROM observation_groups"))
            count = result.scalar()
            print(f"  Observation groups: {count}")
            
            # Confirmation
            print("\n⚠️  WARNING: This will delete ALL test cycle related data!")
            response = input("Are you sure you want to continue? (yes/no): ")
            
            if response.lower() != 'yes':
                print("Cleanup cancelled.")
                return
            
            print("\nDeleting data in correct order to respect foreign key constraints...")
            
            # Delete in reverse dependency order
            
            # 1. Delete observations (depends on observation_groups)
            result = await session.execute(text("DELETE FROM observations"))
            print(f"Deleted {result.rowcount} observations")
            
            # 2. Delete observation groups (depends on cycle_reports)
            result = await session.execute(text("DELETE FROM observation_groups"))
            print(f"Deleted {result.rowcount} observation groups")
            
            # 3. Delete test execution results
            result = await session.execute(text("DELETE FROM test_execution_results"))
            print(f"Deleted {result.rowcount} test execution results")
            
            # 4. Delete test executions (depends on workflow_phases)
            result = await session.execute(text("DELETE FROM cycle_report_test_execution_test_executions"))
            print(f"Deleted {result.rowcount} test executions")
            
            # 5. Delete workflow phase transitions
            result = await session.execute(text("DELETE FROM workflow_phase_transitions"))
            print(f"Deleted {result.rowcount} workflow phase transitions")
            
            # 6. Delete workflow phases (depends on cycle_reports)
            result = await session.execute(text("DELETE FROM workflow_phases"))
            print(f"Deleted {result.rowcount} workflow phases")
            
            # 7. Delete cycle report assignments if exists
            try:
                result = await session.execute(text("DELETE FROM cycle_report_assignments"))
                print(f"Deleted {result.rowcount} cycle report assignments")
            except:
                pass  # Table might not exist
            
            # 8. Delete cycle reports (depends on test_cycles)
            result = await session.execute(text("DELETE FROM cycle_reports"))
            print(f"Deleted {result.rowcount} cycle reports")
            
            # 9. Delete test cycles
            result = await session.execute(text("DELETE FROM test_cycles"))
            print(f"Deleted {result.rowcount} test cycles")
            
            # 10. Delete any LLM audit logs related to test cycles
            result = await session.execute(text("DELETE FROM llm_audit_logs WHERE context_type = 'test_cycle'"))
            print(f"Deleted {result.rowcount} LLM audit logs")
            
            # Commit the transaction
            await session.commit()
            
            print("\n✅ Cleanup completed successfully!")
            print("\nVerifying cleanup...")
            
            # Verify all data is deleted
            tables = [
                'test_cycles', 'cycle_reports', 'workflow_phases', 
                'test_executions', 'observations', 'observation_groups'
            ]
            
            all_clean = True
            for table in tables:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                if count > 0:
                    print(f"  ❌ {table}: {count} records remaining")
                    all_clean = False
                else:
                    print(f"  ✅ {table}: clean")
            
            if all_clean:
                print("\n🎉 All test cycle data has been successfully removed!")
                print("You can now start fresh with new test cycles.")
            else:
                print("\n⚠️  Some data remains. Please check the tables above.")
                
        except Exception as e:
            print(f"\n❌ Error during cleanup: {str(e)}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(cleanup_test_cycles())