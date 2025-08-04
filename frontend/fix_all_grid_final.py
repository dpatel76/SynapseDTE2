#!/usr/bin/env python3
"""
Fix all Grid component usages to use proper container/item props
"""

import os
import re
import glob

def fix_all_grid_final():
    """Fix all Grid component usages to use proper container/item props"""
    
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
            print(f"Fixing Grid props in {file_path}")
            
            # Fix Grid imports to use standard Grid
            content = re.sub(
                r'import\s*{\s*Grid2\s+as\s+Grid\s*}\s*from\s*["\']@mui/system["\'];?',
                'import Grid from "@mui/material/Grid";',
                content
            )
            
            content = re.sub(
                r'import\s*{\s*Unstable_Grid2\s+as\s+Grid\s*}\s*from\s*["\']@mui/material["\'];?',
                'import Grid from "@mui/material/Grid";',
                content
            )
            
            # Fix Grid usages that have size props but no item prop
            content = re.sub(
                r'<Grid\s+([^>]*?)xs=\{(\d+)\}([^>]*?)>',
                r'<Grid item xs={\2} \1\3>',
                content
            )
            
            content = re.sub(
                r'<Grid\s+([^>]*?)sm=\{(\d+)\}([^>]*?)>',
                r'<Grid item sm={\2} \1\3>',
                content
            )
            
            content = re.sub(
                r'<Grid\s+([^>]*?)md=\{(\d+)\}([^>]*?)>',
                r'<Grid item md={\2} \1\3>',
                content
            )
            
            # Fix cases where there are multiple props
            content = re.sub(
                r'<Grid\s+item\s+item\s+',
                r'<Grid item ',
                content
            )
            
            # Clean up any duplicate "item" props
            content = re.sub(
                r'item\s+item',
                r'item',
                content
            )
            
        # Save if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed Grid props in {file_path}")

if __name__ == "__main__":
    fix_all_grid_final()
    print("All Grid prop fixes completed!")