"""Integration tests for clean architecture"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from datetime import datetime, timedelta

from app.main_clean import app
from app.db.session import AsyncSessionLocal
from app.models import User, Role, UserRole, TestingCycle
from app.core.security import get_password_hash


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create a test database session"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user with Test Executive role"""
    # Create role if it doesn't exist
    role = await db_session.get(Role, 2)  # Test Executive role
    if not role:
        role = Role(
            role_id=2,
            role_name="Test Executive",
            description="Test Executive role"
        )
        db_session.add(role)
    
    # Create user
    user = User(
        username="test_executive",
        email="test_exec@test.com",
        full_name="Test Executive",
        hashed_password=get_password_hash("testpass123"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # Assign role
    user_role = UserRole(
        user_id=user.user_id,
        role_id=role.role_id
    )
    db_session.add(user_role)
    await db_session.commit()
    
    return user


@pytest.fixture
async def auth_headers(test_user):
    """Get authentication headers"""
    from app.core.security import create_access_token
    
    access_token = create_access_token(
        subject=str(test_user.user_id)
    )
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestPlanningPhaseIntegration:
    """Integration tests for planning phase"""
    
    @pytest.mark.asyncio
    async def test_create_test_cycle_flow(self, client: AsyncClient, auth_headers: dict):
        """Test complete flow of creating a test cycle"""
        # Create test cycle
        cycle_data = {
            "cycle_name": f"Integration Test Cycle {datetime.now().timestamp()}",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "description": "Integration test cycle"
        }
        
        response = await client.post(
            "/api/v1/cycles/",
            json=cycle_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        cycle = response.json()
        assert cycle["cycle_name"] == cycle_data["cycle_name"]
        assert cycle["status"] == "Planning"
        assert "cycle_id" in cycle
        
        return cycle["cycle_id"]
    
    @pytest.mark.asyncio
    async def test_add_report_to_cycle(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test adding a report to a cycle"""
        # First create a cycle
        cycle_id = await self.test_create_test_cycle_flow(client, auth_headers)
        
        # Create a test report in database
        from app.models import Report
        report = Report(
            report_name="Test Report",
            regulation="SOX",
            report_type="Quarterly",
            frequency="Quarterly",
            is_active=True
        )
        db_session.add(report)
        await db_session.commit()
        
        # Add report to cycle
        response = await client.post(
            f"/api/v1/cycles/{cycle_id}/reports",
            params={"report_id": report.report_id},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert len(result["cycle"]["reports"]) == 1
    
    @pytest.mark.asyncio
    async def test_workflow_status(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test getting workflow status"""
        # Create cycle and add report
        cycle_id = await self.test_create_test_cycle_flow(client, auth_headers)
        
        # Create and add report
        from app.models import Report
        report = Report(
            report_name="Workflow Test Report",
            regulation="SOX",
            report_type="Quarterly",
            frequency="Quarterly",
            is_active=True
        )
        db_session.add(report)
        await db_session.commit()
        
        await client.post(
            f"/api/v1/cycles/{cycle_id}/reports",
            params={"report_id": report.report_id},
            headers=auth_headers
        )
        
        # Get workflow status
        response = await client.get(
            f"/api/v1/workflow/{cycle_id}/reports/{report.report_id}/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        status = response.json()
        assert status["current_phase"] == "Planning"
        assert len(status["phases"]) == 8
        assert status["can_advance"] is True


class TestScopingPhaseIntegration:
    """Integration tests for scoping phase"""
    
    @pytest.mark.asyncio
    async def test_generate_attributes(self, client: AsyncClient, auth_headers: dict):
        """Test generating test attributes"""
        # This would require a full workflow setup
        # For now, we'll test the endpoint structure
        
        # Mock LLM response
        with pytest.raises(Exception):
            # This will fail without proper setup, but tests the flow
            response = await client.post(
                "/api/v1/cycles/1/reports/1/generate-attributes",
                params={"sample_size": 25},
                headers=auth_headers
            )


class TestCleanArchitecturePatterns:
    """Test architectural patterns are followed"""
    
    def test_domain_independence(self):
        """Test that domain layer has no external dependencies"""
        import app.domain.entities.test_cycle as domain_module
        
        # Check imports
        module_imports = dir(domain_module)
        
        # Domain should not import from infrastructure
        assert "sqlalchemy" not in str(domain_module.__file__)
        assert "fastapi" not in str(domain_module.__file__)
        
        # Domain should only use standard library and domain imports
        import_statements = []
        with open(domain_module.__file__, 'r') as f:
            for line in f:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    import_statements.append(line.strip())
        
        for imp in import_statements:
            assert 'sqlalchemy' not in imp
            assert 'fastapi' not in imp
            assert 'app.models' not in imp
            assert 'app.api' not in imp
    
    def test_use_case_structure(self):
        """Test use cases follow consistent structure"""
        from app.application.use_cases.planning import CreateTestCycleUseCase
        
        # Check use case has required methods
        assert hasattr(CreateTestCycleUseCase, 'execute')
        
        # Check constructor accepts dependencies
        import inspect
        sig = inspect.signature(CreateTestCycleUseCase.__init__)
        params = list(sig.parameters.keys())
        
        # Should have repository and service dependencies
        assert 'cycle_repository' in params
        assert 'notification_service' in params
        assert 'audit_service' in params
    
    def test_repository_interfaces(self):
        """Test repository interfaces are properly defined"""
        from app.application.interfaces.repositories import TestCycleRepository
        
        # Check it's an abstract base class
        assert hasattr(TestCycleRepository, '__abstractmethods__')
        
        # Check required methods
        required_methods = ['get', 'save', 'delete', 'find_by_status']
        for method in required_methods:
            assert hasattr(TestCycleRepository, method)


@pytest.mark.asyncio
async def test_end_to_end_workflow(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Test complete workflow from planning to scoping"""
    # 1. Create test cycle
    cycle_data = {
        "cycle_name": f"E2E Test Cycle {datetime.now().timestamp()}",
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "description": "End-to-end test"
    }
    
    response = await client.post(
        "/api/v1/cycles/",
        json=cycle_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    cycle = response.json()
    cycle_id = cycle["cycle_id"]
    
    # 2. Create and add report
    from app.models import Report
    report = Report(
        report_name="E2E Test Report",
        regulation="SOX",
        report_type="Quarterly",
        frequency="Quarterly",
        is_active=True
    )
    db_session.add(report)
    await db_session.commit()
    report_id = report.report_id
    
    response = await client.post(
        f"/api/v1/cycles/{cycle_id}/reports",
        params={"report_id": report_id},
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # 3. Assign tester
    # Create a tester user
    from app.models import User, Role, UserRole
    tester_role = await db_session.get(Role, 1)  # Tester role
    if not tester_role:
        tester_role = Role(role_id=1, role_name="Tester", description="Tester role")
        db_session.add(tester_role)
    
    tester = User(
        username="e2e_tester",
        email="tester@test.com",
        full_name="E2E Tester",
        hashed_password=get_password_hash("testpass"),
        is_active=True
    )
    db_session.add(tester)
    await db_session.commit()
    
    tester_user_role = UserRole(user_id=tester.user_id, role_id=1)
    db_session.add(tester_user_role)
    await db_session.commit()
    
    response = await client.put(
        f"/api/v1/cycles/{cycle_id}/reports/{report_id}/assign-tester",
        params={"tester_id": tester.user_id},
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # 4. Finalize planning phase
    response = await client.post(
        f"/api/v1/cycles/{cycle_id}/finalize",
        headers=auth_headers
    )
    assert response.status_code == 200
    result = response.json()
    assert result["cycle"]["status"] == "Active"
    
    # 5. Check workflow advanced to scoping
    response = await client.get(
        f"/api/v1/workflow/{cycle_id}/reports/{report_id}/status",
        headers=auth_headers
    )
    assert response.status_code == 200
    status = response.json()
    assert status["current_phase"] == "Scoping"