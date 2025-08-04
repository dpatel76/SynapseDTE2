#!/usr/bin/env python3
"""
Fresh Test Database Creation Script

This script creates a fresh test database and applies the foundational seed data migration
to validate the migration against the current production database.

SAFETY: This script creates a NEW test database and does not modify the existing system.
"""

import asyncio
import sys
import subprocess
import json
import os
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


class FreshTestDatabaseManager:
    """Manage fresh test database creation and migration testing"""
    
    def __init__(self):
        self.production_url = settings.database_url.replace('+asyncpg', '')
        self.test_db_name = f"synapse_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_db_url = self._build_test_db_url()
        
    def _build_test_db_url(self) -> str:
        """Build test database URL"""
        # Parse production URL to extract components
        import urllib.parse
        parsed = urllib.parse.urlparse(self.production_url)
        
        # Build test database URL with new database name
        test_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{self.test_db_name}"
        return test_url
    
    def create_test_database(self) -> bool:
        """Create a fresh test database"""
        
        print(f"🏗️  Creating fresh test database: {self.test_db_name}")
        
        try:
            # Connect to default database to create new test database
            parsed = urllib.parse.urlparse(self.production_url)
            admin_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
            
            admin_engine = create_engine(admin_url)
            
            with admin_engine.connect() as conn:
                # Enable autocommit for database creation
                conn.execute(text("COMMIT"))
                
                # Drop database if it exists (cleanup from previous runs)
                conn.execute(text(f'DROP DATABASE IF EXISTS "{self.test_db_name}"'))
                
                # Create new database
                conn.execute(text(f'CREATE DATABASE "{self.test_db_name}"'))
                
            print(f"    ✅ Created database: {self.test_db_name}")
            return True
            
        except Exception as e:
            print(f"    ❌ Error creating database: {e}")
            return False
    
    def run_alembic_migrations(self) -> bool:
        """Run alembic migrations on test database"""
        
        print("🚀 Running alembic migrations on test database...")
        
        try:
            # Set environment for test database
            env = {
                **os.environ,
                'DATABASE_URL': self.test_db_url
            }
            
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
            print(f"    ❌ Error running migrations: {e}")
            return False
    
    def apply_seed_data_migration(self) -> bool:
        """Apply the comprehensive seed data migration"""
        
        print("🌱 Applying comprehensive seed data migration...")
        
        try:
            # Import and run our seed data migration
            from test.comprehensive_seed_data_migration import upgrade
            
            # Temporarily set database URL for the migration
            original_url = settings.database_url
            settings.database_url = self.test_db_url
            
            try:
                upgrade()
                print("    ✅ Seed data migration applied successfully")
                return True
            finally:
                # Restore original database URL
                settings.database_url = original_url
                
        except Exception as e:
            print(f"    ❌ Error applying seed data migration: {e}")
            return False
    
    def compare_with_production(self) -> Dict[str, Any]:
        """Compare test database with production database"""
        
        print("📊 Comparing test database with production...")
        
        # Use the existing database reconciliation report
        from test.database_reconciliation_report import DatabaseComparator
        
        try:
            comparator = DatabaseComparator(self.production_url, self.test_db_url)
            report = comparator.compare_tables()
            recommendations = comparator.generate_reconciliation_recommendations(report)
            
            comparison_result = {
                'timestamp': datetime.now().isoformat(),
                'test_database': self.test_db_name,
                'production_vs_test': report,
                'recommendations': recommendations,
                'success': True
            }
            
            return comparison_result
            
        except Exception as e:
            print(f"    ❌ Error during comparison: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'test_database': self.test_db_name,
                'error': str(e),
                'success': False
            }
    
    def generate_reconciliation_stats(self, comparison_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed reconciliation statistics"""
        
        print("📈 Generating reconciliation statistics...")
        
        if not comparison_result['success']:
            return {
                'error': 'Comparison failed',
                'details': comparison_result.get('error', 'Unknown error')
            }
        
        report = comparison_result['production_vs_test']
        
        # Calculate statistics
        foundational_tables = [
            'users', 'roles', 'permissions', 'role_permissions', 'user_roles',
            'lobs', 'sla_configurations', 'regulatory_data_dictionary'
        ]
        
        stats = {
            'overall': {
                'total_tables_production': report['summary']['production_table_count'],
                'total_tables_test': report['summary']['test_table_count'],
                'schema_match_score': 0,
                'data_completeness_score': 0
            },
            'foundational_tables': {},
            'data_continuity': {},
            'recommendations_summary': {
                'critical_issues': 0,
                'warnings': 0,
                'successes': 0
            }
        }
        
        # Analyze foundational tables
        for table in foundational_tables:
            if table in report['detailed_comparison']:
                comparison = report['detailed_comparison'][table]
                
                stats['foundational_tables'][table] = {
                    'exists_in_both': comparison['differences']['exists_in_both'],
                    'schema_match': comparison['differences']['schema_match'],
                    'production_rows': comparison['production']['row_count'],
                    'test_rows': comparison['test']['row_count'],
                    'data_match': comparison['production']['row_count'] == comparison['test']['row_count']
                }
        
        # Calculate scores
        foundational_existing = sum(1 for t in stats['foundational_tables'].values() if t['exists_in_both'])
        foundational_schema_match = sum(1 for t in stats['foundational_tables'].values() if t['schema_match'])
        foundational_data_match = sum(1 for t in stats['foundational_tables'].values() if t['data_match'])
        
        if foundational_tables:
            stats['overall']['schema_match_score'] = (foundational_schema_match / len(foundational_tables)) * 100
            stats['overall']['data_completeness_score'] = (foundational_data_match / len(foundational_tables)) * 100
        
        # Analyze recommendations
        recommendations = comparison_result['recommendations']
        for rec in recommendations:
            if '❌' in rec or 'Critical' in rec:
                stats['recommendations_summary']['critical_issues'] += 1
            elif '⚠️' in rec:
                stats['recommendations_summary']['warnings'] += 1
            elif '✅' in rec:
                stats['recommendations_summary']['successes'] += 1
        
        return stats
    
    def cleanup_test_database(self) -> bool:
        """Clean up the test database"""
        
        print(f"🧹 Cleaning up test database: {self.test_db_name}")
        
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(self.production_url)
            admin_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
            
            admin_engine = create_engine(admin_url)
            
            with admin_engine.connect() as conn:
                conn.execute(text("COMMIT"))
                conn.execute(text(f'DROP DATABASE IF EXISTS "{self.test_db_name}"'))
                
            print(f"    ✅ Cleaned up database: {self.test_db_name}")
            return True
            
        except Exception as e:
            print(f"    ⚠️ Error during cleanup (may be ok): {e}")
            return False


async def run_full_migration_test():
    """Run the complete fresh database migration test"""
    
    print("🏛️  FRESH DATABASE MIGRATION TEST")
    print("=" * 60)
    print("Creating fresh test database and validating seed data migration")
    print("This test will NOT modify the existing production database")
    print("=" * 60)
    
    test_manager = FreshTestDatabaseManager()
    
    try:
        # Step 1: Create test database
        if not test_manager.create_test_database():
            print("❌ Failed to create test database")
            return
        
        # Step 2: Run alembic migrations
        if not test_manager.run_alembic_migrations():
            print("❌ Failed to run alembic migrations")
            return
        
        # Step 3: Apply seed data migration
        if not test_manager.apply_seed_data_migration():
            print("❌ Failed to apply seed data migration")
            return
        
        # Step 4: Compare with production
        comparison_result = test_manager.compare_with_production()
        
        # Step 5: Generate reconciliation stats
        stats = test_manager.generate_reconciliation_stats(comparison_result)
        
        # Step 6: Save results
        results_dir = Path("test/migration_test_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed comparison
        comparison_file = results_dir / f"comparison_{timestamp}.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison_result, f, indent=2, default=str)
        
        # Save reconciliation stats
        stats_file = results_dir / f"reconciliation_stats_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        # Display results
        print("\n📊 MIGRATION TEST RESULTS")
        print("=" * 40)
        print(f"Test Database: {test_manager.test_db_name}")
        print(f"Schema Match Score: {stats['overall']['schema_match_score']:.1f}%")
        print(f"Data Completeness Score: {stats['overall']['data_completeness_score']:.1f}%")
        
        print("\n🌱 FOUNDATIONAL TABLES STATUS")
        print("-" * 35)
        for table, info in stats['foundational_tables'].items():
            schema_status = "✅" if info['schema_match'] else "❌"
            data_status = "✅" if info['data_match'] else "⚠️"
            print(f"{schema_status}{data_status} {table:25} | P:{info['production_rows']:3d} T:{info['test_rows']:3d}")
        
        print("\n📋 RECOMMENDATIONS SUMMARY")
        print("-" * 30)
        print(f"✅ Successes: {stats['recommendations_summary']['successes']}")
        print(f"⚠️ Warnings: {stats['recommendations_summary']['warnings']}")
        print(f"❌ Critical Issues: {stats['recommendations_summary']['critical_issues']}")
        
        print(f"\n💾 RESULTS SAVED")
        print("-" * 20)
        print(f"📄 Detailed comparison: {comparison_file}")
        print(f"📊 Reconciliation stats: {stats_file}")
        
        # Overall assessment
        if stats['recommendations_summary']['critical_issues'] == 0:
            print("\n🎉 ASSESSMENT: Migration test PASSED!")
            print("   The seed data migration successfully replicates foundational data")
        else:
            print(f"\n⚠️ ASSESSMENT: Migration test has {stats['recommendations_summary']['critical_issues']} critical issues")
            print("   Review the detailed comparison for specific problems")
        
    finally:
        # Step 7: Cleanup (optional - comment out to keep for inspection)
        cleanup_choice = input("\n🧹 Cleanup test database? (y/N): ").lower()
        if cleanup_choice == 'y':
            test_manager.cleanup_test_database()
        else:
            print(f"💾 Test database preserved: {test_manager.test_db_name}")
            print(f"    URL: {test_manager.test_db_url}")


def main():
    """Main function for command-line usage"""
    
    import os
    
    asyncio.run(run_full_migration_test())


if __name__ == "__main__":
    main()