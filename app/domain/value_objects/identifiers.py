"""Domain value objects for identifiers"""

from typing import NewType


# Type aliases for domain identifiers
CycleId = NewType('CycleId', int)
ReportId = NewType('ReportId', int)
UserId = NewType('UserId', int)
AttributeId = NewType('AttributeId', int)
SampleId = NewType('SampleId', str)
TestCaseId = NewType('TestCaseId', str)
ObservationId = NewType('ObservationId', str)
DocumentId = NewType('DocumentId', str)


class EntityId:
    """Base value object for entity identifiers"""
    
    def __init__(self, value: str | int):
        if not value:
            raise ValueError("Entity ID cannot be empty")
        self._value = value
    
    @property
    def value(self):
        return self._value
    
    def __str__(self):
        return str(self._value)
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._value == other._value
    
    def __hash__(self):
        return hash(self._value)