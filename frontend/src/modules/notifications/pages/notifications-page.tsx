/**
 * Notifications page — user's personal notifications.
 *
 * Shows a paginated list of notifications with mark-read, mark-all-read,
 * and delete actions.
 */

import { useState } from "react";
import {
  Bell,
  CheckCheck,
  Trash2,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Inbox,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  useNotifications,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
  useDeleteNotification,
} from "@/modules/notifications/hooks/use-notifications";
import type { NotificationItem } from "@/modules/notifications/types";

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const secs = Math.floor(diffMs / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function formatTimestamp(dateStr: string): string {
  return new Date(dateStr).toLocaleString();
}

/** Map notification type to a readable label. */
const NOTIFICATION_TYPE_LABELS: Record<string, string> = {
  "analysis.completed": "Analysis Complete",
  "analysis.failed": "Analysis Failed",
  "team.invite": "Team Invitation",
  "team.removed": "Removed from Team",
  "team.role_changed": "Role Changed",
};

function getNotificationTypeLabel(type: string): string {
  return NOTIFICATION_TYPE_LABELS[type] ?? type.replace(/[._]/g, " ");
}

/** Map notification type to a color class for the icon badge. */
function getNotificationTypeColor(type: string): string {
  if (type === "analysis.failed" || type === "team.removed") {
    return "bg-red-500/15 text-red-600 dark:text-red-400";
  }
  if (type === "team.invite" || type === "team.role_changed") {
    return "bg-violet-500/15 text-violet-600 dark:text-violet-400";
  }
  // analysis.completed and everything else
  return "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400";
}

interface NotificationCardProps {
  notification: NotificationItem;
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
}

function NotificationCard({
  notification,
  onMarkRead,
  onDelete,
}: NotificationCardProps) {
  return (
    <div
      className={`flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50 ${
        !notification.read ? "border-l-4 border-l-primary bg-primary/5" : ""
      }`}
    >
      <div className="mt-0.5">
        <Bell className={`h-4 w-4 ${notification.read ? "text-muted-foreground" : "text-primary"}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${getNotificationTypeColor(notification.type)}`}
          >
            {getNotificationTypeLabel(notification.type)}
          </span>
          <span
            className="text-xs text-muted-foreground"
            title={formatTimestamp(notification.created_at)}
          >
            {timeAgo(notification.created_at)}
          </span>
          {!notification.read && (
            <span className="h-2 w-2 rounded-full bg-primary" />
          )}
        </div>
        <p className="mt-1 text-sm font-medium">{notification.title}</p>
        <p className="text-sm text-muted-foreground">{notification.message}</p>
      </div>
      <div className="flex items-center gap-1">
        {!notification.read && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => onMarkRead(notification.id)}
            title="Mark as read"
          >
            <CheckCheck className="h-4 w-4" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-destructive"
          onClick={() => onDelete(notification.id)}
          title="Delete notification"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export function NotificationsPage() {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, isError, error } = useNotifications(page);
  const markReadMutation = useMarkNotificationRead();
  const markAllReadMutation = useMarkAllNotificationsRead();
  const deleteMutation = useDeleteNotification();

  const notifications = data?.items ?? [];
  const total = data?.total ?? 0;
  const unreadCount = data?.unread_count ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  const handleMarkRead = (id: string) => {
    markReadMutation.mutate(id);
  };

  const handleMarkAllRead = () => {
    markAllReadMutation.mutate();
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="mt-1 text-muted-foreground">
            {unreadCount > 0
              ? `You have ${unreadCount} unread notification${unreadCount !== 1 ? "s" : ""}`
              : "All caught up!"}
          </p>
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleMarkAllRead}
            disabled={markAllReadMutation.isPending}
            className="self-start sm:self-auto"
          >
            <CheckCheck className="mr-1 h-4 w-4" />
            Mark all read
          </Button>
        )}
      </div>

      {/* Loading state */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading notifications...
        </div>
      ) : isError ? (
        /* Error state */
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {(error as { message?: string })?.message ?? "Failed to load notifications"}
        </div>
      ) : notifications.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-muted-foreground">
          <Inbox className="mb-3 h-10 w-10 opacity-30" />
          <p className="text-sm">No notifications yet.</p>
          <p className="mt-1 text-xs">
            Notifications about analysis results, team invites, and other events will appear here.
          </p>
        </div>
      ) : (
        <>
          {/* Notification list */}
          <div className="space-y-1">
            {notifications.map((notification) => (
              <NotificationCard
                key={notification.id}
                notification={notification}
                onMarkRead={handleMarkRead}
                onDelete={handleDelete}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pt-4">
              <p className="text-sm text-muted-foreground">
                Page {page} of {totalPages} ({total} notification{total !== 1 ? "s" : ""})
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
