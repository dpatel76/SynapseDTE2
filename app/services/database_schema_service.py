"""
Database Schema Discovery Service
Fetches table and column information from configured data sources
"""

import logging
from typing import Dict, List, Any, Optional
import asyncpg
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.models.cycle_report_data_source import CycleReportDataSource as DataSourceConfig

logger = logging.getLogger(__name__)


class DatabaseSchemaService:
    """Service for discovering database schemas from configured data sources"""
    
    async def get_schema_info(self, data_source: DataSourceConfig) -> Dict[str, Any]:
        """
        Get schema information (tables and columns) from a data source
        
        Returns:
            {
                "tables": [
                    {
                        "schema": "public",
                        "table_name": "customers",
                        "columns": [
                            {
                                "column_name": "customer_id",
                                "data_type": "integer",
                                "is_nullable": False,
                                "is_primary_key": True
                            },
                            ...
                        ]
                    },
                    ...
                ]
            }
        """
        try:
            source_type = data_source.source_type.lower() if hasattr(data_source.source_type, 'lower') else str(data_source.source_type).lower()
            
            # Extract specific table from connection config if specified
            connection_config = data_source.connection_config or {}
            specific_table = connection_config.get('table_name')
            specific_schema = connection_config.get('schema', 'public')
            
            if specific_table:
                logger.info(f"Fetching schema for specific table: {specific_schema}.{specific_table}")
            
            if source_type == 'postgresql':
                return await self._get_postgresql_schema(data_source, specific_table, specific_schema)
            elif source_type == 'mysql':
                return await self._get_mysql_schema(data_source, specific_table)
            else:
                logger.warning(f"Schema discovery not implemented for {source_type}")
                return {"tables": [], "error": f"Schema discovery not supported for {source_type}"}
                
        except Exception as e:
            logger.error(f"Failed to get schema info: {str(e)}")
            return {"tables": [], "error": str(e)}
    
    async def _get_postgresql_schema(self, data_source: DataSourceConfig, specific_table: Optional[str] = None, specific_schema: Optional[str] = None) -> Dict[str, Any]:
        """Get schema information from PostgreSQL database"""
        connection_config = data_source.connection_config or {}
        auth_config = data_source.auth_config or {}
        
        # Build connection URL
        host = connection_config.get('host', 'localhost')
        port = connection_config.get('port', 5432)
        database = connection_config.get('database')
        username = auth_config.get('username')
        password = auth_config.get('password')
        
        if not all([database, username, password]):
            return {"tables": [], "error": "Missing connection parameters"}
        
        try:
            # Connect to PostgreSQL
            conn = await asyncpg.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )
            
            try:
                # Build WHERE clause based on specific table/schema
                where_conditions = ["t.table_schema NOT IN ('pg_catalog', 'information_schema')", "t.table_type = 'BASE TABLE'"]
                params = []
                
                if specific_table:
                    where_conditions.append(f"t.table_name = ${len(params) + 1}")
                    params.append(specific_table)
                
                if specific_schema:
                    where_conditions.append(f"t.table_schema = ${len(params) + 1}")
                    params.append(specific_schema)
                
                where_clause = " AND ".join(where_conditions)
                
                # Query to get tables and their columns
                query = f"""
                    SELECT 
                        t.table_schema,
                        t.table_name,
                        array_agg(
                            json_build_object(
                                'column_name', c.column_name,
                                'data_type', c.data_type,
                                'is_nullable', c.is_nullable = 'YES',
                                'is_primary_key', COALESCE(pk.is_primary_key, false),
                                'ordinal_position', c.ordinal_position
                            ) ORDER BY c.ordinal_position
                        ) as columns
                    FROM information_schema.tables t
                    JOIN information_schema.columns c 
                        ON t.table_schema = c.table_schema 
                        AND t.table_name = c.table_name
                    LEFT JOIN (
                        SELECT 
                            kcu.table_schema,
                            kcu.table_name,
                            kcu.column_name,
                            true as is_primary_key
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu 
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                        WHERE tc.constraint_type = 'PRIMARY KEY'
                    ) pk ON c.table_schema = pk.table_schema 
                        AND c.table_name = pk.table_name 
                        AND c.column_name = pk.column_name
                    WHERE {where_clause}
                    GROUP BY t.table_schema, t.table_name
                    ORDER BY t.table_schema, t.table_name
                """
                
                if params:
                    rows = await conn.fetch(query, *params)
                else:
                    rows = await conn.fetch(query)
                
                tables = []
                for row in rows:
                    # Parse the JSON columns if they're strings
                    columns = row['columns']
                    if isinstance(columns, list) and columns and isinstance(columns[0], str):
                        import json
                        columns = [json.loads(col) for col in columns]
                    
                    tables.append({
                        "schema": row['table_schema'],
                        "table_name": row['table_name'],
                        "full_name": f"{row['table_schema']}.{row['table_name']}",
                        "columns": columns
                    })
                
                logger.info(f"Discovered {len(tables)} tables in PostgreSQL database")
                return {"tables": tables}
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"PostgreSQL schema discovery failed: {str(e)}")
            return {"tables": [], "error": str(e)}
    
    async def _get_mysql_schema(self, data_source: DataSourceConfig, specific_table: Optional[str] = None) -> Dict[str, Any]:
        """Get schema information from MySQL database"""
        connection_config = data_source.connection_config or {}
        auth_config = data_source.auth_config or {}
        
        host = connection_config.get('host', 'localhost')
        port = int(connection_config.get('port', 3306))
        database = connection_config.get('database')
        username = auth_config.get('username')
        password = auth_config.get('password')
        
        if not all([database, username, password]):
            return {"tables": [], "error": "Missing connection parameters"}
        
        try:
            # Connect to MySQL
            conn = await aiomysql.connect(
                host=host,
                port=port,
                db=database,
                user=username,
                password=password
            )
            
            try:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Build query based on specific table
                    if specific_table:
                        query = """
                            SELECT 
                                TABLE_SCHEMA,
                                TABLE_NAME
                            FROM information_schema.TABLES
                            WHERE TABLE_SCHEMA = %s
                                AND TABLE_TYPE = 'BASE TABLE'
                                AND TABLE_NAME = %s
                            ORDER BY TABLE_NAME
                        """
                        params = (database, specific_table)
                    else:
                        query = """
                            SELECT 
                                TABLE_SCHEMA,
                                TABLE_NAME
                            FROM information_schema.TABLES
                            WHERE TABLE_SCHEMA = %s
                                AND TABLE_TYPE = 'BASE TABLE'
                            ORDER BY TABLE_NAME
                        """
                        params = (database,)
                    
                    await cursor.execute(query, params)
                    tables_result = await cursor.fetchall()
                    
                    tables = []
                    for table_row in tables_result:
                        table_schema = table_row['TABLE_SCHEMA']
                        table_name = table_row['TABLE_NAME']
                        
                        # Get columns for this table
                        await cursor.execute("""
                            SELECT 
                                c.COLUMN_NAME,
                                c.DATA_TYPE,
                                c.IS_NULLABLE,
                                c.COLUMN_KEY,
                                c.ORDINAL_POSITION
                            FROM information_schema.COLUMNS c
                            WHERE c.TABLE_SCHEMA = %s
                                AND c.TABLE_NAME = %s
                            ORDER BY c.ORDINAL_POSITION
                        """, (table_schema, table_name))
                        
                        columns_result = await cursor.fetchall()
                        
                        columns = []
                        for col in columns_result:
                            columns.append({
                                "column_name": col['COLUMN_NAME'],
                                "data_type": col['DATA_TYPE'],
                                "is_nullable": col['IS_NULLABLE'] == 'YES',
                                "is_primary_key": col['COLUMN_KEY'] == 'PRI',
                                "ordinal_position": col['ORDINAL_POSITION']
                            })
                        
                        tables.append({
                            "schema": table_schema,
                            "table_name": table_name,
                            "full_name": f"{table_schema}.{table_name}",
                            "columns": columns
                        })
                    
                    logger.info(f"Discovered {len(tables)} tables in MySQL database")
                    return {"tables": tables}
                    
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"MySQL schema discovery failed: {str(e)}")
            return {"tables": [], "error": str(e)}
    
    def format_schema_for_prompt(self, schema_info: Dict[str, Any], limit: int = 50) -> str:
        """
        Format schema information for LLM prompt
        Limits the number of tables to avoid token limits
        """
        tables = schema_info.get("tables", [])
        
        if not tables:
            return "No schema information available"
        
        # Limit tables if necessary
        if len(tables) > limit:
            tables = tables[:limit]
            truncated = True
        else:
            truncated = False
        
        formatted_lines = ["Available Tables and Columns:"]
        
        for table in tables:
            formatted_lines.append(f"\nTable: {table['full_name']}")
            # Use the limit parameter for columns per table instead of hard-coded 20
            columns = table.get('columns', [])
            column_limit = min(len(columns), limit) if limit else len(columns)
            for col in columns[:column_limit]:
                pk_indicator = " (PK)" if col.get('is_primary_key') else ""
                nullable = " NULL" if col.get('is_nullable') else " NOT NULL"
                formatted_lines.append(
                    f"  - {col['column_name']}: {col['data_type']}{pk_indicator}{nullable}"
                )
            
            if len(columns) > column_limit:
                formatted_lines.append(f"  ... and {len(columns) - column_limit} more columns")
        
        if truncated:
            formatted_lines.append(f"\n... and {len(schema_info.get('tables', [])) - limit} more tables")
        
        return "\n".join(formatted_lines)


# Global service instance
_schema_service = None

def get_schema_service() -> DatabaseSchemaService:
    """Get the global schema service instance"""
    global _schema_service
    if _schema_service is None:
        _schema_service = DatabaseSchemaService()
    return _schema_service