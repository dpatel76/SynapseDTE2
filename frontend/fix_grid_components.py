#!/usr/bin/env python3
"""
Fix Grid component issues by replacing Grid with Grid2 imports
"""

import os
import re
import glob

def fix_grid_components():
    """Fix Grid component issues by using Grid2"""
    
    # Get all TypeScript and TSX files
    files = glob.glob("/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/**/*.{ts,tsx}", recursive=True)
    
    for file_path in files:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if file uses Grid component with size props
        if '<Grid' in content and ('xs=' in content or 'sm=' in content or 'md=' in content):
            print(f"Fixing {file_path}")
            
            # Fix Grid imports - replace with Grid2
            content = re.sub(
                r'import\s+Grid\s+from\s+["\']@mui/material/Grid["\'];?',
                r'import Grid from "@mui/material/Grid2";',
                content
            )
            
            # Fix Grid imports from general @mui/material import
            if 'import {' in content and 'Grid' in content and '@mui/material' in content:
                # Replace Grid with Grid2 as Grid in imports
                content = re.sub(
                    r'import\s*{\s*([^}]*?)Grid([^}]*?)}\s*from\s*["\']@mui/material["\'];?',
                    lambda m: f'import {{ {m.group(1)}Grid2 as Grid{m.group(2)} }} from "@mui/material";',
                    content
                )
            
            # If no Grid import found but Grid is used, add Grid2 import
            if 'import Grid' not in content and '<Grid' in content:
                # Find the best place to add import
                import_pattern = r'(import\s+.*?from\s+["\']@mui/material["\'];?\n)'
                match = re.search(import_pattern, content)
                if match:
                    # Add after existing mui imports
                    content = content[:match.end()] + 'import Grid from "@mui/material/Grid2";\n' + content[match.end():]
                else:
                    # Add at the beginning after React imports
                    react_import = re.search(r'(import\s+.*?from\s+["\']react["\'];?\n)', content)
                    if react_import:
                        content = content[:react_import.end()] + 'import Grid from "@mui/material/Grid2";\n' + content[react_import.end():]
                    else:
                        # Add at the very beginning
                        content = 'import Grid from "@mui/material/Grid2";\n' + content
        
        # Save if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed {file_path}")

if __name__ == "__main__":
    fix_grid_components()
    print("Grid component fixes completed!")