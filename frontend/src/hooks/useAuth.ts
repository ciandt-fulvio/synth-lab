/**
 * useAuth hook for authentication state management.
 *
 * Provides React Query-powered authentication state and operations.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCurrentUser, login, logout, User } from "../services/auth-api";

export function useAuth() {
  const queryClient = useQueryClient();

  // Query for current user
  const {
    data: user,
    isLoading,
    error,
  } = useQuery<User | null>({
    queryKey: ["auth", "currentUser"],
    queryFn: getCurrentUser,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false, // Don't retry on 401
  });

  // Mutation for logout
  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      // Invalidate current user query
      queryClient.setQueryData(["auth", "currentUser"], null);
      queryClient.invalidateQueries({ queryKey: ["auth"] });
    },
  });

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    error,
    login, // This redirects, doesn't return a promise
    logout: () => logoutMutation.mutate(),
    isLoggingOut: logoutMutation.isPending,
  };
}
