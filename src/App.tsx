import { Container, Typography, CssBaseline } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from '@/components/Login';
import ProtectedRoute from '@/components/ProtectedRoute';
import UserProfile from '@/components/UserProfile';
import Alerts from '@/components/Alerts';
import { AuthProvider } from '@/context/AuthContext';
import theme from '@/theme';
import './App.css';
import Dashboard from '@/pages/Dashboard';
import { FC } from 'react';

const App: FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute>
                <Container maxWidth="sm" sx={{ mt: 4 }}>
                  <UserProfile />
                </Container>
              </ProtectedRoute>
            } />
            <Route path="/alerts" element={
              <ProtectedRoute>
                <Alerts />
              </ProtectedRoute>
            } />
            <Route path="/admin/*" element={
              <ProtectedRoute>
                <Container maxWidth="lg" sx={{ mt: 4 }}>
                  <Typography variant="h4" gutterBottom>Admin Panel</Typography>
                  <Typography>Admin functionality will be implemented here</Typography>
                </Container>
              </ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
