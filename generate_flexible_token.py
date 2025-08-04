import asyncio
import argparse
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
from app.core.auth import create_access_token

async def create_test_token(email: str):
    async with AsyncSessionLocal() as db:
        # Get user by email
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            token = create_access_token(
                data={"sub": str(user.user_id), "user_id": user.user_id}
            )
            with open('.test_token', 'w') as f:
                f.write(token)
            print(f"Token created for {user.email} (ID: {user.user_id}, Role: {user.role})")
            return token
        else:
            print(f"User with email {email} not found")
            return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate test token for a user')
    parser.add_argument('email', help='Email address of the user')
    args = parser.parse_args()
    
    asyncio.run(create_test_token(args.email))