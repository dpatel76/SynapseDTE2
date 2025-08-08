from pydantic_settings import BaseSettings
from typing import Optional
import os

print("=== Pydantic Settings Diagnostic ===")

# Test 1: Environment variable
os.environ['TEST_KEY'] = 'hello_world'

class EnvTest(BaseSettings):
    test_key: Optional[str] = None

env_result = EnvTest()
print(f"Environment test: {env_result.test_key}")

# Test 2: Our .env file
class DotEnvTest(BaseSettings):
    database_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    model_config = {
        'env_file': '.env',
        'extra': 'ignore'
    }

dot_env_result = DotEnvTest()
print(f"DATABASE_URL found: {bool(dot_env_result.database_url)}")
print(f"ANTHROPIC_API_KEY found: {bool(dot_env_result.anthropic_api_key)}")
print(f"GOOGLE_API_KEY found: {bool(dot_env_result.google_api_key)}")

if dot_env_result.anthropic_api_key:
    print(f"Anthropic value: {dot_env_result.anthropic_api_key[:15]}...")
    
print("\n=== Raw file content ===")
with open('.env', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines, 1):
        print(f"Line {i}: {repr(line)}") 