#!/usr/bin/env python3

import os
import re

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')

def fix_grid_size_numeric(file_path):
    """Fix Grid size props that have numeric values without 'xs' prefix."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix Grid size={{ 12 }} -> Grid size={{ xs: 12 }}
    content = re.sub(r'size=\{\{\s*(\d+)\s*\}\}', r'size={{ xs: \1 }}', content)
    
    # Fix Grid size={{ 6, md: 4 }} -> Grid size={{ xs: 6, md: 4 }}
    content = re.sub(r'size=\{\{\s*(\d+),\s*([^}]+)\s*\}\}', r'size={{ xs: \1, \2 }}', content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed Grid size numeric props in {file_path}")
        return True
    return False

def main():
    """Process all TypeScript/JavaScript files in the src directory."""
    fixed_files = []
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                file_path = os.path.join(root, file)
                if fix_grid_size_numeric(file_path):
                    fixed_files.append(file_path)
    
    if fixed_files:
        print(f"\nFixed {len(fixed_files)} files:")
        for file_path in fixed_files:
            print(f"  - {os.path.relpath(file_path, src_dir)}")
    else:
        print("No files needed fixing.")

if __name__ == "__main__":
    main()