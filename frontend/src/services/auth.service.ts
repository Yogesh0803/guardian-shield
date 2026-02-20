import api from './api';
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types';

export const authService = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/login', data);
    localStorage.setItem('access_token', res.data.access_token);
    localStorage.setItem('refresh_token', res.data.refresh_token);
    return res.data;
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/register', data);
    localStorage.setItem('access_token', res.data.access_token);
    localStorage.setItem('refresh_token', res.data.refresh_token);
    return res.data;
  },

  async getMe(): Promise<User> {
    const res = await api.get<User>('/auth/me');
    return res.data;
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
