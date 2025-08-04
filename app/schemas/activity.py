from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ActivityResponse(BaseModel):
    audit_id: int
    user_id: Optional[int] = None
    action: str
    table_name: str
    record_id: int
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    timestamp: datetime
    session_id: Optional[str] = None

    class Config:
        from_attributes = True 