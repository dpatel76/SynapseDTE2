# SynapseDTE Clean Architecture Guide

## Overview

This guide provides comprehensive documentation for the clean architecture implementation of SynapseDTE. The clean architecture separates concerns into distinct layers, making the system more maintainable, testable, and flexible.

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│              (FastAPI Routes & DTOs)                │
├─────────────────────────────────────────────────────┤
│                 Application Layer                    │
│            (Use Cases & Interfaces)                 │
├─────────────────────────────────────────────────────┤
│                   Domain Layer                       │
│          (Entities & Business Rules)                │
├─────────────────────────────────────────────────────┤
│               Infrastructure Layer                   │
│        (Database, External Services)                │
└─────────────────────────────────────────────────────┘
```

## Layer Descriptions

### 1. Domain Layer (`app/domain/`)
The heart of the application containing business logic and rules.

- **Entities**: Core business objects with behavior
  - `TestCycle`: Manages test cycle lifecycle
  - Rich domain models with business rules enforcement

- **Value Objects**: Immutable objects representing concepts
  - `CycleStatus`: Enumeration with transition rules
  - `ReportAssignment`: Immutable report-to-cycle assignment
  - `RiskScore`: Validated risk score (1-10)

- **Domain Events**: Things that happened in the domain
  - `TestCycleCreated`, `ReportAddedToCycle`, etc.

### 2. Application Layer (`app/application/`)
Orchestrates the flow of data and coordinates domain objects.

- **Use Cases**: Application-specific business rules
  - 31 use cases covering all 8 workflow phases
  - Each use case has single responsibility
  - Returns `UseCaseResult` with success/failure

- **DTOs**: Data Transfer Objects for communication
  - Input/Output contracts for use cases
  - Type-safe data validation

- **Interfaces**: Ports for external dependencies
  - Repository interfaces (data access)
  - Service interfaces (external services)

### 3. Infrastructure Layer (`app/infrastructure/`)
Implements interfaces defined by the application layer.

- **Repositories**: Data access implementations
  - `SQLAlchemyTestCycleRepository`
  - `SQLAlchemyReportRepository`
  - `SQLAlchemyUserRepository`
  - `SQLAlchemyWorkflowRepository`

- **Services**: External service adapters
  - `NotificationServiceImpl`: Database notifications
  - `EmailServiceImpl`: SMTP email sending
  - `LLMServiceImpl`: AI/LLM integration
  - `AuditServiceImpl`: Audit logging
  - `SLAServiceImpl`: SLA tracking
  - `DocumentStorageServiceImpl`: File storage

- **Container**: Dependency injection
  - Wires all components together
  - Provides clean dependency management

### 4. Presentation Layer (`app/api/`)
Handles HTTP requests and responses.

- **Endpoints**: FastAPI routes
  - Thin controllers that delegate to use cases
  - Handle HTTP concerns only
  - Convert between HTTP and DTOs

## Key Design Patterns

### 1. Dependency Inversion
- High-level modules don't depend on low-level modules
- Both depend on abstractions (interfaces)
- Example: Use cases depend on repository interfaces, not implementations

### 2. Single Responsibility
- Each class has one reason to change
- Use cases handle one business operation
- Services handle one external integration

### 3. Open/Closed Principle
- Open for extension, closed for modification
- New features added by creating new use cases
- Existing code rarely modified

## Usage Examples

### Creating a Test Cycle

```python
# In endpoint
@router.post("/cycles")
async def create_cycle(
    cycle_in: TestingCycleCreate,
    db: AsyncSession = Depends(get_db),
    container = Depends(get_container),
    current_user = Depends(get_current_user)
):
    # Create DTO
    dto = CreateTestCycleDTO(
        cycle_name=cycle_in.cycle_name,
        start_date=cycle_in.start_date,
        end_date=cycle_in.end_date,
        created_by=current_user.user_id
    )
    
    # Get use case
    use_case = container.get_create_test_cycle_use_case(db)
    
    # Execute
    result = await use_case.execute(dto)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data
```

### Testing Use Cases

```python
# Test without database or external services
async def test_create_cycle():
    # Mock dependencies
    mock_repo = Mock()
    mock_repo.get_by_name = AsyncMock(return_value=None)
    mock_repo.save = AsyncMock(return_value=test_cycle)
    
    # Create use case
    use_case = CreateTestCycleUseCase(
        cycle_repository=mock_repo,
        user_repository=mock_user_repo,
        notification_service=mock_notif,
        audit_service=mock_audit
    )
    
    # Execute
    result = await use_case.execute(dto)
    
    # Assert
    assert result.success
    assert result.data.cycle_name == "Test Cycle"
```

## Workflow Implementation

Each workflow phase has dedicated use cases:

1. **Planning Phase**
   - `CreateTestCycleUseCase`
   - `AddReportToCycleUseCase`
   - `AssignTesterUseCase`
   - `FinalizeTestCycleUseCase`

2. **Scoping Phase**
   - `GenerateTestAttributesUseCase`
   - `ReviewAttributesUseCase`
   - `ApproveAttributesUseCase`

3. **Sample Selection**
   - `GenerateSampleSelectionUseCase`
   - `ApproveSampleSelectionUseCase`
   - `UploadSampleDataUseCase`

4. **Data Owner Identification**
   - `IdentifyDataOwnersUseCase`
   - `AssignDataOwnerUseCase`
   - `CompleteDataOwnerIdentificationUseCase`

5. **Request for Information**
   - `CreateRFIUseCase`
   - `SubmitRFIResponseUseCase`
   - `CompleteRFIPhaseUseCase`

6. **Testing Execution**
   - `ExecuteTestUseCase`
   - `GetTestingProgressUseCase`
   - `CompleteTestingPhaseUseCase`

7. **Observation Management**
   - `CreateObservationUseCase`
   - `UpdateObservationUseCase`
   - `CompleteObservationPhaseUseCase`
   - `GroupObservationsUseCase`

8. **Testing Report**
   - `GenerateTestingReportUseCase`
   - `ReviewTestingReportUseCase`
   - `FinalizeTestingReportUseCase`

## Benefits

1. **Testability**: Business logic can be tested without infrastructure
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Easy to change implementations
4. **Scalability**: Add features without modifying existing code
5. **Documentation**: Code structure documents the business domain

## Migration Strategy

1. **Gradual Migration**
   - Run both architectures side-by-side
   - Migrate one endpoint at a time
   - Feature flag to switch between implementations

2. **Testing**
   - Unit test use cases
   - Integration test repositories
   - E2E test complete workflows

3. **Deployment**
   - Use `docker-compose.clean.yml` for clean architecture
   - Environment variable `ENABLE_CLEAN_ARCHITECTURE=true`
   - Monitor performance and errors

## Running Clean Architecture

```bash
# Start services
./scripts/start_clean_architecture.sh

# Run tests
pytest tests/test_clean_architecture/

# Access services
- API: http://localhost:8001
- Frontend: http://localhost:3001
- Docs: http://localhost:8001/docs
```

## Best Practices

1. **Keep Domain Pure**
   - No framework dependencies
   - No database concerns
   - Only business logic

2. **Use Cases Are Orchestrators**
   - Coordinate domain objects
   - Handle transactions
   - Return results, not throw exceptions

3. **DTOs for Boundaries**
   - Use DTOs at layer boundaries
   - Don't expose domain objects to presentation
   - Validate input at boundaries

4. **Dependency Injection**
   - Use constructor injection
   - Depend on interfaces, not implementations
   - Use container for wiring

5. **Event-Driven Updates**
   - Domain events for side effects
   - Eventual consistency where appropriate
   - Audit trail through events

## Troubleshooting

### Common Issues

1. **Circular Dependencies**
   - Solution: Ensure dependencies flow inward
   - Domain → Nothing
   - Application → Domain
   - Infrastructure → Application & Domain
   - Presentation → Application

2. **Transaction Boundaries**
   - Solution: Manage transactions in use cases
   - One transaction per use case
   - Repository methods are atomic

3. **Testing Complexity**
   - Solution: Test at appropriate level
   - Unit test domain logic
   - Integration test repositories
   - E2E test critical paths

## Future Enhancements

1. **Event Sourcing**
   - Store domain events
   - Rebuild state from events
   - Complete audit trail

2. **CQRS**
   - Separate read/write models
   - Optimize for different use cases
   - Scale reads independently

3. **Microservices**
   - Extract bounded contexts
   - Service per workflow phase
   - Event-driven communication

## Conclusion

The clean architecture implementation provides a solid foundation for maintaining and scaling SynapseDTE. By separating concerns and following SOLID principles, the system is more maintainable, testable, and adaptable to changing requirements.