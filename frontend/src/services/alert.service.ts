import api from './api';
import type { Alert, AttackStats } from '../types';

export const alertService = {
  async getAll(params?: {
    endpoint_id?: string;
    app_id?: string;
    severity?: string;
    limit?: number;
  }): Promise<Alert[]> {
    const res = await api.get<Alert[]>('/alerts', { params });
    return res.data;
  },

  async getByEndpointApp(endpointId: string, appId: string): Promise<Alert[]> {
    const res = await api.get<Alert[]>(`/alerts/endpoint/${endpointId}/app/${appId}`);
    return res.data;
  },

  async getAttackStats(endpointId: string): Promise<AttackStats[]> {
    const res = await api.get<AttackStats[]>(`/attacks/endpoint/${endpointId}`);
    return res.data;
  },

  async getAppAttackStats(endpointId: string, appName: string): Promise<AttackStats[]> {
    const res = await api.get<AttackStats[]>(`/attacks/endpoint/${endpointId}/app/${appName}`);
    return res.data;
  },
};
