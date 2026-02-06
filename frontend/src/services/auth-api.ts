/**
 * Authentication service for Google OAuth and session management.
 *
 * Handles login redirects, fetching current user, and logout.
 */

import { fetchAPI } from "./api";

export interface User {
  id: string;
  google_user_id: string;
  email: string;
  display_name: string | null;
  profile_picture_url: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Redirect to Google OAuth login flow.
 */
export async function login(): Promise<void> {
  const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  window.location.href = `${backendUrl}/auth/login`;
}

/**
 * Fetch current authenticated user.
 *
 * @returns User data if authenticated, null otherwise
 */
export async function getCurrentUser(): Promise<User | null> {
  try {
    const user = await fetchAPI<User>("/auth/me");
    return user;
  } catch (error) {
    // Not authenticated or session expired
    return null;
  }
}

/**
 * Logout current user.
 *
 * Clears localStorage token and server session cookie.
 */
export async function logout(): Promise<void> {
  localStorage.removeItem('auth_token');
  await fetchAPI("/auth/logout", {
    method: "POST",
  });
}
