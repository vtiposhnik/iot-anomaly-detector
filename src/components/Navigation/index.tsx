import React from 'react';
import { Box, List, ListItem, ListItemIcon, ListItemText, Divider, Paper } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  Dashboard as DashboardIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  DeviceHub as DevicesIcon,
  Assessment as AssessmentIcon,
  Person as PersonIcon
} from '@mui/icons-material';

/**
 * Navigation component for the dashboard
 * Provides links to different sections of the application
 */
const Navigation: React.FC = () => {
  const location = useLocation();
  
  // Navigation items
  const navItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'Alerts', icon: <NotificationsIcon />, path: '/alerts' },
    { text: 'Devices', icon: <DevicesIcon />, path: '/devices' },
    { text: 'Analytics', icon: <AssessmentIcon />, path: '/analytics' },
    { text: 'Profile', icon: <PersonIcon />, path: '/profile' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' }
  ];
  
  return (
    <Paper elevation={1} sx={{ height: '100%', borderRadius: 0 }}>
      <Box sx={{ width: '100%', maxWidth: 240 }}>
        <List component="nav" aria-label="main navigation">
          {navItems.map((item) => (
            <ListItem 
              button 
              key={item.text} 
              component={RouterLink} 
              to={item.path}
              selected={location.pathname === item.path}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'primary.light',
                  color: 'primary.contrastText',
                  '& .MuiListItemIcon-root': {
                    color: 'primary.contrastText',
                  },
                  '&:hover': {
                    backgroundColor: 'primary.main',
                  }
                },
                '&:hover': {
                  backgroundColor: 'action.hover',
                }
              }}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
        <Divider />
      </Box>
    </Paper>
  );
};

export default Navigation;
