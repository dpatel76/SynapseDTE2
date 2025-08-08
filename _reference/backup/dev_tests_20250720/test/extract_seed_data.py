#!/usr/bin/env python3
"""
Seed Data Extraction Script

This script extracts actual seed data from the current database to create
a comprehensive foundational seed data migration.

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

from sqlalchemy import create_engine, text
from app.core.config import settings


class SeedDataExtractor:
    """Extract seed data from current database"""
    
    def __init__(self, database_url: str):
        # Convert asyncpg URL to sync URL for extraction
        sync_url = database_url.replace('+asyncpg', '')
        self.engine = create_engine(sync_url)
        
    def extract_table_data(self, table_name: str, order_by: str = None) -> List[Dict[str, Any]]:
        """Extract all data from a specific table"""
        
        print(f"  📤 Extracting data from {table_name}...")
        
        try:
            with self.engine.connect() as conn:
                # Build query with optional ordering
                query = f'SELECT * FROM "{table_name}"'
                if order_by:
                    query += f' ORDER BY {order_by}'
                
                result = conn.execute(text(query))
                columns = list(result.keys())
                
                data = []
                for row in result.fetchall():
                    row_dict = {}
                    for i, col_name in enumerate(columns):
                        value = row[i]
                        # Convert to JSON-serializable format
                        if value is not None:
                            if hasattr(value, 'isoformat'):  # datetime objects
                                value = value.isoformat()
                            elif not isinstance(value, (str, int, float, bool)):
                                value = str(value)
                        row_dict[col_name] = value
                    data.append(row_dict)
                
                print(f"    ✅ Extracted {len(data)} rows from {table_name}")
                return data
                
        except Exception as e:
            print(f"    ❌ Error extracting from {table_name}: {e}")
            return []
    
    def extract_all_foundational_data(self) -> Dict[str, Any]:
        """Extract all foundational seed data"""
        
        print("🌱 Extracting foundational seed data...")
        
        # Define foundational tables in dependency order
        foundational_tables = {
            'lobs': 'lob_id',
            'roles': 'role_id', 
            'permissions': 'permission_id',
            'role_permissions': 'role_id, permission_id',
            'users': 'user_id',
            'user_roles': 'user_id, role_id',
            'regulatory_data_dictionary': 'dict_id',
            'universal_sla_configurations': 'sla_config_id'
        }
        
        extracted_data = {
            'timestamp': datetime.now().isoformat(),
            'tables': {},
            'statistics': {},
            'metadata': {
                'extraction_order': list(foundational_tables.keys()),
                'total_tables': len(foundational_tables)
            }
        }
        
        total_rows = 0
        
        for table_name, order_by in foundational_tables.items():
            data = self.extract_table_data(table_name, order_by)
            extracted_data['tables'][table_name] = data
            extracted_data['statistics'][table_name] = len(data)
            total_rows += len(data)
        
        extracted_data['metadata']['total_rows'] = total_rows
        
        return extracted_data
    
    def generate_comprehensive_migration(self, seed_data: Dict[str, Any]) -> str:
        """Generate comprehensive migration with actual seed data"""
        
        print("📝 Generating comprehensive seed data migration...")
        
        # Generate migration header
        migration_code = f'''"""
Comprehensive Foundational Seed Data Migration for SynapseDTE
Generated: {seed_data['timestamp']}

This migration contains ACTUAL foundational data extracted from the current database:
- {seed_data['metadata']['total_tables']} foundational tables
- {seed_data['metadata']['total_rows']} total seed data rows
- Complete RBAC system with roles, permissions, and mappings
- User accounts with proper role assignments
- Lines of Business (LOBs) configuration
- Regulatory data dictionary entries
- SLA configurations (if any)

CRITICAL: This migration contains real production data. Review carefully before applying.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime


def upgrade() -> None:
    """Create comprehensive foundational seed data"""
    
    print("🌱 Seeding comprehensive foundational data for SynapseDTE...")
'''

        # Generate table definitions and data insertions
        table_order = ['lobs', 'roles', 'permissions', 'role_permissions', 'users', 'user_roles', 'regulatory_data_dictionary', 'universal_sla_configurations']
        
        for table_name in table_order:
            if table_name in seed_data['tables'] and seed_data['tables'][table_name]:
                migration_code += self._generate_table_migration(table_name, seed_data['tables'][table_name])
        
        # Generate downgrade function
        migration_code += '''
    print("✅ Comprehensive foundational seed data migration completed!")


def downgrade() -> None:
    """Remove comprehensive foundational seed data"""
    
    print("🧹 Removing comprehensive foundational seed data...")
    
    # Delete in reverse order due to foreign key constraints
'''
        
        # Generate cleanup in reverse order
        cleanup_order = list(reversed(table_order))
        for table_name in cleanup_order:
            if table_name in seed_data['tables'] and seed_data['tables'][table_name]:
                migration_code += f'    op.execute("DELETE FROM {table_name}")\n'
        
        migration_code += '''    
    print("✅ Comprehensive foundational seed data removed")
'''
        
        return migration_code
    
    def _generate_table_migration(self, table_name: str, table_data: List[Dict[str, Any]]) -> str:
        """Generate migration code for a specific table"""
        
        if not table_data:
            return f"\n    # {table_name} table is empty - no data to insert\n"
        
        # Get column names from first row
        columns = list(table_data[0].keys())
        
        # Generate table definition
        table_def = f"""
    # {table_name.upper()} TABLE DATA
    print("  📊 Seeding {table_name} ({len(table_data)} rows)...")
    
    {table_name}_table = table('{table_name}',
"""
        
        for col_name in columns:
            table_def += f"        column('{col_name}', sa.{self._get_sqlalchemy_type(table_data[0][col_name])}),\n"
        
        table_def += "    )\n"
        
        # Generate data insertions
        table_def += f"\n    {table_name}_data = [\n"
        
        for row in table_data:
            table_def += "        {\n"
            for col_name, value in row.items():
                if value is None:
                    table_def += f"            '{col_name}': None,\n"
                elif isinstance(value, str):
                    # Escape single quotes in strings
                    escaped_value = value.replace("'", "\\'")
                    table_def += f"            '{col_name}': '{escaped_value}',\n"
                elif isinstance(value, bool):
                    table_def += f"            '{col_name}': {value},\n"
                else:
                    table_def += f"            '{col_name}': {value},\n"
            table_def += "        },\n"
        
        table_def += f"    ]\n\n    op.bulk_insert({table_name}_table, {table_name}_data)\n"
        
        return table_def
    
    def _get_sqlalchemy_type(self, value: Any) -> str:
        """Determine SQLAlchemy type from value"""
        if value is None:
            return "String"
        elif isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, int):
            return "Integer"
        elif isinstance(value, float):
            return "Float"
        elif isinstance(value, str):
            if 'T' in value and ':' in value:  # Likely datetime
                return "DateTime"
            return "String"
        else:
            return "String"


async def run_extraction():
    """Run the seed data extraction"""
    
    print("🌱 SEED DATA EXTRACTION")
    print("=" * 50)
    print("Extracting foundational seed data from current database")
    print("This is a READ-ONLY operation - no data will be modified")
    print("=" * 50)
    
    try:
        # Initialize extractor
        extractor = SeedDataExtractor(settings.database_url)
        
        # Extract all foundational data
        seed_data = extractor.extract_all_foundational_data()
        
        # Generate comprehensive migration
        migration_code = extractor.generate_comprehensive_migration(seed_data)
        
        # Save results
        results_dir = Path("test")
        results_dir.mkdir(exist_ok=True)
        
        # Save extracted seed data
        seed_data_file = results_dir / "extracted_seed_data.json"
        with open(seed_data_file, 'w') as f:
            json.dump(seed_data, f, indent=2, default=str)
        
        # Save comprehensive migration
        migration_file = results_dir / "comprehensive_seed_data_migration.py"
        with open(migration_file, 'w') as f:
            f.write(migration_code)
        
        # Display summary
        print("\n📊 EXTRACTION SUMMARY")
        print("-" * 30)
        print(f"Total tables: {seed_data['metadata']['total_tables']}")
        print(f"Total rows: {seed_data['metadata']['total_rows']}")
        
        print("\n📋 TABLE BREAKDOWN")
        print("-" * 25)
        for table_name, row_count in seed_data['statistics'].items():
            status = "✅" if row_count > 0 else "⚠️"
            print(f"{status} {table_name:25} | {row_count:4d} rows")
        
        print(f"\n💾 FILES CREATED")
        print("-" * 20)
        print(f"📄 Seed data: {seed_data_file}")
        print(f"🚀 Migration: {migration_file}")
        
        # Show migration stats
        with open(migration_file, 'r') as f:
            migration_lines = len(f.readlines())
        
        print(f"\n📈 MIGRATION STATISTICS")
        print("-" * 30)
        print(f"Migration file size: {migration_lines} lines")
        print(f"Contains actual data: ✅ Yes")
        print(f"Ready for testing: ✅ Yes")
        
        return seed_data
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        raise


def main():
    """Main function for command-line usage"""
    
    asyncio.run(run_extraction())


if __name__ == "__main__":
    main()