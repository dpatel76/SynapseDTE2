"""
Base model class with common fields and functionality
"""

from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from app.core.database import Base
from app.models.audit_mixin import AuditMixin


class TimestampMixin:
    """Mixin for timestamp fields only"""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """Base model with auto-generated id and timestamps"""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True, index=True)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


class CustomPKModel(Base, TimestampMixin):
    """Base model for models with custom primary keys"""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    def __repr__(self):
        return f"<{self.__class__.__name__}()>"


class AuditableBaseModel(BaseModel, AuditMixin):
    """Base model with auto-generated id, timestamps, and audit fields"""
    
    __abstract__ = True


class AuditableCustomPKModel(CustomPKModel, AuditMixin):
    """Base model for models with custom primary keys and audit fields"""
    
    __abstract__ = True 