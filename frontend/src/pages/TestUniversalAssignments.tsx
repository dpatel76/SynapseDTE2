import React, { useState } from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  Stack,
  Chip,
} from '@mui/material';
import { useUniversalAssignments } from '../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../components/UniversalAssignmentAlert';
import apiClient from '../api/client';
import { toast } from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

const TestUniversalAssignments: React.FC = () => {
  const { user } = useAuth();
  const [testResult, setTestResult] = useState<string>('');
  const [loading, setLoading] = useState(false);
  
  // Test with dummy cycle and report IDs
  const testCycleId = 21;
  const testReportId = 156;
  
  const {
    assignments,
    isLoading,
    acknowledgeAssignment,
    startAssignment,
    completeAssignment,
    refreshAssignments,
  } = useUniversalAssignments({
    phase: 'Planning',
    cycleId: testCycleId,
    reportId: testReportId,
  });

  const createTestAssignment = async () => {
    setLoading(true);
    try {
      const response = await apiClient.post('/universal-assignments/assignments', {
        assignment_type: 'Phase Review',
        from_role: user?.role || 'Tester',
        to_role: 'Test Manager',
        title: 'Test Assignment - Review Planning Phase',
        description: 'This is a test assignment created from the frontend',
        task_instructions: 'Please review this test assignment',
        context_type: 'Report',
        context_data: {
          cycle_id: testCycleId,
          report_id: testReportId,
          phase_name: 'Planning',
        },
        priority: 'High',
        due_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours from now
        requires_approval: false,
      });

      setTestResult(`Created assignment: ${response.data.assignment_id}`);
      toast.success('Test assignment created successfully!');
      refreshAssignments();
    } catch (error: any) {
      setTestResult(`Error: ${error.response?.data?.detail || error.message}`);
      toast.error('Failed to create test assignment');
    } finally {
      setLoading(false);
    }
  };

  const testMetrics = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/universal-assignments/assignments/metrics');
      setTestResult(JSON.stringify(response.data, null, 2));
      toast.success('Metrics fetched successfully!');
    } catch (error: any) {
      setTestResult(`Error: ${error.response?.data?.detail || error.message}`);
      toast.error('Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Universal Assignments Test Page
      </Typography>

      <Stack spacing={3}>
        {/* Current User Info */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current User
            </Typography>
            <Typography variant="body2">
              Name: {user?.first_name} {user?.last_name}
            </Typography>
            <Typography variant="body2">
              Role: {user?.role}
            </Typography>
            <Typography variant="body2">
              Email: {user?.email}
            </Typography>
          </CardContent>
        </Card>

        {/* Test Actions */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Test Actions
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                onClick={createTestAssignment}
                disabled={loading}
              >
                Create Test Assignment
              </Button>
              <Button
                variant="outlined"
                onClick={testMetrics}
                disabled={loading}
              >
                Fetch Metrics
              </Button>
              <Button
                variant="outlined"
                onClick={refreshAssignments}
                disabled={loading}
              >
                Refresh Assignments
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Active Assignments */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Active Assignments ({assignments.length})
            </Typography>
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : assignments.length === 0 ? (
              <Alert severity="info">No active assignments found</Alert>
            ) : (
              <Stack spacing={2}>
                {assignments.map((assignment) => (
                  <UniversalAssignmentAlert
                    key={assignment.assignment_id}
                    assignment={assignment}
                    onAcknowledge={acknowledgeAssignment}
                    onStart={startAssignment}
                    onComplete={completeAssignment}
                  />
                ))}
              </Stack>
            )}
          </CardContent>
        </Card>

        {/* Test Results */}
        {testResult && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Test Results
              </Typography>
              <Box
                component="pre"
                sx={{
                  backgroundColor: 'grey.100',
                  p: 2,
                  borderRadius: 1,
                  overflow: 'auto',
                  fontSize: '0.875rem',
                }}
              >
                {testResult}
              </Box>
            </CardContent>
          </Card>
        )}
      </Stack>
    </Container>
  );
};

export default TestUniversalAssignments;