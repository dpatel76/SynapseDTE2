#!/usr/bin/env python3

print("Manual .env file parsing:")
with open('.env', 'r') as f:
    content = f.read()

print("Raw content:")
print(repr(content))
print("\nParsed lines:")
for line_num, line in enumerate(content.split('\n'), 1):
    if line.strip() and not line.startswith('#'):
        if '=' in line:
            key, value = line.split('=', 1)
            print(f"Line {line_num}: {key} = {value[:20]}...")
        else:
            print(f"Line {line_num}: Invalid format: {line}")

print("\nTesting python-dotenv:")
try:
    from dotenv import dotenv_values
    env_vars = dotenv_values('.env')
    print(f"dotenv found: {list(env_vars.keys())}")
    for key in ['ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']:
        if key in env_vars:
            print(f"{key}: {env_vars[key][:20]}...")
except ImportError:
    print("python-dotenv not available") 