#!/usr/bin/env python3
"""
Check Alembic migration chain
"""

import os
import re
from pathlib import Path

# Get all migration files
migration_dir = Path("alembic/versions")
migrations = {}

# Parse each migration file
for file in migration_dir.glob("*.py"):
    if file.name == "__pycache__":
        continue
        
    with open(file) as f:
        content = f.read()
        
    # Extract revision and down_revision
    revision_match = re.search(r"revision = ['\"]([^'\"]+)['\"]", content)
    down_revision_match = re.search(r"down_revision = ['\"]([^'\"]+)['\"]", content)
    
    if revision_match:
        revision = revision_match.group(1)
        down_revision = down_revision_match.group(1) if down_revision_match else None
        
        # Extract description from docstring
        desc_match = re.search(r'"""([^"]+)"""', content)
        description = desc_match.group(1).strip() if desc_match else "No description"
        
        migrations[revision] = {
            "file": file.name,
            "down_revision": down_revision,
            "description": description,
            "timestamp": file.name.split("-")[0] if "-" in file.name else "unknown"
        }

# Build the chain
print("\n" + "="*80)
print("ALEMBIC MIGRATION CHAIN")
print("="*80)

# Find the head (migration with no children)
heads = []
for rev, info in migrations.items():
    is_head = True
    for other_rev, other_info in migrations.items():
        if other_info["down_revision"] == rev:
            is_head = False
            break
    if is_head:
        heads.append(rev)

print(f"\nFound {len(heads)} head(s): {', '.join(heads)}\n")

# Trace back from each head
for head in heads:
    print(f"Chain from head '{head}':")
    print("-" * 60)
    
    current = head
    level = 0
    while current:
        if current in migrations:
            info = migrations[current]
            indent = "  " * level
            print(f"{indent}├─ {current}")
            print(f"{indent}│  File: {info['file']}")
            print(f"{indent}│  Desc: {info['description']}")
            if info['down_revision']:
                print(f"{indent}│  Parent: {info['down_revision']}")
            print(f"{indent}│")
            current = info['down_revision']
            level += 1
        else:
            if current != 'None':
                print(f"{indent}└─ {current} (not found in directory)")
            break

# Check for RBAC migrations specifically
print("\n" + "="*80)
print("RBAC MIGRATIONS")
print("="*80)

rbac_migrations = [(rev, info) for rev, info in migrations.items() 
                   if 'rbac' in info['file'].lower() or 'rbac' in info['description'].lower()]

for rev, info in sorted(rbac_migrations, key=lambda x: x[1]['file']):
    print(f"\n{info['file']}:")
    print(f"  Revision: {rev}")
    print(f"  Description: {info['description']}")
    print(f"  Parent: {info['down_revision']}")

print("\n" + "="*80)