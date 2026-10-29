import { afterAll, afterEach, describe, expect, it, jest } from '@jest/globals';

jest.mock('../../stores/authStore', () => ({
  useAuthStore: {
    getState: () => ({ token: null, clear: jest.fn() }),
  },
}));

jest.mock('expo-constants', () => ({
  __esModule: true,
  default: { expoConfig: null },
}));

import { api } from './client';

describe('API request errors', () => {
  const fetchMock = jest.spyOn(globalThis, 'fetch');

  afterEach(() => {
    fetchMock.mockReset();
  });

  afterAll(() => {
    fetchMock.mockRestore();
  });

  it('explains that a refused fetch is a backend connection problem', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(
      api.register({ email: 'learner@example.test', password: 'valid-password', full_name: 'Learner' }),
    ).rejects.toMatchObject({
      name: 'ApiError',
      status: 0,
      message: expect.stringContaining('Unable to connect to the ElimuQuest API'),
    });
  });

  it('preserves HTTP authentication errors instead of reporting a connection failure', async () => {
    fetchMock.mockResolvedValueOnce(
      {
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Email or password is incorrect' }),
      } as unknown as Response,
    );

    await expect(
      api.login({ email: 'learner@example.test', password: 'wrong-password' }),
    ).rejects.toMatchObject({
      name: 'ApiError',
      status: 401,
      message: 'Email or password is incorrect',
    });
  });

  it('reports a timeout distinctly', async () => {
    fetchMock.mockRejectedValueOnce(Object.assign(new Error('aborted'), { name: 'AbortError' }));

    await expect(
      api.login({ email: 'learner@example.test', password: 'valid-password' }),
    ).rejects.toMatchObject({
      name: 'ApiError',
      status: 0,
      message: 'The request timed out. Check the API server and try again.',
    });
  });

  it('reports malformed successful responses as an API response error', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => {
        throw new SyntaxError('Unexpected token');
      },
    } as unknown as Response);

    await expect(
      api.login({ email: 'learner@example.test', password: 'valid-password' }),
    ).rejects.toMatchObject({
      name: 'ApiError',
      status: 200,
      message: 'The API returned an invalid response (HTTP 200). Check the backend logs and try again.',
    });
  });
});
