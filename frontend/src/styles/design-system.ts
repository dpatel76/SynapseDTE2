/**
 * SynapseDTE Unified Design System
 * Consistent design tokens and components for the entire application
 */

// Color Palette - Deloitte Brand Colors
export const colors = {
  // Primary colors
  primary: {
    main: '#0E7C7B',      // Deloitte teal
    light: '#17A398',
    dark: '#0A5A59',
    contrast: '#FFFFFF'
  },
  
  // Secondary colors
  secondary: {
    main: '#62B5E5',      // Deloitte blue
    light: '#8AC5ED',
    dark: '#3A9BD8',
    contrast: '#FFFFFF'
  },
  
  // Semantic colors
  success: {
    main: '#4CAF50',
    light: '#81C784',
    dark: '#388E3C',
    background: '#E8F5E9'
  },
  
  warning: {
    main: '#FF9800',
    light: '#FFB74D',
    dark: '#F57C00',
    background: '#FFF3E0'
  },
  
  error: {
    main: '#F44336',
    light: '#E57373',
    dark: '#D32F2F',
    background: '#FFEBEE'
  },
  
  info: {
    main: '#2196F3',
    light: '#64B5F6',
    dark: '#1976D2',
    background: '#E3F2FD'
  },
  
  // Neutral colors
  grey: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#EEEEEE',
    300: '#E0E0E0',
    400: '#BDBDBD',
    500: '#9E9E9E',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121'
  },
  
  // Background colors
  background: {
    default: '#FAFAFA',
    paper: '#FFFFFF',
    dark: '#121212'
  },
  
  // Text colors
  text: {
    primary: 'rgba(0, 0, 0, 0.87)',
    secondary: 'rgba(0, 0, 0, 0.6)',
    disabled: 'rgba(0, 0, 0, 0.38)',
    hint: 'rgba(0, 0, 0, 0.38)'
  }
};

// Typography
export const typography = {
  fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  
  h1: {
    fontSize: '2.5rem',
    fontWeight: 700,
    lineHeight: 1.2,
    letterSpacing: '-0.01562em'
  },
  
  h2: {
    fontSize: '2rem',
    fontWeight: 600,
    lineHeight: 1.3,
    letterSpacing: '-0.00833em'
  },
  
  h3: {
    fontSize: '1.75rem',
    fontWeight: 600,
    lineHeight: 1.4,
    letterSpacing: '0em'
  },
  
  h4: {
    fontSize: '1.5rem',
    fontWeight: 500,
    lineHeight: 1.4,
    letterSpacing: '0.00735em'
  },
  
  h5: {
    fontSize: '1.25rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0em'
  },
  
  h6: {
    fontSize: '1.125rem',
    fontWeight: 500,
    lineHeight: 1.6,
    letterSpacing: '0.0075em'
  },
  
  body1: {
    fontSize: '1rem',
    fontWeight: 400,
    lineHeight: 1.5,
    letterSpacing: '0.00938em'
  },
  
  body2: {
    fontSize: '0.875rem',
    fontWeight: 400,
    lineHeight: 1.43,
    letterSpacing: '0.01071em'
  },
  
  caption: {
    fontSize: '0.75rem',
    fontWeight: 400,
    lineHeight: 1.66,
    letterSpacing: '0.03333em'
  },
  
  button: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.75,
    letterSpacing: '0.02857em',
    textTransform: 'uppercase' as const
  }
};

// Spacing
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48
};

// Breakpoints
export const breakpoints = {
  xs: 0,
  sm: 600,
  md: 960,
  lg: 1280,
  xl: 1920
};

// Shadows
export const shadows = {
  none: 'none',
  xs: '0px 2px 4px rgba(0, 0, 0, 0.05)',
  sm: '0px 4px 6px rgba(0, 0, 0, 0.07)',
  md: '0px 6px 12px rgba(0, 0, 0, 0.10)',
  lg: '0px 8px 16px rgba(0, 0, 0, 0.12)',
  xl: '0px 12px 24px rgba(0, 0, 0, 0.15)'
};

// Border radius
export const borderRadius = {
  xs: 2,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  round: '50%'
};

// Transitions
export const transitions = {
  easing: {
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    sharp: 'cubic-bezier(0.4, 0, 0.6, 1)'
  },
  duration: {
    shortest: 150,
    shorter: 200,
    short: 250,
    standard: 300,
    complex: 375,
    enteringScreen: 225,
    leavingScreen: 195
  }
};

// Z-index values
export const zIndex = {
  appBar: 1100,
  drawer: 1200,
  modal: 1300,
  snackbar: 1400,
  tooltip: 1500
};

// Component styles
export const components = {
  button: {
    primary: {
      backgroundColor: colors.primary.main,
      color: colors.primary.contrast,
      '&:hover': {
        backgroundColor: colors.primary.dark
      }
    },
    secondary: {
      backgroundColor: colors.secondary.main,
      color: colors.secondary.contrast,
      '&:hover': {
        backgroundColor: colors.secondary.dark
      }
    },
    outlined: {
      border: `1px solid ${colors.primary.main}`,
      color: colors.primary.main,
      '&:hover': {
        backgroundColor: colors.primary.light + '10'
      }
    }
  },
  
  card: {
    default: {
      backgroundColor: colors.background.paper,
      borderRadius: borderRadius.md,
      boxShadow: shadows.sm,
      padding: spacing.md
    },
    hover: {
      boxShadow: shadows.md,
      transform: 'translateY(-2px)',
      transition: `all ${transitions.duration.short}ms ${transitions.easing.easeInOut}`
    }
  },
  
  input: {
    default: {
      borderColor: colors.grey[300],
      '&:focus': {
        borderColor: colors.primary.main,
        boxShadow: `0 0 0 2px ${colors.primary.light}40`
      }
    },
    error: {
      borderColor: colors.error.main,
      '&:focus': {
        borderColor: colors.error.main,
        boxShadow: `0 0 0 2px ${colors.error.light}40`
      }
    }
  }
};

// Utility functions
export const getColor = (color: string, shade?: string) => {
  const colorGroup = colors[color as keyof typeof colors];
  if (typeof colorGroup === 'object' && shade) {
    return colorGroup[shade as keyof typeof colorGroup];
  }
  return colorGroup;
};

export const getSpacing = (...args: (keyof typeof spacing)[]) => {
  return args.map(key => `${spacing[key]}px`).join(' ');
};

// Media queries
export const mediaQuery = {
  up: (breakpoint: keyof typeof breakpoints) => 
    `@media (min-width: ${breakpoints[breakpoint]}px)`,
  down: (breakpoint: keyof typeof breakpoints) => 
    `@media (max-width: ${breakpoints[breakpoint] - 1}px)`,
  between: (start: keyof typeof breakpoints, end: keyof typeof breakpoints) =>
    `@media (min-width: ${breakpoints[start]}px) and (max-width: ${breakpoints[end] - 1}px)`
};