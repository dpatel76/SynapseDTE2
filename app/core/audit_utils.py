"""
Audit utilities for setting audit fields explicitly
"""

from typing import Any
from app.models.user import User
from app.models.audit_mixin import AuditMixin


def set_audit_fields_on_create(instance: Any, current_user: User) -> None:
    """
    Set audit fields when creating a new record.
    
    Args:
        instance: The model instance being created
        current_user: The user performing the action
    """
    if isinstance(instance, AuditMixin) and current_user:
        instance.created_by_id = current_user.user_id
        instance.updated_by_id = current_user.user_id


def set_audit_fields_on_update(instance: Any, current_user: User) -> None:
    """
    Set audit fields when updating a record.
    
    Args:
        instance: The model instance being updated
        current_user: The user performing the action
    """
    if isinstance(instance, AuditMixin) and current_user:
        instance.updated_by_id = current_user.user_id