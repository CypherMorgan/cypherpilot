/** TanStack Query hooks for Notifications. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
} from "@/modules/notifications/services/notifications";

const NOTIFICATION_KEYS = {
  all: ["notifications"] as const,
  list: (page?: number) => [...NOTIFICATION_KEYS.all, "list", page] as const,
  unread: ["notifications", "unread"] as const,
};

/**
 * Fetch paginated notifications.
 */
export function useNotifications(page: number = 1) {
  return useQuery({
    queryKey: NOTIFICATION_KEYS.list(page),
    queryFn: () => getNotifications({ page }),
    staleTime: 30_000,
  });
}

/**
 * Fetch unread notification count — polls every 30s.
 */
export function useUnreadCount() {
  return useQuery({
    queryKey: NOTIFICATION_KEYS.unread,
    queryFn: getUnreadCount,
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}

/**
 * Mark a single notification as read.
 */
export function useMarkNotificationRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) =>
      markNotificationRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * Mark all notifications as read.
 */
export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * Delete a notification.
 */
export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) => deleteNotification(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });
}
