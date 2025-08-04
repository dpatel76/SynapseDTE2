#!/usr/bin/env python3
"""Get a working auth token"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

# Create token for user_id=3 (Test User)
user_id = 3
payload = {
    "sub": str(user_id),
    "user_id": user_id,
    "exp": datetime.now(timezone.utc) + timedelta(days=7)
}

token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
print(f"Token for user_id={user_id}:")
print(token)

# Save to file
with open('.test_token', 'w') as f:
    f.write(token)
print("\nToken saved to .test_token")