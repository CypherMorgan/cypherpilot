import { useQuery } from "@tanstack/react-query";

import { getDashboardStats } from "@/services/dashboard";

const DASHBOARD_STATS_KEY = ["dashboard", "stats"] as const;

/**
 * TanStack Query hook for personal usage analytics.
 * Refetches on window focus; retried once to tolerate transient errors.
 */
export function useDashboardStats() {
  return useQuery({
    queryKey: DASHBOARD_STATS_KEY,
    queryFn: getDashboardStats,
    staleTime: 60_000,
    retry: 1,
  });
}
