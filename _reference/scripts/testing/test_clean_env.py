#!/usr/bin/env python3
from typing import Optional
from pydantic_settings import BaseSettings
import sys
import os

# Clear any existing environment variables
if 'ANTHROPIC_API_KEY' in os.environ:
    del os.environ['ANTHROPIC_API_KEY']
if 'GOOGLE_API_KEY' in os.environ:
    del os.environ['GOOGLE_API_KEY']

class TestSettings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    model_config = {
        'env_file': '.env',
        'case_sensitive': True,
        'extra': 'ignore'
    }

print("Testing with clean environment:")
s = TestSettings()
print(f'Claude found: {bool(s.anthropic_api_key)}')
print(f'Gemini found: {bool(s.google_api_key)}')

if s.anthropic_api_key:
    print(f'Claude key: {s.anthropic_api_key[:15]}...')
if s.google_api_key:
    print(f'Gemini key: {s.google_api_key[:15]}...')

# Test the actual app settings
sys.path.insert(0, '.')
from app.core.config import get_settings
get_settings.cache_clear()
actual = get_settings()
print(f'App settings - Claude: {bool(actual.anthropic_api_key)}, Gemini: {bool(actual.google_api_key)}') 