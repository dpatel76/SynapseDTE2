# Versioning UI Integration Guide

This guide explains how to add versioning functionality to phase pages in the SynapseDTE application.

## Quick Start

To add versioning to any phase page, use the `PhaseVersioningSection` component:

```tsx
import { PhaseVersioningSection } from '../../components/common/PhaseVersioningSection';

// In your phase component:
<PhaseVersioningSection
  cycleId={cycleId.toString()}
  reportId={reportId.toString()}
  phaseName="Your Phase Name"
  entityType="YourEntityType"
  entityId={entityId}
  currentVersion={currentVersion}
  onVersionChange={handleVersionChange}
  showActivities={true}
  showApprovalButtons={true}
  readOnly={false}
/>
```

## Available Components

### 1. VersionSelector
A dropdown selector for choosing versions with creation capabilities.

```tsx
<VersionSelector
  entityType="ReportAttribute"
  entityId={attributeId}
  currentVersion={1}
  onVersionChange={(version) => console.log('Selected version:', version)}
  onViewHistory={() => setShowHistory(true)}
  showCreateButton={true}
  showApprovalStatus={true}
  approvedOnly={false}
/>
```

### 2. VersionApprovalButtons
Buttons for approving/rejecting versions (for authorized users).

```tsx
<VersionApprovalButtons
  entityType="SampleSet"
  versionId={versionId}
  versionNumber={2}
  versionStatus="pending_approval"
  onStatusChange={() => refreshData()}
/>
```

### 3. VersionHistoryViewer
A dialog component for viewing complete version history.

```tsx
<VersionHistoryViewer
  entityType="TestExecution"
  entityId={testId}
  open={showHistory}
  onClose={() => setShowHistory(false)}
  onVersionSelect={(version) => loadVersion(version.version_number)}
/>
```

### 4. ActivityStateManager
Manages activity states within a phase with manual controls.

```tsx
<ActivityStateManager
  cycleId={cycleId}
  reportId={reportId}
  phaseName="Planning"
  showControls={true}
  onPhaseComplete={() => navigateToNextPhase()}
/>
```

### 5. PhaseStatusIndicator
A simple status badge for showing phase state.

```tsx
<PhaseStatusIndicator
  cycleId={cycleId}
  reportId={reportId}
  phaseName="Scoping"
  showDetails={true}
/>
```

## Entity Types

The following entity types are supported for versioning:

- `ReportAttribute` - Planning phase attributes
- `SampleSet` - Sample selection phase
- `DataProfilingRule` - Data profiling rules
- `TestExecution` - Test execution results
- `Observation` - Observation management
- `ScopingDecision` - Scoping phase decisions

## Integration Steps

### 1. Import Required Components

```tsx
import { 
  VersionSelector,
  VersionHistoryViewer,
  ActivityStateManager,
  PhaseVersioningSection 
} from '../../components/common';
```

### 2. Add State Management

```tsx
const [currentVersion, setCurrentVersion] = useState(1);
const [showVersionHistory, setShowVersionHistory] = useState(false);
```

### 3. Handle Version Changes

```tsx
const handleVersionChange = async (version: number) => {
  setCurrentVersion(version);
  // Load data for the selected version
  await loadDataForVersion(version);
};
```

### 4. Add UI Components

```tsx
// Option 1: Use the all-in-one component
<PhaseVersioningSection
  cycleId={cycleId}
  reportId={reportId}
  phaseName="Sample Selection"
  entityType="SampleSet"
  entityId={sampleSetId}
  currentVersion={currentVersion}
  onVersionChange={handleVersionChange}
/>

// Option 2: Use individual components
<VersionSelector
  entityType="SampleSet"
  entityId={sampleSetId}
  currentVersion={currentVersion}
  onVersionChange={handleVersionChange}
  onViewHistory={() => setShowVersionHistory(true)}
/>
```

## Permissions

Version management follows these permission rules:

- **Create Version**: Tester, Test Manager, Report Owner
- **Approve/Reject**: Report Owner, Report Owner Executive, Test Manager
- **View History**: All authenticated users

## Best Practices

1. **Entity ID Format**: Use consistent ID formats (e.g., `${cycleId}_${reportId}` for phase-specific entities).

2. **Version Loading**: Always handle version changes by reloading the appropriate data:
   ```tsx
   const loadDataForVersion = async (version: number) => {
     const versionData = await api.getVersionData(entityType, entityId, version);
     setData(versionData);
   };
   ```

3. **Read-Only Mode**: Disable version creation in read-only scenarios:
   ```tsx
   showCreateButton={!isReadOnly && canCreateVersion}
   ```

4. **Auto-Save Integration**: Coordinate versioning with auto-save features:
   ```tsx
   // Create new version when significant changes are saved
   if (significantChange) {
     await createNewVersion('Major update to test cases');
   }
   ```

5. **Version Comparison**: Use the compare API for showing differences:
   ```tsx
   const compareVersions = async (v1: number, v2: number) => {
     const diff = await versionApi.compareVersions(entityType, v1, v2);
     showDiffDialog(diff);
   };
   ```

## Example: Adding to Sample Selection Page

```tsx
// SampleSelectionPage.tsx
import React, { useState } from 'react';
import { PhaseVersioningSection } from '../../components/common/PhaseVersioningSection';

const SampleSelectionPage = ({ cycleId, reportId }) => {
  const [sampleSetId, setSampleSetId] = useState(null);
  const [currentVersion, setCurrentVersion] = useState(1);

  const handleVersionChange = async (version) => {
    setCurrentVersion(version);
    // Reload sample set for the selected version
    const versionedSampleSet = await sampleApi.getSampleSetVersion(sampleSetId, version);
    setSampleData(versionedSampleSet);
  };

  return (
    <Container>
      {/* Existing page content */}
      
      {/* Add versioning section */}
      {sampleSetId && (
        <PhaseVersioningSection
          cycleId={cycleId}
          reportId={reportId}
          phaseName="Sample Selection"
          entityType="SampleSet"
          entityId={sampleSetId}
          currentVersion={currentVersion}
          onVersionChange={handleVersionChange}
          showActivities={true}
          showApprovalButtons={true}
          readOnly={false}
        />
      )}
    </Container>
  );
};
```

## Troubleshooting

1. **Version not loading**: Ensure the entity type and ID match the backend expectations.
2. **Permissions error**: Check user role and entity-specific permissions.
3. **Version history empty**: Verify that the entity has been saved at least once.
4. **Approval buttons not showing**: Only shown for pending_approval status and authorized users.