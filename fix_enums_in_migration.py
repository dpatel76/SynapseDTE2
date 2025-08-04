#!/usr/bin/env python3
"""
Fix enum type creation in migration file to avoid duplicates.
"""

import re


def fix_enums(input_file: str, output_file: str):
    """Fix enum type creation to use checkfirst=True."""
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Find all inline ENUM definitions in column definitions
    # Pattern: postgresql.ENUM(..., name='enum_name')
    enum_pattern = r"postgresql\.ENUM\((.*?), name='([^']+)'\)"
    
    # Find all unique enum types
    enum_matches = re.findall(enum_pattern, content, re.DOTALL)
    unique_enums = {}
    
    for values, enum_name in enum_matches:
        if enum_name not in unique_enums:
            unique_enums[enum_name] = values
    
    # Create enum definitions at the top of upgrade function
    enum_definitions = []
    for enum_name, values in unique_enums.items():
        if enum_name != 'user_role_enum':  # Skip user_role_enum as it's already defined
            var_name = enum_name.replace('-', '_')
            enum_definitions.append(f"    {var_name} = postgresql.ENUM({values}, name='{enum_name}')")
            enum_definitions.append(f"    {var_name}.create(op.get_bind(), checkfirst=True)")
    
    # Insert enum definitions after the user_role_enum creation
    if enum_definitions:
        insert_after = "user_role_enum.create(op.get_bind(), checkfirst=True)"
        insert_pos = content.find(insert_after)
        if insert_pos != -1:
            insert_pos = content.find('\n', insert_pos) + 1
            enum_defs_str = '\n'.join(enum_definitions) + '\n'
            content = content[:insert_pos] + enum_defs_str + content[insert_pos:]
    
    # Replace all inline ENUM definitions with the variable references
    for enum_name in unique_enums:
        if enum_name != 'user_role_enum':  # Skip user_role_enum
            var_name = enum_name.replace('-', '_')
            # Pattern to replace inline ENUM with variable
            pattern = rf"postgresql\.ENUM\([^)]+, name='{enum_name}'\)"
            content = re.sub(pattern, var_name, content)
    
    # Write the fixed content
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {len(unique_enums)} enum types in {output_file}")
    print("Enums found:", list(unique_enums.keys()))


if __name__ == "__main__":
    input_file = "/Users/dineshpatel/code/projects/SynapseDTE2/alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models.py"
    output_file = "/Users/dineshpatel/code/projects/SynapseDTE2/alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models_enums_fixed.py"
    
    fix_enums(input_file, output_file)