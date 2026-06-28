import React, { useState, useMemo } from 'react';
import { Box, Typography, Grid, Button } from '@mui/material';
import WifiTetheringIcon from '@mui/icons-material/WifiTethering';
import AccountTreeIcon from '@mui/icons-material/AccountTree';

import { useTelemetry }      from '../hooks/useTelemetry';
import { useAlerts }         from '../hooks/useAlerts';
import { useRecommendations } from '../hooks/useRecommendations';
import { useHealthStatus }   from '../hooks/useHealthStatus';

import DashboardToolbar          from '../components/DashboardToolbar';
import QoECard                   from '../components/QoECard';
import RecommendationCard        from '../components/RecommendationCard';
import AlertCard                 from '../components/AlertCard';
import StatusCard                from '../components/StatusCard';
import TelemetryCharts           from '../components/TelemetryCharts';
import InterferenceTimeline      from '../components/InterferenceTimeline';
import ApiDebugPanel             from '../components/ApiDebugPanel';
import CausalMetricChainModal    from '../components/CausalMetricChainModal';

const Overview = () => {
  /* ── fleet health (AP list + selector seed) ── */
  const healthHook = useHealthStatus();
  const { data: healthData, loading: healthLoading, error: healthError } = healthHook;

  const [selectedAp, setSelectedAp] = useState('');
  const [causalOpen, setCausalOpen]   = useState(false);
  React.useEffect(() => {
    if (healthData?.length && !selectedAp) setSelectedAp(healthData[0].ap_id);
  }, [healthData, selectedAp]);

  /* ── per-AP feeds ── */
  const telemetryHook = useTelemetry(selectedAp);
  const alertsHook    = useAlerts(selectedAp, true);
  const recsHook      = useRecommendations(selectedAp);

  const { data: telemetryData, loading: telemetryLoading } = telemetryHook;
  const { data: alertsData,    loading: alertsLoading    } = alertsHook;
  const { data: recsData,      loading: recsLoading      } = recsHook;

  const anyError = healthError || telemetryHook.error || alertsHook.error || recsHook.error;

  /* ── derived ── */
  const latestTelemetry  = telemetryData?.[0]  ?? null;
  const previousTelemetry = telemetryData?.[1] ?? null;
  const latestRec        = recsData?.[0]       ?? null;

  return (
    <Box>
      {/* ── Toolbar: AP selector + status ── */}
      <DashboardToolbar
        healthData={healthData}
        selectedAp={selectedAp}
        setSelectedAp={setSelectedAp}
        anyError={anyError}
        lastUpdate={latestTelemetry?.timestamp}
      />

      {/* ── Row 1: Executive KPIs ── */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* QoE — widest card, visual centrepiece */}
        <Grid item xs={12} md={3}>
          <QoECard
            score={latestTelemetry?.qoe_score}
            category={latestTelemetry?.qoe_category}
            loading={telemetryLoading}
            previousScore={previousTelemetry?.qoe_score}
          />
        </Grid>

        {/* Recommendation hero */}
        <Grid item xs={12} md={5}>
          <RecommendationCard recommendation={latestRec} loading={recsLoading} />
        </Grid>

        {/* Interference */}
        <Grid item xs={12} md={2}>
          <StatusCard
            title="Active Interference"
            status={latestTelemetry?.interference_type || 'None'}
            description="PHY Layer Impact"
            severity={
              latestTelemetry?.interference_type &&
              latestTelemetry.interference_type !== 'None'
                ? 'error'
                : 'good'
            }
            icon={<WifiTetheringIcon />}
            loading={telemetryLoading}
          />
        </Grid>

        {/* Alerts */}
        <Grid item xs={12} md={2}>
          <AlertCard count={alertsData?.length ?? 0} loading={alertsLoading} />
        </Grid>
      </Grid>

      {/* ── Causal Chain header + Explain button ── */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
          Causal Chain Analysis
        </Typography>
        <Button
          id="explain-causal-chain-btn"
          variant="contained"
          size="small"
          startIcon={<AccountTreeIcon />}
          onClick={() => setCausalOpen(true)}
          disabled={!latestTelemetry}
          sx={{
            background: 'linear-gradient(135deg, #1976d2 0%, #3b82f6 100%)',
            textTransform: 'none',
            fontWeight: 700,
            fontSize: '0.82rem',
            boxShadow: '0 2px 8px rgba(59,130,246,0.4)',
            '&:hover': {
              background: 'linear-gradient(135deg, #1565c0 0%, #2563eb 100%)',
              boxShadow: '0 4px 16px rgba(59,130,246,0.5)',
            }
          }}
        >
          Explain Causal Metric Chain
        </Button>
      </Box>

      <InterferenceTimeline
        latestTelemetry={latestTelemetry}
        previousTelemetry={previousTelemetry}
        recommendation={latestRec}
        loading={telemetryLoading}
      />

      {/* ── Causal Metric Chain Modal ── */}
      <CausalMetricChainModal
        open={causalOpen}
        onClose={() => setCausalOpen(false)}
        telemetry={latestTelemetry}
        recommendation={latestRec}
        apId={selectedAp}
      />

      {/* ── Real-time Charts ── */}
      <Box sx={{ mb: 3 }}>
        <TelemetryCharts data={telemetryData} loading={telemetryLoading} />
      </Box>

      {/* ── Live Data Verification Panel (collapsible) ── */}
      <ApiDebugPanel feeds={[
        { endpoint: healthHook.endpoint,    recordCount: healthHook.recordCount,    lastFetch: healthHook.lastFetch,    error: healthHook.error },
        { endpoint: telemetryHook.endpoint, recordCount: telemetryHook.recordCount, lastFetch: telemetryHook.lastFetch, error: telemetryHook.error },
        { endpoint: alertsHook.endpoint,    recordCount: alertsHook.recordCount,    lastFetch: alertsHook.lastFetch,    error: alertsHook.error },
        { endpoint: recsHook.endpoint,      recordCount: recsHook.recordCount,      lastFetch: recsHook.lastFetch,      error: recsHook.error },
      ]} />
    </Box>
  );
};

export default Overview;
