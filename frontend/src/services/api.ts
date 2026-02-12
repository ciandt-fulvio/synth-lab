// src/services/api.ts - Base API configuration

import type { QueryClient } from '@tanstack/react-query';

// In production, VITE_API_URL should point to the backend service URL
// In development, /api is proxied to localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Global QueryClient reference for auth invalidation on 401
let _queryClient: QueryClient | null = null;

/** Register the QueryClient so fetchAPI can invalidate auth cache on 401. */
export function setQueryClient(qc: QueryClient) {
  _queryClient = qc;
}

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  // Build headers with Authorization token from localStorage
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options?.headers as Record<string, string>,
  };
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include',  // Still send cookies for dev (same-domain)
      headers,
    });

    if (!response.ok) {
      // Handle session expiry: clear auth state so ProtectedRoute redirects to login
      if (response.status === 401) {
        localStorage.removeItem('auth_token');
        // Invalidate auth cache - ProtectedRoute will redirect to /login
        if (_queryClient) {
          _queryClient.setQueryData(['auth', 'currentUser'], null);
        } else if (!window.location.pathname.startsWith('/login')) {
          // Fallback if QueryClient not registered yet
          window.location.href = '/login';
        }
      }

      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = null;
      }

      throw new APIError(
        errorData?.detail || `HTTP error ${response.status}`,
        response.status,
        errorData
      );
    }

    // Handle empty responses
    const text = await response.text();
    if (!text) {
      return null as T;
    }

    // Check content type to determine how to parse response
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return JSON.parse(text) as T;
    }

    // Return text as-is for non-JSON responses (markdown, plain text, etc.)
    return text as T;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unknown error occurred'
    );
  }
}
