#!/usr/bin/env python3
"""
Detect potential circular imports in the codebase
"""

import os
import re
from collections import defaultdict
import networkx as nx

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

def build_import_graph(root_dir):
    """Build a directed graph of imports"""
    G = nx.DiGraph()
    import_map = defaultdict(list)
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip certain directories
        if any(skip in dirpath for skip in ['__pycache__', '.git', 'venv', 'backup', 'tests']):
            continue
            
        for filename in filenames:
            if filename.endswith('.py') and not filename.startswith('test_'):
                file_path = os.path.join(dirpath, filename)
                module_path = file_path.replace(root_dir + '/', '').replace('/', '.').replace('.py', '')
                
                # Only process app modules
                if module_path.startswith('app.'):
                    imports = extract_imports(file_path)
                    import_map[module_path] = imports
                    
                    # Add nodes and edges to graph
                    G.add_node(module_path)
                    for imp in imports:
                        G.add_edge(module_path, imp)
    
    return G, import_map

def find_circular_imports(G):
    """Find all circular dependencies in the graph"""
    try:
        cycles = list(nx.simple_cycles(G))
        return cycles
    except:
        return []

def analyze_workflow_dependencies():
    """Specifically analyze workflow-related dependencies"""
    root_dir = '/Users/dineshpatel/code/projects/SynapseDTE'
    
    print("Building import graph...")
    G, import_map = build_import_graph(root_dir)
    
    print(f"\nTotal modules analyzed: {len(G.nodes)}")
    print(f"Total import relationships: {len(G.edges)}")
    
    # Find circular imports
    print("\nDetecting circular imports...")
    cycles = find_circular_imports(G)
    
    if cycles:
        print(f"\nFound {len(cycles)} circular import chains:")
        for i, cycle in enumerate(cycles, 1):
            if len(cycle) == 2:
                print(f"\n{i}. Direct circular import:")
                print(f"   {cycle[0]} ↔ {cycle[1]}")
            else:
                print(f"\n{i}. Circular import chain:")
                for j in range(len(cycle)):
                    print(f"   {cycle[j]} → {cycle[(j+1) % len(cycle)]}")
    else:
        print("\nNo circular imports detected!")
    
    # Analyze workflow-specific imports
    print("\n\nWorkflow-related import analysis:")
    workflow_modules = [node for node in G.nodes if 'workflow' in node]
    
    for module in sorted(workflow_modules):
        print(f"\n{module}:")
        print(f"  Imports: {import_map[module]}")
        print(f"  Imported by: {[n for n in G.nodes if module in import_map[n]]}")

if __name__ == "__main__":
    analyze_workflow_dependencies()