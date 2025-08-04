"""
Audit Mixin for tracking user creation and updates
Provides created_by and updated_by fields for all models
"""

from sqlalchemy import Column, Integer, ForeignKey, event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declared_attr
from typing import Optional


class AuditMixin:
    """
    Mixin that adds created_by and updated_by fields to track user actions.
    
    This mixin should be added to models that need user tracking.
    It works in conjunction with the audit_listener to automatically
    populate these fields.
    """
    
    @declared_attr
    def created_by_id(cls):
        """ID of the user who created this record"""
        return Column(
            Integer, 
            ForeignKey('users.user_id', ondelete='SET NULL'),
            nullable=True,
            comment="ID of user who created this record"
        )
    
    @declared_attr
    def updated_by_id(cls):
        """ID of the user who last updated this record"""
        return Column(
            Integer, 
            ForeignKey('users.user_id', ondelete='SET NULL'),
            nullable=True,
            comment="ID of user who last updated this record"
        )
    
    @declared_attr
    def created_by(cls):
        """Relationship to the user who created this record"""
        return relationship(
            "User",
            foreign_keys=[cls.created_by_id],
            primaryjoin=f"User.user_id=={cls.__name__}.created_by_id",
            lazy="select"
        )
    
    @declared_attr
    def updated_by(cls):
        """Relationship to the user who last updated this record"""
        return relationship(
            "User",
            foreign_keys=[cls.updated_by_id],
            primaryjoin=f"User.user_id=={cls.__name__}.updated_by_id",
            lazy="select"
        )


def get_current_user_id() -> Optional[int]:
    """
    Get the current user ID from the context.
    This is set by the middleware for each request.
    """
    from app.core.context import get_current_user_context
    
    try:
        user_context = get_current_user_context()
        if user_context:
            return user_context.get('user_id')
    except:
        # If we're not in a request context (e.g., migrations, scripts)
        return None
    
    return None


def audit_insert_listener(mapper, connection, target):
    """
    SQLAlchemy event listener for insert operations.
    Automatically sets created_by_id and updated_by_id.
    """
    user_id = get_current_user_id()
    if user_id and hasattr(target, 'created_by_id'):
        target.created_by_id = user_id
        target.updated_by_id = user_id


def audit_update_listener(mapper, connection, target):
    """
    SQLAlchemy event listener for update operations.
    Automatically sets updated_by_id.
    """
    user_id = get_current_user_id()
    if user_id and hasattr(target, 'updated_by_id'):
        target.updated_by_id = user_id


def register_audit_listeners():
    """
    Register the audit listeners for all models that use AuditMixin.
    This should be called during application initialization.
    """
    from app.core.database import Base
    
    # Import all models to ensure they're registered
    import app.models  # This imports the __init__.py which imports all models
    
    # Get all mapped classes
    for mapper in Base.registry.mappers:
        model_class = mapper.class_
        
        # Check if this model uses AuditMixin
        if hasattr(model_class, '__mro__') and AuditMixin in model_class.__mro__:
            # Register event listeners
            event.listen(model_class, 'before_insert', audit_insert_listener, propagate=True)
            event.listen(model_class, 'before_update', audit_update_listener, propagate=True)