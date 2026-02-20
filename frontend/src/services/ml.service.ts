import api from './api';
import type { MLStatus } from '../types';

export const mlService = {
  async getStatus(): Promise<MLStatus> {
    const res = await api.get<MLStatus>('/ml/status');
    return res.data;
  },

  async retrain(): Promise<{ message: string }> {
    const res = await api.post<{ message: string }>('/ml/retrain');
    return res.data;
  },
};
