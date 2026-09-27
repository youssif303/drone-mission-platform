import { create } from 'zustand';
import { Mission } from '../types';

interface AppState {
  activeMission: Mission | null;
  isLive: boolean;
  selectedTrackId: number | null;
  actions: {
    setActiveMission: (mission: Mission | null) => void;
    setIsLive: (isLive: boolean) => void;
    selectTrack: (trackId: number | null) => void;
  };
}

export const useAppStore = create<AppState>((set) => ({
  activeMission: null,
  isLive: false,
  selectedTrackId: null,
  actions: {
    setActiveMission: (mission) => set({ activeMission: mission }),
    setIsLive: (isLive) => set({ isLive }),
    selectTrack: (trackId) => set({ selectedTrackId: trackId }),
  },
}));
