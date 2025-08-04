#!/usr/bin/env python3
"""
Fix all Grid imports to use Grid2 from MUI v7
"""

import os
import re
import glob

def fix_all_grid_imports():
    """Fix all Grid imports across all files"""
    
    # Get all TypeScript and TSX files
    files = glob.glob("/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/**/*.{ts,tsx}", recursive=True)
    
    for file_path in files:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if file uses Grid components with xs, sm, md props
        if '<Grid' in content and ('xs=' in content or 'sm=' in content or 'md=' in content):
            print(f"Fixing Grid import in {file_path}")
            
            # Check if Grid is imported in general @mui/material import
            if re.search(r'import\s*{\s*([^}]*?)Grid([^}]*?)}\s*from\s*["\']@mui/material["\']', content):
                # Remove Grid from the general import
                content = re.sub(
                    r'import\s*{\s*([^}]*?)Grid,([^}]*?)}\s*from\s*["\']@mui/material["\']',
                    r'import { \1\2} from "@mui/material"',
                    content
                )
                content = re.sub(
                    r'import\s*{\s*([^}]*?),\s*Grid([^}]*?)}\s*from\s*["\']@mui/material["\']',
                    r'import { \1\2} from "@mui/material"',
                    content
                )
                content = re.sub(
                    r'import\s*{\s*Grid,([^}]*?)}\s*from\s*["\']@mui/material["\']',
                    r'import { \1} from "@mui/material"',
                    content
                )
                content = re.sub(
                    r'import\s*{\s*Grid\s*}\s*from\s*["\']@mui/material["\']',
                    r'',
                    content
                )
                
                # Clean up any double commas or spaces
                content = re.sub(r'{\s*,', r'{', content)
                content = re.sub(r',\s*}', r'}', content)
                content = re.sub(r',\s*,', r',', content)
                
                # Add Grid2 as Grid import
                if 'import { Grid2 as Grid } from "@mui/material";' not in content:
                    # Find a good place to insert the import
                    mui_import_match = re.search(r'(import\s*{[^}]*}\s*from\s*["\']@mui/material["\'];?\n)', content)
                    if mui_import_match:
                        content = content[:mui_import_match.end()] + 'import { Grid2 as Grid } from "@mui/material";\n' + content[mui_import_match.end():]
                    else:
                        # Add at the beginning after other imports
                        react_import_match = re.search(r'(import\s+.*?from\s+["\']react["\'];?\n)', content)
                        if react_import_match:
                            content = content[:react_import_match.end()] + 'import { Grid2 as Grid } from "@mui/material";\n' + content[react_import_match.end():]
                        else:
                            content = 'import { Grid2 as Grid } from "@mui/material";\n' + content
        
        # Save if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed Grid import in {file_path}")

if __name__ == "__main__":
    fix_all_grid_imports()
    print("All Grid import fixes completed!")