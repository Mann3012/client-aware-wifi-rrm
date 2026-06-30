import React, { memo, useMemo } from 'react';
import { Card, CardContent, Typography, Box, Skeleton, Grid } from '@mui/material';
import {
  ResponsiveContainer, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ReferenceArea
} from 'recharts';

/* ─────────────────── Helpers ─────────────────── */

const formatTick = (ts) => {
  if (!ts) return '';
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <Box sx={{
      p: 1.5,
      bgcolor: '#1e2235',
      border: '1px solid #3a3f5c',
      borderRadius: 1,
      boxShadow: 6,
      minWidth: 160,
    }}>
      <Typography variant="caption" sx={{ color: '#94a3b8', display: 'block', mb: 0.5 }}>
        {new Date(label).toLocaleTimeString()}
      </Typography>
      {payload.map((entry, i) => (
        <Typography key={i} variant="body2" sx={{ color: entry.color, fontWeight: 700 }}>
          {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : '-'}
        </Typography>
      ))}
    </Box>
  );
};

/* ─────────────────── Single Chart Card ─────────────────── */

const ChartCard = memo(({ title, data, dataKey, name, color, domain, unit, height = 320, loading, children, titleVariant = 'subtitle1' }) => {
  const gradId = `grad_${dataKey}`;
  return (
    <Card sx={{ height: '100%', boxShadow: 3 }}>
      <CardContent sx={{ pb: '12px !important' }}>
        <Typography variant={titleVariant} sx={{ fontWeight: 700, mb: 1.5 }} color="text.secondary">
          {title}
        </Typography>
        {loading ? (
          <Skeleton variant="rectangular" height={height} sx={{ borderRadius: 1 }} />
        ) : (
          <Box sx={{ width: '100%', height }}>
            <ResponsiveContainer>
              <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
                <defs>
                  <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={color} stopOpacity={0.35} />
                    <stop offset="95%" stopColor={color} stopOpacity={0}    />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a3047" vertical={false} />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatTick}
                  stroke="#4b5680"
                  tick={{ fontSize: 13, fill: '#94a3b8' }}
                  minTickGap={50}
                  tickLine={false}
                />
                <YAxis
                  domain={domain}
                  stroke="#4b5680"
                  tick={{ fontSize: 13, fill: '#94a3b8' }}
                  width={52}
                  tickLine={false}
                  tickFormatter={(v) => `${v}${unit}`}
                />
                <Tooltip content={<CustomTooltip />} />
                {children}
                <Area
                  type="monotone"
                  dataKey={dataKey}
                  name={`${name} (${unit})`}
                  stroke={color}
                  fill={`url(#${gradId})`}
                  strokeWidth={3}
                  dot={false}
                  activeDot={{ r: 5, strokeWidth: 0 }}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
});

/* ─────────────────── Main Export ─────────────────── */

const TelemetryCharts = ({ data, loading }) => {
  // Oldest → Newest for charts
  const chartData = useMemo(() => (data ? [...data].reverse() : []), [data]);
  const retryData  = useMemo(() => chartData.map(d => ({ ...d, retry_pct: +(d.retry_rate * 100).toFixed(2) })), [chartData]);

  return (
    <Box>
      {/* Row 1: RSSI + Noise */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="RSSI vs Time"
            data={chartData}
            dataKey="rssi"
            name="RSSI"
            color="#1976d2"
            domain={[-90, -30]}
            unit=" dBm"
            loading={loading}
          >
            <ReferenceLine y={-70} stroke="#1976d2" strokeDasharray="4 4"
              label={{ value: '-70 dBm (Fair)', position: 'insideTopLeft', fill: '#64b5f6', fontSize: 11 }} />
          </ChartCard>
        </Grid>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Noise Floor vs Time"
            data={chartData}
            dataKey="noise_floor"
            name="Noise"
            color="#ed6c02"
            domain={[-105, -65]}
            unit=" dBm"
            loading={loading}
          >
            <ReferenceArea y1={-85} y2={-65} fill="#ed6c02" fillOpacity={0.08} />
            <ReferenceLine y={-85} stroke="#ff9800" strokeDasharray="4 4"
              label={{ value: '-85 dBm (High Noise)', position: 'insideTopLeft', fill: '#ffb74d', fontSize: 11 }} />
          </ChartCard>
        </Grid>
      </Grid>

      {/* Row 2: SNR + Retry Rate */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="SNR vs Time"
            data={chartData}
            dataKey="snr"
            name="SNR"
            color="#2e7d32"
            domain={[0, 50]}
            unit=" dB"
            loading={loading}
          >
            <ReferenceArea y1={0}  y2={20} fill="#d32f2f" fillOpacity={0.07} />
            <ReferenceArea y1={20} y2={25} fill="#fbc02d" fillOpacity={0.07} />
            <ReferenceArea y1={25} y2={50} fill="#2e7d32" fillOpacity={0.07} />
            <ReferenceLine y={20} stroke="#ef5350" strokeDasharray="4 4"
              label={{ value: '20 dB (Min Good)', position: 'insideTopLeft', fill: '#ef9a9a', fontSize: 11 }} />
          </ChartCard>
        </Grid>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Packet Error Rate (PER) vs Time"
            data={retryData}
            dataKey="retry_pct"
            name="Retry"
            color="#c62828"
            domain={[0, 100]}
            unit="%"
            loading={loading}
          >
            <ReferenceArea y1={20} y2={100} fill="#c62828" fillOpacity={0.07} />
            <ReferenceLine y={20} stroke="#ef5350" strokeDasharray="4 4"
              label={{ value: '20% (High Retries)', position: 'insideTopLeft', fill: '#ef9a9a', fontSize: 11 }} />
          </ChartCard>
        </Grid>
      </Grid>

      {/* Row 3: QoE — full width, taller, dominant */}
      <Grid container>
        <Grid item xs={12}>
          <Card sx={{
            boxShadow: 6,
            borderLeft: 6,
            borderColor: '#9c27b0',
            background: 'linear-gradient(135deg, rgba(156,39,176,0.06) 0%, transparent 60%)',
          }}>
            <CardContent sx={{ pb: '12px !important' }}>
              <Typography variant="h5" sx={{ fontWeight: 800, mb: 2 }} color="#ce93d8">
                Quality of Experience (QoE) — Live Trend
              </Typography>
              {loading ? (
                <Skeleton variant="rectangular" height={400} sx={{ borderRadius: 1 }} />
              ) : (
                <Box sx={{ width: '100%', height: 400 }}>
                  <ResponsiveContainer>
                    <AreaChart data={chartData} margin={{ top: 10, right: 24, left: 0, bottom: 4 }}>
                      <defs>
                        <linearGradient id="gradQoE" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%"  stopColor="#9c27b0" stopOpacity={0.45} />
                          <stop offset="95%" stopColor="#9c27b0" stopOpacity={0}    />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2a3047" vertical={false} />
                      <XAxis
                        dataKey="timestamp"
                        tickFormatter={formatTick}
                        stroke="#4b5680"
                        tick={{ fontSize: 13, fill: '#94a3b8' }}
                        minTickGap={60}
                        tickLine={false}
                      />
                      <YAxis
                        domain={[0, 100]}
                        stroke="#4b5680"
                        tick={{ fontSize: 14, fill: '#94a3b8' }}
                        width={44}
                        tickLine={false}
                        ticks={[0, 25, 50, 65, 85, 100]}
                      />
                      <Tooltip content={<CustomTooltip />} />

                      <ReferenceArea y1={0} y2={40} fill="#c62828" fillOpacity={0.08} />
                      <ReferenceArea y1={40} y2={65} fill="#f57f17" fillOpacity={0.08} />
                      <ReferenceArea y1={65} y2={85} fill="#f9a825" fillOpacity={0.06} />
                      <ReferenceArea y1={85} y2={100} fill="#2e7d32" fillOpacity={0.08} />

                      <ReferenceLine y={65} stroke="#f57f17" strokeDasharray="4 4"
                        label={{ value: 'Good threshold (65)', position: 'insideTopRight', fill: '#ffcc02', fontSize: 12 }} />
                      <ReferenceLine y={85} stroke="#66bb6a" strokeDasharray="4 4"
                        label={{ value: 'Excellent threshold (85)', position: 'insideTopRight', fill: '#a5d6a7', fontSize: 12 }} />

                      <Area
                        type="monotone"
                        dataKey="qoe_score"
                        name="QoE (Score)"
                        stroke="#ce93d8"
                        fill="url(#gradQoE)"
                        strokeWidth={4}
                        dot={false}
                        activeDot={{ r: 7, strokeWidth: 0 }}
                        isAnimationActive={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default memo(TelemetryCharts);
