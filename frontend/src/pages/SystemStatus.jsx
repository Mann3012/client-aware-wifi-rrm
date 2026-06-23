import React, { useMemo } from 'react';
import {
  Box, Typography, Card, CardContent, Grid,
  Chip, Table, TableBody, TableCell, TableHead,
  TableRow, Skeleton, Divider, Avatar, Paper
} from '@mui/material';
import CheckCircleIcon    from '@mui/icons-material/CheckCircle';
import ErrorIcon          from '@mui/icons-material/Error';
import WifiIcon           from '@mui/icons-material/Wifi';
import PeopleIcon         from '@mui/icons-material/People';
import StarIcon           from '@mui/icons-material/Star';
import WarningAmberIcon   from '@mui/icons-material/WarningAmber';
import WifiTetheringIcon  from '@mui/icons-material/WifiTethering';
import BuildIcon          from '@mui/icons-material/Build';

import { useHealthStatus }     from '../hooks/useHealthStatus';
import { useTelemetry }        from '../hooks/useTelemetry';
import { useAlerts }           from '../hooks/useAlerts';
import { useRecommendations }  from '../hooks/useRecommendations';
import { USE_MOCK_DATA }       from '../config';

/* ────────────────────── helpers ────────────────────── */

const fmt = (ts) => ts ? new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—';

const HealthChip = ({ status }) => {
  const map = {
    Healthy:  'success',
    Warning:  'warning',
    Critical: 'error',
    Degraded: 'error',
  };
  return (
    <Chip
      size="small"
      label={status ?? 'Unknown'}
      color={map[status] ?? 'default'}
      sx={{ fontWeight: 700, minWidth: 72 }}
    />
  );
};

const SummaryTile = ({ icon, label, value, accent, loading }) => (
  <Card sx={{ height: '100%', boxShadow: 2, borderTop: 3, borderColor: accent }}>
    <CardContent sx={{ pb: '12px !important' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Avatar sx={{ bgcolor: accent, width: 32, height: 32 }}>{icon}</Avatar>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
          {label}
        </Typography>
      </Box>
      {loading
        ? <Skeleton width="60%" height={44} />
        : <Typography variant="h3" sx={{ fontWeight: 800 }}>{value ?? '—'}</Typography>
      }
    </CardContent>
  </Card>
);

const ConnDot = ({ ok, label }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
    {ok
      ? <CheckCircleIcon sx={{ fontSize: 13, color: 'success.main' }} />
      : <ErrorIcon        sx={{ fontSize: 13, color: 'error.main'   }} />
    }
    <Typography variant="caption" color="text.disabled">{label}</Typography>
  </Box>
);

/* ════════════════════════════════════════════════════ */

const SystemStatus = () => {
  /* hooks – all fetching from real FastAPI (/api/…) */
  const healthHook  = useHealthStatus();
  const telHook     = useTelemetry(null);          // all APs
  const alertsHook  = useAlerts(null, false);      // all alerts
  const recsHook    = useRecommendations(null);    // all recs

  const { data: healthData,   loading: hLoad,  error: hErr  } = healthHook;
  const { data: telemetryAll, loading: tLoad,  error: tErr  } = telHook;
  const { data: alertsAll,    loading: aLoad,  error: aErr  } = alertsHook;
  const { data: recsAll,      loading: rLoad,  error: rErr  } = recsHook;

  /* ── fleet-wide derived metrics ── */
  const totalAPs     = healthData?.length ?? 0;
  const totalClients = useMemo(
    () => healthData?.reduce((s, ap) => s + (ap.client_count ?? 0), 0) ?? 0,
    [healthData]
  );
  const avgQoE = useMemo(() => {
    const vals = (telemetryAll ?? []).map(t => t.qoe_score).filter(v => v != null);
    return vals.length ? (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : null;
  }, [telemetryAll]);
  const activeAlerts = alertsAll?.length ?? 0;
  const interferenceAPs = useMemo(
    () => (telemetryAll ?? []).filter(t => t.interference_type && t.interference_type !== 'None').length,
    [telemetryAll]
  );
  const activeRecs = recsAll?.length ?? 0;

  /* ── recent slices ── */
  const recentAlerts = (alertsAll ?? []).slice(0, 10);
  const recentRecs   = (recsAll   ?? []).slice(0, 10);

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
        Network Operations Center — Status
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Live operational summary across all managed Access Points · auto-refreshes every 5 s
      </Typography>

      {USE_MOCK_DATA && (
        <Card sx={{ mb: 3, borderLeft: 5, borderColor: 'warning.main' }}>
          <CardContent>
            <Typography color="warning.main" sx={{ fontWeight: 700 }}>
              ⚠ Mock Data Active — set VITE_USE_MOCK_DATA=false to connect to FastAPI
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* ════ A: Fleet Summary Tiles ════ */}
      <Typography variant="h6" color="text.secondary" sx={{ mb: 1.5, fontWeight: 700 }}>
        A · Fleet Summary
      </Typography>
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={6} sm={4} md={2}>
          <SummaryTile icon={<WifiIcon />}          label="Total APs"          value={totalAPs}          accent="#1565c0" loading={hLoad} />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <SummaryTile icon={<PeopleIcon />}        label="Total Clients"      value={totalClients}      accent="#2e7d32" loading={hLoad} />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <SummaryTile icon={<StarIcon />}          label="Average QoE"        value={avgQoE}            accent="#6a1b9a" loading={tLoad} />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <SummaryTile icon={<WarningAmberIcon />}  label="Active Alerts"      value={activeAlerts}      accent={activeAlerts > 0 ? '#c62828' : '#2e7d32'} loading={aLoad} />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <SummaryTile icon={<WifiTetheringIcon />} label="Interference APs"   value={interferenceAPs}   accent={interferenceAPs > 0 ? '#e65100' : '#2e7d32'} loading={tLoad} />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <SummaryTile icon={<BuildIcon />}         label="Active Recs"        value={activeRecs}        accent="#0277bd" loading={rLoad} />
        </Grid>
      </Grid>

      {/* ════ B: AP Inventory ════ */}
      <Typography variant="h6" color="text.secondary" sx={{ mb: 1.5, fontWeight: 700 }}>
        B · Access Point Inventory
      </Typography>
      <Card sx={{ boxShadow: 3, mb: 4 }}>
        <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
          {hLoad ? (
            <Box sx={{ p: 2 }}><Skeleton height={200} /></Box>
          ) : !healthData?.length ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">No AP data — is the backend running?</Typography>
            </Box>
          ) : (
            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'background.default' }}>
                    {['AP ID', 'Health', 'Channel', 'Clients', 'Alerts', 'Last Recommendation'].map(h => (
                      <TableCell key={h} sx={{ fontWeight: 700, color: 'text.secondary', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>
                        {h}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {healthData.map((ap) => (
                    <TableRow key={ap.ap_id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
                          {ap.ap_id}
                        </Typography>
                      </TableCell>
                      <TableCell><HealthChip status={ap.status} /></TableCell>
                      <TableCell>
                        <Chip label={`Ch ${ap.channel ?? '—'}`} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>{ap.client_count ?? 0}</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={ap.active_alert_count ?? 0}
                          color={(ap.active_alert_count ?? 0) > 0 ? 'error' : 'default'}
                          sx={{ fontWeight: 700, minWidth: 32 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {ap.recent_recommendation ?? 'None'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}
        </CardContent>
      </Card>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* ════ C: Active Alerts Table ════ */}
        <Grid item xs={12} lg={6}>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 1.5, fontWeight: 700 }}>
            C · Active Alerts
          </Typography>
          <Card sx={{ boxShadow: 3, height: '100%' }}>
            <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
              {aLoad ? (
                <Box sx={{ p: 2 }}><Skeleton height={200} /></Box>
              ) : !recentAlerts.length ? (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <CheckCircleIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                  <Typography color="text.secondary">No active alerts — system healthy</Typography>
                </Box>
              ) : (
                <Box sx={{ overflowX: 'auto' }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'background.default' }}>
                        {['Time', 'AP', 'Metric', 'Value', 'Description'].map(h => (
                          <TableCell key={h} sx={{ fontWeight: 700, color: 'text.secondary', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>
                            {h}
                          </TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recentAlerts.map((alert, i) => (
                        <TableRow key={alert.id ?? i} hover>
                          <TableCell>
                            <Typography variant="caption" sx={{ fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                              {fmt(alert.timestamp)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
                              {alert.ap_id ?? '—'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={alert.metric ?? alert.alert_type ?? '—'} size="small" color="warning" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 700, color: 'error.main' }}>
                              {typeof alert.value === 'number' ? alert.value.toFixed(2) : (alert.value ?? '—')}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption" color="text.secondary" sx={{ maxWidth: 200, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {alert.description ?? '—'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* ════ D: Recent Recommendations Table ════ */}
        <Grid item xs={12} lg={6}>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 1.5, fontWeight: 700 }}>
            D · Recent Recommendations
          </Typography>
          <Card sx={{ boxShadow: 3, height: '100%' }}>
            <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
              {rLoad ? (
                <Box sx={{ p: 2 }}><Skeleton height={200} /></Box>
              ) : !recentRecs.length ? (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <CheckCircleIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                  <Typography color="text.secondary">No recommendations — system optimal</Typography>
                </Box>
              ) : (
                <Box sx={{ overflowX: 'auto' }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'background.default' }}>
                        {['Time', 'AP', 'Action', 'Confidence', 'Reason'].map(h => (
                          <TableCell key={h} sx={{ fontWeight: 700, color: 'text.secondary', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>
                            {h}
                          </TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recentRecs.map((rec, i) => (
                        <TableRow key={rec.id ?? i} hover>
                          <TableCell>
                            <Typography variant="caption" sx={{ fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                              {fmt(rec.timestamp)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
                              {rec.ap_id ?? '—'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={rec.action ?? '—'}
                              size="small"
                              color="warning"
                              sx={{ fontWeight: 700, fontFamily: 'monospace', fontSize: '0.68rem' }}
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={`${((rec.confidence ?? 0) * 100).toFixed(0)}%`}
                              size="small"
                              color="primary"
                              sx={{ fontWeight: 700 }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption" color="text.secondary" sx={{ maxWidth: 220, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {rec.reason ?? '—'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* ════ E: Connectivity Footer ════ */}
      <Box sx={{ pt: 2, borderTop: '1px solid', borderColor: 'divider', display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <Typography variant="caption" color="text.disabled" sx={{ mr: 1, fontWeight: 600 }}>
          API Connectivity:
        </Typography>
        <ConnDot ok={!hErr}  label={`AP Status (${healthHook.recordCount} APs, ${healthHook.lastFetch ? fmt(healthHook.lastFetch) : '…'})`} />
        <ConnDot ok={!tErr}  label={`Telemetry (${telHook.recordCount} records, ${telHook.lastFetch ? fmt(telHook.lastFetch) : '…'})`} />
        <ConnDot ok={!aErr}  label={`Alerts (${alertsHook.recordCount} records, ${alertsHook.lastFetch ? fmt(alertsHook.lastFetch) : '…'})`} />
        <ConnDot ok={!rErr}  label={`Recommendations (${recsHook.recordCount} records, ${recsHook.lastFetch ? fmt(recsHook.lastFetch) : '…'})`} />
      </Box>
    </Box>
  );
};

export default SystemStatus;
