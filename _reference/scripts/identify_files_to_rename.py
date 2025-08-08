#!/usr/bin/env python3
"""
Identify all files that need renaming to remove prefixes and suffixes
"""

import os
import re
from collections import defaultdict

# Patterns to identify files that need renaming
PREFIXES_TO_REMOVE = ['Simplified']
SUFFIXES_TO_REMOVE = ['_clean', 'Clean', 'Enhanced', 'Redesigned', 'Refactored', 'Fixed', '_v2', 'V2']

def needs_renaming(filename):
    """Check if a file needs renaming"""
    name_without_ext = filename.rsplit('.', 1)[0]
    
    # Check for prefixes
    for prefix in PREFIXES_TO_REMOVE:
        if name_without_ext.startswith(prefix):
            return True
    
    # Check for suffixes
    for suffix in SUFFIXES_TO_REMOVE:
        if name_without_ext.endswith(suffix):
            return True
    
    return False

def suggest_new_name(filepath):
    """Suggest a new name for the file"""
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name_without_ext = filename.rsplit('.', 1)[0]
    extension = filename.rsplit('.', 1)[1] if '.' in filename else ''
    
    new_name = name_without_ext
    
    # Remove prefixes
    for prefix in PREFIXES_TO_REMOVE:
        if new_name.startswith(prefix):
            new_name = new_name[len(prefix):]
            # Convert first character to lowercase if needed
            if new_name and new_name[0].isupper() and len(new_name) > 1 and new_name[1].islower():
                new_name = new_name[0].lower() + new_name[1:]
    
    # Remove suffixes
    for suffix in SUFFIXES_TO_REMOVE:
        if new_name.endswith(suffix):
            new_name = new_name[:-len(suffix)]
    
    # Add extension back
    if extension:
        new_name = f"{new_name}.{extension}"
    
    return os.path.join(directory, new_name)

def find_imports_to_update(filepath, old_name, new_name):
    """Find files that import this module"""
    imports_to_update = []
    
    # Extract module names
    old_module = old_name.rsplit('.', 1)[0]
    new_module = new_name.rsplit('.', 1)[0]
    
    # Search for imports in the codebase
    root_dir = '/Users/dineshpatel/code/projects/SynapseDTE'
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip certain directories
        if any(skip in dirpath for skip in ['__pycache__', '.git', 'venv', 'backup', 'node_modules']):
            continue
            
        for filename in filenames:
            if filename.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    # Check for various import patterns
                    if old_module in content:
                        imports_to_update.append(file_path)
                except:
                    pass
    
    return imports_to_update

def main():
    root_dir = '/Users/dineshpatel/code/projects/SynapseDTE'
    files_to_rename = defaultdict(list)
    
    print("Scanning for files to rename...")
    print("=" * 80)
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip certain directories
        if any(skip in dirpath for skip in ['__pycache__', '.git', 'venv', 'backup', 'node_modules', '.backup']):
            continue
            
        for filename in filenames:
            # Skip backup files
            if filename.endswith('.backup'):
                continue
                
            if needs_renaming(filename):
                filepath = os.path.join(dirpath, filename)
                new_filepath = suggest_new_name(filepath)
                
                # Group by directory
                rel_dir = os.path.relpath(dirpath, root_dir)
                files_to_rename[rel_dir].append({
                    'old': filename,
                    'new': os.path.basename(new_filepath),
                    'full_old': filepath,
                    'full_new': new_filepath
                })
    
    # Display results
    total_files = sum(len(files) for files in files_to_rename.values())
    print(f"\nFound {total_files} files to rename:\n")
    
    # Group by type
    frontend_files = []
    backend_files = []
    
    for directory, files in sorted(files_to_rename.items()):
        for file_info in files:
            if 'frontend' in directory:
                frontend_files.append((directory, file_info))
            else:
                backend_files.append((directory, file_info))
    
    # Display frontend files
    if frontend_files:
        print("\nFRONTEND FILES:")
        print("-" * 80)
        for directory, file_info in frontend_files:
            print(f"\n{directory}/")
            print(f"  {file_info['old']} → {file_info['new']}")
            
            # Check for imports
            imports = find_imports_to_update(file_info['full_old'], file_info['old'], file_info['new'])
            if imports:
                print(f"  ⚠️  {len(imports)} files import this module")
    
    # Display backend files
    if backend_files:
        print("\n\nBACKEND FILES:")
        print("-" * 80)
        for directory, file_info in backend_files:
            print(f"\n{directory}/")
            print(f"  {file_info['old']} → {file_info['new']}")
            
            # Check for imports
            imports = find_imports_to_update(file_info['full_old'], file_info['old'], file_info['new'])
            if imports:
                print(f"  ⚠️  {len(imports)} files import this module")
    
    # Generate rename script
    print("\n\nGenerating rename script...")
    
    script_content = """#!/bin/bash
# Auto-generated script to rename files
# Review carefully before running!

set -e  # Exit on error

echo "Starting file renaming..."

"""
    
    for directory, files in files_to_rename.items():
        for file_info in files:
            old_path = file_info['full_old']
            new_path = file_info['full_new']
            
            # Skip if target already exists
            script_content += f"""
# Rename {file_info['old']} to {file_info['new']}
if [ -f "{old_path}" ]; then
    if [ ! -f "{new_path}" ]; then
        echo "Renaming {file_info['old']} → {file_info['new']}"
        mv "{old_path}" "{new_path}"
    else
        echo "⚠️  Target already exists: {new_path}"
    fi
fi
"""
    
    script_content += """
echo "File renaming complete!"
echo "Remember to update all imports after renaming."
"""
    
    with open('scripts/rename_files_cleanup.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('scripts/rename_files_cleanup.sh', 0o755)
    print("✓ Created scripts/rename_files_cleanup.sh")
    
    # Create import update script
    print("\nCreating import update script...")
    
    import_script = """#!/usr/bin/env python3
# Auto-generated script to update imports after renaming
import os
import re

replacements = [
"""
    
    for directory, files in files_to_rename.items():
        for file_info in files:
            old_module = file_info['old'].rsplit('.', 1)[0]
            new_module = file_info['new'].rsplit('.', 1)[0]
            import_script += f"    ('{old_module}', '{new_module}'),\n"
    
    import_script += """
]

def update_imports(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original_content = content
        for old, new in replacements:
            # Update various import patterns
            content = re.sub(rf'\\b{old}\\b', new, content)
        
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
    return False

# Update all files
root_dir = '/Users/dineshpatel/code/projects/SynapseDTE'
updated_files = 0

for dirpath, dirnames, filenames in os.walk(root_dir):
    if any(skip in dirpath for skip in ['__pycache__', '.git', 'venv', 'backup', 'node_modules']):
        continue
        
    for filename in filenames:
        if filename.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
            filepath = os.path.join(dirpath, filename)
            if update_imports(filepath):
                updated_files += 1
                print(f"Updated: {filepath}")

print(f"\\nUpdated {updated_files} files")
"""
    
    with open('scripts/update_imports_after_rename.py', 'w') as f:
        f.write(import_script)
    
    os.chmod('scripts/update_imports_after_rename.py', 0o755)
    print("✓ Created scripts/update_imports_after_rename.py")
    
    print(f"\n\nSummary:")
    print(f"- Total files to rename: {total_files}")
    print(f"- Frontend files: {len(frontend_files)}")
    print(f"- Backend files: {len(backend_files)}")
    print("\nNext steps:")
    print("1. Review the file list above")
    print("2. Run: bash scripts/rename_files_cleanup.sh")
    print("3. Run: python scripts/update_imports_after_rename.py")
    print("4. Test the application thoroughly")

if __name__ == "__main__":
    main()