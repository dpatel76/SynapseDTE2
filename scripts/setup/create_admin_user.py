"""
Script to create an admin user in the SynapseDT application
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.auth import get_password_hash
from app.models.user import User
from app.core.config import settings

# Create async database engine
engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def create_admin_user():
    """Create an admin user"""
    async with AsyncSessionLocal() as db:
        try:
            # Admin user configuration
            admin_data = {
                "first_name": "System",
                "last_name": "Admin",
                "email": "admin@example.com",
                "phone": "1234567899",
                "role": "Admin",
                "password": "AdminUser123!",
                "needs_lob": False
            }
            
            # Create admin user
            admin = User(
                first_name=admin_data["first_name"],
                last_name=admin_data["last_name"],
                email=admin_data["email"],
                phone=admin_data["phone"],
                role=admin_data["role"],
                hashed_password=get_password_hash(admin_data["password"]),
                lob_id=None,  # Admin doesn't need a specific LOB
                is_active=True
            )
            db.add(admin)
            
            # Commit changes
            await db.commit()
            
            print("Successfully created admin user:")
            print(f"- Role: {admin_data['role']}")
            print(f"  Email: {admin_data['email']}")
            print(f"  Password: {admin_data['password']}")
                
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(create_admin_user()) 