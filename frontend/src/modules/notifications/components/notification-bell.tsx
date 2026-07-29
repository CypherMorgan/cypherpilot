/**
 * Notification bell icon with unread badge.
 *
 * Renders a bell icon in the topbar with the unread count.
 * Clicking navigates to the notifications page.
 */

import { Bell, BellRing } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useUnreadCount } from "@/modules/notifications/hooks/use-notifications";
import { cn } from "@/lib/utils";

export function NotificationBell() {
  const navigate = useNavigate();
  const { data } = useUnreadCount();
  const unreadCount = data?.count ?? 0;

  return (
    <Button
      variant="ghost"
      size="icon"
      className="relative"
      onClick={() => navigate("/notifications")}
      aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
    >
      {unreadCount > 0 ? (
        <BellRing className="h-5 w-5" />
      ) : (
        <Bell className="h-5 w-5" />
      )}
      {unreadCount > 0 && (
        <span
          className={cn(
            "absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground",
          )}
        >
          {unreadCount > 99 ? "99+" : unreadCount}
        </span>
      )}
    </Button>
  );
}
