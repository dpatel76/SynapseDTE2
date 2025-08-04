#!/usr/bin/env python3
"""Fix get_async_session imports in temporal activities"""

import os
import re

files_to_fix = [
    "app/temporal/activities/notification_activities.py",
    "app/temporal/activities/test_activities.py"
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace import
        content = content.replace(
            "from app.core.database import get_async_session",
            "from app.core.database import get_db"
        )
        
        # Replace usage
        content = content.replace(
            "async with get_async_session() as db:",
            "async with get_db() as db:"
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Fixed {file_path}")
    else:
        print(f"File not found: {file_path}")

print("Done!")