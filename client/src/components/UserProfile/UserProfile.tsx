/**
 * User Profile Component
 * 
 * Displays information about the currently logged-in user
 */

import React from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Avatar, 
  Divider, 
  Chip,
  Button
} from '@mui/material';
import { Person as PersonIcon, Logout as LogoutIcon } from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';

/**
 * User Profile component
 */
const UserProfile: React.FC = () => {
  const { user, logout } = useAuth();

  // If no user is logged in, show a message
  if (!user) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1">
          Not logged in
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
          <PersonIcon />
        </Avatar>
        <Box>
          <Typography variant="h6">
            {user.full_name || user.username}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {user.email}
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Username
        </Typography>
        <Typography variant="body1">
          {user.username}
        </Typography>
      </Box>

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Roles
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {user.roles.map((role) => (
            <Chip 
              key={role} 
              label={role} 
              color={role === 'admin' ? 'primary' : 'default'} 
              size="small" 
            />
          ))}
        </Box>
      </Box>

      <Button
        variant="outlined"
        color="error"
        startIcon={<LogoutIcon />}
        onClick={logout}
        fullWidth
        sx={{ mt: 2 }}
      >
        Logout
      </Button>
    </Paper>
  );
};

export default UserProfile;
