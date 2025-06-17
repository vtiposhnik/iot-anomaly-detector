/**
 * Login Component
 * 
 * Provides a login form for users to authenticate with the IoT Anomaly Detection System
 */

import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Container,
  Alert,
  CircularProgress
} from '@mui/material';
import { useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

/**
 * Login component
 */
const Login: React.FC = () => {
  // State for form fields
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState('');

  // Get authentication context
  const { login, loading, error, isLoggedIn } = useAuth();

  // Navigation
  const location = useLocation();

  // Get the redirect path from location state or default to dashboard
  const from = location.state?.from?.pathname || '/dashboard';

  /**
   * Handle form submission
   * 
   * @param event Form submit event
   */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    // Validate form
    if (!username.trim()) {
      setFormError('Username is required');
      return;
    }

    if (!password) {
      setFormError('Password is required');
      return;
    }

    setFormError('');

    try {
      // Attempt to login
      await login(username, password);
      
      // Redirect to the page user was trying to access
      // This will happen automatically after successful login due to the isLoggedIn check below
    } catch (err) {
      // Error is handled by the auth context
      console.error('Login failed:', err);
    }
  };

  if (isLoggedIn) {
    return <Navigate to={from} replace />;
  }

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <Typography component="h1" variant="h5">
            IoT Anomaly Detection System
          </Typography>

          <Typography component="h2" variant="h6" sx={{ mt: 2 }}>
            Sign In
          </Typography>

          {(error || formError) && (
            <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
              {formError || error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2, width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
            />

            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Sign In'}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
