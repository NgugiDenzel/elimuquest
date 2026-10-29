import { useAuthStore } from '../stores/authStore';
import { api } from '../services/api/client';

export function useAuthActions() {
  const setSession = useAuthStore((state) => state.setSession);
  const clear = useAuthStore((state) => state.clear);

  return {
    login: async (email: string, password: string) => {
      const result = await api.login({ email, password });
      const user = await api.meWithToken(result.access_token);
      await setSession(result.access_token, user);
      return user;
    },
    register: async (fullName: string, email: string, password: string) => {
      await api.register({ full_name: fullName, email, password });
      const result = await api.login({ email, password });
      const user = await api.meWithToken(result.access_token);
      await setSession(result.access_token, user);
      return user;
    },
    logout: clear,
  };
}
