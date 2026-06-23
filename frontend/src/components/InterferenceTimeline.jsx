import React from 'react';
import { Card, CardContent, Typography, Box, Skeleton } from '@mui/material';
import { motion } from 'framer-motion';
import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';
import WifiTetheringIcon from '@mui/icons-material/WifiTethering';
import WarningIcon from '@mui/icons-material/Warning';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import MoodBadIcon from '@mui/icons-material/MoodBad';
import BuildIcon from '@mui/icons-material/Build';

const TimelineNode = ({ icon, title, deltaValue, currentValue, color, delay }) => (
  <Box 
    component={motion.div}
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', minWidth: '120px' }}
  >
    <Box sx={{ 
      bgcolor: `${color}.main`, 
      color: 'white', 
      p: 2, 
      borderRadius: '50%', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      mb: 1.5,
      boxShadow: 3
    }}>
      {icon}
    </Box>
    <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 'bold' }}>{title}</Typography>
    <Typography variant="h6" sx={{ color: `${color}.main`, fontWeight: 'bold', lineHeight: 1.2 }}>{deltaValue}</Typography>
    {currentValue && (
      <Typography variant="caption" color="text.secondary">Currently: {currentValue}</Typography>
    )}
  </Box>
);

const InterferenceTimeline = ({ latestTelemetry, previousTelemetry, recommendation, loading }) => {
  if (loading) {
    return (
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom color="text.secondary">Causal Chain Analysis</Typography>
          <Skeleton variant="rectangular" height={140} />
        </CardContent>
      </Card>
    );
  }

  const interferenceType = latestTelemetry?.interference_type && latestTelemetry.interference_type !== 'None' 
    ? latestTelemetry.interference_type 
    : 'No Event';
    
  const hasInterference = interferenceType !== 'No Event';
  const recAction = recommendation?.action && recommendation.action !== 'NONE' ? recommendation.action.replace('_', ' ') : 'No Action';

  const calcDelta = (curr, prev, isPct = false, suffix = '') => {
    if (curr === undefined || prev === undefined || curr === null || prev === null) return '-';
    let c = curr;
    let p = prev;
    if (isPct) { c *= 100; p *= 100; }
    const diff = c - p;
    if (Math.abs(diff) < 0.1) return `Flat`;
    const arrow = diff > 0 ? '↑' : '↓';
    return `${arrow} ${Math.abs(diff).toFixed(1)}${suffix}`;
  };

  const noiseColor = (latestTelemetry?.noise_floor || 0) > (previousTelemetry?.noise_floor || 0) ? 'error' : 'success';
  const snrColor = (latestTelemetry?.snr || 0) < (previousTelemetry?.snr || 0) ? 'error' : 'success';
  const retryColor = (latestTelemetry?.retry_rate || 0) > (previousTelemetry?.retry_rate || 0) ? 'error' : 'success';
  const qoeColor = (latestTelemetry?.qoe_score || 0) < (previousTelemetry?.qoe_score || 0) ? 'error' : 'success';

  return (
    <Card sx={{ 
      mb: 4, 
      bgcolor: hasInterference ? 'rgba(211, 47, 47, 0.03)' : 'background.paper',
      borderLeft: 6,
      borderColor: hasInterference ? 'error.main' : 'primary.main',
      boxShadow: 2
    }}>
      <CardContent>
        <Typography variant="h6" gutterBottom color="text.secondary" sx={{ fontWeight: 'bold' }}>
          Causal Chain Analysis
        </Typography>
        
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          mt: 4, 
          mb: 2,
          flexWrap: { xs: 'wrap', md: 'nowrap' }, 
          gap: { xs: 2, md: 0 },
          overflowX: 'auto'
        }}>
          
          <TimelineNode icon={<WifiTetheringIcon />} title="Interference" deltaValue={interferenceType} color={hasInterference ? 'error' : 'primary'} delay={0.1} />
          <Box component={motion.div} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}><ArrowRightAltIcon color="action" fontSize="large" /></Box>
          
          <TimelineNode icon={<WarningIcon />} title="Noise Floor" deltaValue={calcDelta(latestTelemetry?.noise_floor, previousTelemetry?.noise_floor, false, ' dBm')} currentValue={`${latestTelemetry?.noise_floor ?? '-'} dBm`} color={noiseColor} delay={0.3} />
          <Box component={motion.div} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}><ArrowRightAltIcon color="action" fontSize="large" /></Box>

          <TimelineNode icon={<ReportProblemIcon />} title="SNR" deltaValue={calcDelta(latestTelemetry?.snr, previousTelemetry?.snr, false, ' dB')} currentValue={`${latestTelemetry?.snr ?? '-'} dB`} color={snrColor} delay={0.5} />
          <Box component={motion.div} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}><ArrowRightAltIcon color="action" fontSize="large" /></Box>

          <TimelineNode icon={<WarningIcon />} title="Retry Rate" deltaValue={calcDelta(latestTelemetry?.retry_rate, previousTelemetry?.retry_rate, true, '%')} currentValue={`${latestTelemetry ? (latestTelemetry.retry_rate * 100).toFixed(1) : '-'}%`} color={retryColor} delay={0.7} />
          <Box component={motion.div} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}><ArrowRightAltIcon color="action" fontSize="large" /></Box>

          <TimelineNode icon={<MoodBadIcon />} title="QoE Score" deltaValue={calcDelta(latestTelemetry?.qoe_score, previousTelemetry?.qoe_score)} currentValue={latestTelemetry?.qoe_score?.toFixed(1) ?? '-'} color={qoeColor} delay={0.9} />
          <Box component={motion.div} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.0 }}><ArrowRightAltIcon color="action" fontSize="large" /></Box>

          <TimelineNode icon={<BuildIcon />} title="Recommendation" deltaValue={recAction} color="primary" delay={1.1} />

        </Box>
      </CardContent>
    </Card>
  );
};

export default InterferenceTimeline;
