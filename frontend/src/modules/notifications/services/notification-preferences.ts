import { apiClient } from "@/services/api-client";
import type { ApiSuccessResponse } from "@/types/api";
import type {
  NotificationPreference,
  NotificationPreferenceUpdate,
} from "@/modules/notifications/types/preferences";

export async function getNotificationPreferences(): Promise<NotificationPreference> {
  const response = await apiClient.get<
    ApiSuccessResponse<NotificationPreference>
  >("/notification-preferences");
  return response.data.data;
}

export async function updateNotificationPreferences(
  update: NotificationPreferenceUpdate,
): Promise<NotificationPreference> {
  const response = await apiClient.patch<
    ApiSuccessResponse<NotificationPreference>
  >("/notification-preferences", update);
  return response.data.data;
}
