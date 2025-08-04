#!/usr/bin/env python3
"""
Script to check which tables are missing audit columns (created_by_id, updated_by_id)
and generate SQL to add them.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.models import *  # Import all models to ensure they're registered
from app.models.base import AuditableBaseModel, AuditableCustomPKModel
from app.models.audit_mixin import AuditMixin


def get_models_with_audit_mixin():
    """Get all SQLAlchemy models that use AuditMixin"""
    models_with_audit = []
    
    # Import all model modules to ensure they're loaded
    import app.models
    from app.core.database import Base
    
    # Get all mapped classes
    for mapper in Base.registry.mappers:
        model_class = mapper.class_
        
        # Check if this model uses AuditMixin
        if hasattr(model_class, '__mro__') and AuditMixin in model_class.__mro__:
            table_name = model_class.__tablename__
            models_with_audit.append({
                'model': model_class.__name__,
                'table': table_name
            })
    
    return models_with_audit


def check_audit_columns(engine):
    """Check which tables are missing audit columns"""
    inspector = inspect(engine)
    
    # Get all tables
    all_tables = inspector.get_table_names()
    
    # Get models that should have audit columns
    audit_models = get_models_with_audit_mixin()
    audit_tables = {m['table'] for m in audit_models}
    
    missing_columns = []
    
    for table_name in audit_tables:
        if table_name not in all_tables:
            print(f"⚠️  Table '{table_name}' does not exist in database")
            continue
            
        columns = {col['name'] for col in inspector.get_columns(table_name)}
        
        missing_created = 'created_by_id' not in columns
        missing_updated = 'updated_by_id' not in columns
        
        if missing_created or missing_updated:
            missing_columns.append({
                'table': table_name,
                'missing_created_by': missing_created,
                'missing_updated_by': missing_updated,
                'model': next((m['model'] for m in audit_models if m['table'] == table_name), 'Unknown')
            })
    
    return missing_columns


def generate_sql_fixes(missing_columns):
    """Generate SQL to add missing columns"""
    if not missing_columns:
        return "-- No missing audit columns found!"
    
    sql_statements = []
    sql_statements.append("-- SQL to add missing audit columns")
    sql_statements.append("BEGIN;")
    sql_statements.append("")
    
    for item in missing_columns:
        table = item['table']
        sql_statements.append(f"-- Table: {table} (Model: {item['model']})")
        
        if item['missing_created_by']:
            sql_statements.append(f"ALTER TABLE {table} ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;")
            sql_statements.append(f"COMMENT ON COLUMN {table}.created_by_id IS 'ID of user who created this record';")
            sql_statements.append(f"CREATE INDEX idx_{table}_created_by ON {table}(created_by_id);")
        
        if item['missing_updated_by']:
            sql_statements.append(f"ALTER TABLE {table} ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;")
            sql_statements.append(f"COMMENT ON COLUMN {table}.updated_by_id IS 'ID of user who last updated this record';")
            sql_statements.append(f"CREATE INDEX idx_{table}_updated_by ON {table}(updated_by_id);")
        
        sql_statements.append("")
    
    sql_statements.append("COMMIT;")
    
    return "\n".join(sql_statements)


def main():
    """Main function"""
    print("🔍 Checking for missing audit columns...\n")
    
    # Create database engine
    engine = create_engine(settings.database_url)
    
    # Get models with audit mixin
    audit_models = get_models_with_audit_mixin()
    print(f"📊 Found {len(audit_models)} models using AuditMixin:")
    for model in sorted(audit_models, key=lambda x: x['table']):
        print(f"   - {model['model']} → {model['table']}")
    print()
    
    # Check for missing columns
    missing_columns = check_audit_columns(engine)
    
    if not missing_columns:
        print("✅ All tables have the required audit columns!")
        return
    
    print(f"❌ Found {len(missing_columns)} tables missing audit columns:\n")
    
    for item in missing_columns:
        status = []
        if item['missing_created_by']:
            status.append("created_by_id")
        if item['missing_updated_by']:
            status.append("updated_by_id")
        
        print(f"   - {item['table']} (missing: {', '.join(status)})")
    
    print("\n" + "="*60)
    print("Generated SQL to fix missing columns:")
    print("="*60 + "\n")
    
    sql_fix = generate_sql_fixes(missing_columns)
    print(sql_fix)
    
    # Optionally save to file
    output_file = project_root / "scripts" / "fix_missing_audit_columns.sql"
    with open(output_file, 'w') as f:
        f.write(sql_fix)
    
    print(f"\n💾 SQL saved to: {output_file}")


if __name__ == "__main__":
    main()