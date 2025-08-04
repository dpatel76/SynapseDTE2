#!/usr/bin/env python3
"""
Fix Grid2 imports across all files
"""

import os
import re
import glob

def fix_grid2_imports():
    """Fix all Grid2 imports to use the proper MUI v7 import"""
    
    # Get all TypeScript and TSX files
    files = glob.glob("/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/**/*.{ts,tsx}", recursive=True)
    
    for file_path in files:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix Grid2 import from @mui/material/Grid2
        if 'import Grid from "@mui/material/Grid2"' in content:
            print(f"Fixing Grid2 import in {file_path}")
            content = content.replace(
                'import Grid from "@mui/material/Grid2";',
                'import { Grid2 as Grid } from "@mui/material";'
            )
        
        # Fix Grid2 as Grid import
        if 'import Grid2 as Grid from "@mui/material/Grid2"' in content:
            print(f"Fixing Grid2 as Grid import in {file_path}")
            content = content.replace(
                'import Grid2 as Grid from "@mui/material/Grid2";',
                'import { Grid2 as Grid } from "@mui/material";'
            )
        
        # Save if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed Grid2 import in {file_path}")

if __name__ == "__main__":
    fix_grid2_imports()
    print("Grid2 import fixes completed!")