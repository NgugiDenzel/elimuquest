import React, { useCallback, useEffect, useState } from 'react';
import { authTokenStorage } from '../services/storage/authToken';
import { api } from '../services/api/client';
import { useAuthStore } from '../stores/authStore';

type AuthProviderProps = { children: React.ReactNode };

export function AuthProvider({ children }: AuthProviderProps) {
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);
  const setHydrated = useAuthStore((state) => state.setHydrated);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  const restore = useCallback(async () => {
    setRestoreError(null);
    try {
      const token = await authTokenStorage.get();
      if (token) {
        setToken(token);
        const user = await api.me();
        setUser(user);
      }
    } catch (error) {
      setRestoreError(error instanceof Error ? error.message : 'Could not restore your session.');
    } finally {
      setHydrated(true);
    }
  }, [setHydrated, setToken, setUser]);

  useEffect(() => {
    void Promise.resolve().then(() => restore());
  }, [restore]);

  return (
    <AuthContext.Provider value={{ restoreError, retryRestore: restore }}>
      {children}
    </AuthContext.Provider>
  );
}

type AuthContextValue = {
  restoreError: string | null;
  retryRestore: () => Promise<void>;
};

const AuthContext = React.createContext<AuthContextValue>({
  restoreError: null,
  retryRestore: async () => undefined,
});

export function useAuthStatus() {
  return React.useContext(AuthContext);
}
