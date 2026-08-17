import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getNotificationPreferences,
  updateNotificationPreferences,
} from "@/modules/notifications/services/notification-preferences";
import type { NotificationPreferenceUpdate } from "@/modules/notifications/types/preferences";

const PREFERENCE_KEYS = {
  all: ["notification-preferences"] as const,
};

export function useNotificationPreferences() {
  return useQuery({
    queryKey: PREFERENCE_KEYS.all,
    queryFn: getNotificationPreferences,
    staleTime: 60_000,
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (update: NotificationPreferenceUpdate) =>
      updateNotificationPreferences(update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PREFERENCE_KEYS.all });
    },
  });
}
