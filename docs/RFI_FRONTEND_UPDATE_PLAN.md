# RFI Frontend Update Plan

## Overview
This document outlines the plan to update the RFI (Request for Information) frontend to use the version metadata system, following the same pattern as Sample Selection and Scoping phases.

## Current State
- RFI frontend uses `phase_data` JSON storage through `WorkflowPhase` model
- No version management implemented
- Editability is not controlled by version status
- No report owner feedback display based on version metadata

## Target State
- RFI frontend will use the new `cycle_report_rfi_versions` and `cycle_report_rfi_evidence_versioned` tables
- Version status will determine editability (only draft versions are editable)
- Report owner feedback will be displayed based on version metadata
- Implement "Make Changes" workflow for creating new draft versions from feedback

## Implementation Steps

### 1. Update RFI API Client
Create `/frontend/src/api/rfiVersions.ts`:
- `getVersions(cycleId, reportId)` - Get all versions
- `getVersion(versionId)` - Get specific version with evidence
- `createVersion(cycleId, reportId, data)` - Create new version
- `getVersionEvidence(versionId, filters)` - Get evidence with filters
- `submitEvidence(testCaseId, data)` - Submit evidence
- `updateTesterDecision(evidenceId, decision)` - Update tester decision
- `bulkTesterDecision(versionId, evidenceIds, decision)` - Bulk decisions
- `sendToReportOwner(versionId)` - Send for report owner review
- `resubmitAfterFeedback(versionId)` - Create new version after feedback

### 2. Update NewRequestInfoPage Component

#### Add Version State Management
```typescript
const [versions, setVersions] = useState<RFIVersion[]>([]);
const [selectedVersionId, setSelectedVersionId] = useState<string>('');
const [currentVersion, setCurrentVersion] = useState<RFIVersion | null>(null);
```

#### Add Version Selection UI
- Add version dropdown similar to Sample Selection
- Display version status badge
- Show read-only alert for non-draft versions

#### Update Evidence Display
- Show tester decisions
- Show report owner decisions and feedback
- Display final status based on both decisions

### 3. Create RFI Evidence Components

#### `/frontend/src/components/request-info/RFIEvidenceTable.tsx`
- Display evidence with version awareness
- Show decisions from both tester and report owner
- Implement bulk selection and actions
- Disable actions for non-draft versions

#### `/frontend/src/components/request-info/RFIVersionSelector.tsx`
- Version dropdown component
- Show version status and statistics
- Enable/disable based on user role

#### `/frontend/src/components/request-info/RFIReportOwnerFeedback.tsx`
- Display report owner feedback
- Show decision statistics
- "Make Changes" button for creating new version

### 4. Update Existing Components

#### Update `DataSourceQueryPanel.tsx`
- Check version editability before allowing queries
- Show version status in UI

#### Update `EvidenceSubmissionPanel.tsx`
- Check version editability before allowing uploads
- Show version status in UI

#### Update `TesterEvidenceReview.tsx`
- Use version-based evidence data
- Show both tester and report owner decisions
- Implement version-aware decision updates

### 5. Implement Version Workflows

#### Start Phase with Version
When starting RFI phase:
1. Create initial draft version
2. Set submission deadline and instructions
3. Initialize evidence tracking

#### Submit for Approval
When all evidence collected:
1. Update version status to pending_approval
2. Create assignment for approver

#### Report Owner Review
1. Send evidence to report owner
2. Track review status in version metadata
3. Display feedback when complete

#### Make Changes Flow
After report owner feedback:
1. Create new draft version
2. Carry forward approved evidence
3. Reset rejected evidence for resubmission

### 6. Update Type Definitions

Create `/frontend/src/types/rfiVersions.ts`:
```typescript
interface RFIVersion {
  version_id: string;
  phase_id: number;
  version_number: number;
  version_status: VersionStatus;
  parent_version_id?: string;
  
  // Statistics
  total_test_cases: number;
  submitted_count: number;
  approved_count: number;
  rejected_count: number;
  pending_count: number;
  
  // Metadata
  can_be_edited: boolean;
  has_report_owner_feedback: boolean;
  report_owner_feedback_summary?: any;
  
  // Audit
  created_at: string;
  submitted_at?: string;
  approved_at?: string;
}

interface RFIEvidence {
  evidence_id: string;
  version_id: string;
  test_case_id: number;
  evidence_type: 'document' | 'data_source';
  evidence_status: EvidenceStatus;
  
  // Decisions
  tester_decision?: Decision;
  tester_notes?: string;
  report_owner_decision?: Decision;
  report_owner_notes?: string;
  
  // Computed
  is_approved: boolean;
  is_rejected: boolean;
  needs_resubmission: boolean;
  final_status: string;
}
```

## Migration Strategy

1. **Phase 1**: Implement version API client and types
2. **Phase 2**: Add version selection UI without changing functionality
3. **Phase 3**: Update evidence display to show version data
4. **Phase 4**: Implement editability based on version status
5. **Phase 5**: Add report owner feedback display
6. **Phase 6**: Implement Make Changes workflow
7. **Phase 7**: Remove old phase_data dependencies

## Testing Plan

1. **Version Creation**: Test creating initial and subsequent versions
2. **Evidence Submission**: Test submitting both document and query evidence
3. **Decision Flow**: Test tester and report owner decision workflows
4. **Make Changes**: Test creating new version after feedback
5. **Read-only Mode**: Test that non-draft versions are read-only
6. **Role Permissions**: Test that report owners see read-only view

## Success Criteria

- [ ] RFI uses version tables instead of phase_data
- [ ] Only draft versions can be edited
- [ ] Report owner feedback is displayed from version metadata
- [ ] Make Changes creates new draft version with carried forward evidence
- [ ] All existing RFI functionality continues to work
- [ ] Performance is maintained or improved