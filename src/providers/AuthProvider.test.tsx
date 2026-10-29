import { render, screen, waitFor } from '@testing-library/react-native';
import { afterEach, beforeEach, describe, expect, it, jest } from '@jest/globals';
import React from 'react';
import { Text } from 'react-native';
import { AuthProvider, useAuthStatus } from './AuthProvider';
import { api } from '../services/api/client';
import { authTokenStorage } from '../services/storage/authToken';
import { useAuthStore } from '../stores/authStore';

jest.mock('../services/storage/authToken', () => ({
  authTokenStorage: {
    get: jest.fn(),
    set: jest.fn(),
    remove: jest.fn(),
  },
}));

jest.mock('../services/api/client', () => ({
  api: {
    me: jest.fn(),
  },
}));

function AuthStatus() {
  const { restoreError } = useAuthStatus();
  return <Text>{restoreError ?? 'Session ready'}</Text>;
}

describe('AuthProvider session restoration', () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null, hydrated: false });
    jest.mocked(authTokenStorage.get).mockReset();
    jest.mocked(api.me).mockReset();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('hydrates when no saved token exists', async () => {
    jest.mocked(authTokenStorage.get).mockResolvedValue(null);

    render(
      <AuthProvider>
        <AuthStatus />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(useAuthStore.getState().hydrated).toBe(true);
    });
    expect(screen.getByText('Session ready')).toBeTruthy();
  });

  it('reports a failed profile restore and still completes hydration', async () => {
    jest.mocked(authTokenStorage.get).mockResolvedValue('stored-token');
    jest.mocked(api.me).mockRejectedValue(new Error('Profile request failed'));

    render(
      <AuthProvider>
        <AuthStatus />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(useAuthStore.getState().hydrated).toBe(true);
      expect(screen.getByText('Profile request failed')).toBeTruthy();
    });
    expect(useAuthStore.getState().token).toBe('stored-token');
  });
});
