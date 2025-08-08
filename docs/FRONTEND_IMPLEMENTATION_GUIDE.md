# Frontend Implementation Guide - Evidence View for Testers

## Problem
When testers click the evidence icon, they don't see the same detailed view that data owners see. Currently, it either shows a simple popover or a "coming soon" message.

## Solution
Use the new endpoint `/api/v1/request-info/test-cases/{test_case_id}/evidence-details` to show the same detailed view.

## Implementation Steps

### 1. Create Evidence Details Modal Component

Create a new component `EvidenceDetailsModal.tsx`:

```typescript
import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Link
} from '@mui/material';
import { Close as CloseIcon, Download as DownloadIcon } from '@mui/icons-material';
import { requestInfoService } from '../../services/requestInfoService';

interface EvidenceDetailsModalProps {
  open: boolean;
  testCaseId: string;
  onClose: () => void;
  onResend?: () => void;
  userRole: string;
}

export const EvidenceDetailsModal: React.FC<EvidenceDetailsModalProps> = ({
  open,
  testCaseId,
  onClose,
  onResend,
  userRole
}) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    if (open && testCaseId) {
      fetchEvidenceDetails();
    }
  }, [open, testCaseId]);

  const fetchEvidenceDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await requestInfoService.getTestCaseEvidenceDetails(testCaseId);
      setData(response.data);
    } catch (err) {
      setError('Failed to load evidence details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (!open) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Evidence Details</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {loading && (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        )}
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        )}
        
        {!loading && !error && data && (
          <>
            {/* Test Case Info */}
            <Box mb={3}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Test Case Information
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Test Case" 
                    secondary={data.test_case.test_case_name}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Attribute" 
                    secondary={data.test_case.attribute_name}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Data Owner" 
                    secondary={`${data.test_case.data_owner_name} (${data.test_case.data_owner_email})`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Status" 
                    secondary={
                      <Chip 
                        label={data.test_case.status} 
                        size="small" 
                        color={data.test_case.status === 'Submitted' ? 'success' : 'warning'}
                      />
                    }
                  />
                </ListItem>
                {data.test_case.requires_revision && (
                  <ListItem>
                    <ListItemText 
                      primary="Revision Required" 
                      secondary={data.test_case.revision_reason}
                      secondaryTypographyProps={{ color: 'error' }}
                    />
                  </ListItem>
                )}
              </List>
            </Box>

            <Divider sx={{ my: 2 }} />

            {/* Tabs for Evidence Details */}
            <Tabs value={activeTab} onChange={handleTabChange}>
              <Tab label="Current Evidence" />
              <Tab label="Validation Results" />
              <Tab label="Tester Decisions" />
            </Tabs>

            <Box mt={2}>
              {activeTab === 0 && data.current_evidence && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Evidence Type: {data.current_evidence.evidence_type}
                  </Typography>
                  
                  {data.current_evidence.evidence_type === 'document' && data.current_evidence.file_info && (
                    <List>
                      <ListItem>
                        <ListItemText 
                          primary="File Name" 
                          secondary={data.current_evidence.file_info.original_filename}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="File Size" 
                          secondary={`${(data.current_evidence.file_info.file_size_bytes / 1024 / 1024).toFixed(2)} MB`}
                        />
                      </ListItem>
                      <ListItem>
                        <Link 
                          href={data.current_evidence.file_info.download_url} 
                          target="_blank"
                          rel="noopener"
                        >
                          <Button startIcon={<DownloadIcon />} variant="outlined" size="small">
                            Download File
                          </Button>
                        </Link>
                      </ListItem>
                    </List>
                  )}
                  
                  {data.current_evidence.evidence_type === 'data_source' && data.current_evidence.query_info && (
                    <List>
                      <ListItem>
                        <ListItemText 
                          primary="Data Source" 
                          secondary={data.current_evidence.query_info.data_source_name}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Query" 
                          secondary={
                            <Typography 
                              component="pre" 
                              variant="body2" 
                              sx={{ 
                                fontFamily: 'monospace', 
                                bgcolor: 'grey.100', 
                                p: 1, 
                                borderRadius: 1,
                                overflow: 'auto'
                              }}
                            >
                              {data.current_evidence.query_info.query_text}
                            </Typography>
                          }
                        />
                      </ListItem>
                    </List>
                  )}
                </Box>
              )}
              
              {activeTab === 1 && (
                <List>
                  {data.validation_results.map((result: any, index: number) => (
                    <ListItem key={index}>
                      <ListItemText 
                        primary={result.rule}
                        secondary={result.message}
                        secondaryTypographyProps={{ 
                          color: result.result === 'passed' ? 'success.main' : 'error.main' 
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
              
              {activeTab === 2 && (
                <List>
                  {data.tester_decisions.map((decision: any, index: number) => (
                    <ListItem key={index}>
                      <ListItemText 
                        primary={`${decision.decided_by} - ${decision.decision}`}
                        secondary={
                          <>
                            <Typography variant="body2">{decision.decision_notes}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(decision.decided_at).toLocaleString()}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        {data?.can_resend && userRole === 'Tester' && (
          <Button onClick={onResend} variant="contained" color="warning">
            Resend to Data Owner
          </Button>
        )}
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};
```

### 2. Update the Service Layer

Add the new method to `requestInfoService.ts`:

```typescript
// In services/requestInfoService.ts
export const requestInfoService = {
  // ... existing methods ...
  
  getTestCaseEvidenceDetails: (testCaseId: string) => {
    return api.get(`/api/v1/request-info/test-cases/${testCaseId}/evidence-details`);
  },
};
```

### 3. Update TestCasesTable Component

In `TestCasesTable.tsx`, replace the simple popover with the modal:

```typescript
// Add import
import { EvidenceDetailsModal } from '../EvidenceDetailsModal';

// Add state for modal
const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
const [selectedTestCaseId, setSelectedTestCaseId] = useState<string | null>(null);

// Update handleEvidenceClick
const handleEvidenceClick = (event: React.MouseEvent<HTMLElement>, testCase: TestCase) => {
  setSelectedTestCaseId(testCase.test_case_id);
  setEvidenceModalOpen(true);
};

// Replace the Popover with the Modal
{/* Remove the old Popover component */}

{/* Add the Evidence Details Modal */}
<EvidenceDetailsModal
  open={evidenceModalOpen}
  testCaseId={selectedTestCaseId || ''}
  onClose={() => {
    setEvidenceModalOpen(false);
    setSelectedTestCaseId(null);
  }}
  onResend={() => {
    // Handle resend action
    if (onResend && selectedTestCaseId) {
      const testCase = testCases.find(tc => tc.test_case_id === selectedTestCaseId);
      if (testCase) {
        onResend(testCase);
      }
    }
    setEvidenceModalOpen(false);
  }}
  userRole={userRole || 'Tester'}
/>
```

### 4. Update Pages Using TestCasesTable

In pages that use `TestCasesTable`, ensure the `onViewEvidence` prop is removed since we're handling it directly in the table:

```typescript
// In NewRequestInfoPage.tsx or similar
<TestCasesTable
  testCases={testCases}
  onResend={handleResend}
  // Remove onViewEvidence prop - it's handled internally now
/>
```

## Key Features Implemented

1. **Full Evidence Details**: Shows all information that data owners see
2. **Tabbed Interface**: Organizes information into Current Evidence, Validation Results, and Tester Decisions
3. **File Downloads**: Direct download links for document evidence
4. **Query Display**: Shows SQL queries for data source evidence
5. **Revision Status**: Clearly shows if revision is required and why
6. **Action Buttons**: Resend button enabled based on permissions

## Testing

1. Click on evidence icon for a test case with document evidence
2. Verify all tabs show correct information
3. Test download functionality for documents
4. Click on evidence icon for a test case with data source evidence
5. Verify query information is displayed correctly
6. Test resend functionality if user is a tester

This implementation ensures testers see the exact same detailed view that data owners see, maintaining consistency across the application.