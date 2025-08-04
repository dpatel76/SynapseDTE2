# Table Refactoring - Model and Query Update Plan

## The Complete Picture

When renaming a table, we need to update:

### 1. **Database Level**
- Table name in database
- Foreign key constraints
- Indexes
- Views/Stored procedures

### 2. **Model Level** 
- `__tablename__` in model class
- ForeignKey references in other models
- Relationship back_populates
- Model class name (sometimes)

### 3. **Query Level**
- ORM queries using the model
- Raw SQL queries
- Query builder patterns
- Service layer queries

### 4. **Import Level**
- Model imports in __init__.py
- Model imports in services
- Model imports in API endpoints

## Example: Renaming `data_owner_assignments`

### Before:
```python
# Model
class DataOwnerAssignment(Base):
    __tablename__ = "data_owner_assignments"
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"))
    
# Service
assignments = db.query(DataOwnerAssignment).filter_by(cycle_id=cycle_id).all()

# Raw SQL
query = "SELECT * FROM data_owner_assignments WHERE status = 'pending'"

# Relationship
class TestCycle(Base):
    data_owner_assignments = relationship("DataOwnerAssignment", back_populates="cycle")
```

### After:
```python
# Model
class DataOwnerAssignment(Base):
    __tablename__ = "cycle_report_data_owner_assignments"
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"))
    
# Service (no change - uses model)
assignments = db.query(DataOwnerAssignment).filter_by(cycle_id=cycle_id).all()

# Raw SQL (updated)
query = "SELECT * FROM cycle_report_data_owner_assignments WHERE status = 'pending'"

# Relationship (no change - uses model class)
class TestCycle(Base):
    data_owner_assignments = relationship("DataOwnerAssignment", back_populates="cycle")
```

## What Our Scripts Handle

### `rename_single_table.py` handles:
1. ✅ Updates `__tablename__` in model
2. ✅ Updates ForeignKey references
3. ✅ Creates database migration
4. ✅ Calls update_models_and_queries.py

### `update_models_and_queries.py` handles:
1. ✅ Updates relationship back_populates
2. ✅ Updates service layer queries
3. ✅ Updates API endpoint queries
4. ✅ Updates raw SQL in .py and .sql files
5. ✅ Updates model imports if name changes

## Special Cases to Handle

### 1. **Model Name Changes**
Some tables might need model class renames:
- `samples` → `cycle_report_test_execution_sample_data`
- Model: `Sample` → `TestExecutionSampleData`?

### 2. **Pluralization in Relationships**
```python
# Need to handle both:
back_populates="data_owner_assignment"  # Singular
back_populates="data_owner_assignments" # Plural
```

### 3. **Complex Queries**
```python
# Subqueries
subquery = db.query(DataOwnerAssignment.id).subquery()

# Joins
query = db.query(User).join(DataOwnerAssignment)

# Raw SQL in strings
sql = f"""
    SELECT u.*, da.*
    FROM users u
    JOIN data_owner_assignments da ON u.id = da.user_id
"""
```

### 4. **Migration Files**
Existing migrations that reference old table names need special handling

## Execution Strategy

### Phase 1: Analysis
```bash
# Find all references
python scripts/analyze_table_dependencies.py
```

### Phase 2: Test on Small Table
```bash
# Pick a low-impact table first
python scripts/rename_single_table.py \
  --old-name "pde_mapping_approval_rules" \
  --new-name "cycle_report_planning_pde_mapping_approval_rules"
```

### Phase 3: Verify
- Check model updated
- Check queries work
- Run tests
- Check API endpoints

### Phase 4: Continue with Other Tables
Follow the phased approach, one workflow phase at a time

## Potential Issues and Solutions

### Issue 1: Circular Dependencies
**Problem**: Tables reference each other
**Solution**: Update both in same transaction

### Issue 2: Runtime Dynamic Queries
**Problem**: Table names built at runtime
```python
table_name = f"{prefix}_assignments"
query = f"SELECT * FROM {table_name}"
```
**Solution**: Need manual review and update

### Issue 3: External References
**Problem**: Other services, scripts, or tools reference tables
**Solution**: Document all external dependencies

### Issue 4: ORM Cache
**Problem**: SQLAlchemy caches metadata
**Solution**: Restart services after changes

## Testing Strategy

### 1. Unit Tests
```python
def test_data_owner_assignment_renamed():
    # Should work with new table name
    assignment = DataOwnerAssignment(...)
    db.session.add(assignment)
    db.session.commit()
```

### 2. Integration Tests
- Test all API endpoints
- Test service methods
- Test raw SQL queries

### 3. Performance Tests
- Ensure no performance degradation
- Check query plans haven't changed

## Rollback Plan

If something goes wrong:

1. **Database**: Run rollback migration
2. **Code**: Git revert the commit
3. **Cache**: Clear ORM cache
4. **Services**: Restart all services

## Summary

The scripts now handle the complete refactoring:
- Database schema changes
- Model updates
- Query updates (ORM and raw SQL)
- Import updates
- Migration generation

This comprehensive approach ensures nothing is missed during the table renaming process.