#!/usr/bin/env python3
"""
Generate initial Alembic migration from current database state
"""
import subprocess
import os
import sys
import datetime

def main():
    print("Generating initial Alembic migration from current database state...")
    
    # Set environment for local execution
    env = os.environ.copy()
    env['DATABASE_URL'] = 'postgresql://synapse_user:synapse_password@localhost:5433/synapse_dt'
    
    # Create timestamp for migration
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate migration
    cmd = [
        'alembic',
        'revision',
        '--autogenerate',
        '-m', f'initial_migration_{timestamp}'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error generating migration: {result.stderr}")
        return 1
    
    print(f"Migration generated: {result.stdout}")
    
    # Find the generated migration file
    versions_dir = 'alembic/versions'
    migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
    if migration_files:
        latest_migration = sorted(migration_files)[-1]
        print(f"\nGenerated migration file: {versions_dir}/{latest_migration}")
        
        # Apply the migration
        print("\nApplying migration...")
        apply_cmd = ['alembic', 'upgrade', 'head']
        apply_result = subprocess.run(apply_cmd, env=env, capture_output=True, text=True)
        
        if apply_result.returncode != 0:
            print(f"Error applying migration: {apply_result.stderr}")
            return 1
        
        print("Migration applied successfully!")
        print(apply_result.stdout)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())