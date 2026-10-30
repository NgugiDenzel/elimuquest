import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { useAuthStore } from '../../stores/authStore';
import type {
  AnswerFeedback,
  AdminLesson,
  CurriculumOption,
  Dashboard,
  LeaderboardEntry,
  Lesson,
  LessonCompletion,
  Profile,
  Progress,
  Subject,
} from './types';

function developmentApiUrl(): string {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }

  const hostUri = Constants.expoConfig?.hostUri;
  if (hostUri) {
    try {
      return `http://${new URL(`http://${hostUri}`).hostname}:8000`;
    } catch {
      return 'http://localhost:8000';
    }
  }

  return 'http://localhost:8000';
}

const configuredApiUrl = process.env.EXPO_PUBLIC_API_URL?.trim();
const baseUrl = (configuredApiUrl || (__DEV__ ? developmentApiUrl() : '')).replace(/\/$/, '');
const requestTimeoutMs = 90000;
const requestTimeoutMessage =
  'The server is taking longer than expected to respond. It may be waking from inactivity; wait a moment and try again.';

function transportError(error: unknown): ApiError {
  if (error instanceof Error && error.name === 'AbortError') {
    return new ApiError(requestTimeoutMessage, 0);
  }
  if (error instanceof TypeError) {
    return new ApiError(
      `Unable to connect to the ElimuQuest API at ${baseUrl}. Confirm the backend is running and this address is reachable. Browser apps also require CORS to allow their origin; phones must use the computer's LAN address instead of localhost.`,
      0,
    );
  }
  return new ApiError('The API request failed unexpectedly. Please try again.', 0);
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  authenticated = true,
  tokenOverride?: string,
): Promise<T> {
  if (!baseUrl) {
    throw new ApiError(
      'The API URL is not configured. Set EXPO_PUBLIC_API_URL and rebuild the app.',
      0,
    );
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), requestTimeoutMs);
  const token = tokenOverride ?? useAuthStore.getState().token;
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/api/v1${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(authenticated && token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
  } catch (error) {
    clearTimeout(timeout);
    if (controller.signal.aborted) {
      throw new ApiError(requestTimeoutMessage, 0);
    }
    throw transportError(error);
  }

  try {
    if (!response.ok) {
      let message = `Request failed (${response.status})`;
      try {
        const body = await response.json() as { detail?: string };
        if (body.detail) message = body.detail;
      } catch {
        // Keep the status-based message when the response is not JSON.
      }
      if (response.status === 401 && authenticated) {
        await useAuthStore.getState().clear();
      }
      throw new ApiError(message, response.status);
    }
    try {
      return await response.json() as T;
    } catch {
      throw new ApiError(
        `The API returned an invalid response (HTTP ${response.status}). Check the backend logs and try again.`,
        response.status,
      );
    }
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  register: (data: { email: string; password: string; full_name: string }) =>
    request<Profile>('/auth/register', { method: 'POST', body: JSON.stringify(data) }, false),
  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; token_type: string }>(
      '/auth/login',
      { method: 'POST', body: JSON.stringify(data) },
      false,
    ),
  me: () => request<Profile>('/me'),
  meWithToken: async (token: string) => {
    if (!baseUrl) {
      throw new ApiError(
        'The API URL is not configured. Set EXPO_PUBLIC_API_URL and rebuild the app.',
        0,
      );
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), requestTimeoutMs);
    try {
      const response = await fetch(`${baseUrl}/api/v1/me`, {
        headers: { Accept: 'application/json', Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({})) as { detail?: string };
        throw new ApiError(body.detail || `Request failed (${response.status})`, response.status);
      }
      return await response.json() as Profile;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (controller.signal.aborted) {
        throw new ApiError(requestTimeoutMessage, 0);
      }
      throw transportError(error);
    } finally {
      clearTimeout(timeout);
    }
  },
  updateProfile: (data: Partial<Pick<Profile, 'full_name' | 'form' | 'curriculum_system' | 'curriculum_level' | 'timezone' | 'daily_goal_xp'>>) =>
    request<Profile>('/me/profile', { method: 'PATCH', body: JSON.stringify(data) }),
  curricula: () => request<{ items: CurriculumOption[] }>('/curricula'),
  adminLessons: () => request<{ items: AdminLesson[]; count: number }>('/admin/lessons'),
  updateLessonStatus: (
    lessonId: string,
    status: AdminLesson['status'],
  ) => request<{ id: string; status: AdminLesson['status']; published: boolean }>(
    `/admin/lessons/${encodeURIComponent(lessonId)}/status`,
    { method: 'PATCH', body: JSON.stringify({ status }) },
  ),
  dashboard: () => request<Dashboard>('/dashboard'),
  subjects: () => request<Subject[]>('/subjects'),
  subject: (id: string) => request<Subject>(`/subjects/${encodeURIComponent(id)}`),
  learningPath: (id: string) => request<{
    subject: string;
    curriculum_system: string;
    curriculum_level: string;
    curriculum_version: string;
    curriculum_label: string;
    lessons: Array<{ id: string; title: string; description: string; completed: boolean; questions_count: number }>;
  }>(`/subjects/${encodeURIComponent(id)}/learning-path`),
  lesson: (id: string) => request<Lesson>(`/lessons/${encodeURIComponent(id)}`),
  startLesson: (lessonId: string) =>
    request<{ id: string; lesson: Lesson }>('/lesson-sessions', {
      method: 'POST',
      body: JSON.stringify({ lesson_id: lessonId }),
    }),
  answer: (sessionId: string, questionId: string, answer: string) =>
    request<AnswerFeedback>(`/lesson-sessions/${sessionId}/answers`, {
      method: 'POST',
      body: JSON.stringify({ question_id: questionId, answer }),
    }),
  completeLesson: (sessionId: string) =>
    request<LessonCompletion>(`/lesson-sessions/${sessionId}/complete`, { method: 'POST' }),
  progress: () => request<Progress>('/progress'),
  leaderboard: () => request<LeaderboardEntry[]>('/leaderboard'),
};
