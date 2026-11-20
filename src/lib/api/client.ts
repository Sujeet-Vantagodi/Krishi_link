/**
 * API client configuration and network wrapper
 * Allows swapping between mock implementation and live FastAPI backend
 * via VITE_API_BASE_URL.
 */

const resolveApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL && import.meta.env.VITE_API_BASE_URL.startsWith('http')) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;
  }
  return 'http://localhost:8000/api/v1';
};

const resolveWsBaseUrl = () => {
  if (import.meta.env.VITE_WS_URL && import.meta.env.VITE_WS_URL.startsWith('ws')) {
    return import.meta.env.VITE_WS_URL;
  }
  if (typeof window !== 'undefined') {
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${wsProto}//${window.location.hostname}:8000/ws`;
  }
  return 'ws://localhost:8000/ws';
};

export const API_BASE_URL = resolveApiBaseUrl();
export const WS_BASE_URL = resolveWsBaseUrl();

export interface ApiResponse<T> {
  data: T;
  status: number;
}

export class ApiError extends Error {
  public code: string;
  public details?: any;

  constructor(code: string, message: string, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
  }
}

// Simulates network latency
export const delay = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms));
