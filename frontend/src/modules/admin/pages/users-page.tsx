/**
 * Users page — admin-only user management.
 *
 * Lists all users with pagination, shows role badges,
 * and lets admins promote/demote other users.
 */

import { useEffect, useState, useCallback } from "react";
import {
  Shield,
  User as UserIcon,
  Eye,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Users as UsersIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/hooks/use-auth";
import * as authService from "@/services/auth";
import type { User } from "@/services/auth";

const ROLE_CONFIG: Record<string, { label: string; icon: typeof Shield; color: string }> = {
  admin: {
    label: "Admin",
    icon: Shield,
    color: "bg-orange-500/15 text-orange-600 dark:text-orange-400",
  },
  user: {
    label: "User",
    icon: UserIcon,
    color: "bg-blue-500/15 text-blue-600 dark:text-blue-400",
  },
  viewer: {
    label: "Viewer",
    icon: Eye,
    color: "bg-muted text-muted-foreground",
  },
};

function RoleBadge({ role }: { role: string }) {
  const config = ROLE_CONFIG[role] ?? ROLE_CONFIG.user;
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${config.color}`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
}

export function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const pageSize = 20;

  const isAdmin = currentUser?.role === "admin";

  const fetchUsers = useCallback(async (p: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await authService.listUsers(p, pageSize);
      setUsers(result.users);
      setTotal(result.total);
    } catch (err: unknown) {
      setError((err as { message?: string })?.message ?? "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers(page);
  }, [page, fetchUsers]);

  const handleRoleChange = async (userId: string, newRole: string) => {
    setUpdatingId(userId);
    try {
      const updated = await authService.updateUserRole(userId, newRole);
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
    } catch (err: unknown) {
      setError((err as { message?: string })?.message ?? "Failed to update role");
    } finally {
      setUpdatingId(null);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-muted-foreground">
          <UsersIcon className="mb-3 h-10 w-10 opacity-30" />
          <p className="text-sm">Admin access required</p>
          <p className="mt-1 text-xs">Only administrators can manage users.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Users</h1>
        <p className="mt-1 text-muted-foreground">
          Manage user accounts and roles. {total} total user{total !== 1 ? "s" : ""}.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading users...
        </div>
      ) : error ? (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : users.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-muted-foreground">
          <UsersIcon className="mb-3 h-10 w-10 opacity-30" />
          <p className="text-sm">No users found.</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full min-w-[600px] text-sm">
              <thead>
                <tr className="border-b bg-muted/50 text-left">
                  <th className="px-4 py-3 font-medium">User</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Joined</th>
                  {isAdmin && <th className="px-4 py-3 font-medium text-right">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b last:border-b-0 transition-colors hover:bg-muted/30">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{user.display_name || user.username}</span>
                        {user.id === currentUser?.id && (
                          <span className="text-xs text-muted-foreground">(you)</span>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground">@{user.username}</span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{user.email}</td>
                    <td className="px-4 py-3">
                      <RoleBadge role={user.role} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    {isAdmin && (
                      <td className="px-4 py-3 text-right">
                        {user.id !== currentUser?.id ? (
                          <Select
                            value={user.role}
                            onValueChange={(val) => handleRoleChange(user.id, val)}
                            disabled={updatingId === user.id}
                          >
                            <SelectTrigger className="w-[120px]">
                              {updatingId === user.id ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <SelectValue />
                              )}
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="admin">Admin</SelectItem>
                              <SelectItem value="user">User</SelectItem>
                              <SelectItem value="viewer">Viewer</SelectItem>
                            </SelectContent>
                          </Select>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pt-4">
              <p className="text-sm text-muted-foreground">
                Page {page} of {totalPages} ({total} users)
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
