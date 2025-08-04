#!/usr/bin/env python3
from app.core.config import Settings, get_settings
import traceback

print("=== Testing Actual Settings Class ===")

try:
    # Test direct Settings creation
    print("1. Testing direct Settings creation...")
    direct_settings = Settings()
    print(f"   Claude: {bool(direct_settings.anthropic_api_key)}")
    print(f"   Gemini: {bool(direct_settings.google_api_key)}")
    
    if direct_settings.anthropic_api_key:
        print(f"   Anthropic key: {direct_settings.anthropic_api_key[:15]}...")
    
except Exception as e:
    print(f"   Error: {e}")
    traceback.print_exc()

try:
    # Test get_settings function
    print("\n2. Testing get_settings function...")
    get_settings.cache_clear()
    cached_settings = get_settings()
    print(f"   Claude: {bool(cached_settings.anthropic_api_key)}")
    print(f"   Gemini: {bool(cached_settings.google_api_key)}")
    
    if cached_settings.anthropic_api_key:
        print(f"   Anthropic key: {cached_settings.anthropic_api_key[:15]}...")
        
except Exception as e:
    print(f"   Error: {e}")
    traceback.print_exc()

print("\n3. Comparing with working diagnostic...")
from typing import Optional
from pydantic_settings import BaseSettings

class WorkingSettings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    model_config = {'env_file': '.env', 'extra': 'ignore'}

working = WorkingSettings()
print(f"   Working - Claude: {bool(working.anthropic_api_key)}, Gemini: {bool(working.google_api_key)}") 