#!/usr/bin/env python3
"""
Extract Complete Database Schema including sequences
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

class CompleteSchemaExtractor:
    """Extract complete schema from database"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent
        
    async def extract_schema(self):
        """Extract complete schema from database"""
        conn = await asyncpg.connect(**DB_CONFIG)
        
        try:
            schema_file = self.output_dir / "01_complete_schema.sql"
            with open(schema_file, 'w') as f:
                f.write("-- SynapseDTE Complete Database Schema\n")
                f.write(f"-- Generated from existing database: {DB_CONFIG['database']}\n")
                f.write(f"-- Date: {datetime.now()}\n\n")
                
                # Add extensions
                f.write("-- Enable required extensions\n")
                f.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
                f.write("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n")
                
                # Extract sequences first
                sequences = await self._extract_sequences(conn)
                if sequences:
                    f.write("-- Sequences\n")
                    for seq in sequences:
                        f.write(seq + "\n")
                    f.write("\n")
                
                # Extract tables with proper DDL
                tables = await self._extract_tables(conn)
                for table_ddl in tables:
                    f.write(table_ddl + "\n\n")
                    
                # Extract indexes
                indexes = await self._extract_indexes(conn)
                if indexes:
                    f.write("-- Indexes\n")
                    for idx in indexes:
                        f.write(idx + "\n")
                        
            print(f"Complete schema exported to: {schema_file}")
            
        finally:
            await conn.close()
            
    async def _extract_sequences(self, conn) -> list:
        """Extract all sequences"""
        query = """
            SELECT 
                'CREATE SEQUENCE IF NOT EXISTS ' || sequence_name || 
                ' START WITH ' || COALESCE(start_value::text, '1') ||
                ' INCREMENT BY ' || increment ||
                ' MINVALUE ' || COALESCE(min_value::text, '1') ||
                ' MAXVALUE ' || COALESCE(max_value::text, '9223372036854775807') ||
                CASE WHEN cycle_option = 'YES' THEN ' CYCLE' ELSE ' NO CYCLE' END ||
                ';' as seq_ddl
            FROM information_schema.sequences
            WHERE sequence_schema = 'public'
            ORDER BY sequence_name
        """
        
        result = await conn.fetch(query)
        return [row['seq_ddl'] for row in result]
        
    async def _extract_tables(self, conn) -> list:
        """Extract all tables with constraints"""
        # Get all tables
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        
        tables = await conn.fetch(tables_query)
        table_ddls = []
        
        for table in tables:
            table_name = table['table_name']
            
            # Use pg_dump style query to get table DDL
            ddl_query = f"""
                SELECT 
                    'CREATE TABLE IF NOT EXISTS ' || quote_ident('{table_name}') || ' (' ||
                    string_agg(
                        E'\\n    ' || column_definition || 
                        CASE WHEN constraint_defs != '' THEN '' ELSE '' END,
                        ','
                        ORDER BY ordinal_position
                    ) ||
                    CASE 
                        WHEN constraint_defs != '' THEN 
                            ',' || E'\\n    ' || constraint_defs 
                        ELSE '' 
                    END ||
                    E'\\n);' as create_table
                FROM (
                    SELECT 
                        a.attnum as ordinal_position,
                        quote_ident(a.attname) || ' ' ||
                        pg_catalog.format_type(a.atttypid, a.atttypmod) ||
                        CASE WHEN a.attnotnull THEN ' NOT NULL' ELSE '' END ||
                        CASE 
                            WHEN pg_get_expr(d.adbin, d.adrelid) IS NOT NULL 
                            THEN ' DEFAULT ' || pg_get_expr(d.adbin, d.adrelid)
                            ELSE ''
                        END as column_definition,
                        (
                            SELECT string_agg(
                                'CONSTRAINT ' || quote_ident(con.conname) || ' ' || 
                                pg_get_constraintdef(con.oid),
                                E',\\n    '
                            )
                            FROM pg_constraint con
                            WHERE con.conrelid = c.oid
                        ) as constraint_defs
                    FROM pg_catalog.pg_attribute a
                    JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
                    LEFT JOIN pg_catalog.pg_attrdef d ON (a.attrelid, a.attnum) = (d.adrelid, d.adnum)
                    WHERE c.relname = '{table_name}'
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                ) as cols
                GROUP BY constraint_defs
            """
            
            result = await conn.fetchval(ddl_query)
            if result:
                table_ddls.append(f"-- Table: {table_name}\n{result}")
                
        return table_ddls
        
    async def _extract_indexes(self, conn) -> list:
        """Extract all indexes"""
        query = """
            SELECT 
                indexdef || ';' as idx_ddl
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND indexname NOT IN (
                SELECT conname 
                FROM pg_constraint 
                WHERE contype IN ('p', 'u')
            )
            ORDER BY tablename, indexname
        """
        
        result = await conn.fetch(query)
        return [row['idx_ddl'] for row in result]

async def main():
    """Main execution"""
    extractor = CompleteSchemaExtractor()
    await extractor.extract_schema()
    
if __name__ == "__main__":
    asyncio.run(main())