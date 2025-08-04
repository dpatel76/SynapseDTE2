#!/usr/bin/env python3
"""
Extract DDL from database using information_schema
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

class DDLExtractor:
    """Extract DDL from database"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent
        
    async def extract_ddl(self):
        """Extract complete DDL"""
        conn = await asyncpg.connect(**DB_CONFIG)
        
        try:
            schema_file = self.output_dir / "01_schema_complete.sql"
            with open(schema_file, 'w') as f:
                f.write("-- SynapseDTE Database Schema\n")
                f.write(f"-- Generated from: {DB_CONFIG['database']}\n")
                f.write(f"-- Date: {datetime.now()}\n\n")
                
                # Add extensions
                f.write("-- Enable required extensions\n")
                f.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
                f.write("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n")
                
                # Get all sequences
                seq_query = """
                    SELECT 
                        schemaname,
                        sequencename,
                        last_value,
                        increment_by
                    FROM pg_sequences
                    WHERE schemaname = 'public'
                    ORDER BY sequencename
                """
                sequences = await conn.fetch(seq_query)
                
                if sequences:
                    f.write("-- Sequences\n")
                    for seq in sequences:
                        f.write(f"CREATE SEQUENCE IF NOT EXISTS {seq['sequencename']};\n")
                    f.write("\n")
                
                # Get all tables
                tables_query = """
                    SELECT DISTINCT 
                        c.relname as table_name
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relkind = 'r'
                    AND n.nspname = 'public'
                    ORDER BY c.relname
                """
                
                tables = await conn.fetch(tables_query)
                
                for table in tables:
                    table_name = table['table_name']
                    print(f"Processing table: {table_name}")
                    
                    # Get columns
                    columns_query = """
                        SELECT 
                            a.attname as column_name,
                            pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
                            a.attnotnull as not_null,
                            pg_get_expr(d.adbin, d.adrelid) as default_value,
                            a.attnum as ordinal_position
                        FROM pg_catalog.pg_attribute a
                        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
                        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                        LEFT JOIN pg_catalog.pg_attrdef d ON (a.attrelid, a.attnum) = (d.adrelid, d.adnum)
                        WHERE c.relname = $1
                        AND n.nspname = 'public'
                        AND a.attnum > 0
                        AND NOT a.attisdropped
                        ORDER BY a.attnum
                    """
                    
                    columns = await conn.fetch(columns_query, table_name)
                    
                    if columns:
                        f.write(f"-- Table: {table_name}\n")
                        f.write(f"CREATE TABLE IF NOT EXISTS {table_name} (\n")
                        
                        col_defs = []
                        for col in columns:
                            col_def = f"    {col['column_name']} {col['data_type']}"
                            if col['not_null']:
                                col_def += " NOT NULL"
                            if col['default_value']:
                                col_def += f" DEFAULT {col['default_value']}"
                            col_defs.append(col_def)
                            
                        # Get constraints
                        constraints_query = """
                            SELECT 
                                con.conname as constraint_name,
                                con.contype as constraint_type,
                                pg_get_constraintdef(con.oid) as constraint_def
                            FROM pg_catalog.pg_constraint con
                            JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
                            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                            WHERE c.relname = $1
                            AND n.nspname = 'public'
                            ORDER BY 
                                CASE con.contype 
                                    WHEN 'p' THEN 1 
                                    WHEN 'f' THEN 2 
                                    WHEN 'u' THEN 3 
                                    WHEN 'c' THEN 4 
                                END
                        """
                        
                        constraints = await conn.fetch(constraints_query, table_name)
                        
                        for con in constraints:
                            col_defs.append(f"    CONSTRAINT {con['constraint_name']} {con['constraint_def']}")
                            
                        f.write(",\n".join(col_defs))
                        f.write("\n);\n\n")
                        
                        # Get indexes
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
                                WHERE contype IN ('p', 'u', 'f')
                            )
                            ORDER BY indexname
                        """
                        
                        indexes = await conn.fetch(indexes_query, table_name)
                        
                        if indexes:
                            f.write(f"-- Indexes for {table_name}\n")
                            for idx in indexes:
                                f.write(f"{idx['indexdef']};\n")
                            f.write("\n")
                            
            print(f"\nSchema extracted to: {schema_file}")
            
            # Also generate a simpler version without sequences
            await self._generate_simple_schema(conn)
            
        finally:
            await conn.close()
            
    async def _generate_simple_schema(self, conn):
        """Generate a simpler schema file without sequence dependencies"""
        schema_file = self.output_dir / "01_schema_simple.sql"
        
        with open(schema_file, 'w') as f:
            f.write("-- SynapseDTE Database Schema (Simplified)\n")
            f.write(f"-- Generated from: {DB_CONFIG['database']}\n")
            f.write(f"-- Date: {datetime.now()}\n\n")
            
            # Add extensions
            f.write("-- Enable required extensions\n")
            f.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
            f.write("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n")
            
            # Get tables with SERIAL columns simplified
            tables_query = """
                SELECT DISTINCT 
                    c.relname as table_name
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relkind = 'r'
                AND n.nspname = 'public'
                ORDER BY c.relname
            """
            
            tables = await conn.fetch(tables_query)
            
            for table in tables:
                table_name = table['table_name']
                
                # Get columns and replace sequence defaults with SERIAL
                columns_query = """
                    SELECT 
                        a.attname as column_name,
                        pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
                        a.attnotnull as not_null,
                        pg_get_expr(d.adbin, d.adrelid) as default_value,
                        a.attnum as ordinal_position,
                        CASE 
                            WHEN pg_get_expr(d.adbin, d.adrelid) LIKE 'nextval%' 
                                AND a.atttypid = 23 THEN 'SERIAL'
                            WHEN pg_get_expr(d.adbin, d.adrelid) LIKE 'nextval%' 
                                AND a.atttypid = 20 THEN 'BIGSERIAL'
                            ELSE NULL
                        END as serial_type
                    FROM pg_catalog.pg_attribute a
                    JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
                    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                    LEFT JOIN pg_catalog.pg_attrdef d ON (a.attrelid, a.attnum) = (d.adrelid, d.adnum)
                    WHERE c.relname = $1
                    AND n.nspname = 'public'
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                    ORDER BY a.attnum
                """
                
                columns = await conn.fetch(columns_query, table_name)
                
                if columns:
                    f.write(f"-- Table: {table_name}\n")
                    f.write(f"CREATE TABLE IF NOT EXISTS {table_name} (\n")
                    
                    col_defs = []
                    for col in columns:
                        if col['serial_type']:
                            col_def = f"    {col['column_name']} {col['serial_type']}"
                        else:
                            col_def = f"    {col['column_name']} {col['data_type']}"
                            if col['not_null']:
                                col_def += " NOT NULL"
                            if col['default_value'] and not col['default_value'].startswith('nextval'):
                                col_def += f" DEFAULT {col['default_value']}"
                        col_defs.append(col_def)
                        
                    f.write(",\n".join(col_defs))
                    f.write("\n);\n\n")
                    
        print(f"Simple schema extracted to: {schema_file}")

async def main():
    """Main execution"""
    extractor = DDLExtractor()
    await extractor.extract_ddl()
    
if __name__ == "__main__":
    asyncio.run(main())