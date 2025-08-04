"""Email value object"""
import re
from typing import Any


class Email:
    """Value object representing an email address"""
    
    _EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __init__(self, value: str):
        if not value:
            raise ValueError("Email cannot be empty")
        
        value = value.strip().lower()
        
        if not self._EMAIL_REGEX.match(value):
            raise ValueError(f"Invalid email format: {value}")
        
        self._value = value
    
    @property
    def value(self) -> str:
        """Get the email value"""
        return self._value
    
    def __str__(self) -> str:
        return self._value
    
    def __repr__(self) -> str:
        return f"Email('{self._value}')"
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Email):
            return False
        return self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)