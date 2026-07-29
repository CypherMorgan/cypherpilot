/** Notification API service. */

import { apiClient } from "@/services/api-client";
import type { ApiSuccessResponse } from "@/types/api";
import type {
  NotificationItem,
  NotificationListResponse,
  UnreadCountResponse,
} from "@/modules/notifications/types";

/**
 * Fetch notifications with pagination.
 */
export async function getNotifications(params: {
  page?: number;
  page_size?: number;
  unread_only?: boolean;
}): Promise<NotificationListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));
  if (params.unread_only) searchParams.set("unread_only", "true");

  const qs = searchParams.toString();
  const response = await apiClient.get<ApiSuccessResponse<NotificationListResponse>>(
    `/notifications${qs ? `?${qs}` : ""}`,
  );
  return response.data.data;
}

/**
 * Get unread notification count.
 */
export async function getUnreadCount(): Promise<UnreadCountResponse> {
  const response = await apiClient.get<ApiSuccessResponse<UnreadCountResponse>>(
    "/notifications/unread",
  );
  return response.data.data;
}

/**
 * Mark a single notification as read.
 */
export async function markNotificationRead(
  notificationId: string,
): Promise<NotificationItem> {
  const response = await apiClient.patch<ApiSuccessResponse<NotificationItem>>(
    `/notifications/${notificationId}/read`,
  );
  return response.data.data;
}

/**
 * Mark all notifications as read.
 */
export async function markAllNotificationsRead(): Promise<{ count: number }> {
  const response = await apiClient.patch<ApiSuccessResponse<{ count: number }>>(
    "/notifications/read-all",
  );
  return response.data.data;
}

/**
 * Delete a notification.
 */
export async function deleteNotification(
  notificationId: string,
): Promise<void> {
  await apiClient.delete(`/notifications/${notificationId}`);
}
