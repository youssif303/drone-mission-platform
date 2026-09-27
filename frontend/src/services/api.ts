import axios from 'axios';
import { Mission, TrackedObject, TrackHistoryPoint, Alert, AlertRule, HealthStatus } from '../types';

const api = axios.create({
  baseURL: '/api'
});

export const getMissions = () => api.get<Mission[]>('/missions').then(res => res.data);
export const getMission = (id: number) => api.get<Mission>(`/missions/${id}`).then(res => res.data);
export const createMission = (data: Partial<Mission>) => api.post<Mission>('/missions', data).then(res => res.data);
export const updateMission = (id: number, data: Partial<Mission>) => api.put<Mission>(`/missions/${id}`, data).then(res => res.data);
export const deleteMission = (id: number) => api.delete(`/missions/${id}`).then(res => res.data);

export const startMission = (id: number) => api.post(`/missions/${id}/start`).then(res => res.data);
export const pauseMission = (id: number) => api.post(`/missions/${id}/pause`).then(res => res.data);
export const abortMission = (id: number) => api.post(`/missions/${id}/abort`).then(res => res.data);

export const getTracks = (params?: any) => api.get<TrackedObject[]>('/tracks', { params }).then(res => res.data);
export const getTrack = (trackId: number) => api.get<TrackedObject>(`/tracks/${trackId}`).then(res => res.data);
export const getTrackHistory = (trackId: number) => api.get<TrackHistoryPoint[]>(`/tracks/${trackId}/history`).then(res => res.data);

export const getAlerts = (params?: any) => api.get<Alert[]>('/alerts', { params }).then(res => res.data);
export const createAlertRule = (data: Partial<AlertRule>) => api.post<AlertRule>('/alerts/rules', data).then(res => res.data);
export const getAlertRules = () => api.get<AlertRule[]>('/alerts/rules').then(res => res.data);
export const deleteAlertRule = (id: number) => api.delete(`/alerts/rules/${id}`).then(res => res.data);

export const getReport = (missionId: number) => api.get(`/reports/mission/${missionId}`, { responseType: 'blob' }).then(res => res.data);

export const getHealth = () => api.get<HealthStatus>('/health').then(res => res.data);
