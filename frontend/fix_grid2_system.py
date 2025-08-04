#!/usr/bin/env python3
"""
Fix Grid2 imports to use @mui/system
"""

import os
import re
import glob

def fix_grid2_system():
    """Fix all Grid2 imports to use @mui/system"""
    
    # Get all TypeScript and TSX files
    files = glob.glob("/Users/dineshpatel/code/projects/SynapseDTE/frontend/src/**/*.{ts,tsx}", recursive=True)
    
    for file_path in files:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix Grid2 imports
        if 'import { Unstable_Grid2 as Grid } from "@mui/material";' in content:
            print(f"Fixing Grid2 import in {file_path}")
            content = content.replace(
                'import { Unstable_Grid2 as Grid } from "@mui/material";',
                'import { Grid2 as Grid } from "@mui/system";'
            )
        
        # Save if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed Grid2 import in {file_path}")

if __name__ == "__main__":
    fix_grid2_system()
    print("Grid2 system import fixes completed!")