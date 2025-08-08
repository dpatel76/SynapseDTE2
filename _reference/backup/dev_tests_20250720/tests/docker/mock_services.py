#!/usr/bin/env python3
"""
Mock Services for Testing Without Real Infrastructure
Provides lightweight mock services for testing containerization
"""

import asyncio
import json
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import redis
from unittest.mock import MagicMock

# Mock FastAPI Backend
mock_app = FastAPI(title="Mock SynapseDTE Backend")

# In-memory data store
mock_data = {
    "users": {},
    "test_cycles": {},
    "health_status": "healthy"
}

@mock_app.get("/api/v1/health")
async def health_check():
    """Mock health endpoint"""
    return {
        "status": mock_data["health_status"],
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "temporal": "healthy"
        }
    }

@mock_app.post("/api/v1/auth/register")
async def register_user(user_data: Dict[str, Any]):
    """Mock user registration"""
    user_id = len(mock_data["users"]) + 1
    mock_data["users"][user_id] = user_data
    return {"id": user_id, "email": user_data.get("email")}

@mock_app.post("/api/v1/auth/login")
async def login_user(username: str, password: str):
    """Mock user login"""
    return {
        "access_token": "mock_token_12345",
        "token_type": "bearer"
    }

@mock_app.get("/api/v1/users/me")
async def get_current_user():
    """Mock get current user"""
    return {
        "id": 1,
        "email": "test@synapse.local",
        "first_name": "Test",
        "last_name": "User"
    }

@mock_app.post("/api/v1/test-cycles")
async def create_test_cycle(cycle_data: Dict[str, Any]):
    """Mock test cycle creation"""
    cycle_id = len(mock_data["test_cycles"]) + 1
    mock_data["test_cycles"][cycle_id] = cycle_data
    return {"id": cycle_id, **cycle_data}


class MockRedis:
    """Mock Redis client for testing"""
    
    def __init__(self):
        self.data = {}
    
    def set(self, key: str, value: str):
        self.data[key] = value
        return True
    
    def get(self, key: str):
        return self.data.get(key)
    
    def ping(self):
        return True


class MockTemporalClient:
    """Mock Temporal client for testing"""
    
    async def start_workflow(self, workflow: str, args: Dict[str, Any]):
        return {
            "workflow_id": f"mock_workflow_{workflow}",
            "run_id": "mock_run_12345"
        }
    
    async def get_workflow_status(self, workflow_id: str):
        return {
            "status": "completed",
            "result": {"success": True}
        }


def create_mock_services():
    """Create mock service instances"""
    return {
        "backend": mock_app,
        "redis": MockRedis(),
        "temporal": MockTemporalClient(),
        "database": MagicMock()  # Mock database connection
    }


async def run_mock_backend(port: int = 18000):
    """Run mock backend server"""
    config = uvicorn.Config(
        mock_app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # Run mock backend
    print("🎭 Starting mock backend on port 18000...")
    asyncio.run(run_mock_backend())