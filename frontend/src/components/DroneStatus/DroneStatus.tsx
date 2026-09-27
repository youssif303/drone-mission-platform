import React from 'react';
import { useDroneTelemetry } from '../../hooks/useDroneTelemetry';
import { Navigation, ArrowUpCircle, Battery, Wifi, WifiOff, MapPin, Compass } from 'lucide-react';
import { clsx } from 'clsx';
import { DroneState } from '../../types';

export interface DroneStatusProps {
  droneState?: DroneState | null;
}

export const DroneStatus: React.FC<DroneStatusProps> = ({ droneState: propDroneState }) => {
  const { droneState: hookDroneState, isConnected } = useDroneTelemetry();
  const droneState = propDroneState || hookDroneState;

  const alt = droneState?.alt ?? 50.0;
  const speed = droneState?.speed ?? 14.5;
  const lat = droneState?.lat ?? 48.1351;
  const lon = droneState?.lon ?? 11.5820;
  const battery = droneState?.battery ?? 95.0;
  const heading = droneState?.heading ?? 68.0;

  const renderBatteryColor = (level: number) => {
    if (level <= 20) return 'text-red-400 bg-red-500';
    if (level <= 50) return 'text-amber-400 bg-amber-500';
    return 'text-green-400 bg-green-500';
  };

  return (
    <div className="w-full h-full bg-[#111827] rounded-lg border border-gray-700/80 p-2.5 flex flex-col justify-between shadow-lg font-mono">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-gray-700/60 pb-1.5 mb-1.5">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          <span className="font-bold text-gray-200 tracking-wider text-xs uppercase">
            AIRCRAFT TELEMETRY // DRONE-01
          </span>
        </div>
        <div className="flex items-center gap-1.5 bg-black/50 px-2 py-0.5 rounded border border-gray-700 text-[10px]">
          {isConnected ? <Wifi className="w-3 h-3 text-green-400" /> : <WifiOff className="w-3 h-3 text-amber-400" />}
          <span className={isConnected ? "text-green-400 font-bold" : "text-amber-400 font-bold"}>
            {isConnected ? 'LIVE FEED' : 'SIMULATED'}
          </span>
        </div>
      </div>

      {/* 5-Column Compact Grid */}
      <div className="grid grid-cols-5 gap-1.5 text-center">
        {/* Altitude */}
        <div className="bg-[#1f2937]/70 rounded p-1.5 border border-gray-700/40 flex flex-col items-center justify-center">
          <div className="flex items-center gap-1 text-[10px] text-gray-400 uppercase">
            <ArrowUpCircle className="w-2.5 h-2.5 text-blue-400" />
            <span>ALT</span>
          </div>
          <span className="text-xs font-bold text-gray-100 mt-0.5">{alt.toFixed(1)}m</span>
        </div>

        {/* Speed */}
        <div className="bg-[#1f2937]/70 rounded p-1.5 border border-gray-700/40 flex flex-col items-center justify-center">
          <div className="flex items-center gap-1 text-[10px] text-gray-400 uppercase">
            <Navigation className="w-2.5 h-2.5 text-emerald-400" />
            <span>SPEED</span>
          </div>
          <span className="text-xs font-bold text-emerald-400 mt-0.5">{(speed * 3.6).toFixed(0)} <span className="text-[9px] font-normal text-gray-400">km/h</span></span>
        </div>

        {/* Heading */}
        <div className="bg-[#1f2937]/70 rounded p-1.5 border border-gray-700/40 flex flex-col items-center justify-center">
          <div className="flex items-center gap-1 text-[10px] text-gray-400 uppercase">
            <Compass className="w-2.5 h-2.5 text-purple-400" />
            <span>HEADING</span>
          </div>
          <span className="text-xs font-bold text-gray-100 mt-0.5">{heading.toFixed(0)}°</span>
        </div>

        {/* Battery */}
        <div className="bg-[#1f2937]/70 rounded p-1.5 border border-gray-700/40 flex flex-col items-center justify-center">
          <div className="flex items-center gap-1 text-[10px] text-gray-400 uppercase">
            <Battery className="w-2.5 h-2.5 text-green-400" />
            <span>BATTERY</span>
          </div>
          <div className="flex items-center gap-1 mt-0.5">
            <span className={clsx("text-xs font-bold", renderBatteryColor(battery).split(' ')[0])}>
              {battery.toFixed(0)}%
            </span>
            <div className="w-6 h-1.5 bg-gray-700 rounded overflow-hidden">
              <div 
                className={clsx("h-full", renderBatteryColor(battery).split(' ')[1])} 
                style={{ width: `${Math.max(5, Math.min(100, battery))}%` }} 
              />
            </div>
          </div>
        </div>

        {/* GPS Coordinates */}
        <div className="bg-[#1f2937]/70 rounded p-1.5 border border-gray-700/40 flex flex-col items-center justify-center">
          <div className="flex items-center gap-1 text-[10px] text-gray-400 uppercase">
            <MapPin className="w-2.5 h-2.5 text-amber-400" />
            <span>GPS</span>
          </div>
          <span className="text-[9px] text-gray-300 leading-tight mt-0.5 font-mono">
            {lat.toFixed(4)}<br/>{lon.toFixed(4)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default DroneStatus;
