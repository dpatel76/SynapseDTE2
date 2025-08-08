#!/usr/bin/env python3
"""
Verify database structure and requirements
"""

import asyncio
import asyncpg
import json
from pathlib import Path

# Database configuration - READ ONLY
DB_CONFIG = {
    'host': 'localhost',
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password',
    'port': 5432
}

async def verify_database():
    """Verify database structure"""
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Count all tables
        table_count_query = """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """
        table_count = await conn.fetchval(table_count_query)
        print(f"Total tables in database: {table_count}")
        
        # Get all custom types
        types_query = """
            SELECT 
                n.nspname as schema,
                t.typname as type_name,
                t.typtype as type_type,
                CASE 
                    WHEN t.typtype = 'e' THEN 
                        (SELECT string_agg(e.enumlabel, ', ' ORDER BY e.enumsortorder)
                         FROM pg_enum e WHERE e.enumtypid = t.oid)
                    ELSE NULL
                END as enum_values
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public'
            AND t.typtype IN ('e', 'c', 'd')
            ORDER BY t.typname
        """
        
        types = await conn.fetch(types_query)
        print(f"\nCustom types found: {len(types)}")
        for t in types:
            print(f"  - {t['type_name']} ({t['type_type']})")
            if t['enum_values']:
                print(f"    Values: {t['enum_values']}")
        
        # Check for SERIAL columns
        serial_query = """
            SELECT 
                c.table_name,
                c.column_name,
                c.column_default
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
            AND c.column_default LIKE 'nextval%'
            ORDER BY c.table_name, c.ordinal_position
        """
        
        serial_columns = await conn.fetch(serial_query)
        print(f"\nColumns using sequences (SERIAL): {len(serial_columns)}")
        
        # Get table dependencies (foreign keys)
        deps_query = """
            SELECT 
                tc.table_name as dependent_table,
                kcu.column_name as fk_column,
                ccu.table_name as referenced_table,
                ccu.column_name as referenced_column
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
            ORDER BY tc.table_name
        """
        
        dependencies = await conn.fetch(deps_query)
        print(f"\nForeign key relationships: {len(dependencies)}")
        
        # Analyze minimal seed requirements
        print("\n=== Analyzing Minimal Seed Requirements ===")
        
        # Core tables that need data for system to function
        core_tables = [
            'users',
            'rbac_roles',
            'rbac_permissions', 
            'rbac_role_permissions',
            'rbac_user_roles',
            'lobs',
            'reports',
            'regulatory_data_dictionaries',
            'workflow_phases',
            'activity_definitions',
            'test_cycles'
        ]
        
        for table in core_tables:
            count_query = f"SELECT COUNT(*) FROM {table}"
            try:
                count = await conn.fetchval(count_query)
                print(f"  {table}: {count} records")
            except:
                print(f"  {table}: ERROR")
                
        # Check authentication requirements
        print("\n=== Authentication Requirements ===")
        auth_query = """
            SELECT 
                u.email,
                r.name as role_name
            FROM users u
            LEFT JOIN rbac_user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN rbac_roles r ON ur.role_id = r.id
            WHERE u.email IN ('admin@example.com', 'tester@example.com')
            ORDER BY u.email
        """
        
        auth_users = await conn.fetch(auth_query)
        print(f"Test users configured: {len(auth_users)}")
        for user in auth_users:
            print(f"  - {user['email']} ({user['role_name']})")
            
        # Check report configuration
        print("\n=== Report Configuration ===")
        report_query = """
            SELECT 
                r.report_id,
                r.report_name,
                COUNT(rd.attribute_id) as attribute_count
            FROM reports r
            LEFT JOIN regulatory_data_dictionaries rd ON r.report_id = rd.report_id
            GROUP BY r.report_id, r.report_name
            ORDER BY r.report_id
            LIMIT 5
        """
        
        reports = await conn.fetch(report_query)
        for report in reports:
            print(f"  - {report['report_name']}: {report['attribute_count']} attributes")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_database())