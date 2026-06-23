import React from 'react';
import { Card, CardContent, Typography, Box, Skeleton, Chip, Grid } from '@mui/material';
import BuildIcon from '@mui/icons-material/Build';

const RecommendationCard = ({ recommendation, loading }) => {
  const hasRec = recommendation && recommendation.action && recommendation.action !== 'NONE';
  const actionTitle = hasRec ? recommendation.action.replace('_', ' ') : 'SYSTEM OPTIMAL';
  const severityColor = hasRec ? 'warning.main' : 'success.main';

  // Map backend actions to expected business benefits
  const getExpectedBenefit = (action) => {
    switch(action) {
      case 'CHANNEL_CHANGE': return 'Higher SNR, Lower Co-Channel Interference';
      case 'POWER_INCREASE': return 'Improved Coverage, Higher RSSI';
      case 'POWER_DECREASE': return 'Reduced Cell Overlap, Lower Noise Floor';
      case 'WIDTH_DECREASE': return 'Higher SNR Margin, Improved Stability';
      default: return 'Maintained High QoE';
    }
  };

  return (
    <Card sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      borderLeft: 6,
      borderColor: severityColor,
      bgcolor: 'background.paper',
      boxShadow: 3
    }}>
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 'bold' }}>Active Recommendation</Typography>
          <BuildIcon sx={{ color: severityColor, fontSize: 28 }} />
        </Box>
        
        {loading ? (
          <Skeleton variant="rectangular" height={120} />
        ) : (
          <Box>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', mb: 3, color: severityColor }}>
              {actionTitle}
            </Typography>
            
            {hasRec ? (
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Reason</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>{recommendation.reason}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Expected Outcome</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>{getExpectedBenefit(recommendation.action)}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>Confidence</Typography>
                    <Chip size="medium" label={`${(recommendation.confidence * 100).toFixed(0)}%`} color="primary" sx={{ fontWeight: 'bold' }} />
                  </Box>
                </Grid>
              </Grid>
            ) : (
              <Box sx={{ display: 'flex', alignItems: 'center', height: '100px' }}>
                <Typography variant="body1" color="text.secondary" sx={{ fontSize: '1.1rem' }}>
                  No active RRM actions required. The system is operating normally.
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default RecommendationCard;
