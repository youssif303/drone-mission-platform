import React, { useState } from 'react';
import { Mission } from '../../types';
import { startMission, pauseMission, abortMission, getReport } from '../../services/api';
import { Play, Pause, Square, FileDown } from 'lucide-react';
import clsx from 'clsx';

import { useAppStore } from '../../store/appStore';

interface MissionProgressProps {
  mission: Mission | null;
  onStatusChange?: (status: any) => void;
}

export default function MissionProgress({ mission, onStatusChange }: MissionProgressProps) {
  const [loading, setLoading] = useState(false);

  const waypoints = mission?.waypoints || [];
  const status = mission?.status || 'active';
  const name = mission?.name || 'Alpha Recon Patrol';

  const reachedCount = waypoints.filter(wp => Boolean((wp as any).reached)).length;
  const activeIndex = status === 'completed'
    ? waypoints.length
    : (status === 'active' ? reachedCount : 0);
  const progressPercent = waypoints.length > 0
    ? Math.min(100, Math.round((reachedCount / waypoints.length) * 100))
    : 50;

  const handleAction = async (actionFn: (id: number) => Promise<any>, newStatus: any) => {
    if (newStatus && onStatusChange) {
      onStatusChange(newStatus);
    }
    if (mission) {
      useAppStore.getState().actions.setActiveMission({
        ...mission,
        status: newStatus
      });
    }

    if (!mission?.id) return;
    setLoading(true);
    try {
      await actionFn(mission.id);
    } catch (error) {
      console.error('Mission action failed', error);
    } finally {
      setLoading(false);
    }
  };

  const onAbort = () => {
    if (confirm('Are you sure you want to abort the current mission?')) {
      handleAction(abortMission, 'aborted');
    }
  };

  const onExportReport = async () => {
    const mId = mission?.id || 1;
    try {
      const blob = await getReport(mId);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `mission_report_${mId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      window.location.href = '/reports';
    }
  };

  return (
    <div className="w-full h-full bg-[#111827] border-t border-gray-700 px-4 py-2 flex flex-col justify-center">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="text-xs uppercase tracking-wider text-gray-400 font-semibold">Active Mission:</span>
          <h2 className="text-sm font-bold text-gray-100">{name}</h2>
          <span className={clsx(
            'px-2 py-0.5 rounded text-[10px] font-bold uppercase',
            status === 'active' ? 'bg-green-900/80 text-green-400 border border-green-700' :
            status === 'paused' ? 'bg-amber-900/80 text-amber-400 border border-amber-700' :
            status === 'completed' ? 'bg-blue-900/80 text-blue-400 border border-blue-700' :
            status === 'aborted' ? 'bg-red-900/80 text-red-400 border border-red-700' :
            'bg-gray-800 text-gray-400'
          )}>
            {status}
          </span>
        </div>
        <div className="text-xs font-mono text-gray-300">
          Progress: <span className="text-green-400 font-bold">{progressPercent}%</span>
        </div>
      </div>
      
      <div className="flex items-center justify-between gap-4">
        {/* Waypoints line */}
        <div className="flex items-center gap-2 overflow-x-auto py-1 flex-1">
          {waypoints.length === 0 ? (
            <span className="text-xs text-gray-500">Autonomous flight path active</span>
          ) : (
            waypoints.map((_, idx) => {
              let state = 'pending';
              if (idx < activeIndex) state = 'reached';
              if (idx === activeIndex && status === 'active') state = 'en_route';

              return (
                <div key={idx} className="flex items-center gap-2 shrink-0">
                  <div className={clsx(
                    'flex items-center justify-center w-6 h-6 rounded-full border text-xs font-mono font-bold',
                    state === 'reached' ? 'bg-green-500/20 border-green-500 text-green-400' :
                    state === 'en_route' ? 'bg-amber-500/20 border-amber-500 text-amber-400 animate-pulse' :
                    'bg-gray-800 border-gray-600 text-gray-500'
                  )}>
                    {state === 'reached' ? '✓' : idx + 1}
                  </div>
                  {idx < waypoints.length - 1 && (
                    <div className={clsx(
                      'h-0.5 w-8',
                      idx < activeIndex ? 'bg-green-500' : 'bg-gray-700'
                    )} />
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            disabled={loading || status === 'active' || status === 'completed' || status === 'aborted'}
            onClick={() => handleAction(startMission, 'active')}
            className="flex items-center gap-1.5 px-3 py-1 bg-green-600 hover:bg-green-500 disabled:opacity-40 disabled:hover:bg-green-600 text-white text-xs font-medium rounded transition-colors"
          >
            <Play className="w-3 h-3" /> Start
          </button>
          <button
            disabled={loading || status !== 'active'}
            onClick={() => handleAction(pauseMission, 'paused')}
            className="flex items-center gap-1.5 px-3 py-1 bg-amber-600 hover:bg-amber-500 disabled:opacity-40 disabled:hover:bg-amber-600 text-white text-xs font-medium rounded transition-colors"
          >
            <Pause className="w-3 h-3" /> Pause
          </button>
          <button
            disabled={loading || status === 'completed' || status === 'aborted'}
            onClick={onAbort}
            className="flex items-center gap-1.5 px-3 py-1 bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:hover:bg-red-600 text-white text-xs font-medium rounded transition-colors"
          >
            <Square className="w-3 h-3" /> Abort
          </button>
          <button
            onClick={onExportReport}
            className="flex items-center gap-1.5 px-3 py-1 bg-gray-800 hover:bg-gray-700 border border-gray-600 text-green-400 text-xs font-medium rounded transition-colors shadow"
            title="Download Mission PDF Report"
          >
            <FileDown className="w-3.5 h-3.5" /> PDF Report
          </button>
        </div>
      </div>
    </div>
  );
}
