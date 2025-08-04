#!/usr/bin/env python3
"""
Extract Data from Current Database
This script connects to the existing database and extracts seed data
in a format suitable for containerized deployment.
Database is accessed in READ-ONLY mode.
"""

import os
import sys
import json
import asyncio
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncpg

# Database configuration - READ ONLY
DB_CONFIG = {
    'host': 'localhost',
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password',
    'port': 5432
}

class DataExtractor:
    """Extract seed data from existing database"""
    
    def __init__(self):
        self.conn = None
        
        # Define extraction order (dependencies first)
        self.table_order = [
            # Core tables
            'users',
            'roles', 
            'permissions',
            'role_permissions',
            'user_roles',
            
            # Reference data
            'lobs',
            'data_owners',
            'reports',
            'report_attributes',
            
            # Test cycles
            'test_cycles',
            'cycle_reports',
            
            # Workflow
            'workflow_phases',
            
            # Add more tables as needed
        ]
        
        # Tables to extract all data
        self.full_extract_tables = {
            'roles', 'permissions', 'role_permissions',
            'lobs', 'reports', 'report_attributes',
            'workflow_phases'
        }
        
        # Tables to extract sample data only
        self.sample_extract_tables = {
            'users': 10,  # Extract 10 users
            'test_cycles': 5,  # Extract 5 most recent cycles
            'cycle_reports': 20,  # Extract 20 most recent reports
        }
        
    async def connect(self):
        """Create database connection"""
        # We'll use asyncpg directly instead of SQLAlchemy for better control
        self.conn = await asyncpg.connect(**DB_CONFIG)
        
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table structure and row count"""
        # Get row count
        row_count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        
        # Get column info
        column_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = $1
            ORDER BY ordinal_position
        """
        
        column_result = await self.conn.fetch(column_query, table_name)
        columns = [dict(row) for row in column_result]
        
        return {
            "table_name": table_name,
            "row_count": row_count,
            "columns": columns
        }
            
    async def extract_table_data(self, table_name: str, limit: int = None) -> List[Dict]:
        """Extract data from a table"""
        query = f"SELECT * FROM {table_name}"
        
        # Add ordering for consistent extraction
        if table_name in ['users', 'test_cycles', 'cycle_reports']:
            query += " ORDER BY created_at DESC"
        elif 'id' in await self._get_column_names(table_name):
            query += " ORDER BY id"
            
        if limit:
            query += f" LIMIT {limit}"
            
        result = await self.conn.fetch(query)
        
        # Convert rows to dictionaries
        rows = []
        for row in result:
            row_dict = dict(row)
            
            # Convert special types for JSON serialization
            for key, value in row_dict.items():
                if isinstance(value, (datetime, date)):
                    row_dict[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_dict[key] = float(value)
                elif isinstance(value, bytes):
                    row_dict[key] = value.hex()
                elif isinstance(value, uuid.UUID):
                    row_dict[key] = str(value)
                    
            rows.append(row_dict)
            
        return rows
            
    async def _get_column_names(self, table_name: str) -> List[str]:
        """Get column names for a table"""
        query = """
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
        """
        result = await self.conn.fetch(query, table_name)
        return [row['column_name'] for row in result]
        
    async def extract_seed_data(self, output_dir: Path):
        """Extract all seed data"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track extraction results
        extraction_summary = {
            "extraction_date": datetime.now().isoformat(),
            "database": DB_CONFIG['database'],
            "tables": {}
        }
        
        # Get all tables
        table_query = """
            SELECT table_name 
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        result = await self.conn.fetch(table_query)
        all_tables = [row['table_name'] for row in result]
            
        print(f"Found {len(all_tables)} tables in database")
        
        # Extract data from each table
        for table_name in all_tables:
            try:
                print(f"\nProcessing table: {table_name}")
                
                # Get table info
                table_info = await self.get_table_info(table_name)
                print(f"  Rows: {table_info['row_count']}")
                
                # Determine extraction strategy
                if table_info['row_count'] == 0:
                    print(f"  Skipping - no data")
                    continue
                    
                # Extract data
                if table_name in self.full_extract_tables:
                    # Extract all data
                    data = await self.extract_table_data(table_name)
                    print(f"  Extracted all {len(data)} rows")
                elif table_name in self.sample_extract_tables:
                    # Extract sample data
                    limit = self.sample_extract_tables[table_name]
                    data = await self.extract_table_data(table_name, limit)
                    print(f"  Extracted {len(data)} sample rows (limit: {limit})")
                else:
                    # Skip large tables by default
                    if table_info['row_count'] > 1000:
                        print(f"  Skipping - too many rows ({table_info['row_count']})")
                        extraction_summary['tables'][table_name] = {
                            "status": "skipped",
                            "reason": "too_many_rows",
                            "row_count": table_info['row_count']
                        }
                        continue
                    else:
                        # Extract all data for small tables
                        data = await self.extract_table_data(table_name)
                        print(f"  Extracted all {len(data)} rows")
                        
                # Save data to JSON file
                if data:
                    output_file = output_dir / f"{table_name}.json"
                    with open(output_file, 'w') as f:
                        json.dump({
                            "table": table_name,
                            "row_count": len(data),
                            "extracted_at": datetime.now().isoformat(),
                            "data": data
                        }, f, indent=2)
                        
                    extraction_summary['tables'][table_name] = {
                        "status": "extracted",
                        "row_count": len(data),
                        "file": str(output_file.name)
                    }
                    
            except Exception as e:
                print(f"  ERROR: {str(e)}")
                extraction_summary['tables'][table_name] = {
                    "status": "error",
                    "error": str(e)
                }
                
        # Save extraction summary
        summary_file = output_dir / "_extraction_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(extraction_summary, f, indent=2)
            
        print(f"\nExtraction complete! Summary saved to: {summary_file}")
        
    async def generate_insert_scripts(self, output_dir: Path):
        """Generate SQL INSERT scripts from extracted data"""
        data_dir = output_dir / "seed_data"
        sql_dir = output_dir / "sql_seeds"
        sql_dir.mkdir(parents=True, exist_ok=True)
        
        # Read all JSON files
        json_files = sorted(data_dir.glob("*.json"))
        
        for json_file in json_files:
            if json_file.name.startswith("_"):
                continue
                
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            table_name = data['table']
            rows = data['data']
            
            if not rows:
                continue
                
            # Generate SQL file
            sql_file = sql_dir / f"{json_file.stem}.sql"
            with open(sql_file, 'w') as f:
                f.write(f"-- Seed data for {table_name}\n")
                f.write(f"-- Generated from: {json_file.name}\n")
                f.write(f"-- Rows: {len(rows)}\n\n")
                
                # Generate INSERT statements
                for row in rows:
                    columns = list(row.keys())
                    values = []
                    
                    for col, val in row.items():
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, bool):
                            values.append("TRUE" if val else "FALSE")
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        else:
                            # Escape single quotes
                            val_str = str(val).replace("'", "''")
                            values.append(f"'{val_str}'")
                            
                    f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES\n")
                    f.write(f"({', '.join(values)});\n\n")
                    
        print(f"SQL seed scripts generated in: {sql_dir}")
        
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            
async def main():
    """Main execution"""
    extractor = DataExtractor()
    
    try:
        await extractor.connect()
        
        output_dir = Path(__file__).parent
        seed_data_dir = output_dir / "seed_data"
        
        # Extract seed data
        print("Extracting seed data from database...")
        await extractor.extract_seed_data(seed_data_dir)
        
        # Generate SQL scripts
        print("\nGenerating SQL insert scripts...")
        await extractor.generate_insert_scripts(output_dir)
        
    finally:
        await extractor.close()
        
if __name__ == "__main__":
    asyncio.run(main())