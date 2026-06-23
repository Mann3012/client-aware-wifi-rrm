import React from 'react';
import StatusCard from './StatusCard';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';

const AlertCard = ({ count, loading }) => {
  const status = `${count} Active`;
  let severity = 'good';
  let description = 'System operating normally';

  if (count > 0) {
    severity = count > 3 ? 'critical' : 'warning';
    description = 'Anomalies detected recently';
  }

  return (
    <StatusCard
      title="Active Alerts (30m)"
      status={status}
      description={description}
      icon={<NotificationsActiveIcon />}
      loading={loading}
      severity={severity}
    />
  );
};

export default AlertCard;
