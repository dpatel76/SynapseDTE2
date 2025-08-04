"""Base entity for domain entities"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.domain.events.base import DomainEvent


@dataclass
class BaseEntity(ABC):
    """Base class for all domain entities"""
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def add_domain_event(self, event: DomainEvent):
        """Add a domain event"""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get all domain events"""
        return self._domain_events.copy()
    
    def clear_domain_events(self):
        """Clear all domain events"""
        self._domain_events.clear()
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()