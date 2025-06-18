/**
 * Authentication Header Component
 * 
 * Displays login/logout buttons and user information in the header
 */

import React from 'react';
import {
  Box,
  Button,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon
} from '@mui/material';
import {
  Person as PersonIcon,
  Logout as LogoutIcon,
  AdminPanelSettings as AdminIcon,
  Login as LoginIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

/**
 * Authentication Header component
 */
const AuthHeader: React.FC = () => {
  const { user, logout, isAdmin, isLoggedIn } = useAuth();
  const navigate = useNavigate();

  // Menu state
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  // Handle menu open
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  // Handle menu close
  const handleClose = () => {
    setAnchorEl(null);
  };

  // Handle login button click
  const handleLogin = () => {
    navigate('/login');
  };

  // Handle profile menu item click
  const handleProfile = () => {
    handleClose();
    navigate('/profile');
  };

  // Handle admin panel menu item click
  const handleAdmin = () => {
    handleClose();
    navigate('/admin');
  };

  // Handle logout menu item click
  const handleLogout = () => {
    handleClose();
    logout();
    navigate('/login');
  };


  if (isLoggedIn) {
    return (
      <>
        <Button
          onClick={handleClick}
          color="inherit"
          startIcon={
            <Avatar
              sx={{
                width: 32,
                height: 32,
                bgcolor: 'primary.main',
                color: 'white'
              }}
            >
              {user?.username.charAt(0).toUpperCase()}
            </Avatar>
          }
          sx={{ textTransform: 'none' }}
        >
          {user?.full_name || user?.username}
        </Button>

        <Menu
          anchorEl={anchorEl}
          open={open}
          onClose={handleClose}
          onClick={handleClose}
          PaperProps={{
            elevation: 3,
            sx: {
              minWidth: 200,
              mt: 1
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem onClick={handleProfile}>
            <ListItemIcon>
              <PersonIcon fontSize="small" />
            </ListItemIcon>
            Profile
          </MenuItem>

          {isAdmin() && (
            <MenuItem onClick={handleAdmin}>
              <ListItemIcon>
                <AdminIcon fontSize="small" />
              </ListItemIcon>
              Admin Panel
            </MenuItem>
          )}

          <Divider />

          <MenuItem onClick={handleLogout}>
            <ListItemIcon>
              <LogoutIcon fontSize="small" />
            </ListItemIcon>
            Logout
          </MenuItem>
        </Menu>
      </>
    )
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <Button
        color="inherit"
        onClick={handleLogin}
        startIcon={<LoginIcon />}
      >
        Login
      </Button>
    </Box>
  );
};

export default AuthHeader;
