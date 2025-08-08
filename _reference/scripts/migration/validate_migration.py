#!/usr/bin/env python3
"""
Validate that a clean migration produces the same schema as the existing database.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.engine import Engine
from typing import Dict, List, Set, Tuple
import json


class SchemaComparator:
    """Compare database schemas to ensure migrations are equivalent."""
    
    def __init__(self, source_url: str, target_url: str):
        self.source_engine = create_engine(source_url)
        self.target_engine = create_engine(target_url)
        self.differences = []
    
    def compare_schemas(self) -> bool:
        """Compare source and target database schemas."""
        
        print("Comparing database schemas...")
        
        # Get inspectors
        source_inspector = inspect(self.source_engine)
        target_inspector = inspect(self.target_engine)
        
        # Compare tables
        source_tables = set(source_inspector.get_table_names())
        target_tables = set(target_inspector.get_table_names())
        
        # Check for missing tables
        missing_in_target = source_tables - target_tables
        extra_in_target = target_tables - source_tables
        
        if missing_in_target:
            self.differences.append(f"Tables missing in target: {missing_in_target}")
        if extra_in_target:
            self.differences.append(f"Extra tables in target: {extra_in_target}")
        
        # Compare columns for common tables
        common_tables = source_tables & target_tables
        
        for table in common_tables:
            source_columns = {col['name']: col for col in source_inspector.get_columns(table)}
            target_columns = {col['name']: col for col in target_inspector.get_columns(table)}
            
            # Check columns
            source_col_names = set(source_columns.keys())
            target_col_names = set(target_columns.keys())
            
            missing_cols = source_col_names - target_col_names
            extra_cols = target_col_names - source_col_names
            
            if missing_cols:
                self.differences.append(f"Table {table}: missing columns {missing_cols}")
            if extra_cols:
                self.differences.append(f"Table {table}: extra columns {extra_cols}")
            
            # Compare column types for common columns
            for col_name in source_col_names & target_col_names:
                source_col = source_columns[col_name]
                target_col = target_columns[col_name]
                
                if str(source_col['type']) != str(target_col['type']):
                    self.differences.append(
                        f"Table {table}.{col_name}: type mismatch "
                        f"{source_col['type']} vs {target_col['type']}"
                    )
                
                if source_col['nullable'] != target_col['nullable']:
                    self.differences.append(
                        f"Table {table}.{col_name}: nullable mismatch"
                    )
        
        # Compare indexes
        for table in common_tables:
            source_indexes = source_inspector.get_indexes(table)
            target_indexes = target_inspector.get_indexes(table)
            
            source_idx_names = {idx['name'] for idx in source_indexes if idx['name']}
            target_idx_names = {idx['name'] for idx in target_indexes if idx['name']}
            
            missing_idx = source_idx_names - target_idx_names
            if missing_idx:
                self.differences.append(f"Table {table}: missing indexes {missing_idx}")
        
        # Compare foreign keys
        for table in common_tables:
            source_fks = source_inspector.get_foreign_keys(table)
            target_fks = target_inspector.get_foreign_keys(table)
            
            source_fk_names = {fk['name'] for fk in source_fks if fk['name']}
            target_fk_names = {fk['name'] for fk in target_fks if fk['name']}
            
            missing_fks = source_fk_names - target_fk_names
            if missing_fks:
                self.differences.append(f"Table {table}: missing foreign keys {missing_fks}")
        
        return len(self.differences) == 0
    
    def print_report(self):
        """Print comparison report."""
        if not self.differences:
            print("✅ Schemas match perfectly!")
        else:
            print("❌ Schema differences found:")
            for diff in self.differences:
                print(f"  - {diff}")
    
    def export_schema_sql(self, engine: Engine, output_file: str):
        """Export schema as SQL for manual comparison."""
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        with open(output_file, 'w') as f:
            for table in metadata.sorted_tables:
                f.write(f"-- Table: {table.name}\n")
                f.write(str(table.compile(engine.dialect)) + ";\n\n")
        
        print(f"Schema exported to {output_file}")


def check_data_integrity(source_url: str, target_url: str):
    """Verify seed data was properly migrated."""
    
    print("\nChecking seed data integrity...")
    
    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url)
    
    checks = [
        ("SELECT COUNT(*) FROM users WHERE role IN ('Tester', 'Test Manager', 'Report Owner', 'Report Owner Executive', 'Data Provider', 'CDO')", "test users"),
        ("SELECT COUNT(*) FROM lobs", "LOBs"),
        ("SELECT COUNT(*) FROM rbac_permissions", "permissions"),
        ("SELECT COUNT(*) FROM rbac_roles", "roles"),
    ]
    
    all_match = True
    
    for query, description in checks:
        with source_engine.connect() as source_conn:
            source_count = source_conn.execute(query).scalar()
        
        with target_engine.connect() as target_conn:
            target_count = target_conn.execute(query).scalar()
        
        if source_count == target_count:
            print(f"  ✅ {description}: {source_count} records match")
        else:
            print(f"  ❌ {description}: {source_count} vs {target_count}")
            all_match = False
    
    return all_match


def main():
    """Main validation function."""
    
    if len(sys.argv) != 3:
        print("Usage: python validate_migration.py <source_db_url> <target_db_url>")
        print("Example: python validate_migration.py postgresql://localhost/synapse_dt postgresql://localhost/synapse_dt_test")
        sys.exit(1)
    
    source_url = sys.argv[1]
    target_url = sys.argv[2]
    
    print("Database Migration Validator")
    print("=" * 50)
    
    # Compare schemas
    comparator = SchemaComparator(source_url, target_url)
    schemas_match = comparator.compare_schemas()
    comparator.print_report()
    
    # Export schemas for manual review
    comparator.export_schema_sql(comparator.source_engine, "source_schema.sql")
    comparator.export_schema_sql(comparator.target_engine, "target_schema.sql")
    
    # Check data
    data_matches = check_data_integrity(source_url, target_url)
    
    # Final verdict
    print("\n" + "=" * 50)
    if schemas_match and data_matches:
        print("✅ Migration validation PASSED!")
        print("The clean migration produces an equivalent database.")
    else:
        print("❌ Migration validation FAILED!")
        print("Please review the differences and update the migration.")
        sys.exit(1)


if __name__ == "__main__":
    main()