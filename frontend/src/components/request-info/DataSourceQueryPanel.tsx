import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Stack,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Tooltip,
  Tabs,
  Tab,
  Divider,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Storage as StorageIcon,
  Search as SearchIcon,
  PlayArrow as PlayArrowIcon,
  Download as DownloadIcon,
  Code as CodeIcon,
  TableChart as TableChartIcon,
  Visibility as VisibilityIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Storage as DatabaseIcon,
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNotifications } from '../../contexts/NotificationContext';
import RequestInfoAPI from '../../api/requestInfo';
import { apiClient } from '../../api/client';

interface DataSource {
  data_source_id: string;
  source_name: string;
  connection_type: string;
  is_active: boolean;
  last_used?: string;
}

interface QueryRequest {
  query_request_id: string;
  data_source_id: string;
  query_type: 'ad_hoc' | 'predefined' | 'template';
  query_text: string;
  query_description: string;
  created_at: string;
  created_by: string;
  status: 'pending' | 'approved' | 'executed' | 'failed';
  result_count?: number;
  result_preview?: any[];
}

interface DataSourceQueryPanelProps {
  cycleId: number;
  reportId: number;
  onQueryResultsReceived: (results: any[]) => void;
}

const DataSourceQueryPanel: React.FC<DataSourceQueryPanelProps> = ({
  cycleId,
  reportId,
  onQueryResultsReceived,
}) => {
  const [selectedDataSource, setSelectedDataSource] = useState<string>('');
  const [queryType, setQueryType] = useState<'ad_hoc' | 'predefined' | 'template'>('predefined');
  const [queryText, setQueryText] = useState('');
  const [queryDescription, setQueryDescription] = useState('');
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const { showToast } = useNotifications();

  // Load available data sources
  const { data: dataSources, isLoading: sourcesLoading } = useQuery({
    queryKey: ['data-sources', cycleId, reportId],
    queryFn: async () => {
      const response = await apiClient.get(`/planning/cycles/${cycleId}/reports/${reportId}/data-sources`);
      return response.data;
    },
  });

  // Load query history
  const { data: queryHistory, refetch: refetchHistory } = useQuery({
    queryKey: ['query-history', cycleId, reportId],
    queryFn: async () => {
      const response = await apiClient.get(`/request-info/cycles/${cycleId}/reports/${reportId}/queries`);
      return response.data;
    },
  });

  // Submit query mutation
  const submitQueryMutation = useMutation({
    mutationFn: async (queryData: any) => {
      const response = await apiClient.post(
        `/request-info/cycles/${cycleId}/reports/${reportId}/queries`,
        queryData
      );
      return response.data;
    },
    onSuccess: (data) => {
      showToast('success', 'Query submitted successfully');
      refetchHistory();
      if (data.result_preview) {
        setPreviewData(data.result_preview);
        setShowPreviewDialog(true);
        onQueryResultsReceived(data.result_preview);
      }
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to submit query');
    },
  });

  // Execute query mutation
  const executeQueryMutation = useMutation({
    mutationFn: async (queryId: string) => {
      const response = await apiClient.post(
        `/request-info/cycles/${cycleId}/reports/${reportId}/queries/${queryId}/execute`
      );
      return response.data;
    },
    onSuccess: (data) => {
      showToast('success', 'Query executed successfully');
      refetchHistory();
      if (data.results) {
        setPreviewData(data.results);
        setShowPreviewDialog(true);
        onQueryResultsReceived(data.results);
      }
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to execute query');
    },
  });

  const handleSubmitQuery = () => {
    if (!selectedDataSource || !queryText || !queryDescription) {
      showToast('error', 'Please fill in all required fields');
      return;
    }

    submitQueryMutation.mutate({
      data_source_id: selectedDataSource,
      query_type: queryType,
      query_text: queryText,
      query_description: queryDescription,
    });
  };

  const getPredefinedQueries = () => {
    return [
      {
        id: 'sample_data',
        name: 'Sample Data Extract',
        description: 'Retrieve sample records for testing',
        template: 'SELECT * FROM {table_name} WHERE {conditions} LIMIT 1000',
      },
      {
        id: 'attribute_values',
        name: 'Attribute Value Analysis',
        description: 'Analyze distinct values for specific attributes',
        template: 'SELECT {attribute}, COUNT(*) as count FROM {table_name} GROUP BY {attribute} ORDER BY count DESC',
      },
      {
        id: 'data_quality',
        name: 'Data Quality Check',
        description: 'Check for null values and data completeness',
        template: 'SELECT {columns}, COUNT(*) as total_records, SUM(CASE WHEN {attribute} IS NULL THEN 1 ELSE 0 END) as null_count FROM {table_name}',
      },
      {
        id: 'boundary_analysis',
        name: 'Boundary Value Analysis',
        description: 'Find minimum and maximum values for numeric attributes',
        template: 'SELECT MIN({numeric_column}) as min_value, MAX({numeric_column}) as max_value, AVG({numeric_column}) as avg_value FROM {table_name}',
      },
    ];
  };

  return (
    <Box>
      <Typography variant="h6" display="flex" alignItems="center" gap={1} mb={3}>
        <DatabaseIcon />
        Data Source Queries
      </Typography>

      <Grid container spacing={3}>
        {/* Query Builder */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Create Query Request
              </Typography>

              <Stack spacing={3}>
                {/* Data Source Selection */}
                <FormControl fullWidth>
                  <InputLabel>Select Data Source</InputLabel>
                  <Select
                    value={selectedDataSource}
                    onChange={(e) => setSelectedDataSource(e.target.value)}
                    disabled={sourcesLoading}
                  >
                    {dataSources?.map((source: DataSource) => (
                      <MenuItem key={source.data_source_id} value={source.data_source_id}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <StorageIcon fontSize="small" />
                          {source.source_name}
                          <Chip
                            label={source.connection_type}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {/* Query Type Tabs */}
                <Tabs
                  value={queryType}
                  onChange={(e, value) => setQueryType(value)}
                  sx={{ borderBottom: 1, borderColor: 'divider' }}
                >
                  <Tab label="Predefined Queries" value="predefined" />
                  <Tab label="Custom Query" value="ad_hoc" />
                  <Tab label="Template Query" value="template" />
                </Tabs>

                {/* Query Input Based on Type */}
                {queryType === 'predefined' && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Select from common query patterns
                    </Typography>
                    <Stack spacing={1}>
                      {getPredefinedQueries().map((query) => (
                        <Card
                          key={query.id}
                          variant="outlined"
                          sx={{
                            cursor: 'pointer',
                            '&:hover': { bgcolor: 'action.hover' },
                            border: queryText === query.template ? 2 : 1,
                            borderColor: queryText === query.template ? 'primary.main' : 'divider',
                          }}
                          onClick={() => {
                            setQueryText(query.template);
                            setQueryDescription(query.description);
                          }}
                        >
                          <CardContent sx={{ py: 1 }}>
                            <Typography variant="subtitle2">{query.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {query.description}
                            </Typography>
                          </CardContent>
                        </Card>
                      ))}
                    </Stack>
                  </Box>
                )}

                {queryType === 'ad_hoc' && (
                  <TextField
                    label="SQL Query"
                    multiline
                    rows={6}
                    value={queryText}
                    onChange={(e) => setQueryText(e.target.value)}
                    fullWidth
                    placeholder="Enter your SQL query here..."
                    sx={{ fontFamily: 'monospace' }}
                  />
                )}

                {queryType === 'template' && (
                  <>
                    <Alert severity="info">
                      Use placeholders like {'{table_name}'}, {'{attribute}'}, {'{conditions}'} that will be replaced with actual values
                    </Alert>
                    <TextField
                      label="Query Template"
                      multiline
                      rows={4}
                      value={queryText}
                      onChange={(e) => setQueryText(e.target.value)}
                      fullWidth
                      placeholder="SELECT {columns} FROM {table_name} WHERE {conditions}"
                      sx={{ fontFamily: 'monospace' }}
                    />
                  </>
                )}

                {/* Query Description */}
                <TextField
                  label="Query Description"
                  value={queryDescription}
                  onChange={(e) => setQueryDescription(e.target.value)}
                  fullWidth
                  placeholder="Describe the purpose of this query..."
                  multiline
                  rows={2}
                />

                {/* Submit Button */}
                <Button
                  variant="contained"
                  startIcon={<PlayArrowIcon />}
                  onClick={handleSubmitQuery}
                  disabled={!selectedDataSource || !queryText || submitQueryMutation.isPending}
                  fullWidth
                >
                  {submitQueryMutation.isPending ? 'Submitting...' : 'Submit Query Request'}
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Query History */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Query History
              </Typography>

              {queryHistory && queryHistory.length > 0 ? (
                <Stack spacing={2}>
                  {queryHistory.slice(0, 5).map((query: QueryRequest) => (
                    <Card key={query.query_request_id} variant="outlined">
                      <CardContent sx={{ p: 2 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="start">
                          <Box flex={1}>
                            <Typography variant="body2" fontWeight="medium">
                              {query.query_description}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {query.query_type} • {new Date(query.created_at).toLocaleDateString()}
                            </Typography>
                          </Box>
                          <Chip
                            label={query.status}
                            size="small"
                            color={
                              query.status === 'executed' ? 'success' :
                              query.status === 'approved' ? 'primary' :
                              query.status === 'failed' ? 'error' : 'default'
                            }
                          />
                        </Box>

                        {query.status === 'approved' && (
                          <Box mt={1}>
                            <Button
                              size="small"
                              startIcon={<PlayArrowIcon />}
                              onClick={() => executeQueryMutation.mutate(query.query_request_id)}
                              disabled={executeQueryMutation.isPending}
                            >
                              Execute
                            </Button>
                          </Box>
                        )}

                        {query.result_count && (
                          <Box display="flex" alignItems="center" gap={1} mt={1}>
                            <TableChartIcon fontSize="small" color="action" />
                            <Typography variant="caption">
                              {query.result_count} records
                            </Typography>
                            <IconButton
                              size="small"
                              onClick={() => {
                                if (query.result_preview) {
                                  setPreviewData(query.result_preview);
                                  setShowPreviewDialog(true);
                                }
                              }}
                            >
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </Stack>
              ) : (
                <Alert severity="info">
                  No query history available. Create your first query request above.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Preview Dialog */}
      <Dialog
        open={showPreviewDialog}
        onClose={() => setShowPreviewDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Query Results Preview</DialogTitle>
        <DialogContent>
          {previewData.length > 0 && (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {Object.keys(previewData[0]).map((key) => (
                      <TableCell key={key}>{key}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {previewData.slice(0, 10).map((row, index) => (
                    <TableRow key={index}>
                      {Object.values(row).map((value: any, cellIndex) => (
                        <TableCell key={cellIndex}>
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          {previewData.length > 10 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Showing first 10 records of {previewData.length} total results
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPreviewDialog(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => {
              // Export functionality would go here
              showToast('info', 'Export functionality coming soon');
            }}
          >
            Export Results
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataSourceQueryPanel;