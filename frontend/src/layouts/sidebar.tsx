import { NavLink } from "react-router-dom";
import {
  Bell,
  BellRing,
  LayoutDashboard,
  Settings,
  type LucideIcon,
  FlaskConical,
  Bug,
  Megaphone,
  Users,
  FileJson,
  Activity,
  Shield,
  GitCompareArrows,
  Layers,
  LayoutTemplate,
  Webhook,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { AnimatedLogo } from "@/components/animated-logo";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { UserMenu } from "@/components/user-menu";
import { useAuth } from "@/hooks/use-auth";

interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  disabled?: boolean;
}

const mainNav: NavItem[] = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Notifications", path: ROUTES.NOTIFICATIONS, icon: Bell },
  { label: "Notification Preferences", path: ROUTES.NOTIFICATION_PREFERENCES, icon: BellRing },
  { label: "Webhooks", path: "/webhooks", icon: Webhook },
  { label: "Teams", path: "/teams", icon: Users },
  { label: "Activity", path: "/activity", icon: Activity },
  { label: "Compare", path: "/compare", icon: GitCompareArrows },
];

const adminNav: NavItem[] = [
  { label: "Users", path: "/users", icon: Shield },
];

const moduleNav: NavItem[] = [
  { label: "Requirement Analysis", path: ROUTES.REQUIREMENT_ANALYSIS, icon: FileJson },
  { label: "API Test Generation", path: ROUTES.API_TEST_GENERATION, icon: FlaskConical },
  { label: "Failure Analysis", path: ROUTES.FAILURE_ANALYSIS, icon: Bug },
  { label: "Templates", path: ROUTES.TEMPLATES, icon: LayoutTemplate },
  { label: "Batch Analysis", path: ROUTES.FAILURE_BATCH, icon: Layers },
];

const bottomNav: NavItem[] = [
  { label: "What's New", path: "/changelog", icon: Megaphone },
  { label: "Settings", path: "/settings", icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed }: SidebarProps) {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const renderNavItems = (items: NavItem[]) =>
    items.map((item) => (
      <Tooltip key={item.path} delayDuration={collapsed ? 100 : 1000}>
        <TooltipTrigger asChild>
          <NavLink
            to={item.disabled ? "#" : item.path}
            onClick={(e) => {
              if (item.disabled) e.preventDefault();
            }}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                item.disabled
                  ? "cursor-not-allowed opacity-40"
                  : "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                isActive && !item.disabled
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground",
                collapsed && "justify-center px-2",
              )
            }
            title={item.label}
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        </TooltipTrigger>
        {collapsed && (
          <TooltipContent side="right">
            <p>{item.label}</p>
          </TooltipContent>
        )}
      </Tooltip>
    ));

  return (
    <aside
      className={cn(
        "flex flex-col border-r bg-sidebar-background transition-all duration-200",
        collapsed ? "w-16" : "w-60",
      )}
    >
      {/* Logo / App name */}
      <div
        className={cn(
          "flex h-14 items-center border-b border-sidebar-border px-4",
          collapsed && "justify-center px-0",
        )}
      >
        {collapsed ? (
          <AnimatedLogo variant="compact" />
        ) : (
          <AnimatedLogo variant="full" />
        )}
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col gap-1 p-3">
        <div className="flex flex-col gap-1">{renderNavItems(mainNav)}</div>

        {isAdmin && (
          <>
            {!collapsed && (
              <>
                <div className="py-2">
                  <Separator className="bg-sidebar-border" />
                </div>
                <p className="px-3 text-xs font-medium text-sidebar-muted-foreground">
                  Admin
                </p>
                <div className="mt-1 flex flex-col gap-1">
                  {renderNavItems(adminNav)}
                </div>
              </>
            )}
            {collapsed && (
              <div className="py-2">
                <Separator className="bg-sidebar-border" />
              </div>
            )}
            {collapsed && <div className="flex flex-col gap-1">{renderNavItems(adminNav)}</div>}
          </>
        )}

        {!collapsed && (
          <>
            <div className="py-2">
              <Separator className="bg-sidebar-border" />
            </div>
            <p className="px-3 text-xs font-medium text-sidebar-muted-foreground">
              Modules
            </p>
            <div className="mt-1 flex flex-col gap-1">
              {renderNavItems(moduleNav)}
            </div>
          </>
        )}

        {collapsed && (
          <div className="py-2">
            <Separator className="bg-sidebar-border" />
          </div>
        )}
        {collapsed && <div className="flex flex-col gap-1">{renderNavItems(moduleNav)}</div>}
      </nav>

      {/* Bottom section: user menu + settings */}
      <div className="border-t border-sidebar-border p-3">
        {!collapsed && <UserMenu />}
        {collapsed && (
          <div className="flex flex-col items-center gap-1">
            <UserMenu />
          </div>
        )}
        <div className="mt-2 flex flex-col gap-1">{renderNavItems(bottomNav)}</div>
      </div>
    </aside>
  );
}
