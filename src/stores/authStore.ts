import { create } from 'zustand';
import { authTokenStorage } from '../services/storage/authToken';
import type { Profile } from '../services/api/types';

type AuthState = {
  token: string | null;
  user: Profile | null;
  hydrated: boolean;
  setToken: (token: string | null) => void;
  setSession: (token: string, user: Profile) => Promise<void>;
  setUser: (user: Profile) => void;
  clear: () => Promise<void>;
  setHydrated: (hydrated: boolean) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  hydrated: false,
  setToken: (token) => set({ token }),
  setSession: async (token, user) => {
    await authTokenStorage.set(token);
    set({ token, user });
  },
  setUser: (user) => set({ user }),
  clear: async () => {
    await authTokenStorage.remove();
    set({ token: null, user: null });
  },
  setHydrated: (hydrated) => set({ hydrated }),
}));
