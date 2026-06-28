import React, { useState, useCallback } from 'react';
import {
  Dialog, DialogTitle, DialogContent, IconButton,
  Box, Typography, Divider, Chip, Button, Tooltip,
  LinearProgress, Collapse, Paper
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

/* ─────────────────── colour helpers ─────────────────── */

/** Returns { color, bg, label } for a numeric value against thresholds. */
const severity = (value, { goodAbove, warnBelow, unit = '' } = {}) => {
  if (value == null) return { color: '#64748B', bg: 'rgba(100,116,139,0.12)', label: 'N/A' };
  if (goodAbove != null) {
    if (value >= goodAbove) return { color: '#22c55e', bg: 'rgba(34,197,94,0.10)', label: 'Healthy' };
    if (value >= warnBelow) return { color: '#f59e0b', bg: 'rgba(245,158,11,0.10)', label: 'Warning' };
    return { color: '#ef4444', bg: 'rgba(239,68,68,0.10)', label: 'Critical' };
  }
  return { color: '#64748B', bg: 'rgba(100,116,139,0.12)', label: '' };
};

const snrQuality = (snr) => {
  if (snr == null) return { label: 'Unknown', color: '#64748B' };
  if (snr > 25) return { label: 'Excellent', color: '#22c55e' };
  if (snr >= 20) return { label: 'Good', color: '#22c55e' };
  if (snr >= 10) return { label: 'Moderate', color: '#f59e0b' };
  return { label: 'Poor', color: '#ef4444' };
};

/* ─────────────────── sub-components ─────────────────── */

const SectionHeader = ({ step, icon, title, accent }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
    <Box sx={{
      bgcolor: accent, color: '#fff', borderRadius: '50%',
      width: 32, height: 32, display: 'flex', alignItems: 'center',
      justifyContent: 'center', fontSize: '0.85rem', fontWeight: 800,
      flexShrink: 0
    }}>
      {step}
    </Box>
    <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.98rem', color: accent }}>
      {icon} {title}
    </Typography>
  </Box>
);

const MetricRow = ({ label, value, unit = '', color, note }) => (
  <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', py: 0.6, gap: 2 }}>
    <Typography variant="body2" color="text.secondary" sx={{ flexShrink: 0, minWidth: 180 }}>
      {label}
    </Typography>
    <Box sx={{ textAlign: 'right' }}>
      <Typography variant="body2" sx={{ fontWeight: 700, color: color ?? 'text.primary', fontFamily: 'monospace' }}>
        {value != null ? `${value}${unit}` : '—'}
      </Typography>
      {note && (
        <Typography variant="caption" sx={{ color: color ?? 'text.secondary', display: 'block' }}>
          {note}
        </Typography>
      )}
    </Box>
  </Box>
);

const StatusBadge = ({ label, color }) => (
  <Chip
    label={label}
    size="small"
    sx={{
      fontWeight: 700, fontSize: '0.75rem',
      bgcolor: `${color}22`, color,
      border: `1px solid ${color}55`
    }}
  />
);

const ArrowDivider = ({ label }) => (
  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', my: 1.5, gap: 0.5 }}>
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Box sx={{ width: 60, height: 1, bgcolor: 'divider' }} />
      <Typography variant="caption" color="text.disabled" sx={{ fontWeight: 600, whiteSpace: 'nowrap', fontSize: '0.7rem' }}>
        ↓  {label}  ↓
      </Typography>
      <Box sx={{ width: 60, height: 1, bgcolor: 'divider' }} />
    </Box>
  </Box>
);

const Section = ({ children, accent = '#334155' }) => (
  <Paper elevation={0} sx={{
    border: `1px solid ${accent}44`,
    borderLeft: `4px solid ${accent}`,
    borderRadius: 2,
    p: 2,
    mb: 0.5,
    bgcolor: 'background.default'
  }}>
    {children}
  </Paper>
);

const ImpactBar = ({ label, before, after, unit = '', color }) => {
  const delta = after != null && before != null ? (after - before) : null;
  const pct = before !== 0 && delta != null ? Math.min(100, Math.abs(delta / Math.abs(before)) * 100) : 0;
  return (
    <Box sx={{ mb: 1.5 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Typography variant="caption" color="text.disabled">{before?.toFixed(1)}{unit}</Typography>
          <Typography variant="caption" sx={{ color }}>→</Typography>
          <Typography variant="body2" sx={{ fontWeight: 700, color, fontFamily: 'monospace' }}>
            {after?.toFixed(1)}{unit}
          </Typography>
          {delta != null && (
            <Typography variant="caption" sx={{ color, fontWeight: 600 }}>
              ({delta > 0 ? '+' : ''}{delta.toFixed(1)}{unit})
            </Typography>
          )}
        </Box>
      </Box>
      <LinearProgress
        variant="determinate"
        value={pct}
        sx={{
          height: 5, borderRadius: 4,
          bgcolor: 'rgba(255,255,255,0.06)',
          '& .MuiLinearProgress-bar': { bgcolor: color, borderRadius: 4 }
        }}
      />
    </Box>
  );
};

/* ─────────────────── causal engine ─────────────────── */

/**
 * Derives all causal chain data from telemetry + recommendation.
 * Falls back to estimated/derived values where direct fields are absent.
 */
function buildCausalChain(telemetry, recommendation) {
  if (!telemetry) return null;

  const t = telemetry;

  // ── Environment ──
  const distance    = t.distance     ?? t.avg_distance    ?? null;
  const maxDistance = t.max_distance ?? null;
  const wallCount   = t.wall_count   ?? null;
  const wallLoss    = t.wall_loss    ?? (wallCount != null ? wallCount * 3 : null);  // ~3 dB/wall estimate
  const freqMhz     = t.freq_mhz    ?? 5180;   // default 5 GHz
  const txPower     = t.tx_power    ?? 20;      // dBm
  const chanUtil    = t.airtime_utilization ?? t.channel_utilization ?? null;
  const intType     = (t.interference_type && t.interference_type !== 'None') ? t.interference_type : null;
  const clientCount = t.client_count ?? null;

  // ── Propagation ──
  // Free-space path loss: FSPL(dB) = 20log10(d) + 20log10(f_MHz) + 20log10(4π/c) ≈ 20log10(d) + 20log10(f) - 27.55
  const pathLoss = distance != null
    ? parseFloat((20 * Math.log10(Math.max(distance, 1)) + 20 * Math.log10(freqMhz) - 27.55 + (wallLoss ?? 0)).toFixed(1))
    : null;
  const receivedPowerEstimate = pathLoss != null ? parseFloat((txPower - pathLoss).toFixed(1)) : null;

  // ── RF Signal Quality ──
  const rssi       = t.rssi        ?? receivedPowerEstimate ?? null;
  const noiseFloor = t.noise_floor ?? -96;
  const snrActual  = t.snr         ?? (rssi != null ? parseFloat((rssi - noiseFloor).toFixed(1)) : null);

  const snrQ = snrQuality(snrActual);

  // ── Network Impact ──
  const retryRate     = t.retry_rate         ?? null;           // 0–1
  const packetLoss    = t.packet_loss        ?? (retryRate != null ? Math.min(retryRate * 0.7, 1) : null);
  const airtimeUtil   = t.airtime_utilization ?? null;
  // MCS / modulation efficiency: estimate from SNR
  const modulationEff = snrActual != null
    ? (snrActual > 25 ? '256-QAM (MCS 11)' : snrActual > 20 ? '64-QAM (MCS 7)' : snrActual > 15 ? '16-QAM (MCS 4)' : 'BPSK/QPSK (MCS 0–2)')
    : '—';
  // Retry-driven airtime overhead
  const retryOverhead = retryRate != null ? parseFloat((retryRate * 100).toFixed(1)) : null;

  // ── QoE ──
  const qoeScore    = t.qoe_score    ?? null;
  const qoeCategory = t.qoe_category ?? null;
  // Throughput degradation driven by retry + airtime
  const thputDegPct = retryRate != null ? parseFloat((retryRate * 100 * 1.5).toFixed(1)) : null;
  const latencyInc  = retryRate != null ? parseFloat((retryRate * 120).toFixed(0)) : null;   // ms estimate

  // ── Root Cause ──
  const rec = recommendation;
  const rootCause = rec?.root_cause
    ?? deriveRootCause(rssi, snrActual, noiseFloor, retryRate, airtimeUtil, intType, distance);
  const confidence = rec?.confidence ?? 0.80;

  // ── Justification ──
  const action = rec?.action ?? 'NONE';
  const justification = buildJustification(action, rssi, snrActual, noiseFloor, distance, wallCount, retryRate, qoeScore, intType, airtimeUtil, rootCause);

  // ── Predicted Impact ──
  const impact = estimateImpact(action, rssi, snrActual, qoeScore, airtimeUtil, retryRate);

  return {
    env: { distance, maxDistance, wallCount, wallLoss, freqMhz, txPower, chanUtil, intType, clientCount },
    propagation: { pathLoss, receivedPowerEstimate, txPower, freqMhz },
    rf: { rssi, noiseFloor, snrActual, snrQ },
    network: { retryRate, packetLoss, modulationEff, airtimeUtil, retryOverhead },
    qoe: { qoeScore, qoeCategory, thputDegPct, latencyInc },
    rootCause: { cause: rootCause, confidence },
    justification,
    impact,
    action
  };
}

function deriveRootCause(rssi, snr, noiseFloor, retryRate, airtimeUtil, intType, distance) {
  if (intType) return 'Interference Issue';
  if (rssi != null && rssi < -78) return 'Coverage Issue';
  if (snr != null && snr < 10) {
    if (noiseFloor != null && noiseFloor > -85) return 'Interference Issue';
    return 'Coverage Issue';
  }
  if (airtimeUtil != null && airtimeUtil > 0.75) return 'Congestion Issue';
  if (retryRate != null && retryRate > 0.2) return 'Capacity Issue';
  if (distance != null && distance > 25) return 'Obstruction Issue';
  return 'System Optimal';
}

function buildJustification(action, rssi, snr, noiseFloor, distance, walls, retryRate, qoe, intType, airtimeUtil, rootCause) {
  const rssiStr  = rssi != null ? `${rssi.toFixed(1)} dBm` : 'unknown';
  const snrStr   = snr  != null ? `${snr.toFixed(1)} dB`  : 'unknown';
  const retStr   = retryRate != null ? `${(retryRate * 100).toFixed(1)}%` : 'unknown';
  const qoeStr   = qoe  != null ? qoe.toFixed(1) : 'unknown';
  const distStr  = distance  != null ? `${distance.toFixed(0)} m` : 'unknown';
  const wallStr  = walls     != null ? `${walls} wall${walls !== 1 ? 's' : ''}` : 'unknown';
  const noiseStr = noiseFloor != null ? `${noiseFloor.toFixed(1)} dBm` : 'unknown';

  const templates = {
    POWER_INCREASE: `POWER_INCREASE was recommended because RSSI fell to ${rssiStr} due to high path loss caused by ${distStr} of distance and ${wallStr}. Noise floor remained at ${noiseStr}, indicating coverage degradation rather than interference. Low RSSI reduced SNR to ${snrStr}, driving retransmissions up to ${retStr} and degrading QoE to ${qoeStr}/10. Increasing AP transmit power is expected to improve coverage and restore SNR above 20 dB.`,
    POWER_DECREASE: `POWER_DECREASE was recommended because the AP is transmitting at excessive power, causing cell overlap and elevated noise floor (${noiseStr}). Despite RSSI of ${rssiStr}, interference from adjacent APs is elevating the noise floor. Reducing TX power will shrink the cell boundary, lower co-channel interference, and improve SNR to healthy levels.`,
    CHANNEL_CHANGE: `CHANNEL_CHANGE was recommended because ${intType ? `active ${intType} interference` : 'elevated noise floor'} degraded the noise floor to ${noiseStr}, collapsing SNR to ${snrStr}. RSSI (${rssiStr}) indicates adequate signal strength, ruling out a coverage issue. The primary root cause is RF interference driving retransmissions to ${retStr} and QoE down to ${qoeStr}/10. Migrating to a clean channel eliminates the interference source.`,
    WIDTH_DECREASE: `WIDTH_DECREASE was recommended because the current channel width is susceptible to high interference levels (noise floor ${noiseStr}, SNR ${snrStr}). Narrowing channel width reduces the noise bandwidth, improving SNR margin and link stability. Current retry rate of ${retStr} confirms unstable modulation is causing QoE degradation to ${qoeStr}/10.`,
    NONE: `No corrective action is required. RSSI is ${rssiStr}, SNR is ${snrStr}, and QoE is ${qoeStr}/10. All metrics are within acceptable thresholds. The system is operating at nominal performance.`
  };
  return templates[action] ?? `${action} was recommended as the optimal RRM action given current conditions. Root cause identified: ${rootCause}. Current metrics — RSSI: ${rssiStr}, SNR: ${snrStr}, Retry Rate: ${retStr}, QoE: ${qoeStr}/10.`;
}

function estimateImpact(action, rssi, snr, qoe, airtimeUtil, retryRate) {
  const delta = {
    POWER_INCREASE: { rssi: 6, snr: 6, qoe: 1.8, retry: -0.12 },
    POWER_DECREASE: { rssi: -4, snr: 5, qoe: 1.2, retry: -0.10 },
    CHANNEL_CHANGE: { rssi: 1, snr: 10, qoe: 2.2, retry: -0.20 },
    WIDTH_DECREASE: { rssi: 0, snr: 4, qoe: 1.0, retry: -0.08 },
    NONE:           { rssi: 0, snr: 0, qoe: 0, retry: 0 },
  }[action] ?? { rssi: 0, snr: 0, qoe: 0, retry: 0 };

  return {
    rssiAfter:  rssi != null  ? parseFloat((rssi + delta.rssi).toFixed(1)) : null,
    snrAfter:   snr  != null  ? parseFloat((snr  + delta.snr ).toFixed(1)) : null,
    qoeAfter:   qoe  != null  ? Math.min(10, parseFloat((qoe  + delta.qoe ).toFixed(1))) : null,
    retryAfter: retryRate != null ? Math.max(0, parseFloat((retryRate + delta.retry).toFixed(3))) : null,
    rssiBefore: rssi, snrBefore: snr, qoeBefore: qoe, retryBefore: retryRate,
  };
}

/* ─────────────────── plain-text export ─────────────────── */

function buildPlainText(chain, apId) {
  const { env, propagation, rf, network, qoe, rootCause, justification, impact, action } = chain;
  const ts = new Date().toLocaleString();
  const lines = [
    `═══════════════════════════════════════════════════════`,
    `  CAUSAL METRIC CHAIN — ENGINEERING REPORT`,
    `  AP: ${apId ?? 'Unknown'}   Generated: ${ts}`,
    `═══════════════════════════════════════════════════════`,
    ``,
    `[1] ENVIRONMENT FACTORS`,
    `  Client Distance         : ${env.distance?.toFixed(1) ?? '—'} m (max ${env.maxDistance?.toFixed(1) ?? '—'} m)`,
    `  Walls / Obstacles       : ${env.wallCount ?? '—'} walls  (attenuation: ${env.wallLoss?.toFixed(1) ?? '—'} dB)`,
    `  Interference Source     : ${env.intType ?? 'None'}`,
    `  Channel Utilization     : ${env.chanUtil != null ? (env.chanUtil * 100).toFixed(1) + ' %' : '—'}`,
    `  Connected Clients       : ${env.clientCount ?? '—'}`,
    ``,
    `[2] PROPAGATION ANALYSIS`,
    `  Operating Frequency     : ${env.freqMhz} MHz`,
    `  AP TX Power             : ${env.txPower} dBm`,
    `  Estimated Path Loss     : ${propagation.pathLoss?.toFixed(1) ?? '—'} dB`,
    `  Estimated Received Pwr  : ${propagation.receivedPowerEstimate?.toFixed(1) ?? '—'} dBm`,
    ``,
    `[3] RF SIGNAL QUALITY`,
    `  RSSI                    : ${rf.rssi?.toFixed(1) ?? '—'} dBm`,
    `  Noise Floor             : ${rf.noiseFloor?.toFixed(1) ?? '—'} dBm`,
    `  SNR                     : ${rf.snrActual?.toFixed(1) ?? '—'} dB  (${rf.snrQ.label})`,
    `  Formula: SNR = RSSI − Noise Floor = ${rf.rssi?.toFixed(1) ?? '?'} − (${rf.noiseFloor?.toFixed(1) ?? '?'}) = ${rf.snrActual?.toFixed(1) ?? '?'} dB`,
    ``,
    `[4] NETWORK IMPACT`,
    `  Retry Rate              : ${network.retryRate != null ? (network.retryRate * 100).toFixed(1) + ' %' : '—'}`,
    `  Packet Loss (est.)      : ${network.packetLoss != null ? (network.packetLoss * 100).toFixed(1) + ' %' : '—'}`,
    `  Modulation Efficiency   : ${network.modulationEff}`,
    `  Airtime Utilization     : ${network.airtimeUtil != null ? (network.airtimeUtil * 100).toFixed(1) + ' %' : '—'}`,
    ``,
    `[5] USER EXPERIENCE IMPACT`,
    `  Throughput Degradation  : ~${qoe.thputDegPct?.toFixed(1) ?? '—'} %`,
    `  Latency Increase (est.) : ~${qoe.latencyInc?.toFixed(0) ?? '—'} ms`,
    `  QoE Score               : ${qoe.qoeScore?.toFixed(1) ?? '—'} / 10  (${qoe.qoeCategory ?? '—'})`,
    ``,
    `[6] ROOT CAUSE DETECTION`,
    `  Dominant Cause          : ${rootCause.cause}`,
    `  Confidence Score        : ${(rootCause.confidence * 100).toFixed(0)}%`,
    ``,
    `[7] RECOMMENDATION JUSTIFICATION`,
    `  Action: ${action}`,
    ``,
    `  ${justification}`,
    ``,
    `[8] PREDICTED IMPACT (if recommendation applied)`,
    `  RSSI: ${impact.rssiBefore?.toFixed(1) ?? '?'} dBm → ${impact.rssiAfter?.toFixed(1) ?? '?'} dBm (${impact.rssiAfter != null && impact.rssiBefore != null ? (impact.rssiAfter - impact.rssiBefore > 0 ? '+' : '') + (impact.rssiAfter - impact.rssiBefore).toFixed(1) : '?'} dBm)`,
    `  SNR : ${impact.snrBefore?.toFixed(1) ?? '?'} dB  → ${impact.snrAfter?.toFixed(1) ?? '?'} dB  (${impact.snrAfter != null && impact.snrBefore != null ? (impact.snrAfter - impact.snrBefore > 0 ? '+' : '') + (impact.snrAfter - impact.snrBefore).toFixed(1) : '?'} dB)`,
    `  QoE : ${impact.qoeBefore?.toFixed(1) ?? '?'} / 10 → ${impact.qoeAfter?.toFixed(1) ?? '?'} / 10 (${impact.qoeAfter != null && impact.qoeBefore != null ? (impact.qoeAfter - impact.qoeBefore > 0 ? '+' : '') + (impact.qoeAfter - impact.qoeBefore).toFixed(1) : '?'})`,
    ``,
    `═══════════════════════════════════════════════════════`,
    `  End of Report`,
    `═══════════════════════════════════════════════════════`,
  ];
  return lines.join('\n');
}

/* ─────────────────── main modal ─────────────────── */

const SECTION_ACCENTS = {
  env:        '#3b82f6',
  propagation:'#8b5cf6',
  rf:         '#06b6d4',
  network:    '#f59e0b',
  qoe:        '#ec4899',
  rootCause:  '#ef4444',
  rec:        '#22c55e',
  impact:     '#10b981',
};

const CausalMetricChainModal = ({ open, onClose, telemetry, recommendation, apId }) => {
  const [copied, setCopied] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    env: true, propagation: true, rf: true,
    network: true, qoe: true, rootCause: true, rec: true, impact: true
  });

  const chain = buildCausalChain(telemetry, recommendation);

  const toggleSection = useCallback((key) => {
    setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const handleCopy = useCallback(() => {
    if (!chain) return;
    const text = buildPlainText(chain, apId);
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  }, [chain, apId]);

  const CollapseToggle = ({ sectionKey }) => (
    <IconButton size="small" onClick={() => toggleSection(sectionKey)} sx={{ ml: 'auto', color: 'text.secondary' }}>
      {expandedSections[sectionKey] ? <KeyboardArrowUpIcon fontSize="small" /> : <KeyboardArrowDownIcon fontSize="small" />}
    </IconButton>
  );

  if (!chain) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>Explain Causal Metric Chain</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
            No telemetry data available. Please wait for a simulation tick.
          </Typography>
        </DialogContent>
      </Dialog>
    );
  }

  const { env, propagation, rf, network, qoe, rootCause, justification, impact, action } = chain;
  const rssiSev = severity(rf.rssi, { goodAbove: -65, warnBelow: -78 });
  const snrSev  = severity(rf.snrActual, { goodAbove: 20, warnBelow: 10 });
  const noiseSev = severity(rf.noiseFloor, { goodAbove: -90, warnBelow: -80 }); // inverted: lower noise is better
  const noiseSevReal = rf.noiseFloor != null
    ? (rf.noiseFloor < -90 ? { color: '#22c55e', label: 'Healthy' } : rf.noiseFloor < -80 ? { color: '#f59e0b', label: 'Warning' } : { color: '#ef4444', label: 'Critical' })
    : { color: '#64748B', label: 'N/A' };
  const retrySev = severity(network.retryRate != null ? 1 - network.retryRate : null, { goodAbove: 0.90, warnBelow: 0.80 });
  const retrySevReal = network.retryRate != null
    ? (network.retryRate < 0.10 ? { color: '#22c55e', label: 'Healthy' } : network.retryRate < 0.20 ? { color: '#f59e0b', label: 'Warning' } : { color: '#ef4444', label: 'Critical' })
    : { color: '#64748B', label: 'N/A' };
  const airtimeSev = env.chanUtil != null
    ? (env.chanUtil < 0.60 ? { color: '#22c55e', label: 'Healthy' } : env.chanUtil < 0.80 ? { color: '#f59e0b', label: 'Warning' } : { color: '#ef4444', label: 'Critical' })
    : { color: '#64748B', label: 'N/A' };
  const qoeSev = qoe.qoeScore != null
    ? (qoe.qoeScore >= 7 ? { color: '#22c55e', label: 'Good' } : qoe.qoeScore >= 4 ? { color: '#f59e0b', label: 'Fair' } : { color: '#ef4444', label: 'Poor' })
    : { color: '#64748B', label: 'N/A' };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
      PaperProps={{
        sx: {
          bgcolor: 'background.default',
          backgroundImage: 'none',
          border: '1px solid rgba(255,255,255,0.08)',
          maxHeight: '90vh',
        }
      }}
    >
      {/* ── Header ── */}
      <DialogTitle sx={{
        display: 'flex', alignItems: 'center', gap: 1.5,
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        py: 2, px: 3,
        bgcolor: 'background.paper'
      }}>
        <AccountTreeIcon sx={{ color: '#3b82f6' }} />
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 800, lineHeight: 1.2 }}>
            Explain Causal Metric Chain
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {apId ? `AP: ${apId}` : ''} · Root-cause engineering report · {new Date().toLocaleTimeString()}
          </Typography>
        </Box>
        <Tooltip title={copied ? 'Copied!' : 'Copy as plain text'}>
          <Button
            id="causal-chain-copy-btn"
            variant="outlined"
            size="small"
            startIcon={copied ? <CheckIcon /> : <ContentCopyIcon />}
            onClick={handleCopy}
            color={copied ? 'success' : 'primary'}
            sx={{ mr: 1, textTransform: 'none', fontWeight: 600 }}
          >
            {copied ? 'Copied' : 'Copy'}
          </Button>
        </Tooltip>
        <IconButton id="causal-chain-close-btn" onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ px: 3, pt: 2, pb: 3 }}>

        {/* ─── SECTION 1: Environment ─── */}
        <Section accent={SECTION_ACCENTS.env}>
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => toggleSection('env')}>
            <SectionHeader step="1" icon="🌍" title="Environment Factors" accent={SECTION_ACCENTS.env} />
            <CollapseToggle sectionKey="env" />
          </Box>
          <Collapse in={expandedSections.env}>
            <MetricRow label="Client Distance (avg)" value={env.distance?.toFixed(1)} unit=" m"
              color={env.distance != null ? (env.distance < 15 ? '#22c55e' : env.distance < 25 ? '#f59e0b' : '#ef4444') : undefined} />
            {env.maxDistance != null && (
              <MetricRow label="Max Client Distance" value={env.maxDistance?.toFixed(1)} unit=" m" />
            )}
            <MetricRow label="Walls / Obstacles" value={env.wallCount} unit="" note={env.wallLoss != null ? `~${env.wallLoss.toFixed(1)} dB signal attenuation` : undefined}
              color={env.wallCount != null ? (env.wallCount <= 1 ? '#22c55e' : env.wallCount <= 3 ? '#f59e0b' : '#ef4444') : undefined} />
            <MetricRow label="Interference Source" value={env.intType ?? 'None'}
              color={env.intType ? '#ef4444' : '#22c55e'} />
            <MetricRow label="Channel Utilization" value={env.chanUtil != null ? (env.chanUtil * 100).toFixed(1) : null} unit=" %"
              color={airtimeSev.color}
              note={airtimeSev.label} />
            <MetricRow label="Connected Clients" value={env.clientCount} />
          </Collapse>
        </Section>

        <ArrowDivider label="drives propagation" />

        {/* ─── SECTION 2: Propagation ─── */}
        <Section accent={SECTION_ACCENTS.propagation}>
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => toggleSection('propagation')}>
            <SectionHeader step="2" icon="📡" title="Propagation Analysis" accent={SECTION_ACCENTS.propagation} />
            <CollapseToggle sectionKey="propagation" />
          </Box>
          <Collapse in={expandedSections.propagation}>
            <MetricRow label="Operating Frequency" value={env.freqMhz} unit=" MHz" />
            <MetricRow label="AP TX Power" value={env.txPower} unit=" dBm" />
            <MetricRow label="Free-Space Path Loss" value={propagation.pathLoss} unit=" dB"
              color={propagation.pathLoss != null ? (propagation.pathLoss < 70 ? '#22c55e' : propagation.pathLoss < 85 ? '#f59e0b' : '#ef4444') : undefined}
              note={env.wallCount != null ? `Includes ${env.wallCount} wall(s) × ~3 dB each` : undefined} />
            <MetricRow label="Estimated Received Power" value={propagation.receivedPowerEstimate} unit=" dBm" />
            {env.distance != null && (
              <Box sx={{ mt: 1, p: 1, bgcolor: 'rgba(139,92,246,0.08)', borderRadius: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', lineHeight: 1.8 }}>
                  FSPL = 20·log₁₀({env.distance?.toFixed(0)}m) + 20·log₁₀({env.freqMhz}MHz) − 27.55 + {env.wallLoss?.toFixed(1) ?? 0}dB wall loss
                  {propagation.pathLoss != null ? ` = ${propagation.pathLoss} dB` : ''}
                </Typography>
              </Box>
            )}
          </Collapse>
        </Section>

        <ArrowDivider label="determines signal quality" />

        {/* ─── SECTION 3: RF Signal Quality ─── */}
        <Section accent={SECTION_ACCENTS.rf}>
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => toggleSection('rf')}>
            <SectionHeader step="3" icon="📶" title="RF Signal Quality" accent={SECTION_ACCENTS.rf} />
            <CollapseToggle sectionKey="rf" />
          </Box>
          <Collapse in={expandedSections.rf}>
            <MetricRow label="RSSI" value={rf.rssi?.toFixed(1)} unit=" dBm"
              color={rssiSev.color} note={rssiSev.label} />
            <MetricRow label="Noise Floor" value={rf.noiseFloor?.toFixed(1)} unit=" dBm"
              color={noiseSevReal.color} note={noiseSevReal.label} />
            <Divider sx={{ my: 1, opacity: 0.3 }} />
            <Box sx={{ p: 1.5, bgcolor: 'rgba(6,182,212,0.07)', borderRadius: 1, mb: 1 }}>
              <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mb: 0.5 }}>
                SNR Calculation
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', color: SECTION_ACCENTS.rf }}>
                SNR = RSSI − Noise Floor = {rf.rssi?.toFixed(1) ?? '?'} − ({rf.noiseFloor?.toFixed(1) ?? '?'}) = <strong>{rf.snrActual?.toFixed(1) ?? '?'} dB</strong>
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
              <MetricRow label="SNR" value={rf.snrActual?.toFixed(1)} unit=" dB"
                color={snrSev.color} />
              <StatusBadge label={rf.snrQ.label} color={rf.snrQ.color} />
            </Box>
            <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {[
                { range: '>25 dB', label: 'Excellent', color: '#22c55e' },
                { range: '20–25 dB', label: 'Good', color: '#22c55e' },
                { range: '10–20 dB', label: 'Moderate', color: '#f59e0b' },
                { range: '<10 dB', label: 'Poor', color: '#ef4444' },
              ].map(({ range, label, color }) => (
                <Chip key={label} size="small" label={`${range} → ${label}`}
                  sx={{ fontSize: '0.68rem', bgcolor: `${color}18`, color, border: `1px solid ${color}33` }}
                />
              ))}
            </Box>
          </Collapse>
        </Section>

        <ArrowDivider label="impacts network layer" />

        {/* ─── SECTION 4: Network Impact ─── */}
        <Section accent={SECTION_ACCENTS.network}>
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => toggleSection('network')}>
            <SectionHeader step="4" icon="🔁" title="Network Impact" accent={SECTION_ACCENTS.network} />
            <CollapseToggle sectionKey="network" />
          </Box>
          <Collapse in={expandedSections.network}>
            <MetricRow label="Retry Rate" value={network.retryRate != null ? (network.retryRate * 100).toFixed(1) : null} unit=" %"
              color={retrySevReal.color} note={retrySevReal.label} />
            <MetricRow label="Packet Loss (est.)" value={network.packetLoss != null ? (network.packetLoss * 100).toFixed(1) : null} unit=" %" />
            <MetricRow label="Modulation Scheme" value={network.modulationEff}
              color={rf.snrActual != null ? (rf.snrActual > 20 ? '#22c55e' : rf.snrActual > 10 ? '#f59e0b' : '#ef4444') : undefined} />
            <MetricRow label="Airtime Utilization" value={network.airtimeUtil != null ? (network.airtimeUtil * 100).toFixed(1) : null} unit=" %"
              color={airtimeSev.color} note={airtimeSev.label} />
            {network.retryOverhead != null && (
              <Box sx={{ mt: 1, p: 1, bgcolor: 'rgba(245,158,11,0.07)', borderRadius: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Retransmission airtime overhead: <strong style={{ color: '#f59e0b' }}>{network.retryOverhead}%</strong> of total airtime wasted on retries
                </Typography>
              </Box>
            )}
          </Collapse>
        </Section>

        <ArrowDivider label="degrades user experience" />

        {/* ─── SECTION 5: QoE Impact ─── */}
        <Section accent={SECTION_ACCENTS.qoe}>
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => toggleSection('qoe')}>
            <SectionHeader step="5" icon="👤" title="User Experience Impact" accent={SECTION_ACCENTS.qoe} />
            <CollapseToggle sectionKey="qoe" />
          </Box>
          <Collapse in={expandedSections.qoe}>
            <MetricRow label="Throughput Degradation (est.)" value={qoe.thputDegPct?.toFixed(1)} unit=" %" color={qoe.thputDegPct != null ? (qoe.thputDegPct < 10 ? '#22c55e' : qoe.thputDegPct < 25 ? '#f59e0b' : '#ef4444') : undefined} />
            <MetricRow label="Latency Increase (est.)" value={qoe.latencyInc?.toFixed(0)} unit=" ms" color={qoe.latencyInc != null ? (qoe.latencyInc < 20 ? '#22c55e' : qoe.latencyInc < 60 ? '#f59e0b' : '#ef4444') : undefined} />
            <MetricRow label="QoE Score" value={qoe.qoeScore?.toFixed(1)} unit=" / 10"
              color={qoeSev.color} note={`${qoe.qoeCategory ?? ''} — ${qoeSev.label}`} />
          </Collapse>
        </Section>

        <ArrowDivider label="triggers root cause detection" />

        {/* ─── SECTION 6: Root Cause ─── */}
        <Section accent={SECTION_ACCENTS.rootCause}>
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => toggleSection('rootCause')}>
            <SectionHeader step="6" icon="🔍" title="Root Cause Detection" accent={SECTION_ACCENTS.rootCause} />
            <CollapseToggle sectionKey="rootCause" />
          </Box>
          <Collapse in={expandedSections.rootCause}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, my: 1.5 }}>
              <Typography variant="body2" color="text.secondary">Dominant Cause</Typography>
              <Chip
                label={rootCause.cause}
                sx={{
                  fontWeight: 800, fontSize: '0.85rem',
                  bgcolor: 'rgba(239,68,68,0.15)', color: '#ef4444',
                  border: '1px solid rgba(239,68,68,0.4)'
                }}
              />
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                Confidence Score
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={(rootCause.confidence ?? 0) * 100}
                  sx={{
                    flexGrow: 1, height: 8, borderRadius: 4,
                    bgcolor: 'rgba(255,255,255,0.06)',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: rootCause.confidence >= 0.85 ? '#22c55e' : rootCause.confidence >= 0.65 ? '#f59e0b' : '#ef4444',
                      borderRadius: 4
                    }
                  }}
                />
                <Typography variant="body2" sx={{ fontWeight: 700, fontFamily: 'monospace', minWidth: 40, color: '#ef4444' }}>
                  {((rootCause.confidence ?? 0) * 100).toFixed(0)}%
                </Typography>
              </Box>
            </Box>
          </Collapse>
        </Section>

        <ArrowDivider label="produces recommendation" />

        {/* ─── SECTION 7: Recommendation Justification ─── */}
        <Section accent={SECTION_ACCENTS.rec}>
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => toggleSection('rec')}>
            <SectionHeader step="7" icon="⚡" title="Recommendation Justification" accent={SECTION_ACCENTS.rec} />
            <CollapseToggle sectionKey="rec" />
          </Box>
          <Collapse in={expandedSections.rec}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
              <Typography variant="body2" color="text.secondary">Selected Action</Typography>
              <Chip
                label={action}
                sx={{
                  fontWeight: 800, fontFamily: 'monospace', fontSize: '0.82rem',
                  bgcolor: 'rgba(34,197,94,0.15)', color: '#22c55e',
                  border: '1px solid rgba(34,197,94,0.4)'
                }}
              />
              {recommendation?.confidence != null && (
                <Chip
                  label={`${(recommendation.confidence * 100).toFixed(0)}% confidence`}
                  size="small"
                  sx={{ bgcolor: 'rgba(59,130,246,0.12)', color: '#3b82f6', fontSize: '0.7rem' }}
                />
              )}
            </Box>
            <Paper elevation={0} sx={{ p: 1.5, bgcolor: 'rgba(34,197,94,0.05)', border: '1px solid rgba(34,197,94,0.18)', borderRadius: 1.5 }}>
              <Typography variant="body2" sx={{ lineHeight: 1.8, color: 'text.primary', fontStyle: 'italic' }}>
                "{justification}"
              </Typography>
            </Paper>
          </Collapse>
        </Section>

        {/* ─── SECTION 8: Predicted Impact ─── */}
        <Section accent={SECTION_ACCENTS.impact}>
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => toggleSection('impact')}>
            <SectionHeader step="8" icon="📈" title="Predicted Impact (if Applied)" accent={SECTION_ACCENTS.impact} />
            <CollapseToggle sectionKey="impact" />
          </Box>
          <Collapse in={expandedSections.impact}>
            {action === 'NONE' ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
                No action required. System is operating optimally.
              </Typography>
            ) : (
              <>
                <ImpactBar label="RSSI" before={impact.rssiBefore} after={impact.rssiAfter} unit=" dBm"
                  color={impact.rssiAfter != null && impact.rssiAfter > (impact.rssiBefore ?? -100) ? '#22c55e' : '#f59e0b'} />
                <ImpactBar label="SNR" before={impact.snrBefore} after={impact.snrAfter} unit=" dB"
                  color={impact.snrAfter != null && impact.snrAfter > (impact.snrBefore ?? 0) ? '#22c55e' : '#f59e0b'} />
                <ImpactBar label="QoE Score" before={impact.qoeBefore} after={impact.qoeAfter} unit=" / 10"
                  color={impact.qoeAfter != null && impact.qoeAfter > (impact.qoeBefore ?? 0) ? '#22c55e' : '#f59e0b'} />
                {impact.retryBefore != null && (
                  <ImpactBar label="Retry Rate" before={parseFloat((impact.retryBefore * 100).toFixed(1))} after={parseFloat((impact.retryAfter * 100).toFixed(1))} unit=" %"
                    color={impact.retryAfter != null && impact.retryAfter < (impact.retryBefore ?? 1) ? '#22c55e' : '#f59e0b'} />
                )}
              </>
            )}
          </Collapse>
        </Section>

      </DialogContent>
    </Dialog>
  );
};

export default CausalMetricChainModal;
