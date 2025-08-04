from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

app = FastAPI()

@app.get("/test/{cycle_id}/reports/{report_id}/observations")
async def test_observations(
    cycle_id: int,
    report_id: int,
    observation_status: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = None,
    observation_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test endpoint"""
    return {
        "cycle_id": cycle_id,
        "report_id": report_id,
        "status": observation_status,
        "user": current_user.email if current_user else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)