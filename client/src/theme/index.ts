import { createTheme, responsiveFontSizes } from '@mui/material/styles';

// Create a custom theme with a professional color palette
let theme = createTheme({
  palette: {
    primary: {
      main: '#2c3e50', // Dark blue/slate
      light: '#3e5771',
      dark: '#1a252f',
      contrastText: '#fff',
    },
    secondary: {
      main: '#3498db', // Bright blue
      light: '#5dade2',
      dark: '#2980b9',
      contrastText: '#fff',
    },
    error: {
      main: '#e74c3c', // Red for critical alerts
      light: '#ec7063',
      dark: '#c0392b',
    },
    warning: {
      main: '#f39c12', // Orange for warnings
      light: '#f5b041',
      dark: '#d68910',
    },
    info: {
      main: '#2ecc71', // Green for info
      light: '#58d68d',
      dark: '#27ae60',
    },
    success: {
      main: '#2ecc71', // Green for success
      light: '#58d68d',
      dark: '#27ae60',
    },
    background: {
      default: '#f5f7fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#2c3e50',
      secondary: '#7f8c8d',
    },
  },
  typography: {
    fontFamily: '"Montserrat", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
});

// Make fonts responsive
theme = responsiveFontSizes(theme);

export default theme;
