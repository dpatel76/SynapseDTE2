import React, { useState } from 'react';
import Grid from '@mui/material/Grid';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Stack,
  Alert,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  Checkbox,
  FormControlLabel,
  FormGroup,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Science as ScienceIcon,
  BugReport as BugReportIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  Security as SecurityIcon,
  Shuffle as ShuffleIcon,
  Preview as PreviewIcon,
  Download as DownloadIcon,
  FilterList as FilterListIcon,
  Analytics as AnalyticsIcon,
  AutoFixHigh as AutoFixHighIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as ChartTooltip, Legend } from 'recharts';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNotifications } from '../contexts/NotificationContext';

interface SamplePool {
  pool_id: string;
  category: 'normal' | 'anomaly' | 'boundary_high' | 'boundary_low' | 'outlier' | 'edge_case' | 'high_risk';
  total_candidates: number;
  diversity_score: number;
  relevance_score: number;
}

interface IntelligentSample {
  sample_id: string;
  record_identifier: string;
  category: string;
  selection_reason: string;
  anomaly_score?: number;
  risk_score?: number;
  testing_priority: number;
  must_test: boolean;
  masked_data: Record<string, any>;
}

interface SamplingConfig {
  target_sample_size: number;
  strategies: string[];
  normal_percentage: number;
  anomaly_percentage: number;
  boundary_percentage: number;
  edge_case_percentage: number;
}

interface IntelligentSamplingPanelProps {
  cycleId: number;
  reportId: number;
  profilingJobId?: string;
}

// Mock API
const api = {
  getSamplePools: async (profilingJobId: string): Promise<SamplePool[]> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return [
      {
        pool_id: '1',
        category: 'anomaly',
        total_candidates: 12543,
        diversity_score: 0.85,
        relevance_score: 0.92,
      },
      {
        pool_id: '2',
        category: 'boundary_high',
        total_candidates: 3421,
        diversity_score: 0.72,
        relevance_score: 0.88,
      },
      {
        pool_id: '3',
        category: 'boundary_low',
        total_candidates: 2876,
        diversity_score: 0.68,
        relevance_score: 0.85,
      },
      {
        pool_id: '4',
        category: 'high_risk',
        total_candidates: 1543,
        diversity_score: 0.90,
        relevance_score: 0.95,
      },
      {
        pool_id: '5',
        category: 'normal',
        total_candidates: 458923,
        diversity_score: 0.45,
        relevance_score: 0.50,
      },
    ];
  },

  createSamplingJob: async (config: SamplingConfig & { profiling_job_id: string }): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 1500));
    return 'job-123';
  },

  getSelectedSamples: async (jobId: string): Promise<IntelligentSample[]> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return [
      {
        sample_id: '1',
        record_identifier: 'CUST_000123',
        category: 'anomaly',
        selection_reason: 'Failed 3 profiling rules; High anomaly score',
        anomaly_score: 0.92,
        risk_score: 0.75,
        testing_priority: 9,
        must_test: true,
        masked_data: {
          customer_id: 'CUST_000123',
          ssn: 'XXX-XX-4567',
          balance: 150000.00,
          transaction_count: 1250,
        },
      },
      {
        sample_id: '2',
        record_identifier: 'CUST_000456',
        category: 'boundary_high',
        selection_reason: 'Boundary high value for balance attribute',
        anomaly_score: 0.45,
        risk_score: 0.88,
        testing_priority: 8,
        must_test: false,
        masked_data: {
          customer_id: 'CUST_000456',
          ssn: 'XXX-XX-8901',
          balance: 2500000.00,
          transaction_count: 50,
        },
      },
      // More samples...
    ];
  },

  previewSamples: async (poolId: string, count: number): Promise<IntelligentSample[]> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return Array.from({ length: count }, (_, i) => ({
      sample_id: `preview-${i}`,
      record_identifier: `CUST_${Math.floor(Math.random() * 1000000)}`,
      category: 'anomaly',
      selection_reason: 'Sample preview',
      anomaly_score: Math.random(),
      risk_score: Math.random(),
      testing_priority: Math.floor(Math.random() * 10) + 1,
      must_test: Math.random() > 0.7,
      masked_data: {
        customer_id: `CUST_${Math.floor(Math.random() * 1000000)}`,
        ssn: 'XXX-XX-****',
        balance: Math.floor(Math.random() * 100000),
      },
    }));
  },
};

const CATEGORY_COLORS = {
  normal: '#4caf50',
  anomaly: '#f44336',
  boundary_high: '#ff9800',
  boundary_low: '#03a9f4',
  outlier: '#9c27b0',
  edge_case: '#795548',
  high_risk: '#e91e63',
};

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'anomaly': return <BugReportIcon />;
    case 'boundary_high': return <TrendingUpIcon />;
    case 'boundary_low': return <TrendingDownIcon />;
    case 'high_risk': return <WarningIcon />;
    case 'normal': return <CheckIcon />;
    default: return <ScienceIcon />;
  }
};

const IntelligentSamplingPanel: React.FC<IntelligentSamplingPanelProps> = ({
  cycleId,
  reportId,
  profilingJobId,
}) => {
  const [config, setConfig] = useState<SamplingConfig>({
    target_sample_size: 1000,
    strategies: ['anomaly_based', 'boundary', 'risk_based', 'random'],
    normal_percentage: 40,
    anomaly_percentage: 30,
    boundary_percentage: 20,
    edge_case_percentage: 10,
  });
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [selectedPool, setSelectedPool] = useState<SamplePool | null>(null);
  const [samplingJobId, setSamplingJobId] = useState<string | null>(null);
  const { showToast } = useNotifications();

  // Queries
  const { data: pools, isLoading: poolsLoading } = useQuery({
    queryKey: ['sample-pools', profilingJobId],
    queryFn: () => api.getSamplePools(profilingJobId!),
    enabled: !!profilingJobId,
  });

  const { data: selectedSamples, isLoading: samplesLoading } = useQuery({
    queryKey: ['selected-samples', samplingJobId],
    queryFn: () => api.getSelectedSamples(samplingJobId!),
    enabled: !!samplingJobId,
  });

  const { data: previewSamples } = useQuery({
    queryKey: ['preview-samples', selectedPool?.pool_id],
    queryFn: () => api.previewSamples(selectedPool!.pool_id, 5),
    enabled: !!selectedPool && previewDialogOpen,
  });

  // Mutations
  const createJobMutation = useMutation({
    mutationFn: (config: SamplingConfig) => 
      api.createSamplingJob({ ...config, profiling_job_id: profilingJobId! }),
    onSuccess: (jobId) => {
      setSamplingJobId(jobId);
      showToast('success', 'Intelligent sampling job created');
    },
    onError: (error: Error) => {
      showToast('error', `Failed to create sampling job: ${error.message}`);
    },
  });

  const handleStrategyChange = (strategy: string) => {
    const newStrategies = config.strategies.includes(strategy)
      ? config.strategies.filter(s => s !== strategy)
      : [...config.strategies, strategy];
    setConfig({ ...config, strategies: newStrategies });
  };

  const handlePercentageChange = (field: string, value: number) => {
    const newConfig = { ...config, [field]: value };
    
    // Ensure percentages add up to 100
    const total = newConfig.normal_percentage + newConfig.anomaly_percentage + 
                  newConfig.boundary_percentage + newConfig.edge_case_percentage;
    
    if (total !== 100) {
      // Adjust normal percentage to compensate
      newConfig.normal_percentage = Math.max(0, newConfig.normal_percentage - (total - 100));
    }
    
    setConfig(newConfig);
  };

  const distributionData = [
    { name: 'Normal', value: config.normal_percentage, color: CATEGORY_COLORS.normal },
    { name: 'Anomaly', value: config.anomaly_percentage, color: CATEGORY_COLORS.anomaly },
    { name: 'Boundary', value: config.boundary_percentage, color: CATEGORY_COLORS.boundary_high },
    { name: 'Edge Case', value: config.edge_case_percentage, color: CATEGORY_COLORS.high_risk },
  ];

  const poolStats = pools?.reduce((acc, pool) => {
    acc.totalCandidates += pool.total_candidates;
    acc.avgDiversity += pool.diversity_score;
    acc.avgRelevance += pool.relevance_score;
    return acc;
  }, { totalCandidates: 0, avgDiversity: 0, avgRelevance: 0 });

  if (poolStats && pools) {
    poolStats.avgDiversity /= pools.length;
    poolStats.avgRelevance /= pools.length;
  }

  if (!profilingJobId) {
    return (
      <Alert severity="info">
        Please complete profiling before selecting samples.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" display="flex" alignItems="center" gap={1} mb={3}>
        <ScienceIcon />
        Intelligent Sample Selection
      </Typography>

      <Grid container spacing={3}>
        {/* Configuration Panel */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="subtitle1" gutterBottom>Sampling Configuration</Typography>
            
            <Stack spacing={3}>
              {/* Target Sample Size */}
              <TextField
                label="Target Sample Size"
                type="number"
                value={config.target_sample_size}
                onChange={(e) => setConfig({ ...config, target_sample_size: parseInt(e.target.value) })}
                fullWidth
              />

              {/* Sampling Strategies */}
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Sampling Strategies
                </Typography>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={config.strategies.includes('anomaly_based')}
                        onChange={() => handleStrategyChange('anomaly_based')}
                      />
                    }
                    label="Anomaly-based"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={config.strategies.includes('boundary')}
                        onChange={() => handleStrategyChange('boundary')}
                      />
                    }
                    label="Boundary Values"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={config.strategies.includes('risk_based')}
                        onChange={() => handleStrategyChange('risk_based')}
                      />
                    }
                    label="Risk-based"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={config.strategies.includes('random')}
                        onChange={() => handleStrategyChange('random')}
                      />
                    }
                    label="Random Baseline"
                  />
                </FormGroup>
              </Box>

              {/* Distribution Sliders */}
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Sample Distribution
                </Typography>
                
                <Box sx={{ px: 2 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2">Normal</Typography>
                    <Typography variant="body2">{config.normal_percentage}%</Typography>
                  </Box>
                  <Slider
                    value={config.normal_percentage}
                    onChange={(_, value) => handlePercentageChange('normal_percentage', value as number)}
                    min={0}
                    max={100}
                    sx={{ color: CATEGORY_COLORS.normal }}
                  />

                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2">Anomaly</Typography>
                    <Typography variant="body2">{config.anomaly_percentage}%</Typography>
                  </Box>
                  <Slider
                    value={config.anomaly_percentage}
                    onChange={(_, value) => handlePercentageChange('anomaly_percentage', value as number)}
                    min={0}
                    max={100}
                    sx={{ color: CATEGORY_COLORS.anomaly }}
                  />

                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2">Boundary</Typography>
                    <Typography variant="body2">{config.boundary_percentage}%</Typography>
                  </Box>
                  <Slider
                    value={config.boundary_percentage}
                    onChange={(_, value) => handlePercentageChange('boundary_percentage', value as number)}
                    min={0}
                    max={100}
                    sx={{ color: CATEGORY_COLORS.boundary_high }}
                  />

                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2">Edge Case</Typography>
                    <Typography variant="body2">{config.edge_case_percentage}%</Typography>
                  </Box>
                  <Slider
                    value={config.edge_case_percentage}
                    onChange={(_, value) => handlePercentageChange('edge_case_percentage', value as number)}
                    min={0}
                    max={100}
                    sx={{ color: CATEGORY_COLORS.high_risk }}
                  />
                </Box>
              </Box>

              <Button
                variant="contained"
                fullWidth
                startIcon={<AutoFixHighIcon />}
                onClick={() => createJobMutation.mutate(config)}
                disabled={createJobMutation.isPending || !config.strategies.length}
              >
                {createJobMutation.isPending ? 'Creating Job...' : 'Create Intelligent Sampling Job'}
              </Button>
            </Stack>
          </Paper>
        </Grid>

        {/* Pool Statistics and Visualization */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="subtitle1" gutterBottom>Sample Pool Analysis</Typography>
            
            {poolsLoading ? (
              <CircularProgress />
            ) : pools && poolStats ? (
              <Stack spacing={3}>
                {/* Summary Stats */}
                <Grid container spacing={2}>
                  <Grid size={{ xs: 4 }}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {poolStats.totalCandidates.toLocaleString()}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Total Candidates
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 4 }}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="secondary">
                        {(poolStats.avgDiversity * 100).toFixed(0)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Avg Diversity
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 4 }}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {(poolStats.avgRelevance * 100).toFixed(0)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Avg Relevance
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {/* Distribution Chart */}
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Target Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={distributionData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                      >
                        {distributionData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <ChartTooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>

                {/* Pool List */}
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Available Pools
                  </Typography>
                  <Stack spacing={1}>
                    {pools.map(pool => (
                      <Card key={pool.pool_id} variant="outlined">
                        <CardContent sx={{ p: 2 }}>
                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Box display="flex" alignItems="center" gap={1}>
                              {getCategoryIcon(pool.category)}
                              <Box>
                                <Typography variant="body2" fontWeight="medium">
                                  {pool.category.replace('_', ' ').toUpperCase()}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {pool.total_candidates.toLocaleString()} candidates
                                </Typography>
                              </Box>
                            </Box>
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedPool(pool);
                                setPreviewDialogOpen(true);
                              }}
                            >
                              <PreviewIcon />
                            </IconButton>
                          </Box>
                          <Box display="flex" gap={2} mt={1}>
                            <Chip
                              label={`Diversity: ${(pool.diversity_score * 100).toFixed(0)}%`}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={`Relevance: ${(pool.relevance_score * 100).toFixed(0)}%`}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </Stack>
                </Box>
              </Stack>
            ) : (
              <Alert severity="info">No sample pools available</Alert>
            )}
          </Paper>
        </Grid>

        {/* Selected Samples */}
        {selectedSamples && (
          <Grid size={{ xs: 12 }}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="subtitle1">
                  Selected Samples ({selectedSamples.length})
                </Typography>
                <Button startIcon={<DownloadIcon />} variant="outlined">
                  Export Samples
                </Button>
              </Box>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Sample ID</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell>Selection Reason</TableCell>
                      <TableCell align="center">Risk Score</TableCell>
                      <TableCell align="center">Priority</TableCell>
                      <TableCell align="center">Must Test</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {selectedSamples.slice(0, 10).map(sample => (
                      <TableRow key={sample.sample_id}>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {sample.record_identifier}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getCategoryIcon(sample.category)}
                            label={sample.category.toUpperCase()}
                            size="small"
                            sx={{ 
                              bgcolor: `${CATEGORY_COLORS[sample.category as keyof typeof CATEGORY_COLORS]}20`,
                              color: CATEGORY_COLORS[sample.category as keyof typeof CATEGORY_COLORS],
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ maxWidth: 300 }}>
                            {sample.selection_reason}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Box display="flex" alignItems="center" gap={1}>
                            <LinearProgress
                              variant="determinate"
                              value={sample.risk_score! * 100}
                              sx={{ width: 60, height: 6 }}
                              color={sample.risk_score! > 0.7 ? 'error' : 'warning'}
                            />
                            <Typography variant="caption">
                              {(sample.risk_score! * 100).toFixed(0)}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <Badge
                            badgeContent={sample.testing_priority}
                            color={sample.testing_priority > 7 ? 'error' : 'primary'}
                          />
                        </TableCell>
                        <TableCell align="center">
                          {sample.must_test && (
                            <Chip label="Required" size="small" color="error" />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        )}
      </Grid>

      {/* Preview Dialog */}
      <Dialog open={previewDialogOpen} onClose={() => setPreviewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Sample Pool Preview: {selectedPool?.category.replace('_', ' ').toUpperCase()}
        </DialogTitle>
        <DialogContent>
          {previewSamples ? (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Record ID</TableCell>
                    <TableCell>Risk Score</TableCell>
                    <TableCell>Masked Data</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {previewSamples.map(sample => (
                    <TableRow key={sample.sample_id}>
                      <TableCell>{sample.record_identifier}</TableCell>
                      <TableCell>{(sample.risk_score! * 100).toFixed(0)}%</TableCell>
                      <TableCell>
                        <Typography variant="caption" component="pre">
                          {JSON.stringify(sample.masked_data, null, 2)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <CircularProgress />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default IntelligentSamplingPanel;