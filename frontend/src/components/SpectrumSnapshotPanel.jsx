import React from 'react';
import { Card, CardContent, Typography, Box, Grid, Chip, Skeleton } from '@mui/material';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import { parseSpectrumSnapshot } from '../utils/causalChain';

const SpectrumSnapshotPanel = ({ telemetry, loading }) => {
  const spectrum = parseSpectrumSnapshot(telemetry?.spectrum_snapshot);

  if (loading) {
    return (
      <Card sx={{ mb: 3, boxShadow: 2 }}>
        <CardContent>
          <Skeleton height={100} />
        </CardContent>
      </Card>
    );
  }

  if (!spectrum) {
    return (
      <Card sx={{ mb: 3, boxShadow: 2, borderLeft: 4, borderColor: 'divider' }}>
        <CardContent>
          <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 700 }}>
            Sensing Radio — Spectrum Snapshot
          </Typography>
          <Typography variant="body2" color="text.disabled" sx={{ mt: 1 }}>
            No spectrum data yet. Trigger a simulation step to populate sensing radio measurements.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const spec = spectrum.spectrum || {};
  const interferers = spectrum.detected_interferers || [];
  const quality = spectrum.channel_quality_score;

  return (
    <Card sx={{ mb: 3, boxShadow: 3, borderLeft: 4, borderColor: quality < 50 ? 'error.main' : quality < 75 ? 'warning.main' : 'success.main' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <GraphicEqIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 700 }} color="text.secondary">
            Sensing Radio — Spectrum Snapshot
          </Typography>
          <Chip
            size="small"
            label={`Ch ${spec.channel ?? '—'}`}
            variant="outlined"
            sx={{ ml: 'auto', fontFamily: 'monospace' }}
          />
        </Box>

        <Grid container spacing={2} sx={{ mb: interferers.length ? 2 : 0 }}>
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="text.secondary">Channel Quality</Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, color: quality >= 75 ? 'success.main' : quality >= 50 ? 'warning.main' : 'error.main' }}>
              {quality != null ? `${quality}/100` : '—'}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="text.secondary">Noise Floor</Typography>
            <Typography variant="h6" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
              {spec.noise_floor_dbm != null ? `${spec.noise_floor_dbm} dBm` : '—'}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="text.secondary">Peak Power</Typography>
            <Typography variant="h6" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
              {spec.peak_power_dbm != null ? `${spec.peak_power_dbm} dBm` : '—'}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="text.secondary">Channel Busy</Typography>
            <Typography variant="h6" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
              {spec.channel_busy_fraction != null ? `${(spec.channel_busy_fraction * 100).toFixed(1)}%` : '—'}
            </Typography>
          </Grid>
        </Grid>

        {interferers.length > 0 && (
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Detected Interferers
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5 }}>
              {interferers.map((inf, i) => (
                <Chip
                  key={i}
                  size="small"
                  label={`${inf.classification} @ ${inf.center_freq_mhz} MHz (${inf.power_dbm} dBm)`}
                  color={inf.classification === 'wifi' ? 'default' : 'warning'}
                  variant="outlined"
                  sx={{ fontSize: '0.72rem' }}
                />
              ))}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default SpectrumSnapshotPanel;
