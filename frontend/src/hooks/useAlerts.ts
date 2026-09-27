import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { Alert } from '../types';

export function useAlerts() {
  const { data, isConnected } = useWebSocket<Alert>('/ws/alerts');
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    if (data) {
      setAlerts(prev => {
        const newAlerts = [data, ...prev];
        return newAlerts.slice(0, 100);
      });
    }
  }, [data]);

  return { alerts, isConnected };
}
