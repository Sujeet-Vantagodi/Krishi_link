import { create } from 'zustand';
import { User, Role } from '../types';
import { changeLanguage } from '../i18n';
import { API_BASE_URL } from '../lib/api/client';

export interface AuthState {
  user: User | null;
  role: Role;
  token: string | null;
  isAuthenticated: boolean;
  setRole: (role: Role) => void;
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

// Retrieve stored login session from localStorage
const getInitialAuth = (): { user: User; role: Role; token: string; isAuthenticated: boolean } => {
  if (typeof window !== 'undefined') {
    try {
      const storedUser = localStorage.getItem('krishilink_user');
      const storedToken = localStorage.getItem('krishilink_token');
      if (storedUser && storedToken) {
        const parsed = JSON.parse(storedUser);
        return {
          user: parsed,
          role: parsed.role || 'buyer',
          token: storedToken,
          isAuthenticated: true,
        };
      }
    } catch (e) {
      console.warn('Could not parse stored user session:', e);
    }
  }
  return {
    user: DEMO_USERS.buyer,
    role: 'buyer',
    token: 'mock_jwt_token_buyer_123',
    isAuthenticated: true,
  };
};

const initialAuth = getInitialAuth();

export const useAuthStore = create<AuthState>((set, get) => ({
  user: initialAuth.user,
  role: initialAuth.role,
  token: initialAuth.token,
  isAuthenticated: initialAuth.isAuthenticated,

  setRole: (role: Role) => {
    const currentUser = get().user;
    if (currentUser && currentUser.role === role) {
      set({ role });
      return;
    }
    const demoUser = DEMO_USERS[role] || DEMO_USERS.buyer;
    set({ role, user: demoUser, isAuthenticated: true });
    if (typeof window !== 'undefined') {
      localStorage.setItem('krishilink_user', JSON.stringify(demoUser));
      localStorage.setItem('krishilink_token', 'mock_jwt_token_' + demoUser.id);
    }
    if (role === 'farmer') {
      changeLanguage('kn');
    } else {
      changeLanguage('en');
    }
  },

  setUser: (user: User | null) => {
    set({
      user,
      role: user ? user.role : 'buyer',
      isAuthenticated: !!user,
    });
    if (typeof window !== 'undefined') {
      if (user) {
        localStorage.setItem('krishilink_user', JSON.stringify(user));
      } else {
        localStorage.removeItem('krishilink_user');
        localStorage.removeItem('krishilink_token');
      }
    }
  },

  loginWithPhone: async (phone: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/otp/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone }),
      });
      if (res.ok) {
        const data = await res.json();
        return data.request_id || 'req_' + Math.random().toString(36).substring(2, 8);
      }
    } catch (e) {
      console.warn('Backend OTP request failed, using local simulation:', e);
    }
    return 'req_' + Math.random().toString(36).substring(2, 8);
  },

  verifyOtp: async (requestId: string, otp: string) => {
    await new Promise((r) => setTimeout(r, 400));
    // Accept 123456 or any 6-digit OTP for demo
    if (otp === '123456' || otp.length === 6) {
      const currentUser = get().user;
      const user = currentUser || DEMO_USERS[get().role] || DEMO_USERS.buyer;
      const token = get().token || ('mock_jwt_token_' + user.id);
      set({
        user,
        isAuthenticated: true,
        token,
      });
      if (typeof window !== 'undefined') {
        localStorage.setItem('krishilink_user', JSON.stringify(user));
        localStorage.setItem('krishilink_token', token);
      }
      return true;
    }
    return false;
  },

  logout: () => {
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
    if (typeof window !== 'undefined') {
      localStorage.removeItem('krishilink_user');
      localStorage.removeItem('krishilink_token');
    }
  },

  switchDemoRole: (role: Role) => {
    const newUser = DEMO_USERS[role];
    set({
      user: newUser,
      role,
      isAuthenticated: true,
      token: 'mock_jwt_' + role,
    });
    if (typeof window !== 'undefined') {
      localStorage.setItem('krishilink_user', JSON.stringify(newUser));
      localStorage.setItem('krishilink_token', 'mock_jwt_' + role);
    }
    if (role === 'farmer') {
      changeLanguage('kn');
    } else {
      changeLanguage('en');
    }
  },

  fetchCurrentUser: async () => {
    const token = get().token || (typeof window !== 'undefined' ? localStorage.getItem('krishilink_token') : null);
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const updatedUser: User = {
          id: data.id,
          name: data.name,
          phone: data.phone,
          email: data.email,
          role: data.role as Role,
          language: data.language || 'en',
          employee_id: data.employee_id || (data.profile && data.profile.employee_id),
          profile: data.profile,
        };
        set({ user: updatedUser, role: data.role as Role, isAuthenticated: true });
        if (typeof window !== 'undefined') {
          localStorage.setItem('krishilink_user', JSON.stringify(updatedUser));
        }
      }
    } catch (e) {
      // offline or backend unreachable
    }
  },
}));
