#!/usr/bin/env python3
"""
Extract Database Schema from SQLAlchemy Models
This script analyzes the current models and generates SQL schema files
with proper column organization:
1. Primary keys
2. Foreign keys
3. Business attributes
4. Audit mixin fields
5. Timestamp fields
"""

import os
import sys
import importlib
import inspect
from datetime import datetime
from typing import List, Dict, Any, Set
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.orm import class_mapper
from sqlalchemy.ext.declarative import DeclarativeMeta
from app.models.base import Base
from app.core.database import engine

# Import all models based on what's available in __init__.py
from app.models import (
    # User and RBAC
    User, Role, Permission, RolePermission, UserRole,
    UserPermission, ResourcePermission, RoleHierarchy, Resource,
    
    # Core entities
    Report, ReportAttribute, LOB, DataSource, TestCycle, CycleReport,
    
    # Workflow
    WorkflowPhase, WorkflowActivity, WorkflowExecution,
    WorkflowStep, WorkflowTransition, WorkflowMetrics,
    
    # Planning models
    PlanningVersion, PlanningPDEMapping, CycleReportDataSource,
    
    # Scoping models
    ScopingVersion, ScopingAttribute, ScopingAuditLog,
    
    # Sample Selection
    SampleSelectionVersion, SampleSelectionSample,
    
    # Data Profiling
    DataProfilingRuleVersion, ProfilingRule, DataProfilingUpload,
    
    # Test Execution
    TestExecution, TestExecutionReview, TestExecutionAudit,
    
    # Observations
    ObservationRecord, ObservationImpactAssessment, ObservationResolution,
    
    # Other models
    RegulatoryDataDictionary, UniversalAssignment,
    CycleReportDocument, ActivityDefinition,
    SLAConfiguration, LLMAuditLog, AuditLog,
    TestReportSection, TestReportGeneration
)

class SchemaExtractor:
    """Extract and organize database schema"""
    
    def __init__(self):
        self.models = []
        self.tables = {}
        self.audit_columns = {
            'created_by_id', 'updated_by_id', 
            'created_by', 'updated_by',
            'created_at', 'updated_at'
        }
        self.timestamp_columns = {
            'created_at', 'updated_at', 'deleted_at',
            'submitted_at', 'approved_at', 'rejected_at',
            'completed_at', 'started_at', 'ended_at'
        }
        
    def discover_models(self):
        """Discover all SQLAlchemy models"""
        # Get all classes that inherit from Base
        for name, obj in globals().items():
            if (inspect.isclass(obj) and 
                issubclass(obj, Base) and 
                obj != Base and
                hasattr(obj, '__tablename__')):
                self.models.append(obj)
                
        # Also check all imported model modules
        models_path = project_root / 'app' / 'models'
        for py_file in models_path.glob('*.py'):
            if py_file.name.startswith('__') or 'backup' in str(py_file):
                continue
                
            module_name = f"app.models.{py_file.stem}"
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, Base) and 
                        obj != Base and
                        hasattr(obj, '__tablename__') and
                        obj not in self.models):
                        self.models.append(obj)
            except Exception as e:
                print(f"Warning: Could not import {module_name}: {e}")
                
        print(f"Discovered {len(self.models)} models")
        
    def categorize_columns(self, model):
        """Categorize columns for a model"""
        mapper = class_mapper(model)
        
        primary_keys = []
        foreign_keys = []
        business_attrs = []
        audit_fields = []
        timestamp_fields = []
        
        for column in mapper.columns:
            col_name = column.name
            
            # Primary keys
            if column.primary_key:
                primary_keys.append(column)
            # Foreign keys
            elif column.foreign_keys:
                foreign_keys.append(column)
            # Audit fields
            elif col_name in self.audit_columns and 'by' in col_name:
                audit_fields.append(column)
            # Timestamp fields
            elif col_name in self.timestamp_columns or col_name.endswith('_at'):
                timestamp_fields.append(column)
            # Business attributes
            else:
                business_attrs.append(column)
                
        return {
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'business_attrs': business_attrs,
            'audit_fields': audit_fields,
            'timestamp_fields': timestamp_fields
        }
        
    def generate_create_table_sql(self, model):
        """Generate CREATE TABLE SQL for a model"""
        table_name = model.__tablename__
        categorized = self.categorize_columns(model)
        
        sql_lines = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]
        column_definitions = []
        
        # Process columns in order
        all_columns = (
            categorized['primary_keys'] +
            categorized['foreign_keys'] +
            categorized['business_attrs'] +
            categorized['audit_fields'] +
            categorized['timestamp_fields']
        )
        
        for column in all_columns:
            col_def = self._get_column_definition(column)
            column_definitions.append(f"    {col_def}")
            
        # Add constraints
        constraints = self._get_table_constraints(model)
        if constraints:
            column_definitions.extend([f"    {c}" for c in constraints])
            
        sql_lines.append(",\n".join(column_definitions))
        sql_lines.append(");")
        
        # Add indexes
        indexes = self._get_table_indexes(model)
        if indexes:
            sql_lines.append("")
            sql_lines.extend(indexes)
            
        # Add comments
        sql_lines.insert(0, f"-- Table: {table_name}")
        sql_lines.insert(1, f"-- Model: {model.__name__}")
        sql_lines.insert(2, "")
        
        return "\n".join(sql_lines)
        
    def _get_column_definition(self, column):
        """Get SQL column definition"""
        col_type = self._get_sql_type(column.type)
        nullable = "NULL" if column.nullable else "NOT NULL"
        default = ""
        
        if column.default is not None:
            if hasattr(column.default, 'arg'):
                default_val = column.default.arg
                if callable(default_val):
                    if default_val.__name__ == 'utcnow':
                        default = " DEFAULT CURRENT_TIMESTAMP"
                    elif default_val.__name__ == 'generate_uuid':
                        default = " DEFAULT gen_random_uuid()"
                else:
                    default = f" DEFAULT {default_val}"
                    
        return f"{column.name} {col_type} {nullable}{default}"
        
    def _get_sql_type(self, col_type):
        """Convert SQLAlchemy type to PostgreSQL type"""
        type_name = col_type.__class__.__name__
        
        type_mapping = {
            'Integer': 'INTEGER',
            'BigInteger': 'BIGINT',
            'String': f'VARCHAR({getattr(col_type, "length", 255)})',
            'Text': 'TEXT',
            'Boolean': 'BOOLEAN',
            'DateTime': 'TIMESTAMP WITH TIME ZONE',
            'Date': 'DATE',
            'Time': 'TIME',
            'Float': 'FLOAT',
            'Numeric': 'DECIMAL',
            'JSON': 'JSONB',
            'UUID': 'UUID',
            'Enum': 'VARCHAR(50)',  # Simplified for now
        }
        
        return type_mapping.get(type_name, 'VARCHAR(255)')
        
    def _get_table_constraints(self, model):
        """Get table constraints"""
        constraints = []
        mapper = class_mapper(model)
        
        # Primary key constraint
        pk_columns = [c.name for c in mapper.columns if c.primary_key]
        if pk_columns:
            constraints.append(f"CONSTRAINT {model.__tablename__}_pkey PRIMARY KEY ({', '.join(pk_columns)})")
            
        # Foreign key constraints
        for column in mapper.columns:
            if column.foreign_keys:
                for fk in column.foreign_keys:
                    fk_name = f"fk_{model.__tablename__}_{column.name}"
                    ref_table = fk.column.table.name
                    ref_column = fk.column.name
                    constraints.append(
                        f"CONSTRAINT {fk_name} FOREIGN KEY ({column.name}) "
                        f"REFERENCES {ref_table}({ref_column}) ON DELETE CASCADE"
                    )
                    
        # Unique constraints
        if hasattr(model, '__table_args__'):
            table_args = model.__table_args__
            if isinstance(table_args, tuple):
                for arg in table_args:
                    if hasattr(arg, 'name') and hasattr(arg, 'columns'):
                        if 'unique' in arg.name or hasattr(arg, 'unique') and arg.unique:
                            col_names = [c.name for c in arg.columns]
                            constraints.append(
                                f"CONSTRAINT {arg.name} UNIQUE ({', '.join(col_names)})"
                            )
                            
        return constraints
        
    def _get_table_indexes(self, model):
        """Get table indexes"""
        indexes = []
        table_name = model.__tablename__
        
        # Add indexes for foreign keys
        mapper = class_mapper(model)
        for column in mapper.columns:
            if column.foreign_keys and not column.primary_key:
                idx_name = f"idx_{table_name}_{column.name}"
                indexes.append(f"CREATE INDEX {idx_name} ON {table_name}({column.name});")
                
        # Add indexes for commonly queried fields
        common_indexed_fields = {'email', 'username', 'code', 'name', 'status', 'type'}
        for column in mapper.columns:
            if column.name in common_indexed_fields and not column.primary_key:
                idx_name = f"idx_{table_name}_{column.name}"
                indexes.append(f"CREATE INDEX {idx_name} ON {table_name}({column.name});")
                
        # Add composite indexes for audit fields
        audit_cols = [c.name for c in mapper.columns if c.name in self.audit_columns]
        if 'created_at' in audit_cols:
            idx_name = f"idx_{table_name}_created_at"
            indexes.append(f"CREATE INDEX {idx_name} ON {table_name}(created_at DESC);")
            
        return indexes
        
    def generate_schema_files(self, output_dir: Path):
        """Generate all schema files"""
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate main schema file
        schema_file = output_dir / "01_schema.sql"
        with open(schema_file, 'w') as f:
            f.write("-- SynapseDTE Database Schema\n")
            f.write(f"-- Generated: {datetime.now()}\n")
            f.write("-- This file contains the complete database schema\n\n")
            
            # Add UUID extension
            f.write("-- Enable required extensions\n")
            f.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
            f.write("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n")
            
            # Group tables by category
            table_categories = {
                'Core': ['users', 'roles', 'permissions', 'role_permissions', 'user_roles'],
                'Reports': ['reports', 'report_attributes', 'report_inventory'],
                'LOB': ['lobs', 'data_owners', 'data_owner_lob_assignments'],
                'Test Cycles': ['test_cycles', 'cycle_reports'],
                'Workflow': ['workflow_phases', 'workflow_activities', 'workflow_tracking'],
                # Add more categories
            }
            
            # Track which tables have been written
            written_tables = set()
            
            # Write tables by category
            for category, table_list in table_categories.items():
                f.write(f"\n-- =====================\n")
                f.write(f"-- {category} Tables\n")
                f.write(f"-- =====================\n\n")
                
                for model in self.models:
                    if model.__tablename__ in table_list:
                        f.write(self.generate_create_table_sql(model))
                        f.write("\n\n")
                        written_tables.add(model.__tablename__)
                        
            # Write any remaining tables
            remaining_models = [m for m in self.models if m.__tablename__ not in written_tables]
            if remaining_models:
                f.write(f"\n-- =====================\n")
                f.write(f"-- Other Tables\n")
                f.write(f"-- =====================\n\n")
                
                for model in remaining_models:
                    f.write(self.generate_create_table_sql(model))
                    f.write("\n\n")
                    
        print(f"Schema file generated: {schema_file}")
        
        # Generate drop script
        drop_file = output_dir / "00_drop_all.sql"
        with open(drop_file, 'w') as f:
            f.write("-- Drop all tables (use with caution!)\n")
            f.write("-- This script drops all tables in reverse dependency order\n\n")
            
            # Reverse the order for dropping
            for model in reversed(self.models):
                f.write(f"DROP TABLE IF EXISTS {model.__tablename__} CASCADE;\n")
                
        print(f"Drop script generated: {drop_file}")
        
def main():
    """Main execution"""
    extractor = SchemaExtractor()
    extractor.discover_models()
    
    output_dir = Path(__file__).parent
    extractor.generate_schema_files(output_dir)
    
    print("\nSchema extraction complete!")
    print(f"Files generated in: {output_dir}")

if __name__ == "__main__":
    main()