import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
from app.core.auth import create_access_token

async def create_test_token():
    async with AsyncSessionLocal() as db:
        # Get tester user
        result = await db.execute(
            select(User).where(User.email == "jane.smith@techcorp.com")
        )
        user = result.scalar_one_or_none()
        
        if user:
            token = create_access_token(
                data={"sub": user.email, "user_id": user.user_id}
            )
            with open('.test_token', 'w') as f:
                f.write(token)
            print(f"Token created for {user.email}")
        else:
            print("User not found")

if __name__ == "__main__":
    asyncio.run(create_test_token())