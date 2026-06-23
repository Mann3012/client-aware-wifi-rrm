import React from 'react';
import { Card, CardContent, Typography, Box, Skeleton, Chip } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';

const MetricCard = ({ title, value, unit, status, description, loading, trendValue, trendDirection, trendGoodDirection }) => {
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'good':
      case 'excellent':
      case 'healthy':
        return 'success.main';
      case 'fair':
      case 'warning':
        return 'warning.main';
      case 'poor':
      case 'bad':
      case 'critical':
        return 'error.main';
      default:
        return 'text.secondary';
    }
  };

  const getTrendColor = () => {
    if (!trendDirection || trendDirection === 'flat' || !trendGoodDirection) return 'text.secondary';
    return trendDirection === trendGoodDirection ? 'success.main' : 'error.main';
  };

  const renderTrendIcon = () => {
    if (trendDirection === 'up') return <TrendingUpIcon fontSize="small" sx={{ color: getTrendColor(), mr: 0.5 }} />;
    if (trendDirection === 'down') return <TrendingDownIcon fontSize="small" sx={{ color: getTrendColor(), mr: 0.5 }} />;
    return <TrendingFlatIcon fontSize="small" sx={{ color: 'text.secondary', mr: 0.5 }} />;
  };

  return (
    <Card sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: 4,
      }
    }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        
        {loading ? (
          <Skeleton variant="rectangular" height={60} />
        ) : (
          <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 1 }}>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
              {value}
            </Typography>
            {unit && (
              <Typography variant="subtitle1" color="text.secondary" sx={{ ml: 1 }}>
                {unit}
              </Typography>
            )}
          </Box>
        )}

        {!loading && (
          <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1, mt: 1 }}>
            {trendDirection && (
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {renderTrendIcon()}
                <Typography variant="body2" sx={{ color: getTrendColor(), fontWeight: 'bold' }}>
                  {trendValue}
                </Typography>
              </Box>
            )}
            
            {status && (
              <Chip 
                label={status} 
                size="small" 
                sx={{ 
                  bgcolor: getStatusColor(status), 
                  color: 'white',
                  fontWeight: 'bold',
                  ml: trendDirection ? 1 : 0
                }} 
              />
            )}
            {description && (
              <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                {description}
              </Typography>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default MetricCard;
