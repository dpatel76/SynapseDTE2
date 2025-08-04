"""
Database Connection Service for RFI Query Validation
Handles secure connections to various database types for query execution
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncpg
import aiomysql
import aiofiles
import pandas as pd
from sqlalchemy import create_engine, text
from contextlib import asynccontextmanager
import logging

from app.core.exceptions import ValidationError, BusinessLogicError

logger = logging.getLogger(__name__)


class DatabaseConnectionService:
    """Service for managing database connections and query execution"""
    
    def __init__(self):
        self.connection_pools: Dict[str, Any] = {}
        self.supported_types = ['postgresql', 'mysql', 'oracle', 'csv', 'api']
        
    async def test_connection(
        self, 
        connection_type: str, 
        connection_details: Dict[str, Any],
        test_query: Optional[str] = None
    ) -> bool:
        """Test database connection with optional test query"""
        if connection_type not in self.supported_types:
            raise ValidationError(f"Unsupported connection type: {connection_type}")
            
        try:
            if connection_type == 'postgresql':
                return await self._test_postgresql(connection_details, test_query)
            elif connection_type == 'mysql':
                return await self._test_mysql(connection_details, test_query)
            elif connection_type == 'csv':
                return await self._test_csv(connection_details)
            elif connection_type == 'api':
                return await self._test_api(connection_details)
            else:
                raise ValidationError(f"Connection type {connection_type} not implemented")
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            raise BusinessLogicError(f"Connection test failed: {str(e)}")
    
    async def execute_query(
        self,
        connection_type: str,
        connection_details: Dict[str, Any],
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Execute query and return results"""
        if connection_type not in self.supported_types:
            raise ValidationError(f"Unsupported connection type: {connection_type}")
            
        try:
            if connection_type == 'postgresql':
                return await self._execute_postgresql(connection_details, query, parameters, timeout)
            elif connection_type == 'mysql':
                return await self._execute_mysql(connection_details, query, parameters, timeout)
            elif connection_type == 'csv':
                return await self._execute_csv(connection_details, query, parameters)
            else:
                raise ValidationError(f"Query execution for {connection_type} not implemented")
        except asyncio.TimeoutError:
            raise BusinessLogicError("Query execution timed out")
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise BusinessLogicError(f"Query execution failed: {str(e)}")
    
    # PostgreSQL implementation
    async def _test_postgresql(self, connection_details: Dict[str, Any], test_query: Optional[str]) -> bool:
        """Test PostgreSQL connection"""
        conn = None
        try:
            conn = await asyncpg.connect(
                host=connection_details['host'],
                port=connection_details.get('port', 5432),
                database=connection_details['database'],
                user=connection_details['username'],
                password=connection_details.get('password', ''),
                timeout=10.0
            )
            
            if test_query:
                await conn.fetch(test_query)
            else:
                await conn.fetch("SELECT 1")
                
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {str(e)}")
            raise
        finally:
            if conn:
                await conn.close()
    
    async def _execute_postgresql(
        self, 
        connection_details: Dict[str, Any], 
        query: str, 
        parameters: Optional[Dict[str, Any]],
        timeout: float
    ) -> Dict[str, Any]:
        """Execute PostgreSQL query"""
        conn = None
        try:
            conn = await asyncpg.connect(
                host=connection_details['host'],
                port=connection_details.get('port', 5432),
                database=connection_details['database'],
                user=connection_details['username'],
                password=connection_details.get('password', ''),
                timeout=timeout
            )
            
            # Convert parameters to positional args for asyncpg
            if parameters:
                # Replace :param with $1, $2, etc.
                query_parts = query.split(':')
                new_query = query_parts[0]
                args = []
                for i, part in enumerate(query_parts[1:], 1):
                    param_name = part.split()[0].rstrip(',).;')
                    if param_name in parameters:
                        new_query += f"${i}" + part[len(param_name):]
                        args.append(parameters[param_name])
                    else:
                        new_query += ':' + part
                query = new_query
                results = await conn.fetch(query, *args, timeout=timeout)
            else:
                results = await conn.fetch(query, timeout=timeout)
            
            # Convert results to list of dicts
            rows = [dict(row) for row in results]
            columns = list(rows[0].keys()) if rows else []
            
            # Get total count (without LIMIT)
            count_query = f"SELECT COUNT(*) as total FROM ({query.split('LIMIT')[0]}) as subquery"
            if 'LIMIT' in query.upper():
                try:
                    if parameters and args:
                        count_result = await conn.fetchval(count_query, *args, timeout=5.0)
                    else:
                        count_result = await conn.fetchval(count_query, timeout=5.0)
                    total_count = count_result
                except:
                    total_count = len(rows)
            else:
                total_count = len(rows)
            
            return {
                'rows': rows,
                'columns': columns,
                'total_count': total_count,
                'row_count': len(rows)
            }
            
        finally:
            if conn:
                await conn.close()
    
    # MySQL implementation
    async def _test_mysql(self, connection_details: Dict[str, Any], test_query: Optional[str]) -> bool:
        """Test MySQL connection"""
        conn = None
        try:
            conn = await aiomysql.connect(
                host=connection_details['host'],
                port=connection_details.get('port', 3306),
                db=connection_details['database'],
                user=connection_details['username'],
                password=connection_details.get('password', ''),
                connect_timeout=10
            )
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if test_query:
                    await cursor.execute(test_query)
                else:
                    await cursor.execute("SELECT 1")
                await cursor.fetchall()
                
            return True
        except Exception as e:
            logger.error(f"MySQL connection test failed: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def _execute_mysql(
        self, 
        connection_details: Dict[str, Any], 
        query: str, 
        parameters: Optional[Dict[str, Any]],
        timeout: float
    ) -> Dict[str, Any]:
        """Execute MySQL query"""
        conn = None
        try:
            conn = await aiomysql.connect(
                host=connection_details['host'],
                port=connection_details.get('port', 3306),
                db=connection_details['database'],
                user=connection_details['username'],
                password=connection_details.get('password', ''),
                connect_timeout=int(timeout)
            )
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # MySQL uses %s placeholders
                if parameters:
                    # Convert :param to %s
                    mysql_query = query
                    args = []
                    for param_name, param_value in parameters.items():
                        mysql_query = mysql_query.replace(f":{param_name}", "%s")
                        args.append(param_value)
                    await cursor.execute(mysql_query, args)
                else:
                    await cursor.execute(query)
                    
                rows = await cursor.fetchall()
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Get total count
                if 'LIMIT' in query.upper():
                    count_query = f"SELECT COUNT(*) as total FROM ({query.split('LIMIT')[0]}) as subquery"
                    await cursor.execute(count_query)
                    count_result = await cursor.fetchone()
                    total_count = count_result['total'] if count_result else len(rows)
                else:
                    total_count = len(rows)
                
                return {
                    'rows': rows,
                    'columns': columns,
                    'total_count': total_count,
                    'row_count': len(rows)
                }
                
        finally:
            if conn:
                conn.close()
    
    # CSV implementation
    async def _test_csv(self, connection_details: Dict[str, Any]) -> bool:
        """Test CSV file access"""
        file_path = connection_details.get('file_path')
        if not file_path:
            raise ValidationError("CSV connection requires 'file_path'")
            
        try:
            async with aiofiles.open(file_path, mode='r') as f:
                # Just read first line to test
                await f.readline()
            return True
        except Exception as e:
            logger.error(f"CSV file test failed: {str(e)}")
            raise
    
    async def _execute_csv(
        self, 
        connection_details: Dict[str, Any], 
        query: str, 
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute query on CSV file using pandas"""
        file_path = connection_details.get('file_path')
        if not file_path:
            raise ValidationError("CSV connection requires 'file_path'")
            
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Simple query parsing for CSV (only supports basic WHERE conditions)
            if 'WHERE' in query.upper():
                # Extract WHERE conditions
                where_clause = query.upper().split('WHERE')[1].split('LIMIT')[0]
                
                # Apply parameters if any
                if parameters:
                    for param_name, param_value in parameters.items():
                        where_clause = where_clause.replace(f":{param_name}", f"'{param_value}'")
                
                # Apply filter (very basic implementation)
                # In production, use a proper SQL parser
                filtered_df = df
            else:
                filtered_df = df
            
            # Apply LIMIT if present
            if 'LIMIT' in query.upper():
                limit = int(query.upper().split('LIMIT')[1].strip().split()[0])
                filtered_df = filtered_df.head(limit)
            
            # Convert to result format
            rows = filtered_df.to_dict('records')
            columns = list(filtered_df.columns)
            
            return {
                'rows': rows,
                'columns': columns,
                'total_count': len(df),
                'row_count': len(rows)
            }
            
        except Exception as e:
            logger.error(f"CSV query execution failed: {str(e)}")
            raise
    
    # API implementation placeholder
    async def _test_api(self, connection_details: Dict[str, Any]) -> bool:
        """Test API connection"""
        # Implement API connection test
        raise NotImplementedError("API connections not yet implemented")
    
    async def close_all_pools(self):
        """Close all connection pools"""
        for pool_name, pool in self.connection_pools.items():
            try:
                if hasattr(pool, 'close'):
                    await pool.close()
            except Exception as e:
                logger.error(f"Error closing pool {pool_name}: {str(e)}")
        self.connection_pools.clear()