import { Menu, Server } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/theme-toggle";
import { useHealth } from "@/hooks/use-health";
import { NotificationBell } from "@/modules/notifications/components/notification-bell";
import { cn } from "@/lib/utils";

interface TopbarProps {
  onMenuToggle: () => void;
  sidebarCollapsed?: boolean;
}

export function Topbar({ onMenuToggle }: TopbarProps) {
  const { data: health, isError } = useHealth();

  return (
    <header className="flex h-14 items-center gap-3 border-b bg-background px-4">
      {/* Mobile menu toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onMenuToggle}
        aria-label="Toggle navigation menu"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Page title area — children can set via outlet context */}
      <div className="flex-1" />

      {/* Notification bell */}
      <NotificationBell />

      <Separator orientation="vertical" className="h-6" />

      {/* Backend connection indicator */}
      <div className="flex items-center gap-2">
        <div
          className={cn(
            "h-2 w-2 rounded-full",
            isError ? "bg-destructive" : "bg-emerald-500",
          )}
          title={
            isError
              ? "Backend unavailable"
              : health
                ? `Backend connected — ${health.app_version}`
                : "Checking..."
          }
        />
        <Server className="h-4 w-4 text-muted-foreground" />
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Theme toggle */}
      <ThemeToggle />
    </header>
  );
}
