import { apiClient } from "@/services/api-client";
import type { ApiSuccessResponse, DashboardStats } from "@/types/api";

/**
 * Fetch aggregate usage analytics for the authenticated user.
 * Requires a valid bearer token (401 when signed out).
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await apiClient.get<
    ApiSuccessResponse<DashboardStats>
  >("/dashboard/stats");
  return response.data.data;
}
