import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  LinearProgress,
  Chip,
  Stack,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Info,
  ExpandMore,
  History
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface DetectionResults {
  processed_count: number;
  groups_created: number;
  observations_created: number;
  errors: string[];
  phase_id?: number;
  cycle_id?: number;
  report_id?: number;
  detection_timestamp?: string;
  detection_user_id?: number;
}

interface DetectionStatistics {
  total_failed_executions: number;
  failed_with_observations: number;
  failed_without_observations: number;
  detection_coverage: number;
  observation_groups: number;
  total_observations: number;
}

interface DetectionRunnerProps {
  phaseId?: number;
  cycleId?: number;
  reportId?: number;
}

const DetectionRunner: React.FC<DetectionRunnerProps> = ({
  phaseId,
  cycleId,
  reportId
}) => {
  const theme = useTheme();
  const [statistics, setStatistics] = useState<DetectionStatistics | null>(null);
  const [detectionResults, setDetectionResults] = useState<DetectionResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Configuration
  const [batchSize, setBatchSize] = useState(100);
  const [detectionScope, setDetectionScope] = useState<'phase' | 'cycle' | 'report'>('phase');
  
  // History dialog
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [detectionHistory, setDetectionHistory] = useState<DetectionResults[]>([]);

  useEffect(() => {
    fetchStatistics();
  }, [phaseId, cycleId, reportId]);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      setError(null);

      if (phaseId) {
        const response = await fetch(`/api/v1/observation-management-unified/detect/status/phase/${phaseId}`);
        if (response.ok) {
          const data = await response.json();
          setStatistics(data);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const runDetection = async () => {
    try {
      setRunning(true);
      setError(null);
      setSuccess(null);
      setDetectionResults(null);

      let endpoint = '';
      const params = new URLSearchParams();
      params.append('batch_size', batchSize.toString());

      if (detectionScope === 'phase' && phaseId) {
        endpoint = `/api/v1/observation-management-unified/detect/phase/${phaseId}`;
      } else if (detectionScope === 'cycle' && cycleId) {
        endpoint = `/api/v1/observation-management-unified/detect/cycle/${cycleId}`;
      } else if (detectionScope === 'report' && reportId) {
        endpoint = `/api/v1/observation-management-unified/detect/report/${reportId}`;
      } else {
        throw new Error('Invalid detection scope or missing ID');
      }

      const response = await fetch(`${endpoint}?${params}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Detection failed');
      }

      const results = await response.json();
      setDetectionResults(results);
      
      if (results.errors && results.errors.length > 0) {
        setError(`Detection completed with errors: ${results.errors.join(', ')}`);
      } else {
        setSuccess(`Detection completed successfully! Created ${results.groups_created} groups and ${results.observations_created} observations.`);
      }

      // Refresh statistics
      fetchStatistics();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Detection failed');
    } finally {
      setRunning(false);
    }
  };

  const canRunDetection = () => {
    return (detectionScope === 'phase' && phaseId) ||
           (detectionScope === 'cycle' && cycleId) ||
           (detectionScope === 'report' && reportId);
  };

  const getDetectionScopeLabel = () => {
    switch (detectionScope) {
      case 'phase': return 'Current Phase';
      case 'cycle': return 'Entire Cycle';
      case 'report': return 'Entire Report';
      default: return 'Unknown';
    }
  };

  const getCoverageColor = (coverage: number) => {
    if (coverage >= 0.8) return theme.palette.success.main;
    if (coverage >= 0.6) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  if (loading && !statistics) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Observation Detection
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Current Statistics */}
      {statistics && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Failed Executions
                </Typography>
                <Typography variant="h4">
                  {statistics.total_failed_executions}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  With Observations
                </Typography>
                <Typography variant="h4" color="success.main">
                  {statistics.failed_with_observations}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Without Observations
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {statistics.failed_without_observations}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Detection Coverage
                </Typography>
                <Typography variant="h4" sx={{ color: getCoverageColor(statistics.detection_coverage) }}>
                  {Math.round(statistics.detection_coverage * 100)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={statistics.detection_coverage * 100}
                  sx={{ 
                    mt: 1,
                    '& .MuiLinearProgress-bar': {
                      bgcolor: getCoverageColor(statistics.detection_coverage)
                    }
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Detection Configuration */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Detection Configuration
          </Typography>
          
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <FormControl fullWidth>
                <InputLabel>Detection Scope</InputLabel>
                <Select
                  value={detectionScope}
                  label="Detection Scope"
                  onChange={(e) => setDetectionScope(e.target.value as 'phase' | 'cycle' | 'report')}
                  disabled={running}
                >
                  {phaseId && <MenuItem value="phase">Current Phase</MenuItem>}
                  {cycleId && <MenuItem value="cycle">Entire Cycle</MenuItem>}
                  {reportId && <MenuItem value="report">Entire Report</MenuItem>}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <TextField
                fullWidth
                label="Batch Size"
                type="number"
                value={batchSize}
                onChange={(e) => setBatchSize(parseInt(e.target.value) || 100)}
                inputProps={{ min: 1, max: 1000 }}
                disabled={running}
              />
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={running ? <CircularProgress size={20} /> : <PlayArrow />}
                  onClick={runDetection}
                  disabled={running || !canRunDetection()}
                  fullWidth
                >
                  {running ? 'Running...' : 'Run Detection'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<History />}
                  onClick={() => setHistoryDialogOpen(true)}
                  disabled={running}
                >
                  History
                </Button>
              </Stack>
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Scope: {getDetectionScopeLabel()} | Batch Size: {batchSize} executions
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Detection Progress */}
      {running && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Detection in Progress
            </Typography>
            <LinearProgress sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              Processing failed test executions and creating observations...
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Last Detection Results */}
      {detectionResults && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Last Detection Results
            </Typography>
            
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Processed
                </Typography>
                <Typography variant="h6">
                  {detectionResults.processed_count}
                </Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Groups Created
                </Typography>
                <Typography variant="h6" color="success.main">
                  {detectionResults.groups_created}
                </Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Observations Created
                </Typography>
                <Typography variant="h6" color="primary.main">
                  {detectionResults.observations_created}
                </Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Errors
                </Typography>
                <Typography variant="h6" color="error.main">
                  {detectionResults.errors.length}
                </Typography>
              </Grid>
            </Grid>
            
            {detectionResults.detection_timestamp && (
              <Typography variant="body2" color="text.secondary">
                Completed at: {new Date(detectionResults.detection_timestamp).toLocaleString()}
              </Typography>
            )}
            
            {detectionResults.errors.length > 0 && (
              <Accordion sx={{ mt: 2 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography>
                    <ErrorIcon color="error" sx={{ mr: 1 }} />
                    View Errors ({detectionResults.errors.length})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={1}>
                    {detectionResults.errors.map((error, index) => (
                      <Alert key={index} severity="error">
                        {error}
                      </Alert>
                    ))}
                  </Stack>
                </AccordionDetails>
              </Accordion>
            )}
          </CardContent>
        </Card>
      )}

      {/* Detection Tips */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Detection Tips
          </Typography>
          
          <Stack spacing={2}>
            <Box display="flex" alignItems="flex-start" gap={1}>
              <Info color="info" />
              <Typography variant="body2">
                Detection automatically finds failed test executions and creates observation groups by attribute and LOB.
              </Typography>
            </Box>
            
            <Box display="flex" alignItems="flex-start" gap={1}>
              <CheckCircle color="success" />
              <Typography variant="body2">
                Run detection after test execution phases complete to capture all failures.
              </Typography>
            </Box>
            
            <Box display="flex" alignItems="flex-start" gap={1}>
              <Warning color="warning" />
              <Typography variant="body2">
                Use smaller batch sizes (50-100) for better performance on large datasets.
              </Typography>
            </Box>
            
            <Box display="flex" alignItems="flex-start" gap={1}>
              <ErrorIcon color="error" />
              <Typography variant="body2">
                Already processed test executions will be skipped to avoid duplicates.
              </Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* History Dialog */}
      <Dialog
        open={historyDialogOpen}
        onClose={() => setHistoryDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Detection History</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Recent detection runs for this phase
          </Typography>
          
          {detectionHistory.length === 0 ? (
            <Alert severity="info">
              No detection history available
            </Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Processed</TableCell>
                    <TableCell>Groups Created</TableCell>
                    <TableCell>Observations Created</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {detectionHistory.map((result, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        {result.detection_timestamp 
                          ? new Date(result.detection_timestamp).toLocaleString()
                          : 'N/A'
                        }
                      </TableCell>
                      <TableCell>{result.processed_count}</TableCell>
                      <TableCell>{result.groups_created}</TableCell>
                      <TableCell>{result.observations_created}</TableCell>
                      <TableCell>
                        <Chip
                          label={result.errors.length > 0 ? 'With Errors' : 'Success'}
                          color={result.errors.length > 0 ? 'warning' : 'success'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DetectionRunner;