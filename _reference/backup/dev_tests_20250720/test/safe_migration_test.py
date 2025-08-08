#!/usr/bin/env python3
"""
Safe Migration Test Script

This script safely tests the migration by:
1. Creating a completely separate test database 
2. Using the actual alembic migrations to create the proper schema
3. Testing the seed data migration
4. Comparing results WITHOUT touching the production database

SAFETY: Uses separate test database - NEVER touches production database
"""

import asyncio
import sys
import json
import os
import subprocess
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


class SafeMigrationTester:
    """Safely test migrations in isolated environment"""
    
    def __init__(self):
        self.production_url = settings.database_url.replace('+asyncpg', '')
        self.test_db_name = f"synapse_safe_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_db_url = self._build_test_db_url()
        
    def _build_test_db_url(self) -> str:
        """Build test database URL"""
        parsed = urllib.parse.urlparse(self.production_url)
        return f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{self.test_db_name}"
    
    def create_test_database(self) -> bool:
        """Create a fresh test database"""
        
        print(f"🏗️  Creating safe test database: {self.test_db_name}")
        print(f"    Production DB: {self.production_url.split('/')[-1]}")
        print(f"    Test DB: {self.test_db_name}")
        print(f"    ✅ These are COMPLETELY SEPARATE databases")
        
        try:
            parsed = urllib.parse.urlparse(self.production_url)
            admin_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
            
            admin_engine = create_engine(admin_url)
            
            with admin_engine.connect() as conn:
                conn.execute(text("COMMIT"))
                conn.execute(text(f'DROP DATABASE IF EXISTS "{self.test_db_name}"'))
                conn.execute(text(f'CREATE DATABASE "{self.test_db_name}"'))
                
            print(f"    ✅ Created test database: {self.test_db_name}")
            return True
            
        except Exception as e:
            print(f"    ❌ Error creating test database: {e}")
            return False
    
    def run_alembic_migrations(self) -> bool:
        """Run actual alembic migrations on test database"""
        
        print("🚀 Running alembic migrations on test database...")
        print("    This creates the proper schema using existing migrations")
        
        try:
            # Set environment for test database
            env = os.environ.copy()
            env['DATABASE_URL'] = self.test_db_url
            
            # Run alembic upgrade
            result = subprocess.run(
                ['alembic', 'upgrade', 'head'],
                env=env,
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent)
            )
            
            if result.returncode == 0:
                print("    ✅ Alembic migrations completed successfully")
                return True
            else:
                print(f"    ❌ Alembic migrations failed:")
                print(f"    STDOUT: {result.stdout}")
                print(f"    STDERR: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"    ❌ Error running alembic: {e}")
            return False
    
    def test_seed_data_compatibility(self) -> Dict[str, Any]:
        """Test if our extracted seed data is compatible with the schema"""
        
        print("🧪 Testing seed data compatibility...")
        
        # Load extracted seed data
        try:
            with open('test/extracted_seed_data.json', 'r') as f:
                seed_data = json.load(f)
        except FileNotFoundError:
            return {'error': 'extracted_seed_data.json not found'}
        
        test_engine = create_engine(self.test_db_url)
        compatibility_report = {
            'timestamp': datetime.now().isoformat(),
            'tables_tested': {},
            'overall_status': 'unknown'
        }
        
        table_order = ['lobs', 'roles', 'permissions', 'role_permissions', 'users', 'user_roles', 'regulatory_data_dictionary', 'sla_configurations']
        
        successful_inserts = 0
        total_tables = 0
        
        for table_name in table_order:
            if table_name in seed_data['tables'] and seed_data['tables'][table_name]:
                total_tables += 1
                print(f"    🔍 Testing {table_name} ({len(seed_data['tables'][table_name])} rows)")
                
                try:
                    with test_engine.connect() as conn:
                        # Test insert with first row only
                        test_row = seed_data['tables'][table_name][0]
                        
                        # Build insert statement
                        columns = ', '.join([f'"{k}"' for k in test_row.keys()])
                        placeholders = ', '.join([f":{k}" for k in test_row.keys()])
                        insert_sql = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
                        
                        conn.execute(text(insert_sql), test_row)
                        conn.commit()
                        
                        # If successful, insert remaining rows
                        for row in seed_data['tables'][table_name][1:]:
                            conn.execute(text(insert_sql), row)
                        conn.commit()
                        
                        # Verify count
                        count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                        inserted_count = count_result.scalar()
                        
                        compatibility_report['tables_tested'][table_name] = {
                            'status': 'success',
                            'expected_rows': len(seed_data['tables'][table_name]),
                            'inserted_rows': inserted_count,
                            'match': inserted_count == len(seed_data['tables'][table_name])
                        }
                        
                        successful_inserts += 1
                        print(f"        ✅ Inserted {inserted_count} rows successfully")
                        
                except Exception as e:
                    compatibility_report['tables_tested'][table_name] = {
                        'status': 'failed',
                        'error': str(e),
                        'expected_rows': len(seed_data['tables'][table_name]),
                        'inserted_rows': 0
                    }
                    print(f"        ❌ Failed: {e}")
        
        # Calculate overall status
        if successful_inserts == total_tables:
            compatibility_report['overall_status'] = 'perfect'
        elif successful_inserts > total_tables * 0.8:
            compatibility_report['overall_status'] = 'good'
        else:
            compatibility_report['overall_status'] = 'needs_work'
        
        compatibility_report['summary'] = {
            'successful_tables': successful_inserts,
            'total_tables': total_tables,
            'success_rate': (successful_inserts / total_tables) * 100 if total_tables > 0 else 0
        }
        
        return compatibility_report
    
    def compare_with_production(self) -> Dict[str, Any]:
        """Compare test database with production database"""
        
        print("📊 Comparing test database with production...")
        
        prod_engine = create_engine(self.production_url)
        test_engine = create_engine(self.test_db_url)
        
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'foundational_tables': {},
            'summary': {}
        }
        
        foundational_tables = ['lobs', 'roles', 'permissions', 'role_permissions', 'users', 'user_roles', 'regulatory_data_dictionary', 'sla_configurations']
        
        total_prod_rows = 0
        total_test_rows = 0
        perfect_matches = 0
        
        for table in foundational_tables:
            print(f"    🔍 Comparing {table}...")
            
            try:
                # Get production count
                with prod_engine.connect() as conn:
                    prod_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
                
                # Get test count
                with test_engine.connect() as conn:
                    test_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
                
                is_perfect_match = prod_count == test_count
                if is_perfect_match:
                    perfect_matches += 1
                
                comparison['foundational_tables'][table] = {
                    'production_rows': prod_count,
                    'test_rows': test_count,
                    'perfect_match': is_perfect_match,
                    'difference': abs(prod_count - test_count),
                    'completeness_percentage': (test_count / prod_count * 100) if prod_count > 0 else 100
                }
                
                total_prod_rows += prod_count
                total_test_rows += test_count
                
                status = "✅" if is_perfect_match else "⚠️"
                print(f"        {status} Prod: {prod_count}, Test: {test_count}")
                
            except Exception as e:
                comparison['foundational_tables'][table] = {
                    'error': str(e),
                    'production_rows': 0,
                    'test_rows': 0,
                    'perfect_match': False
                }
                print(f"        ❌ Error: {e}")
        
        comparison['summary'] = {
            'total_production_rows': total_prod_rows,
            'total_test_rows': total_test_rows,
            'perfect_matches': perfect_matches,
            'total_tables': len(foundational_tables),
            'perfect_match_percentage': (perfect_matches / len(foundational_tables)) * 100,
            'overall_completeness': (total_test_rows / total_prod_rows * 100) if total_prod_rows > 0 else 0
        }
        
        return comparison
    
    def cleanup_test_database(self, auto_cleanup: bool = False) -> bool:
        """Clean up the test database"""
        
        if not auto_cleanup:
            try:
                cleanup_choice = input(f"\n🧹 Cleanup test database '{self.test_db_name}'? (y/N): ").lower()
                if cleanup_choice != 'y':
                    print(f"💾 Test database preserved: {self.test_db_name}")
                    print(f"    Connection URL: {self.test_db_url}")
                    return False
            except EOFError:
                # Running in non-interactive mode, default to cleanup
                auto_cleanup = True
        
        print(f"🧹 Cleaning up test database: {self.test_db_name}")
        
        try:
            parsed = urllib.parse.urlparse(self.production_url)
            admin_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
            
            admin_engine = create_engine(admin_url)
            
            with admin_engine.connect() as conn:
                conn.execute(text("COMMIT"))
                conn.execute(text(f'DROP DATABASE IF EXISTS "{self.test_db_name}"'))
                
            print(f"    ✅ Cleaned up test database: {self.test_db_name}")
            return True
            
        except Exception as e:
            print(f"    ⚠️ Error during cleanup: {e}")
            return False


async def run_safe_migration_test():
    """Run the safe migration test"""
    
    print("🛡️  SAFE MIGRATION TEST")
    print("=" * 60)
    print("Testing seed data migration in completely isolated environment")
    print("🔒 SAFETY GUARANTEE: Production database is NEVER modified")
    print("=" * 60)
    
    tester = SafeMigrationTester()
    
    try:
        # Step 1: Create test database
        if not tester.create_test_database():
            print("❌ Failed to create test database - aborting")
            return
        
        # Step 2: Run alembic migrations
        if not tester.run_alembic_migrations():
            print("❌ Failed to run alembic migrations - aborting")
            return
        
        # Step 3: Test seed data compatibility
        compatibility_report = tester.test_seed_data_compatibility()
        
        # Step 4: Compare with production
        comparison_report = tester.compare_with_production()
        
        # Save results
        results_dir = Path("test/safe_migration_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save compatibility report
        compatibility_file = results_dir / f"compatibility_report_{timestamp}.json"
        with open(compatibility_file, 'w') as f:
            json.dump(compatibility_report, f, indent=2, default=str)
        
        # Save comparison report
        comparison_file = results_dir / f"comparison_report_{timestamp}.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison_report, f, indent=2, default=str)
        
        # Display results
        print("\n🎯 SAFE MIGRATION TEST RESULTS")
        print("=" * 50)
        
        # Compatibility results
        if 'error' in compatibility_report:
            print(f"❌ Compatibility test failed: {compatibility_report['error']}")
        else:
            success_rate = compatibility_report['summary']['success_rate']
            print(f"🧪 SEED DATA COMPATIBILITY: {success_rate:.1f}%")
            
            if success_rate >= 100:
                print("   ✅ Perfect compatibility - all tables inserted successfully")
            elif success_rate >= 80:
                print("   ⚠️ Good compatibility - minor issues")
            else:
                print("   ❌ Poor compatibility - significant issues")
        
        # Comparison results
        summary = comparison_report['summary']
        print(f"\n📊 PRODUCTION vs TEST COMPARISON")
        print("-" * 40)
        print(f"Perfect matches: {summary['perfect_matches']}/{summary['total_tables']} ({summary['perfect_match_percentage']:.1f}%)")
        print(f"Overall completeness: {summary['overall_completeness']:.1f}%")
        print(f"Total rows: {summary['total_production_rows']} → {summary['total_test_rows']}")
        
        print(f"\n🌱 FOUNDATIONAL TABLES BREAKDOWN")
        print("-" * 40)
        for table, stats in comparison_report['foundational_tables'].items():
            if 'error' in stats:
                print(f"❌ {table:25} | Error: {stats['error']}")
            else:
                status = "✅" if stats['perfect_match'] else "⚠️"
                print(f"{status} {table:25} | P:{stats['production_rows']:3d} T:{stats['test_rows']:3d} ({stats['completeness_percentage']:.0f}%)")
        
        print(f"\n💾 RESULTS SAVED")
        print("-" * 20)
        print(f"📄 Compatibility: {compatibility_file}")
        print(f"📊 Comparison: {comparison_file}")
        
        # Overall assessment
        overall_success = (
            compatibility_report.get('summary', {}).get('success_rate', 0) >= 95 and
            summary['perfect_match_percentage'] >= 90
        )
        
        if overall_success:
            print("\n🎉 OVERALL ASSESSMENT: MIGRATION READY!")
            print("   The seed data migration is production-ready")
            print("   ✅ Schema compatibility verified")
            print("   ✅ Data completeness verified") 
        else:
            print("\n⚠️ OVERALL ASSESSMENT: NEEDS REVIEW")
            print("   Check the detailed reports for specific issues")
        
        print(f"\n🔒 SAFETY CONFIRMATION")
        print("-" * 25)
        print(f"✅ Production database UNCHANGED")
        print(f"✅ Test performed in isolation: {tester.test_db_name}")
        
    finally:
        # Cleanup (auto-cleanup in non-interactive mode)
        tester.cleanup_test_database(auto_cleanup=True)


def main():
    """Main function for command-line usage"""
    
    asyncio.run(run_safe_migration_test())


if __name__ == "__main__":
    main()