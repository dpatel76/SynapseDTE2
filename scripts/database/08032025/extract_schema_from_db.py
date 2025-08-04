#!/usr/bin/env python3
"""
Extract Database Schema from Existing Database
This script connects to the current database and extracts the actual schema
with proper column organization.
"""

import asyncio
import asyncpg
from pathlib import Path
from datetime import datetime

# Database configuration - READ ONLY
DB_CONFIG = {
    'host': 'localhost',
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password',
    'port': 5432
}

class SchemaExtractor:
    """Extract schema from existing database"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent
        self.tables = {}
        
    async def extract_schema(self):
        """Extract complete schema from database"""
        conn = await asyncpg.connect(**DB_CONFIG)
        
        try:
            # Get all tables
            tables_query = """
                SELECT 
                    t.table_name,
                    obj_description(c.oid) as table_comment
                FROM information_schema.tables t
                JOIN pg_catalog.pg_class c ON c.relname = t.table_name
                WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name
            """
            
            tables = await conn.fetch(tables_query)
            print(f"Found {len(tables)} tables in database")
            
            # Generate schema file
            schema_file = self.output_dir / "01_schema.sql"
            with open(schema_file, 'w') as f:
                f.write("-- SynapseDTE Database Schema\n")
                f.write(f"-- Generated from existing database: {DB_CONFIG['database']}\n")
                f.write(f"-- Date: {datetime.now()}\n\n")
                
                # Add extensions
                f.write("-- Enable required extensions\n")
                f.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
                f.write("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n")
                
                # Process each table
                for table_record in tables:
                    table_name = table_record['table_name']
                    print(f"Processing table: {table_name}")
                    
                    # Get table DDL
                    create_sql = await self._get_table_ddl(conn, table_name)
                    
                    f.write(f"\n-- Table: {table_name}\n")
                    if table_record['table_comment']:
                        f.write(f"-- {table_record['table_comment']}\n")
                    f.write(create_sql)
                    f.write("\n")
                    
                    # Get indexes
                    indexes = await self._get_table_indexes(conn, table_name)
                    if indexes:
                        f.write(f"\n-- Indexes for {table_name}\n")
                        for idx in indexes:
                            f.write(idx + ";\n")
                        f.write("\n")
                        
            print(f"\nSchema exported to: {schema_file}")
            
            # Generate drop script
            await self._generate_drop_script(tables)
            
        finally:
            await conn.close()
            
    async def _get_table_ddl(self, conn, table_name: str) -> str:
        """Get CREATE TABLE statement with organized columns"""
        # Get column information
        columns_query = """
            SELECT 
                a.attname as column_name,
                pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
                a.attnotnull as not_null,
                pg_get_expr(d.adbin, d.adrelid) as default_value,
                CASE WHEN p.contype = 'p' THEN true ELSE false END as is_primary_key,
                CASE WHEN f.contype = 'f' THEN true ELSE false END as is_foreign_key,
                f.confrelid::regclass as foreign_table,
                a.attnum as ordinal_position,
                col_description(c.oid, a.attnum) as column_comment,
                'business' as column_category  -- Simplified for now
            FROM pg_catalog.pg_attribute a
            JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
            LEFT JOIN pg_catalog.pg_attrdef d ON (a.attrelid, a.attnum) = (d.adrelid, d.adnum)
            LEFT JOIN pg_catalog.pg_constraint p ON p.conrelid = c.oid AND a.attnum = ANY(p.conkey) AND p.contype = 'p'
            LEFT JOIN pg_catalog.pg_constraint f ON f.conrelid = c.oid AND a.attnum = ANY(f.conkey) AND f.contype = 'f'
            WHERE c.relname = $1
            AND a.attnum > 0
            AND NOT a.attisdropped
            ORDER BY 
                CASE 
                    WHEN p.contype = 'p' THEN 1  -- Primary keys first
                    WHEN f.contype = 'f' THEN 2  -- Foreign keys second
                    WHEN a.attname IN ('created_by_id', 'updated_by_id') THEN 4  -- Audit fields
                    WHEN a.attname LIKE '%_at' THEN 5  -- Timestamp fields
                    ELSE 3  -- Business attributes
                END,
                a.attnum
        """
        
        columns = await conn.fetch(columns_query, table_name)
        
        # Build CREATE TABLE statement
        create_lines = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]
        column_defs = []
        
        for col in columns:
            col_def = f"    {col['column_name']} {col['data_type']}"
            
            if col['not_null']:
                col_def += " NOT NULL"
                
            if col['default_value']:
                col_def += f" DEFAULT {col['default_value']}"
                
            column_defs.append(col_def)
            
        # Get constraints
        constraints = await self._get_table_constraints(conn, table_name)
        if constraints:
            column_defs.extend(constraints)
            
        create_lines.append(",\n".join(column_defs))
        create_lines.append(");")
        
        return "\n".join(create_lines)
        
    async def _get_table_constraints(self, conn, table_name: str) -> list:
        """Get table constraints"""
        constraints_query = """
            SELECT 
                con.conname as constraint_name,
                con.contype as constraint_type,
                pg_get_constraintdef(con.oid) as constraint_def
            FROM pg_catalog.pg_constraint con
            JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
            WHERE c.relname = $1
            AND con.contype IN ('p', 'f', 'u', 'c')
            ORDER BY 
                CASE con.contype 
                    WHEN 'p' THEN 1 
                    WHEN 'f' THEN 2 
                    WHEN 'u' THEN 3 
                    WHEN 'c' THEN 4 
                END
        """
        
        constraints = await conn.fetch(constraints_query, table_name)
        
        constraint_defs = []
        for con in constraints:
            constraint_defs.append(f"    CONSTRAINT {con['constraint_name']} {con['constraint_def']}")
            
        return constraint_defs
        
    async def _get_table_indexes(self, conn, table_name: str) -> list:
        """Get table indexes"""
        indexes_query = """
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = $1
            AND schemaname = 'public'
            AND indexname NOT IN (
                SELECT conname 
                FROM pg_constraint 
                WHERE contype = 'p'
            )
            ORDER BY indexname
        """
        
        indexes = await conn.fetch(indexes_query, table_name)
        return [idx['indexdef'] for idx in indexes]
        
    async def _generate_drop_script(self, tables):
        """Generate drop script"""
        drop_file = self.output_dir / "00_drop_all.sql"
        
        with open(drop_file, 'w') as f:
            f.write("-- Drop all tables (use with caution!)\n")
            f.write(f"-- Generated: {datetime.now()}\n")
            f.write("-- This script drops all tables in reverse dependency order\n\n")
            
            # Reverse order for dropping
            for table in reversed(tables):
                f.write(f"DROP TABLE IF EXISTS {table['table_name']} CASCADE;\n")
                
        print(f"Drop script generated: {drop_file}")
        
async def main():
    """Main execution"""
    extractor = SchemaExtractor()
    await extractor.extract_schema()
    
if __name__ == "__main__":
    asyncio.run(main())