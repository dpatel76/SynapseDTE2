#!/usr/bin/env python3
"""
Database Introspection Script

This script captures the current state of the database schema and data
to help create an accurate foundational seed data migration.

SAFETY: This script is READ-ONLY and does not modify the database.
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.engine import Engine
from app.core.config import settings


class DatabaseIntrospector:
    """Introspect current database schema and data"""
    
    def __init__(self, database_url: str):
        # Convert asyncpg URL to sync URL for introspection
        sync_url = database_url.replace('+asyncpg', '')
        self.engine = create_engine(sync_url)
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        
    def get_schema_info(self) -> Dict[str, Any]:
        """Get comprehensive schema information"""
        
        print("🔍 Introspecting database schema...")
        
        tables = self.inspector.get_table_names()
        schema_info = {
            'timestamp': datetime.now().isoformat(),
            'total_tables': len(tables),
            'tables': {},
            'enums': {},
            'sequences': []
        }
        
        # Get detailed table information
        for table_name in sorted(tables):
            print(f"  📋 Analyzing table: {table_name}")
            schema_info['tables'][table_name] = self._get_table_details(table_name)
        
        # Get enums (PostgreSQL specific)
        try:
            with self.engine.connect() as conn:
                enum_query = text("""
                    SELECT t.typname, e.enumlabel 
                    FROM pg_type t 
                    JOIN pg_enum e ON t.oid = e.enumtypid 
                    ORDER BY t.typname, e.enumsortorder
                """)
                result = conn.execute(enum_query)
                
                current_enum = None
                for row in result:
                    enum_name = row[0]
                    enum_value = row[1]
                    
                    if enum_name not in schema_info['enums']:
                        schema_info['enums'][enum_name] = []
                    schema_info['enums'][enum_name].append(enum_value)
                    
        except Exception as e:
            print(f"  ⚠️ Could not retrieve enums: {e}")
            
        return schema_info
    
    def _get_table_details(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table"""
        
        table_info = {
            'columns': {},
            'primary_keys': [],
            'foreign_keys': [],
            'indexes': [],
            'constraints': [],
            'row_count': 0,
            'sample_data': [],
            'data_types_summary': {}
        }
        
        # Get columns
        columns = self.inspector.get_columns(table_name)
        for col in columns:
            table_info['columns'][col['name']] = {
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': str(col.get('default')) if col.get('default') is not None else None,
                'primary_key': col.get('primary_key', False)
            }
            
            if col.get('primary_key', False):
                table_info['primary_keys'].append(col['name'])
        
        # Get foreign keys
        for fk in self.inspector.get_foreign_keys(table_name):
            table_info['foreign_keys'].append({
                'name': fk.get('name'),
                'constrained_columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns']
            })
        
        # Get indexes
        for idx in self.inspector.get_indexes(table_name):
            table_info['indexes'].append({
                'name': idx['name'],
                'columns': idx['column_names'],
                'unique': idx.get('unique', False)
            })
        
        # Get row count and sample data
        try:
            with self.engine.connect() as conn:
                # Row count
                count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                table_info['row_count'] = count_result.scalar()
                
                # Sample data (first 3 rows if any data exists)
                if table_info['row_count'] > 0:
                    sample_result = conn.execute(text(f'SELECT * FROM "{table_name}" LIMIT 3'))
                    columns_list = list(sample_result.keys())
                    
                    for row in sample_result.fetchall():
                        row_dict = {}
                        for i, col_name in enumerate(columns_list):
                            value = row[i]
                            # Convert to JSON-serializable format
                            if value is not None:
                                if hasattr(value, 'isoformat'):  # datetime objects
                                    value = value.isoformat()
                                elif not isinstance(value, (str, int, float, bool)):
                                    value = str(value)
                            row_dict[col_name] = value
                        table_info['sample_data'].append(row_dict)
                
        except Exception as e:
            table_info['error'] = str(e)
            
        return table_info
    
    def get_foundational_data_analysis(self) -> Dict[str, Any]:
        """Analyze foundational data that should be included in seed migration"""
        
        print("🌱 Analyzing foundational data...")
        
        foundational_tables = [
            'users', 'roles', 'permissions', 'role_permissions', 'user_roles',
            'lobs', 'sla_configurations', 'regulatory_data_dictionary',
            'alembic_version'
        ]
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'foundational_tables': {},
            'recommendations': [],
            'data_summary': {}
        }
        
        for table_name in foundational_tables:
            print(f"  📊 Analyzing foundational table: {table_name}")
            
            if table_name in self.inspector.get_table_names():
                table_details = self._get_table_details(table_name)
                analysis['foundational_tables'][table_name] = table_details
                
                # Generate recommendations based on data
                if table_details['row_count'] > 0:
                    analysis['recommendations'].append(
                        f"✅ Table '{table_name}' has {table_details['row_count']} rows - include in seed migration"
                    )
                else:
                    analysis['recommendations'].append(
                        f"⚠️ Table '{table_name}' is empty - may need seed data"
                    )
            else:
                analysis['recommendations'].append(
                    f"❌ Table '{table_name}' does not exist - may need to be created"
                )
        
        return analysis
    
    def generate_migration_template(self, analysis: Dict[str, Any]) -> str:
        """Generate a template for the foundational seed data migration"""
        
        print("📝 Generating migration template...")
        
        template = '''"""
Enhanced Foundational Seed Data Migration for SynapseDTE
Generated: {timestamp}

This migration creates foundational data based on current database analysis:
- Database introspection performed on {table_count} tables
- Foundational data analyzed for {foundational_count} critical tables
- Migration template generated with actual data structures

SAFETY: Review all data before applying this migration
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime


def upgrade() -> None:
    """Create foundational seed data based on current database analysis"""
    
    print("🌱 Seeding foundational data for SynapseDTE (Enhanced Version)...")
    
    # TODO: Add enum definitions based on schema analysis
    {enum_definitions}
    
    # TODO: Add table definitions based on schema analysis
    {table_definitions}
    
    # TODO: Add data insertion based on current database content
    {data_insertions}
    
    print("✅ Enhanced foundational seed data migration completed!")


def downgrade() -> None:
    """Remove foundational seed data"""
    
    print("🧹 Removing foundational seed data...")
    
    # TODO: Add cleanup statements in reverse order
    {cleanup_statements}
    
    print("✅ Enhanced foundational seed data removed")
'''.format(
            timestamp=analysis['timestamp'],
            table_count=len(analysis.get('foundational_tables', {})),
            foundational_count=len([t for t in analysis.get('foundational_tables', {}).values() if t['row_count'] > 0]),
            enum_definitions="# Enum definitions will be added here",
            table_definitions="# Table definitions will be added here", 
            data_insertions="# Data insertions will be added here",
            cleanup_statements="# Cleanup statements will be added here"
        )
        
        return template


async def run_introspection():
    """Run the database introspection"""
    
    print("🏛️  DATABASE INTROSPECTION REPORT")
    print("=" * 60)
    print("Analyzing current database structure and data")
    print("This is a READ-ONLY analysis - no data will be modified")
    print("=" * 60)
    
    try:
        # Initialize introspector
        introspector = DatabaseIntrospector(settings.database_url)
        
        # Get schema information
        schema_info = introspector.get_schema_info()
        
        # Get foundational data analysis
        foundational_analysis = introspector.get_foundational_data_analysis()
        
        # Generate migration template
        migration_template = introspector.generate_migration_template(foundational_analysis)
        
        # Save results
        results_dir = Path("test/introspection_results")
        results_dir.mkdir(exist_ok=True)
        
        # Save schema info
        schema_file = results_dir / "schema_analysis.json"
        with open(schema_file, 'w') as f:
            json.dump(schema_info, f, indent=2, default=str)
        
        # Save foundational analysis
        foundational_file = results_dir / "foundational_analysis.json" 
        with open(foundational_file, 'w') as f:
            json.dump(foundational_analysis, f, indent=2, default=str)
        
        # Save migration template
        template_file = results_dir / "migration_template.py"
        with open(template_file, 'w') as f:
            f.write(migration_template)
        
        # Display summary
        print("\n📊 SCHEMA SUMMARY")
        print("-" * 30)
        print(f"Total tables: {schema_info['total_tables']}")
        print(f"Total enums: {len(schema_info['enums'])}")
        
        print("\n🌱 FOUNDATIONAL DATA SUMMARY")
        print("-" * 35)
        
        for table_name, table_info in foundational_analysis['foundational_tables'].items():
            status = "✅" if table_info['row_count'] > 0 else "⚠️"
            print(f"{status} {table_name:25} | {table_info['row_count']:4d} rows")
        
        print("\n💡 RECOMMENDATIONS")
        print("-" * 25)
        for rec in foundational_analysis['recommendations']:
            print(f"  {rec}")
        
        print(f"\n📄 Results saved to: {results_dir}")
        print(f"  📋 Schema analysis: {schema_file}")
        print(f"  🌱 Foundational analysis: {foundational_file}")
        print(f"  📝 Migration template: {template_file}")
        
        return {
            'schema_info': schema_info,
            'foundational_analysis': foundational_analysis,
            'migration_template': migration_template
        }
        
    except Exception as e:
        print(f"❌ Error during introspection: {e}")
        raise


def main():
    """Main function for command-line usage"""
    
    asyncio.run(run_introspection())


if __name__ == "__main__":
    main()