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
export const API_DEMO_MODE = import.meta.env.VITE_API_DEMO_MODE === 'true';

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

export async function requestApi<T>(
  path: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: unknown,
): Promise<T> {
  const token = localStorage.getItem('krishilink_token');
  const headers = new Headers({ Accept: 'application/json' });
  if (token && !token.startsWith('mock_jwt')) headers.set('Authorization', `Bearer ${token}`);
  if (body !== undefined) headers.set('Content-Type', 'application/json');
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError('NETWORK_ERROR', 'Unable to reach the KrishiLink API');
  }
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const detail = error?.error ?? error?.detail?.error ?? error?.detail;
    throw new ApiError(
      detail?.code ?? `HTTP_${response.status}`,
      detail?.message ?? (typeof detail === 'string' ? detail : response.statusText),
      detail?.details,
    );
  }
  return response.json();
}

// Simulates network latency
export const delay = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms));
