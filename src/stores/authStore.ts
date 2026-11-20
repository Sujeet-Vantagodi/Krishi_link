import { create } from 'zustand';
import { User, Role } from '../types';
import { changeLanguage } from '../i18n';
import { API_DEMO_MODE, ApiError, requestApi } from '../lib/api/client';

export interface AuthState {
  user: User | null;
  role: Role;
  token: string | null;
  isAuthenticated: boolean;
  acceptSession: (session: AuthSession) => User;
  setUser: (user: User | null) => void;
  loginWithPhone: (phone: string) => Promise<string>;
  verifyOtp: (requestId: string, otp: string) => Promise<boolean>;
  logout: () => void;
  switchDemoRole: (role: Role) => void;
  fetchCurrentUser: () => Promise<void>;
}

// Pre-seeded demo users for rapid switching
export const DEMO_USERS: Record<Role, User> = {
  buyer: {
    id: 'u_buyer_1',
    phone: '+919876543201',
    role: 'buyer',
    name: 'Udupi Upahar (Kiran Kumar)',
    language: 'en',
  },
  farmer: {
    id: 'u_farmer_1',
    phone: '+919876543202',
    role: 'farmer',
    name: 'Ramesh Gowda (ರಾಮೇಶ್ ಗೌಡ)',
    language: 'kn',
  },
  driver: {
    id: 'u_driver_1',
    phone: '+919876543203',
    role: 'driver',
    name: 'Suresh Kumar',
    language: 'en',
  },
  admin: {
    id: 'u_admin_1',
    phone: '+919876543204',
    role: 'admin',
    name: 'Anita Rao (Ops Tower)',
    language: 'en',
    employee_id: 'KL-OPS-8841',
  },
  hub_staff: {
    id: 'u_staff_1',
    phone: '+919876543205',
    role: 'hub_staff',
    name: 'Praveen Nayak (Kolar Mini Hub)',
    language: 'kn',
  },
};

export interface AuthSession {
  access_token: string;
  refresh_token: string;
  user: User | (Omit<User, 'role'> & { role: 'super_admin' });
}

function presentationUser(user: AuthSession['user']): User {
  return { ...user, role: user.role === 'super_admin' ? 'admin' : user.role };
}

const tokenKey = 'krishilink_token';
const refreshKey = 'krishilink_refresh_token';
const userKey = 'krishilink_user';
const demoUser = API_DEMO_MODE
  ? (() => {
      const stored = localStorage.getItem(userKey);
      try {
        return stored ? JSON.parse(stored) as User : DEMO_USERS.buyer;
      } catch {
        return DEMO_USERS.buyer;
      }
    })()
  : null;

let sessionVersion = 0;
let restoring: Promise<void> | undefined;

export const useAuthStore = create<AuthState>((set, get) => ({
  user: demoUser,
  role: demoUser?.role ?? 'buyer',
  token: API_DEMO_MODE ? 'mock_jwt_token_buyer_123' : null,
  isAuthenticated: API_DEMO_MODE,

  acceptSession: (session) => {
    sessionVersion++;
    const user = presentationUser(session.user);
    localStorage.setItem(tokenKey, session.access_token);
    localStorage.setItem(refreshKey, session.refresh_token);
    localStorage.setItem(userKey, JSON.stringify(user));
    set({ user, role: user.role, token: session.access_token, isAuthenticated: true });
    return user;
  },

  setUser: (user) => {
    if (!user) {
      get().logout();
    } else if (user.id === get().user?.id) {
      const updated = { ...user, role: get().role };
      localStorage.setItem(userKey, JSON.stringify(updated));
      set({ user: updated });
    }
  },

  loginWithPhone: async (phone) => {
    if (API_DEMO_MODE) return 'req_demo';
    const result = await requestApi<{ request_id: string }>('/auth/otp/request', 'POST', { phone });
    return result.request_id;
  },

  verifyOtp: async (requestId, otp) => {
    if (API_DEMO_MODE) return requestId === 'req_demo' && otp === '123456';
    try {
      get().acceptSession(await requestApi<AuthSession>('/auth/otp/verify', 'POST', {
        request_id: requestId, otp,
      }));
      return true;
    } catch {
      return false;
    }
  },

  logout: () => {
    sessionVersion++;
    localStorage.removeItem(tokenKey);
    localStorage.removeItem(refreshKey);
    localStorage.removeItem(userKey);
    set({ user: null, role: 'buyer', token: null, isAuthenticated: false });
  },

  switchDemoRole: (role) => {
    if (!API_DEMO_MODE) return;
    const user = DEMO_USERS[role];
    localStorage.setItem(userKey, JSON.stringify(user));
    set({ user, role, isAuthenticated: true, token: 'mock_jwt_' + role });
    changeLanguage(user.language);
  },

  fetchCurrentUser: () => {
    if (API_DEMO_MODE || !localStorage.getItem(tokenKey)) return Promise.resolve();
    if (restoring) return restoring;
    const version = sessionVersion;
    restoring = (async () => {
      try {
        let user: AuthSession['user'];
        try {
          user = await requestApi<AuthSession['user']>('/me');
        } catch (error) {
          const refresh_token = localStorage.getItem(refreshKey);
          if (!(error instanceof ApiError) || error.code !== 'HTTP_401' && error.code !== 'UNAUTHENTICATED' ||
              !refresh_token || version !== sessionVersion) throw error;
          const tokens = await requestApi<Omit<AuthSession, 'user'>>('/auth/refresh', 'POST', { refresh_token });
          if (version !== sessionVersion) return;
          localStorage.setItem(tokenKey, tokens.access_token);
          localStorage.setItem(refreshKey, tokens.refresh_token);
          user = await requestApi<AuthSession['user']>('/me');
        }
        if (version !== sessionVersion) return;
        const updated = presentationUser(user);
        localStorage.setItem(userKey, JSON.stringify(updated));
        set({ user: updated, role: updated.role, token: localStorage.getItem(tokenKey), isAuthenticated: true });
      } catch (error) {
        if (version === sessionVersion && error instanceof ApiError &&
            ['HTTP_401', 'UNAUTHENTICATED'].includes(error.code)) get().logout();
      }
    })().finally(() => { restoring = undefined; });
    return restoring;
  },
}));
