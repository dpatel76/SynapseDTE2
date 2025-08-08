#!/usr/bin/env python3
"""Quick test of server startup"""

import subprocess
import time
import sys

# Start the server
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--port', '8001'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait a bit
time.sleep(3)

# Check if it's still running
if proc.poll() is None:
    print("✅ Server started successfully!")
    proc.terminate()
else:
    print("❌ Server failed to start")
    stdout, stderr = proc.communicate()
    print("STDOUT:", stdout)
    print("STDERR:", stderr[:1000])