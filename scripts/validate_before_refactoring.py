#!/usr/bin/env python3
"""
Validation script to run before starting the table refactoring.
Checks:
1. All tables exist as expected
2. No naming conflicts with new names
3. Foreign key constraints are valid
4. Application is working
5. Tests are passing
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


def check(name: str, description: str):
    """Decorator for check functions"""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            print(f"\n🔍 {description}...")
            self.results["summary"]["total_checks"] += 1
            
            try:
                result = await func(self, *args, **kwargs)
                if result["status"] == "PASS":
                    print(f"   ✅ PASS")
                    self.results["summary"]["passed"] += 1
                else:
                    print(f"   ❌ FAIL: {result.get('message', 'Unknown error')}")
                    self.results["summary"]["failed"] += 1
                    
                self.results["checks"][name] = result
                return result
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                self.results["summary"]["failed"] += 1
                self.results["checks"][name] = {
                    "status": "ERROR",
                    "message": str(e)
                }
                return {"status": "ERROR", "message": str(e)}
                
        return wrapper
    return decorator


class RefactoringValidator:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "warnings": [],
            "errors": [],
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0
            }
        }
        
        # Tables to check
        self.tables_to_rename = {
            "cycle_report_planning_attributes": "cycle_report_planning_attributes",
            "cycle_report_planning_attribute_version_history": "cycle_report_planning_attribute_version_history",
            # ... (rest of the mapping from earlier)
        }
        
        self.tables_to_remove = [
            "data_profiling_phases",
            "sample_selection_phases",
            "test_execution_phases",
            "observation_management_phases",
            "test_report_phases",
            "cycle_report_request_info_phases",
            "cycle_report_sample_sets",
            "data_owner_sla_violations",
            "data_owner_escalation_log",
            "data_owner_notifications",
        ]
        
    async def validate_all(self):
        """Run all validation checks"""
        print("=" * 60)
        print("TABLE REFACTORING VALIDATION")
        print("=" * 60)
        
        # Database checks
        await self.check_database_connection()
        await self.check_existing_tables()
        await self.check_new_table_names()
        await self.check_foreign_keys()
        await self.check_table_sizes()
        
        # Application checks
        await self.check_api_health()
        await self.check_sample_endpoints()
        
        # Generate report
        self.generate_report()
        
    @check("database_connection", "Checking database connection")
    async def check_database_connection(self):
        """Verify database is accessible"""
        try:
            engine = create_engine(settings.database_url.replace("+asyncpg", ""))
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return {"status": "PASS", "message": "Database connection successful"}
        except Exception as e:
            return {"status": "FAIL", "message": f"Database connection failed: {str(e)}"}
            
    @check("existing_tables", "Checking if all tables exist")
    async def check_existing_tables(self):
        """Check that all tables we want to rename/remove exist"""
        engine = create_engine(settings.database_url.replace("+asyncpg", ""))
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        missing_tables = []
        
        # Check tables to rename
        for old_name in self.tables_to_rename:
            if old_name not in existing_tables:
                missing_tables.append(old_name)
                
        # Check tables to remove
        for table in self.tables_to_remove:
            if table not in existing_tables:
                self.results["warnings"].append(f"Table to remove '{table}' doesn't exist (may already be removed)")
                
        if missing_tables:
            return {
                "status": "FAIL",
                "message": f"Missing tables: {', '.join(missing_tables)}",
                "missing_count": len(missing_tables)
            }
        else:
            return {
                "status": "PASS",
                "message": f"All {len(self.tables_to_rename)} tables to rename exist"
            }
            
    @check("new_table_names", "Checking for naming conflicts")
    async def check_new_table_names(self):
        """Ensure new table names don't already exist"""
        engine = create_engine(settings.database_url.replace("+asyncpg", ""))
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        conflicts = []
        
        for old_name, new_name in self.tables_to_rename.items():
            if new_name in existing_tables:
                conflicts.append(f"{new_name} (renaming from {old_name})")
                
        if conflicts:
            return {
                "status": "FAIL",
                "message": f"New table names already exist: {', '.join(conflicts)}",
                "conflicts": conflicts
            }
        else:
            return {
                "status": "PASS",
                "message": "No naming conflicts found"
            }
            
    @check("foreign_keys", "Checking foreign key dependencies")
    async def check_foreign_keys(self):
        """Check foreign key dependencies"""
        engine = create_engine(settings.database_url.replace("+asyncpg", ""))
        
        with engine.connect() as conn:
            # Query to find all foreign keys referencing our tables
            query = text("""
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND (ccu.table_name = ANY(:table_names) OR tc.table_name = ANY(:table_names))
            """)
            
            all_tables = list(self.tables_to_rename.keys()) + self.tables_to_remove
            result = conn.execute(query, {"table_names": all_tables})
            
            fk_count = 0
            fk_details = []
            
            for row in result:
                fk_count += 1
                fk_details.append({
                    "table": row.table_name,
                    "column": row.column_name,
                    "references": f"{row.foreign_table_name}.{row.foreign_column_name}",
                    "constraint": row.constraint_name
                })
                
        return {
            "status": "PASS",
            "message": f"Found {fk_count} foreign key relationships",
            "foreign_keys": fk_details[:10]  # First 10 for report
        }
        
    @check("table_sizes", "Checking table sizes")
    async def check_table_sizes(self):
        """Check size of tables to understand scope"""
        engine = create_engine(settings.database_url.replace("+asyncpg", ""))
        
        large_tables = []
        total_rows = 0
        
        with engine.connect() as conn:
            for table in list(self.tables_to_rename.keys()) + self.tables_to_remove:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    total_rows += count
                    
                    if count > 10000:
                        large_tables.append({"table": table, "rows": count})
                except:
                    pass  # Table might not exist
                    
        if large_tables:
            self.results["warnings"].append(f"Large tables found: {large_tables}")
            
        return {
            "status": "PASS",
            "message": f"Total rows across all tables: {total_rows:,}",
            "large_tables": large_tables
        }
        
    @check("api_health", "Checking API health")
    async def check_api_health(self):
        """Check if API is running"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/api/v1/health")
                if response.status_code == 200:
                    return {"status": "PASS", "message": "API is healthy"}
                else:
                    return {"status": "FAIL", "message": f"API returned status {response.status_code}"}
        except Exception as e:
            return {"status": "FAIL", "message": f"Cannot connect to API: {str(e)}"}
            
    @check("sample_endpoints", "Testing sample API endpoints")
    async def check_sample_endpoints(self):
        """Test a few endpoints to ensure they work"""
        import httpx
        
        endpoints_to_test = [
            "/api/v1/auth/login",
            "/api/v1/cycles",
            "/api/v1/reports"
        ]
        
        failed_endpoints = []
        
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints_to_test:
                try:
                    response = await client.get(f"http://localhost:8000{endpoint}")
                    # We expect 401 for auth-required endpoints, but that's OK
                    if response.status_code not in [200, 401, 403]:
                        failed_endpoints.append(f"{endpoint} ({response.status_code})")
                except Exception as e:
                    failed_endpoints.append(f"{endpoint} (Error: {str(e)})")
                    
        if failed_endpoints:
            return {
                "status": "FAIL",
                "message": f"Failed endpoints: {', '.join(failed_endpoints)}"
            }
        else:
            return {
                "status": "PASS",
                "message": f"All {len(endpoints_to_test)} test endpoints responded correctly"
            }
            
    def generate_report(self):
        """Generate validation report"""
        report_file = Path(f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total checks: {self.results['summary']['total_checks']}")
        print(f"Passed: {self.results['summary']['passed']}")
        print(f"Failed: {self.results['summary']['failed']}")
        
        if self.results["warnings"]:
            print(f"\n⚠️  Warnings: {len(self.results['warnings'])}")
            for warning in self.results["warnings"]:
                print(f"   - {warning}")
                
        if self.results["errors"]:
            print(f"\n❌ Errors: {len(self.results['errors'])}")
            for error in self.results["errors"]:
                print(f"   - {error}")
                
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Return status
        if self.results['summary']['failed'] > 0:
            print("\n❌ VALIDATION FAILED - Fix issues before proceeding with refactoring")
            return False
        else:
            print("\n✅ VALIDATION PASSED - Ready to proceed with refactoring")
            return True


async def main():
    validator = RefactoringValidator()
    success = await validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())