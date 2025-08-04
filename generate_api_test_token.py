#!/usr/bin/env python3
"""
Generate a test token for API testing
"""

import jwt
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://synapse_user:synapse_password@localhost/synapse_dt"
SECRET_KEY = "synapsedtekey"  # Should match your FastAPI secret
ALGORITHM = "HS256"

def generate_token(email: str):
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get user info
        result = conn.execute(text("""
            SELECT user_id, email, role, first_name, last_name
            FROM users
            WHERE email = :email AND is_active = true
        """), {"email": email}).fetchone()
        
        if not result:
            print(f"User {email} not found or inactive")
            return None
            
        user_id, email, role, first_name, last_name = result
        
        # Create token payload
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "first_name": first_name,
            "last_name": last_name,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        
        # Generate token
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "tester@example.com"
    token = generate_token(email)
    if token:
        print(token)
    else:
        sys.exit(1)
