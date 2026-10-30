import Constants from 'expo-constants';

/**
 * API client communicating with FastAPI backend.
 * Handles automatic JWT injection, tenant boundary resolution, and response decoding.
 */

// Dynamically determine host IP from Expo hostUri or fallback to LAN IP for physical device
const debuggerHost = Constants.expoConfig?.hostUri;
const hostIp = debuggerHost ? debuggerHost.split(':')[0] : '192.168.1.111';
export const API_BASE_URL = `http://${hostIp}:8000/api/v1`;

let _authToken: string | null = null;
let _tenantId: string | null = null;

export const setAuthToken = (token: string | null) => {
  _authToken = token;
};

export const setTenantId = (tenantId: string | null) => {
  _tenantId = tenantId;
};

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<{ success: boolean; data?: T; error?: string }> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (_authToken) {
      headers['Authorization'] = `Bearer ${_authToken}`;
    }
    if (_tenantId) {
      headers['X-Tenant-ID'] = _tenantId;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    const json = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = json?.detail || json?.message || `HTTP ${response.status}: Request failed`;
      return { success: false, error: typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg) };
    }

    return { success: true, data: json as T };
  } catch (err: any) {
    return { success: false, error: err.message || 'Network connection failed' };
  }
}
