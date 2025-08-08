#!/usr/bin/env python3
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class TestExactSettings(BaseSettings):
    """Test settings that exactly match our main config"""
    
    # Other settings
    app_name: str = "Test App"
    debug: bool = False
    
    # LLM Configuration - exactly like our main config
    anthropic_api_key: Optional[str] = None
    claude_model: str = "claude-3-5-sonnet-20241022"
    
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"
    
    # Same model_config as main
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

@lru_cache()
def get_test_settings() -> TestExactSettings:
    """Get cached settings instance"""
    return TestExactSettings()

print("Testing exact config structure:")
get_test_settings.cache_clear()
settings = get_test_settings()

print(f"Claude key found: {bool(settings.anthropic_api_key)}")
print(f"Gemini key found: {bool(settings.google_api_key)}")

if settings.anthropic_api_key:
    print(f"Claude: {settings.anthropic_api_key[:20]}...")
if settings.google_api_key:
    print(f"Gemini: {settings.google_api_key[:20]}...")

# Test without cache
print("\nTesting without cache:")
direct_settings = TestExactSettings()
print(f"Direct - Claude: {bool(direct_settings.anthropic_api_key)}, Gemini: {bool(direct_settings.google_api_key)}")

# Test with explicit env file path
class TestWithPath(BaseSettings):
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    model_config = {
        "env_file": "/Users/dineshpatel/code/SynapseDT/.env",
        "case_sensitive": True,
        "extra": "ignore"
    }

print("\nTesting with full path:")
path_settings = TestWithPath()
print(f"Path - Claude: {bool(path_settings.anthropic_api_key)}, Gemini: {bool(path_settings.google_api_key)}") 