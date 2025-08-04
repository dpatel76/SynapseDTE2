import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  Typography,
  Chip,
  Divider,
  IconButton,
  Fade,
  Popper,
  ClickAwayListener,
  Autocomplete,
  Avatar,
  Badge,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Assessment,
  Science,
  BugReport,
  Person,
  Folder,
  Schedule,
  TrendingUp,
  DataUsage,
  Security,
  Settings,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Types for search system
interface SearchResult {
  id: string;
  type: 'cycle' | 'report' | 'phase' | 'test_case' | 'observation' | 'user' | 'document';
  title: string;
  subtitle?: string;
  description?: string;
  status?: string;
  priority?: string;
  category?: string;
  lastModified?: Date;
  tags?: string[];
  url: string;
  highlight?: string;
  relevanceScore: number;
}

interface SearchCategory {
  key: string;
  label: string;
  icon: React.ReactNode;
  count: number;
  color: string;
}

interface GlobalSearchProps {
  placeholder?: string;
  size?: 'small' | 'medium';
  variant?: 'outlined' | 'filled' | 'standard';
}

const GlobalSearch: React.FC<GlobalSearchProps> = ({
  placeholder = "Search cycles, tests, observations, users...",
  size = 'medium',
  variant = 'outlined'
}) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Mock search data for demonstration
  const mockSearchData: SearchResult[] = [
    // Test Cycles
    {
      id: 'cycle_001',
      type: 'cycle',
      title: 'Q4 2024 Financial Institutions',
      subtitle: 'Banking Regulatory Report',
      description: 'Quarterly testing cycle for financial institutions regulatory compliance',
      status: 'Active',
      lastModified: new Date('2025-01-15'),
      tags: ['Banking', 'Q4', 'Regulatory'],
      url: '/cycles',
      relevanceScore: 0.95,
    },
    {
      id: 'cycle_002',
      type: 'cycle',
      title: 'Q3 2024 Credit Unions',
      subtitle: 'Credit Union Report',
      description: 'Third quarter testing for credit union data validation',
      status: 'Completed',
      lastModified: new Date('2024-12-20'),
      tags: ['Credit Union', 'Q3', 'Completed'],
      url: '/cycles',
      relevanceScore: 0.85,
    },
    
    // Test Cases
    {
      id: 'tc_001',
      type: 'test_case',
      title: 'Institution Name Validation',
      subtitle: 'Data Validation • Institution_Name',
      description: 'Verify institution names comply with regulatory standards',
      status: 'Passed',
      priority: 'High',
      category: 'Data Validation',
      lastModified: new Date('2025-01-15'),
      tags: ['Validation', 'Institution', 'Names'],
      url: '/phases/test-execution',
      relevanceScore: 0.92,
    },
    {
      id: 'tc_002',
      type: 'test_case',
      title: 'Total Assets Calculation Logic',
      subtitle: 'Calculation Logic • Total_Assets',
      description: 'Validate total assets calculation methodology',
      status: 'Failed',
      priority: 'Critical',
      category: 'Calculation Logic',
      lastModified: new Date('2025-01-16'),
      tags: ['Calculation', 'Assets', 'Critical'],
      url: '/phases/test-execution',
      relevanceScore: 0.88,
    },
    
    // Observations
    {
      id: 'obs_001',
      type: 'observation',
      title: 'Calculation Error in Total Assets',
      subtitle: 'Critical • Total_Assets',
      description: '2.3% variance in total assets calculation due to derivative valuation',
      status: 'In Progress',
      priority: 'Critical',
      category: 'Calculation Error',
      lastModified: new Date('2025-01-16'),
      tags: ['Critical', 'Calculation', 'Assets'],
      url: '/phases/observation-management',
      relevanceScore: 0.90,
    },
    {
      id: 'obs_002',
      type: 'observation',
      title: 'Institution Name Whitespace Issue',
      subtitle: 'Resolved • Institution_Name',
      description: 'Trailing whitespace found in institution name fields',
      status: 'Resolved',
      priority: 'Low',
      category: 'Data Quality Issue',
      lastModified: new Date('2025-01-18'),
      tags: ['Resolved', 'Data Quality', 'Names'],
      url: '/phases/observation-management',
      relevanceScore: 0.75,
    },
    
    // Users
    {
      id: 'user_001',
      type: 'user',
      title: 'Jane Smith',
      subtitle: 'Senior Data Analyst',
      description: 'Lead testing analyst specializing in financial data validation',
      status: 'Active',
      lastModified: new Date('2025-01-10'),
      tags: ['Analyst', 'Testing', 'Financial'],
      url: '/users',
      relevanceScore: 0.80,
    },
    {
      id: 'user_002',
      type: 'user',
      title: 'John Doe',
      subtitle: 'Validation Specialist',
      description: 'Expert in calculation logic and business rule validation',
      status: 'Active',
      lastModified: new Date('2025-01-12'),
      tags: ['Specialist', 'Validation', 'Logic'],
      url: '/users',
      relevanceScore: 0.78,
    },
    
    // Reports
    {
      id: 'report_001',
      type: 'report',
      title: 'Q4 2024 Testing Summary',
      subtitle: 'Summary Report',
      description: 'Comprehensive testing results for Q4 2024 financial institutions',
      status: 'Published',
      lastModified: new Date('2025-01-20'),
      tags: ['Summary', 'Q4', 'Financial'],
      url: '/reports',
      relevanceScore: 0.85,
    },
    
    // Phase Documents
    {
      id: 'phase_planning',
      type: 'phase',
      title: 'Planning Phase',
      subtitle: 'Workflow Phase',
      description: 'Initial planning and setup for testing cycles',
      status: 'Complete',
      lastModified: new Date('2025-01-10'),
      tags: ['Planning', 'Phase', 'Setup'],
      url: '/phases/planning',
      relevanceScore: 0.70,
    },
    {
      id: 'phase_scoping',
      type: 'phase',
      title: 'Scoping Phase',
      subtitle: 'Workflow Phase',
      description: 'Define testing scope and attribute selection',
      status: 'Complete',
      lastModified: new Date('2025-01-12'),
      tags: ['Scoping', 'Attributes', 'Selection'],
      url: '/phases/scoping',
      relevanceScore: 0.72,
    },
  ];

  // Search categories
  const searchCategories: SearchCategory[] = [
    { key: 'all', label: 'All Results', icon: <SearchIcon />, count: 0, color: 'primary' },
    { key: 'cycle', label: 'Test Cycles', icon: <Assessment />, count: 0, color: 'primary' },
    { key: 'test_case', label: 'Test Cases', icon: <Science />, count: 0, color: 'success' },
    { key: 'observation', label: 'Observations', icon: <BugReport />, count: 0, color: 'warning' },
    { key: 'user', label: 'Users', icon: <Person />, count: 0, color: 'info' },
    { key: 'report', label: 'Reports', icon: <TrendingUp />, count: 0, color: 'secondary' },
    { key: 'phase', label: 'Phases', icon: <Folder />, count: 0, color: 'default' },
  ];

  // Perform search
  const performSearch = (term: string) => {
    if (!term.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    
    // Simulate API delay
    setTimeout(() => {
      const searchResults = mockSearchData
        .filter(item => {
          const searchText = `${item.title} ${item.subtitle} ${item.description} ${item.tags?.join(' ')}`.toLowerCase();
          const searchTerms = term.toLowerCase().split(' ');
          return searchTerms.every(searchTerm => searchText.includes(searchTerm));
        })
        .sort((a, b) => b.relevanceScore - a.relevanceScore)
        .slice(0, 20);

      // Add highlighting
      const highlightedResults = searchResults.map(result => ({
        ...result,
        highlight: highlightSearchTerm(result.title, term),
      }));

      setResults(highlightedResults);
      setLoading(false);
    }, 300);
  };

  // Highlight search terms
  const highlightSearchTerm = (text: string, term: string): string => {
    if (!term) return text;
    const regex = new RegExp(`(${term})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  };

  // Get icon for result type
  const getResultIcon = (type: string) => {
    switch (type) {
      case 'cycle': return <Assessment color="primary" />;
      case 'test_case': return <Science color="success" />;
      case 'observation': return <BugReport color="warning" />;
      case 'user': return <Person color="info" />;
      case 'report': return <TrendingUp color="secondary" />;
      case 'phase': return <Folder />;
      default: return <SearchIcon />;
    }
  };

  // Get status color
  const getStatusColor = (status: string, priority?: string) => {
    if (priority === 'Critical') return 'error';
    
    switch (status) {
      case 'Active':
      case 'In Progress': return 'primary';
      case 'Passed':
      case 'Complete':
      case 'Resolved': return 'success';
      case 'Failed': return 'error';
      case 'Published': return 'info';
      default: return 'default';
    }
  };

  // Handle search input change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setSearchTerm(value);
    performSearch(value);
    setIsOpen(value.length > 0);
  };

  // Handle result selection
  const handleResultSelect = (result: SearchResult) => {
    navigate(result.url);
    setIsOpen(false);
    setSearchTerm('');
  };

  // Handle clear search
  const handleClearSearch = () => {
    setSearchTerm('');
    setResults([]);
    setIsOpen(false);
  };

  // Filter results by category
  const filteredResults = selectedCategory === 'all' 
    ? results 
    : results.filter(result => result.type === selectedCategory);

  // Update category counts
  const categoriesWithCounts = searchCategories.map(category => ({
    ...category,
    count: category.key === 'all' 
      ? results.length 
      : results.filter(result => result.type === category.key).length
  }));

  // Format last modified date
  const formatLastModified = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <ClickAwayListener onClickAway={() => setIsOpen(false)}>
      <Box sx={{ position: 'relative', width: '100%', maxWidth: 500 }} ref={searchRef}>
        <TextField
          fullWidth
          size={size}
          variant={variant}
          placeholder={placeholder}
          value={searchTerm}
          onChange={handleSearchChange}
          onFocus={() => searchTerm && setIsOpen(true)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
            endAdornment: searchTerm && (
              <InputAdornment position="end">
                <IconButton size="small" onClick={handleClearSearch}>
                  <ClearIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              backgroundColor: 'background.paper',
            }
          }}
        />

        <Popper
          open={isOpen}
          anchorEl={searchRef.current}
          placement="bottom-start"
          style={{ width: searchRef.current?.offsetWidth || 'auto', zIndex: 1300 }}
          transition
        >
          {({ TransitionProps }) => (
            <Fade {...TransitionProps} timeout={200}>
              <Paper
                elevation={8}
                sx={{
                  mt: 1,
                  maxHeight: 500,
                  overflow: 'hidden',
                  border: 1,
                  borderColor: 'divider',
                }}
              >
                {loading ? (
                  <Box sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Searching...
                    </Typography>
                  </Box>
                ) : results.length > 0 ? (
                  <Box>
                    {/* Category Filter */}
                    <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider' }}>
                      <Box display="flex" gap={1} flexWrap="wrap">
                        {categoriesWithCounts.map((category) => (
                          <Chip
                            key={category.key}
                            label={`${category.label} (${category.count})`}
                            size="small"
                            variant={selectedCategory === category.key ? 'filled' : 'outlined'}
                            color={category.color as any}
                            icon={category.icon as React.ReactElement}
                            onClick={() => setSelectedCategory(category.key)}
                            sx={{ cursor: 'pointer' }}
                          />
                        ))}
                      </Box>
                    </Box>

                    {/* Search Results */}
                    <List
                      sx={{
                        maxHeight: 400,
                        overflow: 'auto',
                        p: 0,
                      }}
                    >
                      {filteredResults.slice(0, 10).map((result, index) => (
                        <ListItemButton
                          key={result.id}
                          onClick={() => handleResultSelect(result)}
                          sx={{
                            borderBottom: index < filteredResults.length - 1 ? 1 : 0,
                            borderColor: 'divider',
                            py: 1.5,
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 40 }}>
                            {getResultIcon(result.type)}
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box component="span" display="flex" alignItems="center" gap={1}>
                                <Typography
                                  component="span"
                                  variant="subtitle2"
                                  dangerouslySetInnerHTML={{ __html: result.highlight || result.title }}
                                />
                                {result.status && (
                                  <Chip
                                    label={result.status}
                                    size="small"
                                    color={getStatusColor(result.status, result.priority) as any}
                                    variant="outlined"
                                  />
                                )}
                                {result.priority && ['Critical', 'High'].includes(result.priority) && (
                                  <Chip
                                    label={result.priority}
                                    size="small"
                                    color={result.priority === 'Critical' ? 'error' : 'warning'}
                                  />
                                )}
                              </Box>
                            }
                            secondary={
                              <>
                                <Typography component="span" variant="body2" color="text.secondary" display="block">
                                  {result.subtitle}
                                </Typography>
                                {result.description && (
                                  <Typography component="span" variant="caption" color="text.secondary" display="block">
                                    {result.description.substring(0, 80)}
                                    {result.description.length > 80 ? '...' : ''}
                                  </Typography>
                                )}
                                <Box component="span" display="flex" alignItems="center" gap={2} mt={0.5}>
                                  {result.lastModified && (
                                    <Typography component="span" variant="caption" color="text.secondary">
                                      <Schedule sx={{ fontSize: 12, mr: 0.5 }} />
                                      {formatLastModified(result.lastModified)}
                                    </Typography>
                                  )}
                                  {result.tags && result.tags.length > 0 && (
                                    <Box component="span" display="flex" gap={0.5}>
                                      {result.tags.slice(0, 2).map((tag, tagIndex) => (
                                        <Chip
                                          key={tagIndex}
                                          label={tag}
                                          size="small"
                                          variant="outlined"
                                          sx={{ fontSize: '0.6rem', height: 16 }}
                                        />
                                      ))}
                                    </Box>
                                  )}
                                </Box>
                              </>
                            }
                          />
                        </ListItemButton>
                      ))}
                    </List>

                    {filteredResults.length > 10 && (
                      <Box sx={{ p: 1, textAlign: 'center', borderTop: 1, borderColor: 'divider' }}>
                        <Typography variant="caption" color="text.secondary">
                          Showing 10 of {filteredResults.length} results
                        </Typography>
                      </Box>
                    )}
                  </Box>
                ) : searchTerm ? (
                  <Box sx={{ p: 3, textAlign: 'center' }}>
                    <SearchIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                    <Typography variant="body2" color="text.secondary">
                      No results found for "{searchTerm}"
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Try different keywords or check spelling
                    </Typography>
                  </Box>
                ) : null}
              </Paper>
            </Fade>
          )}
        </Popper>
      </Box>
    </ClickAwayListener>
  );
};

export default GlobalSearch; 