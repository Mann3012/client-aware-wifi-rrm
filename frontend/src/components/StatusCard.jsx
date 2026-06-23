import React from 'react';
import { Card, CardContent, Typography, Box, Skeleton, Chip } from '@mui/material';

const StatusCard = ({ title, status, description, icon, loading, severity }) => {
  const getSeverityColor = (sev) => {
    switch (sev?.toLowerCase()) {
      case 'info':
      case 'good':
      case 'healthy':
      case 'none':
        return 'success.main';
      case 'warning':
      case 'medium':
        return 'warning.main';
      case 'error':
      case 'high':
      case 'critical':
        return 'error.main';
      default:
        return 'primary.main';
    }
  };

  return (
    <Card sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      borderLeft: 4,
      borderColor: getSeverityColor(severity),
      transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: 4,
      }
    }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary">
            {title}
          </Typography>
          {icon && <Box sx={{ color: 'text.secondary' }}>{icon}</Box>}
        </Box>
        
        {loading ? (
          <Skeleton variant="rectangular" height={60} />
        ) : (
          <Box>
            <Typography variant="h5" component="div" sx={{ fontWeight: 'bold', mb: 1, color: getSeverityColor(severity) }}>
              {status}
            </Typography>
            {description && (
              <Typography variant="body2" color="text.secondary">
                {description}
              </Typography>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default StatusCard;
