"""
Data Source Query Service for Production-Grade Data Profiling
Handles querying real data from configured data sources with support for large datasets
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg
import aiomysql
import cx_Oracle
import pymssql
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.models.cycle_report_data_source import CycleReportDataSource as DataSourceConfig, DataSourceType
from app.models.planning import PlanningPDEMapping as PDEMapping

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure chunking for large datasets
CHUNK_SIZE = 100_000  # Process 100k rows at a time
MAX_MEMORY_MB = 1024  # Maximum memory usage in MB
QUERY_TIMEOUT = 300  # 5 minutes timeout for queries


class DataSourceQueryService:
    """Service for querying data from various data sources"""
    
    def __init__(self):
        self.connection_pools = {}
        self.chunk_size = CHUNK_SIZE
        
    async def get_connection_string(self, data_source: DataSourceConfig) -> str:
        """Build connection string based on data source type"""
        config = data_source.connection_config
        
        if data_source.source_type == DataSourceType.POSTGRESQL:
            return f"postgresql+asyncpg://{config['user']}:{config['password']}@{config['host']}:{config.get('port', 5432)}/{config['database']}"
        elif data_source.source_type == DataSourceType.MYSQL:
            return f"mysql+aiomysql://{config['user']}:{config['password']}@{config['host']}:{config.get('port', 3306)}/{config['database']}"
        elif data_source.source_type == DataSourceType.ORACLE:
            return f"oracle+cx_oracle://{config['user']}:{config['password']}@{config['host']}:{config.get('port', 1521)}/{config['service_name']}"
        elif data_source.source_type == DataSourceType.SQLSERVER:
            return f"mssql+pymssql://{config['user']}:{config['password']}@{config['host']}:{config.get('port', 1433)}/{config['database']}"
        else:
            raise ValueError(f"Unsupported data source type: {data_source.source_type}")
    
    async def test_connection(self, data_source: DataSourceConfig) -> Dict[str, Any]:
        """Test connection to data source"""
        try:
            conn_string = await self.get_connection_string(data_source)
            engine = create_async_engine(conn_string, pool_size=1, max_overflow=0)
            
            async with engine.connect() as conn:
                # Simple test query
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()
                
            await engine.dispose()
            
            return {
                "success": True,
                "message": "Connection successful",
                "source_type": data_source.source_type
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "source_type": data_source.source_type
            }
    
    async def get_row_count(self, data_source: DataSourceConfig, table_name: str, 
                           where_clause: Optional[str] = None) -> int:
        """Get row count for a table with optional filtering"""
        try:
            conn_string = await self.get_connection_string(data_source)
            engine = create_async_engine(conn_string)
            
            query = f"SELECT COUNT(*) AS row_count FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            async with engine.connect() as conn:
                result = await conn.execute(text(query))
                row = await result.fetchone()
                count = row.row_count if hasattr(row, 'row_count') else row[0]
                
            await engine.dispose()
            return count
            
        except Exception as e:
            logger.error(f"Failed to get row count: {str(e)}")
            raise
    
    async def query_data_chunked(self, data_source: DataSourceConfig, query: str,
                                params: Optional[Dict] = None) -> AsyncIterator[pd.DataFrame]:
        """
        Query data in chunks for memory-efficient processing of large datasets
        Yields DataFrames of chunk_size rows
        """
        try:
            conn_string = await self.get_connection_string(data_source)
            
            # Use synchronous engine for pandas compatibility
            sync_conn_string = conn_string.replace('+asyncpg', '').replace('+aiomysql', '')
            engine = create_engine(sync_conn_string)
            
            # Add LIMIT/OFFSET for chunking based on database type
            offset = 0
            while True:
                if data_source.source_type in [DataSourceType.POSTGRESQL, DataSourceType.MYSQL]:
                    chunk_query = f"{query} LIMIT {self.chunk_size} OFFSET {offset}"
                elif data_source.source_type == DataSourceType.SQLSERVER:
                    # SQL Server uses OFFSET FETCH
                    chunk_query = f"{query} ORDER BY 1 OFFSET {offset} ROWS FETCH NEXT {self.chunk_size} ROWS ONLY"
                elif data_source.source_type == DataSourceType.ORACLE:
                    # Oracle uses ROWNUM
                    chunk_query = f"""
                        SELECT * FROM (
                            SELECT a.*, ROWNUM rnum FROM ({query}) a 
                            WHERE ROWNUM <= {offset + self.chunk_size}
                        ) WHERE rnum > {offset}
                    """
                else:
                    chunk_query = query  # Fallback to full query
                
                # Read chunk
                chunk_df = await asyncio.to_thread(
                    pd.read_sql_query, 
                    chunk_query, 
                    engine, 
                    params=params
                )
                
                if chunk_df.empty:
                    break
                    
                yield chunk_df
                
                # If we got less than chunk_size rows, we're done
                if len(chunk_df) < self.chunk_size:
                    break
                    
                offset += self.chunk_size
                
            engine.dispose()
            
        except Exception as e:
            logger.error(f"Failed to query data: {str(e)}")
            raise
    
    async def query_attribute_data(self, data_source: DataSourceConfig, 
                                  pde_mapping: PDEMapping,
                                  limit: Optional[int] = None) -> pd.DataFrame:
        """
        Query data for a specific attribute using its PDE mapping
        """
        try:
            # Build query from PDE mapping
            table_name = data_source.connection_config.get('default_table')
            source_field = pde_mapping.source_field
            
            # Build base query
            query = f"SELECT {source_field} as attribute_value FROM {table_name}"
            
            # Add any profiling criteria (e.g., date ranges, filters)
            if pde_mapping.profiling_criteria:
                criteria = pde_mapping.profiling_criteria
                if 'where_clause' in criteria:
                    query += f" WHERE {criteria['where_clause']}"
            
            # Add limit if specified
            if limit:
                if data_source.source_type in [DataSourceType.POSTGRESQL, DataSourceType.MYSQL]:
                    query += f" LIMIT {limit}"
                elif data_source.source_type == DataSourceType.SQLSERVER:
                    query = f"SELECT TOP {limit} {source_field} as attribute_value FROM {table_name}"
                elif data_source.source_type == DataSourceType.ORACLE:
                    query += f" WHERE ROWNUM <= {limit}"
            
            # For large datasets, use chunked reading
            total_rows = await self.get_row_count(
                data_source, 
                table_name,
                pde_mapping.profiling_criteria.get('where_clause') if pde_mapping.profiling_criteria else None
            )
            
            if total_rows > self.chunk_size:
                # Process in chunks
                logger.info(f"Large dataset detected ({total_rows} rows), processing in chunks")
                chunks = []
                async for chunk in self.query_data_chunked(data_source, query):
                    chunks.append(chunk)
                    if limit and sum(len(c) for c in chunks) >= limit:
                        break
                
                result_df = pd.concat(chunks, ignore_index=True)
                if limit:
                    result_df = result_df.head(limit)
            else:
                # Small dataset, query all at once
                conn_string = await self.get_connection_string(data_source)
                sync_conn_string = conn_string.replace('+asyncpg', '').replace('+aiomysql', '')
                engine = create_engine(sync_conn_string)
                
                result_df = await asyncio.to_thread(
                    pd.read_sql_query,
                    query,
                    engine
                )
                
                engine.dispose()
            
            # Apply any transformation rules
            if pde_mapping.transformation_rule:
                result_df = await self._apply_transformation(
                    result_df, 
                    pde_mapping.transformation_rule
                )
            
            # Rename column to attribute name
            result_df.columns = [pde_mapping.attribute.attribute_name]
            
            return result_df
            
        except Exception as e:
            logger.error(f"Failed to query attribute data: {str(e)}")
            raise
    
    async def _apply_transformation(self, df: pd.DataFrame, 
                                   transformation_rule: Dict) -> pd.DataFrame:
        """Apply transformation rules to data"""
        try:
            rule_type = transformation_rule.get('type', 'direct')
            
            if rule_type == 'direct':
                # No transformation needed
                return df
            elif rule_type == 'calculated':
                # Apply calculation
                expression = transformation_rule.get('expression')
                if expression:
                    # Safe evaluation of expression
                    df['attribute_value'] = df.eval(expression, engine='python')
            elif rule_type == 'lookup':
                # Apply lookup mapping
                lookup_map = transformation_rule.get('lookup_map', {})
                df['attribute_value'] = df['attribute_value'].map(lookup_map)
            elif rule_type == 'conditional':
                # Apply conditional logic
                conditions = transformation_rule.get('conditions', [])
                for condition in conditions:
                    mask = df.eval(condition['if'], engine='python')
                    df.loc[mask, 'attribute_value'] = condition['then']
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to apply transformation: {str(e)}")
            return df  # Return original data if transformation fails
    
    async def execute_profiling_rule_on_source(self, data_source: DataSourceConfig,
                                              pde_mapping: PDEMapping,
                                              rule_code: str) -> Dict[str, Any]:
        """
        Execute a profiling rule directly on the data source for efficiency
        """
        try:
            # For very large datasets, try to push computation to database
            if data_source.source_type in [DataSourceType.POSTGRESQL, DataSourceType.MYSQL]:
                # Try to convert rule to SQL
                sql_result = await self._execute_rule_as_sql(
                    data_source, 
                    pde_mapping, 
                    rule_code
                )
                if sql_result:
                    return sql_result
            
            # Fallback to Python execution with chunked processing
            total_passed = 0
            total_failed = 0
            total_count = 0
            
            # Process data in chunks
            async for chunk_df in self.query_data_chunked(
                data_source, 
                f"SELECT {pde_mapping.source_field} FROM {data_source.connection_config.get('default_table')}"
            ):
                # Apply transformation if needed
                if pde_mapping.transformation_rule:
                    chunk_df = await self._apply_transformation(
                        chunk_df, 
                        pde_mapping.transformation_rule
                    )
                
                # Rename column to attribute name
                chunk_df.columns = [pde_mapping.attribute.attribute_name]
                
                # Execute rule code on chunk
                exec_globals = {"df": chunk_df, "pd": pd, "np": np}
                exec(rule_code, exec_globals)
                
                # Get the function name from the rule code
                func_name = rule_code.split("def ")[1].split("(")[0]
                check_func = exec_globals[func_name]
                
                # Execute the check
                result = check_func(chunk_df, pde_mapping.attribute.attribute_name)
                
                # Aggregate results
                if isinstance(result, dict):
                    total_passed += result.get("passed", 0)
                    total_failed += result.get("failed", 0)
                    total_count += result.get("total", 0)
            
            # Calculate final metrics
            pass_rate = (total_passed / total_count * 100) if total_count > 0 else 0
            
            return {
                "passed": total_passed,
                "failed": total_failed,
                "total": total_count,
                "pass_rate": pass_rate
            }
            
        except Exception as e:
            logger.error(f"Failed to execute profiling rule on source: {str(e)}")
            raise
    
    async def _execute_rule_as_sql(self, data_source: DataSourceConfig,
                                  pde_mapping: PDEMapping,
                                  rule_code: str) -> Optional[Dict[str, Any]]:
        """
        Try to convert and execute rule as SQL for better performance
        """
        # This is a simplified implementation - in production, you'd have
        # more sophisticated rule-to-SQL conversion
        
        source_field = pde_mapping.source_field
        table_name = data_source.connection_config.get('default_table')
        
        # Check if rule is a simple completeness check
        if "notna()" in rule_code or "notnull" in rule_code.lower():
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({source_field}) as passed,
                    COUNT(*) - COUNT({source_field}) as failed
                FROM {table_name}
            """
            
            conn_string = await self.get_connection_string(data_source)
            engine = create_async_engine(conn_string)
            
            async with engine.connect() as conn:
                result = await conn.execute(text(query))
                row = await result.mappings().fetchone()
                
            await engine.dispose()
            
            total = row['total']
            passed = row['passed']
            failed = row['failed']
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            return {
                "passed": passed,
                "failed": failed,
                "total": total,
                "pass_rate": pass_rate
            }
        
        # Add more SQL conversions for other rule types as needed
        
        return None  # Couldn't convert to SQL


# Singleton instance
_data_source_query_service = None

def get_data_source_query_service() -> DataSourceQueryService:
    """Get singleton instance of data source query service"""
    global _data_source_query_service
    if _data_source_query_service is None:
        _data_source_query_service = DataSourceQueryService()
    return _data_source_query_service