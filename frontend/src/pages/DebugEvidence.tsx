import React, { useState } from 'react';
import { Box, Button, TextField, Typography, Paper } from '@mui/material';
import { requestInfoService } from '../services/requestInfoService';

export const DebugEvidence: React.FC = () => {
  const [testCaseId, setTestCaseId] = useState('408');
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const testApi = async () => {
    try {
      setError(null);
      setResponse(null);
      
      console.log(`Testing API for test case ${testCaseId}...`);
      const result = await requestInfoService.getTestCaseEvidenceDetails(testCaseId);
      
      console.log('Raw response:', result);
      console.log('Response data:', result.data);
      console.log('Current evidence:', result.data?.current_evidence);
      console.log('Current evidence count:', result.data?.current_evidence?.length || 0);
      
      setResponse(result.data);
    } catch (err: any) {
      console.error('Error:', err);
      setError(err.message || 'Unknown error');
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>Debug Evidence API</Typography>
      
      <Box display="flex" gap={2} mb={3}>
        <TextField
          label="Test Case ID"
          value={testCaseId}
          onChange={(e) => setTestCaseId(e.target.value)}
        />
        <Button variant="contained" onClick={testApi}>
          Test API
        </Button>
      </Box>

      {error && (
        <Paper sx={{ p: 2, mb: 2, bgcolor: 'error.light' }}>
          <Typography color="error">Error: {error}</Typography>
        </Paper>
      )}

      {response && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Response Data:</Typography>
          
          <Typography variant="subtitle1" gutterBottom>
            Test Case: {response.test_case?.test_case_name || 'N/A'}
          </Typography>
          
          <Typography variant="subtitle1" gutterBottom>
            Current Evidence Count: {response.current_evidence?.length || 0}
          </Typography>
          
          {response.current_evidence?.map((e: any, i: number) => (
            <Box key={i} ml={2} mb={1}>
              <Typography variant="body2">
                - Version {e.version_number}: {e.evidence_type} (is_current: {String(e.is_current)})
              </Typography>
            </Box>
          ))}
          
          <Typography variant="subtitle1" gutterBottom mt={2}>
            Validation Results Count: {response.validation_results?.length || 0}
          </Typography>
          
          <Typography variant="subtitle1" gutterBottom>
            Tester Decisions Count: {response.tester_decisions?.length || 0}
          </Typography>
          
          <details>
            <summary>Full JSON Response</summary>
            <pre>{JSON.stringify(response, null, 2)}</pre>
          </details>
        </Paper>
      )}
    </Box>
  );
};