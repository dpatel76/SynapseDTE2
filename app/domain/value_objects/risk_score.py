"""Risk Score Value Object"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RiskScore:
    """
    Represents a risk score for an attribute or test
    Immutable value object with validation
    """
    value: int
    
    def __post_init__(self):
        """Validate risk score is within valid range"""
        if not 1 <= self.value <= 10:
            raise ValueError(f"Risk score must be between 1 and 10, got {self.value}")
    
    @property
    def is_high_risk(self) -> bool:
        """Check if this is a high risk score (7-10)"""
        return self.value >= 7
    
    @property
    def is_medium_risk(self) -> bool:
        """Check if this is a medium risk score (4-6)"""
        return 4 <= self.value <= 6
    
    @property
    def is_low_risk(self) -> bool:
        """Check if this is a low risk score (1-3)"""
        return self.value <= 3
    
    @property
    def risk_level(self) -> str:
        """Get risk level as string"""
        if self.is_high_risk:
            return "High"
        elif self.is_medium_risk:
            return "Medium"
        else:
            return "Low"
    
    def __str__(self) -> str:
        return f"{self.value}/10 ({self.risk_level})"
    
    def __lt__(self, other):
        if not isinstance(other, RiskScore):
            return NotImplemented
        return self.value < other.value
    
    def __le__(self, other):
        if not isinstance(other, RiskScore):
            return NotImplemented
        return self.value <= other.value
    
    @classmethod
    def high(cls) -> 'RiskScore':
        """Create a high risk score"""
        return cls(8)
    
    @classmethod
    def medium(cls) -> 'RiskScore':
        """Create a medium risk score"""
        return cls(5)
    
    @classmethod
    def low(cls) -> 'RiskScore':
        """Create a low risk score"""
        return cls(2)