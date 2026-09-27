import React, { useState } from 'react';
import { TrackedObject } from '../../types';
import clsx from 'clsx';
import { format } from 'date-fns';
import { ArrowUp, ArrowDown } from 'lucide-react';

interface TrackingTableProps {
  tracks: TrackedObject[];
  selectedTrackId: number | null;
  onSelectTrack: (id: number) => void;
}

const CLASS_COLORS: Record<string, string> = {
  person: 'bg-red-500',
  car: 'bg-orange-500',
  truck: 'bg-amber-500',
  bus: 'bg-yellow-500',
  bicycle: 'bg-blue-500',
  motorcycle: 'bg-purple-500',
};

type SortKey = 'id' | 'class_name' | 'speed' | 'heading' | 'status' | 'last_seen';

export default function TrackingTable({ tracks, selectedTrackId, onSelectTrack }: TrackingTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('last_seen');
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const normalizedTracks = (tracks || []).map((t, idx) => {
    const raw = t as any;
    const id = raw.track_id ?? raw.id ?? (idx + 1);
    const className = String(raw.class_name || 'unknown').toLowerCase();
    const lat = Number(raw.lat ?? raw.last_lat ?? 0);
    const lon = Number(raw.lon ?? raw.last_lon ?? 0);
    const speed = Number(raw.speed ?? raw.last_speed_mps ?? 0);
    const heading = Number(raw.heading ?? raw.last_heading_deg ?? 0);
    const status = String(raw.status || 'CONFIRMED').toUpperCase();
    const lastSeen = raw.last_seen ? String(raw.last_seen) : new Date().toISOString();

    return {
      rawId: id,
      className,
      lat,
      lon,
      speed,
      heading,
      status,
      lastSeen,
    };
  });

  const sortedTracks = [...normalizedTracks].sort((a, b) => {
    let aVal: any = a[sortKey as keyof typeof a];
    let bVal: any = b[sortKey as keyof typeof b];
    if (sortKey === 'id') {
      aVal = a.rawId;
      bVal = b.rawId;
    }

    if (aVal === undefined || bVal === undefined) return 0;
    if (aVal < bVal) return sortAsc ? -1 : 1;
    if (aVal > bVal) return sortAsc ? 1 : -1;
    return 0;
  });

  const getSortIcon = (key: SortKey) => {
    if (sortKey !== key) return null;
    return sortAsc ? <ArrowUp className="w-3 h-3 inline ml-1" /> : <ArrowDown className="w-3 h-3 inline ml-1" />;
  };

  const safeFormatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return '--:--:--';
      return format(d, 'HH:mm:ss');
    } catch {
      return '--:--:--';
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0f1a] border border-gray-700 rounded-md overflow-hidden">
      <div className="p-3 border-b border-gray-700 bg-gray-900 flex items-center justify-between">
        <h2 className="text-sm font-bold text-gray-200">Tracked Targets ({normalizedTracks.length})</h2>
        <span className="text-[10px] text-green-400 bg-green-950 px-2 py-0.5 rounded border border-green-800">
          AI PERCEPTION ACTIVE
        </span>
      </div>

      <div className="flex-1 overflow-auto">
        {normalizedTracks.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500 text-xs">
            Scanning for targets...
          </div>
        ) : (
          <table className="w-full text-left border-collapse text-xs">
            <thead className="sticky top-0 bg-gray-800 text-gray-400 z-10 shadow">
              <tr>
                <th className="p-2 cursor-pointer hover:text-gray-200" onClick={() => handleSort('id')}>ID {getSortIcon('id')}</th>
                <th className="p-2 cursor-pointer hover:text-gray-200" onClick={() => handleSort('class_name')}>Class {getSortIcon('class_name')}</th>
                <th className="p-2">GPS</th>
                <th className="p-2 cursor-pointer hover:text-gray-200" onClick={() => handleSort('speed')}>Speed (m/s) {getSortIcon('speed')}</th>
                <th className="p-2 cursor-pointer hover:text-gray-200" onClick={() => handleSort('heading')}>Heading {getSortIcon('heading')}</th>
                <th className="p-2 cursor-pointer hover:text-gray-200" onClick={() => handleSort('status')}>Status {getSortIcon('status')}</th>
                <th className="p-2 cursor-pointer hover:text-gray-200" onClick={() => handleSort('last_seen')}>Last Seen {getSortIcon('last_seen')}</th>
              </tr>
            </thead>
            <tbody className="text-gray-300 font-mono">
              {sortedTracks.map((track) => (
                <tr
                  key={track.rawId}
                  onClick={() => onSelectTrack(track.rawId)}
                  className={clsx(
                    'border-b border-gray-800 cursor-pointer transition-colors',
                    selectedTrackId === track.rawId ? 'bg-green-950/60 border-l-4 border-l-green-400' : 'hover:bg-gray-800/50'
                  )}
                >
                  <td className="p-2">#{track.rawId}</td>
                  <td className="p-2">
                    <span className={clsx('px-1.5 py-0.5 rounded text-[10px] text-white font-bold', CLASS_COLORS[track.className] || 'bg-blue-600')}>
                      {track.className.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-2">
                    {track.lat.toFixed(5)}, {track.lon.toFixed(5)}
                  </td>
                  <td className="p-2">{track.speed.toFixed(1)}</td>
                  <td className="p-2">{track.heading.toFixed(0)}°</td>
                  <td className="p-2">
                    <span className="text-green-400 font-semibold">{track.status}</span>
                  </td>
                  <td className="p-2">{safeFormatDate(track.lastSeen)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
