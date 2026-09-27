import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Plane } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import MissionPlanner from './pages/MissionPlanner';
import Reports from './pages/Reports';
import { useAppStore } from './store/appStore';
import clsx from 'clsx';

export default function App() {
  const isLive = useAppStore(state => state.isLive);

  return (
    <BrowserRouter>
      <div className="bg-[#0a0f1a] text-gray-100 h-screen flex flex-col overflow-hidden">
        {/* Nav bar */}
        <nav className="h-14 bg-gray-900 border-b border-gray-700 flex items-center px-6 shrink-0 justify-between">
          <div className="flex items-center gap-3">
            <Plane className="text-green-400 w-6 h-6" />
            <span className="text-lg font-bold text-green-400">
              Drone Mission Planning & Perception Platform
            </span>
          </div>

          <div className="flex items-center gap-6 h-full">
            <NavLink
              to="/"
              className={({ isActive }) =>
                clsx('text-sm font-medium h-full flex items-center border-b-2', isActive ? 'text-green-400 border-green-400' : 'text-gray-400 border-transparent hover:text-gray-200')
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/planner"
              className={({ isActive }) =>
                clsx('text-sm font-medium h-full flex items-center border-b-2', isActive ? 'text-green-400 border-green-400' : 'text-gray-400 border-transparent hover:text-gray-200')
              }
            >
              Mission Planner
            </NavLink>
            <NavLink
              to="/reports"
              className={({ isActive }) =>
                clsx('text-sm font-medium h-full flex items-center border-b-2', isActive ? 'text-green-400 border-green-400' : 'text-gray-400 border-transparent hover:text-gray-200')
              }
            >
              Reports
            </NavLink>
          </div>

          <div className="flex items-center gap-2">
            <div className={clsx('w-3 h-3 rounded-full', isLive ? 'bg-green-500 animate-pulse shadow-[0_0_8px_#10b981]' : 'bg-red-500')} />
            <span className={clsx('text-sm font-bold font-mono tracking-wider', isLive ? 'text-green-400' : 'text-red-400')}>
              {isLive ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden flex flex-col relative">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/planner" element={<MissionPlanner />} />
            <Route path="/reports" element={<Reports />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
