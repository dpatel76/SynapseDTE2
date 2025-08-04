# Sample Selection Duplication Analysis

## Current Architecture Issue

### The Problem
When creating new versions of sample selection, the system currently creates completely new samples for each version, leading to:
1. **Database bloat**: Each version stores its own copy of samples
2. **Performance impact**: Duplicate data increases query times
3. **Inconsistency risks**: Same logical sample might have different IDs across versions
4. **Resource waste**: Storage and processing overhead

### Current Behavior

#### Version Creation Flow
1. Version 1 created → Generates 100 new samples
2. Version 2 created → Generates another 100 new samples (duplicates)
3. Version 3 created → Generates another 100 new samples (more duplicates)

Result: 300 sample records for what might be the same 100 logical samples

#### Sample Structure
```sql
-- Current: Each version has its own samples
sample_selection_samples
- sample_id (UUID) - unique per version
- version_id (UUID) - ties to specific version
- sample_data (JSONB) - actual sample content
- ... other fields
```

## Root Cause Analysis

### 1. Version-Centric Design
- Samples are tightly coupled to versions
- No concept of "logical sample" that exists across versions
- Each version treats samples as completely new entities

### 2. Lack of Sample Identity
- No unique identifier for the logical sample (e.g., account number, customer ID)
- `sample_identifier` field exists but not used for deduplication
- No tracking of sample lineage across versions

### 3. Carry Forward Limitation
- `carry_forward_samples` method creates new copies instead of references
- Even carried samples get new UUIDs
- No link to original sample beyond metadata

## Proposed Solution

### Architecture Refactoring Approach

#### Option 1: Shared Sample Pool with Version Associations
```sql
-- Logical samples table (shared pool)
sample_selection_logical_samples
- logical_sample_id (UUID) - permanent ID
- sample_identifier (string) - business key
- sample_data (JSONB) - core data
- created_at
- source_info

-- Version-sample associations
sample_selection_version_samples
- version_id (UUID)
- logical_sample_id (UUID)
- sample_status (included/excluded)
- decision_data
- metadata
```

#### Option 2: Sample Inheritance Model
```sql
-- Base samples (first occurrence)
sample_selection_base_samples
- base_sample_id (UUID)
- sample_identifier (unique)
- immutable_data

-- Version-specific overrides
sample_selection_version_overrides
- version_id
- base_sample_id
- override_data
- decisions
```

#### Option 3: Event Sourcing Pattern
- Store sample creation as events
- Reconstruct version state from events
- Avoid storing duplicate data

### Recommended Solution: Option 1 (Shared Sample Pool)

#### Benefits
1. **Efficiency**: Store each unique sample once
2. **Consistency**: Same sample has same ID across versions
3. **Flexibility**: Easy to track sample history
4. **Performance**: Reduced data volume
5. **Backward Compatible**: Can migrate existing data

#### Implementation Plan

##### Phase 1: Database Schema Changes
```sql
-- 1. Create logical samples table
CREATE TABLE sample_selection_logical_samples (
    logical_sample_id UUID PRIMARY KEY,
    sample_identifier VARCHAR(255) UNIQUE NOT NULL,
    lob_id INTEGER REFERENCES lobs(lob_id),
    sample_data JSONB NOT NULL,
    sample_category VARCHAR(50),
    risk_score NUMERIC(5,2),
    confidence_score NUMERIC(5,2),
    generation_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER,
    source_version_id UUID -- first version that created it
);

-- 2. Create version-sample association table
CREATE TABLE sample_selection_version_samples (
    version_id UUID REFERENCES sample_selection_versions(version_id),
    logical_sample_id UUID REFERENCES sample_selection_logical_samples(logical_sample_id),
    included BOOLEAN DEFAULT true,
    tester_decision VARCHAR(50),
    tester_decision_notes TEXT,
    tester_decision_at TIMESTAMP,
    report_owner_decision VARCHAR(50),
    report_owner_decision_notes TEXT,
    report_owner_decision_at TIMESTAMP,
    validation_results JSONB,
    PRIMARY KEY (version_id, logical_sample_id)
);

-- 3. Create indexes
CREATE INDEX idx_logical_samples_identifier ON sample_selection_logical_samples(sample_identifier);
CREATE INDEX idx_version_samples_version ON sample_selection_version_samples(version_id);
```

##### Phase 2: Service Layer Changes

```python
class SampleSelectionService:
    async def generate_intelligent_samples_v2(
        self,
        db: AsyncSession,
        version_id: uuid.UUID,
        target_distribution: Dict[str, int]
    ) -> List[LogicalSample]:
        """Generate samples using shared pool approach"""
        
        # 1. Determine needed samples
        needed_samples = await self._identify_needed_samples(
            db, version_id, target_distribution
        )
        
        # 2. Check existing logical samples
        existing_samples = await self._find_existing_logical_samples(
            db, [s.identifier for s in needed_samples]
        )
        
        # 3. Create only new logical samples
        new_samples = []
        for needed in needed_samples:
            if needed.identifier not in existing_samples:
                logical_sample = LogicalSample(
                    logical_sample_id=uuid.uuid4(),
                    sample_identifier=needed.identifier,
                    sample_data=needed.data,
                    # ... other fields
                )
                new_samples.append(logical_sample)
        
        if new_samples:
            db.add_all(new_samples)
        
        # 4. Create version associations for all samples
        associations = []
        all_samples = existing_samples + new_samples
        for sample in all_samples:
            assoc = VersionSampleAssociation(
                version_id=version_id,
                logical_sample_id=sample.logical_sample_id,
                included=True
            )
            associations.append(assoc)
        
        db.add_all(associations)
        await db.commit()
        
        return all_samples
```

##### Phase 3: Migration Strategy

1. **Create new tables** without dropping old ones
2. **Migrate existing data**:
   ```python
   async def migrate_existing_samples():
       # Group samples by identifier
       # Create logical samples for unique identifiers
       # Create associations for all versions
   ```
3. **Update services** to use new tables
4. **Run in parallel** for a period
5. **Validate data** consistency
6. **Switch over** completely
7. **Archive old tables**

### Expected Improvements

#### Before Refactoring
- 3 versions × 100 samples = 300 records
- Storage: ~300KB (assuming 1KB per sample)
- Query complexity: O(n × versions)

#### After Refactoring
- 100 logical samples + 300 associations
- Storage: ~100KB samples + ~30KB associations = ~130KB (56% reduction)
- Query complexity: O(n) for samples + O(versions) for associations
- Deduplication ratio: Up to 67% for 3 versions

### Risk Mitigation

1. **Data Integrity**: 
   - Maintain referential integrity with foreign keys
   - Add unique constraints on business keys
   
2. **Performance**:
   - Add appropriate indexes
   - Monitor query performance during migration
   
3. **Backward Compatibility**:
   - Keep old tables during transition
   - Provide compatibility layer in services
   
4. **Rollback Plan**:
   - Keep backups of original data
   - Design migration to be reversible

## Conclusion

The shared sample pool approach (Option 1) provides the best balance of:
- **Efficiency**: Significant reduction in data duplication
- **Maintainability**: Clear separation of concerns
- **Flexibility**: Easy to extend and modify
- **Performance**: Better query performance with proper indexing
- **Migration Safety**: Can be implemented gradually without breaking changes

This refactoring will establish a more scalable foundation for the sample selection system while maintaining all current functionality.