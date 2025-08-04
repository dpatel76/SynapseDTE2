"""Report domain entity"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Base entity import removed - using dataclass directly


@dataclass
class ReportEntity:
    """Report domain entity with business logic"""
    # Required fields first
    report_id: int
    report_name: str
    report_type: str
    lob_id: int
    frequency: str
    business_unit: str
    report_owner_id: int
    
    # Optional fields
    description: Optional[str] = None
    regulatory_requirements: Optional[str] = None
    report_owner_executive_id: Optional[int] = None
    
    # Status and timing
    status: str = "Active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Attributes count
    total_attributes: int = 0
    mandatory_attributes: int = 0
    critical_attributes: int = 0
    
    def is_regulatory(self) -> bool:
        """Check if report is regulatory"""
        return bool(self.regulatory_requirements)
    
    def is_critical(self) -> bool:
        """Check if report is critical based on type and attributes"""
        critical_types = ["FINRA", "SEC", "CFTC", "Federal Reserve"]
        return self.report_type in critical_types or self.critical_attributes > 0
    
    def get_priority(self) -> str:
        """Get report priority"""
        if self.is_critical():
            return "Critical"
        elif self.is_regulatory():
            return "High"
        elif self.mandatory_attributes > 10:
            return "Medium"
        else:
            return "Low"
    
    def can_be_assigned_to(self, user_role: str) -> bool:
        """Check if report can be assigned to a user with given role"""
        allowed_roles = ["Tester", "Test Manager", "Test Executive"]
        return user_role in allowed_roles
    
    def get_completion_percentage(self, completed_attributes: int) -> float:
        """Calculate completion percentage"""
        if self.total_attributes == 0:
            return 0.0
        return (completed_attributes / self.total_attributes) * 100
    
    def validate(self) -> List[str]:
        """Validate report entity"""
        errors = []
        
        if not self.report_name:
            errors.append("Report name is required")
        
        if not self.report_type:
            errors.append("Report type is required")
        
        if self.lob_id <= 0:
            errors.append("Valid LOB ID is required")
        
        if self.report_owner_id <= 0:
            errors.append("Valid report owner ID is required")
        
        return errors