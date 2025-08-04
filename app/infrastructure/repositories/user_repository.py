"""
SQLAlchemy implementation of UserRepository - Clean Architecture
"""
from typing import List, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.interfaces.repositories import UserRepository
from app.domain.entities.user import UserEntity
from app.domain.value_objects import Email
from app.models.user import User as UserModel


class UserRepositoryImpl(UserRepository):
    """SQLAlchemy implementation of user repository with clean architecture"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def find_by_id(self, user_id: int) -> Optional[UserEntity]:
        """Find user by ID"""
        result = await self.session.execute(
            select(UserModel)
            .where(UserModel.user_id == user_id)
            .options(
                selectinload(UserModel.permissions),
                selectinload(UserModel.created_reports),
                selectinload(UserModel.assigned_cycles)
            )
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return None
        
        return self._to_entity(user_model)
    
    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        """Find user by email"""
        import time
        import structlog
        logger = structlog.get_logger()
        
        start = time.time()
        logger.info("UserRepository.find_by_email started", email=email)
        
        try:
            logger.info("Executing SQL query", elapsed=f"{time.time() - start:.2f}s")
            result = await self.session.execute(
                select(UserModel)
                .where(UserModel.email == email)
                .options(
                    # Don't load relationships during login to avoid ambiguous foreign key issues
                )
            )
            logger.info("SQL query executed", elapsed=f"{time.time() - start:.2f}s")
            
            user_model = result.scalar_one_or_none()
            logger.info(f"User model found: {user_model is not None}", elapsed=f"{time.time() - start:.2f}s")
            
            if not user_model:
                return None
            
            logger.info("Converting to entity", elapsed=f"{time.time() - start:.2f}s")
            entity = self._to_entity(user_model)
            logger.info("Entity created", elapsed=f"{time.time() - start:.2f}s")
            return entity
        except Exception as e:
            logger.error(f"Error in find_by_email: {str(e)}", elapsed=f"{time.time() - start:.2f}s")
            raise
    
    async def find_all(self) -> List[UserEntity]:
        """Find all users"""
        result = await self.session.execute(
            select(UserModel)
            .order_by(UserModel.created_at.desc())
        )
        user_models = result.scalars().all()
        
        return [self._to_entity(user) for user in user_models]
    
    async def find_by_role(self, role: str) -> List[UserEntity]:
        """Find users by role"""
        result = await self.session.execute(
            select(UserModel)
            .where(UserModel.role == role)
            .order_by(UserModel.first_name, UserModel.last_name)
        )
        user_models = result.scalars().all()
        
        return [self._to_entity(user) for user in user_models]
    
    async def create(self, user: UserEntity) -> UserEntity:
        """Create a new user"""
        user_model = UserModel(
            email=user.email.value,
            hashed_password=user.hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active
        )
        
        self.session.add(user_model)
        await self.session.commit()
        await self.session.refresh(user_model)
        
        return self._to_entity(user_model)
    
    async def update(self, user: UserEntity) -> UserEntity:
        """Update an existing user"""
        result = await self.session.execute(
            select(UserModel)
            .where(UserModel.user_id == user.user_id)
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            raise ValueError(f"User with id {user.user_id} not found")
        
        # Update fields
        user_model.email = user.email.value
        user_model.first_name = user.first_name
        user_model.last_name = user.last_name
        user_model.role = user.role
        user_model.is_active = user.is_active
        
        if user.hashed_password:
            user_model.hashed_password = user.hashed_password
        
        await self.session.commit()
        await self.session.refresh(user_model)
        
        return self._to_entity(user_model)
    
    async def delete(self, user_id: int) -> bool:
        """Delete a user (soft delete)"""
        result = await self.session.execute(
            select(UserModel)
            .where(UserModel.user_id == user_id)
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return False
        
        user_model.is_active = False
        await self.session.commit()
        
        return True
    
    async def find_active_users(self) -> List[UserEntity]:
        """Find all active users"""
        result = await self.session.execute(
            select(UserModel)
            .where(UserModel.is_active == True)
            .order_by(UserModel.first_name, UserModel.last_name)
        )
        user_models = result.scalars().all()
        
        return [self._to_entity(user) for user in user_models]
    
    async def search_users(self, query: str) -> List[UserEntity]:
        """Search users by name or email"""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(UserModel)
            .where(
                or_(
                    UserModel.first_name.ilike(search_pattern),
                    UserModel.last_name.ilike(search_pattern),
                    UserModel.email.ilike(search_pattern)
                )
            )
            .order_by(UserModel.first_name, UserModel.last_name)
        )
        user_models = result.scalars().all()
        
        return [self._to_entity(user) for user in user_models]
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get permissions for a user"""
        # Get user with permissions
        result = await self.session.execute(
            select(UserModel)
            .where(UserModel.user_id == user_id)
            .options(
                selectinload(UserModel.permissions)
            )
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return []
        
        # Get role-based permissions
        role_permissions = self._get_role_permissions(user_model.role)
        
        # Get user-specific permissions
        user_permissions = []
        if hasattr(user_model, 'permissions') and user_model.permissions:
            for up in user_model.permissions:
                if up.permission and up.granted:
                    user_permissions.append(f"{up.permission.resource}:{up.permission.action}")
        
        # Combine and deduplicate
        all_permissions = list(set(role_permissions + user_permissions))
        
        return all_permissions
    
    def _to_entity(self, user_model: UserModel) -> UserEntity:
        """Convert database model to domain entity"""
        return UserEntity(
            user_id=user_model.user_id,
            email=Email(user_model.email),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            role=user_model.role,
            is_active=user_model.is_active,
            hashed_password=user_model.hashed_password,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at
        )
    
    def _get_role_permissions(self, role: str) -> List[str]:
        """Get default permissions for a role"""
        # This is a simplified version - in production, this would come from database
        role_permissions_map = {
            "Tester": [
                "cycles:read",
                "reports:read",
                "planning:read",
                "scoping:read",
                "sample_selection:read",
                "sample_selection:create",
                "request_info:read",
                "test_execution:read",
                "test_execution:create",
                "test_execution:update",
                "observation_management:read",
                "observation_management:create"
            ],
            "Test Manager": [
                "cycles:*",
                "reports:*",
                "planning:*",
                "scoping:*",
                "sample_selection:*",
                "request_info:*",
                "test_execution:*",
                "observation_management:*",
                "users:read"
            ],
            "Report Owner": [
                "cycles:read",
                "reports:read",
                "planning:read",
                "planning:approve",
                "scoping:read",
                "scoping:approve",
                "sample_selection:read",
                "sample_selection:approve",
                "request_info:read",
                "request_info:update",
                "test_execution:read",
                "observation_management:read",
                "observation_management:approve"
            ],
            "Report Owner Executive": [
                "cycles:read",
                "reports:read",
                "dashboards:read",
                "metrics:read",
                "observation_management:read",
                "observation_management:approve"
            ],
            "Data Owner": [
                "cycles:read",
                "reports:read",
                "request_info:read",
                "request_info:update",
                "request_info:upload",
                "dashboards:read"
            ],
            "CDO": [
                "cycles:read",
                "reports:read",
                "data_owner:*",
                "request_info:read",
                "dashboards:read"
            ]
        }
        
        return role_permissions_map.get(role, [])
    
    # Methods required by abstract base class interface
    async def get(self, user_id: int) -> Optional[dict]:
        """Get a user by ID - returns dict for compatibility"""
        user_entity = await self.find_by_id(user_id)
        if not user_entity:
            return None
        
        return {
            "user_id": user_entity.user_id,
            "email": user_entity.email.value,
            "first_name": user_entity.first_name,
            "last_name": user_entity.last_name,
            "role": user_entity.role,
            "is_active": user_entity.is_active,
            "created_at": user_entity.created_at
        }
    
    async def find_testers(self) -> List[dict]:
        """Find all users with tester role - returns dict list for compatibility"""
        tester_entities = await self.find_by_role("Tester")
        return [
            {
                "user_id": user.user_id,
                "email": user.email.value,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_active": user.is_active
            }
            for user in tester_entities
        ]