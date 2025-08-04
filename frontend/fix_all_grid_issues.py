#!/usr/bin/env python3
"""
Script to fix all Grid component issues in the React frontend
"""

import os
import re

def fix_grid_imports_and_usage(file_path):
    """Fix Grid imports and usage in a TypeScript file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix imports - convert GridLegacy to proper Grid import
        content = re.sub(
            r'import \{ GridLegacy as Grid(.*?) \} from \'@mui/material\';',
            r'import {\1 } from \'@mui/material\';\nimport Grid from \'@mui/material/Grid\';',
            content
        )
        
        # Fix mixed import patterns
        content = re.sub(
            r'GridLegacy as Grid,\s*',
            '',
            content
        )
        
        # Fix Grid component usage with mixed props (e.g., md={6} size={{ xs: 12 }})
        # Find patterns like: md={value} size={{ xs: 12, ... }}
        def fix_mixed_grid_props(match):
            full_match = match.group(0)
            # Extract the md/lg/sm value
            md_match = re.search(r'(md|lg|sm)=\{([^}]+)\}', full_match)
            size_match = re.search(r'size=\{\{\s*([^}]+)\s*\}\}', full_match)
            
            if md_match and size_match:
                prop_name = md_match.group(1)
                prop_value = md_match.group(2)
                size_content = size_match.group(1)
                
                # Remove the old prop and add it to size
                new_size_content = f"{size_content}, {prop_name}: {prop_value}"
                return full_match.replace(f"{prop_name}={{{prop_value}}}", "").replace(f"size={{{{ {size_content} }}}}", f"size={{{{ {new_size_content} }}}}")
            
            return full_match
        
        content = re.sub(
            r'<Grid[^>]*(?:md|lg|sm)=\{[^}]+\}[^>]*size=\{\{[^}]+\}\}[^>]*>',
            fix_mixed_grid_props,
            content
        )
        
        # Fix standalone md/lg/sm props without size (convert to size prop)
        content = re.sub(
            r'<Grid([^>]*?)\s+(md|lg|sm)=\{([^}]+)\}([^>]*?)>',
            r'<Grid\1 size={{ \2: \3 }}\4>',
            content
        )
        
        # Fix syntax error in WorkflowVisualization.tsx
        content = re.sub(
            r'md=\{level\.length size=\{\{ xs: 12 \}\}> 1 \? 6 : 12\}',
            r'size={{ xs: 12, md: level.length > 1 ? 6 : 12 }}',
            content
        )
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all Grid issues"""
    frontend_dir = '/Users/dineshpatel/code/projects/SynapseDTE/frontend/src'
    
    fixed_files = []
    
    # Find all TypeScript files
    for root, dirs, files in os.walk(frontend_dir):
        for file in files:
            if file.endswith('.tsx') or file.endswith('.ts'):
                file_path = os.path.join(root, file)
                try:
                    if fix_grid_imports_and_usage(file_path):
                        fixed_files.append(file_path)
                        print(f"Fixed: {file_path}")
                except Exception as e:
                    print(f"Error with {file_path}: {e}")
    
    print(f"\nFixed {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main()