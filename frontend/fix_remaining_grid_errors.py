#!/usr/bin/env python3

import os
import re

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')

def fix_grid_syntax_errors(file_path):
    """Fix common Grid syntax errors in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix CircularProgress size prop - remove object wrapper
    content = re.sub(r'<CircularProgress\s+size=\{\{\s*(\d+)\s*\}\}', r'<CircularProgress size={\1}', content)
    
    # Fix Table size prop - remove object wrapper
    content = re.sub(r'<Table\s+size=\{\{\s*([^}]+)\s*\}\}', r'<Table size={\1}', content)
    
    # Fix trailing spaces in Grid size prop
    content = re.sub(r'<Grid\s+size=\{\{\s*([^}]+?)\s+\}\}', r'<Grid size={{ \1 }}', content)
    
    # Fix malformed Grid size props with extra spaces
    content = re.sub(r'size=\{\{\s*([^}]+?)\s+\}\}', r'size={{ \1 }}', content)
    
    # Fix triple braces in Grid size prop
    content = re.sub(r'size=\{\{\{\s*([^}]+)\s*\}\}\}', r'size={{ \1 }}', content)
    
    # Fix missing closing braces in Grid size prop
    content = re.sub(r'size=\{\{\s*([^}]+?)\s*\}([^}])', r'size={{ \1 }}\2', content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed Grid syntax errors in {file_path}")
        return True
    return False

def main():
    """Process all TypeScript/JavaScript files in the src directory."""
    fixed_files = []
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                file_path = os.path.join(root, file)
                if fix_grid_syntax_errors(file_path):
                    fixed_files.append(file_path)
    
    if fixed_files:
        print(f"\nFixed {len(fixed_files)} files:")
        for file_path in fixed_files:
            print(f"  - {os.path.relpath(file_path, src_dir)}")
    else:
        print("No files needed fixing.")

if __name__ == "__main__":
    main()