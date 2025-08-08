#!/usr/bin/env python3
import os
from typing import Optional
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    model_config = {
        'env_file': '.env',
        'case_sensitive': True,
        'extra': 'ignore'  # Allow extra fields
    }

print("Testing .env file reading:")
s = TestSettings()
print(f'Direct Pydantic test - Claude: {bool(s.anthropic_api_key)}, Gemini: {bool(s.google_api_key)}')
print(f'Raw env check - ANTHROPIC_API_KEY: {bool(os.getenv("ANTHROPIC_API_KEY"))}')
print(f'Raw env check - GOOGLE_API_KEY: {bool(os.getenv("GOOGLE_API_KEY"))}')

if s.anthropic_api_key:
    print(f'Claude key starts with: {s.anthropic_api_key[:20]}...')
if s.google_api_key:
    print(f'Gemini key starts with: {s.google_api_key[:20]}...')

# Test our actual config
from app.core.config import get_settings
get_settings.cache_clear()
actual_settings = get_settings()
print(f'Actual config - Claude: {bool(actual_settings.anthropic_api_key)}, Gemini: {bool(actual_settings.google_api_key)}') 