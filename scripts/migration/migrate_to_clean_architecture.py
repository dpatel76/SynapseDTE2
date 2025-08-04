"""Migration script to transition endpoints to clean architecture"""
import os
import shutil
from pathlib import Path
from datetime import datetime


def create_backup(source_dir: Path, backup_dir: Path):
    """Create backup of existing endpoints"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"backup_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=True)
    
    for file in source_dir.glob("*.py"):
        if not file.name.endswith("_clean.py"):
            shutil.copy2(file, backup_path / file.name)
    
    print(f"✓ Created backup at: {backup_path}")
    return backup_path


def update_imports_in_file(file_path: Path):
    """Update imports in a file to use clean architecture"""
    content = file_path.read_text()
    
    # Update imports
    replacements = [
        # Replace direct model imports with DTOs
        ("from app.models import", "from app.application.dto import"),
        # Replace service imports with use case imports
        ("from app.services.", "from app.application.use_cases."),
        # Replace CRUD imports with repository imports
        ("from app.crud.", "from app.infrastructure.repositories."),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    file_path.write_text(content)


def migrate_endpoint(endpoint_path: Path, container_import: str):
    """Migrate an endpoint to use clean architecture"""
    content = endpoint_path.read_text()
    
    # Add container import
    if "from app.infrastructure.container import" not in content:
        import_line = "from app.infrastructure.container import get_container, get_db\n"
        # Find the last import line
        lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                last_import_idx = i
        
        lines.insert(last_import_idx + 1, import_line)
        content = '\n'.join(lines)
    
    # Add container dependency to endpoints
    content = content.replace(
        "db: AsyncSession = Depends(deps.get_current_db)",
        "db: AsyncSession = Depends(get_db),\n    container=Depends(get_container)"
    )
    
    endpoint_path.write_text(content)
    print(f"✓ Migrated: {endpoint_path.name}")


def create_migration_guide():
    """Create a guide for manual migration steps"""
    guide = """
# Clean Architecture Migration Guide

## Automated Changes Made:
1. Created backups of all existing endpoints
2. Updated imports to use clean architecture components
3. Added dependency injection container to endpoints

## Manual Steps Required:

### 1. Update Endpoint Logic
Replace direct service/CRUD calls with use case executions:

**Before:**
```python
cycle = await crud.testing_cycle.create(db, obj_in=cycle_in)
```

**After:**
```python
dto = CreateTestCycleDTO(
    cycle_name=cycle_in.cycle_name,
    start_date=cycle_in.start_date,
    end_date=cycle_in.end_date,
    created_by=current_user.user_id
)
use_case = container.get_create_test_cycle_use_case(db)
result = await use_case.execute(dto)

if not result.success:
    raise HTTPException(status_code=400, detail=result.error)

cycle = result.data
```

### 2. Update Response Models
Convert domain entities/DTOs to response schemas:

**Before:**
```python
return cycle
```

**After:**
```python
return TestingCycleResponse(
    cycle_id=cycle.cycle_id,
    cycle_name=cycle.cycle_name,
    status=cycle.status
)
```

### 3. Error Handling
Use consistent error handling with use case results:

```python
if not result.success:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.error
    )
```

### 4. Testing
1. Run unit tests for use cases
2. Run integration tests for endpoints
3. Test with frontend to ensure compatibility

### 5. Gradual Migration
1. Start with one endpoint at a time
2. Test thoroughly before moving to the next
3. Keep old endpoints as fallback until fully migrated
4. Remove old code only after confirming everything works

## Benefits After Migration:
- Testable business logic
- Clear separation of concerns
- Easy to swap implementations
- Better error handling
- Consistent API responses
"""
    
    with open("MIGRATION_GUIDE.md", "w") as f:
        f.write(guide)
    
    print("✓ Created migration guide: MIGRATION_GUIDE.md")


def main():
    """Main migration script"""
    print("Starting Clean Architecture Migration...")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    endpoints_dir = project_root / "app" / "api" / "v1" / "endpoints"
    backup_dir = project_root / "backups"
    
    # Create backup
    backup_path = create_backup(endpoints_dir, backup_dir)
    
    # List endpoints to migrate
    endpoints_to_migrate = [
        "planning.py",
        "scoping.py",
        "sample_selection.py",
        "data_owner.py",
        "request_for_information.py",
        "testing_execution.py",
        "observation_management.py",
        "benchmarking.py"
    ]
    
    # Migrate each endpoint
    for endpoint_name in endpoints_to_migrate:
        endpoint_path = endpoints_dir / endpoint_name
        if endpoint_path.exists():
            # Create clean version
            clean_path = endpoints_dir / endpoint_name.replace(".py", "_clean.py")
            if not clean_path.exists():
                shutil.copy2(endpoint_path, clean_path)
                migrate_endpoint(clean_path, "app.infrastructure.container")
    
    # Create migration guide
    create_migration_guide()
    
    print("\n✅ Migration preparation complete!")
    print(f"📁 Backups saved to: {backup_path}")
    print("📄 Review MIGRATION_GUIDE.md for manual steps")
    print("\n⚠️  Remember to:")
    print("  1. Update each endpoint to use use cases")
    print("  2. Test thoroughly before removing old code")
    print("  3. Update frontend API calls if needed")


if __name__ == "__main__":
    main()