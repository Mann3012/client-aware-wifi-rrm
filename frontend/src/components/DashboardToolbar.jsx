import React from 'react';
import { Box, Typography, Chip, FormControl, Select, MenuItem, InputLabel } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { format } from 'date-fns';

const DashboardToolbar = ({ healthData, selectedAp, setSelectedAp, anyError, lastUpdate }) => {
  const apStatusInfo = healthData?.find(ap => ap.ap_id === selectedAp);

  return (
    <Box sx={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      mb: 3, 
      p: 2, 
      bgcolor: 'background.paper', 
      borderRadius: 2,
      boxShadow: 1,
      flexWrap: 'wrap',
      gap: 2
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>NOC Overview</Typography>
        
        <FormControl sx={{ minWidth: 220 }} size="small">
          <InputLabel id="select-ap-label">Target Access Point</InputLabel>
          <Select
            labelId="select-ap-label"
            value={selectedAp}
            label="Target Access Point"
            onChange={(e) => setSelectedAp(e.target.value)}
            disabled={!healthData || healthData.length === 0}
            sx={{ fontWeight: 'bold' }}
          >
            {healthData && healthData.map((ap) => (
              <MenuItem key={ap.ap_id} value={ap.ap_id}>
                {ap.ap_id}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {apStatusInfo && (
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', ml: 2, borderLeft: 1, borderColor: 'divider', pl: 3 }}>
            <Typography variant="body2" color="text.secondary">Channel: <strong>{apStatusInfo.channel}</strong></Typography>
            <Typography variant="body2" color="text.secondary">Clients: <strong>{apStatusInfo.client_count}</strong></Typography>
            <Chip 
              size="small" 
              label={apStatusInfo.status} 
              color={apStatusInfo.status === 'Healthy' ? 'success' : (apStatusInfo.status === 'Warning' ? 'warning' : 'error')} 
            />
          </Box>
        )}
      </Box>

      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
        <Chip 
          icon={anyError ? <ErrorIcon /> : <CheckCircleIcon />} 
          label={anyError ? "Backend Disconnected" : "Backend Connected"} 
          color={anyError ? "error" : "success"} 
          variant="outlined"
          size="small"
        />
        <Chip 
          icon={anyError ? <ErrorIcon /> : <CheckCircleIcon />} 
          label={anyError ? "DB Error" : "Database Connected"} 
          color={anyError ? "error" : "success"} 
          variant="outlined"
          size="small"
        />
        <Chip 
          icon={anyError ? <ErrorIcon /> : <CheckCircleIcon />} 
          label={anyError ? "Stream Halted" : "Telemetry Streaming"} 
          color={anyError ? "error" : "success"} 
          variant="outlined"
          size="small"
        />
        <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
          Last Update: {lastUpdate ? format(new Date(lastUpdate), 'HH:mm:ss') : '--:--:--'}
        </Typography>
      </Box>
    </Box>
  );
};

export default DashboardToolbar;
