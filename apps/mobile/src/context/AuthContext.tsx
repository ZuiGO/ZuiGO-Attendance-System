import React, { createContext, useContext, useState, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';
import { setAuthToken, setTenantId } from '../services/api';
import { getOrCreateDeviceBinding, DeviceBindingInfo } from '../services/deviceSecurity';

interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  tenantId: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserProfile | null;
  deviceBinding: DeviceBindingInfo | null;
  login: (email: string, password: string, tenantId: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [deviceBinding, setDeviceBinding] = useState<DeviceBindingInfo | null>(null);

  useEffect(() => {
    async function initAuth() {
      const binding = await getOrCreateDeviceBinding();
      setDeviceBinding(binding);

      const savedToken = await SecureStore.getItemAsync('zuigo_jwt_token');
      const savedUserStr = await SecureStore.getItemAsync('zuigo_user_profile');

      if (savedToken && savedUserStr) {
        try {
          const profile: UserProfile = JSON.parse(savedUserStr);
          setUser(profile);
          setAuthToken(savedToken);
          setTenantId(profile.tenantId);
          setIsAuthenticated(true);
        } catch {
          // Bad profile JSON
        }
      }
      setIsLoading(false);
    }
    initAuth();
  }, []);

  const login = async (email: string, password: string, tenantId: string) => {
    setIsLoading(true);

    // Simulated login with device binding validation
    const mockUser: UserProfile = {
      id: 'e4b3e839-4cb5-4f3e-8e68-07df9706dbb7',
      name: email.split('@')[0].toUpperCase(),
      email,
      role: 'EMPLOYEE',
      tenantId: tenantId || 'c7e8e58a-3642-4f30-8025-4b0717fb0534',
    };

    const mockToken = `jwt-token-${Date.now()}`;
    await SecureStore.setItemAsync('zuigo_jwt_token', mockToken);
    await SecureStore.setItemAsync('zuigo_user_profile', JSON.stringify(mockUser));

    setAuthToken(mockToken);
    setTenantId(mockUser.tenantId);
    setUser(mockUser);
    setIsAuthenticated(true);
    setIsLoading(false);

    return { success: true };
  };

  const logout = async () => {
    await SecureStore.deleteItemAsync('zuigo_jwt_token');
    await SecureStore.deleteItemAsync('zuigo_user_profile');
    setAuthToken(null);
    setTenantId(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, user, deviceBinding, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
