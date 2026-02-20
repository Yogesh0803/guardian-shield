import api from './api';
import type { Endpoint } from '../types';

export const endpointService = {
  async getAll(): Promise<Endpoint[]> {
    const res = await api.get<Endpoint[]>('/endpoints');
    return res.data;
  },

  async getById(id: string): Promise<Endpoint> {
    const res = await api.get<Endpoint>(`/endpoints/${id}`);
    return res.data;
  },

  async addApp(endpointId: string, appName: string): Promise<void> {
    await api.post(`/endpoints/${endpointId}/apps`, { name: appName });
  },
};
