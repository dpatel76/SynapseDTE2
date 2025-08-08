# Scoping Versioning and Approval Workflow Analysis

## Executive Summary

The scoping versioning system implements a sophisticated multi-version workflow with report owner approval, feedback integration, and resubmission capabilities. This document extracts key architectural patterns, implementation details, and lessons learned that can be applied to sample selection and data profiling phases.

## Key Architectural Patterns

### 1. Version Management Pattern

**Core Structure:**
- Each phase has multiple versions (draft → pending_approval → approved/rejected → superseded)
- Version numbers are sequential integers starting from 1
- Only one approved version can be active at a time (previous approved versions become superseded)
- UUID-based version_id for unique identification

**Key Implementation:**
```python
class ScopingVersion(CustomPKModel, AuditMixin):
    version_id = Column(UUID, primary_key=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'))
    version_number = Column(Integer, nullable=False)
    version_status = Column(version_status_enum, nullable=False)
    parent_version_id = Column(UUID, ForeignKey('cycle_report_scoping_versions.version_id'))
```

### 2. Attribute-Level Decision Tracking

**Dual-Layer Decision Model:**
- **Tester Decision**: Initial scoping decision (accept/decline/override)
- **Report Owner Decision**: Approval layer (approved/rejected/needs_revision)
- Each attribute maintains its own decision history and status

**Key Fields:**
```python
# Tester fields
tester_decision = Column(tester_decision_enum)
final_scoping = Column(Boolean)
tester_rationale = Column(Text)

# Report Owner fields  
report_owner_decision = Column(report_owner_decision_enum)
report_owner_notes = Column(Text)
report_owner_decided_at = Column(DateTime)
```

### 3. Feedback Integration Pattern

**The "Make Changes" Button Flow:**
1. Report Owner provides feedback (approve/reject individual attributes)
2. Tester sees feedback in a dedicated tab
3. "Make Changes" button creates a new draft version
4. New version copies all attributes WITH existing feedback visible
5. Tester can update decisions while seeing report owner feedback
6. Feedback is preserved until new submission (then reset for fresh review)

**Critical Implementation Detail:**
```python
async def create_version_from_feedback(self, phase_id, parent_version_id, user_id):
    # Copy attributes with BOTH tester decisions AND report owner feedback
    # This allows tester to see feedback while making changes
    new_attribute = ScopingAttribute(
        # Copy tester decisions
        tester_decision=attr.tester_decision,
        final_scoping=attr.final_scoping,
        
        # KEEP report owner decisions visible during editing
        report_owner_decision=attr.report_owner_decision,
        report_owner_notes=attr.report_owner_notes,
        
        # Reset status to pending
        status=AttributeStatus.PENDING
    )
```

### 4. Submission and Approval Workflow

**Submission Process:**
1. Version must be in DRAFT status
2. All attributes must have tester decisions
3. Primary Key attributes auto-approved if missing decisions
4. Report Owner decisions RESET on submission (fresh review)
5. Universal Assignment created for Report Owner

**Approval Process:**
1. Version must be in PENDING_APPROVAL status
2. Previous approved version automatically superseded
3. Universal Assignment completed on approval
4. Version becomes the "current" version

### 5. Universal Assignment Integration

**Pattern for Creating Assignments:**
```python
assignment = UniversalAssignment(
    assignment_type="Scoping Approval",
    from_role=from_user.role,  # Tester
    to_role="Report Owner",
    to_user_id=report.report_owner_id,
    title="Review Scoping Decisions",
    context_type="Report",
    context_data={
        "cycle_id": phase.cycle_id,
        "report_id": phase.report_id,
        "phase_name": "Scoping",
        "version_id": str(version_id),
        "submission_notes": submission_notes
    },
    priority="High",
    due_date=utc_now() + timedelta(days=2)
)
```

## Frontend Patterns

### 1. Report Owner Feedback Component

**Key Features:**
- Loads feedback from most recent version with RO decisions
- Filters to only show attributes that were scoped in
- Shows summary statistics (approved/rejected/changes requested)
- Conditional "Make Changes" button for Testers when feedback exists

**Implementation Pattern:**
```typescript
// Check versions from newest to oldest for feedback
for (const version of versions) {
    const attributes = await loadVersionAttributes(version.version_id);
    const withFeedback = attributes.filter(attr => 
        attr.report_owner_decision !== null && 
        attr.final_scoping === true  // Only scoped-in attributes
    );
    if (withFeedback.length > 0) {
        // Found feedback version
        break;
    }
}
```

### 2. Attribute Name Resolution

**Critical Fix Applied:**
- Backend joins with planning attributes to get `attribute_name`
- Frontend maps planning_attribute_id to display proper names
- Fallback to "Unknown Attribute" if name missing

### 3. Decision Reset Pattern

**Report Owner Decisions Reset on Submission:**
```python
# Reset report owner decisions for fresh review
for attr in version.attributes:
    if attr.report_owner_decision is not None:
        attr.report_owner_decision = None
        attr.report_owner_notes = None
        attr.report_owner_decided_at = None
```

## Key Implementation Fixes

### 1. Enum Type Handling
- Cast enums to strings for database queries to avoid comparison issues
- Use `.value` property when serializing enum fields
- Handle both string and enum types in API responses

### 2. Phase ID Architecture
- Always query for phase_id instead of constructing it
- Use phase_id as the primary context identifier
- Maintain phase_id consistency across all operations

### 3. Version Status Workflow
- Strict status transitions enforced
- Version editability checked before operations
- Proper status updates on all state changes

### 4. Attribute Status Management
- Separate attribute status from version status
- Update attribute status based on both decisions
- Maintain status consistency across operations

## Data Flow Patterns

### 1. Version Creation Flow
```
User Action → Create Version → Initialize with Draft Status → Copy Attributes (optional) → Ready for Editing
```

### 2. Decision Making Flow
```
Tester Decision → Update Attribute → Update Version Stats → Enable Submission → Submit to Report Owner
```

### 3. Feedback Integration Flow
```
Report Owner Decision → Store at Attribute Level → Display in Feedback Tab → Enable "Make Changes" → Create New Version with Feedback Visible
```

### 4. Approval Flow
```
Report Owner Approves → Version Status = Approved → Previous Version = Superseded → Complete Universal Assignment
```

## Best Practices Identified

### 1. Version Management
- Always create new versions for changes (immutability)
- Maintain parent-child relationships between versions
- Track version statistics in real-time
- Implement proper version comparison capabilities

### 2. User Experience
- Show feedback prominently when it exists
- Provide clear action buttons ("Make Changes")
- Display version numbers and history
- Show attribute-level approval status inline

### 3. Data Integrity
- Validate all state transitions
- Maintain audit trails at both version and attribute levels
- Use transactions for multi-step operations
- Implement proper error recovery

### 4. API Design
- Separate endpoints for different operations (create, submit, approve, reject)
- Return comprehensive status information
- Support both phase-based and version-based queries
- Implement proper pagination for large datasets

## Lessons for Other Phases

### 1. Sample Selection Implementation
- Use same version management pattern
- Implement sample-level decisions (include/exclude)
- Add justification fields for decisions
- Create feedback mechanism for Report Owner

### 2. Data Profiling Implementation
- Version rules and execution results separately
- Track rule-level approval status
- Implement feedback at rule level
- Support re-execution with new parameters

### 3. Common Patterns to Reuse
- Version status enum and transitions
- Attribute/item level decision tracking
- Report Owner feedback integration
- Universal Assignment creation
- "Make Changes" button pattern

## Technical Debt Identified

### 1. Enum Handling
- Need consistent enum serialization strategy
- Database enum types vs application enums
- Migration strategy for enum changes

### 2. Performance Considerations
- Version statistics calculation can be expensive
- Need caching for frequently accessed versions
- Optimize attribute loading with proper joins

### 3. Error Handling
- Some 500 errors return success (backend saves but response fails)
- Need better error recovery mechanisms
- Improve error message clarity

## Conclusion

The scoping versioning system provides a robust framework for multi-version workflows with approval mechanisms. The key innovation is the feedback integration pattern that allows iterative refinement while maintaining visibility of previous decisions. This pattern should be replicated across other phases for consistency and user experience.

### Critical Success Factors:
1. **Feedback Visibility**: Always show report owner feedback during revisions
2. **Version Immutability**: Create new versions for changes, don't modify approved versions
3. **Decision Tracking**: Maintain separate decision fields for each role
4. **Status Management**: Clear status transitions with validation
5. **User Experience**: Prominent action buttons and clear workflow indicators