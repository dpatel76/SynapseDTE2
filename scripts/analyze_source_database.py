#!/usr/bin/env python3
"""
Comprehensive source database analysis
Gets complete list of all tables, their structure, and record counts
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def analyze_source_database():
    """Analyze source database completely"""
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL', 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
    
    # Parse connection info
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    
    conn = await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip('/')
    )
    
    try:
        logger.info("Analyzing source database...")
        logger.info("="*80)
        
        # Get ALL tables from the database
        tables_query = """
        SELECT 
            t.table_name,
            obj_description(c.oid) as table_comment
        FROM information_schema.tables t
        JOIN pg_class c ON c.relname = t.table_name
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
        WHERE t.table_schema = 'public' 
        AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name;
        """
        
        tables = await conn.fetch(tables_query)
        logger.info(f"Found {len(tables)} tables in source database")
        logger.info("="*80)
        
        # Get record count for each table
        table_info = []
        total_records = 0
        
        for table in tables:
            table_name = table['table_name']
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                total_records += count
                
                # Get column count
                col_count = await conn.fetchval(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                """)
                
                # Get if table has primary key
                has_pk = await conn.fetchval(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.table_constraints 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table_name}' 
                        AND constraint_type = 'PRIMARY KEY'
                    )
                """)
                
                # Get foreign key count
                fk_count = await conn.fetchval(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.table_constraints 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}' 
                    AND constraint_type = 'FOREIGN KEY'
                """)
                
                table_info.append({
                    'name': table_name,
                    'records': count,
                    'columns': col_count,
                    'has_pk': has_pk,
                    'fk_count': fk_count,
                    'comment': table['table_comment']
                })
                
            except Exception as e:
                logger.error(f"Error analyzing table {table_name}: {e}")
                table_info.append({
                    'name': table_name,
                    'records': -1,
                    'columns': 0,
                    'has_pk': False,
                    'fk_count': 0,
                    'comment': f"ERROR: {str(e)}"
                })
        
        # Sort by number of foreign keys (tables with no FKs first)
        table_info.sort(key=lambda x: (x['fk_count'], x['name']))
        
        # Print detailed report
        logger.info(f"\n{'Table Name':<40} {'Records':>10} {'Columns':>8} {'PK':>4} {'FKs':>4}")
        logger.info("-"*70)
        
        for info in table_info:
            pk_str = "Yes" if info['has_pk'] else "No"
            logger.info(f"{info['name']:<40} {info['records']:>10,} {info['columns']:>8} {pk_str:>4} {info['fk_count']:>4}")
        
        logger.info("-"*70)
        logger.info(f"Total tables: {len(table_info)}")
        logger.info(f"Total records: {total_records:,}")
        
        # Get ENUM types
        logger.info("\n" + "="*80)
        logger.info("PostgreSQL ENUM Types:")
        logger.info("="*80)
        
        enum_query = """
        SELECT 
            t.typname as enum_name,
            array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid  
        JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = 'public'
        GROUP BY t.typname
        ORDER BY t.typname;
        """
        
        enums = await conn.fetch(enum_query)
        for enum in enums:
            logger.info(f"\n{enum['enum_name']}:")
            for value in enum['enum_values']:
                logger.info(f"  - {value}")
        
        # Save table list to file for migration script
        with open('scripts/source_tables_list.txt', 'w') as f:
            f.write("# Source Database Tables\n")
            f.write(f"# Total: {len(table_info)} tables\n")
            f.write("# Format: table_name|record_count|column_count|has_pk|fk_count\n\n")
            for info in table_info:
                f.write(f"{info['name']}|{info['records']}|{info['columns']}|{info['has_pk']}|{info['fk_count']}\n")
        
        logger.info(f"\nTable list saved to: scripts/source_tables_list.txt")
        
        # Identify table dependencies
        logger.info("\n" + "="*80)
        logger.info("Table Creation Order (based on dependencies):")
        logger.info("="*80)
        
        # Group tables by foreign key count
        groups = {}
        for info in table_info:
            fk_count = info['fk_count']
            if fk_count not in groups:
                groups[fk_count] = []
            groups[fk_count].append(info['name'])
        
        for fk_count in sorted(groups.keys()):
            logger.info(f"\nGroup {fk_count} (tables with {fk_count} foreign keys):")
            for table in sorted(groups[fk_count]):
                logger.info(f"  - {table}")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(analyze_source_database())