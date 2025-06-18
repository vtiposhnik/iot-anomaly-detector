import { FC } from 'react';
import { Box, Typography } from '@mui/material';
import ModelControls from '@/components/ModelControls';

const Settings: FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <ModelControls />
    </Box>
  );
};

export default Settings;
