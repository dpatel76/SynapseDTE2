"""
Base service class with common functionality for audit fields
"""

from typing import Optional, Type, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base
from app.models.audit_mixin import AuditMixin
from app.models.user import User

T = TypeVar('T', bound=Base)


class BaseService(Generic[T]):
    """
    Base service class that provides common functionality for services,
    including standard handling of audit fields.
    """
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
    
    def set_audit_fields_on_create(self, instance: T, current_user: User) -> None:
        """
        Set audit fields when creating a new record.
        
        Args:
            instance: The model instance being created
            current_user: The user performing the action
        """
        if isinstance(instance, AuditMixin) and current_user:
            instance.created_by_id = current_user.user_id
            instance.updated_by_id = current_user.user_id
    
    def set_audit_fields_on_update(self, instance: T, current_user: User) -> None:
        """
        Set audit fields when updating a record.
        
        Args:
            instance: The model instance being updated
            current_user: The user performing the action
        """
        if isinstance(instance, AuditMixin) and current_user:
            instance.updated_by_id = current_user.user_id
    
    async def create(self, db: AsyncSession, instance: T, current_user: Optional[User] = None) -> T:
        """
        Create a new record with audit fields.
        
        Args:
            db: Database session
            instance: The model instance to create
            current_user: The user performing the action
            
        Returns:
            The created instance
        """
        if current_user:
            self.set_audit_fields_on_create(instance, current_user)
        
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return instance
    
    async def update(self, db: AsyncSession, instance: T, current_user: Optional[User] = None) -> T:
        """
        Update a record with audit fields.
        
        Args:
            db: Database session
            instance: The model instance to update
            current_user: The user performing the action
            
        Returns:
            The updated instance
        """
        if current_user:
            self.set_audit_fields_on_update(instance, current_user)
        
        await db.commit()
        await db.refresh(instance)
        return instance