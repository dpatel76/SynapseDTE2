#!/usr/bin/env python3
from typing import Optional
from pydantic_settings import BaseSettings

print("=== Testing case_sensitive setting ===")

# Test 1: Without case_sensitive
class WithoutCaseSensitive(BaseSettings):
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    model_config = {'env_file': '.env', 'extra': 'ignore'}

test1 = WithoutCaseSensitive()
print(f"Without case_sensitive - Claude: {bool(test1.anthropic_api_key)}, Gemini: {bool(test1.google_api_key)}")

# Test 2: With case_sensitive = True
class WithCaseSensitive(BaseSettings):
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    model_config = {
        'env_file': '.env', 
        'case_sensitive': True,
        'extra': 'ignore'
    }

test2 = WithCaseSensitive()
print(f"With case_sensitive=True - Claude: {bool(test2.anthropic_api_key)}, Gemini: {bool(test2.google_api_key)}")

# Test 3: With case_sensitive = False
class WithCaseSensitiveFalse(BaseSettings):
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    model_config = {
        'env_file': '.env', 
        'case_sensitive': False,
        'extra': 'ignore'
    }

test3 = WithCaseSensitiveFalse()
print(f"With case_sensitive=False - Claude: {bool(test3.anthropic_api_key)}, Gemini: {bool(test3.google_api_key)}") 