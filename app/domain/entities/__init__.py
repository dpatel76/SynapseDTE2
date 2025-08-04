"""Domain entities - Rich domain models with business logic"""

from .user import UserEntity
from .test_cycle import TestCycle
from .report import ReportEntity

__all__ = [
    'UserEntity',
    'TestCycle',
    'ReportEntity'
]