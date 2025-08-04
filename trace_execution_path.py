#!/usr/bin/env python3
"""Trace the execution path to find where is_match is added"""

import sys
import functools
import json

# Monkey patch json.dumps to trace when is_match is added
original_dumps = json.dumps

def traced_dumps(obj, *args, **kwargs):
    """Traced version of json.dumps"""
    result = original_dumps(obj, *args, **kwargs)
    
    # Check if the result contains is_match
    if isinstance(obj, dict) and 'is_match' in obj:
        import traceback
        print("=" * 80)
        print("FOUND 'is_match' being serialized!")
        print(f"Object: {obj}")
        print("Stack trace:")
        traceback.print_stack()
        print("=" * 80)
    
    return result

# Apply the monkey patch
json.dumps = traced_dumps

# Now import and run the app
sys.path.append('.')
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)