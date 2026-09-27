import React, { useEffect, useState } from 'react';
import { getMissions, getReport } from '../services/api';
import { Mission } from '../types';
import { FileText, Download, ShieldCheck, CheckCircle2, Clock, PlayCircle } from 'lucide-react';
import { format } from 'date-fns';

export default function Reports() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<number | null>(null);

  useEffect(() => {
    getMissions()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setMissions(data);
        } else {
          // Fallback default mission
          setMissions([
            {
              id: 1,
              name: 'Alpha Recon Patrol',
              description: 'Autonomous area perimeter surveillance and target tracking',
              status: 'active',
              created_at: new Date().toISOString(),
              waypoints: []
            }
          ]);
        }
      })
      .catch(() => {
        setMissions([
          {
            id: 1,
            name: 'Alpha Recon Patrol',
            description: 'Autonomous area perimeter surveillance and target tracking',
            status: 'active',
            created_at: new Date().toISOString(),
            waypoints: []
          }
        ]);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleGenerateReport = async (missionId: number, missionName: string) => {
    setGenerating(missionId);
    try {
      const blob = await getReport(missionId);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `mission_report_${missionId}_${missionName.replace(/\s+/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Report error:', error);
      alert('Generating report from backend... Check that backend is active.');
    } finally {
      setGenerating(null);
    }
  };

  return (
    <div className="flex-1 bg-[#0a0f1a] p-6 lg:p-8 overflow-y-auto h-full font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-5">
          <div>
            <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
              <FileText className="w-6 h-6 text-green-400" />
              Tactical Mission Reports & Intelligence Debriefs
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Download formal ISR (Intelligence, Surveillance, Reconnaissance) debriefing PDFs containing waypoint logs, detected target registries, and perimeter threat alerts.
            </p>
          </div>
          
          <button
            onClick={() => missions[0] && handleGenerateReport(missions[0].id, missions[0].name)}
            disabled={missions.length === 0 || generating !== null}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg font-medium text-sm transition-colors shadow-lg shrink-0"
          >
            <Download className="w-4 h-4" />
            {generating ? 'Generating PDF...' : 'Download Active Report'}
          </button>
        </div>

        {/* Feature Overview Card */}
        <div className="bg-gradient-to-r from-gray-900 to-gray-800/80 border border-gray-700/80 rounded-xl p-5 shadow-lg">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-100">
                Automated Mission Intelligence Briefing
              </h2>
              <p className="text-xs text-gray-300 mt-1 leading-relaxed">
                Every autonomous flight logs real-time geo-coordinates, detected ground targets (#1 CAR, #2 PERSON, #3 TRUCK), speeds, and perimeter boundary alerts. Clicking <strong>"Generate Report"</strong> compiles an official ReportLab PDF document suitable for defense, security, and research debriefings.
              </p>
            </div>
          </div>
        </div>

        {/* Missions Grid */}
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-3">
            Available Missions ({missions.length})
          </h2>

          {loading ? (
            <div className="text-gray-400 p-8 text-center font-mono">Loading mission archives...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {missions.map((mission) => {
                const isActive = mission.status === 'active';
                const isCompleted = mission.status === 'completed';

                return (
                  <div
                    key={mission.id}
                    className="bg-gray-900/90 border border-gray-700 rounded-xl p-5 flex flex-col hover:border-gray-500 transition-all shadow-md"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="font-bold text-gray-100 text-base">{mission.name}</h3>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border flex items-center gap-1 ${
                          isActive
                            ? 'bg-green-900/50 text-green-400 border-green-700'
                            : isCompleted
                            ? 'bg-blue-900/50 text-blue-400 border-blue-700'
                            : 'bg-gray-800 text-gray-400 border-gray-700'
                        }`}
                      >
                        {isActive && <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>}
                        {mission.status}
                      </span>
                    </div>

                    <p className="text-xs text-gray-400 mb-4 line-clamp-2 min-h-[32px]">
                      {mission.description || 'Autonomous area perimeter surveillance and target tracking'}
                    </p>

                    <div className="text-xs font-mono text-gray-500 mb-5 flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-gray-500" />
                      <span>{format(new Date(mission.created_at || new Date()), 'MMM dd, yyyy HH:mm')}</span>
                    </div>

                    <div className="mt-auto pt-3 border-t border-gray-800">
                      <button
                        onClick={() => handleGenerateReport(mission.id, mission.name)}
                        disabled={generating === mission.id}
                        className="w-full flex items-center justify-center gap-2 bg-green-600/90 hover:bg-green-500 disabled:opacity-50 text-white font-medium text-xs py-2.5 rounded-lg transition-colors shadow"
                      >
                        <Download className="w-4 h-4" />
                        {generating === mission.id ? 'Compiling PDF...' : 'Generate PDF Report'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
