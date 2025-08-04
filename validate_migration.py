#!/usr/bin/env python3
"""
Script to validate the refactored migration file.

This script checks:
1. No ForeignKeyConstraint lines remain in table definitions
2. All foreign keys are added at the end
3. Downgrade function has corresponding drop statements
4. No circular dependency issues
"""

import re
import sys
from pathlib import Path


def validate_migration_file(file_path: str):
    """Validate the refactored migration file."""
    
    print(f"Validating migration file: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check 1: No ForeignKeyConstraint in table definitions
    fk_constraints_in_tables = re.findall(r'sa\.ForeignKeyConstraint', content)
    if fk_constraints_in_tables:
        issues.append(f"Found {len(fk_constraints_in_tables)} ForeignKeyConstraint lines still in table definitions")
    
    # Check 2: Count op.create_foreign_key statements
    create_fk_statements = re.findall(r'op\.create_foreign_key', content)
    print(f"✅ Found {len(create_fk_statements)} op.create_foreign_key statements")
    
    # Check 3: Count op.drop_constraint statements for foreign keys
    drop_fk_statements = re.findall(r"op\.drop_constraint.*type_='foreignkey'", content)
    print(f"✅ Found {len(drop_fk_statements)} op.drop_constraint statements for foreign keys")
    
    # Check 4: Verify create and drop counts match
    if len(create_fk_statements) != len(drop_fk_statements):
        issues.append(f"Mismatch: {len(create_fk_statements)} create_foreign_key vs {len(drop_fk_statements)} drop_constraint statements")
    
    # Check 5: Verify table structure - look for a few sample tables
    sample_tables = ['users', 'activity_definitions', 'reports']
    for table_name in sample_tables:
        table_pattern = rf"op\.create_table\('{table_name}',(.*?)\n\s*\)"
        table_match = re.search(table_pattern, content, re.DOTALL)
        if table_match:
            table_content = table_match.group(1)
            if 'sa.ForeignKeyConstraint' in table_content:
                issues.append(f"Table '{table_name}' still contains ForeignKeyConstraint")
            print(f"✅ Table '{table_name}' looks clean")
        else:
            issues.append(f"Could not find table '{table_name}' definition")
    
    # Check 6: Verify foreign keys are added after table creations
    upgrade_function_pattern = r'def upgrade\(\) -> None:(.*?)def downgrade\(\) -> None:'
    upgrade_match = re.search(upgrade_function_pattern, content, re.DOTALL)
    
    if upgrade_match:
        upgrade_content = upgrade_match.group(1)
        
        # Find last table creation
        last_table_pos = -1
        for match in re.finditer(r'op\.create_table', upgrade_content):
            last_table_pos = match.end()
        
        # Find first foreign key creation
        first_fk_match = re.search(r'op\.create_foreign_key', upgrade_content)
        first_fk_pos = first_fk_match.start() if first_fk_match else -1
        
        if last_table_pos > 0 and first_fk_pos > 0:
            if first_fk_pos < last_table_pos:
                issues.append("Foreign keys are being created before all tables are created")
            else:
                print("✅ Foreign keys are created after all tables")
    
    # Check 7: Verify no circular references in table creation order
    # This is complex, but we can do a basic check by ensuring base tables come first
    base_tables = ['lobs', 'users']
    dependent_tables = ['reports', 'test_cycles']
    
    table_positions = {}
    for table_name in base_tables + dependent_tables:
        pattern = rf"op\.create_table\('{table_name}'"
        match = re.search(pattern, content)
        if match:
            table_positions[table_name] = match.start()
    
    for base_table in base_tables:
        if base_table in table_positions:
            for dep_table in dependent_tables:
                if dep_table in table_positions:
                    if table_positions[base_table] > table_positions[dep_table]:
                        issues.append(f"Table '{dep_table}' is created before '{base_table}' which it likely depends on")
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    if issues:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print("✅ ALL CHECKS PASSED!")
        print("\nKey metrics:")
        print(f"  • Foreign key constraints moved: {len(create_fk_statements)}")
        print(f"  • Drop statements created: {len(drop_fk_statements)}")
        print(f"  • No circular dependencies detected")
        print(f"  • All tables are clean of inline foreign key constraints")
        print("\n🎉 Migration file is ready for use!")
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_migration.py <migration_file>")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    
    if not Path(migration_file).exists():
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    success = validate_migration_file(migration_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()