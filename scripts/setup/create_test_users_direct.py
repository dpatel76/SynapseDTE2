#!/usr/bin/env python3
"""
Create test users directly in the database
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")
# Convert to sync URL if needed
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test users to create
TEST_USERS = [
    {
        "email": "tester@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "role": "Tester",
        "lob_id": 337,  # Retail Banking
        "is_active": True
    },
    {
        "email": "test_executive@example.com", 
        "password": "password123",
        "first_name": "Test",
        "last_name": "Executive",
        "role": "Test Executive",
        "lob_id": 337,  # Retail Banking
        "is_active": True
    },
    {
        "email": "report_owner@example.com",
        "password": "password123", 
        "first_name": "Report",
        "last_name": "Owner",
        "role": "Report Owner",
        "lob_id": 337,  # Retail Banking
        "is_active": True
    },
    {
        "email": "report_owner_executive@example.com",
        "password": "password123",
        "first_name": "Report Owner",
        "last_name": "Executive", 
        "role": "Report Owner Executive",
        "lob_id": 337,  # Retail Banking
        "is_active": True
    },
    {
        "email": "data_owner@example.com",
        "password": "password123",
        "first_name": "Data",
        "last_name": "Owner",
        "role": "Data Owner",
        "lob_id": 337,  # Retail Banking
        "is_active": True
    },
    {
        "email": "data_executive@example.com",
        "password": "password123",
        "first_name": "Data",
        "last_name": "Executive",
        "role": "Data Executive", 
        "lob_id": 337,  # Retail Banking
        "is_active": True
    }
]

def create_users():
    """Create test users in the database"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            for user in TEST_USERS:
                # Check if user exists
                result = conn.execute(
                    text("SELECT user_id FROM users WHERE email = :email"),
                    {"email": user["email"]}
                )
                
                if result.fetchone():
                    print(f"User {user['email']} already exists, skipping...")
                    continue
                
                # Hash password
                hashed_password = pwd_context.hash(user["password"])
                
                # Insert user
                conn.execute(
                    text("""
                        INSERT INTO users (
                            email, hashed_password, first_name, last_name,
                            role, lob_id, is_active
                        ) VALUES (
                            :email, :hashed_password, :first_name, :last_name,
                            :role, :lob_id, :is_active
                        )
                    """),
                    {
                        "email": user["email"],
                        "hashed_password": hashed_password,
                        "first_name": user["first_name"],
                        "last_name": user["last_name"],
                        "role": user["role"],
                        "lob_id": user["lob_id"],
                        "is_active": user["is_active"]
                    }
                )
                print(f"✅ Created user: {user['email']} ({user['role']})")
            
            trans.commit()
            print("\n✅ All test users created successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error creating users: {e}")
            raise

if __name__ == "__main__":
    print("Creating test users...")
    create_users()