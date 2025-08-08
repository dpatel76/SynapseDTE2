#!/usr/bin/env python3
"""
Rename roles in the database and update all references
CDO -> Data Executive
Test Manager -> Test Executive
Data Provider -> Data Owner
"""

import psycopg2
import os
import re

def update_database_roles():
    """Update role names in the database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='synapse_dt',
            user='synapse_user',
            password='synapse_password'
        )
        
        cur = conn.cursor()
        
        # Update roles table
        print("Updating roles table...")
        cur.execute("""
            UPDATE rbac_roles 
            SET role_name = CASE 
                WHEN role_name = 'Data Executive' THEN 'Data Executive'
                WHEN role_name = 'Test Executive' THEN 'Test Executive'
                WHEN role_name = 'Data Owner' THEN 'Data Owner'
                ELSE role_name
            END
            WHERE role_name IN ('Data Executive', 'Test Executive', 'Data Owner')
        """)
        print(f"  ✅ Updated {cur.rowcount} roles")
        
        # Update users table (handle enum type)
        print("\nUpdating users table...")
        # First, alter the enum type to add new values
        cur.execute("""
            ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'Data Executive';
            ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'Test Executive';
            ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'Data Owner';
        """)
        conn.commit()
        
        # Update user roles
        cur.execute("""
            UPDATE users 
            SET role = CASE 
                WHEN role = 'Data Executive' THEN 'Data Executive'::user_role_enum
                WHEN role = 'Test Executive' THEN 'Test Executive'::user_role_enum
                WHEN role = 'Data Owner' THEN 'Data Owner'::user_role_enum
                ELSE role
            END
            WHERE role::text IN ('Data Executive', 'Test Executive', 'Data Owner')
        """)
        print(f"  ✅ Updated {cur.rowcount} user records")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n✅ Database updates completed!")
        
    except Exception as e:
        print(f"❌ Database update error: {e}")
        return False
    
    return True

def update_python_files():
    """Update role references in Python files"""
    print("\nUpdating Python files...")
    
    # Define replacements
    replacements = [
        # Enum values
        ('DATA_EXECUTIVE = "Data Executive"', 'DATA_EXECUTIVE = "Data Executive"'),
        ('TEST_EXECUTIVE = "Test Executive"', 'TEST_EXECUTIVE = "Test Executive"'),
        ('DATA_OWNER = "Data Owner"', 'DATA_OWNER = "Data Owner"'),
        # String literals
        ('"Data Executive"', '"Data Executive"'),
        ("'Data Executive'", "'Data Executive'"),
        ('"Test Executive"', '"Test Executive"'),
        ("'Test Executive'", "'Test Executive'"),
        ('"Data Owner"', '"Data Owner"'),
        ("'Data Owner'", "'Data Owner'"),
        # UserRoles enum references
        ('UserRoles.DATA_EXECUTIVE', 'UserRoles.DATA_EXECUTIVE'),
        ('UserRoles.TEST_EXECUTIVE', 'UserRoles.TEST_EXECUTIVE'),
        ('UserRoles.DATA_OWNER', 'UserRoles.DATA_OWNER'),
        # Comments and docstrings
        ('Data Executive role', 'Data Executive role'),
        ('Test Executive role', 'Test Executive role'),
        ('Data Owner role', 'Data Owner role'),
        # Phase names
        ('data-owner', 'data-owner'),
        ('data_owner', 'data_owner'),
    ]
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk("/Users/dineshpatel/code/projects/SynapseDTE"):
        # Skip virtual env and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', '__pycache__', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    updated_files = 0
    for filepath in python_files:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            original_content = content
            for old, new in replacements:
                content = content.replace(old, new)
            
            if content != original_content:
                # Create backup
                backup_path = filepath + '.role_backup'
                with open(backup_path, 'w') as f:
                    f.write(original_content)
                
                # Write updated content
                with open(filepath, 'w') as f:
                    f.write(content)
                
                updated_files += 1
                print(f"  ✅ Updated: {filepath}")
                
        except Exception as e:
            print(f"  ❌ Error updating {filepath}: {e}")
    
    print(f"\n✅ Updated {updated_files} Python files")
    return True

def update_typescript_files():
    """Update role references in TypeScript/React files"""
    print("\nUpdating TypeScript/React files...")
    
    # Define replacements
    replacements = [
        # Enum values and types
        ('DATA_EXECUTIVE = "Data Executive"', 'DataExecutive = "Data Executive"'),
        ('TestManager = "Test Executive"', 'TestExecutive = "Test Executive"'),
        ('DataProvider = "Data Owner"', 'DataOwner = "Data Owner"'),
        # String literals
        ('"Data Executive"', '"Data Executive"'),
        ("'Data Executive'", "'Data Executive'"),
        ('"Test Executive"', '"Test Executive"'),
        ("'Test Executive'", "'Test Executive'"),
        ('"Data Owner"', '"Data Owner"'),
        ("'Data Owner'", "'Data Owner'"),
        # UserRole enum references
        ('UserRole.CDO', 'UserRole.DataExecutive'),
        ('UserRole.TestManager', 'UserRole.TestExecutive'),
        ('UserRole.DataProvider', 'UserRole.DataOwner'),
        # UI text
        ('Chief Data Officer', 'Data Executive'),
        ('Test Executive', 'Test Executive'),
        ('Data Owner', 'Data Owner'),
        # Component names
        ('data-owner', 'data-owner'),
    ]
    
    # Find all TypeScript/React files
    ts_files = []
    frontend_dir = "/Users/dineshpatel/code/projects/SynapseDTE/frontend/src"
    for root, dirs, files in os.walk(frontend_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                ts_files.append(os.path.join(root, file))
    
    updated_files = 0
    for filepath in ts_files:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            original_content = content
            for old, new in replacements:
                content = content.replace(old, new)
            
            if content != original_content:
                # Create backup
                backup_path = filepath + '.role_backup'
                with open(backup_path, 'w') as f:
                    f.write(original_content)
                
                # Write updated content
                with open(filepath, 'w') as f:
                    f.write(content)
                
                updated_files += 1
                print(f"  ✅ Updated: {filepath}")
                
        except Exception as e:
            print(f"  ❌ Error updating {filepath}: {e}")
    
    print(f"\n✅ Updated {updated_files} TypeScript/React files")
    return True

def main():
    """Main function to coordinate all updates"""
    print("=" * 60)
    print("Role Renaming Script")
    print("CDO -> Data Executive")
    print("Test Manager -> Test Executive")
    print("Data Provider -> Data Owner")
    print("=" * 60)
    
    # Update database
    if not update_database_roles():
        print("\n❌ Database update failed. Aborting.")
        return
    
    # Update Python files
    if not update_python_files():
        print("\n❌ Python file update failed.")
    
    # Update TypeScript files
    if not update_typescript_files():
        print("\n❌ TypeScript file update failed.")
    
    print("\n" + "=" * 60)
    print("✅ Role renaming completed!")
    print("Next steps:")
    print("1. Restart backend and frontend services")
    print("2. Run tests to verify everything works")
    print("3. Clean up backup files when confirmed")
    print("=" * 60)

if __name__ == "__main__":
    main()