"""Apply FR Y-14M Schedule D.1 table migration"""

import subprocess
import sys
import os

def run_migration():
    """Run the Alembic migration to create fry14m_scheduled1_data table"""
    try:
        # Change to project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(project_root)
        
        print("Running FR Y-14M Schedule D.1 table migration...")
        
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Migration completed successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed!")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()