import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Settings,
  type LucideIcon,
  FlaskConical,
  Bug,
  Megaphone,
  Users,
  FileJson,
  Activity,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { APP_NAME, ROUTES } from "@/lib/constants";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { UserMenu } from "@/components/user-menu";

interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  disabled?: boolean;
}

const mainNav: NavItem[] = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Teams", path: "/teams", icon: Users },
  { label: "Activity", path: "/activity", icon: Activity },
];

const moduleNav: NavItem[] = [
  { label: "Requirement Analysis", path: ROUTES.REQUIREMENT_ANALYSIS, icon: FileJson },
  { label: "API Test Generation", path: ROUTES.API_TEST_GENERATION, icon: FlaskConical },
  { label: "Failure Analysis", path: ROUTES.FAILURE_ANALYSIS, icon: Bug },
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
          <span className="text-lg font-bold text-sidebar-foreground">CP</span>
        ) : (
          <span className="text-base font-bold text-sidebar-foreground">
            {APP_NAME}
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col gap-1 p-3">
        <div className="flex flex-col gap-1">{renderNavItems(mainNav)}</div>

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
