#!/usr/bin/env python3
"""
Fix table creation order based on foreign key dependencies
"""

import asyncio
import asyncpg
from pathlib import Path
from collections import defaultdict, deque

# Database configuration - READ ONLY
DB_CONFIG = {
    'host': 'localhost',
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password',
    'port': 5432
}

class TableOrderFixer:
    """Analyze and fix table creation order"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent
        self.dependencies = defaultdict(set)  # table -> set of tables it depends on
        self.dependents = defaultdict(set)    # table -> set of tables that depend on it
        
    async def analyze_dependencies(self):
        """Analyze table dependencies"""
        conn = await asyncpg.connect(**DB_CONFIG)
        
        try:
            # Get all foreign key relationships
            fk_query = """
                SELECT 
                    tc.table_name as dependent_table,
                    ccu.table_name as referenced_table
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = 'public'
                AND tc.table_name != ccu.table_name  -- Exclude self-references
                ORDER BY tc.table_name
            """
            
            fk_relationships = await conn.fetch(fk_query)
            
            # Build dependency graph
            all_tables = set()
            for rel in fk_relationships:
                dependent = rel['dependent_table']
                referenced = rel['referenced_table']
                
                self.dependencies[dependent].add(referenced)
                self.dependents[referenced].add(dependent)
                all_tables.add(dependent)
                all_tables.add(referenced)
                
            # Get all tables (including those without foreign keys)
            all_tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """
            
            all_table_records = await conn.fetch(all_tables_query)
            for record in all_table_records:
                all_tables.add(record['table_name'])
                
            print(f"Total tables: {len(all_tables)}")
            print(f"Tables with dependencies: {len(self.dependencies)}")
            print(f"Tables being referenced: {len(self.dependents)}")
            
            # Perform topological sort
            ordered_tables = self._topological_sort(all_tables)
            
            # Generate ordered schema file
            await self._generate_ordered_schema(conn, ordered_tables)
            
        finally:
            await conn.close()
            
    def _topological_sort(self, all_tables):
        """Perform topological sort to determine creation order"""
        # Find tables with no dependencies (can be created first)
        no_deps = [table for table in all_tables if table not in self.dependencies]
        
        # Use Kahn's algorithm
        queue = deque(no_deps)
        ordered = []
        temp_deps = {k: set(v) for k, v in self.dependencies.items()}
        
        while queue:
            current = queue.popleft()
            ordered.append(current)
            
            # Remove this table from dependencies of others
            for dependent in self.dependents.get(current, []):
                if dependent in temp_deps:
                    temp_deps[dependent].discard(current)
                    if not temp_deps[dependent]:
                        queue.append(dependent)
                        del temp_deps[dependent]
                        
        # Add any remaining tables (might have circular dependencies)
        remaining = [t for t in all_tables if t not in ordered]
        if remaining:
            print(f"\nWarning: {len(remaining)} tables have circular dependencies:")
            for table in remaining[:10]:
                print(f"  - {table}")
            ordered.extend(remaining)
            
        return ordered
        
    async def _generate_ordered_schema(self, conn, ordered_tables):
        """Generate schema with proper table order"""
        output_file = self.output_dir / "01_schema_ordered.sql"
        
        with open(output_file, 'w') as f:
            f.write("-- SynapseDTE Database Schema (Dependency Ordered)\n")
            f.write("-- This schema creates tables in the correct order based on foreign key dependencies\n\n")
            
            # Add from 01_schema_fixed.sql
            fixed_schema = self.output_dir / "01_schema_fixed.sql"
            if fixed_schema.exists():
                with open(fixed_schema, 'r') as fs:
                    lines = fs.readlines()
                    # Copy extensions and types
                    copying = True
                    for line in lines:
                        if 'CREATE TABLE' in line:
                            break
                        if copying:
                            f.write(line)
                            
            f.write("\n-- =====================================================\n")
            f.write("-- TABLES (In dependency order)\n")
            f.write("-- =====================================================\n\n")
            
            # Group tables by dependency level
            levels = defaultdict(list)
            for i, table in enumerate(ordered_tables):
                level = 0
                # Calculate maximum dependency depth
                visited = set()
                stack = [table]
                while stack:
                    current = stack.pop()
                    if current in visited:
                        continue
                    visited.add(current)
                    deps = self.dependencies.get(current, [])
                    if deps:
                        level = max(level, len(deps))
                        stack.extend(deps)
                levels[level].append(table)
                
            # Write tables by level
            for level in sorted(levels.keys()):
                f.write(f"\n-- Level {level} tables (can be created in parallel)\n")
                for table in sorted(levels[level])[:20]:  # First 20 for brevity
                    f.write(f"-- CREATE TABLE IF NOT EXISTS {table} (...);\n")
                if len(levels[level]) > 20:
                    f.write(f"-- ... and {len(levels[level]) - 20} more tables\n")
                    
            f.write("\n-- Note: Use the complete schema files for actual table definitions\n")
            f.write("-- This file shows the correct creation order\n")
            
            # Save detailed order
            order_file = self.output_dir / "table_creation_order.txt"
            with open(order_file, 'w') as of:
                of.write("Table Creation Order (based on dependencies):\n")
                of.write("=" * 50 + "\n\n")
                
                for i, table in enumerate(ordered_tables, 1):
                    deps = self.dependencies.get(table, set())
                    if deps:
                        of.write(f"{i:3d}. {table} (depends on: {', '.join(sorted(deps))})\n")
                    else:
                        of.write(f"{i:3d}. {table} (no dependencies)\n")
                        
        print(f"\nOrdered schema saved to: {output_file}")
        print(f"Table order saved to: {order_file}")

async def main():
    fixer = TableOrderFixer()
    await fixer.analyze_dependencies()

if __name__ == "__main__":
    asyncio.run(main())