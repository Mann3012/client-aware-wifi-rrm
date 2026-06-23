import React from 'react';
import {
  Box, Typography, Collapse, Divider, Chip
} from '@mui/material';
import SyncIcon from '@mui/icons-material/Sync';
import ErrorIcon from '@mui/icons-material/Error';

/**
 * Temporary live-data verification panel.
 * Shows last API call, records returned, and timestamp for each feed.
 * Renders as a compact collapsible footer bar – non-intrusive for demos.
 */
const ApiDebugPanel = ({ feeds }) => {
  const [open, setOpen] = React.useState(false);

  return (
    <Box sx={{ mt: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
      {/* Toggle header */}
      <Box
        onClick={() => setOpen(o => !o)}
        sx={{
          display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 0.8,
          bgcolor: 'background.paper', cursor: 'pointer',
          '&:hover': { bgcolor: 'action.hover' }
        }}
      >
        <SyncIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
        <Typography variant="caption" color="text.disabled" sx={{ fontFamily: 'monospace', userSelect: 'none' }}>
          Live Data Verification — {open ? 'hide' : 'show'}
        </Typography>
      </Box>

      <Collapse in={open}>
        <Box sx={{ px: 2, py: 1.5, bgcolor: '#0d1117' }}>
          {feeds.map((f, i) => (
            <Box key={i}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.6, flexWrap: 'wrap' }}>
                <Chip
                  size="small"
                  label={f.error ? 'ERROR' : 'OK'}
                  color={f.error ? 'error' : 'success'}
                  sx={{ fontFamily: 'monospace', fontSize: 10, height: 18, minWidth: 46 }}
                />
                <Typography variant="caption" sx={{ color: '#58a6ff', fontFamily: 'monospace', flexShrink: 0 }}>
                  {f.endpoint}
                </Typography>
                <Typography variant="caption" sx={{ color: '#8b949e', fontFamily: 'monospace' }}>
                  → {f.recordCount} record{f.recordCount !== 1 ? 's' : ''}
                </Typography>
                <Typography variant="caption" sx={{ color: '#3fb950', fontFamily: 'monospace', ml: 'auto' }}>
                  {f.lastFetch ? `last: ${new Date(f.lastFetch).toLocaleTimeString()}` : 'pending…'}
                </Typography>
              </Box>
              {i < feeds.length - 1 && <Divider sx={{ borderColor: '#21262d' }} />}
            </Box>
          ))}
        </Box>
      </Collapse>
    </Box>
  );
};

export default ApiDebugPanel;
