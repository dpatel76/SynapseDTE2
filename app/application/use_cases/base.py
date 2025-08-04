"""Base use case class"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List
from dataclasses import dataclass

from app.domain.events.base import DomainEvent

# Generic types for input and output
TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')


@dataclass
class UseCaseResult(Generic[TOutput]):
    """Result wrapper for use cases"""
    success: bool
    data: Optional[TOutput] = None
    error: Optional[str] = None
    events: List[DomainEvent] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []


class UseCase(ABC, Generic[TInput, TOutput]):
    """Base class for all use cases"""
    
    @abstractmethod
    async def execute(self, request: TInput) -> UseCaseResult[TOutput]:
        """Execute the use case"""
        pass
    
    def _success(self, data: TOutput, events: Optional[List[DomainEvent]] = None) -> UseCaseResult[TOutput]:
        """Create a success result"""
        return UseCaseResult(
            success=True,
            data=data,
            events=events or []
        )
    
    def _failure(self, error: str) -> UseCaseResult[TOutput]:
        """Create a failure result"""
        return UseCaseResult(
            success=False,
            error=error
        )