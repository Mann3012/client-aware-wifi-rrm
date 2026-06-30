/**
 * Causal metric chain utilities (Iteration 6).
 * Mirrors dashboard/causal_chain.py for React NOC parity with Streamlit.
 */

export const normalizeInterferenceLabel = (intType) => {
  if (!intType || intType === 'None') return 'None';
  const mapping = {
    BLE: 'Bluetooth',
    MICROWAVE: 'Microwave',
    'Neighbor AP': 'Neighbor AP',
    CO_CHANNEL_INTERFERENCE: 'Neighbor AP',
    CLIENT_CONGESTION: 'Client Congestion',
    WEAK_SIGNAL: 'Weak Signal',
  };
  return mapping[intType] || intType.replace(/_/g, ' ');
};

export const interferenceMatches = (intType, ...keywords) => {
  if (!intType || intType === 'None') return false;
  const label = normalizeInterferenceLabel(intType).toLowerCase();
  const raw = intType.toLowerCase();
  return keywords.some((k) => label.includes(k.toLowerCase()) || raw.includes(k.toLowerCase()));
};

export const parseSpectrumSnapshot = (raw) => {
  if (!raw) return null;
  if (typeof raw === 'object') return raw;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

export const computePathLoss = (distanceM, freqMhz, wallLossDb) => {
  if (distanceM == null || freqMhz == null) return null;
  const d = Math.max(1.0, Number(distanceM));
  const plD0 = 32.44 + 20 * Math.log10(0.001) + 20 * Math.log10(Number(freqMhz));
  return parseFloat((plD0 + 10 * 3.0 * Math.log10(d) + Number(wallLossDb || 0)).toFixed(1));
};

export const snrQuality = (snr) => {
  if (snr == null) return { label: 'Unknown', color: '#64748B' };
  if (snr > 25) return { label: 'Excellent', color: '#22c55e' };
  if (snr >= 20) return { label: 'Good', color: '#22c55e' };
  if (snr >= 10) return { label: 'Moderate', color: '#f59e0b' };
  return { label: 'Poor', color: '#ef4444' };
};

export const getModulation = (snr) => {
  if (snr == null) return 'Unknown';
  if (snr > 28) return '1024-QAM / 256-QAM (MCS 10–11)';
  if (snr > 22) return '256-QAM (MCS 8–9)';
  if (snr > 18) return '64-QAM (MCS 7)';
  if (snr > 13) return '16-QAM (MCS 4–5)';
  if (snr > 8) return 'QPSK (MCS 2–3)';
  return 'BPSK (MCS 0–1)';
};

export const formatRootCauseLabel = (rootCause) => {
  if (!rootCause || rootCause === 'NONE' || rootCause === 'None') return '';
  return rootCause.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

export const deriveRootCauseRanked = (
  rssi, snr, noiseFloor, retryRate, airtimeFrac, intType, distanceM, recRootCause = null,
) => {
  const causes = [];

  if (recRootCause && recRootCause !== 'NONE' && recRootCause !== 'None') {
    const rc = recRootCause.toUpperCase();
    if (rc.includes('MICROWAVE')) {
      causes.push({ label: 'Interference (Microwave)', conf: 0.95, reason: 'Broadband RF noise emission detected by recommendation engine.' });
    } else if (rc.includes('BLE') || rc.includes('BLUETOOTH')) {
      causes.push({ label: 'Interference (Bluetooth)', conf: 0.95, reason: 'Bursty non-WiFi interference detected; overlaps with Wi-Fi frames.' });
    } else if (rc.includes('NEIGHBOR') || rc.includes('CO_CHANNEL')) {
      causes.push({ label: 'Co-Channel Contention (Neighbor AP)', conf: 0.93, reason: 'Neighbor AP traffic increases contention and airtime competition.' });
    } else if (rc.includes('CONGESTION')) {
      causes.push({ label: 'Congestion (High Density)', conf: 0.94, reason: 'Channel is heavily utilized by active traffic, causing medium contention.' });
    } else if (rc.includes('WEAK') || rc.includes('COVERAGE')) {
      causes.push({ label: 'Coverage (Distance + Path Loss)', conf: 0.90, reason: 'Weak signal due to propagation distance and path loss.' });
    } else {
      causes.push({ label: formatRootCauseLabel(recRootCause), conf: 0.90, reason: `Recommendation engine identified root cause: ${formatRootCauseLabel(recRootCause)}.` });
    }
  }

  if (interferenceMatches(intType, 'bluetooth', 'ble')) {
    causes.push({ label: 'Interference (Bluetooth)', conf: 0.95, reason: 'Bursty non-WiFi interference detected; overlaps with Wi-Fi frames.' });
  } else if (interferenceMatches(intType, 'microwave')) {
    causes.push({ label: 'Interference (Microwave)', conf: 0.95, reason: 'Broadband RF noise emission detected.' });
  } else if (interferenceMatches(intType, 'neighbor', 'co_channel')) {
    causes.push({ label: 'Co-Channel Contention (Neighbor AP)', conf: 0.92, reason: 'Neighbor AP traffic increases contention and airtime competition.' });
  } else if (intType && intType !== 'None') {
    causes.push({ label: `Interference (${normalizeInterferenceLabel(intType)})`, conf: 0.90, reason: 'Active non-WiFi interference detected.' });
  } else if (noiseFloor != null && noiseFloor >= -90) {
    causes.push({ label: 'Interference (Elevated Noise)', conf: 0.85, reason: 'Elevated noise floor independent of client traffic.' });
  } else {
    causes.push({ label: 'Interference', conf: 0.15, reason: 'Noise floor is clean at the AP.' });
  }

  if (rssi != null && rssi < -78) {
    if (distanceM != null && distanceM > 20) {
      causes.push({ label: 'Coverage (Distance + Path Loss)', conf: 0.90, reason: 'Weak signal due to propagation distance and path loss.' });
    } else {
      causes.push({ label: 'Coverage (Weak Signal)', conf: 0.88, reason: 'Weak signal despite proximity (possible obstruction).' });
    }
  } else {
    causes.push({ label: 'Coverage', conf: 0.18, reason: 'RSSI remains strong, suggesting adequate signal propagation.' });
  }

  if (airtimeFrac != null && airtimeFrac > 0.75) {
    causes.push({ label: 'Congestion (High Density)', conf: 0.93, reason: 'Channel is heavily utilized by active traffic, causing medium contention.' });
  } else {
    causes.push({ label: 'Congestion', conf: 0.20, reason: 'Airtime utilization is nominal, indicating no channel saturation.' });
  }

  const seen = {};
  causes.forEach((c) => {
    if (!seen[c.label] || c.conf > seen[c.label].conf) seen[c.label] = c;
  });
  const ranked = Object.values(seen).sort((a, b) => b.conf - a.conf);
  if (ranked[0].conf < 0.50) {
    ranked.unshift({ label: 'System Optimal', conf: 0.99, reason: 'All metrics are within healthy nominal parameters.' });
  }
  return ranked;
};

export const estimateImpact = (action, rssi, snr, qoe, retryRate, expectedQoeGain = null) => {
  const deltas = {
    CHANNEL_CHANGE: { rssi: 1, snr: 10, qoe: 15.0, retry: -0.20 },
    POWER_INCREASE: { rssi: 6, snr: 6, qoe: 12.0, retry: -0.12 },
    POWER_DECREASE: { rssi: -4, snr: 5, qoe: 8.0, retry: -0.10 },
    WIDTH_ADJUST: { rssi: 0, snr: 4, qoe: 10.0, retry: -0.08 },
    LOAD_BALANCE: { rssi: 0, snr: 3, qoe: 12.0, retry: -0.10 },
    NONE: { rssi: 0, snr: 0, qoe: 0, retry: 0 },
  }[action] || { rssi: 0, snr: 0, qoe: 0, retry: 0 };

  const qoeDelta = expectedQoeGain != null ? expectedQoeGain : deltas.qoe;
  const clamp = (v, delta, min, max) => {
    if (v == null) return null;
    let r = parseFloat((v + delta).toFixed(2));
    if (min != null) r = Math.max(min, r);
    if (max != null) r = Math.min(max, r);
    return r;
  };

  return {
    rssiBefore: rssi,
    rssiAfter: clamp(rssi, deltas.rssi),
    snrBefore: snr,
    snrAfter: clamp(snr, deltas.snr, 0),
    qoeBefore: qoe,
    qoeAfter: clamp(qoe, qoeDelta, 0, 100),
    retryBefore: retryRate,
    retryAfter: clamp(retryRate, deltas.retry, 0, 1),
  };
};

export const buildExecutiveSummary = (dominant, retryPct, airtimePct, qoeScore, action) => {
  const qoeStr = qoeScore != null ? `${qoeScore.toFixed(1)}/100` : 'N/A';
  let summary;
  if (dominant.label.includes('Coverage')) {
    summary = `Excessive path loss reduced RSSI and SNR, increasing PER (${retryPct}%) and reducing QoE (${qoeStr}).`;
  } else if (dominant.label.includes('Bluetooth')) {
    summary = `Bluetooth interference increased PER (${retryPct}%) despite healthy average signal quality, reducing QoE (${qoeStr}).`;
  } else if (dominant.label.includes('Microwave')) {
    summary = `Microwave interference caused packet corruption (PER ${retryPct}%), reducing throughput and QoE (${qoeStr}).`;
  } else if (dominant.label.includes('Neighbor') || dominant.label.includes('Co-Channel')) {
    summary = `Neighbor AP contention elevated PER (${retryPct}%) and lowered QoE (${qoeStr}).`;
  } else if (dominant.label.includes('Congestion')) {
    summary = `Heavy airtime utilization (${airtimePct}%) increased contention and lowered QoE (${qoeStr}).`;
  } else if (dominant.label.includes('System Optimal')) {
    summary = `All metrics are within healthy nominal parameters. QoE is ${qoeStr}.`;
  } else {
    summary = `Performance metrics deviated from baselines, increasing PER (${retryPct}%) and reducing QoE (${qoeStr}).`;
  }
  summary += ` Dominant root cause: **${dominant.label}** (${Math.round(dominant.conf * 100)}% confidence). Recommended action: **${action}**.`;
  return summary;
};

export const buildCausalChain = (telemetry, recommendation) => {
  if (!telemetry) return null;
  const t = telemetry;
  const rec = recommendation;

  const distance = t.distance ?? null;
  const wallCount = t.wall_count ?? null;
  const wallLoss = t.wall_loss ?? (wallCount != null ? wallCount * 3 : null);
  const freqMhz = t.freq_mhz ?? 5180;
  const txPower = t.tx_power ?? 20;
  const airtimeFrac = t.airtime_utilization ?? null;
  const intType = t.interference_type && t.interference_type !== 'None' ? t.interference_type : null;

  const rssi = t.rssi ?? null;
  const noiseFloor = t.noise_floor ?? -96;
  const snr = t.snr ?? (rssi != null ? parseFloat((rssi - noiseFloor).toFixed(1)) : null);
  const retryRate = t.retry_rate ?? null;
  const qoeScore = t.qoe_score ?? null;
  const qoeCategory = t.qoe_category ?? null;

  const action = rec?.action ?? 'NONE';
  const confidence = rec?.confidence ?? 0.80;
  const expGain = rec?.expected_qoe_gain ?? null;
  const recRootCause = rec?.root_cause ?? null;
  const recReason = rec?.reason ?? null;

  const pathLoss = computePathLoss(distance, freqMhz, wallLoss);
  const modelRssi = pathLoss != null ? parseFloat((txPower - pathLoss).toFixed(1)) : null;
  const spectrum = parseSpectrumSnapshot(t.spectrum_snapshot);

  const rankedCauses = deriveRootCauseRanked(
    rssi, snr, noiseFloor, retryRate, airtimeFrac, intType, distance, recRootCause,
  );
  let dominantCause = rankedCauses[0];
  if (recRootCause && recRootCause !== 'NONE' && recRootCause !== 'None') {
    dominantCause = { ...dominantCause, conf: Math.max(dominantCause.conf, confidence) };
  }

  const retryPct = retryRate != null ? parseFloat((retryRate * 100).toFixed(1)) : null;
  const airtimePct = airtimeFrac != null ? parseFloat((airtimeFrac * 100).toFixed(1)) : null;

  return {
    env: { distance, wallCount, wallLoss, freqMhz, txPower, intType, clientCount: t.client_count, airtimePct, spectrum },
    propagation: { pathLoss, modelRssi, measuredRssi: rssi, txPower },
    rf: { rssi, noiseFloor, snr, snrQ: snrQuality(snr) },
    network: {
      retryRate, retryPct, packetLoss: retryRate != null ? parseFloat((retryRate * 0.7 * 100).toFixed(1)) : null,
      modulation: getModulation(snr), airtimePct,
    },
    qoe: {
      qoeScore, qoeCategory,
      thputDegPct: retryPct != null ? parseFloat((retryPct * 1.5).toFixed(1)) : null,
      latencyMs: retryPct != null ? Math.round(retryPct * 1.2) : null,
    },
    rootCause: { ranked: rankedCauses, dominant: dominantCause },
    recommendation: { action, confidence, expGain, recReason, currentValue: rec?.current_value, recommendedValue: rec?.recommended_value },
    impact: estimateImpact(action, rssi, snr, qoeScore, retryRate, expGain),
    executiveSummary: buildExecutiveSummary(dominantCause, retryPct ?? 0, airtimePct ?? 0, qoeScore, action),
  };
};

export const buildPlainText = (chain, apId) => {
  if (!chain) return '';
  const { env, propagation, rf, network, qoe, rootCause, recommendation, impact } = chain;
  return [
    'CAUSAL METRIC CHAIN — ENGINEERING REPORT',
    `AP: ${apId ?? 'Unknown'}   Generated: ${new Date().toLocaleString()}`,
    '',
    '[0] EXECUTIVE SUMMARY',
    chain.executiveSummary.replace(/\*\*/g, ''),
    '',
    '[1] ENVIRONMENT',
    `  Distance: ${env.distance?.toFixed(1) ?? '—'} m`,
    `  Interference: ${env.intType ? normalizeInterferenceLabel(env.intType) : 'None'}`,
    `  Airtime: ${env.airtimePct ?? '—'} %`,
    '',
    '[3] RF SIGNAL QUALITY',
    `  RSSI: ${rf.rssi?.toFixed(1) ?? '—'} dBm`,
    `  SNR: ${rf.snr?.toFixed(1) ?? '—'} dB (${rf.snrQ.label})`,
    '',
    '[6] ROOT CAUSE',
    `  ${rootCause.dominant.label} (${Math.round(rootCause.dominant.conf * 100)}%)`,
    '',
    '[7] RECOMMENDATION',
    `  Action: ${recommendation.action}`,
    `  ${recommendation.recReason ?? ''}`,
    '',
    '[8] PREDICTED IMPACT',
    `  QoE: ${impact.qoeBefore?.toFixed(1) ?? '?'} → ${impact.qoeAfter?.toFixed(1) ?? '?'}/100`,
  ].join('\n');
};
