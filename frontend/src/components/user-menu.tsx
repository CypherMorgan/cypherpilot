/**
 * UserMenu — displayed in the sidebar bottom section.
 * Shows avatar with initials, username, and a dropdown with logout.
 */

import { LogOut } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

function getInitials(name: string | null | undefined, username: string): string {
  if (name) {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  }
  return username.slice(0, 2).toUpperCase();
}

export function UserMenu() {
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) return null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="w-full justify-start gap-3 px-3">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="text-xs">
              {getInitials(user.display_name, user.username)}
            </AvatarFallback>
          </Avatar>
          <div className="flex flex-col items-start text-left">
            <span className="text-sm font-medium leading-none">
              {user.display_name || user.username}
            </span>
            <span className="mt-0.5 text-xs text-muted-foreground">
              {user.role}
            </span>
          </div>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        <DropdownMenuLabel>
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{user.display_name || user.username}</p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={logout}>
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
