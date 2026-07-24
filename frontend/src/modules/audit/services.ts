/** Audit log API service. */

import { apiClient } from "@/services/api-client";
import type { ApiSuccessResponse } from "@/types/api";

// ── Types ──────────────────────────────────────────────────────

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  team_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  extra_data: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// ── Functions ──────────────────────────────────────────────────

/**
 * Fetch audit log entries with pagination.
 */
export async function getAuditLogs(params: {
  page?: number;
  page_size?: number;
  team_id?: string;
  action_prefix?: string;
}): Promise<AuditLogListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));
  if (params.team_id) searchParams.set("team_id", params.team_id);
  if (params.action_prefix) searchParams.set("action_prefix", params.action_prefix);

  const qs = searchParams.toString();
  const response = await apiClient.get<ApiSuccessResponse<AuditLogListResponse>>(
    `/audit${qs ? `?${qs}` : ""}`,
  );
  return response.data.data;
}

// ── Display helpers ────────────────────────────────────────────

/** Human-readable action labels */
const ACTION_LABELS: Record<string, string> = {
  "auth.register": "Account created",
  "auth.login": "Logged in",
  "auth.change_password": "Password changed",
  "team.create": "Team created",
  "team.invite_member": "Member invited",
  "team.remove_member": "Member removed",
  "team.update_member_role": "Member role updated",
  "session.create": "Analysis started",
  "session.delete": "Analysis deleted",
};

/** Action color classes for badges */
const ACTION_COLORS: Record<string, string> = {
  "auth.register": "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  "auth.login": "bg-blue-500/15 text-blue-600 dark:text-blue-400",
  "auth.change_password": "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  "team.create": "bg-violet-500/15 text-violet-600 dark:text-violet-400",
  "team.invite_member": "bg-violet-500/15 text-violet-600 dark:text-violet-400",
  "team.remove_member": "bg-red-500/15 text-red-600 dark:text-red-400",
  "session.create": "bg-cyan-500/15 text-cyan-600 dark:text-cyan-400",
  "session.delete": "bg-red-500/15 text-red-600 dark:text-red-400",
};

export function getActionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action.replace(/[._]/g, " ");
}

export function getActionColor(action: string): string {
  return (
    ACTION_COLORS[action] ??
    "bg-muted text-muted-foreground"
  );
}
