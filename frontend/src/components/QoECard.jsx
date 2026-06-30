import React from 'react';
import { Card, CardContent, Typography, Box, Skeleton, CircularProgress } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';

const QoECard = ({ score, category, loading, previousScore }) => {
  let statusColor = 'warning.main';
  if (score >= 85) statusColor = 'success.main';
  else if (score < 65) statusColor = 'error.main';

  let trendDirection = null;
  let trendValueStr = null;
  if (score !== undefined && previousScore !== undefined && previousScore !== null) {
    const diff = score - previousScore;
    if (Math.abs(diff) > 0.1) {
      trendDirection = diff > 0 ? 'up' : 'down';
      trendValueStr = `${diff > 0 ? '+' : ''}${diff.toFixed(1)}`;
    } else {
      trendDirection = 'flat';
      trendValueStr = '0.0';
    }
  }

  const getTrendColor = () => {
    if (!trendDirection || trendDirection === 'flat') return 'text.secondary';
    return trendDirection === 'up' ? 'success.main' : 'error.main';
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
      borderLeft: 6,
      borderColor: 'success.main',
      bgcolor: 'background.paper',
      boxShadow: 3
    }}>
      <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 3 }}>
        <Typography variant="h6" color="text.secondary" gutterBottom sx={{ fontWeight: 'bold' }}>
          Quality of Experience (QoE)
        </Typography>
        
        {loading ? (
          <Skeleton variant="circular" width={120} height={120} sx={{ my: 2 }} />
        ) : (
          <Box sx={{ position: 'relative', display: 'inline-flex', my: 2 }}>
            <CircularProgress 
              variant="determinate" 
              value={score || 0} 
              size={140} 
              thickness={4} 
              sx={{ color: statusColor }}
            />
            <Box sx={{
              top: 0, left: 0, bottom: 0, right: 0,
              position: 'absolute', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column'
            }}>
              <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
                {score ? score.toFixed(1) : '-'}
              </Typography>
            </Box>
          </Box>
        )}

        {!loading && (
          <Box sx={{ textAlign: 'center', mt: 1 }}>
            <Typography variant="h5" sx={{ color: statusColor, fontWeight: 'bold', mb: 1 }}>
              {category || 'Unknown'}
            </Typography>
            {trendDirection && (
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {renderTrendIcon()}
                <Typography variant="body1" sx={{ color: getTrendColor(), fontWeight: 'bold' }}>
                  {trendValueStr}
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default QoECard;
