import { useState, useEffect, useCallback } from 'react';
import { fetchAlerts } from '../services/api';
import { REFRESH_INTERVAL } from '../config';

export const useAlerts = (apId = null, activeOnly = false) => {
  const [data, setData]           = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [lastFetch, setLastFetch] = useState(null);
  const [recordCount, setRecordCount] = useState(0);

  const load = useCallback(async () => {
    try {
      const result = await fetchAlerts(apId, activeOnly);
      setData(result ?? []);
      setError(null);
      setLastFetch(new Date().toISOString());
      setRecordCount(result?.length ?? 0);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [apId, activeOnly]);

  useEffect(() => {
    let mounted = true;
    const wrappedLoad = async () => { if (mounted) await load(); };
    wrappedLoad();
    const interval = setInterval(wrappedLoad, REFRESH_INTERVAL);
    return () => { mounted = false; clearInterval(interval); };
  }, [load]);

  return { data, loading, error, lastFetch, recordCount, endpoint: `/api/alerts?ap_id=${apId ?? ''}&active_only=${activeOnly}` };
};
