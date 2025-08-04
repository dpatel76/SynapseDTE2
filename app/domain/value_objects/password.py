"""Password value object"""
import re
from typing import Any


class Password:
    """Value object representing a password"""
    
    # Minimum 8 characters, at least one letter and one number
    _PASSWORD_REGEX = re.compile(r'^(?=.*[A-Za-z])(?=.*\d).{8,}$')
    
    def __init__(self, value: str):
        if not value:
            raise ValueError("Password cannot be empty")
        
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # For production, we'd add more complex validation
        # For now, just basic length check
        self._value = value
    
    @property
    def value(self) -> str:
        """Get the password value (hashed in production)"""
        return self._value
    
    def __str__(self) -> str:
        # Never expose the actual password
        return "********"
    
    def __repr__(self) -> str:
        return "Password(****)"
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Password):
            return False
        return self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)