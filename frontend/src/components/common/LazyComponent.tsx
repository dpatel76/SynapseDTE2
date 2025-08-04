import React, { Suspense, ComponentType } from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  Alert,
  Fade,
  LinearProgress,
} from '@mui/material';
import ErrorBoundary from './ErrorBoundary';

interface LazyComponentProps {
  fallback?: React.ReactNode;
  errorFallback?: React.ReactNode;
  loadingText?: string;
  minLoadingTime?: number;
}

// Default loading component
const DefaultLoadingFallback: React.FC<{ loadingText?: string }> = ({ loadingText = 'Loading...' }) => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '200px',
      gap: 2,
    }}
  >
    <LinearProgress sx={{ width: '100%', mb: 2 }} />
    <CircularProgress size={48} />
    <Typography variant="body1" color="text.secondary">
      {loadingText}
    </Typography>
  </Box>
);

// Default error fallback
const DefaultErrorFallback: React.FC = () => (
  <Alert severity="error" sx={{ m: 2 }}>
    <Typography variant="h6" gutterBottom>
      Failed to load component
    </Typography>
    <Typography variant="body2">
      There was an error loading this part of the application. Please try refreshing the page.
    </Typography>
  </Alert>
);

// Higher-order component for lazy loading
export function withLazyLoading<P extends object>(
  LazyComponent: React.LazyExoticComponent<ComponentType<P>>,
  options: LazyComponentProps = {}
) {
  const {
    fallback,
    errorFallback,
    loadingText,
    minLoadingTime = 300, // Minimum loading time to prevent flash
  } = options;

  return function LazyWrapper(props: P) {
    const [showLoading, setShowLoading] = React.useState(true);

    React.useEffect(() => {
      const timer = setTimeout(() => {
        setShowLoading(false);
      }, minLoadingTime);

      return () => clearTimeout(timer);
    }, []);

    const LoadingFallback = fallback || <DefaultLoadingFallback loadingText={loadingText} />;
    const ErrorFallback = errorFallback || <DefaultErrorFallback />;

    return (
      <ErrorBoundary fallback={ErrorFallback}>
        <Suspense fallback={LoadingFallback}>
          <Fade in={!showLoading} timeout={300}>
            <Box>
              <LazyComponent {...props} />
            </Box>
          </Fade>
        </Suspense>
      </ErrorBoundary>
    );
  };
}

// Component for wrapping lazy components directly
export const LazyComponent: React.FC<LazyComponentProps & { children: React.ReactNode }> = ({
  children,
  fallback,
  errorFallback,
  loadingText,
}) => {
  const LoadingFallback = fallback || <DefaultLoadingFallback loadingText={loadingText} />;
  const ErrorFallback = errorFallback || <DefaultErrorFallback />;

  return (
    <ErrorBoundary fallback={ErrorFallback}>
      <Suspense fallback={LoadingFallback}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
};

export default LazyComponent; 