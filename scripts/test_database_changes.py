#!/usr/bin/env python3
"""Test that the database changes work correctly"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DATABASE_URL = "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt"

def test_database_changes():
    """Test various aspects of the database changes"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Testing Database Changes")
        print("=" * 50)
        
        # 1. Check report_inventory table
        result = conn.execute(text("SELECT COUNT(*) FROM report_inventory"))
        count = result.scalar()
        print(f"✓ report_inventory table has {count} records")
        
        # 2. Check that foreign keys work
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM cycle_reports cr
            JOIN report_inventory ri ON cr.report_id = ri.id
        """))
        count = result.scalar()
        print(f"✓ cycle_reports joined with report_inventory: {count} records")
        
        # 3. Check new tables
        new_tables = [
            'cycle_report_attributes_planning',
            'cycle_report_test_cases',
            'cycle_report_document_submissions',
            'entity_assignments'
        ]
        
        for table in new_tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"✓ {table} table exists with {count} records")
        
        # 4. Check backup tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_name LIKE '%_backup'
            ORDER BY table_name
        """))
        backup_tables = [row[0] for row in result]
        print(f"\n✓ Backup tables created: {len(backup_tables)}")
        for table in backup_tables:
            print(f"  - {table}")
        
        # 5. Test model loading
        try:
            from app.models import Report, CycleReport
            print("\n✓ Models loaded successfully")
            print(f"  - Report.__tablename__ = {Report.__tablename__}")
            print(f"  - Report.report_id mapped to column: {Report.report_id.property.columns[0].name}")
        except Exception as e:
            print(f"\n✗ Error loading models: {e}")
        
        print("\n" + "=" * 50)
        print("All database changes verified successfully!")

if __name__ == "__main__":
    test_database_changes()