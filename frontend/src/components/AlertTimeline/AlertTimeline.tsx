import React, { useEffect, useRef } from 'react';
import { Alert } from '../../types';
import clsx from 'clsx';
import { format } from 'date-fns';

interface AlertTimelineProps {
  alerts: Alert[];
}

export default function AlertTimeline({ alerts }: AlertTimelineProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  
  // Show max 50 alerts
  const displayAlerts = [...alerts].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()).slice(-50);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [displayAlerts]);

  const getIconAndColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return { icon: '🔴', color: 'text-red-400' };
      case 'warning':
        return { icon: '⚠️', color: 'text-amber-400' };
      case 'info':
      default:
        return { icon: 'ℹ️', color: 'text-blue-400' };
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 overflow-hidden">
      <div className="p-3 border-b border-gray-700 bg-gray-800">
        <h2 className="text-sm font-bold text-gray-200">Alert Timeline</h2>
      </div>
      <div className="flex-1 overflow-auto p-2 space-y-1">
        {displayAlerts.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">
            No alerts
          </div>
        ) : (
          displayAlerts.map((alert) => {
            const { icon, color } = getIconAndColor(alert.severity);
            return (
              <div key={alert.id} className="flex items-start gap-2 text-xs p-1.5 hover:bg-gray-800 rounded">
                <span className="shrink-0">{icon}</span>
                <span className="text-gray-500 font-mono shrink-0">
                  [{format(new Date(alert.timestamp), 'HH:mm:ss')}]
                </span>
                <span className={clsx('break-words', color)}>
                  {alert.message}
                </span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
