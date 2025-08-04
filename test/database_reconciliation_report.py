#!/usr/bin/env python3
"""
Database Reconciliation Report

This script compares a test database (after migration) against the current
project database to ensure our foundational migration captures all essential data.

SAFETY: This script is READ-ONLY and does not modify any databases.
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from app.core.config import settings


class DatabaseComparator:
    """Compare two databases for schema and data differences"""
    
    def __init__(self, production_url: str, test_url: str):
        self.prod_engine = create_engine(production_url)
        self.test_engine = create_engine(test_url)
        self.prod_inspector = inspect(self.prod_engine)
        self.test_inspector = inspect(self.test_engine)
        
    def get_table_info(self, engine: Engine, table_name: str) -> Dict[str, Any]:
        """Get comprehensive table information"""
        inspector = inspect(engine)
        
        info = {
            'exists': table_name in inspector.get_table_names(),
            'columns': {},
            'indexes': [],
            'foreign_keys': [],
            'row_count': 0,
            'sample_data': []
        }
        
        if not info['exists']:
            return info
            
        # Get columns
        for col in inspector.get_columns(table_name):
            info['columns'][col['name']] = {
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': col.get('default'),
                'primary_key': col.get('primary_key', False)
            }
        
        # Get indexes
        info['indexes'] = [idx['name'] for idx in inspector.get_indexes(table_name)]
        
        # Get foreign keys
        for fk in inspector.get_foreign_keys(table_name):
            info['foreign_keys'].append({
                'columns': fk['constrained_columns'],
                'refers_to': f"{fk['referred_table']}.{fk['referred_columns']}"
            })
        
        # Get row count and sample data
        try:
            with engine.connect() as conn:
                # Row count
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                info['row_count'] = count_result.scalar()
                
                # Sample data (first 3 rows)
                if info['row_count'] > 0:
                    sample_result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
                    columns = list(sample_result.keys())
                    info['sample_data'] = [
                        dict(zip(columns, row)) for row in sample_result.fetchall()
                    ]
                    
        except Exception as e:
            info['error'] = str(e)
            
        return info
    
    def compare_tables(self) -> Dict[str, Any]:
        """Compare all tables between production and test databases"""
        
        print("🔍 Scanning production database...")
        prod_tables = set(self.prod_inspector.get_table_names())
        
        print("🔍 Scanning test database...")
        test_tables = set(self.test_inspector.get_table_names())
        
        print(f"📊 Production tables: {len(prod_tables)}")
        print(f"🧪 Test tables: {len(test_tables)}")
        
        # Find differences
        only_in_prod = prod_tables - test_tables
        only_in_test = test_tables - prod_tables
        common_tables = prod_tables & test_tables
        
        report = {
            'summary': {
                'production_table_count': len(prod_tables),
                'test_table_count': len(test_tables),
                'common_tables': len(common_tables),
                'only_in_production': len(only_in_prod),
                'only_in_test': len(only_in_test),
                'timestamp': datetime.now().isoformat()
            },
            'table_differences': {
                'only_in_production': sorted(list(only_in_prod)),
                'only_in_test': sorted(list(only_in_test)),
                'common_tables': sorted(list(common_tables))
            },
            'detailed_comparison': {}
        }
        
        # Detailed comparison for foundational tables
        foundational_tables = [
            'users', 'roles', 'permissions', 'role_permissions', 'user_roles',
            'lobs', 'reports', 'test_cycles', 'universal_sla_configurations',
            'alembic_version'
        ]
        
        print("\\n📋 Detailed comparison of foundational tables...")
        
        for table in foundational_tables:
            print(f"  Analyzing {table}...")
            
            prod_info = self.get_table_info(self.prod_engine, table)
            test_info = self.get_table_info(self.test_engine, table)
            
            comparison = {
                'production': prod_info,
                'test': test_info,
                'differences': {
                    'exists_in_both': prod_info['exists'] and test_info['exists'],
                    'schema_match': prod_info.get('columns') == test_info.get('columns'),
                    'row_count_difference': abs(prod_info['row_count'] - test_info['row_count'])
                }
            }
            
            # Column differences
            if prod_info['exists'] and test_info['exists']:
                prod_cols = set(prod_info['columns'].keys())
                test_cols = set(test_info['columns'].keys())
                
                comparison['differences']['missing_columns_in_test'] = sorted(list(prod_cols - test_cols))
                comparison['differences']['extra_columns_in_test'] = sorted(list(test_cols - prod_cols))
                comparison['differences']['common_columns'] = sorted(list(prod_cols & test_cols))
            
            report['detailed_comparison'][table] = comparison
        
        return report
    
    def generate_reconciliation_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparison results"""
        
        recommendations = []
        
        # Missing tables in test
        if report['table_differences']['only_in_production']:
            recommendations.append(
                f"⚠️  Test database is missing {len(report['table_differences']['only_in_production'])} tables that exist in production"
            )
            
        # Missing foundational data
        for table, comparison in report['detailed_comparison'].items():
            if not comparison['differences']['exists_in_both']:
                if comparison['production']['exists'] and not comparison['test']['exists']:
                    recommendations.append(f"❌ Critical: Table '{table}' missing in test database")
                    
            elif comparison['production']['row_count'] > 0 and comparison['test']['row_count'] == 0:
                recommendations.append(f"📭 Table '{table}' exists but has no data in test database")
                
            elif comparison['differences']['row_count_difference'] > 0:
                prod_count = comparison['production']['row_count']
                test_count = comparison['test']['row_count']
                recommendations.append(
                    f"📊 Table '{table}': Production has {prod_count} rows, test has {test_count} rows"
                )
                
            if comparison['differences']['missing_columns_in_test']:
                missing = comparison['differences']['missing_columns_in_test']
                recommendations.append(f"🔧 Table '{table}' missing columns in test: {missing}")
        
        # Success cases
        success_count = sum(1 for comp in report['detailed_comparison'].values() 
                          if comp['differences']['exists_in_both'] and 
                          comp['differences']['schema_match'])
        
        if success_count > 0:
            recommendations.append(f"✅ {success_count} foundational tables have matching schemas")
        
        return recommendations


async def run_reconciliation(test_db_url: Optional[str] = None):
    """Run the database reconciliation report"""
    
    print("🏛️  DATABASE RECONCILIATION REPORT")
    print("=" * 60)
    print("Comparing test database against production database")
    print("This is a READ-ONLY analysis - no data will be modified")
    print("=" * 60)
    
    # Database URLs
    production_url = settings.database_url.replace('+asyncpg', '')  # Remove async driver for sync comparison
    
    if not test_db_url:
        print("❌ Test database URL not provided")
        print("Please run the test database creation script first:")
        print("  python test/create_test_database.py")
        return
    
    try:
        # Create comparator
        comparator = DatabaseComparator(production_url, test_db_url)
        
        # Run comparison
        report = comparator.compare_tables()
        
        # Generate recommendations
        recommendations = comparator.generate_reconciliation_recommendations(report)
        
        # Display summary
        print("\\n📊 SUMMARY")
        print("-" * 30)
        print(f"Production tables: {report['summary']['production_table_count']}")
        print(f"Test tables: {report['summary']['test_table_count']}")
        print(f"Common tables: {report['summary']['common_tables']}")
        print(f"Only in production: {report['summary']['only_in_production']}")
        print(f"Only in test: {report['summary']['only_in_test']}")
        
        # Display foundational table details
        print("\\n🏗️  FOUNDATIONAL TABLES ANALYSIS")
        print("-" * 40)
        
        for table, comparison in report['detailed_comparison'].items():
            status = "✅" if comparison['differences']['exists_in_both'] else "❌"
            prod_rows = comparison['production']['row_count']
            test_rows = comparison['test']['row_count']
            
            print(f"{status} {table:20} | Prod: {prod_rows:4d} rows | Test: {test_rows:4d} rows")
            
            if comparison['differences']['missing_columns_in_test']:
                print(f"    ⚠️  Missing columns: {comparison['differences']['missing_columns_in_test']}")
        
        # Display recommendations
        print("\\n💡 RECOMMENDATIONS")
        print("-" * 25)
        for rec in recommendations:
            print(f"  {rec}")
        
        # Save detailed report
        report_file = Path("test/reconciliation_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\\n📄 Detailed report saved to: {report_file}")
        
        # Overall assessment
        critical_issues = sum(1 for rec in recommendations if "❌" in rec or "Critical" in rec)
        
        if critical_issues == 0:
            print("\\n🎉 ASSESSMENT: Migration appears to cover foundational requirements!")
        else:
            print(f"\\n⚠️  ASSESSMENT: {critical_issues} critical issues need attention")
        
        return report
        
    except Exception as e:
        print(f"❌ Error during reconciliation: {e}")
        raise


def main():
    """Main function for command-line usage"""
    
    if len(sys.argv) > 1:
        test_db_url = sys.argv[1]
        asyncio.run(run_reconciliation(test_db_url))
    else:
        print("Usage: python database_reconciliation_report.py <test_database_url>")
        print("\\nExample:")
        print("  python database_reconciliation_report.py postgresql://test_user:pass@localhost:5432/test_db")
        print("\\nOr first create a test database:")
        print("  python test/create_test_database.py")


if __name__ == "__main__":
    main()