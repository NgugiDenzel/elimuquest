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
    jest.useRealTimers();
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
      message: 'The server is taking longer than expected to respond. It may be waking from inactivity; wait a moment and try again.',
    });
  });

  it('allows a free backend time to wake before aborting the request', async () => {
    jest.useFakeTimers();
    fetchMock.mockImplementationOnce((_input, init) => new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => {
        reject(Object.assign(new Error('aborted'), { name: 'AbortError' }));
      });
    }));

    const request = api.login({ email: 'learner@example.test', password: 'valid-password' });
    let settled = false;
    const observed = request.then(
      () => { settled = true; },
      () => { settled = true; },
    );
    await jest.advanceTimersByTimeAsync(15000);
    await Promise.resolve();
    expect(settled).toBe(false);
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await jest.advanceTimersByTimeAsync(75000);
    await expect(request).rejects.toMatchObject({
      name: 'ApiError',
      status: 0,
      message: 'The server is taking longer than expected to respond. It may be waking from inactivity; wait a moment and try again.',
    });
    await observed;
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
