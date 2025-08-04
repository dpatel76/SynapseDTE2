"""User domain entity"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from app.domain.entities.base import BaseEntity
from app.domain.value_objects import Email


@dataclass
class UserEntity:
    """User domain entity"""
    user_id: Optional[int]
    email: Email
    first_name: str
    last_name: str
    role: str
    is_active: bool = True
    hashed_password: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    last_login: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission"""
        return permission in self.permissions
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return self.role == role
    
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role in ['Admin', 'Test Executive']
    
    def can_access_report(self, report_id: int) -> bool:
        """Check if user can access a specific report"""
        # This would be more complex in a real implementation
        # checking report ownership, LOB assignment, etc.
        if self.is_admin():
            return True
        
        # Check specific permissions
        return self.has_permission(f'reports:{report_id}:read')