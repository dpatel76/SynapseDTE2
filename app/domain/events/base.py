"""Base domain event"""
from abc import ABC
from datetime import datetime
from typing import Dict, Any
import uuid


class DomainEvent(ABC):
    """
    Base class for all domain events
    Events are immutable records of things that have happened
    """
    
    def __init__(self):
        self.event_id = str(uuid.uuid4())
        self.occurred_at = datetime.utcnow()
    
    @property
    def event_type(self) -> str:
        """Get the event type name"""
        return self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "data": {
                k: v for k, v in self.__dict__.items() 
                if k not in ["event_id", "occurred_at"]
            }
        }