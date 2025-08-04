"""
Data Source service for managing external database connections
"""

import asyncio
import time
from typing import List, Tuple, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.dialects.postgresql import insert

from app.models.data_source import DataSource
from app.schemas.data_source import (
    DataSourceCreate, DataSourceUpdate, DataSourceTestResponse,
    DataSourceStatsResponse
)
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataSourceService:
    """Service for managing data sources"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_data_source(self, data_source_data: DataSourceCreate) -> DataSource:
        """Create a new data source with encrypted password"""
        
        # Get next data_source_id
        max_id_result = await self.db.execute(
            select(DataSource.data_source_id).order_by(DataSource.data_source_id.desc()).limit(1)
        )
        max_id = max_id_result.scalar_one_or_none()
        next_id = (max_id or 0) + 1
        
        # Create new data source
        data_source = DataSource(
            data_source_id=next_id,
            data_source_name=data_source_data.data_source_name,
            database_type=data_source_data.database_type,
            database_url=data_source_data.database_url,
            database_user=data_source_data.database_user,
            description=data_source_data.description,
            is_active=data_source_data.is_active
        )
        
        # Set encrypted password
        data_source.set_password(data_source_data.database_password)
        
        self.db.add(data_source)
        await self.db.commit()
        await self.db.refresh(data_source)
        
        logger.info(f"Created data source: {data_source.data_source_name}")
        return data_source
    
    async def get_data_source(self, data_source_id: int) -> Optional[DataSource]:
        """Get data source by ID"""
        result = await self.db.execute(
            select(DataSource).where(DataSource.data_source_id == data_source_id)
        )
        return result.scalar_one_or_none()
    
    async def list_data_sources(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        database_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[DataSource], int]:
        """List data sources with filtering"""
        
        # Build query
        query = select(DataSource)
        conditions = []
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    DataSource.data_source_name.ilike(search_term),
                    DataSource.description.ilike(search_term)
                )
            )
        
        if database_type:
            conditions.append(DataSource.database_type == database_type)
        
        if is_active is not None:
            conditions.append(DataSource.is_active == is_active)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(DataSource.data_source_id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and execute
        query = query.offset(skip).limit(limit).order_by(DataSource.data_source_name)
        result = await self.db.execute(query)
        data_sources = result.scalars().all()
        
        return data_sources, total
    
    async def update_data_source(
        self, 
        data_source_id: int, 
        data_source_data: DataSourceUpdate
    ) -> DataSource:
        """Update data source information"""
        
        # Get existing data source
        data_source = await self.get_data_source(data_source_id)
        if not data_source:
            raise NotFoundException(f"Data source with ID {data_source_id} not found")
        
        # Check name uniqueness if being changed
        if (data_source_data.data_source_name and 
            data_source_data.data_source_name != data_source.data_source_name):
            existing_result = await self.db.execute(
                select(DataSource).where(
                    and_(
                        DataSource.data_source_name == data_source_data.data_source_name,
                        DataSource.data_source_id != data_source_id
                    )
                )
            )
            if existing_result.scalar_one_or_none():
                raise ValidationException("Data source name already exists")
        
        # Update fields
        update_data = data_source_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "database_password":
                # Handle password separately for encryption
                data_source.set_password(value)
            else:
                setattr(data_source, field, value)
        
        await self.db.commit()
        await self.db.refresh(data_source)
        
        logger.info(f"Updated data source: {data_source.data_source_name}")
        return data_source
    
    async def delete_data_source(self, data_source_id: int) -> None:
        """Delete data source (soft delete by marking inactive)"""
        
        data_source = await self.get_data_source(data_source_id)
        if not data_source:
            raise NotFoundException(f"Data source with ID {data_source_id} not found")
        
        # Check if data source is being used (you might want to add this check)
        # For now, we'll just deactivate it
        data_source.is_active = False
        
        await self.db.commit()
        logger.info(f"Deactivated data source: {data_source.data_source_name}")
    
    async def test_connection(self, data_source_id: int) -> DataSourceTestResponse:
        """Test connection to data source"""
        
        data_source = await self.get_data_source(data_source_id)
        if not data_source:
            raise NotFoundException(f"Data source with ID {data_source_id} not found")
        
        start_time = time.time()
        
        try:
            # Get connection info with decrypted password
            connection_info = data_source.get_connection_info()
            
            # Test connection based on database type
            success = await self._test_database_connection(connection_info)
            
            end_time = time.time()
            connection_time_ms = int((end_time - start_time) * 1000)
            
            if success:
                return DataSourceTestResponse(
                    success=True,
                    message="Connection successful",
                    connection_time_ms=connection_time_ms
                )
            else:
                return DataSourceTestResponse(
                    success=False,
                    message="Connection failed",
                    connection_time_ms=connection_time_ms,
                    error_details="Unable to establish connection"
                )
                
        except Exception as e:
            end_time = time.time()
            connection_time_ms = int((end_time - start_time) * 1000)
            
            logger.error(f"Connection test failed for data source {data_source_id}: {str(e)}")
            return DataSourceTestResponse(
                success=False,
                message="Connection test failed",
                connection_time_ms=connection_time_ms,
                error_details=str(e)
            )
    
    async def _test_database_connection(self, connection_info: Dict[str, str]) -> bool:
        """Test actual database connection based on type"""
        
        database_type = connection_info["database_type"]
        
        try:
            if database_type == "PostgreSQL":
                return await self._test_postgresql_connection(connection_info)
            elif database_type == "MySQL":
                return await self._test_mysql_connection(connection_info)
            elif database_type == "Oracle":
                return await self._test_oracle_connection(connection_info)
            elif database_type == "SQL Server":
                return await self._test_sqlserver_connection(connection_info)
            elif database_type == "SQLite":
                return await self._test_sqlite_connection(connection_info)
            else:
                logger.warning(f"Unsupported database type: {database_type}")
                return False
                
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    async def _test_postgresql_connection(self, connection_info: Dict[str, str]) -> bool:
        """Test PostgreSQL connection"""
        try:
            import asyncpg
            
            # Parse connection URL or build connection string
            conn = await asyncpg.connect(
                host=self._extract_host(connection_info["database_url"]),
                port=self._extract_port(connection_info["database_url"]),
                user=connection_info["database_user"],
                password=connection_info["database_password"],
                database=self._extract_database(connection_info["database_url"])
            )
            
            # Simple test query
            await conn.fetchval("SELECT 1")
            await conn.close()
            
            return True
            
        except ImportError:
            logger.warning("asyncpg not installed for PostgreSQL testing")
            return False
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {str(e)}")
            return False
    
    async def _test_mysql_connection(self, connection_info: Dict[str, str]) -> bool:
        """Test MySQL connection"""
        try:
            import aiomysql
            
            conn = await aiomysql.connect(
                host=self._extract_host(connection_info["database_url"]),
                port=self._extract_port(connection_info["database_url"]),
                user=connection_info["database_user"],
                password=connection_info["database_password"],
                db=self._extract_database(connection_info["database_url"])
            )
            
            cursor = await conn.cursor()
            await cursor.execute("SELECT 1")
            await cursor.close()
            conn.close()
            
            return True
            
        except ImportError:
            logger.warning("aiomysql not installed for MySQL testing")
            return False
        except Exception as e:
            logger.error(f"MySQL connection test failed: {str(e)}")
            return False
    
    async def _test_oracle_connection(self, connection_info: Dict[str, str]) -> bool:
        """Test Oracle connection"""
        # Placeholder for Oracle connection testing
        logger.warning("Oracle connection testing not implemented")
        return False
    
    async def _test_sqlserver_connection(self, connection_info: Dict[str, str]) -> bool:
        """Test SQL Server connection"""
        # Placeholder for SQL Server connection testing
        logger.warning("SQL Server connection testing not implemented")
        return False
    
    async def _test_sqlite_connection(self, connection_info: Dict[str, str]) -> bool:
        """Test SQLite connection"""
        try:
            import aiosqlite
            
            async with aiosqlite.connect(connection_info["database_url"]) as conn:
                await conn.execute("SELECT 1")
            
            return True
            
        except ImportError:
            logger.warning("aiosqlite not installed for SQLite testing")
            return False
        except Exception as e:
            logger.error(f"SQLite connection test failed: {str(e)}")
            return False
    
    def _extract_host(self, database_url: str) -> str:
        """Extract host from database URL"""
        # Simple URL parsing - you might want to use urllib.parse for more robust parsing
        if "://" in database_url:
            parts = database_url.split("://")[1].split("/")[0].split("@")
            if len(parts) > 1:
                host_port = parts[1]
            else:
                host_port = parts[0]
            
            if ":" in host_port:
                return host_port.split(":")[0]
            return host_port
        return "localhost"
    
    def _extract_port(self, database_url: str) -> int:
        """Extract port from database URL"""
        try:
            if "://" in database_url:
                parts = database_url.split("://")[1].split("/")[0].split("@")
                if len(parts) > 1:
                    host_port = parts[1]
                else:
                    host_port = parts[0]
                
                if ":" in host_port:
                    return int(host_port.split(":")[1])
            return 5432  # Default PostgreSQL port
        except (ValueError, IndexError):
            return 5432
    
    def _extract_database(self, database_url: str) -> str:
        """Extract database name from database URL"""
        if "://" in database_url:
            parts = database_url.split("://")[1].split("/")
            if len(parts) > 1:
                return parts[1].split("?")[0]  # Remove query parameters
        return "postgres"  # Default database
    
    async def get_stats(self) -> DataSourceStatsResponse:
        """Get data source statistics"""
        
        # Total data sources
        total_result = await self.db.execute(
            select(func.count(DataSource.data_source_id))
        )
        total = total_result.scalar() or 0
        
        # Active data sources
        active_result = await self.db.execute(
            select(func.count(DataSource.data_source_id))
            .where(DataSource.is_active == True)
        )
        active = active_result.scalar() or 0
        
        # Inactive data sources
        inactive = total - active
        
        # Sources by type
        type_counts = await self.db.execute(
            select(DataSource.database_type, func.count(DataSource.data_source_id))
            .group_by(DataSource.database_type)
        )
        sources_by_type = {db_type: count for db_type, count in type_counts.all()}
        
        # Recent connection tests (placeholder)
        recent_tests = []
        
        return DataSourceStatsResponse(
            total_data_sources=total,
            active_data_sources=active,
            inactive_data_sources=inactive,
            sources_by_type=sources_by_type,
            recent_connection_tests=recent_tests
        ) 