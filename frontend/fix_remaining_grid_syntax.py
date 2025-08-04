#!/usr/bin/env python3
"""
Fix remaining Grid component syntax issues in React frontend.
Convert from: <Grid xs={12} md={6}>
To: <Grid size={{ xs: 12, md: 6 }}>
"""

import os
import re
import glob

def fix_grid_syntax(content):
    """Fix Grid component syntax from old to new format"""
    
    # Pattern to match Grid components with old syntax
    # Matches: <Grid xs={12} md={6} lg={4}> etc
    pattern = r'<Grid\s+([^>]*?)>'
    
    def replace_grid_props(match):
        props_str = match.group(1)
        
        # Extract breakpoint props (xs, sm, md, lg, xl)
        breakpoints = {}
        breakpoint_pattern = r'(xs|sm|md|lg|xl)=\{(\d+)\}'
        
        for bp_match in re.finditer(breakpoint_pattern, props_str):
            bp_name = bp_match.group(1)
            bp_value = bp_match.group(2)
            breakpoints[bp_name] = bp_value
        
        # If no breakpoints found, return original
        if not breakpoints:
            return match.group(0)
        
        # Remove old breakpoint props
        new_props = props_str
        for bp_match in re.finditer(breakpoint_pattern, props_str):
            new_props = new_props.replace(bp_match.group(0), '')
        
        # Clean up extra spaces
        new_props = re.sub(r'\s+', ' ', new_props).strip()
        
        # Build size prop
        size_parts = []
        for bp, value in breakpoints.items():
            size_parts.append(f'{bp}: {value}')
        
        size_prop = f'size={{{{ {", ".join(size_parts)} }}}}'
        
        # Combine with other props
        if new_props:
            return f'<Grid {new_props} {size_prop}>'
        else:
            return f'<Grid {size_prop}>'
    
    # Apply the replacement
    result = re.sub(pattern, replace_grid_props, content)
    return result

def process_file(filepath):
    """Process a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix Grid syntax
        new_content = fix_grid_syntax(content)
        
        # Only write if there were changes
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Fixed: {filepath}")
            return True
        else:
            print(f"⏭️  No changes needed: {filepath}")
            return False
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Main function to process all files"""
    print("🔧 Fixing remaining Grid syntax issues...")
    
    # Get all TypeScript/JavaScript files in src directory
    src_dir = "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src"
    patterns = ["**/*.tsx", "**/*.ts", "**/*.jsx", "**/*.js"]
    
    files_to_process = []
    for pattern in patterns:
        files_to_process.extend(glob.glob(os.path.join(src_dir, pattern), recursive=True))
    
    total_files = len(files_to_process)
    fixed_files = 0
    
    print(f"📁 Found {total_files} files to check")
    
    for filepath in files_to_process:
        if process_file(filepath):
            fixed_files += 1
    
    print(f"\n🎉 Complete! Fixed {fixed_files} out of {total_files} files")

if __name__ == "__main__":
    main()