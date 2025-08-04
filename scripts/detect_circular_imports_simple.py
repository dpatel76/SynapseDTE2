#!/usr/bin/env python3
"""
Simple circular import detector without external dependencies
"""

import os
import re
from collections import defaultdict

def extract_imports(file_path):
    """Extract all imports from a Python file"""
    imports = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Match various import patterns
        patterns = [
            r'^from\s+(app\.[^\s]+)\s+import',  # from app.x import y
            r'^import\s+(app\.[^\s]+)',          # import app.x
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return list(set(imports))

def check_mutual_imports(import_map):
    """Check for mutual imports between modules"""
    circular_pairs = []
    
    for module1, imports1 in import_map.items():
        for imported in imports1:
            if imported in import_map:
                # Check if imported module also imports module1
                if module1 in import_map[imported]:
                    pair = tuple(sorted([module1, imported]))
                    if pair not in circular_pairs:
                        circular_pairs.append(pair)
    
    return circular_pairs

def main():
    root_dir = '/Users/dineshpatel/code/projects/SynapseDTE'
    import_map = defaultdict(list)
    
    print("Scanning for imports...")
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip certain directories
        if any(skip in dirpath for skip in ['__pycache__', '.git', 'venv', 'backup', 'tests', 'scripts']):
            continue
            
        for filename in filenames:
            if filename.endswith('.py') and not filename.startswith('test_'):
                file_path = os.path.join(dirpath, filename)
                module_path = file_path.replace(root_dir + '/', '').replace('/', '.').replace('.py', '')
                
                # Only process app modules
                if module_path.startswith('app.'):
                    imports = extract_imports(file_path)
                    if imports:
                        import_map[module_path] = imports
    
    print(f"\nAnalyzed {len(import_map)} modules")
    
    # Check for circular imports
    circular_pairs = check_mutual_imports(import_map)
    
    if circular_pairs:
        print(f"\nFound {len(circular_pairs)} circular import pairs:")
        for module1, module2 in circular_pairs:
            print(f"\n  {module1} ↔ {module2}")
    else:
        print("\nNo direct circular imports found!")
    
    # Analyze workflow-specific modules
    print("\n\nWorkflow module dependencies:")
    workflow_modules = [m for m in import_map if 'workflow' in m]
    
    for module in sorted(workflow_modules):
        imports = [imp for imp in import_map[module] if 'workflow' in imp or 'service' in imp]
        if imports:
            print(f"\n{module}:")
            for imp in imports:
                print(f"  → {imp}")

if __name__ == "__main__":
    main()